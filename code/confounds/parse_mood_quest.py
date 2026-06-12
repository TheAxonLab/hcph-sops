# Copyright 2025 The Axon Lab <theaxonlab@gmail.com>
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
import requests
import re
import pandas as pd
from pathlib import Path

save_data_path = Path("/data/datasets/hcph-mood-quest.tsv")


def parse_issue(text):
    # Normalize line endings and delimiters
    text = text.replace("\r\n", "\n")

    # Split entries using '### ' as a delimiter
    entries = re.split(r"### ", text)[1:]  # Skip the first empty split if any

    # Extract key-value pairs
    data = {}
    for entry in entries:
        lines = entry.strip().split("\n\n")
        key = lines[0].strip()
        value = lines[1].strip() if len(lines) > 1 else "n/a"

        # Special handling for 'Slept during scan' checkboxes
        if key.lower().startswith("slept during scan"):
            sleep_stages = {
                "scan": "Slept during session",
                "T1w": "Slept during T1w",
                "diffusion": "Slept during diffusion",
                "QCT task": "Slept during QCT task",
                "rest task": "Slept during rest task",
                "BHT task": "Slept during BHT task",
            }
            for stage, col_name in sleep_stages.items():
                match = re.search(
                    rf"- \[\s*(x?)\s*\]\s*I slept during the {re.escape(stage)}",
                    value,
                    re.IGNORECASE,
                )
                if match:
                    data[col_name] = "Yes" if match.group(1).lower() == "x" else "No"
                else:
                    data[col_name] = "n/a"
        else:
            # Remove indications in parentheses from the value (except for kind of precipitations)
            if key != "Kind of precipitation":
                value = re.sub(r"\s*\(.*?\)", "", value).strip()

            # Hours spent in bed the previous night have been encoded in diverse format, let's standardize it
            if key == "Time spent in bed the previous night":
                # Normalize hours spent in bed to float
                if re.match(
                    r"^\d+(\.\d+)?$", value
                ):  # Check if already in float format
                    pass  # Keep the value as is
                else:
                    match = re.search(r"(\d+)(?:h|:)?(?:\s*(\d+)\s*(?:min)?)?", value)
                    if match:
                        hours = int(match.group(1))
                        minutes = int(match.group(2)) if match.group(2) else 0
                        value = str(hours + minutes / 60)
                    else:
                        value = "n/a"

            # Handle generic checkboxes
            if "- [X]".lower() in value.lower():
                value = "Yes"
            elif "- [ ]" in value:
                value = "No"

            # MR room temperature, humidity ... appear 3x under the same name in the generalizability sessions questionnaire
            # We need to store the three values to correctly match them with session order later
            if key in data:
                if isinstance(data[key], list):
                    data[key].append(value)
                else:
                    data[key] = [data[key], value]
            else:
                data[key] = value

    return data


