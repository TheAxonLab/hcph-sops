## Executing *MRIQC*

- [ ] Create a dataset to host the *MRIQC* derivatives.
    Remember to set the correct version of the container (in our case {{ settings.versions.mriqc }}).
    ``` shell
    mkdir -p /data/datasets/hcph-derivatives
    cd /data/datasets/hcph-derivatives
    datalad create -c bids mriqc_{{ settings.versions.mriqc }}
    ```
??? warning "Note that *MRIQC* derivatives will be handled as a standalone dataset (hence, the `-d` flag is omitted above)."

    We will consider *MRIQC*'s derivatives as an standalone dataset (as opposed to *sub-datasets*) to permit a more flexible management with *DataLad*.
    Before data release, the *MRIQC*-Derivatives dataset will be added as a sub-dataset to the unprocessed dataset.

- [ ] Run *MRIQC*.
    ```shell
    #Assign the variable to the last session ID
    lastsession=01
    datalad containers-run \
        --container-name mriqc \
        --input sourcedata \
        --output ./derivatives/mriqc-23.1.0 \
        "{inputs} {outputs} participant --session-id ${lastsession} -w ${HOME}/tmp/hcph-derivatives/mriqc-23.1.0 --mem 40G --bids-database-dir {{ settings.paths.hcph_bids }}/.bids-index --dsname hcph"
    ```

