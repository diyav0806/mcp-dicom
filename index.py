"""
index.py

Scans a directory of DICOM files, parses their headers without loading pixel data,
and returns a pandas DataFrame indexing patient, study, and series metadata.

Prototype use only — not for clinical use.
"""

import json
import pathlib
import pandas as pd
import pydicom

def load_config(config_path="config.json") -> dict:
    """Reads project configuration file."""
    path = pathlib.Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"data_dir": "data", "audit_log": "audit.jsonl"}

def extract_header(file_path: pathlib.Path) -> dict:
    """
    Extracts core header attributes from a single DICOM file.
    `stop_before_pixels=True` reads only header metadata, making parsing fast and memory-efficient.
    """
    try:
        # Read metadata only (fast, no pixel array in RAM)
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
        
        # Safely convert PixelSpacing tag if present (e.g. [0.98, 0.98])
        raw_spacing = getattr(ds, "PixelSpacing", None)
        if raw_spacing is not None:
            spacing = [float(x) for x in raw_spacing]
        else:
            spacing = None

        return {
            "PatientID": str(getattr(ds, "PatientID", "UNKNOWN")),
            "StudyDate": str(getattr(ds, "StudyDate", "UNKNOWN")),
            "Modality": str(getattr(ds, "Modality", "UNKNOWN")),
            "BodyPartExamined": str(getattr(ds, "BodyPartExamined", "UNKNOWN")),
            "StudyInstanceUID": str(getattr(ds, "StudyInstanceUID", "UNKNOWN")),
            "SeriesInstanceUID": str(getattr(ds, "SeriesInstanceUID", "UNKNOWN")),
            "SeriesDescription": str(getattr(ds, "SeriesDescription", "N/A")),
            "PixelSpacing": spacing,
            "FilePath": str(file_path.resolve())
        }
    except Exception as e:
        # Return fallback row if file reading fails
        return {
            "PatientID": "CORRUPT",
            "StudyDate": "UNKNOWN",
            "Modality": "UNKNOWN",
            "BodyPartExamined": "UNKNOWN",
            "StudyInstanceUID": "UNKNOWN",
            "SeriesInstanceUID": "UNKNOWN",
            "SeriesDescription": f"Parse error: {e}",
            "PixelSpacing": None,
            "FilePath": str(file_path.resolve())
        }

def build_index(data_dir=None) -> pd.DataFrame:
    """
    Scans data_dir for all .dcm files and returns a pandas DataFrame of header metadata.
    Includes slice counts aggregated per series.
    """
    if data_dir is None:
        config = load_config()
        data_dir = config.get("data_dir", "data")

    folder = pathlib.Path(data_dir)
    dcm_files = list(folder.rglob("*.dcm"))

    columns = [
        "PatientID", "StudyDate", "Modality", "BodyPartExamined",
        "StudyInstanceUID", "SeriesInstanceUID", "SeriesDescription",
        "PixelSpacing", "FilePath", "slice_count"
    ]

    if not dcm_files:
        return pd.DataFrame(columns=columns)

    records = [extract_header(f) for f in dcm_files]
    df = pd.DataFrame(records)

    # Calculate slice count per series
    series_counts = df.groupby("SeriesInstanceUID")["FilePath"].transform("count")
    df["slice_count"] = series_counts

    return df

if __name__ == "__main__":
    df = build_index()
    print(f"Indexed {len(df)} DICOM files across {df['SeriesInstanceUID'].nunique()} series:")
    print(df[["PatientID", "Modality", "BodyPartExamined", "slice_count", "SeriesInstanceUID"]].to_string())
