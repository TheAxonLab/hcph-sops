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

#SBATCH --partition=russpold
#SBATCH --mem=55GB
#SBATCH --cpus-per-task=16
#SBATCH --time=20:00:00
#SBATCH --job-name=fmriprep
#SBATCH --error="slurm-%A_%a.err"

# Submit a Single Session through fMRIPrep

ARGS=($@)
DATADIR=$1
STUDY=`basename $DATADIR`

if [[ -n $SLURM_ARRAY_TASK_ID ]]; then
  SES=${ARGS[`expr ${SLURM_ARRAY_TASK_ID} + 1`]}
else
  SES=$2
fi

echo "Processing: $SES"

IMG="/oak/stanford/groups/russpold/users/cprovins/singularity_images/fmriprep-23.1.4.simg"

WORKDIR="${L_SCRATCH}/fmriprep/${STUDY}/${SES}"
mkdir -p ${WORKDIR}
OUTDIR="${DATADIR}/derivatives"
mkdir -p $OUTDIR

PATCHES=""

BINDINGS="-B $DATADIR/inputs:/data:ro \
-B ${WORKDIR}:/work \
-B ${OUTDIR}:/out \
-B $DATADIR/code/license.txt:/opt/freesurfer/license.txt \
-B ${HOME}/.cache/templateflow/tpl-MNI152NLin6Asym/:${HOME}/.cache/templateflow/tpl-MNI152NLin6Asym/
$PATCHES"

FMRIPREP_CMD="/data /out/fmriprep-23.1.4 participant \
  -w /work \
  --bids-filter-file /work/filter_file_$SES.json \
  --skip_bids_validation \
  --fs-subjects-dir /out/fmriprep-23.1.4/sourcedata/freesurfer \
  --anat-derivatives /out/fmriprep-23.1.4 \
  --nprocs 4 --mem 45G --omp-nthreads 8 -vv"

#Create json file to filter one session only
echo '{"bold": {"datatype": "func", "session": "'${SES#*-}'", "suffix": "bold"}}' > ${WORKDIR}/filter_file_${SES}.json

SING_CMD="singularity run -e $BINDINGS $IMG $FMRIPREP_CMD"
echo $SING_CMD
$SING_CMD
echo "Completed with return code: $?"
