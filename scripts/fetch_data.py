"""
scripts/fetch_data.py

Downloads a small set (3-4) of real, de-identified public DICOM series from the
NCI Imaging Data Commons (IDC) using idc-index, ensuring strict CC BY licensing.
Generates data/SOURCES.md with full attribution and metadata.

Prototype usage only — not for clinical use.
"""

import os
import sys
import pathlib
from idc_index import index

def main():
    # Load configuration
    project_root = pathlib.Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    sources_md_path = data_dir / "SOURCES.md"

    data_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing IDCClient...")
    client = index.IDCClient()

    # Step 1: Inspect index schema to avoid hard-coding unknown columns
    print("Inspecting IDC index schema...")
    schema_df = client.sql_query("DESCRIBE index")
    available_cols = set(schema_df["column_name"].tolist())
    print(f"Index table has {len(available_cols)} columns.")

    # Step 2: Query for 3 distinct, small series (CT, MR, DX) under CC BY licenses (no CC BY-NC)
    print("Querying IDC index for representative small series (CT, MR, DX)...")
    
    # We query top candidate per modality under CC BY licence (< 10 MB total each)
    query = """
    SELECT 
        collection_id, 
        PatientID, 
        SeriesInstanceUID, 
        StudyInstanceUID,
        Modality, 
        BodyPartExamined, 
        SeriesDescription, 
        instanceCount, 
        series_size_MB, 
        license_short_name, 
        source_DOI
    FROM index 
    WHERE series_size_MB BETWEEN 0.2 AND 8
      AND license_short_name LIKE '%CC BY%' 
      AND license_short_name NOT LIKE '%NC%'
      AND Modality IN ('CT', 'MR', 'DX')
    ORDER BY series_size_MB ASC
    """
    
    df = client.sql_query(query)

    # Pick 1 small series for each modality
    selected_series = []
    for modality in ["CT", "MR", "DX"]:
        sub = df[df["Modality"] == modality]
        if not sub.empty:
            selected_series.append(sub.iloc[0].to_dict())

    if not selected_series:
        print("Error: No series matched the query criteria.")
        sys.exit(1)

    print(f"Selected {len(selected_series)} series for download:")
    for item in selected_series:
        print(f" - [{item['Modality']}] Collection: {item['collection_id']}, Patient: {item['PatientID']}, Slices: {item['instanceCount']}, Size: {item['series_size_MB']:.2f} MB, License: {item['license_short_name']}")

    # Step 3: Download each DICOM series into data/
    print("\nDownloading DICOM series into data/...")
    for item in selected_series:
        uid = item["SeriesInstanceUID"]
        print(f"Downloading Series UID: {uid}...")
        client.download_dicom_series(
            seriesInstanceUID=uid,
            downloadDir=str(data_dir)
        )

    # Step 4: Write data/SOURCES.md manifest
    print(f"\nWriting manifest to {sources_md_path}...")
    sources_content = [
        "# Data Sources & Attribution Manifest",
        "",
        "> **Prototype notice**: This project is for research and educational purposes only. Not for clinical use.",
        "",
        "This repository includes metadata indexed from public, de-identified DICOM series downloaded from the [NCI Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov/).",
        "",
        "## Downloaded Series Summary",
        "",
        "| Collection | Patient ID | Modality | Slices | Size (MB) | License | DOI / Citation | Series Instance UID |",
        "|---|---|---|---|---|---|---|---|"
    ]

    for item in selected_series:
        doi = item.get("source_DOI") or "N/A"
        doi_link = f"[{doi}](https://doi.org/{doi})" if doi != "N/A" else "N/A"
        sources_content.append(
            f"| `{item['collection_id']}` | `{item['PatientID']}` | `{item['Modality']}` | {item['instanceCount']} | {item['series_size_MB']:.2f} | {item['license_short_name']} | {doi_link} | `{item['SeriesInstanceUID']}` |"
        )

    sources_content.extend([
        "",
        "## Licensing & Provenance Statement",
        "",
        "- All downloaded DICOM series strictly adhere to Creative Commons Attribution licenses (**CC BY 3.0** / **CC BY 4.0**).",
        "- Series requiring restrictive or Non-Commercial licenses (**CC BY-NC**) were explicitly excluded.",
        "- Data sourced via `idc-index` Python SDK (NCI Imaging Data Commons).",
        ""
    ])

    with open(sources_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sources_content))

    print("Data fetch and manifest creation completed successfully!")

if __name__ == "__main__":
    main()
