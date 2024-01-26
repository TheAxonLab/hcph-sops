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

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

EVENT_DURATION_EPSILON = 0.2
"""Tolerance threshold for tests on event duration."""

EVENTS_TSV_COLUMN_ORDER = ("onset", "duration", "trial_type", "value")
"""The order of TSV columns in the final BIDS-compatible file."""

TRIAL_TYPE = {
    "eye_movement_fixation": "cog",
    "ft_hand": "mot",
    "fixation": "blank",
    "grating": "vis",
    "movie": "movie",
    "bh_body": "red",
    "bh_end": "lightred",
    "end_trial_msg": "end-message",
    "polygon_4": "in",
    "polygon1": "out",
    "polygon_6": "in-last",
    "polygon_8": "out-last",
    "bh_body_2": "hold",
    "bh_end_2": "hold-warning",
    "bh_end_3": "refractory",
    "polygon_5": "out",  # old
    "polygon_7": "out-last",  # old
    "fixation_out": "fixation-point",  # fixation circle in RSfMRI
    "fixation_out_2": "fixation-point",  # fixation circle in RSfMRI
    "text": "instructions-text",  # showing instructions text with fixation point example
}
"""A dictionary mapping the trial identifiers and their semantics in the paradigm."""

PSYCHOPY_HDF5_EVENTS_DATASET = "data_collection/events/keyboard/KeyboardInputEvent"
"""The location of the keyboard events within *Psychopy*'s HDF5 output files."""


def psychopy2pandas(log_path: str | Path) -> pd.DataFrame:
    """
    Convert a PsychoPy log file to a *Pandas* DataFrame.

    Parameters
    ----------
    log_file : :obj:`os.pathlike`
        The path to the PsychoPy log file.

    Returns
    -------
    df : :obj:`pandas.DataFrame`
        A DataFrame containing event information.

    """

    df = pd.read_csv(
        log_path,
        sep="\t",
        names=["onset", "level", "desc"],
        dtype={"onset": float},
    )

    start_time = None
    if (hdf5_log := log_path.parent / log_path.name.replace(".log", ".hdf5")).exists():
        import h5py

        with h5py.File(hdf5_log, "r") as f:
            keypress_df = pd.DataFrame(
                np.asanyarray(f[PSYCHOPY_HDF5_EVENTS_DATASET])
            )

        start_time = keypress_df.loc[
            keypress_df.key.str.decode("utf-8").str.strip() == "s", "time"
        ].values[0]

    # If we can't find the keypress in the HDF5 file, try the plain log
    if start_time is None:
        start_time = df[
            (df.level.str.strip() == "DATA") & df.desc.str.contains("Keypress: s")
        ].onset.values[0]

    # Refer all onsets to the first trigger (first DATA entry)
    df.onset -= start_time

    # Register rows when the eye-tracker went on and off
    et_on = df.desc.str.strip() == "eyetracker.setRecordingState(True)"
    et_off = df.desc.str.strip() == "eyetracker.setRecordingState(False)"

    # Extract events
    df[["trial_type", "start_end"]] = df["desc"].str.extract(
        r"({}):\s+autoDraw\s*=\s*(\w+)".format("|".join(TRIAL_TYPE.keys()))
    )

    # Extract hand of motor block of qct
    df["hand"] = df["desc"].str.extract(r"ft_hand:\s*text\s*=\s*\'(RIGHT|LEFT)\'")
    df.loc[df.hand.notna(), "trial_type"] = "ft_hand"
    # Normalize L/R values of motor blocks
    df = df.replace({"hand": {"RIGHT": "R", "LEFT": "L"}})

    # Extract coordinates of cognitive block of qct
    df[["x", "y"]] = df["desc"].str.extract(
        r"New trial \(rep=\d+, index=\d+\): "
        r"OrderedDict\(\[\(\'xpos\', (-?\d+\.\d+)\), \(\'ypos\', (-?\d+\.\d+)\)\]\)"
    )
    df[["x", "y"]] = df[["x", "y"]].astype(float)
    df.loc[df.x.notna(), "trial_type"] = "eye_movement_fixation"

    df.loc[et_on, "trial_type"] = "et-record-on"
    df.loc[et_off, "trial_type"] = "et-record-off"

    # Drop duplicates (all columns exactly the same)
    df = df.drop_duplicates()

    return df