def match_info_sessions(info_dict, issues_info, title):
    # Extract session and subject number from the title
    # The issue title for the before questionnaire of generalizability session
    # encodes several session numbers
    matches = re.findall(r"sub-(\d+)_ses-2(\d{2})(\d{2})(\d{3})", title)

    session_order_map = {
        "01": "First scanner",
        "02": "Second scanner",
        "03": "Third scanner",
    }

    scanner_index_map = {"060": "Prisma", "034": "Vida", "030": "VidaFit"}

    session_order_map_pe = {
        "01": "PE direction on the first scanner",
        "02": "PE direction on the second scanner",
        "03": "PE direction on the third scanner",
    }

    for participant_id, scanner_repl, scanner_order, scanner_index in matches:
        # Extract the scanner name and phase encoding direction corresponding to the session order
        scanner_key = session_order_map.get(scanner_order)
        scanner_value = info_dict.get(scanner_key)

        # Sanity check that scanner name reported in mood questionnaire correspond to the one in the title
        scanner_name = scanner_index_map.get(scanner_index)
        # if value was not entered in the questionnaire, impute the expected name extracted from issue title
        if scanner_value == "None" or scanner_value is None:
            scanner_value = scanner_name
        else:
            assert (
                scanner_value == scanner_name
            ), f"Scanner index in the title ({scanner_index} = {scanner_name}) does not match the one in the questionnaire '{scanner_value}'."

        pe_key = session_order_map_pe.get(scanner_order)
        pe_value = info_dict.get(pe_key)
        # BIDS specification require missing values to be indicated with 'n/a'
        if pe_value == "None":
            pe_value = "n/a"

        base_dict = {
            "participant_id": participant_id,
            "session_number": f"2{scanner_repl}{scanner_order}{scanner_index}",
            "scanner": scanner_value,
            "PE direction": pe_value,
        }

        # Copy all non-room-environment keys but don't copy the column indicating session-specific info
        for k, v in info_dict.items():
            if k not in [
                "MR room temperature (°C)",
                "MR room humidity (%)",
                "MR room atmospheric pressure (hPa)",
                "MR helium level (%)",
                "First scanner",
                "Second scanner",
                "Third scanner",
                "PE direction on the first scanner",
                "PE direction on the second scanner",
                "PE direction on the third scanner",
            ]:
                base_dict[k] = v

        scanner_order_idx = int(scanner_order) - 1
        for env_key in [
            "MR room temperature (°C)",
            "MR room humidity (%)",
            "MR room atmospheric pressure (hPa)",
            "MR helium level (%)",
        ]:
            env_list = info_dict.get(env_key, [])
            if isinstance(env_list, list):
                base_dict[env_key] = env_list[scanner_order_idx]
            elif isinstance(env_list, str) and "VF" in env_list:
                # in the first session of the generalizability protocol, we indicated the temperature with VF: 21.1, V:19.8
                if scanner_name == "VidaFit":
                    base_dict[env_key] = re.search(
                        r"VF: (\d+(\.\d+)?)", env_list
                    ).group(1)
                elif scanner_name == "Vida":
                    base_dict[env_key] = re.search(r"V:(\d+(\.\d+)?)", env_list).group(
                        1
                    )
                else:
                    # We forgot to record the value for the prisma scanner
                    base_dict[env_key] = "n/a"

        # Replicate the info_dict for each session
        issues_info.append(base_dict)

    return issues_info


def extract_issues_info(
    issue_title_pattern,
    token_path="/home/cprovins/token_axonlab.txt",
    repo_owner="TheAxonLab",
    repo_name="hcph-mood-quest",
):
    # Read token
    with open(token_path, "r") as file:
        token = file.read().strip()

    # GitHub API headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    issues_info = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
        params = {"state": "all", "per_page": 100, "page": page}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            raise ValueError(
                f"GitHub API returned 404: Resource not found at {url}. "
                "This could be due to insufficient permissions. Please check your token's access rights."
            )

        issues = response.json()

        # Stop if no more issues
        if not issues:
            break

        for issue in issues:
            title = issue["title"]
            if re.search(issue_title_pattern, title):
                # Get the issue body
                issue_body = issue["body"]

                # Parse the text
                info_dict = parse_issue(issue_body)

                # We need to carefully handle the infos from the generalizability sessions
                # because the before questionnaire includes most info apply to all sessions
                # indicated in the issue title, but some info correspond to only one session
                if "ses-2" in title and "[BEFORE]" in title:
                    issues_info = match_info_sessions(info_dict, issues_info, title)
                else:
                    # Extract session and subject number from the title
                    match = re.search(r"sub-(\d+)_ses-([a-zA-Z0-9]+)", title)
                    if match:
                        participant_id = match.group(1)
                        session_number = match.group(2)
                        # Add subject and session number at the beginning of the data_dict
                        info_dict = {
                            "participant_id": participant_id,
                            "session_number": session_number,
                            **info_dict,
                        }

                    # Append the data_dict to the list
                    issues_info.append(info_dict)

        page += 1

    return issues_info


## Parse the confounds registered before and after the sessions separately and then merge the dataframes
## Parse the confounds of the reliability sessions first
issues_before_info = extract_issues_info(r"\[MOOD\](?:\[BEFORE\])? sub-001_ses-\d+")
issues_after_info = extract_issues_info(r"\[MOOD\]\[AFTER\] sub-001_ses-\d+")

# Convert the list of dictionaries to a DataFrame
df_before = pd.DataFrame(issues_before_info)
df_after = pd.DataFrame(issues_after_info)

# Merge the confounds collected after the session into the confounds collected before the session
df = pd.merge(
    df_before,
    df_after,
    how="left",
    on=["participant_id", "session_number"],
    suffixes=(None, "_after"),
)

