# mini-dicom-mcp

> **Research Prototype Notice**: This project is for educational and research prototyping purposes only. **Not for clinical use, medical diagnosis, or patient care.**

A minimal [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server written in Python 3.12 that enables AI assistants (such as VS Code GitHub Copilot Agent Mode or Claude Desktop) to query and search a small dataset of **real, public, de-identified DICOM scans** stored locally.

---

## 🏗️ Architecture

```
mcp-dicom/
├── .vscode/
│   └── mcp.json            # VS Code Copilot Agent Mode configuration
├── .gitignore              # Ignores downloaded DICOM files and venv
├── config.json             # Central configuration (data_dir, audit_log)
├── requirements.txt        # Pinned dependencies (mcp, pydicom, pandas, idc-index, pytest)
├── index.py                # In-memory DICOM header metadata indexer (pydicom + pandas)
├── server.py               # MCP Server exposing 4 DICOM tools (MCP Python SDK v2)
├── audit.py                # Cryptographic SHA-256 hash-chained JSONL audit logger
├── verify_audit.py         # Audit log tamper detection verification tool
├── scripts/
│   └── fetch_data.py       # Queries NCI IDC and downloads CC BY DICOM series
├── data/
│   └── SOURCES.md          # Provenance, licensing, and citations manifest
└── tests/
    ├── conftest.py         # Pytest fixtures for synthetic DICOM generation
    ├── test_index.py       # Unit tests for index building
    ├── test_server.py      # Unit tests for all 4 MCP tools
    └── test_audit.py       # Unit tests for tamper detection and hash chaining
```

---

## ⚡ Quickstart & Setup

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd mcp-dicom

# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 3. Download Sample DICOM Scans
Run the data fetching script to query the NCI Imaging Data Commons (IDC) and download 3 small, open-access DICOM series:
```bash
python scripts/fetch_data.py
```

### 4. Verify Local DICOM Index
Verify header parsing and index creation:
```bash
python index.py
```

### 5. Run Pytest Test Suite
Run the offline test suite:
```bash
pytest -v
```

---

## 💻 Run in VS Code (GitHub Copilot Agent Mode)

1. Open this repository folder in **VS Code**.
2. Ensure `.vscode/mcp.json` exists in the workspace root:
   ```json
   {
     "servers": {
       "mini-dicom-mcp": {
         "type": "stdio",
         "command": "${workspaceFolder}/.venv/Scripts/python",
         "args": [
           "${workspaceFolder}/server.py"
         ]
       }
     }
   }
   ```
3. Open **GitHub Copilot Chat** in VS Code and switch to **Agent Mode**.
4. Type `@` in the chat input and select `mini-dicom-mcp`.
5. Ask Copilot questions such as:
   - *"What patients are available in the local DICOM database?"*
   - *"Find all CT studies and list their modalities and body parts."*
   - *"Get a summary for series `1.3.6.1.4.1.14519.5.2.1.7009.9004.154889568880049104519951137017`."*
   - *"Request a transfer for series `1.3.6.1.4.1.14519.5.2.1.1620.1225.248202178673984645532634701440` to `PACS_DEST_01`."*

---

## 🔍 Debugging with MCP Inspector

To test and inspect the server using the official interactive MCP Inspector UI:

```bash
npx @modelcontextprotocol/inspector python server.py
```
Open the browser URL provided in the terminal (usually `http://localhost:5173`) to view and test all 4 tools interactively.

---

## 🛠️ MCP Tools Reference

| Tool Name | Parameters | Description |
|---|---|---|
| `query_patients` | `patient_id: str = ""` | Returns aggregated patient statistics (modalities, study counts, series counts, total slices). |
| `query_studies` | `patient_id: str = ""`, `modality: str = ""` | Searches DICOM studies matching patient ID or imaging modality (`CT`, `MR`, `DX`). |
| `get_series_summary` | `series_uid: str` | Retrieves DICOM header metadata summary (body part, pixel spacing, slice count). **No pixel data returned.** |
| `request_transfer` | `series_uid: str`, `destination: str` | Simulates a DICOM export/transfer request and records it to a tamper-evident audit log. |

---

## 🔒 Audit Logging & Tamper Detection

All DICOM transfer requests via `request_transfer` write to an append-only JSONL audit log (`audit.jsonl`). Each log record includes:
- ISO timestamp
- Tool name & arguments
- Transfer request summary
- SHA-256 cryptographic hash of the current entry combined with the `previous_hash` (blockchain-style hash chaining).

### Verify Audit Integrity
Run the audit log verifier to validate hash chains and detect file tampering:
```bash
python verify_audit.py
```

---

## 📜 Data Provenance & Attribution

All sample DICOM scans included in this research prototype are sourced from the **[NCI Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov/)**.

- **Licensing**: All series strictly use Creative Commons Attribution licenses (**CC BY 3.0** / **CC BY 4.0**). Series with Non-Commercial restrictions (**CC BY-NC**) were explicitly excluded.
- Detailed series provenance, DOIs, and citations are recorded in [data/SOURCES.md](data/SOURCES.md).

### Collections & Citations
- **NLST** (National Lung Screening Trial) — [DOI: 10.7937/tcia.hmq8-j677](https://doi.org/10.7937/tcia.hmq8-j677)
- **EA1141** — [DOI: 10.7937/2bas-hr33](https://doi.org/10.7937/2bas-hr33)
- **VAREPOP_APOLLO** — [DOI: 10.7937/ghkn-md15](https://doi.org/10.7937/ghkn-md15)

---

## ⚠️ Limitations & Disclaimer

- **Not for Clinical Use**: This project is an academic prototype demonstrating MCP integration with medical imaging metadata.
- **Header-Only Indexing**: Pixel data is neither sent to the AI assistant nor loaded into memory during indexing (`stop_before_pixels=True`).
- **Local Prototype**: Designed for local execution with `stdio` transport.
