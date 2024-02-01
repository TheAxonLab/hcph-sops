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

import sys
from pathlib import Path
from json import loads, dumps
import re

from ppjson import CompactJSONEncoder


def edit_meta(json_path: str | Path) -> bool:
    """
    Open metadata, remove ``IntendedFor`` and add ``B0FieldIdentifier``.

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

    # Remove IntendedFor field
    _intendedfor = metadata.pop("IntendedFor", None)

    rewrite = "B0FieldIdentifier" not in metadata or args.force_rewrite

    if not rewrite:
        if _intendedfor is not None:
            print(f"Rewriting after IntendedFor metadata removal: {json_path}.")
            json_path.write_text(
                dumps(metadata, sort_keys=True, indent=2, cls=CompactJSONEncoder)
            )
            return True
        return False

    # Extract session number
    if matches := re.findall(r"/ses-([\w\d]+)/", str(json_path)):
        ses_id = matches[0]
    else:
        print(f"Could not extract session name for {json_path}.", file=sys.stderr)
        sys.exit(1)

    bids_suffix = json_path.name.replace(".json", "").rsplit("_", maxsplit=1)[-1]

    if bids_suffix == "epi":
        epi_type = "b0" if "_acq-b0" in json_path.name else "bold"
        metadata["B0FieldIdentifier"] = f"{ses_id}pepolar{epi_type}"
    else:
        metadata["B0FieldIdentifier"] = f"{ses_id}phasediff"

    print(f"Rewriting after B0FieldIdentifier metadata insertion: {json_path}.")
    json_path.write_text(
        dumps(metadata, sort_keys=True, indent=2, cls=CompactJSONEncoder)
    )

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check and fix fieldmaps' intent metadata.")
    parser.add_argument("json_path", type=str, help="Path to the JSON file.")
    parser.add_argument("-f", "--force_rewrite", action='store_true')
    args = parser.parse_args()

    success = edit_meta(args.json_path)
    print(f"{args.json_path}: [{'DONE' if success else 'SKIPPED'}]")