def pandas2bids(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a Pandas DataFrame with event information to a BIDS-compatible DataFrame.

    This function takes an input DataFrame with event information, performs various data
    transformations to create a BIDS-compatible DataFrame, and returns the resulting DataFrame.

    Notes:

    - Rows without 'trial_type' are dropped from the input DataFrame.
    - New columns 'duration' and 'value' are added to the resulting DataFrame.
    - Durations are calculated based on 'start_end' information and assigned to the appropriate
      rows.
    - Values are retrieved from previous rows for specific trial types and assigned to the
      relevant rows.
    - Event names are normalized based on 'TRIAL_TYPE' (please ensure 'TRIAL_TYPE' is defined).
    - Mock events in 'end-message' are replaced with appropriate values, and block numbers are
      assigned.

    Parameters
    ----------
    input_df : :obj:`pandas.DataFrame`
        The input DataFrame containing event information.

    Returns
    -------
    df : :obj:`pandas.DataFrame`
        A BIDS-compatible DataFrame with columns 'onset', 'duration', 'trial_type', and 'value'.

    Examples
    --------
    >>> input_df = pd.DataFrame(...)
    >>> output_df = pandas2bids(input_df)

    """

    # Drop rows without trial type
    df = input_df[input_df.trial_type.notna()]
    # Prepare new columns (duration and value)
    df = df.reindex(
        columns=[
            "onset",
            "duration",
            "trial_type",
            "value",
            "start_end",
            "hand",
            "x",
            "y",
        ]
    )
    df["value"] = df["value"].astype(str)

    for et in set(df.trial_type.values) - set(("et-record-on", "et-record-off")):
        # Create a subdataframe with only this trial type
        subdf = df[df.trial_type == et].copy()

        if len(subdf) < 2:  # No need to try if not a block
            continue

        # Calculate durations
        onsets = subdf.start_end.notna() & subdf.start_end.str.contains("True")
        offsets = subdf.start_end.notna() & subdf.start_end.str.contains("False")

        # Psychopy stimuli generate two "autoDraw = False" events:
        # first at the end of the stimuli presentation and a second at the end of the routine.
        # When the tracked stimuli end with the psychopy routine, the two "autoDraw = False"
        # events occur at the same time and they are deduplicated by psychopy2bids.
        if len(subdf[onsets].onset.values) == len(subdf[offsets].onset.values):
            durations = subdf[offsets].onset.values - subdf[onsets].onset.values
        else:
            # In the BHT, the stimuli do not last for the full span of the routine, and we have
            # two "autoDraw = False" events.
            # We need to drop the second corresponding to the routine.
            durations = subdf[offsets].onset.values[::2] - subdf[onsets].onset.values

        # And assign the duration to the first event row (the one containing autoDraw = True)
        subdf.loc[onsets, "duration"] = durations

        # Retrieve values from previous row for cognitive and motor blocks
        if et == "eye_movement_fixation":
            shifted = subdf.loc[
                subdf.start_end.isna() & subdf.x.notna(), ["x", "y"]
            ].values
            subdf.loc[onsets, "value"] = [f"({v[0]}, {v[1]})" for v in shifted]
        elif et == "ft_hand":
            shifted = subdf.loc[subdf.start_end.isna(), "hand"].values
            subdf.loc[onsets, "value"] = shifted

        # Move back to general dataframe
        df.loc[df.trial_type == et, subdf.columns] = subdf.values

    # Drop rows from which data was copied to the principal event row.
    df = df.drop(df[df.start_end.notna() & df.start_end.str.contains("False")].index)
    df = df.drop(df[df.start_end.isna() & df.x.notna()].index)
    df = df.drop(df[df.start_end.isna() & df.hand.notna()].index)

    # Normalize event names
    df = df.replace({"trial_type": TRIAL_TYPE})

    # Replace mock events in bht
    if "end-message" in set(df.trial_type.values):
        end_index = df[df.trial_type == "end-message"].index[0]
        df.loc[:end_index] = df.loc[:end_index].replace(
            {
                "trial_type": {
                    "in": "green",
                    "out": "yellow",
                    "in-last": "light-green",
                    "out-last": "gold",
                },
            },
        )
        df.loc[:end_index, "value"] = "mock"

        # After the mock there are 5 "true" blocks.
        len_remaining = len(df.loc[end_index + 1:, "value"])
        df.loc[end_index + 1:, "value"] = [
            f"block{v}" for block in range(1, 7) for v in [block] * 13
        ][:len_remaining]

    # Set duration 0.0 to the eyetracker on/off events
    df.loc[df.trial_type.str.startswith("et-record"), ("duration", "value")] = (0.0, np.nan)

    df = df.replace({"value": {"nan": np.nan}})
    df.dropna(axis=1, how="all", inplace=True)
    df = df.reset_index()

    # Drop columns where all values are nans
    return df


def check_durations(events):
    """Check stimuli durations are close to those of the task's design.

    This function takes an input DataFrame with event information, runs various tests and
    raises exceptions if any test fails.

    Parameters
    ----------
    input_df : :obj:`pandas.DataFrame`
        The input DataFrame containing BIDS-compatible event information.

    """

    EXPECTED_DURATION = {
        "blank": 3,
        "breath_in": 2.7,
        "breath_in_last": 2.7,
        "breath_out": 2.3,
        "breath_out_last": 2.3,
        "cog": 0.5,
        "hold": 13,
        "hold_end": 2,
        "hold_test": 13,
        "hold_test_end": 2,
        "mot": 5,
        "movie": 1200,
        "vis": 3,
    }

    for trial_type, expected_duration in EXPECTED_DURATION.items():
        if trial_type in events["trial_type"].values:
            indices = events[events["trial_type"] == trial_type].index
            for index in indices:
                duration = events.loc[index, "duration"]
                if not abs(duration - expected_duration) < EVENT_DURATION_EPSILON:
                    raise ValueError(
                        f"The duration {duration}s of the task '{events.loc[index, 'trial_type']}'"
                        f" does not match its expected duration of {expected_duration}s"
                    )


def check_repetitions(events):
    """Test that the stimuli appear in blocks with the expected number of consecutive lines

    This function takes an input DataFrame with event information, runs tests and
    raises exceptions if any test fails.

    Parameters
    ----------
    input_df : :obj:`pandas.DataFrame`
        The input DataFrame containing BIDS-compatible event information.

    """

    REPETITION = {"mot": 2, "cog": 6}

    for trial_type, expected_repetitions in REPETITION.items():
        if trial_type in events["trial_type"].values:
            # Extract number of consecutive lines
            repetitions = (
                events[events["trial_type"] == "cog"]
                .groupby((events["trial_type"] != "cog").cumsum())
                .size()
            )
            # Blocks can be consecutive so we check if the block size is a multiple of
            # the expected number of repetitions
            if any(repetitions % expected_repetitions != 0):
                raise ValueError(
                    f"The stimuli '{trial_type}' was expected to repeat {expected_repetitions} "
                    f"times but was repeated {repetitions} times instead."
                )


def check_sequence(events):
    """Test that the sequence of stimuli in the breath-holding task is respected.

    This function takes an input DataFrame with event information, runs tests and
    raises exceptions if any test fails.

    Parameters
    ----------
    input_df : :obj:`pandas.DataFrame`
        The input DataFrame containing BIDS-compatible event information.
    """

    PRECEDE = {
        "end_message": "lightred",
        "gold": "light-green",
        "hold": "out-last",
        "hold_warning": "hold",
        "in-last": "out",
        "light-green": "yellow",
        "lightred": "red",
        "out": "in",
        "out_last": "in-last",
        "red": "gold",
        "refractory": "hold-warning",
        "yellow": "green",
    }

    for trial_type, expected_preceding in PRECEDE.items():
        if trial_type in events["trial_type"].values:
            indices = events[events["trial_type"] == trial_type].index
            for index in indices:
                prev_index = index - 1
                if prev_index >= 0:
                    preceding = events.loc[prev_index, "trial_type"]
                    if preceding != expected_preceding:
                        raise ValueError(
                            f"The events file indicates that the stimulus '{preceding}' "
                            f"preceded the stimulus '{events.loc[index, 'trial_type']}' "
                            "but that does not correspond to the expected sequence."
                        )


def main() -> None:
    """
    Convert a PsychoPy log file to BIDS-compatible event data.

    This function handles the command-line interface for converting a PsychoPy log file to
    BIDS-compatible event data.
    It takes the input log file path and the desired output file path as command-line arguments,
    performs the conversion, and saves the resulting data in a BIDS-compatible TSV file.

    Example command-line::

        python psychopy2events.py -i /path/to/input/log.log -o sub-001_session-029_events.tsv

    """

    parser = argparse.ArgumentParser(
        description="Convert a PsychoPy log file to BIDS-compatible event data."
    )

    # Input file argument
    parser.add_argument(
        "recordings", type=Path, help="Folder containing PsychoPy's logfiles."
    )

    # BIDS file for which the events file is to be generated
    parser.add_argument(
        "bids_file",
        type=Path,
        help="Path to the functional/diffusion image (experiment) this recording corresponds to.",
    )
    args = parser.parse_args()

    if not args.bids_file.exists():
        raise RuntimeError(f"File <{args.bids_file}> doesn't exist.")

    # Extract session number
    if matches := re.findall(r"/ses-([\w\d]+)/", str(args.bids_file)):
        session = matches[0]
    else:
        raise RuntimeError("Could not extract session name")

    # Read schedule
    events_lookup = pd.read_csv(
        Path(__file__).parent / "schedule.tsv",
        sep="\t",
        na_values="n/a",
        dtype={"session": "str"},
    )

    # Extract the row containing the filenames of this particular session
    schedule_session = events_lookup[events_lookup.session == session]
    if len(schedule_session.index) == 0:
        raise RuntimeError(f"Session {session} not found in schedule")

    # Extract task name
    if "_dwi." in str(args.bids_file):
        task = "dwi"
    elif matches := re.findall(r"_task-([\w\d]+)_", str(args.bids_file)):
        task = matches[0]
    else:
        raise RuntimeError("Could not extract task")

    print(f"Generating events file corresponding to {args.bids_file}:")

    # Convert the PsychoPy log file to a Pandas DataFrame
    log_path = (
        args.recordings
        / f"session-{schedule_session.day.values[0]}"
        / schedule_session[f"{task}_events"].values[0]
    )
    input_df = psychopy2pandas(log_path)

    # Convert the Pandas DataFrame to a BIDS-compatible DataFrame
    output_df = pandas2bids(input_df)

    # Test the events dataframe
    check_durations(output_df)
    check_repetitions(output_df)
    check_sequence(output_df)

    refname = args.bids_file.name

    # Drop undesired entities (part and echo)
    refname = re.sub(r"_part-(mag|phase)", "", refname)
    refname = re.sub(r"_echo-\d+", "", refname)

    # Interpolate the events file's name from the BIDS file it annotates
    extension = "".join(args.bids_file.suffixes)
    suffix = refname.replace(extension, "").rsplit("_", 1)[-1]
    output_path = args.bids_file.parent / refname.replace(
        f"_{suffix}{extension}", "_events.tsv"
    )

    # Order columns
    columns = [col for col in EVENTS_TSV_COLUMN_ORDER if col in output_df.columns]

    # Save the BIDS-compatible DataFrame to the specified output file
    output_df[columns].to_csv(
        output_path, sep="\t", index=False, float_format="%.5f", na_rep="n/a"
    )

    print(f" ---> Written out {output_path}.")


if __name__ == "__main__":
    main()
