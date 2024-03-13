import pytest
import os
import random
import pandas as pd
import os.path as op
import fmri.load_save as fl

from itertools import chain


@pytest.mark.parametrize(
    ("path", "expected_path"),
    [
        ("/home/hcph/fmriprep", "/home/hcph/fmriprep/derivatives"),
        ("/home/hcph-derivatives", "/home/hcph-derivatives"),
        ("/home/derivatives", "/home/derivatives"),
        ("/home/derivatives/fmriprep", "/home/derivatives"),
        ("/home/derivatives/fmriprep/23.2.0", "/home/derivatives"),
    ],
)
def test_find_derivative(path, expected_path):
    der_path = fl.find_derivative(path)
    assert der_path == expected_path


@pytest.mark.parametrize(
    "derivative_path", ["/home/derivatives", "/home/hcph-derivatives"]
)
@pytest.mark.parametrize("addition", ["fmriprep", "fmriprep/sub-001", ""])
@pytest.mark.parametrize("mriqc_name", ["mriqc", "mriqc-23.1.0"])
@pytest.mark.parametrize(
    "other_folder_present",
    [["fmriprep", "functional_connectivity"], [], ["mriqc-24.1.0"]],
)
def test_find_mriqc(
    derivative_path, addition, mriqc_name, other_folder_present, monkeypatch
):
    def mock_listdir(path):
        return list(chain.from_iterable([[mriqc_name], other_folder_present]))

    def mock_isdir(path):
        return True

    monkeypatch.setattr(os, "listdir", mock_listdir)
    monkeypatch.setattr(op, "isdir", mock_isdir)
    print(op.join(derivative_path, addition))
    mriqc_path = fl.find_mriqc(op.join(derivative_path, addition))
    assert mriqc_path == op.join(derivative_path, mriqc_name)


def test_reorder_iqms():
    iqms = {
        "bids_name": [
            "sub-3_ses-1_task-rest_bold",
            "sub-3_ses-1_task-qct_bold",
            "sub-3_ses-2_task-rest_bold",
            "sub-2_ses-1_task-rest_bold",
            "sub-1_ses-1_task-rest_bold",
            "sub-4_ses-1_task-rest_bold",
        ],
        "fd_mean": random.sample(range(101), 6),
        "fd_num": random.sample(range(101), 6),
        "fd_perc": random.sample(range(101), 6),
    }

    iqms_df = pd.DataFrame(iqms)

    fc_paths = [
        "/data/sub-2_ses-1_task-rest_connectivity.tsv",
        "/data/sub-1_ses-1_task-rest_connectivity.tsv",
        "/data/sub-3_ses-1_task-rest_connectivity.tsv",
    ]

    iqms_df = fl.reorder_iqms(iqms_df, fc_paths)

    # Verify that sub-1 and ses-2 are not included in iqms_df
    assert "4" not in iqms_df["subject"].values
    assert "2" not in iqms_df["session"].values

    # Verify that no row contains "task-qct" within the bids_name string
    assert not iqms_df["bids_name"].str.contains("task-qct").any()

    # Verify that the order of iqms_df matches the order of fc_paths and that the subject and bids_name match
    assert iqms_df["subject"].values.tolist() == ["2", "1", "3"]
    assert iqms_df["bids_name"].values.tolist() == [
        "sub-2_ses-1_task-rest_bold",
        "sub-1_ses-1_task-rest_bold",
        "sub-3_ses-1_task-rest_bold",
    ]


@pytest.mark.parametrize(
    ("path", "expected_dim"),
    [
        ("/home/DiFuMo2-LP", 2),
        ("/home/DiFuMo64", 64),
        ("/home/DiFuMo128", 128),
        ("/home/DiFuMo-LP", None),
        ("/home/Yeo", None),
    ],
)
def test_find_atlas_dimension(path, expected_dim):
    if expected_dim is not None:
        atlas_dim = fl.find_atlas_dimension(path)
        assert atlas_dim == expected_dim
    else:
        with pytest.raises(ValueError):
            fl.find_atlas_dimension(path)


@pytest.mark.parametrize("return_existing", [False, True])
@pytest.mark.parametrize("return_output", [False, True])
@pytest.mark.parametrize("fc_label", ["sparse inverse covariance", "correlation"])
def test_check_existing_output(return_existing, return_output, fc_label, tmp_path):
    func_filename = ["sub-1/func/sub-1_bold.nii", "sub-2/func/sub-2_bold.nii"]
    existing_filenames = [
        "sub-2_meas-sparseinversecovariance_connectivity.tsv",
        "sub-2_meas-correlation_connectivity.tsv",
        "sub-3_meas-sparseinversecovariance_connectivity.tsv",
    ]

    fc_label = fc_label.replace(" ", "")

    FAKE_PATTERN: list = ["sub-{subject}[_meas-{meas}]" "_{suffix}.{extension}"]

    for file in existing_filenames:
        (tmp_path / file).write_text("")

    if return_existing:
        if return_output:
            existing_file = fl.check_existing_output(
                tmp_path,
                func_filename,
                return_existing=return_existing,
                return_output=return_output,
                patterns=FAKE_PATTERN,
                meas=fc_label,
                **fl.FC_FILLS,
            )
            assert existing_file == [
                str(
                    tmp_path
                    / f'sub-2_meas-{fc_label.replace(" ", "")}_connectivity.tsv'
                )
            ]
        else:
            missing_file, existing_file = fl.check_existing_output(
                tmp_path,
                func_filename,
                return_existing=return_existing,
                patterns=FAKE_PATTERN,
                meas=fc_label,
                **fl.FC_FILLS,
            )
            assert missing_file == ["sub-1/func/sub-1_bold.nii"]
            assert existing_file == ["sub-2/func/sub-2_bold.nii"]
    else:
        missing_file = fl.check_existing_output(
            tmp_path,
            func_filename,
            return_existing=return_existing,
            patterns=FAKE_PATTERN,
            meas=fc_label,
            **fl.FC_FILLS,
        )
        assert missing_file == ["sub-1/func/sub-1_bold.nii"]

    if return_output == True and return_existing == False:
        with pytest.raises(ValueError):
            fl.check_existing_output(
                tmp_path,
                func_filename,
                return_existing=return_existing,
                return_output=return_output,
                patterns=FAKE_PATTERN,
                meas=fc_label,
                **fl.FC_FILLS,
            )

    # Clear temporary directory
    for file in existing_filenames:
        (tmp_path / file).unlink()
    tmp_path.rmdir()
