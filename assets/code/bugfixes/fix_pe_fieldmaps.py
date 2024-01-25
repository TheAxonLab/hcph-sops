# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
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
"""Fix PA fieldmaps which are AP in reality."""
from __future__ import annotations

from pathlib import Path
from json import loads
import subprocess

import pandas as pd
from datalad.api import unlock


def check_and_fix(json_path: str | Path) -> bool:
    """
    Check and fix wrong PA.

    Parameters
    ----------
    json_path : :obj:`os.pathlike`
        Path to the JSON file.

    Returns
    -------
    bool
        True if fix was applied, False otherwise.

    """

    json_path = Path(json_path)

    metadata = loads(json_path.read_text())

    if metadata["PhaseEncodingDirection"] != "j-":
        return False

    print(f"Fixing <{json_path}>")
    nifti_path = str(json_path).replace(".json", ".nii.gz")
    json_ap = str(json_path).replace("_dir-PA_epi", "_dir-AP_epi")
    ap_exists = Path(json_ap).exists()

    # Read scans_tsv
    scans_tsv = (
        json_path.parent.parent
        / json_path.name.replace("_acq-b0_dir-PA_epi.json", "_scans.tsv")
    )
    scans_db = pd.read_csv(scans_tsv, sep=r"\s+", index_col=None)

    run_entity = ""
    if ap_exists:
        # Sometimes, the "PA" direction was acquired after the AP
        idx_pa = scans_db[scans_db.filename.str.endswith(Path(nifti_path).name)].index[0]
        idx_ap = scans_db[scans_db.filename.str.endswith(
            Path(json_ap.replace(".json", ".nii.gz")).name
        )].index[0]
        run_entity = "_run-1" if idx_pa < idx_ap else "_run-2"

    new_json = str(json_path).replace("_dir-PA_epi", f"_dir-AP{run_entity}_epi")

    # Rename JSON (git mv)
    subprocess.call(f"git mv {json_path} {new_json}", shell=True)

    # Unlock NIfTI
    new_nifti = new_json.replace('.json', '.nii.gz')
    unlock(path=nifti_path)
    subprocess.call(f"mv {nifti_path} {new_nifti}", shell=True)

    # Fix scans tsv
    scans_db.filename = scans_db.filename.str.replace(
        Path(nifti_path).name,
        Path(new_nifti).name,
        regex=False,
    )

    if ap_exists:
        new_json_ap = json_ap.replace(
            "_dir-AP_epi",
            f"_dir-AP{'_run-2' if run_entity == '_run-1' else '_run-1'}_epi",
        )

        # Rename JSON (git mv)
        subprocess.call(f"git mv {json_ap} {new_json_ap}", shell=True)

        nifti_ap = json_ap.replace(".json", ".nii.gz")
        new_nifti_ap = new_json_ap.replace('.json', '.nii.gz')
        unlock(path=nifti_ap)
        subprocess.call(f"mv {nifti_ap} {new_nifti_ap}", shell=True)

        scans_db.filename = scans_db.filename.str.replace(
            Path(nifti_ap).name,
            Path(new_nifti_ap).name,
            regex=False,
        )

    scans_db.to_csv(scans_tsv, sep="\t", index=None, na_rep="n/a")

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check and fix wrong PA fieldmaps.")
    parser.add_argument("json_path", type=str, help="Path to the JSON file.")
    args = parser.parse_args()

    success = check_and_fix(args.json_path)
    print(f"{args.json_path}: [{'DONE' if success else 'SKIPPED'}]")
