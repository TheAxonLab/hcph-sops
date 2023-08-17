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
import argparse
import pandas as pd
import os
import gzip
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

EVENTS_JSON_BOILERPLATE = {
    "StimulusPresentation": {
        "OperatingSystem": "Linux Ubuntu 20.04.5",
        "SoftwareName": "PsychoPy",
        "SoftwareRRID": "SCR_006571",
        "SoftwareVersion": "2022.3.0.dev6"
    }
}

def plot_physio_data_with_events(
    time_series_df: pd.DataFrame,
    events_df: pd.DataFrame,
    tsv_file: str,
    output_folder: str = ".",
) -> None:
    """
    Plot physiological data along with events.

    Parameters
    ----------
    time_series_df : :obj:`pandas.DataFrame`
        Table containing the physiological data.
    events_df : :obj:`pandas.DataFrame`
        Table containing the event data.
    tsv_file : :obj:`os.pathlike`
        Path to the TSV file.
    output_folder : :obj:`os.pathfile`
        Output folder for saving the plot image. Default is current directory.

    Returns
    -------
    The path where the plot was saved as a PNG file.

    """
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(30, 10), sharex=True)
    ax1.plot(time_series_df[0], time_series_df[1], label="RB")
    ax2.plot(time_series_df[0], time_series_df[2], label="ECG")
    ax3.plot(time_series_df[0], time_series_df[3], label="GA")
    trial_types = events_df["trial-type"].unique()
    legend_colors = plt.cm.get_cmap("Set1", len(trial_types))
    legend_color_dict = {
        trial_type: legend_colors(i) for i, trial_type in enumerate(trial_types)
    }
    color_patches = []

    for trial_type in trial_types:
        legend_color = legend_color_dict[trial_type]
        color_patch = mpatches.Patch(color=legend_color, label=trial_type)
        color_patches.append(color_patch)
        events_of_type = events_df[events_df["trial-type"] == trial_type]

        for index, row in events_of_type.iterrows():
            ax1.axvline(row["onset"], color=legend_color, linestyle="--")
            ax2.axvline(row["onset"], color=legend_color, linestyle="--")
            ax3.axvline(row["onset"], color=legend_color, linestyle="--")
    ax1.set_ylabel("V")
    ax2.set_ylabel("V")
    ax3.set_ylabel("V")
    ax3.legend(handles=color_patches, loc="lower right")
    ax1.set_title("RB")
    ax2.set_title("ECG")
    ax3.set_title("GA")
    base_name = os.path.basename(tsv_file)
    output_file = os.path.join(
        output_folder, base_name.replace("_physio.tsv.gz", "_plot.png")
    )
    plt.tight_layout()
    plt.savefig(output_file)
    return output_file


