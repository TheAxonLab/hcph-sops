from pathlib import Path
from json import dumps
import string
import numpy as np
from scipy.signal import fftconvolve
import pandas as pd
from typing import Tuple, Optional, Union, List
from pyedfread import edf, edfread
from typing import Optional
import re
import os
import json


def add_events(samples, events):  # very slow
    """
    Update 'fixation' and 'saccade' columns in the samples dataframe based on events dataframe.

    Parameters:
    - samples: DataFrame containing samples data.
    - events: DataFrame containing events data.

    Returns:
    - Updated samples DataFrame.
    """

    samples["fixation"] = 0
    samples["saccade"] = 0
    for _, event in events.iterrows():
        start_time = event["start"]
        end_time = event["end"]
        event_type = event["type"]
        samples.loc[
            (samples["time"] >= start_time) & (samples["time"] <= end_time), event_type
        ] = 1

    return samples


def save_and_process_samples(
    samples: pd.DataFrame,
    events: pd.DataFrame,
    BIDS_folder_path: str,
    task_name: str,
    subject: int,
    session: int,
    pe: str,
    include_events: bool = True,
) -> List[str]:
    """
    Save the processed samples DataFrame into a compressed tsv file and return column names.

    Args:
        samples (pd.DataFrame): DataFrame containing eye tracking samples.
        events (pd.DataFrame): DataFrame containing eye tracking events.
        BIDS_folder_path (str): Root directory path of the BIDS dataset.
        task_name (str): Name of the task.
        subject (int): Subject identifier.
        session (int): Session identifier.
        pe (str): Phase-encoding direction (e.g., 'LR').
        include_events (bool, optional): Include events in the processing. Default is True.

    Returns:
        List[str]: A list of column names in the processed DataFrame.
    """

    if include_events:
        samples = add_events(samples, events)
        print(samples.columns)

    samples["pa_right"][samples["pa_right"] < 1] = "n/a"
    samples["gx_right"][(samples["gx_right"] < 0) | (samples["gx_right"] > 800)] = "n/a"
    samples["gy_right"][
        (samples["gy_right"] <= 0) | (samples["gy_right"] > 600)
    ] = "n/a"

    samples = samples.reindex(columns=[c for c in samples.columns if "left" not in c])
    samples = samples.rename(
        columns={
            "time": "eye_timestamp",
            "gx_right": "eye1_x_coordinate",
            "gy_right": "eye1_y_coordinate",
            "pa_right": "eye1_pupil_size",
            "px_right": "eye1_pupil_x_coordinate",
            "py_right": "eye1_pupil_y_coordinate",
        }
    )

    samples = samples.replace({np.nan: "n/a"})
    samples = samples.replace({100000000: "n/a"})
    print(samples.columns)

    if task_name in ["rest", "bht", "qct"]:
        output_file_name = f"sub-{subject:02d}_ses-{session:03d}_task-{task_name}_dir-{pe}_eyetrack.tsv.gz"
        output_file_dir = os.path.join(
            BIDS_folder_path, f"sub-{subject:03d}/ses-{session:03d}/func/"
        )
    elif task_name == "dwi":
        output_file_name = (
            f"sub-{subject:02d}_ses-{session:03d}_acq-highres_dir-{pe}_eyetrack.tsv.gz"
        )
        output_file_dir = os.path.join(
            BIDS_folder_path, f"sub-{subject:03d}/ses-{session:03d}/dwi/"
        )
    else:
        raise ValueError(f"Unsupported task name: {task_name}")

    os.makedirs(output_file_dir, exist_ok=True)

    output_file_full_path = os.path.join(output_file_dir, output_file_name)
    samples.to_csv(
        output_file_full_path, sep="\t", index=False, header=False, compression="gzip"
    )

    return samples.columns.tolist()


def create_info_json(
    BIDS_folder_path: str,
    task_name: str,
    subject: int,
    session: int,
    pe: str,
    info_json_path: str,
    message_first_trigger: str,
    column_names: List[str],
    samples: pd.DataFrame,
    messages: pd.DataFrame,
) -> Optional[str]:
    """
    Create and save the info JSON file for eye tracking data.

    Args:
        BIDS_folder_path (str): Root directory path of the BIDS dataset.
        task_name (str): Name of the task.
        subject (int): Subject identifier.
        session (int): Session identifier.
        pe (str): Phase-encoding direction (e.g., 'LR').
        info_json_path (str): Path to the info JSON file.
        message_first_trigger (str): Message for the first trigger.
        column_names (List[str]): List of column names in the processed DataFrame.
        samples (pd.DataFrame): DataFrame containing eye tracking samples.
        messages (pd.DataFrame): DataFrame containing messages data.

    Returns:
        Optional[str]: Path to the saved JSON file, or None if no data is available.
    """

    with open(info_json_path, "r") as f:
        info_ET = json.load(f)
    timestamp_first_trigger = find_timestamp_message(messages, message_first_trigger)
    (
        calibration_count,
        calibration_type,
        average_calibration_error,
        max_calibration_error,
        calibration_position,
    ) = extract_calibration(messages)
    (
        recorded_eye,
        eye_tracking_method,
        sampling_frequency,
        pupil_threshold,
        CR_threshold,
        pupil_fit_method,
    ) = extract_ET_parameters(samples, messages)
    header = extract_header(messages)
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
        "Columns": column_names,
        "CalibrationType": calibration_type,
        "CalibrationPosition": calibration_position,
        "AverageCalibrationError": average_calibration_error,
        "MaximalCalibrationError": max_calibration_error,
        "EDFHeader": header,
    }

    final_info = {key: value for key, value in final_info.items() if value is not None}

    if not final_info:
        print("No data to write to the JSON file. Skipping.")
        return None

    if task_name in ["rest", "bht", "qct"]:
        output_file_name = f"sub-{subject:02d}_ses-{session:03d}_task-{task_name}_dir-{pe}_eyetrack.json"
        output_file_dir = os.path.join(
            BIDS_folder_path, f"sub-{subject:03d}/ses-{session:03d}/func/"
        )
    elif task_name == "dwi":
        output_file_name = (
            f"sub-{subject:02d}_ses-{session:03d}_acq-highres_dir-{pe}_eyetrack.json"
        )
        output_file_dir = os.path.join(
            BIDS_folder_path, f"sub-{subject:03d}/ses-{session:03d}/dwi/"
        )
    else:
        raise ValueError(f"Unsupported task name: {task_name}")

    os.makedirs(output_file_dir, exist_ok=True)
    output_json_path = os.path.join(output_file_dir, output_file_name)
    with open(output_json_path, "w") as json_file:
        json.dump(final_info, json_file, indent=4)

    return output_json_path