# Merge same column before and after
df["Slept during session"] = df["Slept during session"].combine_first(
    df["Slept during session_after"]
)
df["Slept during T1w"] = df["Slept during T1w"].combine_first(
    df["Slept during T1w_after"]
)
df["Slept during diffusion"] = df["Slept during diffusion"].combine_first(
    df["Slept during diffusion_after"]
)
df["Slept during QCT task"] = df["Slept during QCT task"].combine_first(
    df["Slept during QCT task_after"]
)
df["Slept during rest task"] = df["Slept during rest task"].combine_first(
    df["Slept during rest task_after"]
)
df["Slept during BHT task"] = df["Slept during BHT task"].combine_first(
    df["Slept during BHT task_after"]
)
df["Rumination"] = df["Rumination"].combine_first(df["Rumination_after"])
df["Anxiety"] = df["Anxiety"].combine_first(df["Anxiety_after"])
df["Physical pain during scan"] = df["Physical pain during scan"].combine_first(
    df["Physical pain during scan_after"]
)
df.drop(
    columns=[
        "Rumination_after",
        "Anxiety_after",
        "Physical pain during scan_after",
        "Are you sure you filled all entries ?_after",
        "Slept during session_after",
        "Slept during T1w_after",
        "Slept during diffusion_after",
        "Slept during QCT task_after",
        "Slept during rest task_after",
        "Slept during BHT task_after",
    ],
    inplace=True,
)

## Manual corrections
# Indicate units or scale range in the column name
df.rename(columns={"Scan date": "date"}, inplace=True)
df.rename(columns={"Scan time": "time"}, inplace=True)
# Harmonize time format with other columns
df["time"] = (
    df["time"]
    .str.replace("-", ":", regex=False)
)

df.rename(
    columns={"NSAIDs intake in the last 24h": "nsaids"},
    inplace=True,
)
df.rename(
    columns={"Alcohol intake in the last 24h": "alcohol"},
    inplace=True,
)
df.rename(
    columns={"Triptans intake in the last 24h": "triptans"},
    inplace=True,
)
# Remove "mg" from values in the "NSAIDs intake in the last 24h (mg)" column
df["nsaids"] = (
    df["nsaids"]
    .str.replace("mg", "", regex=False)
    .str.replace("ibuprofen", "", regex=False)
    .str.strip()
)
df.rename(
    columns={"General health rating": "general_health"},
    inplace=True,
)
df.rename(
    columns={"General stress rating": "general_stress"},
    inplace=True,
)
df.rename(
    columns={
        "Ease of concentration": "ease_concentration"
    },
    inplace=True,
)
df.rename(columns={"Sleep quality": "sleep_quality"}, inplace=True)
df.rename(
    columns={
        "Can remember dreams from previous night": "remember_dreams"
    },
    inplace=True,
)
df.rename(
    columns={
        "Frequency of day dreams (mindwandering) in the last 24h": "day_dreams"
    },
    inplace=True,
)
df.rename(
    columns={
        "Time went to bed the previous night": "time_to_bed"
    },
    inplace=True,
)
df.rename(
    columns={
        "Time spent in bed the previous night": "time_in_bed"
    },
    inplace=True,
)
df.rename(
    columns={
        "Physical pain during scan": "physical_pain"
    },
    inplace=True,
)
# Remove "k" and indicate thousands in the column name
df.rename(
    columns={"Distance walked in the last 24h": "distance_walked"},
    inplace=True,
)
df["distance_walked"] = (
    df["distance_walked"]
    .str.replace("k", "", regex=False)
    .str.replace("m", "", regex=False)
    .str.strip()
)
df.rename(
    columns={"Number of stories climbed in the last 24h": "stories_climbed"},
    inplace=True,
)
df.rename(
    columns={"Calories burned in the last 24h": "calories"},
    inplace=True,
)
df["calories"] = (
    df["calories"]
    .str.replace("k", "", regex=False)
    .str.strip()
)

# Now that we indicated scale range in the column name, we can remove it from values
df.replace("1 (worst)", "1", inplace=True)
df.replace("6 (high concentration)", "2", inplace=True)
df.replace("6 (best)", "2", inplace=True)

# Remove commas that indicate thousands
df.rename(
    columns={"Number of steps made in the last 24h": "steps"},
    inplace=True,
)
df["steps"] = df[
    "steps"
].str.replace(",", "", regex=False)

