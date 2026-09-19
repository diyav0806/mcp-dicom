"""
audit.py

Append-only, tamper-evident JSONL audit logging using cryptographic SHA-256 hash chaining.
Each log entry contains a timestamp, tool name, arguments, summary result, and a SHA-256 hash
of the previous record.

Prototype use only — not for clinical use.
"""

import json
import hashlib
import pathlib
import datetime
from index import load_config

def _get_audit_log_path(log_path=None) -> pathlib.Path:
    if log_path is None:
        config = load_config()
        log_path = config.get("audit_log", "audit.jsonl")
    return pathlib.Path(log_path)

def _get_last_hash(log_file: pathlib.Path) -> str:
    """Returns the SHA-256 hash of the last line in the audit log, or 64 zeros if empty/missing."""
    if not log_file.exists() or log_file.stat().st_size == 0:
        return "0" * 64
    
    last_line = ""
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last_line = line
    
    if not last_line:
        return "0" * 64
    
    try:
        data = json.loads(last_line)
        return data.get("hash", "0" * 64)
    except Exception:
        return "0" * 64

def log_call(tool: str, args: dict, result_summary: dict, log_path=None) -> dict:
    """
    Appends a new audit record to the JSONL log file with a cryptographic hash chain.
    """
    log_file = _get_audit_log_path(log_path)
    previous_hash = _get_last_hash(log_file)
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Core entry data (without the hash field itself)
    payload = {
        "timestamp": timestamp,
        "tool": tool,
        "args": args,
        "result": result_summary,
        "previous_hash": previous_hash
    }
    
    # Compute SHA-256 over deterministic JSON payload
    canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    entry_hash = hashlib.sha256(canonical_bytes).hexdigest()
    
    payload["hash"] = entry_hash
    
    # Append line to JSONL audit log
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")
        
    return payload
