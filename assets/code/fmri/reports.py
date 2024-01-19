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
import numpy as np
from pandas import Series
from matplotlib.axes import Axes
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
from nilearn.plotting import plot_design_matrix, plot_matrix

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
FC_FIGURE_SIZE: tuple = (50, 45)
LABELSIZE: int = 22
NETWORK_CMAP: str = "turbo"


def plot_timeseries_carpet(
    timeseries: np.ndarray,
    labels: Optional[Union[list[str], np.ndarray]] = None,
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
    labels: Optional[Union[list[str], np.ndarray]] = None,
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
