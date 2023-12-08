# Copyright 2023 The Axon Lab <theaxonlab@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
from __future__ import annotations

import re
import json
from pathlib import Path
from warnings import warn
from collections import defaultdict
from itertools import product, groupby
from typing import List

import numpy as np
import pandas as pd

DEFAULT_EYE = "right"
DEFAULT_FREQUENCY = 1000
DEFAULT_MODE = "P-CR"
DEFAULT_SCREEN = (0, 800, 0, 600)

# EyeLink calibration coordinates from
# https://www.sr-research.com/calibration-coordinate-calculator/
EYELINK_CALIBRATION_COORDINATES = [
    (400, 300),
    (400, 51),
    (400, 549),
    (48, 300),
    (752, 300),
    (48, 51),
    (752, 51),
    (48, 549),
    (752, 549),
    (224, 176),
    (576, 176),
    (224, 424),
    (576, 424),
]

EYE_CODE_MAP = defaultdict(lambda: "unknown", {"R": "right", "L": "left", "RL": "both"})
EDF2BIDS_COLUMNS = {
    "g": "",
    "p": "pupil",
    "h": "href",
    "r": "raw",
    "fg": "fast",
    "fh": "fast_href",
    "fr": "fast_raw",
}

BIDS_COLUMNS_ORDER = (
    ["timestamp"]
    + [f"eye{num}_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_pupil_size" for num in (1, 2)]
    + [f"eye{num}_pupil_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_href_{c}_coordinate" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_href_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"eye{num}_raw_{c}_velocity" for num, c in product((1, 2), ("x", "y"))]
    + [f"fast_{c}_velocity" for c in ("x", "y")]
    + [f"fast_{kind}_{c}_velocity" for kind, c in product(("href", "raw"), ("x", "y"))]
    + [f"screen_ppdeg_{c}_coordinate" for c in ("x", "y")]
)


