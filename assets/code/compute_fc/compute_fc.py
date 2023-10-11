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
""" Python script to denoise and aggregate timeseries and, using the latter, compute
functional connectivity matrices from BIDS derivatives (e.g. fmriprep).

Run as (see 'python compute_fc.py -h' for options):

    python compute_fc.py path_to_BIDS_derivatives

In the context of HCPh (pilot), it would be:

    python compute_fc.py /data/datasets/hcph-pilot/derivatives/fmriprep-23.1.4/
"""

import argparse
import logging
import os
import os.path as op
from collections import defaultdict
from itertools import chain
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from bids import BIDSLayout
from bids.layout import parse_file_entities
from bids.layout.writing import build_path
from matplotlib.axes import Axes
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
from nibabel import loadsave
from nilearn_patcher import MultiNiftiMapsMasker as MultiNiftiMapsMasker_patched
from pandas import Series
from sklearn.covariance import GraphicalLassoCV, LedoitWolf

from nilearn._utils import stringify_path
from nilearn.connectome import ConnectivityMeasure, vec_to_sym_matrix
from nilearn.datasets import fetch_atlas_difumo
from nilearn.interfaces.fmriprep import load_confounds
from nilearn.interfaces.fmriprep.load_confounds import _load_single_confounds_file
from nilearn.maskers import MultiNiftiMapsMasker
from nilearn.plotting import plot_design_matrix, plot_matrix
from nilearn.signal import _handle_scrubbed_volumes, _sanitize_confounds, clean

FC_PATTERN: list = [
    "sub-{subject}[/ses-{session}]/func/sub-{subject}"
    "[_ses-{session}][_task-{task}][_meas-{meas}]"
    "_{suffix}{extension}"
]
FC_FILLS: dict = {"suffix": "relmat", "extension": ".tsv"}
TIMESERIES_PATTERN: list = [
    "sub-{subject}[/ses-{session}]/func/sub-{subject}"
    "[_ses-{session}][_task-{task}][_desc-{desc}]"
    "_{suffix}{extension}"
]
TIMESERIES_FILLS: dict = {"desc": "denoised", "extension": ".tsv"}
FIGURE_PATTERN: list = [
    "sub-{subject}/figures/sub-{subject}[_ses-{session}]"
    "[_task-{task}][_meas-{meas}][_desc-{desc}]"
    "_{suffix}{extension}",
    "sub-{subject}/figures/sub-{subject}[_ses-{session}]"
    "[_task-{task}][_desc-{desc}]_{suffix}{extension}",
]
FIGURE_FILLS: dict = {"extension": "png"}
CONFOUND_PATTERN: list = [
    "sub-{subject}[_ses-{session}][_task-{task}][_part-{part}][_desc-{desc}]"
    "_{suffix}{extension}"
]
CONFOUND_FILLS: dict = {"desc": "confounds", "suffix": "timeseries", "extension": "tsv"}

DENOISING_STRATEGY: list = ["high_pass", "motion", "scrub"]

TS_FIGURE_SIZE: tuple = (50, 25)
FC_FIGURE_SIZE: tuple = (50, 45)
LABELSIZE: int = 22
NETWORK_MAPPING: str = "yeo_networks7"  # Also yeo_networks17
NETWORK_CMAP: str = "turbo"


def get_arguments() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="""Compute functional connectivity matrices from fmriprep
                    output directory.""",
    )

    # Input/Output arguments and options
    parser.add_argument("data_dir", help="BIDS dataset or derivatives with data")
    parser.add_argument(
        "--no-save",
        action="store_false",
        default=True,
        help="disable saving of the output",
    )
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
        default=[],
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
        help="standardised DVAR threshold",
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


def separate_by_similar_values(
    input_list: list, external_value: Optional[list] = None
) -> dict:
    """This returns elements of `input_list` with similar values (optionally set by
    `external_value`) separated into sub-lists.

    Parameters
    ----------
    input_list : list
        List to be separated.
    external_value : Optional[list], optional
        Values corresponding to the elements of `input_list`, by default None

    Returns
    -------
    dict
        Dictionnary where each entry is a list of elements that have similar values and
        the keys are the value for each list.
    """
    if external_value is None:
        external_value = input_list

    data_by_value = defaultdict(list)

    for val, data in zip(external_value, input_list):
        data_by_value[val].append(data)
    return data_by_value


