# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
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

import argparse
import logging

import numpy as np
import os.path as op
import pandas as pd

from bids.layout import BIDSLayout, BIDSLayoutIndexer, add_config_paths

from load_save import (
    get_atlas_data,
    find_atlas_dimension,
    load_iqms,
)
from reports import (
    group_report,
)


def get_arguments() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="""Compute functional connectivity group report from functional connectivity matrices.""",
    )

    # Input/Output arguments and options
    parser.add_argument(
        "output",
        help="path to the directory where the functional connectivity matrices are stored",
    )
    parser.add_argument(
        "--mriqc-path",
        default=None,
        help="specify the path to the mriqc derivatives",
    )
    parser.add_argument(
        "--task",
        default=["rest"],
        action="store",
        nargs="+",
        help="a space delimited list of task(s)",
    )
    parser.add_argument(
        "--fc-estimator",
        default="sparse inverse covariance",
        action="store",
        choices=["correlation", "covariance", "sparse", "sparse inverse covariance"],
        type=str,
        help="""type of connectivity to compute (can be 'correlation', 'covariance' or
        'sparse')""",
    )
    parser.add_argument(
        "--atlas-dimension",
        default=64,
        type=int,
        help="dimension of the atlas (usually 64, 128 or 512)",
    )
    parser.add_argument(
        "--FD-thresh",
        default=0.5,
        action="store",
        type=float,
        help="framewise displacement threshold (in mm)",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=1,
        help="""increase output verbosity (-v: standard logging infos; -vv: logging
        infos and NiLearn verbose; -vvv: debug)""",
    )

    args = parser.parse_args()

    return args


def main():
    args = get_arguments()
    output = args.output
    task_filter = args.task
    mriqc_path = args.mriqc_path
    fc_label = args.fc_estimator.replace(" ", "")
    scale = args.atlas_dimension
    fdthresh = str(args.FD_thresh).replace(".", "")

    verbosity_level = args.verbosity

    logging_level_map = {
        0: logging.WARN,
        1: logging.INFO,
        2: logging.INFO,
        3: logging.DEBUG,
    }

    logging.basicConfig(
        # filename='example.log',
        # format='%(asctime)s %(levelname)s:%(message)s',
        format="%(levelname)s: %(message)s",
        level=logging_level_map[min([verbosity_level, 3])],
    )

    logging.captureWarnings(True)

    # Find the atlas dimension from the output path
    atlas_dimension = find_atlas_dimension(output)
    atlas_data = get_atlas_data(dimension=atlas_dimension)
    atlas_filename = getattr(atlas_data, "maps")

    # Find all existing functional connectivity
    # Initialize the BIDS layout, we use a custom indexer because we are using entities that are not yet officially recognized by BIDS 
    config_path = op.abspath(op.join(op.dirname(__file__), "../bids/indexer.json"))
    try:
        add_config_paths(hcph=config_path)
    except ValueError as e:
        if "Configuration 'hcph' already exists" in str(e):
            print("Configuration 'hcph' already exists, skipping add_config_paths.")
        else:
            raise e
    _indexer = BIDSLayoutIndexer(
        config_filename=config_path,
        index_metadata=False,
        validate=False,
    )       
    layout = BIDSLayout(output, config="hcph", indexer=_indexer, validate=False)
    existing_fc = layout.get(
        extension=".tsv",
        suffix="connectivity",
        task=task_filter,
        measure=fc_label,
        fd_threshold=fdthresh,
        scale=scale,
    )
    if not existing_fc:
        raise ValueError(
            f"No functional connectivity matrices found in {output} with task {task_filter}, meas {fc_label},"
            f"fdthresh {fdthresh}, and scale {scale}."
        )

    # Load functional connectivity matrices
    fc_matrices = []
    for file_path in existing_fc:
        fc_matrices.append(np.loadtxt(file_path, delimiter="\t"))

    # Load fMRI duration after censoring
    good_timepoints_df = pd.read_csv(
        op.join(output, "fMRI_duration_after_censoring.csv")
    )

    # Load IQMs
    iqms_df = load_iqms(output, existing_fc, mriqc_path=mriqc_path)

    # Generate group figures
    group_report(
        good_timepoints_df,
        fc_matrices,
        existing_fc,
        iqms_df,
        atlas_filename,
        output,
    )


if __name__ == "__main__":
    main()
