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
""" Python module for functional connectivity visual reports """

import logging
import os
import os.path as op
from typing import Optional, Union

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
from nireports.assembler.report import Report
from nilearn.plotting import plot_design_matrix, plot_matrix
from scipy.stats import pearsonr, ks_2samp
from time import strftime
from uuid import uuid4

from load_save import get_bids_savename


FIGURE_PATTERN: list = [
    "sub-{subject}/figures/sub-{subject}[_ses-{session}]"
    "[_task-{task}][_meas-{meas}][_desc-{desc}]"
    "_{suffix}{extension}",
    "sub-{subject}/figures/sub-{subject}[_ses-{session}]"
    "[_task-{task}][_desc-{desc}]_{suffix}{extension}",
]
FIGURE_FILLS: dict = {"extension": "png"}

TS_FIGURE_SIZE: tuple = (50, 25)
FC_FIGURE_SIZE: tuple = (70, 45)
LABELSIZE: int = 42
NETWORK_CMAP: str = "turbo"
N_PERMUTATION: int = 10000
ALPHA = 0.05
PERCENT_MATCH_CUT_OFF = 95


def plot_timeseries_carpet(
    timeseries: np.ndarray,
    labels: Optional[Union[list[str], np.ndarray]] = None,
    networks: Optional[pd.Series] = None,
) -> list[Axes]:
    """Plot the timeseries as a carpet plot.

    Parameters
    ----------
    timeseries : np.ndarray
        Timeseries to show
    labels : Optional[list[str]], optional
        Labels corresponding to the atlas ROIs, by default None
    networks : Optional[pd.Series], optional
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
    labels: Optional[Union[list[str], np.ndarray]] = None,
    networks: Optional[pd.Series] = None,
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
    networks : Optional[pd.Series], optional
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
                markerfacecolor=net_cmap(val - 1),  # type: ignore
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


def plot_interpolation(
    ts: np.ndarray, interpolated_ts: np.ndarray, filename: str, output: str
) -> None:
    """Plot the interpolated timeseries overlaid with the timeseries before
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
    labels: Optional[Union[list, np.ndarray]] = None,
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
        filename, patterns=FIGURE_PATTERN, desc="heatmap", **FIGURE_FILLS, **kwargs
    )
    _, ax = plt.subplots(figsize=FC_FIGURE_SIZE)

    plot_matrix(matrix, labels=list(labels), axes=ax, vmin=-1, vmax=1)  # type: ignore
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


def group_reportlet_fc_dist(
    fc_matrices: list[np.ndarray],
    output: str,
) -> None:
    """Plot and save the functional connectivity density distributions.

    Parameters
    ----------
    fc_matrices : list[np.ndarray]
        List of functional connectivity matrices
    output : str
        Path to the output directory
    """

    _, ax = plt.subplots(figsize=FC_FIGURE_SIZE)

    for fc_matrix in fc_matrices:
        sns.displot(
            fc_matrix,
            kind="kde",
            fill=True,
            linewidth=0.5,
            legend=False,
            palette="ch:s=.25,rot=-.25",
        )

    ax.tick_params(labelsize=LABELSIZE)

    # Ensure the labels are within the figure
    plt.tight_layout()

    savename = op.join("reportlets", "group_desc-fcdist_bold.svg")

    logging.debug("Saving functional connectivity distribution visual report at:")
    logging.debug(f"\t{op.join(output, savename)}")

    plt.savefig(op.join(output, savename))
    plt.close()