def get_func_filenames_bids(
    paths_to_func_dir: str,
    task_filter: list = [],
    ses_filter: list = [],
    run_filter: list = [],
) -> tuple[list[list[str]], list[float]]:
    """Return the BIDS functional imaging files matching the specified task and session
    filters as well as the first (if multiple) unique repetition time (TR).

    Parameters
    ----------
    paths_to_func_dir : str
        Path to the BIDS (usually derivatives) directory
    task_filter : list, optional
        List of task name(s) to consider, by default []
    ses_filter : list, optional
        List of session name(s) to consider, by default []
    run_filter : list, optional
        List of run(s) to consider, by default []

    Returns
    -------
    tuple[list[list[str]], list[float]]
        Returns two lists with: a list of sorted filenames and a list of TRs.
    """
    logging.debug("Using BIDS to find functional files...")

    layout = BIDSLayout(
        paths_to_func_dir,
        validate=False,
    )

    all_derivatives = layout.get(
        scope="all",
        return_type="file",
        extension=["nii.gz", "gz"],
        suffix="bold",
        task=task_filter,
        session=ses_filter,
        run=run_filter,
    )

    affines = []
    for file in all_derivatives:
        affines.append(loadsave.load(file).affine)

    similar_fov_dict = separate_by_similar_values(
        all_derivatives, np.array(affines)[:, 0, 0]
    )
    if len(similar_fov_dict) > 1:
        logging.warning(
            f"{len(similar_fov_dict)} different FoV found ! "
            "Files with similar FoV will be computed together. "
            "Computation time may increase."
        )

    separated_files = []
    separated_trs = []
    for file_group in similar_fov_dict.values():
        t_rs = []
        for file in file_group:
            t_rs.append(layout.get_metadata(file)["RepetitionTime"])

        similar_tr_dict = separate_by_similar_values(file_group, t_rs)
        separated_files += list(similar_tr_dict.values())
        separated_trs += list(similar_tr_dict.keys())

        if len(similar_tr_dict) > 1:
            logging.warning(
                "Multiple TR values found ! "
                "Files with similar TR will be computed together. "
                "Computation time may increase."
            )

    return separated_files, separated_trs


def get_bids_savename(filename: str, patterns: list = FC_PATTERN, **kwargs) -> str:
    """Return the BIDS filename following the specified patterns and modifying the
    entities from the keywords arguments.

    Parameters
    ----------
    filename : str
        Name of the original BIDS file
    patterns : list, optional
        Patterns for the output file, by default FC_PATTERN

    Returns
    -------
    str
        BIDS output filename.
    """
    entity = parse_file_entities(filename)

    for key, value in kwargs.items():
        entity[key] = value

    bids_savename = build_path(entity, patterns)

    return bids_savename


def get_atlas_data(atlas_name: str = "DiFuMo", **kwargs) -> dict:
    """Fetch the specifies atlas filename and data.

    Parameters
    ----------
    atlas_name : str, optional
        Name of the atlas to fetch, by default "DiFuMo"

    Returns
    -------
    dict
        Dictionnary with keys "maps" (filename) and "labels" (ROI labels).
    """
    logging.info("Fetching the DiFuMo atlas ...")

    if kwargs["dimension"] not in [64, 128, 512]:
        logging.warning(
            "Dimension for DiFuMo atlas is different from 64, 128 or 512 ! Are you"
            "certain you want to deviate from those optimized modes? "
        )

    return fetch_atlas_difumo(legacy_format=False, **kwargs)


def find_derivative(path: str, derivatives_name: str = "derivatives") -> str:
    """Find the corresponding BIDS derivative folder (if existing, otherwise it will be
    created).

    Parameters
    ----------
    path : str
        Path to the BIDS (usually derivatives) dataset.
    derivatives_name : str, optional
        Name of the derivatives folder, by default "derivatives"

    Returns
    -------
    str
        Absolute path to the derivative folder.
    """
    splitted_path = path.split("/")
    if derivatives_name in splitted_path:
        while splitted_path[-1] != derivatives_name:
            splitted_path.pop()
        return "/".join(splitted_path)
    logging.warning(
        f'"{derivatives_name}" could not be found on path - '
        f'creating at: {op.join(path, derivatives_name)}"'
    )
    return op.join(path, derivatives_name)