class EyeTrackingRun:
    """
    Class representing an instance of eye tracking data.

    Examples
    --------
    >>> et_run = EyeTrackingRun(
    ...     recording=recording_df,
    ...     events=events_df,
    ...     messages=messages_df,
    ...     message_first_trigger="start",
    ...     message_last_trigger="end",
    ...     metadata={"MyMetadata": "value"},
    ... )

    """

    def __init__(
        self,
        recording: pd.DataFrame,
        events: pd.DataFrame,
        messages: pd.DataFrame,
        message_first_trigger: str,
        message_last_trigger: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Initialize EyeTrackingRun instance.

        Parameters
        ----------
        recording : pd.DataFrame
            DataFrame containing eye tracking recording.
        events : pd.DataFrame
            DataFrame containing eye tracking events.
        messages : pd.DataFrame
            DataFrame containing eye tracking messages.
        message_first_trigger : str
            Message body that signals the start of the experiment run.
        message_last_trigger : str
            Message body that signals the end of the experiment run.
        metadata : dict
            A dictionary to bootstrap the metadata (e.g., with defaults).

        Notes
        -----
        This method initializes the EyeTrackingRun instance with the provided parameters.

        """
        self.recording = recording
        self.events = events
        self.metadata = metadata or {}

        # Messages may have headers ending with space and drop duplicate rows
        messages = messages.rename(
            columns={c: c.strip() for c in messages.columns.values}
        ).drop_duplicates()

        # Extract calibration headers
        _cal_hdr = messages.trialid.str.startswith("!CAL")
        calibration = messages[_cal_hdr]
        messages = messages.drop(messages.index[_cal_hdr])

        # Find Start time
        start_rows = messages.trialid.str.contains(
            message_first_trigger, case=False, regex=True
        )
        stop_rows = messages.trialid.str.contains(
            message_last_trigger, case=False, regex=True
        )

        # Pick the LAST of the start messages
        self.metadata["StartTime"] = (
            int(messages[start_rows].trialid_time.values[-1])
            if start_rows.any()
            else None
        )

        # Pick the FIRST of the stop messages
        self.metadata["StopTime"] = (
            int(messages[stop_rows].trialid_time.values[0])
            if stop_rows.any()
            else None
        )

        # Drop start and stop messages from messages dataframe
        messages = messages.loc[~start_rows & ~stop_rows, :]

        # Extract !MODE RECORD message signaling start of recording
        mode_record = messages.trialid.str.startswith("!MODE RECORD")

        meta_record = {
            "freq": DEFAULT_FREQUENCY,
            "mode": DEFAULT_MODE,
            "eye": DEFAULT_EYE,
        }

        if mode_record.any():
            try:
                meta_record = re.match(
                    r"\!MODE RECORD (?P<mode>\w+) (?P<freq>\d+) \d \d (?P<eye>[RL]+)",
                    messages[mode_record].trialid.iloc[-1].strip(),
                ).groupdict()

                meta_record["eye"] = EYE_CODE_MAP[meta_record["eye"]]
                meta_record["mode"] = (
                    "P-CR" if meta_record["mode"] == "CR" else meta_record["mode"]
                )
            except AttributeError:
                warn(
                    "Error extracting !MODE RECORD message, "
                    "using default frequency, mode, and eye"
                )
            finally:
                messages = messages.loc[~mode_record]

        self.eye = (
            ("right", "left") if meta_record["eye"] == "both" else (meta_record["eye"],)
        )

        self.metadata["SamplingFrequency"] = int(meta_record["freq"])
        self.metadata["EyeTrackingMethod"] = meta_record["mode"]
        self.metadata["RecordedEye"] = meta_record["eye"]

        # Extract GAZE_COORDS message signaling start of recording
        gaze_msg = messages.trialid.str.startswith("GAZE_COORDS")

        self.metadata["ScreenAOIDefinition"] = [
            "square",
            DEFAULT_SCREEN,
        ]
        if gaze_msg.any():
            try:
                gaze_record = re.match(
                    r"GAZE_COORDS (\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+)",
                    messages[gaze_msg].trialid.iloc[-1].strip(),
                ).groups()
                self.metadata["ScreenAOIDefinition"][1] = [
                    int(round(float(gaze_record[0]))),
                    int(round(float(gaze_record[2]))),
                    int(round(float(gaze_record[1]))),
                    int(round(float(gaze_record[3]))),
                ]
            except AttributeError:
                warn("Error extracting GAZE_COORDS")
            finally:
                messages = messages.loc[~gaze_msg]

        self.screen_resolution = self.metadata["ScreenAOIDefinition"][1][2:]

        # Extract ELCL_PROC AND ELCL_EFIT_PARAMS to extract pupil fit method
        pupilfit_msg = messages.trialid.str.startswith("ELCL_PROC")

        if pupilfit_msg.any():
            try:
                pupilfit_method = [
                    val
                    for val in messages[pupilfit_msg]
                    .trialid.iloc[-1]
                    .strip()
                    .split(" ")[1:]
                    if val
                ]
                self.metadata["PupilFitMethod"] = pupilfit_method[0].lower()
                self.metadata["PupilFitMethodNumberOfParameters"] = int(
                    pupilfit_method[1].strip("(").strip(")")
                )
            except AttributeError:
                warn("Error extracting ELCL_PROC (pupil fitting method)")
            finally:
                messages = messages.loc[~pupilfit_msg]

        pupilfit_msg_params = messages.trialid.str.startswith("ELCL_EFIT_PARAMS")
        if pupilfit_msg_params.any():
            rows = messages[pupilfit_msg_params]
            row = rows.trialid.values[-1].strip().split(" ")[1:]
            try:
                self.metadata["PupilFitParameters"] = [
                    tuple(float(val) for val in vals)
                    for k, vals in groupby(row, key=bool)
                    if k
                ]
            except AttributeError:
                warn("Error extracting ELCL_EFIT_PARAMS (pupil fitting parameters)")
            finally:
                messages = messages.loc[~pupilfit_msg_params]

        # Extract VALIDATE messages for a calibration validation
        validation_msg = messages.trialid.str.startswith("VALIDATE")

        if validation_msg.any():
            self.metadata["ValidationPosition"] = []
            self.metadata["ValidationErrors"] = []

        for i_row, validate_row in enumerate(messages[validation_msg].trialid.values):
            prefix, suffix = validate_row.split("OFFSET")
            validation_eye = (
                f"eye{self.eye.index('right') + 1}"
                if "RIGHT" in prefix
                else f"eye{self.eye.index('left') + 1}"
            )
            validation_coords = [
                int(val.strip())
                for val in prefix.rsplit("at", 1)[-1].split(",")
                if val.strip()
            ]
            self.metadata["ValidationPosition"].append(
                [validation_eye, validation_coords]
            )

            validate_values = [
                float(val)
                for val in re.match(
                    r"(-?\d+\.\d+) deg\.\s+(-?\d+\.\d+),(-?\d+\.\d+) pix\.",
                    suffix.strip(),
                ).groups()
            ]

            self.metadata["ValidationErrors"].append(
                (validation_eye, validate_values[0], tuple(validate_values[1:]))
            )
        messages = messages.loc[~validation_msg]

        # Extract THRESHOLDS messages prior recording and process last
        thresholds_msg = messages.trialid.str.startswith("THRESHOLDS")
        if thresholds_msg.any():
            self.metadata["PupilThreshold"] = [None] * len(self.eye)
            self.metadata["CornealReflectionThreshold"] = [None] * len(self.eye)
            thresholds_chunks = (
                messages[thresholds_msg].trialid.iloc[-1].strip().split(" ")[1:]
            )
            eye_index = self.eye.index(EYE_CODE_MAP[thresholds_chunks[0]])
            self.metadata["PupilThreshold"][eye_index] = int(thresholds_chunks[-2])
            self.metadata["CornealReflectionThreshold"][eye_index] = int(
                thresholds_chunks[-1]
            )
        messages = messages.loc[~thresholds_msg]

        # Consume the remainder of messages
        if not messages.empty:
            self.metadata["LoggedMessages"] = [
                (int(msg_timestamp), msg.strip())
                for msg_timestamp, msg in messages[["trialid_time", "trialid"]].values
            ]

        # Normalize timestamps (should be int and strictly positive)
        self.recording = self.recording.astype({"time": int})
        self.recording = self.recording[self.recording["time"] > 0]

        self.recording = self.recording.rename(
            columns={
                # Fix buggy header names generated by pyedfread
                "fhxyvel": "fhxvel",
                "frxyvel": "frxvel",
                # Normalize weird header names generated by pyedfread
                "rx": "screen_ppdeg_x_coordinate",
                "ry": "screen_ppdeg_y_coordinate",
                # Convert some BIDS columns
                "time": "timestamp",
            }
        )

        # Split extra columns from the dataframe
        self.extra = self.recording[["flags", "input", "htype"]]
        self.recording = self.recording.drop(columns=["flags", "input", "htype"])

        # Remove columns that are always very close to zero
        self.recording = self.recording.loc[:, (self.recording.abs() > 1e-8).any(axis=0)]
        # Remove columns that are always 1e8 or more
        self.recording = self.recording.loc[:, (self.recording.abs() < 1e8).any(axis=0)]
        # Replace unreasonably high values with NaNs
        self.recording = self.recording.replace({1e8: np.nan})

        # Drop one eye's columns if not interested in "both"
        if remove_eye := set(("left", "right")) - set(self.eye):
            remove_eye = remove_eye.pop()  # Drop set decoration
            self.recording = self.recording.reindex(
                columns=[c for c in self.recording.columns if remove_eye not in c]
            )

        for eyenum, eyename in enumerate(self.eye):
            # Clean-up implausible values for pupil area (pa)
            self.recording.loc[
                self.recording[f"pa_{eyename}"] < 1, f"pa_{eyename}"
            ] = np.nan
            self.recording = self.recording.rename(
                columns={f"pa_{eyename}": f"eye{eyenum + 1}_pupil_size"}
            )

            # Clean-up implausible values for gaze x position
            self.recording.loc[
                (self.recording[f"gx_{eyename}"] < 0)
                | (self.recording[f"gx_{eyename}"] > self.screen_resolution[0]),
                f"gx_{eyename}",
            ] = np.nan
            # Clean-up implausible values for gaze y position
            self.recording.loc[
                (self.recording[f"gy_{eyename}"] <= 0)
                | (self.recording[f"gy_{eyename}"] > self.screen_resolution[1]),
                f"gy_{eyename}",
            ] = np.nan

        # Interpolate BIDS column names
        columns = list(
            set(self.recording.columns)
            - set(
                (
                    "timestamp",
                    "screen_ppdeg_x_coordinate",
                    "screen_ppdeg_y_coordinate",
                    "eye1_pupil_size",
                    "eye2_pupil_size",
                )
            )
        )
        bids_columns = []
        for eyenum, eyename in enumerate(self.eye):
            for name in columns:
                colprefix = f"eye{eyenum + 1}" if name.endswith(f"_{eyename}") else ""
                _newname = name.split("_")[0]
                _newname = re.sub(r"([xy])$", r"_\1_coordinate", _newname)
                _newname = re.sub(r"([xy])vel$", r"_\1_velocity", _newname)
                _newname = _newname.split("_", 1)
                _newname[0] = EDF2BIDS_COLUMNS[_newname[0]]
                _newname.insert(0, colprefix)
                bids_columns.append("_".join((_n for _n in _newname if _n)))

        # Rename columns to be BIDS-compliant
        self.recording = self.recording.rename(columns=dict(zip(columns, bids_columns)))

        # Reorder columns to render nicely (tracking first, pupil size after)
        columns = sorted(
            set(self.recording.columns.values).intersection(BIDS_COLUMNS_ORDER),
            key=lambda entry: BIDS_COLUMNS_ORDER.index(entry),
        )
        columns += [c for c in self.recording.columns.values if c not in columns]
        self.recording = self.recording.reindex(columns=columns)

        # Parse calibration metadata
        self.metadata["CalibrationCount"] = 0
        if not calibration.empty:
            warn("Calibration of more than one eye is not implemented")
            calibration.trialid = calibration.trialid.str.replace("!CAL", "")
            calibration.trialid = calibration.trialid.str.strip()

            self.metadata["CalibrationLog"] = list(
                zip(
                    calibration.trialid_time.values.astype(int),
                    calibration.trialid.values,
                )
            )

            calibrations_msg = calibration.trialid.str.startswith(
                "VALIDATION"
            ) & calibration.trialid.str.contains("ERROR")
            self.metadata["CalibrationCount"] = calibrations_msg.sum()

            calibration_last = calibration.index[calibrations_msg][-1]
            try:
                meta_calib = re.match(
                    r"VALIDATION (?P<ctype>[\w\d]+) (?P<eyeid>[RL]+) (?P<eye>RIGHT|LEFT) "
                    r"(?P<result>\w+) ERROR (?P<avg>-?\d+\.\d+) avg\. (?P<max>-?\d+\.\d+) max\s+"
                    r"OFFSET (?P<offsetdeg>-?\d+\.\d+) deg\. "
                    r"(?P<offsetxpix>-?\d+\.\d+),(?P<offsetypix>-?\d+\.\d+) pix\.",
                    calibration.loc[calibration_last, "trialid"].strip(),
                ).groupdict()

                self.metadata["CalibrationType"] = meta_calib["ctype"]
                self.metadata["AverageCalibrationError"] = [float(meta_calib["avg"])]
                self.metadata["MaximalCalibrationError"] = [float(meta_calib["max"])]
                self.metadata["CalibrationResultQuality"] = [meta_calib["result"]]
                self.metadata["CalibrationResultOffset"] = [
                    float(meta_calib["offsetdeg"]),
                    (float(meta_calib["offsetxpix"]), float(meta_calib["offsetypix"])),
                ]
                self.metadata["CalibrationResultOffsetUnits"] = ["deg", "pixels"]
            except AttributeError:
                warn("Calibration data found but unsuccessfully parsed for results")

        # Process events: first generate empty columns
        self.recording["eye1_fixation"] = 0
        self.recording["eye1_saccade"] = 0
        self.recording["eye1_blink"] = 0

        # Add fixations
        for _, fixation_event in self.events[
            self.events["type"] == "fixation"
        ].iterrows():
            self.recording.loc[
                (self.recording["timestamp"] >= fixation_event["start"])
                & (self.recording["timestamp"] <= fixation_event["end"]),
                "eye1_fixation",
            ] = 1

        # Add saccades, and blinks, which are a sub-event of saccades
        for _, saccade_event in self.events[
            self.events["type"] == "saccade"
        ].iterrows():
            self.recording.loc[
                (self.recording["timestamp"] >= saccade_event["start"])
                & (self.recording["timestamp"] <= saccade_event["end"]),
                "eye1_saccade",
            ] = 1

            if saccade_event["blink"] == 1:
                self.recording.loc[
                    (self.recording["timestamp"] >= saccade_event["start"])
                    & (self.recording["timestamp"] <= saccade_event["end"]),
                    "eye1_blink",
                ] = 1


def write_bids(
    et_run: EyeTrackingRun,
    exp_run: str | Path,
) -> List[str]:
    """
    Save an eye-tracking run into a existing BIDS structure.

    Parameters
    ----------
    et_run : :obj:`EyeTrackingRun`
        An object representing an eye-tracking run.
    exp_run : :obj:`os.pathlike`
        The path of the corresponding neuroimaging experiment in BIDS.

    Returns
    -------
    List[str]
        A list of generated files.

    """

    exp_run = Path(exp_run)
    out_dir = exp_run.parent
    refname = exp_run.name
    extension = "".join(exp_run.suffixes)
    suffix = refname.replace(extension, "").rsplit("_", 1)[-1]
    refname = refname.replace(f"_{suffix}", "_eyetrack")

    # Remove undesired entities
    refname = re.sub(r"_part-(mag|phase)", "", refname)
    refname = re.sub(r"_echo-[\w\d]+", "", refname)

    # Write out sidecar JSON
    out_json = out_dir / refname.replace(extension, ".json")
    out_json.write_text(
        json.dumps(et_run.metadata, sort_keys=True, indent=2)
    )

    # Write out data
    out_tsvgz = out_dir / refname.replace(extension, ".tsv.gz")
    et_run.recording.to_csv(
        out_tsvgz,
        sep="\t",
        index=False,
        header=False,
        compression="gzip",
        na_rep="n/a",
    )

    return str(out_tsvgz), str(out_json)
