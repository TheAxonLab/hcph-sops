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
    dwi = create_key(
        "sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-{acquisition}_dwi"
    )
    phdiff = create_key(
        "sub-{subject}/{session}/fmap/sub-{subject}_{session}_phasediff"
    )
    func = create_key(
        "sub-{subject}/{session}/func/sub-{subject}_{session}_task-{task}_bold"
    )

    info = {t1w: [], dwi: [], phdiff: [], func: []}

    last_run = len(seqinfo)
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

        if "t1_mprage" in s.protocol_name:
            info[t1w].append(s.series_id)

        if s.protocol_name.startswith("micro_struct"):
            info[dwi].append(
                {
                    "item": s.series_id,
                    "acquisition": DWI_RES[s.protocol_name.split("_")[-1]],
                }
            )

        if s.protocol_name.startswith("gre_field"):
            info[phdiff].append(s.series_id)

        if s.protocol_name.startswith("cmrr_"):
            task = "rest" if s.series_files > 2000 else "control"
            info[func].append(
                {
                    "item": s.series_id,
                    "task": task,
                }
            )

    return info
