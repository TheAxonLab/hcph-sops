# QA/QC criteria for unprocessed data

The following lists the pre-defined exclusion criteria for analyses of whole-brain structural and functional connectomes.

!!! info "These criteria adapt published QC protocols"

    The visual-assessment criteria below are derived from the *MRIQC* protocol<sup>[2]</sup> (preprint<sup>[3]</sup>) and the functional-MRI quality-control review of Provins et al.<sup>[4]</sup>.

## Anatomical MRI

??? info "The exclusion criteria are tailored to how the anatomical images will be used."

    Given our planned analysis, the T1w image will be used for the spatial alignment with the standard `MNI152NLin2009cAsym` template.
    In addition, surface reconstructions from the T1w image will guide the co-registration of structural and functional (BOLD) images in *fMRIPrep*.
    Since the latter preprocessing steps are relatively robust to structural images with mild artifacts, the exclusion criteria for unprocessed T1w images are lenient.
    However, individual T1w images may be excluded without such a decision lead to exclusion of the whole session in which it belongs.
    We annotate subjects with visible artifacts in the T1w images in order to ensure rigorous scrutinizing of spatial normalization and surface reconstruction outputs from *fMRIPrep* (if both modalities passed the first QC checkpoint with *MRIQC*).

### View of the background of the anatomical image

