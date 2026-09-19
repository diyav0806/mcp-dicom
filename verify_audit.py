"""
verify_audit.py

Verifies the integrity of the append-only audit.jsonl log file by re-computing
SHA-256 hashes and validating the hash chain across all entries.

Prototype use only — not for clinical use.
"""

import json
import hashlib
import pathlib
import sys
from index import load_config

def verify_audit_log(log_path=None) -> tuple[bool, str]:
    """
    Reads the JSONL audit log file and checks:
    1. Valid JSON formatting per line.
    2. Correct SHA-256 computation for payload.
    3. Correct hash chaining (previous_hash matches prior entry's hash).

    Returns (True, "Integrity verified message") or (False, "Failure reason").
    """
    if log_path is None:
        config = load_config()
        log_path = config.get("audit_log", "audit.jsonl")

    path = pathlib.Path(log_path)
    if not path.exists():
        return True, "Audit log does not exist yet (0 entries)."

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return True, "Audit log is empty (0 entries)."

    expected_prev_hash = "0" * 64

    for i, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except Exception as e:
            return False, f"Line {i}: Invalid JSON formatting ({e})"

        stored_hash = record.get("hash")
        stored_prev_hash = record.get("previous_hash")

        if stored_prev_hash != expected_prev_hash:
            return False, (
                f"Line {i}: Hash chain broken! "
                f"Expected previous_hash '{expected_prev_hash}', got '{stored_prev_hash}'."
            )

        # Re-compute payload hash
        payload = {
            "timestamp": record.get("timestamp"),
            "tool": record.get("tool"),
            "args": record.get("args"),
            "result": record.get("result"),
            "previous_hash": record.get("previous_hash")
        }
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        computed_hash = hashlib.sha256(canonical_bytes).hexdigest()

        if computed_hash != stored_hash:
            return False, (
                f"Line {i}: Content tamper detected! "
                f"Computed hash '{computed_hash}' does not match stored hash '{stored_hash}'."
            )

        expected_prev_hash = stored_hash

    return True, f"Audit log intact. Verified {len(lines)} log entry/entries."

if __name__ == "__main__":
    valid, message = verify_audit_log()
    print(f"Audit Verification Result: {'PASSED' if valid else 'FAILED'}")
    print(message)
    if not valid:
        sys.exit(1)
