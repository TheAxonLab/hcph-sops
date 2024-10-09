# Copyright 2024 The Axon Lab <theaxonlab@gmail.com>
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
from pathlib import Path
from json import loads, dumps
from sys import exit
import numpy as np
import pandas as pd
import h5py

from splitruns import DATA_PATH, BIDS_PATH, parse_session, main as extract

RECALIBRATED_SESSION = 23
FIRST_O2_SESSION = (
    11  # The cable to record O2 signal has been received midway through the acquisition
)
MISSING_RB = ("excl029",)


def _channel_id(channel_name):
    name_lower = channel_name.lower()
    if name_lower == "scanner ttl":
        return "trigger"

    if name_lower.startswith("digital") or "stp input" in name_lower:
        channel_num = int(channel_name.strip()[-2])
        return f"stim{channel_num - 1}" if channel_num > 0 else "trigger"

    if name_lower.startswith("card") or name_lower == "ecg" or "eeg100c" in name_lower:
        return "cardiac"

    if (
        name_lower.startswith("resp")
        or name_lower.startswith("rb")
        or "tsd160a" in name_lower
    ):
        return "respiratory0"

    if name_lower.startswith("co2") or name_lower.startswith("ga"):
        return "respiratory1"

    if name_lower.startswith("o2"):
        return "respiratory2"

    raise ValueError(f"Unknown channel name '{channel_name}'")


def _gen_timeseries(ch, offset=0.0):
    return (
        np.linspace(
            ch["start_time"],
            len(ch["data"]) / ch["frequency"] + ch["start_time"],
            num=len(ch["data"]),
        )
        - offset
    )


def get_1st_trigger_time(channels, start_run):
    ch = channels["trigger"]
    trigger_data = ch["data"]

    timeseries = _gen_timeseries(ch)

    index_left = np.abs(timeseries - max(ch["start_time"], start_run - 1)).argmin()
    index_right = np.abs(timeseries - (start_run + 1)).argmin() + 1
    first_trigger = (trigger_data[index_left:index_right] > 1e-5).argmax(axis=0)

    # Align the timeseries with the first trigger
    first_trigger_t = timeseries[index_left:index_right][first_trigger]
    timeseries -= first_trigger_t
    ch["timeseries"] = timeseries
    return timeseries, first_trigger_t


def extract_signal(recording, src_file, out_path, channels, first_trigger_t, session):
    # Generate BIDS name
    recording_filepath = out_path / src_file.name.replace(
        "_physio.hdf5", f"_recording-{recording}_physio.tsv.gz"
    )

    # Generate the time axis
    channel_names = sorted(
        [key for key in channels.keys() if key.startswith(recording)]
    )

    # All recordings MUST have the same frequency and hence, have same time axis
    timeseries = _gen_timeseries(channels[channel_names[0]], offset=first_trigger_t)
    for name in channel_names:
        channels[name]["timeseries"] = timeseries

    # Prepare metadata
    sidecar = loads(Path(f"defaults_{recording}.json").read_text()).copy()
    sidecar.update(
        {
            "SamplingFrequency": channels[channel_names[0]]["frequency"],
            "StartTime": timeseries[0],
        }
    )

    recording_data = {}  # Prepare dataframe
    for colname, name in zip(sidecar["Columns"], channel_names):
        sidecar[colname]["Units"] = channels[name]["units"]
        recording_data[colname] = channels[name]["data"]

    # Before session 23, calibration was a bit off
    if recording == "respiratory" and (
        session.startswith("pilot")
        or int(session.replace("excl", "")) < RECALIBRATED_SESSION
    ):
        if "CO2" in recording_data:
            recording_data["CO2"] = recording_data["CO2"] * (8.0 - 0.045) / 0.8 + 0.045
        if "O2" in recording_data:
            recording_data["O2"] = (recording_data["CO2"] - 0.1) * 10.946 / (
                20.946 + 0.1
            ) + 10

    sidecar["Columns"] = list(recording_data.keys())

    # We can store data now
    pd.DataFrame(recording_data).to_csv(
        recording_filepath,
        compression="gzip",
        header=False,
        sep="\t",
        na_rep="n/a",
    )
    print(f"Recording updated: {recording_filepath}")

    # And metadata
    sidecar_path = recording_filepath.parent / recording_filepath.name.replace(
        ".tsv.gz", ".json"
    )
    sidecar_path.write_text(dumps(sidecar, indent=2))
    print(f"Sidecar JSON updated: {sidecar_path}")

    return recording_filepath


