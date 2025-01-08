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
#SBATCH --account {{ secrets.curnagl.account | default('<someaccount>')}} 
#SBATCH --mail-type ALL 
#SBATCH --mail-user <email>@unil.ch
#
# Job settings
#SBATCH --job-name fmriprep
#SBATCH --partition cpu
#SBATCH --cpus-per-task 10
#SBATCH --mem 10G 
#SBATCH --time 24:00:00 
#SBATCH --export NONE
#SBATCH --chdir /scratch/oesteban
#
# Logging
#SBATCH --output /users/%u/logs/%x-%A-%a.out
#SBATCH --error /users/%u/logs/%x-%A-%a.err

ml singularityce gcc

mkdir -p {{ secrets.data.curnagl_workdir | default('<workdir>')}}/data/derivatives
mkdir -p /scratch/oesteban/fmriprep

export SINGULARITYENV_FS_LICENSE=$HOME/.freesurfer.txt
singularity exec --cleanenv \
        -B {{ secrets.data.curnagl_workdir | default('<workdir>')}}/data/hcph-dataset:/data/datasets/hcph/ \
        -B {{ secrets.data.curnagl_workdir | default('<workdir>')}}/data/derivatives/:/out \
        -B {{ secrets.data.curnagl_workdir | default('<workdir>')}}/data/hcph-fmriprep/:/derivatives \
        -B /scratch/oesteban/fmriprep:/tmp \
        docker://nipreps/fmriprep:24.1.1 \
        fmriprep /data/datasets/hcph/ /out/fmriprep-24.1.1 participant \
        --participant-label 001 \
        --bids-database-dir /data/datasets/hcph/.bids-index/ \
        --nprocs 4 --omp-nthreads ${SLURM_CPUS_PER_TASK} \
        -w /tmp/ -vv --skip-bids-validation --anat-only
