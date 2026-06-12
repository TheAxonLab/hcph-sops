# QA/QC criteria for unprocessed data

The following lists the pre-defined exclusion criteria for analyses of whole-brain structural and functional connectomes.

## Anatomical MRI

??? info "The exclusion criteria are tailored to how the anatomical images will be used."

    Given our planned analysis, the T1w image will be used for the spatial alignment with the standard `MNI152NLin2009cAsym` template.
    In addition, surface reconstructions from the T1w image will guide the co-registration of structural and functional (BOLD) images in *fMRIPrep*.
    Since the latter preprocessing steps are relatively robust to structural images with mild artifacts, the exclusion criteria for unprocessed T1w images are lenient.
    However, individual T1w images may be excluded without such a decision lead to exclusion of the whole session in which it belongs.
    We annotate subjects with visible artifacts in the T1w images in order to ensure rigorous scrutinizing of spatial normalization and surface reconstruction outputs from *fMRIPrep* (if both modalities passed the first QC checkpoint with *MRIQC*).

### View of the background of the anatomical image

- [ ] Check for signal *ripples* around the head typically caused by head motion.
    Exclude this T1w only if identifying these ripples leads to revising the decision on the brain mosaic.
- [ ] Check for signal interference leaked from the eyeballs across the PE direction.
    Exclude this T1w only if identifying these leakages leads to revising the decision on the brain mosaic.
- [ ] Check for ghosts outside the brain, and evaluate whether they may overlap with brain tissue:
    - [ ] Overlapping wrap-around.
    - [ ] Nyquist aliases (typically through PE direction).
    - [ ] Ghosts caused by external elements such as headsets or mirror frames.
    Exclude this T1w only if identifying these ghosts leads to revising the decision on the brain mosaic.

### Zoomed-in mosaic view of the brain

- [ ] Check that the brain is not presented upside down.
    This indicates a mistake in the header.
    Either the header needs to be corrected manually or exclude the session.
- [ ] Check for signal *ripples* around the frontal/prefrontal cortex typically caused by head motion.
    Exclude this particular T1w if ripples are clear and globally localized.
    These T1w images could degrade the quality of surface reconstruction.
- [ ] Check for signal interference leaked from the eyeballs across the PE direction overlapping with brain tissue.
    Exclude this particular T1w if the leaked signal substantially overlaps cortical brain areas.
    These T1w images could degrade the quality of surface reconstruction.
- [ ] Check for ghosts within the brain:
      - [ ] Overlapping wrap-around.
      - [ ] Nyquist aliases (typically through PE direction).
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
    Exclude this particular T1w if any of these ghosts overlap cortical gray matter.