- [ ] Check that *MRIQC* generated all expected individual reports.
    For each session, the following files must be generated:
    ``` text
    derivatives
        ├── mriqc_23.2.0
        │   ├── dataset_description.json
        │   ├── logs
        │   ├── sub-001
        │   ├── sub-001_ses-001_acq-highres_dir-AP_dwi.html
        │   ├── sub-001_ses-001_acq-original_T2w.html
        │   ├── sub-001_ses-001_acq-undistorted_T1w.html
        │   ├── sub-001_ses-001_acq-undistorted_T2w.html
        │   ├── sub-001_ses-001_task-bht_dir-AP_bold.html
        │   ├── sub-001_ses-001_task-qct_dir-AP_bold.html
        │   ├── sub-001_ses-001_task-rest_dir-AP_bold.html
    ```
    - [ ] Adapt the following code to your setup to check this automatically. Adapt it to your setup.
        ```shell
{% filter indent(width=8) %}
{% include 'code/qc/check_all_reports_generated.py' %}
{% endfilter %}
        ```
    
    <a id="mriqc-failed"></a>
    ??? bug "*MRIQC* failed to produce all the expected visual reports" 
        Depending on the specific error condition hit by *MRIQC*, some visual reports may not be generated at all.
        
        - [ ] Check for corresponding *crash files* under the `logs/` directory under the output folder.
        - [ ] Address the issue (e.g., insufficient disk space) and re-run *MRIQC*.
            If the issue is unclear, search for similar problems reported previously in the [issues of the *MRIQC* GitHub repository](https://github.com/nipreps/mriqc/issues).
            The solution could be documented in some existing issue opened by a user who experienced the same problem before you and reported it.
            Don't forget to check closed issues!
            If that did not help, you might find help on [NeuroStars](https://neurostars.org/).
        - [ ] Open a new issue in the *MRIQC* GitHub repository if all the above fails.

- [ ] Check that the `group_{T1w,T2w,bold,dwi}.tsv` file contains the image quality metrics (IQMs) for all the expected inputs (one row per individual run at the input).
- [ ] Push the new derivatives to the remote storage.
    ```shell
    datalad push --to ria-storage
    datalad push --to origin
    ```

## Visualizing *MRIQC*'s individual reports

Following our protocols<sup>[1]</sup>, the quality of unprocessed images MUST be assessed before executing any processing (e.g., *fMRIPrep* or *dMRIPrep* for preprocessing).
In addition, *MRIQC* is executed prior any further processing step considering our preliminary findings regarding *defacing*<sup>[2]</sup>.

### Assessing anatomical images (T<sub>1</sub>-weighted and T<sub>2</sub>-weighted)
- [ ] Open each *MRIQC* report on a Web Browser.
- [ ] Check that the visual report is complete when you open it.

    ??? bug "A visual report is incomplete"

        - [ ] Identify what failed in the subsection "Errors" of section "About" of the visual report.
        - [ ] Address the issue (e.g., out-of-memory when running a container) and re-run *MRIQC*.
            Proceed as [earlier](#mriqc-failed) by finding documentation on the *MRIQC* repository or NeuroStars.

- [ ] Visualize the first mosaic (background mosaic) and apply the [exclusion criteria](qaqc-criteria-unprocessed.md#view-of-the-background-of-the-anatomical-image).

    !!! tip "Do not hesitate to jump back and forth through sections while screening the visual report."

- [ ] Scroll down to the zoomed-in brain mosaic and apply the [exclusion criteria](qaqc-criteria-unprocessed.md#zoomed-in-mosaic-view-of-the-brain).
- [ ] Verify that no errors are reported in the subsection "Errors" of section "About".
If there are, follow the procedure described in ["*MRIQC* failed to produce all the expected visual reports".](#mriqc-failed)
- [ ] Assign a quality rating and indicate artifacts with the *Rating widget*.
    To assign a quality rating:
    - [ ] Open the *Rating widget* by clicking on the slider next to it in the upper right corner of the *MRIQC* visual report.
    - [ ] Open up the "Record specific artifacts" menu and select the artifacts that you spotted according to the [QA/QC criteria](qaqc-criteria-unprocessed.md).
    - [ ] Assign a quality grade that reflects the number of artifacts you spotted and their severity, using the slider.
    - [ ] Optionally, you can write down any extra comment you might have about the data and indicate your level of confidence regarding your ratings in the "Extra details" menu.
- [ ] Download the rating file as a JSON and add it to the derivatives dataset.

!!! warning "Immediately report images deemed *exclude*, as an issue in the dataset's repository"

### Assessing functional images

!!! danger "Insufficient quality of an RSfMRI run requires recalling the session"

    - [ ] Immediately report RSfMRI images deemed *exclude* as an issue in [the dataset's repository](https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}/issues).
    - [ ] Proceed to [scheduling an extra session](../recruitment-scheduling-screening/scheduling.md) after the initially-planned scanning period.

- [ ] Open each *MRIQC* report on a Web Browser in the following order:

    1. QCT,
    1. BHT, and
    1. RSfMRI.

    ??? important "IMPORTANT — QCT and BHT are assessed first as proxies for the RSfMRI run's quality."

        We employ the QCT (mainly) and the BHT as proxies for the quality of the RSfMRI run.
        Screening the reports in the prescribed order (QCT — BHT — RSfMRI) helps identify issues in the QCT and BHT that may anticipate problems in the RSfMRI.

- [ ] Screen all echo-wise visualizations of the base report following these four steps:
    - [ ] Visualize the first mosaic (standard-deviation) and apply the corresponding [exclusion criteria](qaqc-criteria-unprocessed.md#standard-deviation-of-signal-through-time)
    - [ ] Proceed to the background view and search for [artifacts](qaqc-criteria-unprocessed.md#view-of-the-background-of-the-voxel-wise-average-of-the-bold-timeseries).
    - [ ] Inspect the zoomed-in view of the average BOLD mosaic and apply the same [exclusion criteria](qaqc-criteria-unprocessed.md#average-signal-through-time).    
    - [ ] Scroll down to the carpet plot and apply the corresponding [exclusion criteria](qaqc-criteria-unprocessed.md#carpetplot-and-nuisance-signals).

- [ ] Inspect the average BOLD mosaic for each echo in the "Extended echo-wise reports" section and apply the corresponding [exclusion criteria](qaqc-criteria-unprocessed.md#average-signal-through-time).

- [ ] Proceed as [earlier](#mriqc-failed) if errors are reported within the "Errors" section.

### Assessing diffusion images
- [ ] Open each *MRIQC* report on a Web Browser.
- [ ] Visualize all reportlets in the `Summary` section:
    - [ ] Inspect the shell-wise joint distribution of SNR vs FA and apply the corresponding [exclusion criteria](qaqc-criteria-unprocessed.md#).
    - [ ] Scroll down to the fractional anisotropy (FA) map and apply the exclusion criteria.
    - [ ] Navigate to the mean diffusivity (MD) map and apply the exclusion criteria.
- [ ] Continue with the `DWI shells` section. For each b-value, proceed as follows:
    - [ ] Visualize the first flickering mosaic presenting the average and the standard deviation across volumes in that DWI shell and apply the    
        exclusion criteria.
    - [ ] Scroll down to the view of the background and apply the exclusion criteria.
- [ ] Proceed as [earlier](#mriqc-failed) if errors are reported within the "Errors" section.

## Visualizing *MRIQC*'s group reports

Visualize the group report for each modality in the following order: anatomical, functional and diffusion.
- [ ] Open the *MRIQC* group report on a Web Browser.
- [ ] Visualize the IQM distributions and apply the [exclusion criteria](qaqc-criteria-unprocessed.md#group-report) corresponding to the modality.


[1]: https://doi.org/10.3389/fnimg.2022.1073734 "Provins, C., … Esteban, O. (2023). Quality Control in functional MRI studies with MRIQC and fMRIPrep. Frontiers in Neuroimaging 1:1073734. doi:10.3389/fnimg.2022.1073734 (OA)."
[2]: https://rr.peercommunityin.org/articles/rec?id=346 "Provins, C., … Esteban, O. (2023). Defacing biases in manual and automated quality assessments of structural MRI with MRIQC, Stage 1 IPA (in principle acceptance) of Version 3 by Peer Community in Registered Reports."