def check_existing_output(
    output: str, func_filename: list[str], return_existing: bool = False, **kwargs
) -> tuple[list[str], list[str]]:
    """Check for existing output.

    Parameters
    ----------
    output : str
        Path to the output directory
    func_filename : list[str]
        Original file to be computed in the futur
    return_existing : bool, optional
        Condition to return a boolean filter with True for existing data, by default
        False

    Returns
    -------
    tuple[list[str], list[str]]
        Boolean filter with True for missing data (optionally, a second filter with
        existing data)
    """

    missing_data_filter = [
        not op.exists(op.join(output, get_bids_savename(filename, **kwargs)))
        for filename in func_filename
    ]

    missing_data = np.array(func_filename)[missing_data_filter]
    logging.debug(
        f"\t{sum(missing_data_filter)} missing data found for files:"
        "\n\t" + "\n\t".join(missing_data)
    )

    if return_existing:
        existing_data = np.array(func_filename)[
            [not fltr for fltr in missing_data_filter]
        ]
        return missing_data.tolist(), existing_data.tolist()
    return missing_data.tolist()


def load_timeseries(func_filename: list[str], output: str) -> list[np.ndarray]:
    """Load existing timeseries from .csv files.

    Parameters
    ----------
    func_filename : list[str]
        List of timeseries filenames.
    output : str
        Path to the output folder.

    Returns
    -------
    list[np.ndarray]
        List of loaded timeseries.
    """
    if len(func_filename):
        logging.info(f"Loading existing timeseries for {len(func_filename)} files ...")

    loaded_ts = []
    for filename in func_filename:
        path_to_ts = get_bids_savename(
            filename, patterns=TIMESERIES_PATTERN, **TIMESERIES_FILLS
        )
        logging.debug(f"\t{op.join(output, path_to_ts)}")
        loaded_ts.append(
            np.genfromtxt(op.join(output, path_to_ts), float, delimiter="\t")
        )

    return loaded_ts


def get_confounds_manually(func_filename: list[str], **kwargs) -> tuple[list, list]:
    """Manually load the fMRIPrep confounds.

    Parameters
    ----------
    func_filename : list[str]
        List of BIDS functional filenames

    Returns
    -------
    tuple[list, list]
        Two lists, one with the loaded confounds (for each input file) and one with the
        corresponding sample mask.
    """
    confounds, sample_mask = [], []

    for filename in func_filename:
        dir_name = op.dirname(filename)
        confounds_file = op.join(
            dir_name,
            get_bids_savename(filename, patterns=CONFOUND_PATTERN, **CONFOUND_FILLS),
        )

        # confounds_json_file = load_confounds._get_json(confounds_file)
        confounds_json_file = confounds_file.replace("tsv", "json")
        individual_sm, individual_conf = _load_single_confounds_file(
            confounds_file=confounds_file,
            confounds_json_file=confounds_json_file,
            **kwargs,
        )
        confounds.append(individual_conf)
        sample_mask.append(individual_sm)

    return confounds, sample_mask


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
        List of confounds (usually from nilearn.interface.fmriprep.load_confouds),
        by default None
    sample_mask : Optional[list], optional
        List of sample masks (usually from nilearn.interface.fmriprep.load_confouds),
        by default None

    Returns
    -------
    list[np.ndarray]
        List of extracted and denoised timerseries
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
        List of confounds (usually from nilearn.interface.fmriprep.load_confouds).
    sample_mask : list
        List of sample_masks (usually from nilearn.interface.fmriprep.load_confouds).
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


def plot_interpolation(
    ts: np.ndarray, interpolated_ts: np.ndarray, filename: str, output: str
) -> None:
    """Plot the interpolated timeseries overlayed with the timeseries before
    interpolation.

    Parameters
    ----------
    ts : np.ndarray
        Timeseries before interpolation
    interpolated_ts : np.ndarray
        Interpolated timeseries
    filename : str
        Name of the corresponding BIDS functional file
    output : str
        Path to the output directory
    """
    ax = plot_timeseries_signal(ts)
    ax = plot_timeseries_signal(interpolated_ts, color="tab:red", ax=ax, linewidth=2)

    legend_elements = [
        Line2D([0], [0], color=col, label=lab)
        for lab, col in zip(["Timeserie", "Interpolation"], ["tab:blue", "tab:red"])
    ]

    ax.legend(
        handles=legend_elements,
        ncol=2,
        loc="upper left",
        bbox_to_anchor=(0, 1.04),
        fontsize=LABELSIZE,
    )

    interpolate_saveloc = get_bids_savename(
        filename,
        patterns=FIGURE_PATTERN,
        desc="interpolatedtimeseries",
        **FIGURE_FILLS,
    )

    logging.debug("Saving interpolated timeseries visual report at:")
    logging.debug(f"\t{op.join(output, interpolate_saveloc)}")
    os.makedirs(op.join(output, op.dirname(interpolate_saveloc)), exist_ok=True)
    plt.savefig(op.join(output, interpolate_saveloc))
    plt.close()