# Underscore column names
df.rename(
    columns={"PE direction": "pe_dir"},
    inplace=True,
)
df.rename(
    columns={"Outside temperature range": "weather_temperature"},
    inplace=True,
)
df.rename(columns={"Wind": "weather_wind"}, inplace=True)
df.rename(columns={"Precipitation": "weather_precipitation"}, inplace=True)
df.rename(columns={"Kind of precipitation": "weather_precipitation_type"}, inplace=True)
df.rename(columns={"Atmospheric pressure": "weather_pressure"}, inplace=True)
df.rename(columns={"Relative humidity": "weather_humidity"}, inplace=True)
df.rename(columns={"Hours of daylight": "weather_daylight"}, inplace=True)
df.rename(columns={"Blood pressure (mmHg, systolic and diastolic)": "blood_pressure"}, inplace=True)
df.rename(columns={"Caffeine intake in the last 24h (# cups)": "caffeine_24h"}, inplace=True)
df.rename(columns={"Caffeine intake in the last 2h (# cups)": "caffeine_2h"}, inplace=True)

df.rename(
    columns={"Weight (kg)": "weight"},
    inplace=True,
)
df.rename(
    columns={"Hours of work in the last 24h": "beh_work"},
    inplace=True,
)
df.rename(
    columns={"Hours of free time in the last 24h": "beh_freetime"},
    inplace=True,
)
df.rename(
    columns={"Hours spent in sport in the last 24h": "beh_sport"},
    inplace=True,
)
df.rename(
    columns={"Hours spent outdoors in the last 24h": "beh_outdoors"},
    inplace=True,
)
df.rename(
    columns={"Hours spent directly interacting with electronic devices in the last 24h": "beh_electronic_devices"},
    inplace=True,
)
df.rename(
    columns={"Hours spent in active social interaction in the last 24h": "beh_active_social"},
    inplace=True,
)
df.rename(
    columns={"Hours spent in passive social interaction in the last 24h": "beh_passive_social"},
    inplace=True,
)
df.rename(
    columns={"Did you remove your ring or other jewelries ?": "remove_jewelry"},
    inplace=True,
)
df.rename(
    columns={"Are you sure you filled all entries ?": "filled_all_entries"},
    inplace=True,
)
df.rename(
    columns={"MR room temperature (°C)": "mr_room_temperature"},
    inplace=True,
)
df.rename(
    columns={"MR room humidity (%)": "mr_room_humidity"},
    inplace=True,
)
df.rename(
    columns={"MR room atmospheric pressure (hPa)": "mr_room_pressure"},
    inplace=True,
)
df.rename(
    columns={"MR helium level (%)": "mr_room_helium"},
    inplace=True,
)
df.rename(
    columns={"Slept during session": "slept_session"},
    inplace=True,
)
df.rename(
    columns={"Slept during T1w": "slept_t1w"},
    inplace=True,
)
df.rename(
    columns={"Slept during diffusion": "slept_diffusion"},
    inplace=True,
)
df.rename(
    columns={"Slept during QCT task": "slept_qct"},
    inplace=True,
)
df.rename(
    columns={"Slept during rest task": "slept_rest"},
    inplace=True,
)
df.rename(
    columns={"Slept during BHT task": "slept_bht"},
    inplace=True,
)
df.rename(
    columns={"If you slept during the T1w": "time_slept_t1w"},
    inplace=True,
)
df.rename(
    columns={"If you slept during the rest task": "time_slept_rest"},
    inplace=True,
)
df.rename(
    columns={"If you slept during the diffusion": "time_slept_diffusion"},
    inplace=True,
)
df.rename(
    columns={"More detail about rumination, anxiety or pain (optional)": "details_rumination_anxiety_pain"},
    inplace=True,
)
# BIDS specification indicates to encode missing values as "n/a"
df.fillna("n/a", inplace=True)
df.replace("_No response_", "n/a", inplace=True)
df.replace("NONE", "n/a", inplace=True)

# Impute "Slept during session" if it is "n/a", with the union of the columns encoding sleep
slept_columns = [col for col in df.columns if col.startswith("slept_")]
for index, row in df.iterrows():
    if row["slept_session"] == "n/a":
        df.at[index, "slept_session"] = (
            "Yes" if any(row[col] == "Yes" for col in slept_columns)
            else "No"
        )


# Session 14 was not finished if the tickbox were not ticked it's not because the subject did not sleep, but because the form was not filled
df.loc[df["session_number"] == "014", slept_columns] = "n/a"

# Complete that the scanner used for the reliability sessions was the Prisma
df.loc[df["session_number"].str.startswith("0"), "scanner"] = "Prisma"

# put column name in small caps
df.columns = df.columns.str.lower()

# Save to CSV
df.to_csv(save_data_path, sep="\t", index=False)
