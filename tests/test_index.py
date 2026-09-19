"""
tests/test_index.py

Unit tests for index.py (build_index and DICOM header extraction).
"""

import pandas as pd
from index import build_index

def test_build_index_with_synthetic_files(mock_dicom_dir):
    df = build_index(data_dir=mock_dicom_dir)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert set(df["PatientID"].unique()) == {"PATIENT_A", "PATIENT_B"}
    assert set(df["Modality"].unique()) == {"CT", "MR"}

    # Verify slice count calculation (2 for PATIENT_A series, 1 for PATIENT_B)
    pat_a_slices = df[df["PatientID"] == "PATIENT_A"]["slice_count"].iloc[0]
    pat_b_slices = df[df["PatientID"] == "PATIENT_B"]["slice_count"].iloc[0]

    assert pat_a_slices == 2
    assert pat_b_slices == 1

def test_build_index_empty_directory(tmp_path):
    empty_dir = tmp_path / "empty_folder"
    empty_dir.mkdir()

    df = build_index(data_dir=empty_dir)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    assert "PatientID" in df.columns
    assert "slice_count" in df.columns
