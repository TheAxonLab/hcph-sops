#!/bin/bash
#
# Automated intake of one new imaging session into the HCPh DataLad dataset.
#
# Given the path to a freshly downloaded PACS DICOM folder, this script:
#   1. derives the BIDS session id from the folder name,
#   2. updates the dataset and branches into `add/<session>`,
#   3. runs HeuDiConv (reproin heuristic) to convert DICOM -> BIDS,
#   4. saves NIfTI data to the annex and metadata to Git,
#   5. rebuilds the PyBIDS index,
#   6. pushes to GitHub and the RIA store (uploads data to the HPC),
#   7. opens a pull request (linking the originating dataset issue), and
#   8. compacts the DICOMs into a tarball to reclaim space.
#
# Usage:
#   bash add_session.sh <path-to-DICOM-session-folder>
#
# It is meant to be run from the root of the DataLad dataset working tree.
#
# Configuration (override by exporting before invoking; defaults reproduce the
# original pilot/wave-2 setup):
#   PARTICIPANT_PREFIX  registered patient-id prefix used to parse the session   [sub-2022_11_07_]
#   SUBJECT             BIDS subject label                                        [001]
#   BIDS_ROOT           dataset root / HeuDiConv output dir                       [/data/datasets/hcph]
#   SOPS_ROOT           local clone of this SOPs repository                       [$HOME/workspace/hcph-sops]
#   HEURISTIC           HeuDiConv heuristic file                                  [$SOPS_ROOT/code/heudiconv/reproin.py]
#   PYBIDS              pybids executable                                         [pybids]
#   DATASET_BRANCH      default branch of the dataset repository                  [master]
#   ISSUE_REPO          repo holding the per-session "scan" issues               [TheAxonLab/hcph-dataset]
#   REVIEWER            GitHub user to request review from                        [celprov]
#   DICOM_ARCHIVE       directory where DICOM tarballs are stored                 [<DICOM source root>/DICOMS/oe]
#   EXPECTED_SCANS      expected number of lines in the session scans.tsv         [26]

set -u

DICOMFILES=$1
if [ -z "${DICOMFILES:-}" ]; then
  echo "Usage: bash add_session.sh <path-to-DICOM-session-folder>" >&2
  exit 1
fi

# --- Configuration (env-overridable defaults) --------------------------------
: "${PARTICIPANT_PREFIX:=sub-2022_11_07_}"
: "${SUBJECT:=001}"
: "${BIDS_ROOT:=/data/datasets/hcph}"
: "${SOPS_ROOT:=$HOME/workspace/hcph-sops}"
: "${HEURISTIC:=${SOPS_ROOT}/code/heudiconv/reproin.py}"
: "${PYBIDS:=pybids}"
: "${DATASET_BRANCH:=master}"
: "${ISSUE_REPO:=TheAxonLab/hcph-dataset}"
: "${REVIEWER:=celprov}"
: "${EXPECTED_SCANS:=26}"

# Source root holding the participant folder (everything before PARTICIPANT_PREFIX),
# and the BIDS session id (derived from the encoding in the patient id).
DICOMROOT=$( python -c "path = \"${DICOMFILES}\".split('${PARTICIPANT_PREFIX}')[0]; print(path, end='')" )
SESSION=$( python -c "path = \"${DICOMFILES}\".split('${PARTICIPANT_PREFIX}')[-1].split('_'); print(f'2{path[1]}{path[2]}0{path[0]}', end='')" )
SESSION_ROOT=$( dirname $DICOMFILES )
session_id=$( basename $DICOMFILES )

: "${DICOM_ARCHIVE:=${DICOMROOT}/DICOMS/oe}"

session_num=$( expr ${SESSION:1:2} + 0 )
declare -A session_device=( ["030"]="VidaFit" ["060"]="Prisma" ["034"]="Vida07" )
session_date=$( date -d"${session_id:4:8}" +%d.%m.%Y )

echo "Converting Session ${session_num} on ${session_device[${SESSION: -3}]} (${session_date})"

cmd="heudiconv -s \"${SUBJECT}\" -ss \"${SESSION}\" -b -o ${BIDS_ROOT}/ -f ${HEURISTIC} --files $DICOMFILES --minmeta"

git checkout ${DATASET_BRANCH}
datalad update --how ff-only

echo "Switching to new branch \"add/${SESSION}\":"
git checkout -b add/${SESSION}

echo "Executing $cmd.."
eval $cmd

echo "Adding to DataLad dataset..."
rm -rf .heudiconv/
rm sub-${SUBJECT}/ses-$SESSION/func/sub-${SUBJECT}_ses-${SESSION}_task-rest_dir-*_events.tsv
find sub-${SUBJECT}/ses-$SESSION -name "*.tsv" -or -name "*.json" -or -name "*.bvec" -or -name "*.bval" | xargs datalad save --to-git -m "add($SESSION): new session metadata"
find sub-${SUBJECT}/ses-$SESSION -name "*.nii.gz" -or -name "*_eyetrack.tsv.gz" -or -name "*_physio.tsv.gz" -or -name "*_stim.tsv.gz" | xargs datalad save -m "add($SESSION): new session NIfTI data"
echo "Success!"

git clean -fd
git checkout -- task-*_bold.json

echo "Updating PyBIDS database..."
datalad unlock .bids-index/layout_index.sqlite
${PYBIDS} layout --reset-db --no-validate --index-metadata . .bids-index/
datalad save -m 'maint: update PyBIDS index' .bids-index/layout_index.sqlite
datalad push --to=github

echo "Creating PR..."
body_file=$( mktemp )
echo "Outputs of BIDS conversion:" > $body_file
echo '```TSV' >> $body_file
echo '' >> $body_file
cat ${BIDS_ROOT}/sub-${SUBJECT}/ses-${SESSION}/sub-${SUBJECT}_ses-${SESSION}_scans.tsv >> $body_file
echo '```' >> $body_file

# Retrieve original issue number:
gh_issue=$( gh search issues --match title --repo ${ISSUE_REPO} --json number --jq .[0].number  -- is:open label:scan $SESSION )
if [ ! -z "$gh_issue" ]; then
  echo '' >> $body_file
  echo "Prompted-by: ${ISSUE_REPO}#${gh_issue}." >> $body_file
fi

pr_url=$( gh pr create -B "${DATASET_BRANCH}" -r "${REVIEWER}" -a "@me" -t "ADD: ${SESSION} | Session ${session_num} on ${session_device[${SESSION: -3}]} (${session_date})" -F $body_file | tail -n1 )

echo "Compacting DICOMs..."

pushd ${SESSION_ROOT}
tar vczf ${DICOM_ARCHIVE}/${session_id}.tar.gz ${session_id} && rm -rf ${session_id}
popd

rmdir ${SESSION_ROOT}
chmod a-w ${DICOM_ARCHIVE}/${session_id}.tar.gz

echo "Number of lines in scan file (should be ${EXPECTED_SCANS}): $( wc -l sub-${SUBJECT}/ses-${SESSION}/sub-${SUBJECT}_ses-${SESSION}_scans.tsv )"
echo "PR created: $pr_url"
