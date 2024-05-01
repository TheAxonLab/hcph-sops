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
"""Python script to denoise and aggregate timeseries and, using the latter, compute
functional connectivity matrices from BIDS derivatives (e.g. fmriprep).

Run as (see 'python funconn.py -h' for options):

    python funconn.py path_to_BIDS_derivatives

In the context of HCPh (pilot), it would be:

    python funconn.py /data/datasets/hcph-pilot/derivatives/fmriprep-23.1.4/
"""

import argparse
import csv
import logging
import os
import os.path as op
from itertools import chain
from typing import Optional, Union

import numpy as np
from nilearn_patcher import MultiNiftiMapsMasker as MultiNiftiMapsMasker_patched
from sklearn.covariance import GraphicalLassoCV, LedoitWolf

from nilearn._utils import stringify_path
from nilearn.connectome import ConnectivityMeasure, vec_to_sym_matrix
from nilearn.interfaces.fmriprep import load_confounds
from nilearn.maskers import MultiNiftiMapsMasker
from nilearn.signal import _handle_scrubbed_volumes, _sanitize_confounds, clean

from reports import plot_interpolation, visual_report_timeserie, visual_report_fc
from load_save import (
    find_derivative,
    check_existing_output,
    get_atlas_data,
    get_confounds_manually,
    get_func_filenames_bids,
    save_output,
    load_timeseries,
    FC_FILLS,
    FC_PATTERN,
    TIMESERIES_FILLS,
    TIMESERIES_PATTERN,
)

NETWORK_MAPPING: str = "yeo_networks7"  # Also yeo_networks17


