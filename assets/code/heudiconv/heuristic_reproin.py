import os

DWI_RES = {
    "1.6mm-iso": "highres",
    "2mm-iso": "lowres",
}


IGNORE_PROTOCOLS = (
    "DEV",
    "LABEL",
    "REPORT",
    "ADC",
    "TRACEW",
    "FA",
    "ColFA",
    "B0",
    "TENSOR",
    "mprage", #keep only the non-filtered T1w labeled by *_ND
    "10meas" #dismiss a trial of fmap acquisition
)


def create_key(template, outtype=("nii.gz",), annotation_classes=None):
    if template is None or not template:
        raise ValueError("Template must be a valid format string")
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    t1w = create_key("sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w")
    t2w = create_key("sub-{subject}/{session}/anat/sub-{subject}_{session}_T2w")
    dwi = create_key("sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-{acquisition}_dir-{direction}_dwi")
    mag = create_key("sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude")
    phdiff = create_key("sub-{subject}/{session}/fmap/sub-{subject}_{session}_phasediff")
    b0 = create_key("sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-{acquisition}_dir-{direction}_epi")
    func = create_key("sub-{subject}/{session}/func/sub-{subject}_{session}_task-{task}_bold")

    info = {t1w: [], t2w: [], dwi: [], mag: [], phdiff: [], b0: [], func: []}

    for s in seqinfo:
        """
        The namedtuple `s` contains the following fields:

        * total_files_till_now
        * example_dcm_file
        * series_id
        * dcm_dir_name
        * unspecified2
        * unspecified3
        * dim1
        * dim2
        * dim3
        * dim4
        * TR
        * TE
        * protocol_name
        * is_motion_corrected
        * is_derived
        * patient_id
        * study_description
        * referring_physician_name
        * series_description
        * image_type
        """

        # Ignore derived data and reports
        if (
            s.is_derived == "True"
            or s.is_derived is True
            or s.dcm_dir_name.split("_")[-1] in IGNORE_PROTOCOLS
        ):
            continue

        if "T1w" in s.protocol_name:
            info[t1w].append(s.series_id)

        if "T2w" in s.protocol_name:
            info[t2w].append(s.series_id)

        if s.protocol_name.startswith("dwi"):
            info[dwi].append({
                "item": s.series_id,
                "acquisition": s.protocol_name.split("_")[1][4:],
                "direction": s.protocol_name.split("_")[2][4:]
            })

        if "phasediff" in s.protocol_name:
            if s.dim3 == 60:
                info[phdiff].append(s.series_id)
            if s.dim3 == 120:
                info[mag].append(s.series_id)

        if s.protocol_name.startswith("fmap-epi"):
            info[b0].append({
                "item": s.series_id,
                "acquisition": s.protocol_name.split("_")[1][4:],
                "direction": s.protocol_name.split("_")[2][4:]
            })

        if "cmrr" in s.protocol_name:
            task = "rest" if s.series_files > 2000 else "control"
            info[func].append({
                "item": s.series_id,
                "task": task,
            })

    return info
