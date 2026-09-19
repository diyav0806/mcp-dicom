"""
server.py

Minimal Model Context Protocol (MCP) server exposing 4 DICOM metadata and transfer tools.
Built with official MCP Python SDK v2.

Prototype use only — not for clinical use.
"""

import json
import uuid
from mcp.server.mcpserver import MCPServer
from index import build_index
from audit import log_call

# Initialize the MCP Server instance
mcp = MCPServer("mini-dicom-mcp")

@mcp.tool()
def query_patients(patient_id: str = "") -> str:
    """
    Search indexed DICOM patients and return aggregated statistics per patient.

    Args:
        patient_id: Optional patient ID string to filter by (case-insensitive substring match).
    """
    df = build_index()
    if df.empty:
        return json.dumps({"patients": [], "count": 0})

    if patient_id.strip():
        pid_clean = patient_id.strip().lower()
        df = df[df["PatientID"].astype(str).str.lower().str.contains(pid_clean)]

    if df.empty:
        return json.dumps({"patients": [], "count": 0})

    results = []
    grouped = df.groupby("PatientID")
    for pid, group in grouped:
        modalities = sorted(group["Modality"].unique().tolist())
        studies_count = int(group["StudyInstanceUID"].nunique())
        series_count = int(group["SeriesInstanceUID"].nunique())
        total_slices = len(group)
        
        results.append({
            "patient_id": pid,
            "modalities": modalities,
            "studies_count": studies_count,
            "series_count": series_count,
            "total_slices": total_slices
        })

    return json.dumps({"patients": results, "count": len(results)}, indent=2)

@mcp.tool()
def query_studies(patient_id: str = "", modality: str = "") -> str:
    """
    Search indexed DICOM studies matching patient ID or imaging modality.

    Args:
        patient_id: Optional patient ID filter.
        modality: Optional imaging modality filter (e.g. 'CT', 'MR', 'DX').
    """
    df = build_index()
    if df.empty:
        return json.dumps({"studies": [], "count": 0})

    if patient_id.strip():
        pid_clean = patient_id.strip().lower()
        df = df[df["PatientID"].astype(str).str.lower().str.contains(pid_clean)]

    if modality.strip():
        mod_clean = modality.strip().upper()
        df = df[df["Modality"].astype(str).str.upper() == mod_clean]

    if df.empty:
        return json.dumps({"studies": [], "count": 0})

    results = []
    grouped = df.groupby("StudyInstanceUID")
    for st_uid, group in grouped:
        first_row = group.iloc[0]
        results.append({
            "study_instance_uid": st_uid,
            "patient_id": str(first_row["PatientID"]),
            "study_date": str(first_row["StudyDate"]),
            "modality": str(first_row["Modality"]),
            "body_part_examined": str(first_row["BodyPartExamined"]),
            "series_count": int(group["SeriesInstanceUID"].nunique()),
            "total_slices": len(group)
        })

    return json.dumps({"studies": results, "count": len(results)}, indent=2)

@mcp.tool()
def get_series_summary(series_uid: str) -> str:
    """
    Retrieve header metadata summary for a given DICOM SeriesInstanceUID.
    Does not extract or return pixel data.

    Args:
        series_uid: Exact DICOM SeriesInstanceUID.
    """
    df = build_index()
    if df.empty:
        return json.dumps({"error": "No indexed DICOM data available."})

    sub = df[df["SeriesInstanceUID"] == series_uid.strip()]
    if sub.empty:
        return json.dumps({"error": f"SeriesInstanceUID '{series_uid}' not found in local index."})

    first_row = sub.iloc[0]
    summary = {
        "series_instance_uid": str(first_row["SeriesInstanceUID"]),
        "patient_id": str(first_row["PatientID"]),
        "study_instance_uid": str(first_row["StudyInstanceUID"]),
        "study_date": str(first_row["StudyDate"]),
        "modality": str(first_row["Modality"]),
        "body_part_examined": str(first_row["BodyPartExamined"]),
        "series_description": str(first_row["SeriesDescription"]),
        "slice_count": int(first_row["slice_count"]),
        "pixel_spacing": first_row["PixelSpacing"],
        "sample_file_path": str(first_row["FilePath"])
    }

    return json.dumps({"series": summary}, indent=2)

@mcp.tool()
def request_transfer(series_uid: str, destination: str) -> str:
    """
    Request transfer/export of a DICOM series to a specified destination.
    Logs the transfer request to an append-only audit trail.

    Args:
        series_uid: Exact DICOM SeriesInstanceUID to transfer.
        destination: Transfer target (e.g. 'PACS_DEST_01', 's3://my-bucket/').
    """
    series_clean = series_uid.strip()
    dest_clean = destination.strip()

    if not dest_clean:
        return json.dumps({"error": "Destination path or server name is required."})

    df = build_index()
    sub = df[df["SeriesInstanceUID"] == series_clean]
    if sub.empty:
        return json.dumps({"error": f"SeriesInstanceUID '{series_clean}' not found in local index."})

    first_row = sub.iloc[0]
    request_id = str(uuid.uuid4())

    result_summary = {
        "request_id": request_id,
        "status": "pending_approval",
        "series_instance_uid": series_clean,
        "patient_id": str(first_row["PatientID"]),
        "modality": str(first_row["Modality"]),
        "destination": dest_clean,
        "slice_count": int(first_row["slice_count"])
    }

    # Log to audit trail
    log_call(
        tool="request_transfer",
        args={"series_uid": series_clean, "destination": dest_clean},
        result_summary=result_summary
    )

    return json.dumps(result_summary, indent=2)

if __name__ == "__main__":
    mcp.run()