def get_arguments() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="""Compute functional connectivity matrices from fmriprep
                    output directory.""",
    )

    # Input/Output arguments and options
    parser.add_argument("data_dir", help="BIDS dataset or derivatives with data")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="specify an alternative output directory",
    )
    parser.add_argument(
        "--study-name",
        default="",
        help="name of the study"
        "(will be followed by the name and dimension of the atlas)",
    )

    # Script specific options
    parser.add_argument(
        "--overwrite",
        default=False,
        action="store_true",
        help="force computation",
    )
    parser.add_argument(
        "--ses",
        default=[],
        action="store",
        nargs="+",
        help="a space delimited list of session(s)",
    )
    parser.add_argument(
        "--task",
        default=["rest"],
        action="store",
        nargs="+",
        help="a space delimited list of task(s)",
    )
    parser.add_argument(
        "--run",
        default=[],
        action="store",
        nargs="+",
        help="a space delimited list of run(s)",
    )

    # fMRI and denoising specific options
    parser.add_argument(
        "--atlas-dimension",
        default=64,
        type=int,
        help="dimension of the atlas (usually 64, 128 or 512)",
    )
    parser.add_argument(
        "--low-pass",
        default=0.15,
        action="store",
        type=float,
        help="cutoff frequency of low pass filtering",
    )
    parser.add_argument(
        "--denoising-strategy",
        default=("high_pass", "motion", "scrub"),
        action="store",
        type=tuple,
        help="type of noise components to include."
        '- "motion":  head motion estimates. Associated parameter: `motion`'
        '- "wm_csf" confounds derived from white matter and cerebrospinal fluid.'
        '- "global_signal" confounds derived from the global signal.'
        '- "compcor" confounds derived from CompCor (:footcite:t:`Behzadi2007`).'
        '  When using this noise component, "high_pass" must also be applied.'
        '- "scrub" regressors for :footcite:t:`Power2014` scrubbing approach.'
        '- "high_pass" adds discrete cosines transformation'
        "basis regressors to handle low-frequency signal drifts.",
    )
    parser.add_argument(
        "--motion",
        default="basic",
        action="store",
        choices=["basic", "power2", "derivatives", "full"],
        type=str,
        help="type of confounds extracted from head motion estimates."
        "- “basic” translation/rotation (6 parameters)"
        "- “power2” translation/rotation + quadratic terms (12 parameters)"
        "- “derivatives” translation/rotation + derivatives (12 parameters)"
        "- “full” translation/rotation + derivatives + quadratic terms + power2d derivatives (24 parameters)",
    )
    parser.add_argument(
        "--FD-thresh",
        default=0.4,
        action="store",
        type=float,
        help="framewise displacement threshold (in mm)",
    )
    parser.add_argument(
        "--SDVARS-thresh",
        default=5,
        action="store",
        type=float,
        help="standardized DVAR threshold",
    )
    parser.add_argument(
        "--n-scrub-frames",
        default=5,
        action="store",
        type=int,
        help="minimum segment length after volume censoring",
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
        "--no-censor",
        default=False,
        action="store_true",
        help="interpolate volumes with high motion without censoring",
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


def fit_transform_patched(
    func_filename: list[str],
    atlas_filename: str,
    confounds: Optional[list] = None,
    sample_mask: Optional[list] = None,
    **kwargs,
) -> list[np.ndarray]:
    """Attempt to use NiLearn's MultiNiftiMapsMaskers, if it fails it will use the
    patched version of the maskers (to be implemented into NiLearn in the future).

    Parameters
    ----------
    func_filename : list[str]
        List of BIDS functional filenames
    atlas_filename : str
        Path to the atlas file
    confounds : Optional[list], optional
        List of confounds (usually from nilearn.interface.fmriprep.load_confounds),
        by default None
    sample_mask : Optional[list], optional
        List of sample masks (usually from nilearn.interface.fmriprep.load_confounds),
        by default None

    Returns
    -------
    list[np.ndarray]
        List of extracted and denoised timeseries
    """
    masker = MultiNiftiMapsMasker(maps_img=atlas_filename, **kwargs)

    try:
        time_series = masker.fit_transform(
            func_filename, confounds=confounds, sample_mask=sample_mask
        )
    except ValueError as msg:
        if "Number of sample_mask" not in msg:
            raise
        # See nilearn issue #3967 for more details
        logging.warning("Using patched version of 'MultiNiftiMapsMasker ...'")
        masker = MultiNiftiMapsMasker_patched(maps_img=atlas_filename, **kwargs)

        time_series = masker.fit_transform(
            func_filename, confounds=confounds, sample_mask=sample_mask
        )

    return time_series


def interpolate_and_denoise_timeseries(
    func_filename: list[str],
    atlas_filename: str,
    confounds: list,
    sample_mask: list,
    t_r: Optional[float] = None,
    low_pass: Optional[float] = None,
    output: Optional[str] = None,
    verbose: int = 2,
) -> tuple[list[np.ndarray], list]:
    """Interpolate and denoise the timeseries without censoring high motion volumes.

    Parameters
    ----------
    func_filename : list[str]
        List of BIDS functional filenames
    atlas_filename : str
        Path to the atlas filename
    confounds : list
        List of confounds (usually from nilearn.interface.fmriprep.load_confounds).
    sample_mask : list
        List of sample_masks (usually from nilearn.interface.fmriprep.load_confounds).
    t_r : Optional[float], optional
        Repetition time of the MRI acquisition, by default None
    low_pass : Optional[float], optional
        Low-pass filtering cutoff frequency, by default None
    output : Optional[str], optional
        Path to the output directory, by default None
    verbose : int, optional
        Amount of verbosity, by default 2

    Returns
    -------
    tuple[list[np.ndarray], list]
        Two lists, one with the denoised timeseries and one with the corresponding
        confounds.
    """
    logging.info("Interpolating signal (no censoring) ...")
    # Extract the regional signals
    extracted_time_series = fit_transform_patched(
        func_filename,
        atlas_filename,
        standardize="zscore_sample",
        verbose=verbose,
        n_jobs=8,
    )

    interpolated_signals = []
    interpolated_confounds = []
    denoised_signals = []
    for ts, conf, sm, fn in zip(
        extracted_time_series, confounds, sample_mask, func_filename
    ):
        logging.debug(
            f"Timeserie has length {ts.shape[0]} and sample mask has "
            f"length {len(sm)}"
        )

        # This is required as we are manually doing some internal Nilearn machinery
        conf = _sanitize_confounds(ts.shape[0], n_runs=1, confounds=conf)
        conf = stringify_path(conf)

        ts_to_interpolate = ts.copy()

        inter_sig, inter_conf = _handle_scrubbed_volumes(
            signals=ts_to_interpolate,
            confounds=conf,
            sample_mask=sm,
            filter_type="butterworth",
            t_r=t_r,
        )

        if output is not None:
            plot_interpolation(ts, inter_sig, fn, output)

        # Denoise the signals
        denoised_sig = clean(
            inter_sig,
            standardize="zscore_sample",
            confounds=inter_conf,
            low_pass=low_pass,
            t_r=t_r,
        )

        interpolated_signals.append(inter_sig)
        interpolated_confounds.append(inter_conf)
        denoised_signals.append(denoised_sig)

    return denoised_signals, interpolated_confounds


def extract_and_denoise_timeseries(
    func_filename: list[str],
    atlas_filename: str,
    verbose: int = 2,
    interpolate: bool = False,
    low_pass: Optional[float] = None,
    denoising_strategy: Optional[tuple] = (),
    motion: Optional[str] = None,
    t_r: Optional[float] = None,
    output: Optional[str] = None,
    **kwargs,
) -> tuple[list[np.ndarray], list, list[np.ndarray]]:
    """Extract and denoise regional timeseries for a given atlas.

    Parameters
    ----------
    func_filename : list[str]
        List of BIDS functional filenames
    atlas_filename : str
        Path to the atlas filename
    verbose : int, optional
        Amount of verbosity, by default 2
    interpolate : bool, optional
        Condition to ONLY interpolate the timeseries (without censoring),
        by default False
    low_pass : Optional[float], optional
        Low-pass filtering cutoff frequency, by default None
    denoising_strategy = Optional[tuple], optional,
        the type of noise regressors to include.
    motion: Optional[str], optional,
        type of confounds extracted from head motion estimates
    t_r : Optional[float], optional
        Repetition time of the MRI, by default None
    output : Optional[str], optional
        Path to the output directory, by default None

    Returns
    -------
    tuple[list[np.ndarray], list]
        Two lists, one with the extracted and denoised timeseries and one with the
        corresponding confounds.
    """
    if not len(func_filename):
        return [], [], []

    logging.info(f"Extracting and denoising timeseries for {len(func_filename)} files.")
    logging.debug(f"Denoising strategy includes : {' '.join(denoising_strategy)}")
    logging.debug(f"Denoising parameters are: {kwargs}")

    # There is currently a bug in nilearn that prevents "load_confounds" from finding
    # the confounds file if it contains any other BIDS entity than "ses" and "run".
    # It should be fixed in release 0.13.
    try:
        confounds, sample_mask = load_confounds(
            func_filename,
            demean=False,
            strategy=denoising_strategy,
            motion=motion,
            **kwargs,
        )
    except ValueError as msg:
        if "Could not find associated confound file. " not in str(msg):
            raise

        logging.warning(
            "Nilearn could not find the confounds file (this is likely due to a"
            " bug in nilearn.interface.fmriprep.load_confounds that should be fixed in"
            " release 0.13, see nilearn issue #3792)."
        )
        logging.warning("Searching manually ...")

        confounds, sample_mask = get_confounds_manually(
            func_filename,
            demean=False,
            strategy=denoising_strategy,
            motion=motion,
            **kwargs,
        )

    # The outputs of "load_confounds" will not be in a list if
    # "func_filename" is a list with one element.
    if not isinstance(confounds, list):
        confounds = [confounds]
    if not isinstance(sample_mask, list):
        sample_mask = [sample_mask]

    if interpolate:
        time_series, confounds = interpolate_and_denoise_timeseries(
            func_filename,
            atlas_filename,
            confounds,
            sample_mask,
            t_r=t_r,
            low_pass=low_pass,
            output=output,
            verbose=verbose,
        )
        return time_series, confounds

    time_series = fit_transform_patched(
        func_filename,
        atlas_filename,
        confounds,
        sample_mask,
        low_pass=low_pass,
        t_r=t_r,
        standardize="zscore_sample",
        verbose=verbose,
        reports=True,
        n_jobs=8,
    )

    return time_series, confounds, sample_mask


def get_fc_strategy(
    strategy: str = "sparse inverse covariance",
) -> tuple[Union[GraphicalLassoCV, LedoitWolf], str, str]:
    """Get the strategy to compute functional connectivity.

    Parameters
    ----------
    strategy : str, optional
        Name of the strategy, could be "correlation", "covariance" or "sparse",
        by default "sparse inverse covariance"

    Returns
    -------
    tuple[Union[GraphicalLassoCV, LedoitWolf], str, str]
        Returns the covariance estimator, the name of the metric (covariance or
        precision) as well as standardized label for file naming.
    """
    connectivity_kind = "precision"
    connectivity_label = "sparseinversecovariance"
    estimator = GraphicalLassoCV(alphas=6, max_iter=1000)

    if strategy in ["cor", "corr", "correlation"]:
        connectivity_kind = "correlation"
        connectivity_label = "correlation"
        estimator = LedoitWolf(store_precision=False)
    elif strategy not in ["sparse", "sparse inverse covariance"]:
        connectivity_kind = "covariance"
        connectivity_label = "covariance"

    return estimator, connectivity_kind, connectivity_label


def compute_connectivity(
    time_series: list[np.ndarray],
    estimator: Union[LedoitWolf, GraphicalLassoCV] = LedoitWolf(store_precision=False),
    connectivity_kind: str = "correlation",
) -> list[np.ndarray]:
    """Compute the functional connectivity using the specified estimator and
    connectivity kind.

    Parameters
    ----------
    time_series : list[np.ndarray]
        List of timeseries
    estimator : Union[LedoitWolf, GraphicalLassoCV], optional
        Covariance estimator (usually from Scikit-Learn),
        by default LedoitWolf(store_precision=False)
    connectivity_kind : str, optional
        Type of connectivity to compute, by default "correlation"

    Returns
    -------
    list[np.ndarray]
        List of functional connectivity matrices
    """
    if not len(time_series):
        return []
    n_ts = len(time_series)
    n_area = time_series[0].shape[-1]
    logging.info(
        f"Computing functional connectivity matrices for {n_ts} timeseries ..."
    )

    connectivity_estimator = ConnectivityMeasure(
        cov_estimator=estimator,
        kind=connectivity_kind,
        vectorize=True,
        discard_diagonal=True,
    )
    connectivity_measures = connectivity_estimator.fit_transform(time_series)
    return vec_to_sym_matrix(connectivity_measures, diagonal=np.zeros((n_ts, n_area)))


def main():
    args = get_arguments()

    input_path = args.data_dir
    output = args.output
    study_name = args.study_name

    ses_filter = args.ses
    task_filter = args.task
    run_filter = args.run
    overwrite = args.overwrite

    # denoise_only = args.denoise_only
    atlas_dimension = args.atlas_dimension
    low_pass = args.low_pass
    denoising_strategy = args.denoising_strategy
    motion = args.motion
    fd_threshold = args.FD_thresh
    std_dvars_threshold = args.SDVARS_thresh
    scrub = args.n_scrub_frames
    fc_estimator = args.fc_estimator
    interpolate = args.no_censor

    verbosity_level = args.verbosity
    nilearn_verbose = verbosity_level - 1

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

    func_filenames, t_r_list = get_func_filenames_bids(
        input_path,
        task_filter=task_filter,
        ses_filter=ses_filter,
        run_filter=run_filter,
    )
    all_filenames = list(chain.from_iterable(func_filenames))
    logging.info(f"Found {len(all_filenames)} functional file(s):")
    logging.info(
        "\t" + "\n\t".join([op.basename(filename) for filename in all_filenames])
    )

    atlas_data = get_atlas_data(dimension=atlas_dimension)
    atlas_filename = getattr(atlas_data, "maps")
    atlas_labels = getattr(atlas_data, "labels").loc[:, "difumo_names"]
    atlas_network = getattr(atlas_data, "labels").loc[:, NETWORK_MAPPING]

    if output is None:
        run_name = f"DiFuMo{atlas_dimension:d}"
        if study_name:
            run_name = "-".join([study_name, run_name])

        run_name += (low_pass is not None) * "-LP"
        run_name += (interpolate) * "-noCensoring"

        output = op.join(
            find_derivative(input_path), "functional_connectivity", run_name
        )
    logging.info(f"Output will be save as derivatives in:\n\t{output}")

    covar_estimator, fc_kind, fc_label = get_fc_strategy(fc_estimator)
    logging.info(f"'{fc_label}' has been selected as connectivity metric")

    # By default, the timeseries and FC of all filenames in input will be computed
    if not overwrite:
        logging.debug("Looking for existing timeseries ...")
        all_missing_ts, all_existing_ts = check_existing_output(
            output,
            all_filenames,
            return_existing=True,
            patterns=TIMESERIES_PATTERN,
            **TIMESERIES_FILLS,
        )

        logging.info(f"{len(all_missing_ts)} files are missing timeseries.")
        logging.debug("Looking for existing fc matrices ...")
        missing_only_fc = check_existing_output(
            output, all_existing_ts, patterns=FC_PATTERN, meas=fc_label, **FC_FILLS
        )
        logging.info(
            f"{len(all_missing_ts + missing_only_fc)} files are missing FC matrices."
        )
        existing_timeseries = load_timeseries(missing_only_fc, output)
    else:
        missing_only_fc = []
        existing_timeseries = []
        all_missing_ts = all_filenames.copy()

    separated_missing_ts = [
        [file for file in file_group if file in all_missing_ts]
        for file_group in func_filenames
    ]
    sorted_missing_ts = list(chain.from_iterable(separated_missing_ts))
    missing_something = sorted_missing_ts + missing_only_fc

    time_series = []
    all_confounds = []
    all_sample_masks = []
    for filenames_to_ts, t_r in zip(separated_missing_ts, t_r_list):
        ts, conf, mask = extract_and_denoise_timeseries(
            filenames_to_ts,
            atlas_filename,
            verbose=nilearn_verbose,
            t_r=t_r,
            low_pass=low_pass,
            denoising_strategy=denoising_strategy,
            motion=motion,
            fd_threshold=fd_threshold,
            std_dvars_threshold=std_dvars_threshold,
            scrub=scrub,
            interpolate=interpolate,
            output=output,
        )
        time_series += ts
        all_confounds += conf
        all_sample_masks += mask

    # Saving aggregated/denoised timeseries and visual reports
    if len(time_series):
        logging.info("Saving denoised timeseries ...")
        os.makedirs(output, exist_ok=True)
        save_output(
            time_series,
            sorted_missing_ts,
            output,
            patterns=TIMESERIES_PATTERN,
            **TIMESERIES_FILLS,
        )

        for individual_time_serie, confounds, filename in zip(
            time_series, all_confounds, sorted_missing_ts
        ):
            visual_report_timeserie(
                individual_time_serie,
                filename=filename,
                output=output,
                confounds=confounds,
                labels=atlas_labels,
                networks=atlas_network,
            )

    fc_matrices = compute_connectivity(
        time_series + existing_timeseries,
        estimator=covar_estimator,
        connectivity_kind=fc_kind,
    )

    # Compute duration of fMRI scans after censoring
    fMRI_duration_after_censoring = {}
    for filename, mask in zip(all_filenames, all_sample_masks):
        fMRI_duration_after_censoring[op.basename(filename)] = mask.shape[0] * t_r
        # mask.shape[0] indicates the number of volumes that are not censored
    with open(
        op.join(output, "fMRI_duration_after_censoring.csv"), "a", newline=""
    ) as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["filename", "duration"])  # Write header if file is empty
        for key, value in fMRI_duration_after_censoring.items():
            writer.writerow([key, value])

    # Saving FC matrices and visual reports
    if len(fc_matrices):
        logging.info("Saving connectivity matrices ...")
        save_output(
            fc_matrices,
            missing_something,
            output,
            patterns=FC_PATTERN,
            meas=fc_label,
            **FC_FILLS,
        )

        # Generate session-specific figures
        for individual_matrix, filename in zip(fc_matrices, missing_something):
            visual_report_fc(
                individual_matrix,
                filename=filename,
                output=output,
                labels=atlas_labels,
                meas=fc_label,
            )

    logging.info(
        f"Computation is done for {len(missing_something)} files out of the "
        f"{len(all_filenames)} provided."
    )

    if not len(missing_something):
        logging.warning("Nothing was computed. Use --overwrite to overwrite data.")
    logging.info("Functional connectivity finished successfully !")


if __name__ == "__main__":
    main()