def extract_and_denoise_timeseries(
    func_filename: list[str],
    atlas_filename: str,
    verbose: int = 2,
    interpolate: bool = False,
    low_pass: Optional[float] = None,
    t_r: Optional[float] = None,
    output: Optional[str] = None,
    **kwargs,
) -> tuple[list[np.ndarray], list]:
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
        return [], []

    logging.info(f"Extracting and denoising timeseries for {len(func_filename)} files.")
    logging.debug(f"Denoising strategy includes : {' '.join(DENOISING_STRATEGY)}")
    logging.debug(f"Denoising parameters are: {kwargs}")

    # There is currently a bug in nilearn that prevents "load_confounds" from finding
    # the confounds file if it contains any other BIDS entity than "ses" and "run".
    # It should be fixed in release 0.13.
    try:
        confounds, sample_mask = load_confounds(
            func_filename,
            demean=False,
            strategy=DENOISING_STRATEGY,
            motion="basic",
            **kwargs,
        )
    except ValueError as msg:
        if "Could not find associated confound file. " not in str(msg):
            raise

        logging.warning(
            "Nilearn could not find the confounds file (this is likely due to a"
            " bug in nilearn.interface.fmriprep.load_confouds that should be fixed in"
            " release 0.13, see nilearn issue #3792)."
        )
        logging.warning("Searching manually ...")

        confounds, sample_mask = get_confounds_manually(
            func_filename,
            demean=False,
            strategy=DENOISING_STRATEGY,
            motion="basic",
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

    return time_series, confounds


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


def plot_timeseries_carpet(
    timeseries: np.ndarray,
    labels: Optional[list[str]] = None,
    networks: Optional[Series] = None,
) -> list[Axes]:
    """Plot the timeseries as a carpet plot.

    Parameters
    ----------
    timeseries : np.ndarray
        Timeseries to show
    labels : Optional[list[str]], optional
        Labels corresponding to the atlas ROIs, by default None
    networks : Optional[Series], optional
        Networks of the atlas ROIs, by default None

    Returns
    -------
    list[Axes]
        Axes of the plot.
    """
    n_timepoints, n_area = timeseries.shape

    if labels is None:
        labels = np.arange(n_area)

    networks_provided = networks is not None

    sorting_index = np.arange(n_area)

    fig = plt.figure(figsize=TS_FIGURE_SIZE)
    gs = fig.add_gridspec(
        1,
        2,
        wspace=0,
        width_ratios=[0 + 0.005 * networks_provided, 1 - 0.005 * networks_provided],
    )
    ax_net, ax_carpet = gs.subplots()

    if networks_provided:
        networks_sorted = networks.sort_values()
        sorting_index = networks_sorted.index
        net_dict = {net: i + 1 for i, net in enumerate(networks_sorted.unique())}
        net_plot = np.array([[net_dict[net] for net in networks_sorted]])

        net_cmap = get_cmap(NETWORK_CMAP, len(net_dict))
        ax_net.imshow(net_plot.T, cmap=NETWORK_CMAP, aspect="auto")

        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                label=net,
                markerfacecolor=net_cmap(val - 1),
                markersize=15,
            )
            for net, val in net_dict.items()
        ]

        ax_carpet.legend(
            handles=legend_elements,
            ncol=len(net_dict),
            loc="upper left",
            bbox_to_anchor=(0, 1.04),
            fontsize=LABELSIZE,
        )

    image = ax_carpet.imshow(
        timeseries.T[sorting_index],
        cmap="binary_r",
        aspect="auto",
        interpolation="antialiased",
    )
    cbar = plt.colorbar(image, pad=0, aspect=40)
    cbar.ax.tick_params(labelsize=LABELSIZE)

    ax_net.set_yticks(np.arange(n_area))
    ax_net.set_yticklabels(labels)
    ax_net.tick_params(bottom=False, labelbottom=False, labelsize=LABELSIZE)
    ax_carpet.set_xlabel("time", fontsize=LABELSIZE)
    ax_carpet.tick_params(left=False, labelleft=False, labelsize=LABELSIZE)

    plt.subplots_adjust(right=1.11, left=0.151)

    return [ax_net, ax_carpet]


