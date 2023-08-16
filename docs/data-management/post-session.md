## Within 48h after the FIRST session
!!! danger "Anatomical images must be screened for incidental findings within 48h after the first session"
    
    - [ ] Send the T1-weighted and T2-weighted scan to {{ secrets.people.medical_contact | default("███") }} for screening and incidental findings.
    - [ ] Indicate on [our recruits spreadsheet]({{ secrets.data.recruits_url | default("/redacted.html") }}) that the participant's first session has been submitted for screening.
    - [ ] Wait for response from {{ secrets.people.medical_contact | default("███") }} and note down the result of the screening in our [our recruits spreadsheet]({{ secrets.data.recruits_url | default("/redacted.html") }}).

To do so, you'll need to first [download the data from PACS](#download-the-data-from-the-pacs-with-pacsman-only-authorized-users) and then [convert the data into BIDS](#convert-data-to-bids-with-heudiconv-and-phys2bids) as indicated below.

!!! warning "What to do when there are incidental findings"

    - [ ] Discuss with {{ secrets.people.medical_contact | default("███") }} how to proceed with the participant.
    - [ ] Exclude the participant from the study if {{ secrets.people.medical_contact | default("███") }} evaluates they don't meet the participation (inclusion and exclusion) criteria.

## Within one week after the completed session

### Download the data from the PACS with PACSMAN (only authorized users)

- [ ] Login into the PACSMAN computer  (*{{ secrets.hosts.pacsman }}*)
- [ ] Mount a remote filesystem through sshfs:
    ``` bash
    sshfs {{ secrets.hosts.oesteban | default("<hostname>") }}:/data/datasets/hcph-pilot/sourcedata \
                   $HOME/data/hcph-pilot \
          {{ secrets.data.scp_args | default("<args>") }}
    ```