This view is lenient: a finding here only matters if it changes the decision made on the [zoomed-in brain mosaic](#zoomed-in-mosaic-view-of-the-brain).

- [ ] Check for signal *ripples* around the head (head motion).
- [ ] Check for signal interference leaked from the eyeballs along the PE direction.
- [ ] Check for ghosts outside the brain, evaluating whether they overlap brain tissue:
    - [ ] Overlapping wrap-around.
    - [ ] Nyquist aliases (typically along the PE direction).
    - [ ] Ghosts from external elements such as headsets or mirror frames.
- [ ] Check for excessive or "structured" background noise, particularly in or around the brain (reconstruction errors or EM interference).

### Zoomed-in mosaic view of the brain

- [ ] Check the orientation: an upside-down or axis-flipped/swapped brain indicates a wrong NIfTI orientation header (the `qform`/`sform` affine). Correct the header or exclude the session.
- [ ] Check for *ripples* around the frontal/prefrontal cortex (head motion or Gibbs ringing).
    Exclude this T1w if they are clear and globally localized (they degrade surface reconstruction).
- [ ] Check for eyeball signal leaked along the PE direction onto brain tissue.
    Exclude this T1w if it substantially overlaps cortical areas (degrades surface reconstruction).
- [ ] Check for ghosts within the brain:
      - [ ] Overlapping wrap-around.
      - [ ] Nyquist aliases (typically along the PE direction).
      - [ ] Ghosts from external elements such as headsets or mirror frames.
    Exclude this T1w if any overlap cortical gray matter.
- [ ] Check for [fat shifts](https://mriquestions.com/chemical-shift-artifact.html) or RF spoiling within the brain.
    Exclude this T1w if they overlap cortical gray matter.
- [ ] Check for [zipper artifacts](https://mriquestions.com/zipper-artifact.html) and other EM interference.
    Exclude this T1w if they overlap cortical gray matter.
- [ ] Check for distorted regions or extreme deviations from typical anatomy (possible incidental finding or susceptibility distortion).
- [ ] Check for intensity non-uniformity: a slow, smooth intensity drift across the brain that does not reflect gray-matter/white-matter anatomy.
- [ ] Check for excessive B<sub>1</sub> field inhomogeneity.
    Exclude only if a coil failure is evident.
- [ ] Check for blurriness (local noise if confined to one region, global if throughout the image).
- [ ] Check for inhomogeneous [*salt-and-pepper* noise](https://en.wikipedia.org/wiki/Salt-and-pepper_noise) patterns.
    Do not exclude unless the pattern destroys cortical gray-matter areas.
- [ ] Check for global [*salt-and-pepper* noise](https://en.wikipedia.org/wiki/Salt-and-pepper_noise).
    Do not exclude except on evident global imaging failure.
- [ ] Check for low SNR (grainy picture).
    Do not exclude unless the noise destroys cortical gray-matter areas.

### Group report

- [ ] Check again the individual visual report of runs with outlying-low SNR, ensuring they do not fall into one of the [exclusion criteria](#anatomical-mri).

## Task behavior

For accurate estimation of task activation, it is essential to check the quality of both the fMRI images and the task behavior<sup>[1]</sup>.
As such, verifying that the subjects were attempting to perform the instructed task (i.e., not sleeping and not responding randomly) is important.

??? note "Participant compliance should be high within Cohort I."

    Because the one participant in Cohort I is the principal investigator, we assume that he is following all the instructions and reporting any issues as they occur.
    Nonetheless, we will verify that the participant did not inadvertently fall asleep during fMRI runs.

## Functional MRI

### All fMRI runs

- [ ] Revise [the conversion to NIfTI](post-session.md#convert-imaging-data-to-bids-with-heudiconv) if errors such as wrong metadata in the header are found (for instance, invalid orientation information).
- [ ] Verify the participant did not close their eyes for an extended period (likely because they fell asleep) with the [corresponding eye-tracking data](eyetrack-qc.ipynb#plotting-some-data).

### Task fMRI exclusion criteria

??? important "IMPORTANT — QCT and BHT runs with low quality MUST be flagged, but they SHOULD NOT be excluded."

    The BHT and QCT were primarily acquired for QA/QC purposes and to aid in methodological development (e.g., denoising of the RSfMRI).
    This QA/QC protocol should be revised if the task fMRI data are employed for different purposes.

- [ ] Exclude the BHT and QCT fMRI runs displaying extreme distortions of the image, reconstruction failures, electromagnetic spikes, ghost artifacts overlapping cortical gray matter, or extreme noise levels.
    Potential causes can be, e.g., failure in the image reconstruction, mistake in the header leading to the image being in the wrong orientation, extreme noise, and others.

### RSfMRI exclusion criteria

!!! important "The following exclusion criteria are tailored to how the RSfMRI will be used."

    The RSfMRI images will be used to construct and analyze whole-brain functional connectomes.
    Hence, the quality across the whole brain is important, i.e., there is not a region where we can be more lenient.
    Additionally, a stringent QC is required for RSfMRI because noise sources that are highly correlated in different regions likely inflate correlation estimates.

#### Standard deviation of signal through time

- [ ] Check for ghosts within the brain:
      - [ ] Overlapping wrap-around.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
- [ ] Check for high-standard-deviation vertical strikes in the sagittal plane of the standard deviation map.
    Exclude the session if the vertical strike continuously traverses more than half of the brain's length.
- [ ] Check for symmetric brightness along the edges of the skull (head motion).

#### Carpetplot and nuisance signals

- [ ] Check for periodic modulations of the signal (aliasing by regular, slow motion such as respiration).
    Exclude the session if visible throughout the majority of the scan.
- [ ] Check for coil failures (abrupt changes in overall signal intensity not paired with motion peaks).
    Exclude the session if any coil failure is observed.
- [ ] Check for strongly polarized structure in the crown.
    Exclude the session if it is prolonged throughout the majority of the scan and the blocks are particularly pronounced.
- [ ] Check for prolonged dark deflections paired with peaks in the FD trace (motion outbursts).
    Exclude the session if they cover more than half of the scan duration.
- [ ] Check the FD and DVARS traces.
    Exclude the session on an average FD above the predefined threshold (MRIQC default 0.2 mm) or consistently high DVARS with large peaks (motion).
- [ ] Check for hyperintensity in single slices (biases correlation estimates).
    Exclude the session if any single-slice hyperintensities are observed.

#### View of the background of the voxel-wise average of the BOLD timeseries

- [ ] Check for ghosts:
      - [ ] Overlapping wrap-around.
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
        Exclude the session if the intensity of the ghost is similar to the intensity of the inside of the brain.
- [ ] Check for excessive or "structured" background noise, particularly in or around the brain (reconstruction errors or EM interference).

#### Average signal through time

- [ ] Check the orientation: an upside-down or axis-flipped/swapped brain indicates a wrong NIfTI orientation header (the `qform`/`sform` affine). Correct the header or exclude the session.
- [ ] Check that the brain structure is clearly visible.
    Exclude the session if it is not.
- [ ] Check for signal *ripples* around the frontal/prefrontal cortex (head motion).
    Exclude the session if they are clear and globally localized.
- [ ] Check for ghosts within the brain:
      - [ ] Overlapping wrap-around.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
- [ ] Check for missing or particularly blurry slices (coil failure or local noise).
- [ ] Check for intensity non-uniformity (uneven brightness, especially near the head coils).
- [ ] Check for blurriness (local noise if confined to one region, global if throughout the image).
- [ ] Check for low SNR (grainy picture); this dataset is especially prone to it because of the multiband acceleration.

??? warning "Do not exclude subjects presenting susceptibility distortion artifacts yet!"

    We acquired field maps in every session to address susceptibility distortions within the preprocessing.
    If signal dropouts in particular sessions are especially acute or widespread as compared to other sessions, double-check the visual report for other issues.

#### Group report

- [ ] Check again the individual visual report of runs with outlying-high FD, outlying-high tSNR or outlying-low SNR, ensuring they do not fall into one of the [exclusion criteria](#functional-mri).
- [ ] Re-examine the individual visual report of sessions for which `fd_perc` > 50% and double-check that the data does not fall into one of the [exclusion criteria](#functional-mri).
- [ ] Verify that smoothness estimates (FWHM) are roughly consistent across all sessions since they were all acquired with the same protocol.
    If this is not the case, re-examine the individual visual report of sessions with outlying (both low or high) FWHM.

## Diffusion MRI

#### Shell-wise joint distribution of SNR vs FA in every voxel

Heat map of SNR against FA per voxel and shell, with the per-shell SNR histogram below; higher shells should show lower SNR.

- [ ] Flag a clear linear FA-SNR correlation (noise contamination).
- [ ] Flag markedly non-normal per-shell SNR distributions (departure from the expected Rician behavior).
- [ ] Flag substantial overlap between the shells' SNR distributions (suboptimal acquisition parameters).

#### Fractional anisotropy map

- [ ] Exclude if the major WM structures (e.g., the corpus callosum) are not discernible (blurring or poor WM-GM contrast).
- [ ] Check the orientation (quickest on the FA map): an upside-down or axis-flipped/swapped brain indicates a wrong NIfTI orientation header (the `qform`/`sform` affine). Correct the header or exclude the session.
- [ ] Exclude on excessive white speckles, especially in the brain interior (reconstruction error).

#### Mean diffusivity map

- [ ] Exclude if the ventricles and/or surrounding CSF are not prominently identifiable.
- [ ] Exclude on blurring or poor white-matter/gray-matter/ventricle contrast (local or global noise).

#### Voxel-wise average and standard deviation across volumes in a single DWI shell

This reportlet flickers between the voxel-wise average and the across-volume standard deviation (yellow: higher variance; red line: brain mask). As the *b*-value increases, the high-variance signal should track the WM tracts.

##### Voxel-wise average
- [ ] Exclude if the brain structure is not clearly visible.
- [ ] Search for wrap-around artifacts (typically along the phase-encoding direction); exclude only if the fold overlaps the brain.

##### Standard deviation across volumes
- [ ] Exclude if the major WM tracts (especially the corpus callosum) are not clearly visible.
- [ ] Exclude on high-SD vertical strikes (coronal plane) spanning more than half the brain.
- [ ] Exclude on symmetric brightness at the skull edges (head motion).
- [ ] Exclude on excessive or localized variability, or variance outside the WM tracts (local or global noise).
- [ ] Exclude on an aliasing ghost (brain outline shifted along the acquisition axis) that overlaps the actual image.

#### View of the background of the voxel-wise average of a single DWI shell

Enhanced view of the background noise; artifacts here may also appear in the FA or MD maps.

- [ ] Apply the same ghost checks as the [fMRI background view](#view-of-the-background-of-the-voxel-wise-average-of-the-bold-timeseries): wrap-around and external-element ghosts (e.g., headsets, mirror frames), excluding if they overlap cortical gray matter; Nyquist/aliasing ghosts (PE direction), excluding if as intense as brain tissue.
- [ ] Exclude on excessive or structured background noise, especially in or around the brain.

## Physiological recordings

## Eye-tracking

[1]: https://www.frontiersin.org/articles/10.3389/fnimg.2023.1070274 "Etzel, Joset A. “Efficient Evaluation of the Open QC Task fMRI Dataset.” Frontiers in Neuroimaging 2 (2023). doi:10.3389/fnimg.2023.1070274."
[2]: https://doi.org/10.1038/s41596-026-01352-y "Hagen, M. P., Provins, C., MacNicol, E., et al. “Quality assessment and control of unprocessed anatomical, functional and diffusion MRI of the human brain using MRIQC.” Nature Protocols (2026). doi:10.1038/s41596-026-01352-y."
[3]: https://doi.org/10.1101/2024.10.21.619532 "Hagen, M. P., Provins, C., MacNicol, E., et al. “Quality assessment and control of unprocessed anatomical, functional, and diffusion MRI of the human brain using MRIQC.” bioRxiv (2024). doi:10.1101/2024.10.21.619532."
[4]: https://doi.org/10.3389/fnimg.2022.1073734 "Provins, C., MacNicol, E., Seeley, S. H., Hagmann, P. & Esteban, O. “Quality control in functional MRI studies with MRIQC and fMRIPrep.” Frontiers in Neuroimaging 1, 1073734 (2023). doi:10.3389/fnimg.2022.1073734."
