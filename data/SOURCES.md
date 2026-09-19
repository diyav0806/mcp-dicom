# Data Sources & Attribution Manifest

> **Prototype notice**: This project is for research and educational purposes only. Not for clinical use.

This repository includes metadata indexed from public, de-identified DICOM series downloaded from the [NCI Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov/).

## Downloaded Series Summary

| Collection | Patient ID | Modality | Slices | Size (MB) | License | DOI / Citation | Series Instance UID |
|---|---|---|---|---|---|---|---|
| `nlst` | `201397` | `CT` | 1 | 0.20 | CC BY 4.0 | [10.7937/tcia.hmq8-j677](https://doi.org/10.7937/tcia.hmq8-j677) | `1.3.6.1.4.1.14519.5.2.1.7009.9004.154889568880049104519951137017` |
| `ea1141` | `EA1141-8149894` | `MR` | 1 | 0.21 | CC BY 4.0 | [10.7937/2bas-hr33](https://doi.org/10.7937/2bas-hr33) | `1.3.6.1.4.1.14519.5.2.1.1620.1225.248202178673984645532634701440` |
| `varepop_apollo` | `AP-2CM3` | `DX` | 1 | 2.06 | CC BY 4.0 | [10.7937/ghkn-md15](https://doi.org/10.7937/ghkn-md15) | `1.3.6.1.4.1.14519.5.2.1.111496736574540772816177955707250560822` |

## Licensing & Provenance Statement

- All downloaded DICOM series strictly adhere to Creative Commons Attribution licenses (**CC BY 3.0** / **CC BY 4.0**).
- Series requiring restrictive or Non-Commercial licenses (**CC BY-NC**) were explicitly excluded.
- Data sourced via `idc-index` Python SDK (NCI Imaging Data Commons).
