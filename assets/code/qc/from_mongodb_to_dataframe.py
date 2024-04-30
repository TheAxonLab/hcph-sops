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

# !! To run this script, you need to have run docker-compose up in the qkay repository to have running containers !!

from pymongo.mongo_client import MongoClient

# Path PyMongo to allow using PyMongoArrow’s functionality directly to Collection instances of PyMongo
from pymongoarrow.monkey import patch_all

patch_all()

# Connect to the MongoDB database
client = MongoClient("localhost", 27017)

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# List available databases
database_names = client.list_database_names()
for db_name in database_names:
    print(db_name)

# Select the database and extract all ratings
db = client.data_base_qkay
ratings = db.ratings
df = ratings.find_pandas_all({"dataset": "mriqc-23.2.0-withoutdwi"})

# Keep only lines for which "subject" contains T1w
modality = "bold"
df = df[df["subject"].str.contains(modality)]

# Drop columns we don't need
df = df.drop(columns=["_id", "md5sum"])

# Replace newline characters in the 'comments' column with a space
# so that comments do not get split into multiple lines
df["comments"] = df["comments"].str.replace("\n", ", ")

# Save dataframe to csv so we can load it in R
df.to_csv(f"data/desc-ratings_{modality}.tsv", sep="\t", index=False)

# Close the connection
client.close()
