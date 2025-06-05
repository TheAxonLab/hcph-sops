import pandas as pd
from pathlib import Path


def get_confounds_scanstsv(dataset_path):
    """
    Extract and process confound information from a `scans.tsv` file.

    This function reads a `scans.tsv` file from the specified dataset path, processes
    its contents to extract relevant confound information, and returns a DataFrame
    with additional metadata columns.

    Parameters:
    -----------
    dataset_path : str
        The path to the dataset directory containing the `scans.tsv` file.

    Returns:
    --------
    pd.DataFrame
        A pandas DataFrame containing the processed confound information with the following columns:
        - `filename`: The original filename of the scan.
        - `acq_time`: The acquisition time of the scan.
        - `subject`: The subject identifier extracted from the filename.
        - `session`: The session identifier extracted from the filename.
        - `modality`: The modality of the scan (e.g., anat, func) extracted from the filename.
        - `task`: The task identifier extracted from the filename.
        - `pe_dir`: The phase encoding direction extracted from the filename.
        - `day_of_week`: The day of the week extracted from the acquisition time.
        - `time_of_day`: The rounded time of day extracted from the acquisition time.
    """

    ## Read the scans.tsv file
    dataset_path = Path(dataset_path)
    confounds_df = pd.read_csv(dataset_path / "scans.tsv", sep="\t")
    confounds_df.drop(columns=["randstr"], inplace=True)

    # Extract entities
    # Each echo and magnitude and phase part of each functional scans are recorded on separate line,
    # but we have only one final image so keep only one of the identical acq_time
    confounds_df = confounds_df.drop_duplicates(subset=["acq_time"])
    confounds_df = confounds_df.assign(
        subject=confounds_df["filename"].str.extract(r"sub-(\d+)/"),
        session=confounds_df["filename"].str.extract(r"ses-(\w+)/"),
        modality=confounds_df["filename"].str.split("/").str[2],
        task=confounds_df["filename"].str.extract(r"task-(\w+)_"),
        pe_dir=confounds_df["filename"].str.extract(r"dir-(\w+)_"),
    )

    # From the acq_time column, extract the day of week and time of day
    confounds_df = confounds_df.assign(
        datetime=pd.to_datetime(confounds_df["acq_time"])
    )
    confounds_df = confounds_df.assign(
        day_of_week=confounds_df["datetime"].dt.day_name(),
        time_of_day=confounds_df["datetime"].dt.round("H").dt.time,
    )
    confounds_df.drop(columns=["datetime"], inplace=True)

    return confounds_df


def get_iqms(
    iqms_path, iqm_of_interest=["fd_mean"]
):
    """
    Extract imaging quality metrics (IQMs) from a specified TSV file.
    This function reads a TSV file containing IQMs, extracts relevant metadata
    (subject, session, modality, and task) from the `bids_name` column, and filters
    the data to include only the specified IQMs of interest.
    Parameters:
    -----------
    iqms_path : str, optional
        Path to the TSV file containing the IQMs. Default is
        "/data/derivatives/hcph-mriqc/group_dwi.tsv".
    iqm_of_interest : list of str, optional
        List of column names corresponding to the IQMs to retain in the output.
        Default is ["fd_mean"].
    Returns:
    --------
    pd.DataFrame
        A pandas DataFrame containing the extracted metadata (subject, session,
        modality, task) and the specified IQMs of interest.
    """

    iqms_df = pd.read_csv(iqms_path, sep="\t")
    iqms_df = iqms_df.assign(
        subject=iqms_df["bids_name"].str.extract(r"sub-(\d+)_"),
        session=iqms_df["bids_name"].str.extract(r"ses-(\w+)_"),
        modality=iqms_df["bids_name"].str.split("_").str[-1],
        task=iqms_df["bids_name"].str.extract(r"task-(\w+)_"),
    )
    # Keep only the IQMs of interest
    iqms_df = iqms_df[["subject", "session", "modality", "task"] + iqm_of_interest]

    return iqms_df


