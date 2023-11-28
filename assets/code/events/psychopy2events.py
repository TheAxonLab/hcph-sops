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

import argparse
import pandas as pd
from pathlib import Path

TRIAL_TYPE = {
    "eye_movement_fixation": "cog",
    "ft_hand": "mot",
    "fixation": "blank",
    "grating": "vis",
    "movie": "movie",
    "bh_body": "red",
    "bh_end": "lightred",
    "end_trial_msg": "end-message",
    "polygon_4": "in",
    "polygon1": "out",
    "polygon_6": "in-last",
    "polygon_8": "out-last",
    "bh_body_2": "hold",
    "bh_end_2": "hold-warning",
    "bh_end_3": "refractory",
    "polygon_5": "out",  # old
    "polygon_7": "out",  # old
}


def psychopy2pandas(log_path: str | Path) -> pd.DataFrame:
    """
    Convert a PsychoPy log file to a *Pandas* DataFrame.

    Parameters
    ----------
    log_file : :obj:`os.pathlike`
        The path to the PsychoPy log file.

    Returns
    -------
    df : :obj:`pandas.DataFrame`
        A DataFrame containing event information.

    """

    df = pd.read_csv(
        log_path,
        sep="\t",
        names=["onset", "level", "desc"],
        dtype={"onset": float},
    )

    # Refer all onsets to the first trigger (first DATA entry)
    df.onset -= df[df.level.str.contains("DATA")].onset.values[0]

    # Extract events
    df[["trial_type", "start_end"]] = df["desc"].str.extract(
        r"({}):\s+autoDraw\s*=\s*(\w+)".format("|".join(TRIAL_TYPE.keys()))
    )

    # Extract hand of motor block of qct
    df["hand"] = df["desc"].str.extract(r"ft_hand:\s*text\s*=\s*\'(RIGHT|LEFT)\'")
    df.loc[df.hand.notna(), "trial_type"] = "ft_hand"
    # Normalize L/R values of motor blocks
    df = df.replace({"hand": {"RIGHT": "R", "LEFT": "L"}})

    # Extract coordinates of cognitive block of qct
    df[["x", "y"]] = df["desc"].str.extract(
        r"New trial \(rep=\d+, index=\d+\): "
        r"OrderedDict\(\[\(\'xpos\', (-?\d+\.\d+)\), \(\'ypos\', (-?\d+\.\d+)\)\]\)"
    )
    df[["x", "y"]] = df[["x", "y"]].astype(float)
    df.loc[df.x.notna(), "trial_type"] = "eye_movement_fixation"

    # Drop duplicates (all columns exactly the same)
    df = df.drop_duplicates()

    return df