def group_reportlet_qc_fc(
    fc_matrices: list[np.ndarray],
    iqms_df: pd.DataFrame,
    output: str,
) -> dict:
    """Plot and save the QC-FC distributions.

    Parameters
    ----------
    fc_matrices : list[np.ndarray]
        List of functional connectivity matrices
    iqms_df : pd.Dataframe
        Dataframe containing the image quality metrics to correlate with
    output : str
        Path to the output directory
    """

    # Stack the list of arrays into a 3D matrix
    fc_matrices = np.stack(fc_matrices, axis=2)

    # Keep only upper triangle as the matrix is symmetric
    upper_triangle_indices = np.triu_indices(fc_matrices.shape[0], k=1)
    fc_matrices = fc_matrices[upper_triangle_indices]

    if fc_matrices.shape[1] != iqms_df.shape[0]:
        raise ValueError(
            "The number of functional connectivity matrices and IQMs do not match."
        )

    if fc_matrices.shape[1] == 1:
        raise ValueError(
            "We need at least two functional connectivity matrices to be able to compute its correlation with IQMs."
        )

    fig, axs = plt.subplots(1, 3, figsize=FC_FIGURE_SIZE)

    # Iterate over each IQM
    qc_fc_dict = dict()
    for i, iqm_column in enumerate(iqms_df.columns):
        # Create an empty list to store correlations for each edge
        qc_fcs = []

        # Iterate over each edge
        logging.debug("Compute QC-FC correlation for each edge.")
        for e in range(fc_matrices.shape[0]):
            qc_fc = np.corrcoef(fc_matrices[e, :], iqms_df[iqm_column])[0, 1]
            qc_fcs.append(qc_fc)

        # Create a density distribution plot for the current IQM
        logging.debug("Create the density distribution plot.")
        sns.kdeplot(
            qc_fcs, fill=True, label="QC-FC distribution", linewidth=3, ax=axs[i]
        )

        # Save the QC-FC distributions in a dictionary
        qc_fc_dict[iqm_column] = qc_fcs

        ## Permutation analyses
        logging.debug("Compute QC-FC distribution under the null hypothesis.")
        correlations_null = []
        for e in range(fc_matrices.shape[0]):
            for _ in range(N_PERMUTATION):
                permuted_fc = fc_matrices[
                    e, np.random.default_rng(seed=42).permutation(fc_matrices.shape[1])
                ]
                # Correlation under null hypothesis
                correlation = np.corrcoef(permuted_fc, iqms_df[iqm_column])[0, 1]
                correlations_null.append(correlation)

        # Create a density distribution plot for null distribution
        logging.debug("Create the density distribution plot for the null distribution.")
        sns.kdeplot(
            correlations_null,
            fill=False,
            color="red",
            label="Dist under null hypothesis",
            linewidth=3,
            linestyle="dashed",
            ax=axs[i],
        )
        plt.legend(fontsize=LABELSIZE + 2)

        # Compute percent match between the two distributions
        logging.debug("Compute percent match between the two distributions.")
        ks_statistic, _ = ks_2samp(qc_fcs, correlations_null)
        percent_match_ks = (1 - ks_statistic) * 100

        # Plot the box in red if the correlation is significant
        facecolor = "red" if percent_match_ks < PERCENT_MATCH_CUT_OFF else "grey"
        axs[i].text(
            0.08,
            0.9,
            f"QC-FC% = {percent_match_ks:.0f}",
            fontsize=LABELSIZE - 2,
            bbox=dict(facecolor=facecolor, alpha=0.4, boxstyle="round,pad=0.5"),
            transform=axs[i].transAxes,
        )
        axs[i].tick_params(labelsize=LABELSIZE)
        axs[i].set_title(iqm_column, fontsize=LABELSIZE + 2)

    # Turn off individual plot y-labels
    for ax in axs:
        ax.set_ylabel("")

    fig.supylabel("Density", fontsize=LABELSIZE + 2)
    fig.suptitle("QC-FC correlation distributions", fontsize=LABELSIZE + 4)

    savename = op.join("reportlets", "group_desc-qcfc_bold.svg")

    logging.debug("Saving QC-FC visual report at:")
    logging.debug(f"\t{op.join(output, savename)}")

    plt.savefig(op.join(output, savename))
    plt.close()

    return qc_fc_dict


