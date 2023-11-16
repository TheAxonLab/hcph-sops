from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import os
from typing import Tuple, Optional, Union, List
import numpy as np


def plot_pupil_size(
    samples: pd.DataFrame,
    eye: str = "right",
    notebook: bool = True,
    save: bool = False,
    path_save: str = ".",
    filename: str = "pupil_ts.png",
) -> Optional[None]:
    """
    Plots time series of pupil size.

    Parameters:
    - samples (pd.DataFrame): DataFrame containing eye tracking data.
    - eye (str): Specifies whether to plot for the "right" or "left" eye.
    - notebook (bool): If True, the plot is shown in the Jupyter notebook.
    - save (bool): If True, the plot is saved to a file.
    - path_save (str): Path to save the plot file.
    - filename (str): Name of the saved plot file.

    Returns:
    - None if notebook is True, else the path to the saved plot file.

    Example:
    ```python
    plot_pupil_size(samples, eye="left")
    ```
    """
    if eye == "right":
        samples.pa_right[samples.pa_right < 1] = np.nan
        plt.plot(samples["time"], samples["pa_right"])
    elif eye == "left":
        samples.pa_left[samples.pa_left < 1] = np.nan
        plt.plot(samples["time"], samples["pa_left"])
    else:
        print("Invalid eye argument")

    plt.xlabel("timestamp [ms]")
    plt.ylabel("pupil area [pixels]")

    if notebook:
        plt.show()
        return None

    if save:
        plt.savefig(os.path.join(path_save, filename))
        return os.path.join(path_save, filename)

    return None


def plot_coordinates_ts(
    samples: pd.DataFrame,
    eye: str = "right",
    screen_resolution: Tuple[int, int] = (800, 600),
    notebook: bool = True,
    save: bool = False,
    path_save: str = ".",
    filename: str = "coordinates_ts.png",
) -> Optional[None]:
    """
    Plots time series of eye coordinates.

    Parameters:
    - samples (pd.DataFrame): DataFrame containing eye tracking data.
    - eye (str): Specifies whether to plot for the "right" or "left" eye.
    - screen_resolution (Tuple[int, int]): Screen resolution (width, height).
    - notebook (bool): If True, the plot is shown in the Jupyter notebook.
    - save (bool): If True, the plot is saved to a file.
    - path_save (str): Path to save the plot file.
    - filename (str): Name of the saved plot file.

    Returns:
    - None if notebook is True, else the path to the saved plot file.

    Example:
    ```python
    plot_coordinates_ts(samples, eye="left", screen_resolution=(800, 600))
    ```
    """
    if eye == "right":
        samples.gx_right[
            (samples.gx_right < 0) | (samples.gx_right > screen_resolution[0])
        ] = np.nan
        samples.gy_right[
            (samples.gy_right < 0) | (samples.gy_right > screen_resolution[1])
        ] = np.nan

        fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

        axs[0].plot(samples["time"], samples["gx_right"], label="gx_right")
        axs[0].set_ylabel("gx_right")
        axs[1].plot(samples["time"], samples["gy_right"], label="gy_right")
        axs[1].set_xlabel("timestamp [ms]")
        axs[1].set_ylabel("pupil area [pixels]")
        axs[0].set_xlim(samples["time"].iloc[0])

    elif eye == "left":
        samples.gx_left[
            (samples.gx_left < 0) | (samples.gx_left > screen_resolution[0])
        ] = np.nan
        samples.gy_left[
            (samples.gy_left < 0) | (samples.gy_left > screen_resolution[1])
        ] = np.nan

        fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

        axs[0].plot(samples["time"], samples["gx_left"], label="gx_left")
        axs[0].set_ylabel("gx_left")
        axs[1].plot(samples["time"], samples["gy_left"], label="gy_left")
        axs[1].set_xlabel("timestamp [ms]")
        axs[1].set_ylabel("pupil area [pixels]")
        axs[0].set_xlim(samples["time"].iloc[0])

    else:
        print("Invalid eye argument")

    if notebook:
        plt.show()
        return None

    if save:
        plt.savefig(os.path.join(path_save, filename))
        return os.path.join(path_save, filename)

    return None


