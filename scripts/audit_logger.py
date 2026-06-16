#!/usr/bin/env python3
"""Minimal audit logger for command-center.

Writes JSON lines to logs/audit.log with timestamp, command, exit code, and truncated output.
"""
import json
import os
import datetime
import sys

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "audit.log")

def _now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def log_entry(command, returncode, stdout, stderr):
    entry = {
        "ts": _now_iso(),
        "command": command,
        "returncode": int(returncode),
        "stdout": (stdout or "")[:2000],
        "stderr": (stderr or "")[:2000],
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    # simple CLI: python audit_logger.py '<cmd>' <returncode> '<stdout>' '<stderr>'
    if len(sys.argv) >= 5:
        log_entry(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Usage: audit_logger.py '<cmd>' <returncode> '<stdout>' '<stderr>'")