def compute_distance(atlas_path: str) -> np.array:
    """Compute the euclidean distance between the center of mass of the atlas regions.

    Parameters
    ----------
    atlas_path : str
        Path to the atlas Nifti
    Returns
    -------
    np.array
        Distance matrix
    """
    from scipy.ndimage.measurements import center_of_mass

    logging.debug("Compute distance matrix from atlas centers of mass")

    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    # Array to store the center of mass of each region
    centroids = np.zeros((atlas_data.shape[3], 3), dtype=float)
    for r in range(atlas_data.shape[3]):
        centroids[r, ...] = np.array(center_of_mass(atlas_data[..., r]))

    # Compute Euclidean distance matrix using broadcasting
    diff = centroids[:, np.newaxis, :] - centroids
    distance_matrix = np.sqrt(np.sum(diff**2, axis=-1))

    return distance_matrix


def group_reportlet_qc_fc_euclidean(
    qc_fc_dict: dict, atlas_path: str, output: str
) -> None:
    """Plot and save the correlations between QC-FC and euclidean distance.
    The euclidean distance is computed from the centers of mass of each region.

    Parameters
    ----------
    qc_fc_dict : dict
        Dictionary containing the qc-fc distribution over the edges for different IQMs.
    atlas_path : str
        Path to the atlas Nifti
    output : str
        Path to the output directory
    """
    d = compute_distance(atlas_path)
    # Keep only upper triangle as the matrix is symmetric
    upper_triangle_indices = np.triu_indices(d.shape[0], k=1)
    d = d[upper_triangle_indices]

    # Iterate over the IQMs
    fig, axs = plt.subplots(1, 3, figsize=FC_FIGURE_SIZE)
    for i, iqm in enumerate(qc_fc_dict.keys()):
        qc_fc = qc_fc_dict[iqm]

        logging.debug("Compute the correlation between QC-FC and euclidean distance.")
        correlation, p_value = pearsonr(qc_fc, d)

        # Plot the box in red if the correlation is significant
        facecolor = "red" if p_value < ALPHA else "grey"
        axs[i].text(
            0.15,
            0.97,
            f"Correlation = {correlation:.2f}, p-value = {p_value:.4f}",
            fontsize=LABELSIZE - 2,
            bbox=dict(facecolor=facecolor, alpha=0.4, boxstyle="round,pad=0.5"),
            transform=axs[i].transAxes,
        )
        axs[i].scatter(qc_fc, d)

        # Plot trend line
        axs[i].plot(
            np.unique(qc_fc),
            np.poly1d(np.polyfit(qc_fc, d, 1))(np.unique(qc_fc)),
            "r-",
            linewidth=3,
        )
        axs[i].tick_params(labelsize=LABELSIZE)
        axs[i].set_title(iqm, fontsize=LABELSIZE + 2)

    fig.suptitle(
        "Dependence between euclidean distance and QC-FC", fontsize=LABELSIZE + 4
    )
    fig.supxlabel("QC-FC correlation of edge between nodes", fontsize=LABELSIZE + 2)
    fig.supylabel("Euclidean distance separating nodes", fontsize=LABELSIZE + 2)
    # Ensure the labels are within the figure
    # plt.tight_layout()

    savename = op.join("reportlets", "group_desc-qcfcvseuclidean_bold.svg")

    logging.debug("Saving QC-FC vs euclidean distance visual report at:")
    logging.debug(f"\t{op.join(output, savename)}")

    plt.savefig(op.join(output, savename))
    plt.close()


def group_report(
    good_timepoints_df: pd.DataFrame,
    fc_matrices: list[np.ndarray],
    iqms_df: pd.DataFrame,
    atlas_filename: str,
    output: str,
) -> None:
    """Generate a group report."""

    # Generate each reportlets
    group_reportlet_fc_dist(fc_matrices, output)
    qc_fc_dict = group_reportlet_qc_fc(fc_matrices, iqms_df, output)
    group_reportlet_qc_fc_euclidean(qc_fc_dict, atlas_filename, output)

    # Assemble reportlets into a single HTML report
    logging.debug("Assemble the group report into a single HTML report.")

    run_uuid = "{}_{}".format(strftime("%Y%m%d-%H%M%S"), uuid4())
    robj = Report(
        output,
        run_uuid,
        out_filename="group_report.html",
        bootstrap_file=op.join("data", "reports-spec.yml"),
    )
    robj.generate_report()
