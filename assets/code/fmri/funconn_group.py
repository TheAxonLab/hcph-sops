import argparse
import logging

import os.path as op
import numpy as np

from itertools import chain
from funconn import FC_FILLS, FC_PATTERN

from load_save import (
    get_atlas_data,
    find_atlas_dimension,
    find_derivative,
    check_existing_output,
    get_bids_savename,
    get_func_filenames_bids,
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
    input_path = find_derivative(output)
    func_filenames, _ = get_func_filenames_bids(input_path, task_filter=task_filter)
    all_filenames = list(chain.from_iterable(func_filenames))

    existing_fc = check_existing_output(
        output,
        all_filenames,
        return_existing=True,
        return_output=True,
        patterns=FC_PATTERN,
        meas=fc_label,
        **FC_FILLS,
    )
    if not existing_fc:
        filename = op.join(
            output,
            get_bids_savename(
                all_filenames[0], patterns=FC_PATTERN, meas=fc_label, **FC_FILLS
            ),
        )
        raise ValueError(
            f"No functional connectivity of type {filename} were found. Please revise the arguments."
        )

    # Load functional connectivity matrices
    fc_matrices = []
    for file_path in existing_fc:
        fc_matrices.append(np.loadtxt(file_path, delimiter="\t"))

    # Load IQMs
    iqms_df = load_iqms(output, existing_fc, mriqc_path=mriqc_path)

    # Generate group figures
    group_report(
        fc_matrices,
        iqms_df,
        atlas_filename,
        output,
    )

if __name__ == "__main__":
    main()