def plot_heatmap_coordinate_density(
    samples: pd.DataFrame,
    eye: str = "right",
    notebook: bool = True,
    save: bool = False,
    path_save: str = ".",
    filename: str = "heatmap.png",
    screen_resolution: Tuple[int, int] = (800, 600),
) -> Optional[None]:
    """
    Plots a 2D density heatmap for eye tracking coordinates.

    Parameters:
    - samples (pd.DataFrame): DataFrame containing eye tracking data.
    - eye (str): Specifies whether to plot for the "right" or "left" eye.
    - notebook (bool): If True, the plot is shown in the Jupyter notebook.
    - save (bool): If True, the plot is saved to a file.
    - path_save (str): Path to save the plot file.
    - filename (str): Name of the saved plot file.
    - screen_resolution (Tuple[int, int]): Tuple specifying the screen resolution (width, height).

    Returns:
    - None if notebook is True, else the path to the saved plot file.

    Example:
    ```python
    plot_heatmap_coordinate_density(samples, eye="left", screen_resolution=(1024, 768))
    ```
    """
    plt.rcParams["figure.figsize"] = [10, 6]
    cmap = sns.color_palette("coolwarm", as_cmap=True)

    if eye == "right":
        filtered_samples = samples[
            (samples["gx_right"] >= 0)
            & (samples["gx_right"] <= screen_resolution[0])
            & (samples["gy_right"] >= 0)
            & (samples["gy_right"] <= screen_resolution[1])
        ]

        sns.kdeplot(
            data=filtered_samples,
            x="gx_right",
            y="gy_right",
            cmap=cmap,
            fill=True,
            cbar=True,
            thresh=0,
        )

        plt.xlabel("right eye x coordinate [pixels]")
        plt.ylabel("right eye y coordinate [pixels]")

    elif eye == "left":
        filtered_samples = samples[
            (samples["gx_left"] >= 0)
            & (samples["gx_left"] <= screen_resolution[0])
            & (samples["gy_left"] >= 0)
            & (samples["gy_left"] <= screen_resolution[1])
        ]

        sns.kdeplot(
            data=filtered_samples,
            x="gx_left",
            y="gy_left",
            cmap=cmap,
            fill=True,
            cbar=True,
            thresh=0,
        )

        plt.xlabel("left eye x coordinate [pixels]")
        plt.ylabel("left eye y coordinate [pixels]")

    else:
        print("Invalid eye argument")

    plt.gca().invert_yaxis()
    plt.xlim(0, screen_resolution[0])
    plt.ylim(0, screen_resolution[1])

    if notebook:
        plt.show()
        return None

    if save:
        plt.savefig(os.path.join(path_save, filename))
        return os.path.join(path_save, filename)

    return None


def plot_heatmap_coordinate_histo(
    samples: pd.DataFrame,
    eye: str = "right",
    notebook: bool = True,
    save: bool = False,
    path_save: str = ".",
    filename: str = "heatmap.png",
    screen_resolution: Tuple[int, int] = (800, 600),
    bins: int = 100,
) -> Optional[None]:
    """
    Plots a 2D histogram for eye tracking coordinates.

    Parameters:
    - samples (pd.DataFrame): DataFrame containing eye tracking data.
    - eye (str): Specifies whether to plot for the "right" or "left" eye.
    - notebook (bool): If True, the plot is shown in the Jupyter notebook.
    - save (bool): If True, the plot is saved to a file.
    - path_save (str): Path to save the plot file.
    - filename (str): Name of the saved plot file.
    - screen_resolution (Tuple[int, int]): Tuple specifying the screen resolution (width, height).
    - bins (int): Number of bins for the histogram.

    Returns:
    - None if notebook is True, else the path to the saved plot file.

    Example:
    ```python
    plot_heatmap_coordinate_histo(samples, eye="left", screen_resolution=(1024, 768), bins=50)
    ```
    """
    plt.rcParams["figure.figsize"] = [10, 6]
    plt.figure(figsize=(10, 6))
    cmap = sns.color_palette("coolwarm", as_cmap=True)

    if eye == "right":
        filtered_samples = samples[
            (samples["gx_right"] >= 0)
            & (samples["gx_right"] <= screen_resolution[0])
            & (samples["gy_right"] >= 0)
            & (samples["gy_right"] <= screen_resolution[1])
        ]

        plt.hist2d(
            filtered_samples["gx_right"],
            filtered_samples["gy_right"],
            range=[[0, screen_resolution[0]], [0, screen_resolution[1]]],
            bins=bins,
            cmap=cmap,
        )

        plt.xlabel("right eye x coordinate [pixels]")
        plt.ylabel("right eye y coordinate [pixels]")

    elif eye == "left":
        filtered_samples = samples[
            (samples["gx_left"] >= 0)
            & (samples["gx_left"] <= screen_resolution[0])
            & (samples["gy_left"] >= 0)
            & (samples["gy_left"] <= screen_resolution[1])
        ]

        plt.hist2d(
            filtered_samples["gx_left"],
            filtered_samples["gy_left"],
            range=[[0, screen_resolution[0]], [0, screen_resolution[1]]],
            bins=bins,
            cmap=cmap,
        )

        plt.xlabel("left eye x coordinate [pixels]")
        plt.ylabel("left eye y coordinate [pixels]")

    else:
        print("Invalid eye argument")

    plt.gca().invert_yaxis()
    plt.xlim(0, screen_resolution[0])
    plt.ylim(0, screen_resolution[1])

    if notebook:
        plt.show()
        return None

    if save:
        plt.savefig(os.path.join(path_save, filename))
        return os.path.join(path_save, filename)

    return None


def plot_delta(
    events: pd.DataFrame,
    save: Optional[bool] = False,
    path_save: Optional[str] = ".",
    filename: Optional[str] = "blink_durations.png",
    notebook: Optional[bool] = True,
) -> None:
    """
    Plot the distribution of blink durations.

    Parameters:
    - events: DataFrame containing blink events with 'start', 'end', and 'blink' columns.
    - save: Whether to save the plot as an image (default is False).
    - path_save: Path to the directory where the image will be saved (default is current directory).
    - filename: Name of the saved image file (default is "blink_durations.png").
    - notebook: If True, the plot will be displayed in a Jupyter notebook (default is True).

    Returns:
    - None (displays the plot or saves it).
    """
    blinks = events[events["blink"] == True]
    blinks["duration"] = blinks["end"] - blinks["start"]
    plt.figure(figsize=(10, 6))
    plt.plot(blinks["duration"])
    plt.title("Blink Durations Over Time")
    plt.xlabel("Time of Onset (ms)")
    plt.ylabel("Blinks Duration (ms)")
    if notebook:
        plt.show()
    if save:
        plt.savefig(f"{path_save}/{filename}")