- [ ] Edit the query file `vim $HOME/queries/last-session.csv` (most likely, just update with the session's date)
``` text title="mydata-onesession.csv"
{% include 'code/pacsman/mydata-onesession.csv' %}
```
- [ ] Prepare and run PACSMAN, pointing the output to the mounted directory.
    ``` bash
    pacsman --save -q $HOME/queries/last-session.csv \
           --out_directory $HOME/data/hcph-pilot/ \
           --config /opt/PACSMAN/files/config.json
    ```
- [ ] Remove write permissions on the newly downloaded data:
    ``` bash
    chmod -R a-w $HOME/data/hcph-pilot/sub-{{ secrets.ids.pacs_subject | default("01") }}/ses-*
    ```
- [ ] Unmount the remote filesystem:
    ``` bash
    sudo umount $HOME/data/hcph-pilot
    ```

### Retrieve physiological recordings (from {{ secrets.hosts.acqknowledge | default("████") }})

### Copy original DICOMs into the archive of Stockage HOrUs

- [ ] Setup a cron job to execute automatically the synchronization:

    ```
    crontab -e
    [ within your file editor add the following line ]
    0 2 * * * rsync -avurP /data/datasets/hcph-pilot/* {{ secrets.data.curnagl_backup | default("<user>@<host>:<path>") }} &> $HOME/var/log/data-curnagl.log
    ```

## Within two weeks after the completed session

### Convert data to BIDS with HeudiConv

- [ ] Careful to change the number of the session ! Note that we use the heuristic -f reproin, because we have name the sequences at the console following ReproIn convention.
``` bash title="Executing HeudiConv"
{% include 'code/heudiconv/reproin.sh' %}
```

The output of *HeuDiConv* with our current heuristics and reproin conventions should be like:

```
├── ses-15
│   ├── anat
│   │   ├── sub-pilot_ses-15_acq-original_T1w.json
│   │   ├── sub-pilot_ses-15_acq-original_T1w.nii.gz
│   │   ├── sub-pilot_ses-15_acq-undistorted_T1w.json
│   │   ├── sub-pilot_ses-15_acq-undistorted_T1w.nii.gz
│   │   ├── sub-pilot_ses-15_T2w.json
│   │   └── sub-pilot_ses-15_T2w.nii.gz
│   ├── dwi
│   │   ├── sub-pilot_ses-15_acq-highres_dir-LR_dwi.bval
│   │   ├── sub-pilot_ses-15_acq-highres_dir-LR_dwi.bvec
│   │   ├── sub-pilot_ses-15_acq-highres_dir-LR_dwi.json
│   │   └── sub-pilot_ses-15_acq-highres_dir-LR_dwi.nii.gz
│   ├── fmap
│   │   ├── sub-pilot_ses-15_acq-b0_dir-RL_epi.json
│   │   ├── sub-pilot_ses-15_acq-b0_dir-RL_epi.nii.gz
│   │   ├── sub-pilot_ses-15_acq-bold_dir-RL_part-mag_epi.json
│   │   ├── sub-pilot_ses-15_acq-bold_dir-RL_part-mag_epi.nii.gz
│   │   ├── sub-pilot_ses-15_acq-bold_dir-RL_part-phase_epi.json
│   │   ├── sub-pilot_ses-15_acq-bold_dir-RL_part-phase_epi.nii.gz
│   │   ├── sub-pilot_ses-15_magnitude1.json
│   │   ├── sub-pilot_ses-15_magnitude1.nii.gz
│   │   ├── sub-pilot_ses-15_magnitude2.json
│   │   ├── sub-pilot_ses-15_magnitude2.nii.gz
│   │   ├── sub-pilot_ses-15_phasediff.json
│   │   └── sub-pilot_ses-15_phasediff.nii.gz
│   ├── func
│   │   ├── sub-pilot_ses-15_task-bht_echo-1_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-1_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-1_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-1_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-2_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-2_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-2_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-2_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-3_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-3_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-3_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-3_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-4_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-4_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_echo-4_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-bht_echo-4_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-bht_part-mag_events.tsv
│   │   ├── sub-pilot_ses-15_task-bht_part-phase_events.tsv
│   │   ├── sub-pilot_ses-15_task-qct_echo-1_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-1_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-1_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-1_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-2_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-2_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-2_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-2_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-3_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-3_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-3_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-3_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-4_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-4_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_echo-4_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-qct_echo-4_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-qct_part-mag_events.tsv
│   │   ├── sub-pilot_ses-15_task-qct_part-phase_events.tsv
│   │   ├── sub-pilot_ses-15_task-rest_echo-1_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-1_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-1_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-1_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-2_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-2_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-2_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-2_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-3_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-3_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-3_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-3_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-4_part-mag_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-4_part-mag_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_echo-4_part-phase_bold.json
│   │   ├── sub-pilot_ses-15_task-rest_echo-4_part-phase_bold.nii.gz
│   │   ├── sub-pilot_ses-15_task-rest_part-mag_events.tsv
│   │   └── sub-pilot_ses-15_task-rest_part-phase_events.tsv
│   └── sub-pilot_ses-15_scans.tsv
└── ses-16
    ├── anat
    │   ├── sub-pilot_ses-16_acq-original_T1w.json
    │   ├── sub-pilot_ses-16_acq-original_T1w.nii.gz
    │   ├── sub-pilot_ses-16_acq-undistorted_T1w.json
    │   ├── sub-pilot_ses-16_acq-undistorted_T1w.nii.gz
    │   ├── sub-pilot_ses-16_T2w.json
    │   └── sub-pilot_ses-16_T2w.nii.gz
    ├── dwi
    │   ├── sub-pilot_ses-16_acq-highres_dir-RL_dwi.bval
    │   ├── sub-pilot_ses-16_acq-highres_dir-RL_dwi.bvec
    │   ├── sub-pilot_ses-16_acq-highres_dir-RL_dwi.json
    │   └── sub-pilot_ses-16_acq-highres_dir-RL_dwi.nii.gz
    ├── fmap
    │   ├── sub-pilot_ses-16_acq-b0_dir-AP_epi.json
    │   ├── sub-pilot_ses-16_acq-b0_dir-AP_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-b0_dir-LR_epi.json
    │   ├── sub-pilot_ses-16_acq-b0_dir-LR_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-b0_dir-PA_epi.json
    │   ├── sub-pilot_ses-16_acq-b0_dir-PA_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-b0_dir-RL_epi.json
    │   ├── sub-pilot_ses-16_acq-b0_dir-RL_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-AP_part-mag_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-AP_part-mag_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-AP_part-phase_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-AP_part-phase_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-LR_part-mag_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-LR_part-mag_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-LR_part-phase_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-LR_part-phase_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-PA_part-mag_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-PA_part-mag_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-PA_part-phase_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-PA_part-phase_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-RL_part-mag_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-RL_part-mag_epi.nii.gz
    │   ├── sub-pilot_ses-16_acq-bold_dir-RL_part-phase_epi.json
    │   ├── sub-pilot_ses-16_acq-bold_dir-RL_part-phase_epi.nii.gz
    │   ├── sub-pilot_ses-16_magnitude1.json
    │   ├── sub-pilot_ses-16_magnitude1.nii.gz
    │   ├── sub-pilot_ses-16_magnitude2.json
    │   ├── sub-pilot_ses-16_magnitude2.nii.gz
    │   ├── sub-pilot_ses-16_phasediff.json
    │   └── sub-pilot_ses-16_phasediff.nii.gz
    ├── func
    │   ├── sub-pilot_ses-16_task-bht_echo-1_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-1_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-1_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-1_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-2_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-2_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-2_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-2_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-3_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-3_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-3_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-3_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-4_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-4_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_echo-4_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-bht_echo-4_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-bht_part-mag_events.tsv
    │   ├── sub-pilot_ses-16_task-bht_part-phase_events.tsv
    │   ├── sub-pilot_ses-16_task-qct_echo-1_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-1_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-1_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-1_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-2_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-2_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-2_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-2_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-3_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-3_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-3_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-3_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-4_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-4_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_echo-4_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-qct_echo-4_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-qct_part-mag_events.tsv
    │   ├── sub-pilot_ses-16_task-qct_part-phase_events.tsv
    │   ├── sub-pilot_ses-16_task-rest_echo-1_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-1_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-1_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-1_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-2_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-2_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-2_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-2_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-3_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-3_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-3_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-3_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-4_part-mag_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-4_part-mag_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_echo-4_part-phase_bold.json
    │   ├── sub-pilot_ses-16_task-rest_echo-4_part-phase_bold.nii.gz
    │   ├── sub-pilot_ses-16_task-rest_part-mag_events.tsv
    │   └── sub-pilot_ses-16_task-rest_part-phase_events.tsv
    └── sub-pilot_ses-16_scans.tsv
```

!!! warning "We started to generate phase and magnitude only after session 15"

    As a result, the piloting data up to session 14 will look more like:

    ```
    ├── ses-14
    │   ├── anat
    │   │   ├── sub-pilot_ses-14_acq-original_T1w.json
    │   │   ├── sub-pilot_ses-14_acq-original_T1w.nii.gz
    │   │   ├── sub-pilot_ses-14_acq-undistorted_T1w.json
    │   │   ├── sub-pilot_ses-14_acq-undistorted_T1w.nii.gz
    │   │   ├── sub-pilot_ses-14_T2w.json
    │   │   └── sub-pilot_ses-14_T2w.nii.gz
    │   ├── dwi
    │   │   ├── sub-pilot_ses-14_acq-highres_dir-PA_dwi.bval
    │   │   ├── sub-pilot_ses-14_acq-highres_dir-PA_dwi.bvec
    │   │   ├── sub-pilot_ses-14_acq-highres_dir-PA_dwi.json
    │   │   └── sub-pilot_ses-14_acq-highres_dir-PA_dwi.nii.gz
    │   ├── fmap
    │   │   ├── sub-pilot_ses-14_acq-b0_dir-AP_epi.json
    │   │   ├── sub-pilot_ses-14_acq-b0_dir-AP_epi.nii.gz
    │   │   ├── sub-pilot_ses-14_acq-bold_dir-PA_run-1_epi.json
    │   │   ├── sub-pilot_ses-14_acq-bold_dir-PA_run-1_epi.nii.gz
    │   │   ├── sub-pilot_ses-14_acq-bold_dir-PA_run-2_epi.json
    │   │   ├── sub-pilot_ses-14_acq-bold_dir-PA_run-2_epi.nii.gz
    │   │   ├── sub-pilot_ses-14_magnitude1.json
    │   │   ├── sub-pilot_ses-14_magnitude1.nii.gz
    │   │   ├── sub-pilot_ses-14_magnitude2.json
    │   │   ├── sub-pilot_ses-14_magnitude2.nii.gz
    │   │   ├── sub-pilot_ses-14_phasediff.json
    │   │   └── sub-pilot_ses-14_phasediff.nii.gz
    │   ├── func
    │   │   ├── sub-pilot_ses-14_task-bht_echo-1_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_echo-1_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_echo-2_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_echo-2_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_echo-3_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_echo-3_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_echo-4_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_echo-4_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_events.tsv
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-1_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-1_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-2_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-2_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-3_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-3_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-4_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_echo-4_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-1_events.tsv
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-1_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-1_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-2_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-2_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-3_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-3_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-4_bold.json
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_echo-4_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-bht_run-2_events.tsv
    │   │   ├── sub-pilot_ses-14_task-qc_echo-1_bold.json
    │   │   ├── sub-pilot_ses-14_task-qc_echo-1_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-qc_echo-2_bold.json
    │   │   ├── sub-pilot_ses-14_task-qc_echo-2_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-qc_echo-3_bold.json
    │   │   ├── sub-pilot_ses-14_task-qc_echo-3_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-qc_echo-4_bold.json
    │   │   ├── sub-pilot_ses-14_task-qc_echo-4_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-qc_events.tsv
    │   │   ├── sub-pilot_ses-14_task-rest_echo-1_bold.json
    │   │   ├── sub-pilot_ses-14_task-rest_echo-1_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-rest_echo-2_bold.json
    │   │   ├── sub-pilot_ses-14_task-rest_echo-2_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-rest_echo-3_bold.json
    │   │   ├── sub-pilot_ses-14_task-rest_echo-3_bold.nii.gz
    │   │   ├── sub-pilot_ses-14_task-rest_echo-4_bold.json
    │   │   ├── sub-pilot_ses-14_task-rest_echo-4_bold.nii.gz
    │   │   └── sub-pilot_ses-14_task-rest_events.tsv
    │   └── sub-pilot_ses-14_scans.tsv
    ```

### Convert physiological recordings and eye-tracking data to BIDS

- [ ] Plot an overview of the data with the following command. This command generates a PNG plot of the data within the current directory without processing the data itself. The folder containing the physiological data is specified via the -in command line argument.
```
phys2bids -in /data/datasets/hcph-pilot/sourcedata/physio/session-recording.acq -info
```
- [ ] Check the data by opening the PNG plot.
- [ ] If the data appears satisfactory, proceed to process it using the subsequent command. Use the -ntp argument to specify the number of volumes for each task, and the -tr argument to indicate the task's repetition time. Define the output directory with -outdir and provide the path to the heuristic file using -heur. Adjust the subject and session numbers accordingly. Should scanner trigger transmission encounter issues and manual adjustments are made to the trigger data, it is possible to allocate one trigger per task. Set the repetition time duration as the task length, as demonstrated in the example below.
```
phys2bids -in modified-last-session_multiscan.txt -chtrig 4 -ntp  1 1 1 -tr 158 1200 331 -thr 2 -outdir outputdir -heur heur_physio.py -sub pilot -ses 01
```
- [ ] Execute the script write_event_file.py as shown below to generate task event files. This script not only creates JSON and TSV files containing event information, but it also generates PNG plots for each task, displaying both physiological data and corresponding events. These plots are saved in the current directory.

Once the script is executed, the BIDS folder (consisting solely of physiological data in this case) will have the following structure:
```
ses-01
    └── func
        ├── sub-pilot_ses-01_task-bht_events.json
        ├── sub-pilot_ses-01_task-bht_events.tsv
        ├── sub-pilot_ses-01_task-bht_physio.json
        ├── sub-pilot_ses-01_task-bht_physio.tsv.gz
        ├── sub-pilot_ses-01_task-qct_events.json
        ├── sub-pilot_ses-01_task-qct_events.tsv
        ├── sub-pilot_ses-01_task-qct_physio.json
        ├── sub-pilot_ses-01_task-qct_physio.tsv.gz
        ├── sub-pilot_ses-01_task-rest_events.json
        ├── sub-pilot_ses-01_task-rest_events.tsv
        ├── sub-pilot_ses-01_task-rest_physio.json
        └── sub-pilot_ses-01_task-rest_physio.tsv.gz
```


### Incorporate into version control with DataLad

!!!info "Initiating the version-controled dataset"

    Once at the beginning of the project, the datalad dataset will be created:

    - [ ] Add stockage horus as an SSH remote.
