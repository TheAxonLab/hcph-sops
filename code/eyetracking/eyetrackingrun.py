from pathlib import Path
import string
from typing import Optional, List, Tuple, Union
import numpy as np
import pandas as pd
from scipy.signal import fftconvolve
from pyedfread import edf, edfread
from typing import Optional
import re
import os
import json
import seaborn as sns
import matplotlib.pyplot as plt


class EyeTrackingRun:
    def __init__(
        self,
        session: int,
        task_name: str,
        participant: int,
        samples: pd.DataFrame,
        events: pd.DataFrame,
        messages: pd.DataFrame,
        message_first_trigger: str,
        screen_resolution: Tuple[int, int],
        messages_start_fixation: str = "",
        messages_stop_fixation: str = "",
        pe: str = "",
    ):
        self.session = session
        self.task_name = task_name
        self.participant = participant
        self.samples = samples
        self.events = events
        self.messages = messages
        self.message_first_trigger = message_first_trigger
        self.messages_start_fixation = messages_start_fixation
        self.messages_stop_fixation = messages_stop_fixation
        self.screen_resolution = screen_resolution
        self.pe = pe

    def get_calibration_positions(
        self, calibration_type: Optional[str] = None
    ) -> Optional[List[List[int]]]:
        if calibration_type and calibration_type.lower() == "hv9":
            positions = [
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2),
                ],
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2 * 0.17),
                ],
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2 * 0.83),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.12),
                    int(self.screen_resolution[1] / 2),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.88),
                    int(self.screen_resolution[1] / 2),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.12),
                    int(self.screen_resolution[1] / 2 * 0.17),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.88),
                    int(self.screen_resolution[1] / 2 * 0.17),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.12),
                    int(self.screen_resolution[1] / 2 * 0.83),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.88),
                    int(self.screen_resolution[1] / 2 * 0.83),
                ],
            ]
            return positions
        elif calibration_type and calibration_type.lower() == "hv5":
            positions = [
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2),
                ],
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2 * 0.17),
                ],
                [
                    int(self.screen_resolution[0] / 2),
                    int(self.screen_resolution[1] / 2 * 0.83),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.12),
                    int(self.screen_resolution[1] / 2),
                ],
                [
                    int(self.screen_resolution[0] / 2 * 0.88),
                    int(self.screen_resolution[1] / 2),
                ],
            ]
            return positions
        else:
            print("Invalid calibration type")
            return None

    def add_events(self) -> pd.DataFrame:
        """
        Update 'fixation', 'saccade', and 'blink' columns in the samples DataFrame based on events DataFrame.

        Returns:
        - Updated samples DataFrame.
        """
        self.samples["fixation"] = 0
        self.samples["saccade"] = 0
        self.samples["blink"] = 0

        for _, fixation_event in self.events[
            self.events["type"] == "fixation"
        ].iterrows():
            self.samples.loc[
                (self.samples["time"] >= fixation_event["start"])
                & (self.samples["time"] <= fixation_event["end"]),
                "fixation",
            ] = 1

        for _, saccade_event in self.events[
            self.events["type"] == "saccade"
        ].iterrows():
            self.samples.loc[
                (self.samples["time"] >= saccade_event["start"])
                & (self.samples["time"] <= saccade_event["end"]),
                "saccade",
            ] = 1

            if saccade_event["blink"] == 1:
                self.samples.loc[
                    (self.samples["time"] >= saccade_event["start"])
                    & (self.samples["time"] <= saccade_event["end"]),
                    "blink",
                ] = 1

        return self.samples

    def find_timestamp_message(self) -> Optional[int]:
        """
        Finds the first row in the DataFrame containing the specified message string and returns the 'trialid_time' as an integer.

        Returns:
            Optional[int]: The 'trialid_time' as an integer if the message is found; None if the message is not found.
        """
        message_row = self.messages[
            self.messages["trialid "].str.contains(
                self.message_first_trigger, case=False, regex=True
            )
        ].head(1)
        if not message_row.empty:
            return int(message_row["trialid_time"].iloc[0])
        else:
            return None

    def extract_calibration(
        self,
    ) -> Tuple[
        int,
        Optional[str],
        Optional[float],
        Optional[float],
        Optional[List[List[Union[int, int]]]],
    ]:
        """
        Extracts calibration information from the DataFrame of messages.

        Returns:
        Tuple[int, Optional[str], Optional[float], Optional[float], Optional[List[List[Union[int, int]]]]]:
            A tuple containing:
            - Calibration count (int),
            - Calibration type (str or None),
            - Average calibration error (float or None),
            - Maximum calibration error (float or None),
            - Calibration position (list of lists of integers or None).
        """

        row_error_value = self.messages[
            self.messages["trialid "].str.contains("ERROR", case=False, regex=True)
        ].head(1)

        if row_error_value.empty:
            calibration_count = 0
            print("No calibration information found.")
            return calibration_count, None, None, None, None
        else:
            calibration_count = 1
            error_message = row_error_value["trialid "].iloc[0]

            matches = re.findall(r"([-+]?\d*\.\d+|\d+)", error_message)
            average_calibration_error, max_calibration_error = (
                map(float, matches[1:3]) if len(matches) >= 2 else (None, None)
            )

            print("Calibration Count:", calibration_count)
            print("Average Calibration Error:", average_calibration_error)
            print("Maximum Calibration Error:", max_calibration_error)

            if "HV9" in error_message:
                calibration_type = "HV9"
                calibration_position = self.get_calibration_positions(calibration_type)
            else:
                calibration_type = None
                calibration_position = None

            return (
                calibration_count,
                calibration_type,
                average_calibration_error,
                max_calibration_error,
                calibration_position,
            )

    def extract_ET_parameters(
        self,
    ) -> Tuple[str, str, Optional[int], Optional[int], Optional[int], str]:
        """
        Extracts eye tracking parameters from the given samples and messages dataframes.

        Returns:
        Tuple[str, str, Optional[int], Optional[int], Optional[int], str]: A tuple containing the extracted parameters:
            - Recorded eye ('both', 'right', 'left', or 'unknown').
            - Eye tracking method.
            - Sampling frequency (optional, None if not available).
            - Pupil threshold (optional, None if not available).
            - CR threshold (optional, None if not available).
            - Pupil fitting method ('ellipse' or 'center-of-mass').
        """

        row_start = self.messages[
            self.messages["trialid "].str.contains("RECORD", case=False, regex=True)
        ].head(1)
        start_text = row_start["trialid "].iloc[0]
        match_start = re.search(r"RECORD (\w+) (\d+) (\d+) (\d+) (\w+)", start_text)

        if match_start:
            eye_tracking_method, sampling_frequency, _, _,r_eye = match_start.groups()
            sampling_frequency = int(sampling_frequency)
            if r_eye=='R':
                recorded_eye="right"
            elif r_eye=='L':
                recorded_eye = "right"
            elif r_eye=='RL':
                recorded_eye = "both"
            else:
                recorded_eye = "unknown"

            print("recorded eye:",recorded_eye)
            print("Eye Tracking Method:", eye_tracking_method)
            print("Sampling Frequency:", sampling_frequency)
        else:
            eye_tracking_method = "unknown"
            sampling_frequency = None
            print("Eye Tracking Method: unknown")
            print("Sampling Frequency: Not available")

        row_thresholds = self.messages[
            self.messages["trialid "].str.contains("THRESHOLDS", case=False, regex=True)
        ].head(1)
        thresholds_text = row_thresholds["trialid "].iloc[0]
        print(thresholds_text, "threshold")
        match_thresholds = re.search(r"THRESHOLDS (\w+) (\d+) (\d+)", thresholds_text)

        if match_thresholds:
            _, pupil_threshold, CR_threshold = match_thresholds.groups()
            pupil_threshold = int(pupil_threshold)
            CR_threshold = int(CR_threshold)
            print("Pupil Threshold:", pupil_threshold)
            print("CR Threshold:", CR_threshold)
        else:
            pupil_threshold = None
            CR_threshold = None
            print("Pupil Threshold: Not available")
            print("CR Threshold: Not available")

        row_fit_param = self.messages[
            self.messages["trialid "].str.contains("ELCL_PROC", case=False, regex=True)
        ].head(1)
        fit_param_text = row_fit_param["trialid "].iloc[0]

        if "ELLIPSE" in fit_param_text:
            pupil_fit_method = "ellipse"
        else:
            pupil_fit_method = "center-of-mass"

        print("Pupil Fitting Method:", pupil_fit_method)

        return (
            recorded_eye,
            eye_tracking_method,
            sampling_frequency,
            pupil_threshold,
            CR_threshold,
            pupil_fit_method,
        )

    def extract_header(self) -> List[str]:
        """
        Extracts header information from the messages DataFrame.

        Returns:
        list[str]: A list of strings containing the extracted header information.
        """
        self.messages["trialid_cleaned"] = self.messages["trialid "].str.replace(
            r"[\n\x00\t]", ""
        )

        record_index = self.messages[
            self.messages["trialid_cleaned"].str.contains(
                "RECORD", case=False, regex=True
            )
        ].index

        if not record_index.empty:
            header = self.messages.loc[: record_index[0], "trialid_cleaned"].tolist()
            return header
        return self.messages["trialid_cleaned"].tolist()

    def save_and_process_samples(
        self, BIDS_folder_path: str, include_events: bool = True
    ) -> List[str]:
        """
        Save the processed samples DataFrame into a compressed tsv file and return column names.

        Args:
            BIDS_folder_path (str): Root directory path of the BIDS dataset.
            include_events (bool, optional): Include events in the processing. Default is True.

        Returns:
            List[str]: A list of column names in the processed DataFrame.
        """
        if include_events:
            self.add_events()

        self.samples.loc[self.samples["pa_right"] < 1, "pa_right"] = "n/a"
        self.samples.loc[
            (self.samples["gx_right"] < 0)
            | (self.samples["gx_right"] > self.screen_resolution[0]),
            "gx_right",
        ] = "n/a"
        self.samples.loc[
            (self.samples["gy_right"] <= 0)
            | (self.samples["gy_right"] > self.screen_resolution[1]),
            "gy_right",
        ] = "n/a"

        self.samples = self.samples.reindex(
            columns=[c for c in self.samples.columns if "left" not in c]
        )
        self.samples = self.samples.rename(
            columns={
                "time": "eye_timestamp",
                "gx_right": "eye1_x_coordinate",
                "gy_right": "eye1_y_coordinate",
                "pa_right": "eye1_pupil_size",
                "px_right": "eye1_pupil_x_coordinate",
                "py_right": "eye1_pupil_y_coordinate",
                "hx_right": "eye1_head_x_coordinate",
                "hy_right": "eye1_head_y_coordinate",
                "rx": "screen_pixel_per_degree_x",
                "ry": "screen_pixel_per_degree_y",
                "gxvel_right": "eye1_x_velocity",
                "gyvel_right": "eye1_x_velocity",
                "hxvel_right": "eye1_head_x_velocity",
                "hyvel_right": "eye1_head_y_velocity",
                "rxvel_right": "eye1_raw_x_velocity",
                "ryvel_right": "eye1_raw_y_velocity",
                "fgxvel": "eye1_fast_gaze_x_velocity",
                "fgyvel": "eye1_fast_gaze_y_velocity",
                "fhxyvel": "eye1_fast_head_x_velocity",
                "fhyvel": "eye1_fast_head_y_velocity",
                "frxyvel": "eye1_fast_raw_x_velocity",
                "fryvel": "eye1_fast_raw_y_velocity",
            }
        )

        self.samples = self.samples.replace({np.nan: "n/a"})
        self.samples = self.samples.replace({100000000: "n/a"})

        if self.task_name in ["rest", "bht", "qct"]:
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_dir-{self.pe}_eyetrack.tsv.gz"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/func/",
            )
        elif self.task_name == "dwi":
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_acq-highres_dir-{self.pe}_eyetrack.tsv.gz"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/dwi/",
            )
        else:
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_eyetrack.tsv.gz"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/func/",
            )

        os.makedirs(output_file_dir, exist_ok=True)

        output_file_full_path = os.path.join(output_file_dir, output_file_name)

        column_order = [
            "eye_timestamp",
            "eye1_x_coordinate",
            "eye1_y_coordinate",
        ] + [
            col
            for col in self.samples.columns
            if col not in ["eye_timestamp", "eye1_x_coordinate", "eye1_y_coordinate"]
        ]

        self.samples = self.samples[column_order]
        self.samples.to_csv(
            output_file_full_path,
            sep="\t",
            index=False,
            header=False,
            compression="gzip",
        )

        return self.samples.columns.tolist()

    def create_info_json(
        self, BIDS_folder_path: str, info_json_path: str
    ) -> Optional[str]:
        """
        Create and save the info JSON file for eye tracking data.

        Args:
            BIDS_folder_path (str): Root directory path of the BIDS dataset.
            info_json_path (str): Path to the info JSON file.

        Returns:
            Optional[str]: Path to the saved JSON file, or None if no data is available.
        """
        with open(info_json_path, "r") as f:
            info_ET = json.load(f)
            timestamp_first_trigger = self.find_timestamp_message()
        (
            calibration_count,
            calibration_type,
            average_calibration_error,
            max_calibration_error,
            calibration_position,
        ) = self.extract_calibration()
        (
            recorded_eye,
            eye_tracking_method,
            sampling_frequency,
            pupil_threshold,
            CR_threshold,
            pupil_fit_method,
        ) = self.extract_ET_parameters()
        header = self.extract_header()
        final_info = {
            "Manufacturer": info_ET["Manufacturer"],
            "ManufacturersModelName": info_ET["ManufacturersModelName"],
            "DeviceSerialNumber": info_ET["DeviceSerialNumber"],
            "SoftwareVersion": info_ET["SoftwareVersion"],
            "CalibrationUnit": info_ET["CalibrationUnit"],
            "EyeTrackerDistance": info_ET["EyeTrackerDistance"],
            "SampleCoordinateUnits": info_ET["SampleCoordinateUnits"],
            "SampleCoordinateSystem": info_ET["SampleCoordinateSystem"],
            "EnvironmentCoordinates": info_ET["EnvironmentCoordinates"],
            "ScreenAOIDefinition": info_ET["ScreenAOIDefinition"],
            "SamplingFrequency": sampling_frequency,
            "StartTime": timestamp_first_trigger,
            "RecordedEye": recorded_eye,
            "EyeTrackingMethod": eye_tracking_method,
            "PupilFitMethod": pupil_fit_method,
            "GazeMappingSettings": {
                "CRThreshold": CR_threshold,
                "PThreshold": pupil_threshold,
            },
            "CalibrationCount": calibration_count,
            "Columns": self.samples.columns.tolist(),
            "CalibrationType": calibration_type,
            "CalibrationPosition": calibration_position,
            "AverageCalibrationError": average_calibration_error,
            "MaximalCalibrationError": max_calibration_error,
            "EDFHeader": header,
        }

        final_info = {
            key: value for key, value in final_info.items() if value is not None
        }

        if not final_info:
            print("No data to write to the JSON file. Skipping.")
            return None

        if self.task_name in ["rest", "bht", "qct"]:
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_dir-{self.pe}_eyetrack.json"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/func/",
            )
        elif self.task_name == "dwi":
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_acq-highres_dir-{self.pe}_eyetrack.json"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/dwi/",
            )
        else:
            output_file_name = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_eyetrack.json"
            output_file_dir = os.path.join(
                BIDS_folder_path,
                f"sub-{self.participant:03d}/ses-{self.session:03d}/func/",
            )

        os.makedirs(output_file_dir, exist_ok=True)
        output_json_path = os.path.join(output_file_dir, output_file_name)
        with open(output_json_path, "w") as json_file:
            json.dump(final_info, json_file, indent=4)

        return output_json_path

    def plot_pupil_size(
        self,
        eye: str = "right",
        notebook: bool = True,
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        if filename is None:
            filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_pupil_ts.pdf"

        if eye == "right":
            self.samples.pa_right[self.samples.pa_right < 1] = np.nan
            plt.plot(self.samples["time"].values, self.samples["pa_right"].values)
        elif eye == "left":
            self.samples.pa_left[self.samples.pa_left < 1] = np.nan
            plt.plot(self.samples["time"].values, self.samples["pa_left"].values)
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
        self,
        eye: str = "right",
        notebook: bool = True,
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        if filename is None:
            filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_coordinates_ts.pdf"

        if eye == "right":
            self.samples.gx_right[
                (self.samples.gx_right < 0)
                | (self.samples.gx_right > self.screen_resolution[0])
            ] = np.nan
            self.samples.gy_right[
                (self.samples.gy_right < 0)
                | (self.samples.gy_right > self.screen_resolution[1])
            ] = np.nan

            fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

            axs[0].plot(self.samples["gx_right"], label="gx_right")
            axs[1].plot(self.samples["gy_right"], label="gy_right")
            axs[1].set_xlabel("time")
            axs[1].set_ylabel("x coordinate [pixels]")
            axs[1].set_ylabel("y coordinate [pixels]")

        elif eye == "left":
            self.samples.gx_left[
                (self.samples.gx_left < 0)
                | (self.samples.gx_left > self.screen_resolution[0])
            ] = np.nan
            self.samples.gy_left[
                (self.samples.gy_left < 0)
                | (self.samples.gy_left > self.screen_resolution[1])
            ] = np.nan

            fig, axs = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

            axs[0].plot(self.samples["time"], self.samples["gx_left"], label="gx_left")
            axs[0].set_ylabel("gx_left")
            axs[1].plot(self.samples["time"], self.samples["gy_left"], label="gy_left")
            axs[1].set_xlabel("timestamp [ms]")
            axs[1].set_ylabel("pupil area [pixels]")
            axs[0].set_xlim(self.samples["time"].iloc[0])

        else:
            print("Invalid eye argument")

        if notebook:
            plt.show()
            return None

        if save:
            plt.savefig(os.path.join(path_save, filename))
            plt.clf()
            return os.path.join(path_save, filename)

        return None

    def plot_heatmap_coordinate_density(
        self,
        eye: str = "right",
        notebook: bool = True,
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        if filename is None:
            filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_heatmap.pdf"

        plt.rcParams["figure.figsize"] = [10, 6]
        cmap = sns.color_palette("coolwarm", as_cmap=True)

        if eye == "right":
            filtered_samples = self.samples[
                (self.samples["gx_right"] >= 0)
                & (self.samples["gx_right"] <= self.screen_resolution[0])
                & (self.samples["gy_right"] >= 0)
                & (self.samples["gy_right"] <= self.screen_resolution[1])
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
            plt.xlabel("right eye y coordinate [pixels]")
        if notebook:
            plt.show()
        if save:
            plt.savefig(os.path.join(path_save, filename))

    def plot_delta(
        self,
        save: Optional[bool] = False,
        path_save: Optional[str] = ".",
        filename: Optional[str] = "blink_durations.pdf",
        notebook: Optional[bool] = True,
    ) -> None:
        """
        Plot the distribution of blink durations.

        Parameters:
        - save: Whether to save the plot as an image (default is False).
        - path_save: Path to the directory where the image will be saved (default is current directory).
        - filename: Name of the saved image file (default is "blink_durations.png").
        - notebook: If True, the plot will be displayed in a Jupyter notebook (default is True).

        Returns:
        - None (displays the plot or saves it).
        """
        blinks = self.events[self.events["blink"] == True]
        blinks["duration"] = blinks["end"] - blinks["start"]
        plt.figure(figsize=(10, 6))
        plt.plot(blinks["start"], blinks["duration"])
        plt.title("Blink Durations Over Time")
        plt.xlabel("Time of Onset (ms)")
        plt.ylabel("Blinks Duration (ms)")
        if notebook:
            plt.show()
        if save:
            output_filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_{filename}"
            plt.savefig(os.path.join(path_save, output_filename))

    def plot_heatmap_coordinate_histo(
        self,
        eye: str = "right",
        notebook: bool = True,
        save: bool = False,
        path_save: str = ".",
        filename: str = "heatmap.pdf",
        bins: int = 100,
    ) -> Optional[None]:
        """
        Plots a 2D histogram for eye tracking coordinates.

        Parameters:
        - eye (str): Specifies whether to plot for the "right" or "left" eye.
        - notebook (bool): If True, the plot is shown in the Jupyter notebook.
        - save (bool): If True, the plot is saved to a file.
        - path_save (str): Path to save the plot file.
        - filename (str): Name of the saved plot file.
        - bins (int): Number of bins for the histogram.

        Returns:
        - None if notebook is True, else the path to the saved plot file.

        Example:
        ```python
        DwiSession4.plot_heatmap_coordinate_histo(eye="left", screen_resolution=(1024, 768), bins=50)
        ```
        """
        plt.rcParams["figure.figsize"] = [10, 6]
        plt.figure(figsize=(10, 6))
        cmap = sns.color_palette("coolwarm", as_cmap=True)

        if eye == "right":
            filtered_samples = self.samples[
                (self.samples["gx_right"] >= 0)
                & (self.samples["gx_right"] <= self.screen_resolution[0])
                & (self.samples["gy_right"] >= 0)
                & (self.samples["gy_right"] <= self.screen_resolution[1])
            ]

            plt.hist2d(
                filtered_samples["gx_right"],
                filtered_samples["gy_right"],
                range=[[0, self.screen_resolution[0]], [0, self.screen_resolution[1]]],
                bins=bins,
                cmap=cmap,
            )

            plt.xlabel("right eye x coordinate [pixels]")
            plt.ylabel("right eye y coordinate [pixels]")

        elif eye == "left":
            filtered_samples = self.samples[
                (self.samples["gx_left"] >= 0)
                & (self.samples["gx_left"] <= self.screen_resolution[0])
                & (self.samples["gy_left"] >= 0)
                & (self.samples["gy_left"] <= self.screen_resolution[1])
            ]

            plt.hist2d(
                filtered_samples["gx_left"],
                filtered_samples["gy_left"],
                range=[[0, screen_resolution[0]], [0, self.screen_resolution[1]]],
                bins=bins,
                cmap=cmap,
            )

            plt.xlabel("left eye x coordinate [pixels]")
            plt.ylabel("left eye y coordinate [pixels]")

        else:
            print("Invalid eye argument")

        plt.gca().invert_yaxis()
        plt.xlim(0, self.screen_resolution[0])
        plt.ylim(0, self.screen_resolution[1])

        if notebook:
            plt.show()
            return None

        if save:
            output_filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_{filename}"
            plt.savefig(os.path.join(path_save, output_filename))
        return None