def pandas2bids(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a Pandas DataFrame with event information to a BIDS-compatible DataFrame.

    This function takes an input DataFrame with event information, performs various data
    transformations to create a BIDS-compatible DataFrame, and returns the resulting DataFrame.

    Notes:

    - Rows without 'trial_type' are dropped from the input DataFrame.
    - New columns 'duration' and 'value' are added to the resulting DataFrame.
    - Durations are calculated based on 'start_end' information and assigned to the appropriate
      rows.
    - Values are retrieved from previous rows for specific trial types and assigned to the
      relevant rows.
    - Event names are normalized based on 'TRIAL_TYPE' (please ensure 'TRIAL_TYPE' is defined).
    - Mock events in 'end-message' are replaced with appropriate values, and block numbers are
      assigned.

    Parameters
    ----------
    input_df : :obj:`pandas.DataFrame`
        The input DataFrame containing event information.

    Returns
    -------
    df : :obj:`pandas.DataFrame`
        A BIDS-compatible DataFrame with columns 'onset', 'duration', 'trial_type', and 'value'.

    Examples
    --------
    >>> input_df = pd.DataFrame(...)
    >>> output_df = pandas2bids(input_df)

    """

    # Drop rows without trial type
    df = input_df[input_df.trial_type.notna()]
    # Prepare new columns (duration and value)
    df = df.reindex(
        columns=[
            "onset",
            "duration",
            "trial_type",
            "value",
            "start_end",
            "hand",
            "x",
            "y",
        ]
    )
    df["value"] = df["value"].astype(str)

    for et in set(df.trial_type.values):
        # Create a subdataframe with only this trial type
        subdf = df[df.trial_type == et].copy()

        if len(subdf) < 2:  # No need to try if not a block
            continue

        # Calculate durations
        onsets = subdf.start_end.notna() & subdf.start_end.str.contains("True")
        offsets = subdf.start_end.notna() & subdf.start_end.str.contains("False")

        # Psychopy stimuli generate two "autoDraw = False" events:
        # first at the end of the stimuli presentation and a second at the end of the routine.
        # When the tracked stimuli end with the psychopy routine, the two "autoDraw = False"
        # events occur at the same time and they are deduplicated by psychopy2bids.
        if len(subdf[onsets].onset.values) == len(subdf[offsets].onset.values):
            durations = subdf[offsets].onset.values - subdf[onsets].onset.values
        else:
            # In the BHT, the stimuli do not last for the full span of the routine, and we have
            # two "autoDraw = False" events. We need to drop the second corresponding to the routine.
            durations = subdf[offsets].onset.values[::2] - subdf[onsets].onset.values

        # And assign the duration to the first event row (the one containing autoDraw = True)
        subdf.loc[onsets, "duration"] = durations

        # Retrieve values from previous row for cognitive and motor blocks
        if et == "eye_movement_fixation":
            shifted = subdf.loc[
                subdf.start_end.isna() & subdf.x.notna(), ["x", "y"]
            ].values
            subdf.loc[onsets, "value"] = [f"({v[0]}, {v[1]})" for v in shifted]
        elif et == "ft_hand":
            shifted = subdf.loc[subdf.start_end.isna(), "hand"].values
            subdf.loc[onsets, "value"] = shifted

        # Move back to general dataframe
        df.loc[df.trial_type == et, subdf.columns] = subdf.values

    # Drop rows from which data was copied to the principal event row.
    df = df.drop(df[df.start_end.notna() & df.start_end.str.contains("False")].index)
    df = df.drop(df[df.start_end.isna() & df.x.notna()].index)
    df = df.drop(df[df.start_end.isna() & df.hand.notna()].index)

    # Normalize event names
    df = df.replace({"trial_type": TRIAL_TYPE})

    # Replace mock events in bht
    if "end-message" in set(df.trial_type.values):
        end_index = df[df.trial_type == "end-message"].index[0]
        df.loc[:end_index] = df.loc[:end_index].replace(
            {
                "trial_type": {
                    "in": "green",
                    "out": "yellow",
                    "in-last": "light-green",
                    "out-last": "gold",
                },
            },
        )
        df.loc[:end_index, "value"] = "mock"

        # After the mock there are 5 "true" blocks.
        len_remaining = len(df.loc[end_index + 1:, "value"])
        df.loc[end_index + 1:, "value"] = [
            f"block{v}" for block in range(1, 7) for v in [block] * 13
        ][:len_remaining]

    df = df.replace({"value": {"nan": "n/a"}})
    return df[["onset", "duration", "trial_type", "value"]]


def main() -> None:
    """
    Convert a PsychoPy log file to BIDS-compatible event data.

    This function handles the command-line interface for converting a PsychoPy log file to
    BIDS-compatible event data.
    It takes the input log file path and the desired output file path as command-line arguments,
    performs the conversion, and saves the resulting data in a BIDS-compatible TSV file.

    Example command-line::

        python psychopy2events.py -i /path/to/input/log.log -o sub-001_session-029_events.tsv

    """

    parser = argparse.ArgumentParser(
        description="Convert a PsychoPy log file to BIDS-compatible event data."
    )

    # Input file argument
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input PsychoPy log file"
    )

    # Output file argument
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output BIDS-compatible event file",
    )

    args = parser.parse_args()

    # Convert the PsychoPy log file to a Pandas DataFrame
    log_path = args.input
    input_df = psychopy2pandas(log_path)

    # Convert the Pandas DataFrame to a BIDS-compatible DataFrame
    output_df = pandas2bids(input_df)

    # Save the BIDS-compatible DataFrame to the specified output file
    output_path = args.output
    output_df.to_csv(output_path, sep="\t", index=False, float_format="%.5f", na_rep="n/a")


if __name__ == "__main__":
    main()
