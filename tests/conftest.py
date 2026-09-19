"""
tests/conftest.py

Shared pytest fixtures that build temporary, synthetic DICOM files on the fly.
Allows offline unit testing without external network or large download dependencies.
"""

import pytest
import pathlib
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

def create_synthetic_dicom(
    file_path: pathlib.Path,
    patient_id: str = "TEST_P1",
    modality: str = "CT",
    study_uid: str = None,
    series_uid: str = None,
    study_date: str = "20260101",
    body_part: str = "CHEST"
):
    """Generates a tiny valid DICOM file for testing."""
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = FileDataset(str(file_path), {}, file_meta=file_meta, is_little_endian=True, is_implicit_VR=False)
    ds.PatientID = patient_id
    ds.Modality = modality
    ds.StudyInstanceUID = study_uid or generate_uid()
    ds.SeriesInstanceUID = series_uid or generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.StudyDate = study_date
    ds.BodyPartExamined = body_part
    ds.SeriesDescription = "Synthetic Test Series"
    ds.PixelSpacing = [1.0, 1.0]

    # Minimal image pixel tags
    ds.Rows = 2
    ds.Columns = 2
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelData = b"\x00\x00" * 4

    ds.save_as(str(file_path), enforce_file_format=True)
    return ds

@pytest.fixture
def mock_dicom_dir(tmp_path):
    """
    Creates a temporary directory containing 3 synthetic DICOM files:
    - Patient 1: 2 files in 1 CT series
    - Patient 2: 1 file in 1 MR series
    """
    data_dir = tmp_path / "mock_data"
    data_dir.mkdir()

    study1_uid = generate_uid()
    series1_uid = generate_uid()

    # Series 1 (2 slices)
    create_synthetic_dicom(
        data_dir / "slice1.dcm",
        patient_id="PATIENT_A",
        modality="CT",
        study_uid=study1_uid,
        series_uid=series1_uid
    )
    create_synthetic_dicom(
        data_dir / "slice2.dcm",
        patient_id="PATIENT_A",
        modality="CT",
        study_uid=study1_uid,
        series_uid=series1_uid
    )

    # Series 2 (1 slice)
    create_synthetic_dicom(
        data_dir / "slice3.dcm",
        patient_id="PATIENT_B",
        modality="MR",
        body_part="BRAIN"
    )

    return data_dir