- [ ] Check for other artifacts such as [fat shifts](https://mriquestions.com/chemical-shift-artifact.html) or RF spoiling within the brain.
   Exclude this particular T1w if any of these artifacts overlap cortical gray matter.
- [ ] Check for [zipper artifacts](https://mriquestions.com/zipper-artifact.html) and other EM interferences.
    Exclude this particular T1w if any of these artifacts overlap cortical gray matter.
- [ ] Check for excessive B<sub>1</sub> field inhomogeneity.
    Exclude only if it is evident that a coil failure happened.
- [ ] Check for inhomogeneous [*salt-and-pepper* noise patterns](https://en.wikipedia.org/wiki/Salt-and-pepper_noise).
    Generally, do not exclude this T1w image unless the noise pattern destroys cortical gray matter areas.
- [ ] Check for global [*salt-and-pepper* noise](https://en.wikipedia.org/wiki/Salt-and-pepper_noise) distribution.
    Generally, do not exclude this T1w image except evident imaging global failure.
- [ ] Check for low SNR characterized by a grainy picture.
    Generally, do not exclude this T1w image unless the noise pattern destroys cortical gray matter areas.

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
    Exclude the session if the vertical strike continuously traverse more than half of the brain's length.

#### Carpetplot and nuisance signals

- [ ] Check for periodic modulations of the signal, which is a sign that your signal is aliased by a regular and slow 
    motion, like respiration.
    Exclude the session if the modulation is visible throughout the majority of the scan.
- [ ] Check for coil failures.
    They appear as abrupt changes in overall signal intensity not paired with motion peaks.
    Exclude the session if any coil failure is observed.
- [ ] Check for strong polarized structure in the crown.
    Exclude the session if the polarized structure is prolonged throughout the majority of the scan and if the blocks 
    are particularly pronounced.
- [ ] Check for prolonged dark deflections accompanied by peaks in the FD trace as a sign for motion outbursts.
    Exclude the session in case the prolonged dark deflections cover more than half of the scan duration.
- [ ] Check for hyperintensity in single slices.
    Exclude the session if any single-slice hyperintensities are observed.
    Correlation analysis are likely to be biased by such peaks.

#### View of the background of the voxel-wise average of the BOLD timeseries

- [ ] Check for ghosts:
      - [ ] Overlapping wrap-around.
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
        Exclude the session if the intensity of the ghost is similar to the intensity of the inside of the brain.

#### Average signal through time

- [ ] Check that the brain is not presented upside down.
    This indicates an issue of the header.
    Either the header needs to be corrected manually or exclude the session.
- [ ] Check that the brain structure is clearly visible.
    Exclude the session if it is not.
- [ ] Check for signal *ripples* around the frontal/prefrontal cortex typically caused by head motion.
    Exclude the session if ripples are clear and globally localized.
- [ ] Check for ghosts within the brain:
      - [ ] Overlapping wrap-around.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
- [ ] Check for high standard deviation vertical strikes in the sagittal plane of the standard deviation map.
- [ ] Check for low SNR characterized by a grainy picture.
    This dataset is specifically subject to this artifact, because we used multiband acceleration.

??? warning "Do not exclude subjects presenting susceptibility distortion artifacts yet!"

    We acquired field maps in every session to address susceptibility distortions within the preprocessing.
    If signal dropouts in particular sessions are especially acute or widespread as compared to other sessions, double-check the visual report for other issues.

#### Group report

- [ ] Check again the individual visual report of runs with outlying-high FD, outlying-high tSNR or outlying-low SNR, ensuring they do not fall into one of the [exclusion criteria](#function-mri).
- [ ] Re-examine the individual visual report of sessions for which `fd_perc` > 50% and double-check that the data does not fall into one of the [exclusion criteria](#functional-mri).
- [ ] Verify that smoothness estimates (FWHM) are roughly consistent across all sessions since they were all acquired with the same protocol.
    If this is not the case, re-examine the individual visual report of sessions with outlying (both low or high) FWHM.

## Diffusion MRI

The visual assessment of the *MRIQC* diffusion reportlets below follows the *MRIQC* protocol<sup>[2]</sup>.

#### Shell-wise joint distribution of SNR vs FA in every voxel

The top panel shows a heat map of the estimated signal-to-noise ratio (SNR) against the FA of every voxel, separated by shell; the bottom panel shows the histogram of SNR values per shell.
Higher *b*-value shells are expected to exhibit lower SNR.

- [ ] Flag the DWI scan if FA and SNR are clearly linearly correlated, which indicates noise contamination.
- [ ] Flag the DWI scan if the per-shell SNR distributions are markedly non-normal.
    MRI noise is Rician, so for SNR values mostly above ~2 the distribution within each shell should approximately resemble a normal distribution.
- [ ] Flag the DWI scan if the SNR distributions of the different shells overlap substantially, which can indicate suboptimal acquisition parameters.

#### Fractional anisotropy map

This reportlet shows the reconstructed FA for every voxel in a mosaic layout.
There should be a clear contrast between gray and white matter — with FA higher in white matter, and especially high where a single fiber orientation predominates (e.g., the corpus callosum) — and only minimal white speckles around the edges.

- [ ] Exclude the DWI scan if the major white matter structures (e.g., the corpus callosum) are not clearly discernible because of blurriness or a lack of white-matter/gray-matter contrast.
- [ ] Exclude the DWI scan if the brain is not displayed in the correct orientation (an axis flipped or switched because of a data-formatting issue).
- [ ] Exclude the DWI scan if there are excessive white speckles, especially in the interior of the brain (reconstruction error).

#### Mean diffusivity map

This reportlet shows the reconstructed MD for every voxel in a mosaic layout, with a consistent contrast between white matter, gray matter and the ventricles.

- [ ] Exclude the DWI scan if the ventricles and/or the CSF around the brain is not prominently identifiable.
- [ ] Exclude the DWI scan if the brain is not displayed in the correct orientation (an axis flipped or switched because of a data-formatting issue).
- [ ] Exclude the DWI scan if there is blurriness or a lack of contrast between white matter, gray matter and the ventricles (local noise if confined to one area, global noise if present throughout the image).

#### Voxel-wise average and standard deviation across volumes in a single DWI shell

This reportlet flickers between the voxel-wise average and the standard deviation across the volumes of the shell, with yellow indicating higher variance and a red line delineating the brain mask.
As the *b*-value increases, the high-variance (yellow) signal should increasingly resemble the white matter tracts; a shell with *b*=0 may show little variability if only one such volume was collected.

##### Voxel-wise average
- [ ] Check that the brain is not presented upside down.
    This indicates an issue of the header.
    Either the header needs to be corrected manually or exclude the session.
- [ ] Check that the brain structure is clearly visible.
    Exclude the session if it is not.
- [ ] Check for a piece of the head (usually the front or back) that falls outside the FOV and folds over onto the opposite extreme of the image (wrap-around).
    Exclude the session only if the folded part overlaps with the region of interest.

##### Standard deviation across volumes
- [ ] Check that the major white matter tracts, most predominantly the corpus callosum, are clearly visible. Exclude the DWI scan in case it is not.
- [ ] Check for high-standard-deviation vertical strikes in the coronal plane of the standard deviation map.
    Exclude the session if the vertical strike continuously traverses more than half of the brain's length.
- [ ] Exclude the session if there is symmetric brightness along the edges of the skull, which is indicative of head motion.
- [ ] Exclude the session if there is excessive variability, such as brightness localized to one section of the brain or appearing outside the white matter tracts (local or global noise).
- [ ] Check for an extra outline of the brain shifted along the acquisition axis.
    Exclude the session if this aliasing ghost overlaps with the actual image.

#### View of the background of the voxel-wise average of a single DWI shell

This reportlet enhances the background noise; any artifact identified here may also be visible in the FA or MD maps.

- [ ] Apply the same exclusion criteria as for the fMRI background view, that is check for the following ghosts:
      - [ ] Overlapping wrap-around.
      - [ ] Ghosts caused by external elements such as headsets or mirror frames.
      Exclude the session if any of these ghosts overlap cortical gray matter.
      - [ ] Nyquist aliases or aliasing ghost (typically through PE direction).
        Exclude the session if the intensity of the ghost is similar to the intensity of the inside of the brain.
- [ ] Exclude the session if there is excessive or "structured" visual noise in the background, particularly in or around the brain (local or global noise, image-reconstruction errors or electromagnetic interference).

## Physiological recordings

## Eye-tracking

[1]: https://www.frontiersin.org/articles/10.3389/fnimg.2023.1070274 "Etzel, Joset A. “Efficient Evaluation of the Open QC Task fMRI Dataset.” Frontiers in Neuroimaging 2 (2023). doi:10.3389/fnimg.2023.1070274."
[2]: https://doi.org/10.1038/s41596-026-01352-y "Hagen, M. P., Provins, C., MacNicol, E., et al. “Quality assessment and control of unprocessed anatomical, functional and diffusion MRI of the human brain using MRIQC.” Nature Protocols (2026). doi:10.1038/s41596-026-01352-y."
