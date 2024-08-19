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
"""Generate sessions plan."""
import datetime
import random
import click
from collections import defaultdict
import pandas as pd


SCANNER_NAME_MAPPINGS = {
    "Prisma": "060",
    "Vida07": "034",
    "VidaFit": "030",
}


@click.group()
@click.version_option(message="HCPh Session Generator")
def cli() -> None:
    """
    Command-line tool for generating session plans.

    Example::

        python code/sessions/hcph-sessions.py generate -o include/sessions.tsv \\
            --md-output include/sessions.md

    """


@cli.command()
@click.option("-s", "--seed", type=click.IntRange(min=0), default=20231020)
@click.option("-o", "--output", type=click.File("w"))
@click.option("-n", "--num-sessions", type=click.IntRange(min=1), default=36)
@click.option("-i", "--scanner-ids", type=str, multiple=True)
@click.option(
    "--base-date", type=click.DateTime(formats=["%Y-%m-%d"]), default="2023-10-20"
)
@click.option("--sessions-per-day", type=click.IntRange(min=1), default=2)
@click.option("--md-output", type=click.File("w"))
def generate(
    seed: int,
    output: click.utils.LazyFile,
    num_sessions: int,
    scanner_ids: list[str],
    base_date: datetime.date,
    sessions_per_day: int,
    md_output: click.utils.LazyFile,
) -> None:
    """
    Generate a session plan.

    Parameters
    ----------
    seed : int
        Random seed for session plan generation.
    output : file
        File to write the session plan in a tabular format.
    num_sessions : int
        Number of sessions to generate.
    scanner_ids : list
        Identifiers of the scanners (shuffles order).
    base_date : datetime.date
        Base date for session scheduling.
    sessions_per_day : int
        Number of sessions to schedule per day.
    md_output : file
        File to write the session plan in Markdown format.

    Returns
    -------
    None
        Generates a session plan with the specified number of sessions,
        randomizing encoding types, and scheduling them over days.

    """

    random.seed(seed)

    num_devices = len(scanner_ids)

    sessions = list(range(1, num_sessions + 1))
    days = [
        base_date + datetime.timedelta(days=delta)
        for s in range(num_sessions)
        for delta in [s] * sessions_per_day
    ][:num_sessions]

    datadict = defaultdict(list)
    for sid in scanner_ids:
        encodings = (["LR", "RL", "PA", "AP"] * (num_sessions // 4 + 1))[:num_sessions]
        random.shuffle(encodings)

        if num_devices == 1:
            datadict = {
                "session": sessions,
                "day": days,
                "PE": encodings,
            }
        else:
            datadict["day"] += days
            datadict["device"] += [sid] * num_sessions
            datadict["session"] += sessions
            datadict["PE"] += encodings

    table = pd.DataFrame(datadict)

    if num_devices > 1:
        indexes = list(range(len(table)))
        random.shuffle(indexes)

        table = table.iloc[indexes].sort_values(["day", "session"])

        table["sessionwise_order"] = [2, 3, 4] * num_sessions
        table.loc[table["device"] == "Prisma", "sessionwise_order"] = 1
        table = table.sort_values(["day", "session", "sessionwise_order"])
        table["sessionwise_order"] = [1, 2, 3] * num_sessions

        table["bids_id"] = [
            f"{row['session']:03d}{row['sessionwise_order']:02d}"
            f"{SCANNER_NAME_MAPPINGS[row['device']]}"
            for _, row in table.iterrows()
        ]
        table.reset_index(drop=True)
        table.drop(labels=["sessionwise_order"], axis=1, inplace=True)

    table["day"] = table["day"].apply(lambda x: x.date())

    # print(table.to_markdown(index=False))
    # print(table[table["device"] == "Prisma"].to_markdown(index=False))
    # print(table[table["device"] == "Vida07"].to_markdown(index=False))
    # print(table[table["device"] == "VidaFit"].to_markdown(index=False))

    if output:
        table.to_csv(output, index=None, sep="\t")

    if md_output:
        md_output.write(table.to_markdown(index=False))


if __name__ == "__main__":
    """Install entry-point"""
    cli()
