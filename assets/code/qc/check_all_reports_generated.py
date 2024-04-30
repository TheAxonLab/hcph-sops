# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
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

import glob
import os

# Set the paths
cprovins = "/home/data"
data_dir = os.path.join(cprovins, "hcph")
derivatives_dir = os.path.join(cprovins, "hcph-derivatives", "mriqc-24.0.0/")

# Use glob to find all folders matching the pattern ses-*
session_folders = glob.glob(os.path.join(data_dir, "sub-001", "ses-[0-9]*"))

# Extract session numbers from folder names
sessions = [folder.split("-")[-1] for folder in session_folders]

# Define the patterns you want to filter in filenames
patterns = [
    "acq-undistorted_T1w",
    "acq-undistorted_T2w",
    "acq-original_T2w",
    "task-qct_*_bold",
    "task-bht_*_bold",
    "task-rest_*_bold",
    "acq-highres_dir-*_dwi",
]

# Iterate over each session
missing_reports = {}
for session in sessions:
    # Initialize a list to store missing reports for this session
    missing_reports[session] = []

    # Iterate over each pattern
    for pattern in patterns:
        # Construct the regex pattern
        glob_pattern = f"sub-001_ses-{session}_{pattern}.html"

        # Use glob to check if any report files matching the pattern exist
        report_files = glob.glob(os.path.join(derivatives_dir, glob_pattern))

        if not report_files:
            missing_reports[session].append(pattern)

# Print sessions with missing reports
for session_name, missing_patterns in missing_reports.items():
    if missing_patterns:
        print(f"Session {session_name} is missing reports for the following patterns:")
        for pattern in missing_patterns:
            print(f" - {pattern}")
    else:
        print(f"All reports found for session {session_name}.")