def plot_timeseries_signal(
    timeseries: np.ndarray,
    labels: Optional[list[str]] = None,
    networks: Optional[Series] = None,
    vert_scale: float = 5,
    margin_value: float = 0.01,
    color: str = "tab:blue",
    linewidth: float = 4,
    ax: Optional[Axes] = None,
) -> Axes:
    """Plot the timeseries as a signal plot.

    Parameters
    ----------
    timeseries : np.ndarray
        Timeseries to show
    labels : Optional[list[str]], optional
        Labels corresponding to the atlas ROIs, by default None
    networks : Optional[Series], optional
        Networks of the atlas ROIs, by default None
    vert_scale : float, optional
        Vertical space between each signal , by default 5
    margin_value : float, optional
        Plot margin, by default 0.01
    color : _type_, optional
        Default color of the line plots, by default "tab:blue"
    linewidth : float, optional
        Linewidth of the line plots, by default 4
    ax : Optional[Axes], optional
        Axes to draw on, by default None

    Returns
    -------
    Axes
        Axes of the plot.
    """
    n_timepoints, n_area = timeseries.shape

    if labels is None:
        labels = np.arange(n_area)

    networks_provided = networks is not None
    sorting_index = np.arange(n_area)
    colors = [color] * n_area

    if ax is None:
        _, ax = plt.subplots(figsize=TS_FIGURE_SIZE)

    if networks_provided:
        networks_sorted = networks.sort_values()
        sorting_index = networks_sorted.index
        net_dict = {net: i + 1 for i, net in enumerate(networks_sorted.unique())}
        net_plot = np.array([[net_dict[net] for net in networks_sorted]])

        net_cmap = get_cmap(NETWORK_CMAP, len(net_dict))

        colors = [net_cmap(i - 1) for i in net_plot][0]

        legend_elements = [
            Line2D(
                [0],
                [0],
                marker="s",
                color="w",
                label=net,
                markerfacecolor=net_cmap(val - 1),
                markersize=15,
            )
            for net, val in net_dict.items()
        ]

        ax.legend(
            handles=legend_elements,
            ncol=len(net_dict),
            loc="upper left",
            bbox_to_anchor=(0, 1.04),
            fontsize=LABELSIZE,
        )

    x_plot = np.arange(n_timepoints)
    for i, (roi_signal, col) in enumerate(zip(timeseries.T[sorting_index], colors)):
        ax.plot(x_plot, i * vert_scale + roi_signal, color=col, linewidth=linewidth)

    ax.set_yticks(np.arange(n_area) * vert_scale)
    ax.set_yticklabels(labels, fontsize=LABELSIZE)
    ax.set_xlabel("time", fontsize=LABELSIZE)

    ax.grid(visible=True, axis="y")
    ax.margins(x=margin_value, y=margin_value)

    return ax


def visual_report_timeserie(
    timeseries: np.ndarray,
    filename: str,
    output: str,
    confounds: Optional[np.ndarray] = None,
    **kwargs,
) -> None:
    """Plot and save the timeseries visual reports.

    Parameters
    ----------
    timeseries : np.ndarray
        Timeseries to show
    filename : str
        Original filename corresponding to the timeseries
    output : str
        Path to the output directory
    confounds : Optional[np.ndarray], optional
        Confounds to plot, by default None
    """
    # Plotting denoised and aggregated timeseries
    for plot_func, plot_desc in zip(
        [plot_timeseries_carpet, plot_timeseries_signal], ["carpetplot", "timeseries"]
    ):
        ts_saveloc = get_bids_savename(
            filename, patterns=FIGURE_PATTERN, desc=plot_desc, **FIGURE_FILLS
        )
        plot_func(timeseries, **kwargs)

        logging.debug("Saving timeseries visual report at:")
        logging.debug(f"\t{op.join(output, ts_saveloc)}")
        os.makedirs(op.join(output, op.dirname(ts_saveloc)), exist_ok=True)
        plt.savefig(op.join(output, ts_saveloc))
        plt.close()

    # Plotting confounds as a design matrix
    if confounds is not None:
        conf_saveloc = get_bids_savename(
            filename, patterns=FIGURE_PATTERN, desc="designmatrix", **FIGURE_FILLS
        )

        _, ax = plt.subplots(figsize=TS_FIGURE_SIZE)
        plot_design_matrix(confounds, ax=ax)
        logging.debug("Saving confounds visual report at:")
        logging.debug(f"\t{op.join(output, conf_saveloc)}")

        plt.savefig(op.join(output, conf_saveloc))
        plt.close()


