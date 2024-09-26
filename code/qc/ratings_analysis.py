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
#

import pandas as pd
from pathlib import Path

# Load the HCPh data
modalities = ["T1w", "bold"]

for modality in modalities:
    print(f"---------------{modality.upper()}---------------")
    ratings_path = Path(f"./data/desc-ratings_{modality}.tsv")
    df_ratings = pd.read_csv(ratings_path, sep="\t")

    # In case of duplicates, consider only the last rating
    df_ratings.drop_duplicates(subset="subject", keep="last", inplace=True)

    # Extract summary about the rating experience
    total_rating_time = df_ratings["time_sec"].sum()
    hours = total_rating_time // 3600
    minutes = (total_rating_time % 3600) // 60
    print(
        f"It took {df_ratings['rater_id'].iloc[0]} {hours} hours and {minutes} minutes to rate all the {modality} ({len(df_ratings)})."
    )

    average_time = total_rating_time / len(df_ratings)
    minutes = int(average_time // 60)
    seconds = int(average_time % 60)
    print(
        f"The average time to rate a {modality} image is {minutes} minutes and {seconds} seconds."
    )

    print(
        f"The average rating for {modality} images is {df_ratings['rating'].mean():.2f} ± {df_ratings['rating'].std():.2f}."
    )

    excluded = df_ratings[df_ratings["rating"] < 1.45]
    n_excluded = len(excluded)
    print("\n")
    print(f"{n_excluded} {modality} images were excluded from further analysis.")

    for index, row in excluded.iterrows():
        print(f"Image {row['subject']} was excluded because:")
        if row["artifacts"] != "[]":
            print(f"{row['artifacts']}.\n")
        if row["comments"]:
            print(f"{row['comments']}.\n")
