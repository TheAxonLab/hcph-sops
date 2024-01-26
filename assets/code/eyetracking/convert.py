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

from pathlib import Path
import re
import pandas as pd

from eyetrackingrun import EyeTrackingRun, write_bids


TASK_TRIGGER_MSG = {
    "fixation": ("hello", "bye"),
    "qct": ("hello qct", "bye qct"),
    "rest": ("start movie", "Bye rs"),
    "bht": ("hello bht", "Bye bht"),
}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert and EDF file that correspond to a BIDS imaging file.")
    parser.add_argument("recordings", type=Path, help="Folder containing EDF files.")
    parser.add_argument(
        "bids_file",
        type=Path,
        help="Path to the functional/diffusion image (experiment) this recording corresponds to.",
    )
    args = parser.parse_args()

    if not args.bids_file.exists():
        raise RuntimeError(f"File <{args.bids_file}> doesn't exist.")

    # Extract session number
    if (matches := re.findall(r'/ses-([\w\d]+)/', str(args.bids_file))):
        session = matches[0]
    else:
        raise RuntimeError("Could not extract session name")

    # Read schedule
    edf_lookup = pd.read_csv(
        Path(__file__).parent / "schedule.tsv",
        sep="\t",
        na_values="n/a",
        dtype={"session": "str"},
    )

    if not (edf_lookup.session == session).any():
        raise RuntimeError(f"Session {session} not found in schedule")

    # Extract task name
    if "_dwi." in str(args.bids_file):
        task = "fixation"
    elif (matches := re.findall(r'_task-([\w\d]+)_', str(args.bids_file))):
        task = matches[0]
    else:
        raise RuntimeError("Could not extract task")

    print(f"Converting eyetracking corresponding to {args.bids_file}:")

    trigger_messages = TASK_TRIGGER_MSG[task]
    et_session = edf_lookup[edf_lookup.session == session]
    et_obj = EyeTrackingRun.from_edf(
        args.recordings / et_session[f"{task}_edf"].values[0],
        message_first_trigger=trigger_messages[0],
        message_last_trigger=trigger_messages[-1],
    )

    out_files = write_bids(et_obj, args.bids_file)
    print(f" ---> Written out {', and '.join(out_files)}.")
