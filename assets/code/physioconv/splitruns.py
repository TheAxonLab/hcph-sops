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
from json import loads
from sys import exit
import numpy as np
import nibabel as nb
import pandas as pd
from datetime import timezone
import h5py

from bioread import read_file

# Default paths
DATA_PATH = Path("/data/datasets/hcph-pilot-sourcedata/recordings/BIOPAC")
BIDS_PATH = Path("/data/datasets/hcph")


def _get_length(filepath: Path) -> float:
    """
    Calculate the length of the run based on the metadata and file size.

    Parameters
    ----------
    filepath : Path
        The path to the NIfTI file.

    Returns
    -------
    float
        The length of the scan in seconds.

    """

    sidecar_fname = filepath.name.replace(".nii.gz", ".json").replace("_part-mag", "")
    sidecar = filepath.parent / sidecar_fname
    meta = loads(sidecar.read_text())
    if "RepetitionTime" not in meta:
        global_name = (
            sidecar.name.replace("_run-1", "").replace("_run-2", "").split("_", 2)[-1]
        )
        meta |= loads((sidecar.parents[3] / global_name).read_text())

    size = nb.load(filepath).shape[-1]
    return size * meta["RepetitionTime"]


def main(
    participant: str,
    session: str,
    data_path: Path = DATA_PATH,
    bids_path: Path = BIDS_PATH,
) -> list[Path]:
    """
    Process the scan and physiological data for the given participant and session.

    Parameters
    ----------
    participant : str
        The participant identifier (subject id).
    session : int
        The session number.
    data_path : Path, optional
        The path to the data files (default is DATA_PATH).
    bids_path : Path, optional
        The path to the BIDS dataset (default is BIDS_PATH).

    Returns
    -------
    Path
        The path to the generated HDF5 file.

    """
    scans_lookup = pd.read_csv(
        bids_path / "code" / "scans.tsv", sep="\t", na_values="n/a"
    )
    scans_lookup["acq_time"] = pd.to_datetime(scans_lookup.acq_time)
    scans_row = scans_lookup[
        scans_lookup.filename.str.startswith(f"sub-{participant}/ses-{session}/dwi")
    ]

    run_names = scans_lookup[
        (
            scans_lookup.filename.str.startswith(f"sub-{participant}/ses-{session}/dwi")
            | (
                scans_lookup.filename.str.startswith(
                    f"sub-{participant}/ses-{session}/func"
                )
                & scans_lookup.filename.str.contains("_echo-1_part-mag")
            )
        )
    ].filename.values.tolist()

    # BIDS: get onset and length for runs
    bids_start = np.array(
        [
            scans_lookup[scans_lookup.filename.str.contains(_rn)].acq_time.values[0]
            for _rn in run_names
        ],
        dtype=np.datetime64,
    )
    bids_lengths = np.array(
        [int(round(_get_length(bids_path / p) * 1e9)) for p in run_names],
        dtype="timedelta64[ns]",
    )

    # Extract AcqKnowledge metadata
    num_runs = len(run_names)
    run_id = 0
    recording_files = scans_row.physio_files.values
    if (recording_files.size == 0) or pd.isnull(recording_files).all():
        print(f"Skipping {session} (missing).")
        return []

    for physio_path in recording_files[0].split(","):
        acq_session = read_file(str(data_path / physio_path))
        acq_start = np.datetime64(
            str(
                acq_session.event_markers[0]
                .date_created_utc.replace(tzinfo=timezone.utc)
                .astimezone(tz=None)
            ).split("+")[0]
        )
        acq_stop = (
            len(acq_session.channels[4].time_index)
            / acq_session.channels[4].samples_per_second
        )

        # Calculate onsets and offsets (time limits)
        run_tlims = np.tile(bids_start[run_id:], (2, 1)) - acq_start
        run_tlims[1, :] += bids_lengths[run_id:]
        run_tlims = run_tlims / np.timedelta64(1, "s")
        run_tlims = run_tlims[:, run_tlims[1, :] < acq_stop].T
        run_tlims[run_tlims[:, 0] < 0, 0] = 0.0

        clip_onsets = [0] + (run_tlims[1:, 0] - 5.0).tolist()
        clip_offsets = (run_tlims[1:, 0] - 1.0).tolist() + [-1]

        channels = acq_session.channels

        out_files = []
        for chunk_i, (clip_on, clip_off) in enumerate(zip(clip_onsets, clip_offsets)):
            run_name = (
                Path(run_names[run_id])
                .name.replace("_echo-1_part-mag", "")
                .rsplit("_", 1)[0]
            )
            h5_filename = data_path / f"{run_name}_physio.hdf5"
            with h5py.File(h5_filename, "w") as h5f:
                h5f.attrs["start_recording"] = np.datetime_as_string(
                    acq_start,
                    timezone="local",
                ).astype("S30")
                h5f.attrs["start_run"] = run_tlims[chunk_i, 0]
                h5f.attrs["stop_run"] = run_tlims[chunk_i, 1]

                for channel_i, ch in enumerate(channels):
                    onset_index = (
                        0 if clip_on == 0 else np.abs(ch.time_index - clip_on).argmin()
                    )
                    offset_index = (
                        -1
                        if clip_off == -1
                        else np.abs(ch.time_index - clip_off).argmin()
                    )

                    ch_group = h5f.create_group(f"channel_{channel_i}")
                    ch_group.attrs["name"] = ch.name
                    ch_group.attrs["units"] = ch.units
                    ch_group.attrs["frequency"] = ch.samples_per_second
                    ch_group.attrs["start_time"] = round(ch.time_index[onset_index], 6)
                    ch_group.create_dataset(
                        "data",
                        data=ch.data[onset_index:offset_index],
                        compression="gzip",
                        compression_opts=9,
                    )

            print(f"Generated: {h5_filename}")
            out_files.append(h5_filename)
            run_id += 1

        if run_id == num_runs:
            break

    return out_files


def parse_session(session: str | int) -> str:
    """
    Parse the session argument to allow integers or strings.
    If the session argument starts with 'ses-', the prefix is removed.

    Parameters:
    -----------
    session : str
        The session identifier (could be an integer or string).

    Returns:
    --------
    str
        The cleaned session identifier without 'ses-' prefix.
    """
    if isinstance(session, int):
        return f"{session:03d}"

    # Remove 'ses-' prefix if present
    return session[4:] if session.startswith("ses-") else session


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

    main(args.participant, args.session, args.data_path, args.bids_path)