def convert(
    src_file: Path,
    bids_path: Path = BIDS_PATH,
):
    # Preparations
    src_fname = src_file.name.split("_", 2)[:2]
    participant = src_fname[0][4:]
    session = src_fname[1][4:]

    out_path = (
        bids_path
        / f"sub-{participant}"
        / f"ses-{session}"
        / ("func" if "task-" in src_file.name else "dwi")
    )

    # Get data from split run (HDF5)
    channels = {}
    with h5py.File(src_file, "r") as h5f:
        start_recording = np.datetime64(
            h5f.attrs["start_recording"].decode("utf-8").rsplit("+", 1)[0]
        )
        start_run = h5f.attrs["start_run"]
        stop_run = h5f.attrs["stop_run"]

        for i, key in enumerate(h5f.keys()):
            metadata = h5f[key].attrs
            channel_id = _channel_id(metadata["name"])
            channels[channel_id] = dict(metadata.items())
            channels[channel_id]["num"] = int(key.split("_")[-1])
            channels[channel_id]["data"] = h5f[key]["data"][()]

    if (
        session.startswith("pilot")
        or int(session.replace("excl", "")) < FIRST_O2_SESSION
    ):
        channels.pop("respiratory2", None)

    # Extract & store first trigger
    _, first_trigger_t = get_1st_trigger_time(channels, start_run)
    trigger_filepath = out_path / src_file.name.replace("_physio.hdf5", "_stim.tsv.gz")

    columns = ["trigger"] + sorted(
        [_ch for _ch in channels.keys() if _ch.startswith("stim")]
    )
    trigger_data = {name: channels[name]["data"] for name in columns}

    trigger_sidecar = {
        "SamplingFrequency": channels["trigger"]["frequency"],
        "StartTime": channels["trigger"]["timeseries"][0],
        "Columns": columns,
        "Manufacturer": "BIOPAC Systems, Inc., Goleta, CA, US",
    }

    for col in columns:
        trigger_sidecar[col] = {
            "Description": f"Pulse signal [{channels[col]['name']}] generated with Psychopy",
            "Units": channels[col]["units"],
            "Model": "STP100D",
        }

    trigger_sidecar["trigger"]["Description"] = (
        f"Scanner trigger signal [{channels['trigger']['name']}]."
    )

    if out_path.name == "dwi":
        trigger_sidecar["trigger"]["Description"] += (
            " IMPORTANT! The DWI sequence sends triggers during calibration."
            " Therefore, a total of 203 trigger pulses SHOULD be discarded at the beginning of the run"
            " (corresponding to 2 x 87 slices single slice mode, plus 29 for one multi-slice volume)."
        )

    (
        trigger_filepath.parent / trigger_filepath.name.replace(".tsv.gz", ".json")
    ).write_text(dumps(trigger_sidecar, indent=2))

    pd.DataFrame(trigger_data).to_csv(
        trigger_filepath,
        compression="gzip",
        header=False,
        sep="\t",
        na_rep="n/a",
    )

    out_files = []
    for recording in ("cardiac", "respiratory"):
        out_files.append(
            extract_signal(
                recording, src_file, out_path, channels, first_trigger_t, session
            )
        )


def parse_args():
    """
    Parse command line arguments.

    Returns:
    --------
    argparse.Namespace
        Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Process physiological data for a BIDS dataset."
    )
    parser.add_argument("participant", type=str, help="Participant ID")
    parser.add_argument(
        "session",
        type=parse_session,
        help="Session identifier (can be an integer or string).",
    )
    parser.add_argument(
        "--data_path",
        type=Path,
        default=DATA_PATH,
        help="Path to BIOPAC .acq files (default: %(default)s)",
    )
    parser.add_argument(
        "--bids_path",
        type=Path,
        default=BIDS_PATH,
        help="Path to BIDS dataset (default: %(default)s)",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Do not overwrite existing files."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not (
        session_path := args.bids_path
        / f"sub-{args.participant}"
        / f"ses-{args.session}"
    ).exists():
        print(f"Skipping {session_path} (missing).")
        exit(1)

    src_files = sorted(
        args.data_path.glob(f"sub-{args.participant}_ses-{args.session}_*_physio.hdf5")
    )

    if not src_files or args.overwrite:
        src_files = extract(
            args.participant, args.session, args.data_path, args.bids_path
        )

    for chunk in src_files:
        convert(chunk, args.bids_path)
