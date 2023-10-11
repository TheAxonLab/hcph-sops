#!/bin/bash
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
# STATEMENT OF CHANGES: This file is derived from work of the Nipreps
# developers and has been adapted to run smoothly on our particular 
# dataset.
#
# ORIGINAL WORK'S ATTRIBUTION NOTICE:
#
#     Copyright 2021 The NiPreps Developers <nipreps@gmail.com>
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

DATADIR="/oak/stanford/groups/russpold/inprocess/cprovins/hcph-pilot/"
SUB="sub-001"
pushd $DATADIR/inputs/$SUB > /dev/null
ALL_SES=(`ls -d ses-*`)
popd > /dev/null

#Remove session with no fMRI
SES=()
for S in "${ALL_SES[@]}"; do
        if [ -d "$DATADIR/inputs/$SUB/$S/func" ]; then
                SES+=("$S")
        else
            	echo "Session '$S' has no functional scan."
        fi
done

echo "Submitting `basename $DATADIR` with ${#SES[@]} sessions"
# remove one since we are starting at 0
JOBS=`expr ${#SES[@]} - 1`
sbatch --array=0-$JOBS ss-fmriprep.sh $DATADIR ${SES[@]}