def visual_report_fc(
    matrix: np.ndarray,
    filename: str,
    output: str,
    labels: Optional[list] = None,
    **kwargs,
) -> None:
    """Plot and save the functional connectivity visual reports.

    Parameters
    ----------
    matrix : np.ndarray
        Functional connectivity matrix
    filename : str
        Original filename corresponding to the FC matrix
    output : str
        Path to the output directory
    labels : Optional[list], optional
        Labels of the atlas ROIs, by default None
    """
    fc_saveloc = get_bids_savename(
        filename, patterns=FIGURE_PATTERN, desc="heatmap", **kwargs
    )
    _, ax = plt.subplots(figsize=FC_FIGURE_SIZE)

    plot_matrix(matrix, labels=list(labels), axes=ax, vmin=-1, vmax=1)
    ax.tick_params(labelsize=LABELSIZE)

    # Update the size of the colorbar labels
    cbar = ax.images[-1].colorbar
    cbar.ax.tick_params(labelsize=LABELSIZE)

    # Ensure the labels are within the figure
    plt.tight_layout()

    logging.debug("Saving functional connectivity matrices visual report at:")
    logging.debug(f"\t{op.join(output, fc_saveloc)}")

    plt.savefig(op.join(output, fc_saveloc))
    plt.close()


def save_output(
    data_list: list[np.ndarray],
    original_filenames: list[str],
    output: Optional[str] = None,
    **kwargs,
) -> None:
    """Save the output files.

    Parameters
    ----------
    data_list : list[np.ndarray]
        List of data arrays (usually timeseries or matrices)
    original_filenames : list[str]
        List of original filenames
    output : Optional[str], optional
        Path to the output directory, by default None
    """
    for data, filename in zip(data_list, original_filenames):
        path_to_save = get_bids_savename(filename, **kwargs)
        saveloc = op.join(output, path_to_save)
        logging.debug(f"Saving data of type {type(data)} to: {saveloc}")
        os.makedirs(op.dirname(saveloc), exist_ok=True)
        np.savetxt(saveloc, data, delimiter="\t")


def main():
    args = get_arguments()

    input_path = args.data_dir
    save = args.no_save
    output = args.output

    study_name = args.study_name

    ses_filter = args.ses
    task_filter = args.task
    run_filter = args.run
    overwrite = args.overwrite

    # denoise_only = args.denoise_only
    atlas_dimension = args.atlas_dimension
    low_pass = args.low_pass
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
    all_missing_ts = func_filenames.copy()
    existing_timeseries = []
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

    separated_missing_ts = [
        [file for file in file_group if file in all_missing_ts]
        for file_group in func_filenames
    ]
    sorted_missing_ts = list(chain.from_iterable(separated_missing_ts))
    missing_something = sorted_missing_ts + missing_only_fc

    time_series = []
    all_confounds = []
    for filenames_to_ts, t_r in zip(separated_missing_ts, t_r_list):
        ts, conf = extract_and_denoise_timeseries(
            filenames_to_ts,
            atlas_filename,
            verbose=nilearn_verbose,
            t_r=t_r,
            low_pass=low_pass,
            fd_threshold=fd_threshold,
            std_dvars_threshold=std_dvars_threshold,
            scrub=scrub,
            interpolate=interpolate,
            output=output,
        )
        time_series += ts
        all_confounds += conf

    # Saving aggregated/denoised timeseries and visual reports
    if save and len(time_series):
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

    # Saving FC matrices and visual reports
    if save and len(fc_matrices):
        logging.info("Saving connectivity matrices ...")
        save_output(
            fc_matrices,
            missing_something,
            output,
            patterns=FC_PATTERN,
            meas=fc_label,
            **FC_FILLS,
        )

        for individual_matrix, filename in zip(fc_matrices, missing_something):
            visual_report_fc(
                individual_matrix,
                filename=filename,
                output=output,
                labels=atlas_labels,
                meas=fc_label,
                **FIGURE_FILLS,
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
