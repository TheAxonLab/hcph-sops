import pandas as pd
import os
import gzip


def write_event_file(tsv_file: str) -> None:
    """
    This function reads the trigger channels of the physiological file, processes them to create the event file.

    Parameters:
        tsv_file (str): The path to the input gzipped TSV file containing physiological data of a task.

    """
    with gzip.open(tsv_file, "rt") as file:
        df = pd.read_csv(file, sep="\t", header=None)
    event_dataframe = pd.DataFrame(columns=["onset", "duration", "trial-type"])
    if (
        "BreathHolding" in tsv_file
    ):  # This condition must be changed following the naming convention for the tasks.
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
                hold = {"onset": row[0], "duration": 2.7, "trial-type": "hold"}
                event_dataframe = event_dataframe.append(hold, ignore_index=True)
            """
            #For the new version of the psychopy task
            if row[6] == 5:
                breathin = {"onset": row[0], "duration": 2.7, "trial-type": "breath-in"}
                event_dataframe = event_dataframe.append(breathin, ignore_index=True)
            if row[7] == 5:
                breathout = {"onset": row[0] + 2.7,"duration": 2.3,"trial-type": "breath-out"}
                event_dataframe = event_dataframe.append(breathout, ignore_index=True)
            if row[8] == 5:
                hold = {"onset": row[0], "duration": 2.7, "trial-type": "hold"}
                event_dataframe = event_dataframe.append(hold, ignore_index=True)
            """
    elif (
        "PCT" in tsv_file
    ):  # This condition must be changed following the naming convention for the tasks.
        for index, row in df.iterrows():
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
                mot = {"onset": row[0], "duration": 0.5, "trial-type": "blank"}
                event_dataframe = event_dataframe.append(mot, ignore_index=True)
            """
    elif (
        "RestingState" in tsv_file
    ):  # This condition must be changed following the naming convention for the tasks.
        pass

    output_folder = os.path.dirname(tsv_file)
    base_name = os.path.basename(tsv_file)
    output_file = os.path.join(
        output_folder, base_name.replace("_physio.tsv.gz", "_events.tsv")
    )
    event_dataframe.to_csv(output_file, sep="\t", index=False)
    print(f"Event DataFrame saved to {output_file}")


if __name__ == "__main__":
    tsv_file = "/home/esavary/Projects/acknowledge_processing/session_07_14/sub-001/ses-01/func/sub-001_ses-01_task-PCT_rec-labchart_physio.tsv.gz"
    write_event_file(tsv_file)
