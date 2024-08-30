#!/bin/bash

DICOMFILES=$1
DICOMROOT='/data/datasets/hcph-pilot-sourcedata/'

DICOMROOT=$( python -c "path = \"${DICOMFILES}\".split('sub-2022_11_07_')[0]; print(path, end='')" )
SESSION=$( python -c "path = \"${DICOMFILES}\".split('sub-2022_11_07_')[-1].split('_'); print(f'2{path[1]}{path[2]}0{path[0]}', end='')" )
SESSION_ROOT=$( dirname $DICOMFILES )
session_id=$( basename $DICOMFILES )

session_num=$( expr ${SESSION:1:2} + 0 )
declare -A session_device=( ["030"]="VidaFit" ["060"]="Prisma" ["034"]="Vida07" )
session_date=$( date -d"${session_id:4:8}" +%d.%m.%Y )

echo "Converting Session ${session_num} on ${session_device[${SESSION: -3}]} (${session_date})"

cmd="heudiconv -s \"001\" -ss \"${SESSION}\" -b -o /data/datasets/hcph/ -f $HOME/workspace/hcph-sops/code/heudiconv/reproin.py --files $DICOMFILES --minmeta"

git checkout master
datalad update --how ff-only

echo "Switching to new branch \"add/${SESSION}\":"
git checkout -b add/${SESSION}

echo "Executing $cmd.."
eval $cmd

echo "Adding to DataLad dataset..."
rm -rf .heudiconv/
rm sub-001/ses-$SESSION/func/sub-001_ses-${SESSION}_task-rest_dir-*_events.tsv
find sub-001/ses-$SESSION -name "*.tsv" -or -name "*.json" -or -name "*.bvec" -or -name "*.bval" | xargs datalad save --to-git -m "add($SESSION): new session metadata"
find sub-001/ses-$SESSION -name "*.nii.gz" -or -name "*_eyetrack.tsv.gz" -or -name "*_physio.tsv.gz" -or -name "*_stim.tsv.gz" | xargs datalad save -m "add($SESSION): new session NIfTI data"
echo "Success!"

git clean -fd
git checkout -- task-*_bold.json

echo "Updating PyBIDS database..."
datalad unlock .bids-index/layout_index.sqlite
/home/oesteban/.miniconda/bin/pybids layout --reset-db --no-validate --index-metadata . .bids-index/
datalad save -m 'maint: update PyBIDS index' .bids-index/layout_index.sqlite
datalad push --to=github

echo "Creating PR..."
body_file=$( mktemp )
echo "Outputs of BIDS conversion:" > $body_file
echo '```TSV' >> $body_file
echo '' >> $body_file
cat /data/datasets/hcph/sub-001/ses-${SESSION}/sub-001_ses-${SESSION}_scans.tsv >> $body_file
echo '```' >> $body_file

# Retrieve original issue number:
gh_issue=$( gh search issues --match title --repo TheAxonLab/hcph-dataset --json number --jq .[0].number  -- is:open label:scan $SESSION )
if [ ! -z "$gh_issue" ]; then
  echo '' >> $body_file
  echo "Prompted-by: TheAxonLab/hcph-dataset#${gh_issue}." >> $body_file
fi

pr_url=$( gh pr create -B "master" -r "celprov" -a "@me" -t "ADD: ${SESSION} | Session ${session_num} on ${session_device[${SESSION: -3}]} (${session_date})" -F $body_file | tail -n1 )

echo "Compacting DICOMs..."

pushd ${SESSION_ROOT}
tar vczf $DICOMROOT/DICOMS/oe/${session_id}.tar.gz ${session_id} && rm -rf ${session_id}
popd

rmdir ${SESSION_ROOT}
chmod a-w $DICOMROOT/DICOMS/oe/${session_id}.tar.gz

echo "Number of lines in scan file (should be 26): $( wc -l sub-001/ses-${SESSION}/sub-001_ses-${SESSION}_scans.tsv )"
echo "PR created: $pr_url"

