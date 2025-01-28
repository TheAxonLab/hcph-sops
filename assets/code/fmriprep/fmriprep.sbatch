#!/bin/bash
# Copyright 2024 The Axon Lab <theaxonlab@gmail.com> 
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
###########################################################################
#
# General SLURM settings
#SBATCH --mail-type=ALL 
#SBATCH --mail-user={{ secrets.data.curnagl_email | default('<email>@unil.ch') }}
#
# Job settings
#SBATCH --job-name=fmriprep
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=10
#SBATCH --mem=128G 
#SBATCH --time=24:00:00 
#SBATCH --export=NONE
#SBATCH --chdir=/scratch/%u
#
# Logging
#SBATCH --output=/users/%u/logs/%x-%A-%a.out
#SBATCH --error=/users/%u/logs/%x-%A-%a.err

ml singularityce gcc

WORKDIR={{ secrets.data.curnagl_workdir | default('<workdir>')}}
SCRATCH={{ secrets.data.curnagl_scratchdir | default('<scratchdir>')}}/fmriprep/
OUTDIR=$WORKDIR/data/derivatives/fmriprep-generalization/

mkdir -p $OUTDIR
mkdir -p $SCRATCH

export SINGULARITYENV_FS_LICENSE=$HOME/freesurfer.txt

singularity exec --cleanenv \
        -B $WORKDIR/workspace/fmriprep/fmriprep:/opt/conda/envs/fmriprep/lib/python3.11/site-packages/fmriprep \
	    -B $WORKDIR/data/hcph-dataset:/data/datasets/hcph/ \
        -B $OUTDIR:/out \
        -B $SCRATCH:/tmp \
        -B ${HOME}/.cache/templateflow/tpl-MNI152NLin6Asym/:${HOME}/.cache/templateflow/tpl-MNI152NLin6Asym/ \
        docker://nipreps/fmriprep:24.1.1 \
        fmriprep /data/datasets/hcph/ /out participant \
        --participant-label 001 \
        --fs-subjects-dir /out/sourcedata/freesurfer \
        --nprocs 4 --omp-nthreads ${SLURM_CPUS_PER_TASK} \
        -w /tmp/ -vv --skip-bids-validation

echo "Completed with return code: $?"
