"""Reproin heuristic."""
import re
from collections import Counter


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
    "10meas",  # dismiss a trial of fmap acquisition
)

bids_regex = re.compile(r"_(?=(dir|acq|task|run)-([A-Za-z0-9]+))")


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

    t1w = create_key(
        "sub-{subject}/{session}/anat/sub-{subject}_{session}_acq-{acquisition}{run_entity}_T1w"
    )
    t2w = create_key("sub-{subject}/{session}/anat/sub-{subject}_{session}{run_entity}_T2w")
    dwi = create_key(
        "sub-{subject}/{session}/dwi/sub-{subject}_{session}_acq-{acq}_dir-{dir}{run_entity}_dwi"
    )
    mag = create_key("sub-{subject}/{session}/fmap/sub-{subject}_{session}{run_entity}_magnitude")
    phdiff = create_key(
        "sub-{subject}/{session}/fmap/sub-{subject}_{session}{run_entity}_phasediff"
    )
    epi = create_key(
        "sub-{subject}/{session}/fmap/sub-{subject}_{session}"
        "_acq-{acquisition}_dir-{dir}{run_entity}_epi"
    )
    func = create_key(
        "sub-{subject}/{session}/func/sub-{subject}_{session}_task-{task}{run_entity}_bold"
    )
    sbref = create_key(
        "sub-{subject}/{session}/func/sub-{subject}_{session}_task-{task}{run_entity}_sbref"
    )

    info = {t1w: [], t2w: [], dwi: [], mag: [], phdiff: [], epi: [], func: [], sbref: []}

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

        thisitem = {
            "item": s.series_id,
        }
        thiskey = None
        thisitem.update({k: v for k, v in bids_regex.findall(s.protocol_name)})
        thisitem["run_entity"] = f"{thisitem.pop('run', '')}"

        if "T1w" in s.protocol_name:
            thiskey = t1w
            thisitem["acquisition"] = (
                "original" if s.dcm_dir_name.endswith("_ND") else "undistorted"
            )
        elif "T2w" in s.protocol_name:
            thiskey = t2w
        elif s.protocol_name.startswith("dwi-dwi"):
            thiskey = dwi
        elif s.protocol_name.startswith("fmap-phasediff"):
            thiskey = phdiff if s.series_files < 100 else mag
        elif s.protocol_name.startswith("fmap-epi"):
            thiskey = epi
            thisitem["acquisition"] = "b0" if s.sequence_name.endswith("ep_b0") else "bold"
        elif s.protocol_name.startswith("func-bold"):
            thiskey = func

        if thiskey is not None:
            info[thiskey].append(thisitem)

    for mod, items in info.items():
        if len(items) < 2:
            continue

        info[mod] = _assign_run_on_repeat(items)

    return info


def _assign_run_on_repeat(modality_items):
    """
    Assign run IDs for repeated inputs for a given modality.

    Examples
    --------
    >>> _assign_run_on_repeat([
    ...     {"item": "discard1", "acq": "bold", "dir": "PA"},
    ...     {"item": "discard2", "acq": "bold", "dir": "AP"},
    ...     {"item": "discard3", "acq": "bold", "dir": "PA"},
    ... ])  # doctest: +NORMALIZE_WHITESPACE
    [{'item': 'discard1', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-1'},
     {'item': 'discard2', 'acq': 'bold', 'dir': 'AP'},
     {'item': 'discard3', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-2'}]

    >>> _assign_run_on_repeat([
    ...     {"item": "discard1", "acq": "bold", "dir": "PA"},
    ...     {"item": "discard2", "acq": "bold", "dir": "AP"},
    ...     {"item": "discard3", "acq": "bold", "dir": "PA"},
    ...     {"item": "discard4", "acq": "bold", "dir": "AP"},
    ... ])  # doctest: +NORMALIZE_WHITESPACE
    [{'item': 'discard1', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-1'},
     {'item': 'discard2', 'acq': 'bold', 'dir': 'AP', 'run_entity': '_run-1'},
     {'item': 'discard3', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-2'},
     {'item': 'discard4', 'acq': 'bold', 'dir': 'AP', 'run_entity': '_run-2'}]

    >>> _assign_run_on_repeat([
    ...     {"item": "discard1", "acq": "bold", "dir": "PA", "run": "1"},
    ...     {"item": "discard2", "acq": "bold", "dir": "AP"},
    ...     {"item": "discard3", "acq": "bold", "dir": "PA", "run": "2"},
    ... ])  # doctest: +NORMALIZE_WHITESPACE
    [{'item': 'discard1', 'acq': 'bold', 'dir': 'PA', 'run': '1'},
     {'item': 'discard2', 'acq': 'bold', 'dir': 'AP'},
     {'item': 'discard3', 'acq': 'bold', 'dir': 'PA', 'run': '2'}]

    >>> _assign_run_on_repeat([
    ...     {"item": "discard1", "acq": "bold", "dir": "PA", "run_entity": "_run-1"},
    ...     {"item": "discard2", "acq": "bold", "dir": "AP"},
    ...     {"item": "discard3", "acq": "bold", "dir": "PA", "run_entity": "_run-2"},
    ... ])  # doctest: +NORMALIZE_WHITESPACE
    [{'item': 'discard1', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-1'},
     {'item': 'discard2', 'acq': 'bold', 'dir': 'AP'},
     {'item': 'discard3', 'acq': 'bold', 'dir': 'PA', 'run_entity': '_run-2'}]

    """
    modality_items = modality_items.copy()

    str_patterns = [
        "_".join([
            f"{s[0]}-{s[1]}" for s in item.items() if s[0] != "item"
        ])
        for item in modality_items
    ]
    strcount = Counter(str_patterns)

    for string, count in strcount.items():
        if count < 2:
            continue

        runid = 1

        for index, item_string in enumerate(str_patterns):
            if string == item_string:
                modality_items[index].update({
                    "run_entity": f"_run-{runid}",
                })
                runid += 1

    return modality_items
