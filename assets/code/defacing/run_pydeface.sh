#!/bin/sh

data_path="/data/datasets/hcph-pilot"
nondefaced_path="/data/datasets/hcph-pilot-nondefaced"

mkdir -p $nondefaced_path

cd $data_path

for file in ses-*
do
    cd $data_path/$file/anat/
    
    #Depending on the session the T1w image is named differently in the pilot data
    T1W=sub-pilot_${file}_T1w.nii.gz
    T2w=sub-pilot_${file}_T2w.nii.gz
    [ ! -f $T1W ] && T1W=sub-pilot_${file}_acq-undistorted_T1w.nii.gz

    #Overwrite the nondefaced T1w
    pydeface --outfile $data_path/$file/anat/$T1W --force $data_path/$file/anat/$T1W
    #Overwrite the nondefaced T2w
    pydeface --outfile $data_path/$file/anat/$T2W --force $data_path/$file/anat/$T2W
done
