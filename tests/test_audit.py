"""
tests/test_audit.py

Unit tests for audit.py and verify_audit.py.
Verifies cryptographic hash chain creation and tamper detection.
"""

import json
import audit
import verify_audit

def test_audit_logging_and_verification(tmp_path):
    audit_file = tmp_path / "audit.jsonl"

    # Log 3 calls
    audit.log_call("tool_1", {"a": 1}, {"status": "ok"}, log_path=audit_file)
    audit.log_call("tool_2", {"b": 2}, {"status": "ok"}, log_path=audit_file)
    audit.log_call("tool_3", {"c": 3}, {"status": "ok"}, log_path=audit_file)

    # Verify log integrity
    valid, message = verify_audit.verify_audit_log(log_path=audit_file)
    assert valid is True
    assert "Verified 3" in message

def test_audit_tamper_detection(tmp_path):
    audit_file = tmp_path / "audit.jsonl"

    audit.log_call("tool_1", {"a": 1}, {"status": "ok"}, log_path=audit_file)
    audit.log_call("tool_2", {"b": 2}, {"status": "ok"}, log_path=audit_file)

    # Tamper with the 1st line payload content
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    first_record = json.loads(lines[0])
    first_record["args"]["a"] = 999  # Modified value!
    lines[0] = json.dumps(first_record)

    # Save tampered file back
    audit_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Verify log integrity fails
    valid, message = verify_audit.verify_audit_log(log_path=audit_file)
    assert valid is False
    assert "tamper detected" in message.lower()
