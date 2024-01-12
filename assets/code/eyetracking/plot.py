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
from __future__ import annotations

from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from matplotlib.colors import ListedColormap
import matplotlib.image as mpimg

PLT_FIGURE_WIDTH = 16


def _non_linear_alpha(x, b=20, c=0.1):
    sigmoid_transition = 1 / (1 + np.exp(-b * (x - c)))
    return x + (1 - x) * sigmoid_transition * (1 / (1 + np.exp(-b * (x - c))))


def plot_heatmap_coordinate(
    data: pd.DataFrame,
    density: bool = False,
    cbar: bool = False,
    screen_size: Tuple[int, int] = (800, 600),
    background_image=None,
    ax=None,
) -> plt.Figure:
    """
    Plots a heatmap for eye tracking coordinates.

    Parameters
    ----------
    data : :obj:`pandas.DataFrame`
        The dataframe the plot will get data from.
    density : :obj:`bool`
        If `True`, a kernel density estimation is fit to show smooth frequencies.
    cbar : :obj:`bool`
        Plot a colorbar.
    background_image : :obj:`os.pathlike`
        Path to a background image that will be displayed behind the plot.

    Returns
    -------
    fig : :obj:`~matplotlib.pyplot.figure.Figure`
        The matplotlib figure handle

    """
    import seaborn as sns

    # Make the aspect ratio of the figure resemble the screen proportion
    if ax is None:
        plt.figure(
            figsize=(
                PLT_FIGURE_WIDTH,
                PLT_FIGURE_WIDTH * (1 - 0.2 * cbar) * screen_size[1] / screen_size[0],
            )
        )
        ax = plt.gca()

    clip = ((0, screen_size[0]), (0, screen_size[1]))

    if background_image:
        original_cmap = sns.color_palette("YlOrBr", as_cmap=True)
        cmap = original_cmap(np.arange(original_cmap.N))
        cmap[:, -1] = _non_linear_alpha(np.linspace(0, 1, original_cmap.N))
        cmap = ListedColormap(cmap)
        movie_background = mpimg.imread(background_image)
        extent = [0, screen_size[0], screen_size[1], 0]
        ax.imshow(movie_background, zorder=0, extent=extent, alpha=0.7)

    else:
        cmap = sns.color_palette("coolwarm", as_cmap=True)

    if density:
        sns.kdeplot(
            data=data,
            cmap=cmap,
            x="eye1_x_coordinate",
            y="eye1_y_coordinate",
            fill=True,
            cbar=cbar,
            clip=clip,
            thresh=0,
            ax=ax,
        )
    else:
        ax.hist2d(
            data["eye1_x_coordinate"],
            data["eye1_y_coordinate"],
            range=clip,
            bins=(screen_size[0] // 10, screen_size[1] // 10),
            cmap=cmap,
        )

    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("x coordinate [pixels]")
    ax.set_ylabel("y coordinate [pixels]")

    return ax