def get_confounds_mood_issues(token_path="/home/cprovins/token_axonlab.txt"):
    """
    Extract confound data related to mood issues from a GitHub repository.

    This function retrieves issue data from a specified GitHub repository, processes
    the issue titles and bodies to extract relevant confound information, and compiles
    the data into a pandas DataFrame. The extracted confounds include caffeine intake
    (in the last 2 hours and 24 hours) and MR room temperature.

    Parameters:
    -----------
    token_path : str, optional
        Path to the file containing the GitHub personal access token.
        Default is "/home/cprovins/token_axonlab.txt".

    Returns:
    --------
    pd.DataFrame
        A pandas DataFrame containing the extracted confound data with the following columns:
        - `issue_title`: Title of the GitHub issue.
        - `subject`: The subject identifier extracted from the issue title.
        - `session`: The session identifier extracted from the issue title.
        - `caffeine_intake_2h`: Number of cups of caffeine consumed in the last 2 hours (int or None).
        - `caffeine_intake_24h`: Number of cups of caffeine consumed in the last 24 hours (int or None).
        - `room_temp_before`: MR room temperature in degrees Celsius (float or None).

    Notes:
    ------
    - A GitHub personal access token with theAxonLab as the resource owner is required
      to authenticate API requests.
    - Only confounds from the reliability sessions are retrieved, as the issues for
      generalizability sessions differ significantly in structure.
    """

    import requests
    import re

    ## Merge confounds retrieved from the manual issue logs
    # GitHub repository details
    repo_owner = "TheAxonLab"  # Replace with your GitHub username or org name
    repo_name = "hcph-mood-quest"
    # Read token from token.txt
    with open(token_path, "r") as file:
        token = file.read().strip()

    # GitHub API headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Regular expression to match issue titles with the optional [BEFORE] tag and confounds of interest
    issue_title_pattern = r"\[MOOD\](?:\[BEFORE\])? sub-001_ses-0\d{2}"
    caffeine_2h_pattern = r"### Caffeine intake in the last 2h \(# cups\)\s+(\d+)"
    caffeine_24h_pattern = r"### Caffeine intake in the last 24h \(# cups\)\s+(\d+)"
    room_temp_pattern = r"### MR room temperature \(°C\)\s+([\d.]+)"

    data = []
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

                # Extract caffeine intake and room temperature before scan
                caffeine_2h = re.search(caffeine_2h_pattern, issue_body)
                caffeine_24h = re.search(caffeine_24h_pattern, issue_body)
                room_temp = re.search(room_temp_pattern, issue_body)

                data.append(
                    {
                        "issue_title": title,
                        "caffeine_intake_2h": int(caffeine_2h.group(1))
                        if caffeine_2h
                        else None,
                        "caffeine_intake_24h": int(caffeine_24h.group(1))
                        if caffeine_24h
                        else None,
                        "room_temp_before": float(room_temp.group(1))
                        if room_temp
                        else None,
                    }
                )

        page += 1

    confounds_df = pd.DataFrame(data)
    confounds_df = confounds_df.assign(
        subject=confounds_df["issue_title"].str.extract(r"sub-(\d+)_"),
        session=confounds_df["issue_title"].str.extract(r"ses-([a-zA-Z0-9]+)(?:_|$)"),
    )

    return confounds_df


def get_confounds(
    dataset_path,
    iqms_path,
    iqm_of_interest=["fd_mean"],
):
    """
    Extract and merge confounds from various sources for a given dataset.

    This function retrieves confounds from a dataset, optionally merges them with
    image quality metrics (IQMs) if provided, and includes additional confounds
    found in GitHub issue logs.

    Parameters:
    -----------
    dataset_path : str
        The path to the dataset directory.
    iqms_path : str
        The path to the file containing IQMs. If provided, the IQMs will be merged
        with the confounds DataFrame.
    iqm_of_interest : list of str, optional
        A list of IQMs to extract from the IQMs file. Default is ["fd_mean"].

    Returns:
    --------
    pd.DataFrame
        A pandas DataFrame containing the merged confounds from the dataset, IQMs
        (if provided), and mood-related confounds.
    """

    confounds_df = get_confounds_scanstsv(dataset_path)

    ## If iqms_path is provided, read the IQMs and merge them with the confounds
    if iqms_path:
        iqms_df = get_iqms(iqms_path, iqm_of_interest)

        # Merge the fd_mean values into the confounds DataFrame
        confounds_df = pd.merge(
            confounds_df,
            iqms_df,
            on=["subject", "session", "modality", "task"],
            how="left",
        )

    coffee_temp_df = get_confounds_mood_issues()
    # Merge the fd_mean values into the confounds DataFrame
    confounds_df = pd.merge(
        confounds_df, coffee_temp_df, on=["subject", "session"], how="left"
    )
    confounds_df.drop(columns=["issue_title"], inplace=True)
    return confounds_df
