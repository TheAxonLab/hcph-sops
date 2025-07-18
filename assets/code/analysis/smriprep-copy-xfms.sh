#!/bin/bash

# Define source and destination base directories
SRC_BASE="/scratch/cprovins/smriprep/smriprep_wf/single_subject_001_wf/anat_preproc_wf/anat_fit_wf/t2w_template_wf/concat_xfms/mapflow"
SES_BASE="/work/FAC/FBM/DNF/oesteban/hcph/data/derivatives/smriprep-reliability/inu_corrected_individual_T2w"
DEST="/work/FAC/FBM/DNF/oesteban/hcph/data/derivatives/smriprep-reliability/inu_corrected_individual_T2w"

# Create destination directory if it doesn't exist
mkdir -p "$DEST"

# Extract session numbers from filenames, remove duplicates, and sort
sessions_list=$(find "$SES_BASE" -type f -name "sub-001_ses-*_*.nii.gz" \
  | sed -n 's/.*_ses-\([0-9]\+\)_.*/ses-\1/p' \
  | sort -n | uniq)

# Convert to array
mapfile -t sessions <<< "$sessions_list"

# Loop through each _concat_xfms* directory and corresponding session
for i in "${!sessions[@]}"; do
    session_id="${sessions[i]}"  # Now includes 'ses-XXX'

    src_folder="$SRC_BASE/_concat_xfms${i}"
    src_file="$src_folder/out_fwd.tfm"

    # Check if the source file exists
    if [[ -f "$src_file" ]]; then
        dest_file="$DEST/sub-001_${session_id}_acq-undistorted_from-orig_to-T2w_mode-image_xfm.txt"
        cp "$src_file" "$dest_file"
        echo "Copied: $src_file → $dest_file"
    else
        echo "Warning: Source file not found: $src_file"
    fi
done
