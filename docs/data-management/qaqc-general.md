# General QA/QC protocol

Following our protocols<sup>[1]</sup> and best practices<sup>[2]</sup>, we establish quality checkpoints after the outstanding stages of our neuroimaging pipeline.
That is, we establish checkpoints [after the conversion to BIDS](post-session.md#formal-qc), on the [unprocessed (before preprocessing) data](mriqc.md#visualizing-mriqcs-individual-reports), on the [preprocessed data](../processing/preprocessing.md#visualizing-fmripreps-individual-reports), and further downstream, for instance, following [FC extraction](../processing/qaqc-criteria-FC.md). Our QA/QC can be summarized as follows (click [here](../assets/images/qaqc_protocol.png) to see it full size):

![qaqc_protocol](../assets/images/qaqc_protocol.png)

!!! danger "Immediately report errors or quality issues encountered"

    If errors or quality issues are encountered, find the issue corresponding to that session in [the dataset's repository](https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}/issues) and report a comprehensive description of the problems.

As we previously emphasize in our protocol<sup>[1]</sup>, QC exclusion criteria are defined and graded corresponding to the experimental design.

## Individual and group *visual reports*

Following the *NiPreps* guidelines and best practices, quality checkpoints are implemented with visual reports that are released alongside the data and analyses.
These visual reports contain several *atomic views* (meaning, a single quality facet of the data or a particular processing step), which we call *reportlets*, that together allow the curator assess the quality.
These visual reports are formatted as HTML documents, and therefore they are presented *linearly*.
*Google Chrome* is the preferred Web Browser to open the HTML reports.
The following admonition will be found at several places of this protocol to suggest that *visual reports* can be navigated freely to ensure all aspects of quality have been properly assessed:

!!! tip "It is RECOMMENDED to jump back and forth through sections while screening the visual report."

## Assessment of functional MRI

The reliability protocol includes two tasks (QCT and BHT) before the RSfMRI run.
This design tries to leverage these two runs as a quality proxy for the RSfMRI.
The following admonition will be present to remind this strategy when it applies:

???+ important "IMPORTANT — QCT and BHT are assessed first as proxies for the RSfMRI run's quality."

    We employ the QCT (mainly) and the BHT as proxies for the quality of the RSfMRI run.
    Screening the reports in the prescribed order (QCT — BHT — RSfMRI) helps identify issues in the QCT and BHT that may anticipate problems in the RSfMRI.

Consistently with this approach, the exclusion criteria for the QCT and the BHT at the different QC checkpoints are very permissive.
The following admonition will remind this aspect when it applies:

???+ important "IMPORTANT — QCT and BHT runs with low quality MUST be flagged, but they SHOULD NOT be excluded."

    The BHT and QCT were primarily acquired for QA/QC purposes and to aid in methodological development (e.g., denoising of the RSfMRI).
    This QA/QC protocol should be revised if the task fMRI data are employed for different purposes.

## Quality assessment versus exclusion criteria
The QA/QC criteria for some checkpoints are split in two different categories:

- On the one hand, QA criteria instruct how to change the processing of the data in case the criteria are not met.
- On the other hand, exclusion criteria instruct when scans or sessions need to be excluded because of their insufficient quality. 

[1]: https://doi.org/10.3389/fnimg.2022.1073734 "Provins, C., … Esteban, O. (2023). Quality Control in functional MRI studies with MRIQC and fMRIPrep. Frontiers in Neuroimaging 1:1073734. doi:10.3389/fnimg.2022.1073734"
[2]: https://doi.org/10.1016/j.neuroimage.2022.119623 "Niso, G., … Rieger, J. W. (2022). Open and reproducible neuroimaging: from study inception to publication. NeuroImage 119623. doi:10.1016/j.neuroimage.2022.119623"
