"""
tests/test_server.py

Unit tests for server.py MCP tools (query_patients, query_studies, get_series_summary, request_transfer).
Calls tool functions directly.
"""

import json
import pytest
import index
import server
import audit

def test_query_patients(monkeypatch, mock_dicom_dir):
    monkeypatch.setattr("server.build_index", lambda: index.build_index(data_dir=mock_dicom_dir))

    # Test all patients
    res_raw = server.query_patients()
    data = json.loads(res_raw)
    assert data["count"] == 2
    pids = [p["patient_id"] for p in data["patients"]]
    assert "PATIENT_A" in pids
    assert "PATIENT_B" in pids

    # Test patient filter
    res_filtered = json.loads(server.query_patients(patient_id="PATIENT_A"))
    assert res_filtered["count"] == 1
    assert res_filtered["patients"][0]["patient_id"] == "PATIENT_A"
    assert res_filtered["patients"][0]["total_slices"] == 2

def test_query_studies(monkeypatch, mock_dicom_dir):
    monkeypatch.setattr("server.build_index", lambda: index.build_index(data_dir=mock_dicom_dir))

    # Filter by modality CT
    res_ct = json.loads(server.query_studies(modality="CT"))
    assert res_ct["count"] == 1
    assert res_ct["studies"][0]["patient_id"] == "PATIENT_A"

    # Filter by modality MR
    res_mr = json.loads(server.query_studies(modality="MR"))
    assert res_mr["count"] == 1
    assert res_mr["studies"][0]["patient_id"] == "PATIENT_B"

def test_get_series_summary(monkeypatch, mock_dicom_dir):
    monkeypatch.setattr("server.build_index", lambda: index.build_index(data_dir=mock_dicom_dir))

    df = index.build_index(data_dir=mock_dicom_dir)
    target_series = df.iloc[0]["SeriesInstanceUID"]

    res_raw = server.get_series_summary(target_series)
    data = json.loads(res_raw)

    assert "series" in data
    assert data["series"]["series_instance_uid"] == target_series
    assert data["series"]["patient_id"] == df.iloc[0]["PatientID"]

    # Test non-existent series
    res_missing = json.loads(server.get_series_summary("INVALID_SERIES_UID"))
    assert "error" in res_missing

def test_request_transfer(monkeypatch, mock_dicom_dir, tmp_path):
    monkeypatch.setattr("server.build_index", lambda: index.build_index(data_dir=mock_dicom_dir))

    # Redirect audit log to temporary test file
    test_audit_path = tmp_path / "test_audit.jsonl"
    monkeypatch.setattr("audit.load_config", lambda: {"audit_log": str(test_audit_path)})

    df = index.build_index(data_dir=mock_dicom_dir)
    target_series = df.iloc[0]["SeriesInstanceUID"]

    res_raw = server.request_transfer(series_uid=target_series, destination="TEST_PACS")
    data = json.loads(res_raw)

    assert data["status"] == "pending_approval"
    assert data["series_instance_uid"] == target_series
    assert data["destination"] == "TEST_PACS"
    assert "request_id" in data

    # Verify audit file was actually created and written
    assert test_audit_path.exists()
    assert test_audit_path.stat().st_size > 0
