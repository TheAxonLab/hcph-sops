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
import re
import os
import json
from pathlib import Path
import string
from collections import defaultdict
from typing import Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pyedfread import edf, edfread


# EyeLink calibration coordinates from https://www.sr-research.com/calibration-coordinate-calculator/
EYELINK_CALIBRATION_COORDINATES = [
    (400, 300), (400, 51), (400, 549), (48, 300), (752, 300), (48, 51), (752, 51), (48, 549), (752, 549), (224, 176), (576, 176), (224, 424), (576, 424)
]

EYE_CODE_MAP = defaultdict(
    lambda: "unknown", {"R": "right", "L": "left", "RL": "both"}
)
RIGHT_EYE_COLUMNS = {
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


class EyeTrackingRun:
    """
    Class representing an instance of eye tracking data.

    Parameters
    ----------
    session : int
        Session ID.
    task_name : str
        Task name.
    participant : int
        Participant ID.
    samples : pd.DataFrame
        DataFrame containing eye tracking samples.
    events : pd.DataFrame
        DataFrame containing eye tracking events.
    messages : pd.DataFrame
        DataFrame containing eye tracking messages.
    message_first_trigger : str
        Message that signals the first trigger of the run.
    screen_resolution : Tuple[int, int]
        Screen resolution as a tuple of two integers.

    pe : str, optional
        Phase encoding direction (default is an empty string).

    Examples
    --------
    >>> et_run = EyeTrackingRun(
    ...     session="001",
    ...     task_name="rest",
    ...     participant="001",
    ...     samples=samples_df,
    ...     events=events_df,
    ...     messages=messages_df,
    ...     message_first_trigger="start",
    ...     screen_resolution=(800, 600),
    ...     messages_start_fixation="fixation_start",
    ...     messages_stop_fixation="fixation_stop",
    ...     pe="",
    ... )
    """

    def __init__(
        self,
        session: str,
        task_name: str,
        participant: str,
        samples: pd.DataFrame,
        events: pd.DataFrame,
        messages: pd.DataFrame,
        message_first_trigger: str,
        screen_resolution: Tuple[int, int],
        messages_start_fixation: str = "",
        messages_stop_fixation: str = "",
        pe: str = "",
    ) -> None:
        """
        Initialize EyeTrackingRun instance.

        Parameters
        ----------
        session : int
            Session ID.
        task_name : str
            Task name.
        participant : int
            Participant ID.
        samples : pd.DataFrame
            DataFrame containing eye tracking samples.
        events : pd.DataFrame
            DataFrame containing eye tracking events.
        messages : pd.DataFrame
            DataFrame containing eye tracking messages.
        message_first_trigger : str
            Message that serves as the first trigger.
        screen_resolution : Tuple[int, int]
            Screen resolution as a tuple of two integers.
        messages_start_fixation : str, optional
            Message indicating the start of a fixation (default is an empty string).
        messages_stop_fixation : str, optional
            Message indicating the stop of a fixation (default is an empty string).
        pe : str, optional
            Phase encoding direction (default is an empty string).

        Notes
        -----
        This method initializes the EyeTrackingRun instance with the provided parameters.

        """

        self.session = int(session)
        self.task_name = task_name
        self.participant = int(participant)
        self.samples = samples
        self.events = events
        self.messages = messages
        self.message_first_trigger = message_first_trigger
        self.messages_start_fixation = messages_start_fixation
        self.messages_stop_fixation = messages_stop_fixation
        self.screen_resolution = screen_resolution
        self.pe = pe

    def add_events(self) -> pd.DataFrame:
        """
        Update 'fixation', 'saccade', and 'blink' columns in the samples DataFrame based on events DataFrame.

        Returns
        -------
        pd.DataFrame
            Updated samples DataFrame.

        Notes
        -----
        This method updates the 'fixation', 'saccade', and 'blink' columns in the samples DataFrame based on
        information from the events DataFrame.

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

        Returns
        -------
        Optional[int]
            The 'trialid_time' as an integer if the message is found; None if the message is not found.

        Notes
        -----
        This method searches for the first row in the DataFrame that contains the specified message string
        (given by 'self.message_first_trigger') and returns the corresponding 'trialid_time' as an integer.
        """
        message_row = self.messages[
            self.messages["trialid "].str.contains(
                self.message_first_trigger, case=False, regex=True
            )
        ].head(1)
        if not message_row.empty:
            return int(message_row["trialid_time"].iloc[0])

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

        Returns
        -------
        Tuple[int, Optional[str], Optional[float], Optional[float], Optional[List[List[Union[int, int]]]]]
            A tuple containing:
            - Calibration count (int),
            - Calibration type (str or None),
            - Average calibration error (float or None),
            - Maximum calibration error (float or None),
            - Calibration position (list of lists of integers or None).

        Notes
        -----
        This method extracts calibration information from the DataFrame of messages and returns a tuple
        containing various calibration details, such as count, type, average error, maximum error, and position.
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

            calibration_type = None
            calibration_position = None
            if (points := re.findall(r"HV(\d{1,2})", error_message)):
                calibration_type = f"HV{points[0]}"
                calibration_position = EYELINK_CALIBRATION_COORDINATES[:int(points[0])]

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

        Returns
        -------
        Tuple[str, str, Optional[int], Optional[int], Optional[int], str]
            A tuple containing the extracted parameters:
            - Recorded eye ('both', 'right', 'left', or 'unknown').
            - Eye tracking method.
            - Sampling frequency (optional, None if not available).
            - Pupil threshold (optional, None if not available).
            - CR threshold (optional, None if not available).
            - Pupil fitting method ('ellipse' or 'center-of-mass').

        Notes
        -----
        This method extracts eye tracking parameters from the given samples and messages dataframes and
        returns a tuple with information about the recorded eye, eye tracking method, sampling frequency,
        pupil threshold, CR threshold, and pupil fitting method.
        """

        row_start = self.messages[
            self.messages["trialid "].str.contains("RECORD", case=False, regex=True)
        ].head(1)
        start_text = row_start["trialid "].iloc[0]
        match_start = re.search(r"RECORD (\w+) (\d+) (\d+) (\d+) (\w+)", start_text)

        if match_start:
            eye_tracking_method, sampling_frequency, _, _, r_eye = match_start.groups()
            sampling_frequency = int(sampling_frequency)
            recorded_eye = EYE_CODE_MAP[r_eye]

            print("recorded eye:", recorded_eye)
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

        pupil_fit_method = "ellipse" if "ELLIPSE" in fit_param_text else "center-of-mass"

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

        Returns
        -------
        List[str]
            A list of strings containing the extracted header information.

        Notes
        -----
        This method extracts header information from the messages DataFrame and returns a list of strings
        containing the extracted header information.
        """
        self.messages["trialid_cleaned"] = self.messages["trialid "].apply(
            lambda x: ''.join(filter(lambda char: char in string.printable and char != '\n', str(x)))
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
        Save the processed samples DataFrame into a compressed TSV file and return column names.

        Parameters
        ----------
        BIDS_folder_path : str
            Root directory path of the BIDS dataset.
        include_events : bool, optional
            Include events in the processing. Default is True.

        Returns
        -------
        List[str]
            A list of column names in the processed DataFrame.

        Notes
        -----
        This method saves the processed samples DataFrame into a compressed TSV file
        and returns a list of column names in the processed DataFrame.
        """
        
        if include_events:
            self.add_events()

        self.samples.loc[self.samples["pa_right"] < 1, "pa_right"] = np.nan
        self.samples.loc[
            (self.samples["gx_right"] < 0)
            | (self.samples["gx_right"] > self.screen_resolution[0]),
            "gx_right",
        ] = np.nan
        self.samples.loc[
            (self.samples["gy_right"] <= 0)
            | (self.samples["gy_right"] > self.screen_resolution[1]),
            "gy_right",
        ] = np.nan
        self.samples.loc[self.samples["time"] ==0, "time"] = np.nan
        

        self.samples = self.samples.reindex(
            columns=[c for c in self.samples.columns if "left" not in c]
        )
        self.samples = self.samples.rename(columns=RIGHT_EYE_COLUMNS)

        self.samples = self.samples.replace({100000000: np.nan})

        if self.task_name in ("rest", "bht", "qct"):
            output_file_name = f"func/sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_dir-{self.pe}_eyetrack.tsv.gz"
        elif self.task_name == "fixation":
            output_file_name = f"dwi/sub-{self.participant:03d}_ses-{self.session:03d}_acq-highres_dir-{self.pe}_eyetrack.tsv.gz"
        else:
            ValueError("Unknown task type")

        BIDS_folder_path = Path(BIDS_folder_path)
        output_json_path = (
            BIDS_folder_path
            / f"sub-{self.participant:03d}"
            / f"ses-{self.session:03d}"
            / output_file_name
        )
        output_json_path.parent.mkdir(exist_ok=True, parents=True)

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
            output_json_path,
            sep="\t",
            index=False,
            header=False,
            compression="gzip",
            na_rep="n/a",
        )

        return output_json_path

    def create_info_json(
        self, BIDS_folder_path: str, info_json_path: str
    ) -> Optional[str]:
        """
        Create and save the info JSON file for eye tracking data.

        Parameters
        ----------
        BIDS_folder_path : str
            Root directory path of the BIDS dataset.
        info_json_path : str
            Path to the info JSON file.

        Returns
        -------
        Optional[str]
            Path to the saved JSON file, or None if no data is available.

        Examples
        --------
        >>> et_run = EyeTrackingRun(...)  # Initialize with appropriate parameters
        >>> et_run.create_info_json("/path/to/BIDS", "/path/to/info.json")

        """
        info_ET = json.loads(Path(info_json_path).read_text())
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

        if self.task_name in ("rest", "bht", "qct"):
            output_file_name = f"func/sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_dir-{self.pe}_eyetrack.json"
        elif self.task_name == "fixation":
            output_file_name = f"dwi/sub-{self.participant:03d}_ses-{self.session:03d}_acq-highres_dir-{self.pe}_eyetrack.json"
        else:
            raise ValueError("Unknown task type")

        BIDS_folder_path = Path(BIDS_folder_path)
        output_json_path = (
            BIDS_folder_path
            / f"sub-{self.participant:03d}"
            / f"ses-{self.session:03d}"
            / output_file_name
        )
        output_json_path.parent.mkdir(exist_ok=True, parents=True)
        output_json_path.write_text(json.dumps(final_info, indent=2))

        return output_json_path

    def plot_pupil_size(
        self,
        eye: str = "right",
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Plots the time series of pupil size.

        Parameters
        ----------
        eye : str, optional
            Specifies whether to plot for the "right" or "left" eye.
        save : bool, optional
            If True, the plot is saved to a file.
        path_save : str, optional
            Path to save the plot file.
        filename : str, optional
            Name of the saved plot file.

        Returns
        -------
        Optional[str]
            The path to the saved plot file.

        Examples
        --------
        >>> DwiSession4.plot_pupil_size(eye="left")
        """
        
        if filename is None:
            filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_pupil_ts.pdf"
        time_start=self.find_timestamp_message()
        self.samples.time[
            (self.samples.time <= 0)
        ] = np.nan
        if eye == "right":
            self.samples.pa_right[self.samples.pa_right < 1] = np.nan
            plt.plot(self.samples["time"].values - time_start, self.samples["pa_right"].values)
        elif eye == "left":
            self.samples.pa_left[self.samples.pa_left < 1] = np.nan
            plt.plot(self.samples["time"].values- time_start, self.samples["pa_left"].values)
        else:
            print("Invalid eye argument")

        plt.xlabel("time [ms]")
        plt.ylabel("pupil area [pixels]")

        if save:
            plt.savefig(os.path.join(path_save, filename))
            return os.path.join(path_save, filename)

        return plt.gcf()

    def plot_coordinates_ts(
        self,
        eye: str = "right",
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Plots a time series of eye tracking coordinates.

        Parameters
        ----------
        eye : str, optional
            Specifies whether to plot for the "right" or "left" eye.
        save : bool, optional
            If True, the plot is saved to a file.
        path_save : str, optional
            Path to save the plot file.
        filename : str, optional
            Name of the saved plot file.

        Returns
        -------
        Optional[str]
            The path to the saved plot file.

        Example
        -------
        DwiSession4.plot_coordinates_ts(eye="left")
        """
        
        if filename is None:
            filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_coordinates_ts.pdf"
        time_start = self.find_timestamp_message()
        self.samples.time[
            (self.samples.time <= 0)
        ] = np.nan
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
            print(self.samples["time"].values[0:10] - time_start, self.samples["time"].values[-20:-1] - time_start)
            axs[0].plot(self.samples["time"].values - time_start,self.samples["gx_right"], label="gx_right")
            axs[1].plot(self.samples["time"].values - time_start,self.samples["gy_right"], label="gy_right")
            axs[1].set_xlabel("time [ms]")
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
            axs[1].set_xlabel("timestamp")
            axs[1].set_ylabel("pupil area [pixels]")
            axs[0].set_xlim(self.samples["time"].iloc[0])

        else:
            print("Invalid eye argument")


        if save:
            plt.savefig(os.path.join(path_save, filename))
            plt.clf()

        return plt.gcf()

    def plot_heatmap_coordinate_density(
        self,
        eye: str = "right",
        save: bool = False,
        path_save: str = ".",
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """
        Plots a heatmap for eye tracking coordinates.

        Parameters
        ----------
        eye : str, optional
            Specifies whether to plot for the "right" or "left" eye.
        save : bool, optional
            If True, the plot is saved to a file.
        path_save : str, optional
            Path to save the plot file.
        filename : str, optional
            Name of the saved plot file.

        Returns
        -------
        Optional[str]
            The path to the saved plot file.

        Examples
        --------
        >>> DwiSession4.plot_heatmap_coordinate_density(eye="left", screen_resolution=(1024, 768))
        """
        
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
            plt.gca().invert_yaxis()
            plt.xlabel("right eye x coordinate [pixels]")
            plt.xlabel("right eye y coordinate [pixels]")
        elif eye == "left":
            filtered_samples = self.samples[
                (self.samples["gx_left"] >= 0)
                & (self.samples["gx_left"] <= self.screen_resolution[0])
                & (self.samples["gy_left"] >= 0)
                & (self.samples["gy_left"] <= self.screen_resolution[1])
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
            plt.gca().invert_yaxis()
            plt.xlabel("left eye x coordinate [pixels]")
            plt.xlabel("left eye y coordinate [pixels]")
        if save:
            plt.savefig(os.path.join(path_save, filename))
        return plt.gcf()

    def plot_delta(
        self,
        save: Optional[bool] = False,
        path_save: Optional[str] = ".",
        filename: Optional[str] = "blink_durations.pdf",
    ) -> None:
        """
        Plot the distribution of blink durations.

        Parameters
        ----------
        save : bool, optional
            Whether to save the plot as an image (default is False).
        path_save : str, optional
            Path to the directory where the image will be saved (default is current directory).
        filename : str, optional
            Name of the saved image file (default is "blink_durations.png").

        Returns
        -------
        None
            Displays the plot or saves it.

        Notes
        -----
        This method the blink occurences over time.
        """
        time_start = self.find_timestamp_message()
        blinks = self.events[self.events["blink"] == True]
        blinks_start = blinks["start"].values
        blinks_end = blinks["end"].values
        timestamps = self.samples["time"].values

        blinks_array = np.zeros_like(timestamps, dtype=int)
        for start, end in zip(blinks_start, blinks_end):
            blinks_array[(timestamps >= start) & (timestamps <= end)] = 1
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps-time_start,blinks_array)
        plt.xlabel("Blink occurences over time")

        if save:
            output_filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_{filename}"
            plt.savefig(os.path.join(path_save, output_filename))

        return plt.gcf()

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

        Parameters
        ----------
        eye : str, optional
            Specifies whether to plot for the "right" or "left" eye.
        save : bool, optional
            If True, the plot is saved to a file.
        path_save : str, optional
            Path to save the plot file.
        filename : str, optional
            Name of the saved plot file.
        bins : int, optional
            Number of bins for the histogram.

        Returns
        -------
        None or str
            None if notebook is True, else the path to the saved plot file.

        Example
        -------
        >>> DwiSession4.plot_heatmap_coordinate_histo(eye="left", screen_resolution=(1024, 768), bins=50)

        Notes
        -----
        This method plots a 2D histogram for eye tracking coordinates.
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

        if save:
            output_filename = f"sub-{self.participant:03d}_ses-{self.session:03d}_task-{self.task_name}_{filename}"
            plt.savefig(os.path.join(path_save, output_filename))
        return plt.gcf()