def write_event_file(tsv_file: str) -> None:
    """
    This function reads the trigger channels of the physiological file, processes them to create the event file.

    Parameters
    ----------
    tsv_file :obj:`os.pathlike`
         The path to the input gzipped TSV file containing physiological data of a task.

    """
    with gzip.open(tsv_file, "rt") as file:
        df = pd.read_csv(file, sep="\t", header=None)
    event_dataframe = pd.DataFrame(columns=["onset", "duration", "trial-type"])
    if "bht" in tsv_file:
        for index, row in df.iterrows():
            if row[6] == 5:
                breathin = {"onset": row[0], "duration": 2.7, "trial-type": "breath-in"}
                breathout = {
                    "onset": row[0] + 2.7,
                    "duration": 2.3,
                    "trial-type": "breath-out",
                }
                event_dataframe = event_dataframe.append(breathin, ignore_index=True)
                event_dataframe = event_dataframe.append(breathout, ignore_index=True)

            if row[7] == 5:
                hold = {"onset": row[0], "duration": 15, "trial-type": "hold"}
                event_dataframe = event_dataframe.append(hold, ignore_index=True)
            """
            #For the new version of the psychopy task
            if row[6] == 5:
                breathin = {"onset": row[0], "duration": 2.7, "trial-type": "breath-in"}
                event_dataframe = event_dataframe.append(breathin, ignore_index=True)
            if row[7] == 5:
                breathout = {"onset": row[0],"duration": 2.3,"trial-type": "breath-out"}
                event_dataframe = event_dataframe.append(breathout, ignore_index=True)
            if row[8] == 5:
                hold = {"onset": row[0], "duration": 2.7, "trial-type": "hold"}
                event_dataframe = event_dataframe.append(hold, ignore_index=True)
            """
        json_content = EVENTS_JSON_BOILERPLATE.copy()
        json_content["StimulusPresentation"]["Code"] = "https://github.com/TheAxonLab/HCPh-fMRI-tasks/blob/97cc7879622f45129eefb9968890b41631f40851/task-bht_bold.psyexp"
        json_content["trial_type"]={}
        json_content["trial_type"]["Description"] = "Indicator of type of action that is expected"
        json_content["trial_type"]["LongName"] = "Breath-holding task conditions (that is, breath-in, breath-out, and hold)"
        json_content["trial_type"]["Levels"] = {
            "breath-in": "A green rectangle is displayed to indicate breathing in",
            "breath-out": "A yellow rectangle (orange for the last breath-in before hold) is displayed to indicate breathing out",
            "hold": "A red rectangle is displayed to indicate breath hold",
        }

    elif "qct" in tsv_file:
        for index, row in df.iterrows():
            if int(row[0]) > 0:
                if row[6] == 5:
                    vis = {"onset": row[0], "duration": 3, "trial-type": "vis"}
                    event_dataframe = event_dataframe.append(vis, ignore_index=True)
                if row[7] == 5:
                    cog = {"onset": row[0], "duration": 0.5, "trial-type": "cog"}
                    event_dataframe = event_dataframe.append(cog, ignore_index=True)
                if row[8] == 5:

                    mot = {"onset": row[0], "duration": 5, "trial-type": "mot"}
                    event_dataframe = event_dataframe.append(mot, ignore_index=True)
                """
                #Will be used if an additional channel is added in AcqKnowledge
                if row[9] == 5: 
                    blank = {"onset": row[0], "duration": 3, "trial-type": "blank"}
                    event_dataframe = event_dataframe.append(blank, ignore_index=True)
                """
        json_content = EVENTS_JSON_BOILERPLATE.copy()
        json_content["StimulusPresentation"]["Code"] = "https://github.com/TheAxonLab/HCPh-fMRI-tasks/blob/97cc7879622f45129eefb9968890b41631f40851/task-pct_bold.psyexp"
        json_content["trial_type"]={}
        json_content["trial_type"]["Description"] = "Indicator of type of action that is expected"
        json_content["trial_type"]["LongName"] = "Quality control task"
        json_content["trial_type"]["Levels"] = {
            "vis": "Fixation point on top of grating pattern",
            "cog": "Moving fixation points",
            "mot": "Finger taping with the left or right hand following the indications on the screen",
            "blank": "Fixation point in the center of the screen",
        }
    elif "rest" in tsv_file:
        for index, row in df.iterrows():
            if row[4] == 5:
                movie = {"onset": row[0], "duration": 1200, "trial-type": "movie"}
                event_dataframe = event_dataframe.append(movie, ignore_index=True)
        """
        for index, row in df.iterrows():
            if row[6] == 5:
                fixation = {"onset": row[0], "duration": 3, "trial-type": "fixation point"}
                event_dataframe = event_dataframe.append(fixation, ignore_index=True)
            if row[7] == 5:
                fixation_end = {"onset": row[0], "duration": 0, "trial-type": "end fixation point"}
                event_dataframe = event_dataframe.append(fixation_end, ignore_index=True)
            if row[8] == 5:
                movie = {"onset": row[0], "duration": 1200, "trial-type": "movie"}
                event_dataframe = event_dataframe.append(movie, ignore_index=True)
            if row[9] == 5:
                movie_end = {"onset": row[0], "duration": 1200, "trial-type": "end movie"}
                event_dataframe = event_dataframe.append(movie_end, ignore_index=True)
        """
        json_content = EVENTS_JSON_BOILERPLATE.copy()
        json_content["StimulusPresentation"]["Code"] = "https://github.com/TheAxonLab/HCPh-fMRI-tasks/blob/97cc7879622f45129eefb9968890b41631f40851/task-rest_bold.psyexp"
        json_content["trial_type"]={}
        json_content["trial_type"]["Description"] = "Indicator of type of action that is expected"
        json_content["trial_type"]["LongName"] = "Resting state"
        json_content["trial_type"]["Levels"] = {
            "fixation point": "Fixation point in the center of the screen",
            "end fixation point": "End of fixation",
            "movie": "Movie",
            "end movie": "End of the movie",
        }
    output_folder = os.path.dirname(tsv_file)
    base_name = os.path.basename(tsv_file)
    output_file = os.path.join(
        output_folder, base_name.replace("_physio.tsv.gz", "_events.tsv")
    )
    event_dataframe.to_csv(output_file, sep="\t", index=False)
    print(f"Event DataFrame saved to {output_file}")

    json_file = os.path.splitext(output_file)[0] + ".json"
    with open(json_file, "w") as json_output:
        json.dump(json_content, json_output, indent=4)
    print(f"JSON metadata saved to {json_file}")

    plot_physio_data_with_events(df, event_dataframe, tsv_file)


def write_all_event_files(folder_path: str) -> None:
    """
    Find all files in the given folder with names containing "_physio.tsv.gz", write the corresponding event files and save a plot of the physiological data.

    Parameters
    ----------
    folder_path : :obj:`os.pathlike`
        Path to the folder containing the files.

    """
    file_list = os.listdir(folder_path)

    physio_files = [filename for filename in file_list if "_physio.tsv.gz" in filename]

    for filename in physio_files:
        file_path = os.path.join(folder_path, filename)
        write_event_file(file_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Write event files and create plots for physiological data."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the folder containing the files (default: current folder)",
    )
    args = parser.parse_args()
    write_all_event_files(args.path)
