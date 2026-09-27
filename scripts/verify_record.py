#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a CASEOPS evidence manifest."
    )
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()

    if not manifest_path.is_file():
        print(f"FAIL: manifest not found: {manifest_path}")
        return 1

    try:
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: invalid manifest: {exc}")
        return 1

    required = {
        "record_id",
        "stored_path",
        "size_bytes",
        "sha256",
    }

    missing = sorted(required - set(record))

    if missing:
        print("FAIL: manifest missing fields:")
        for field in missing:
            print(f"  - {field}")
        return 1

    stored = Path(record["stored_path"])

    if not stored.is_absolute():
        stored = REPO_ROOT / stored

    if not stored.is_file():
        print(f"FAIL: evidence file missing: {stored}")
        return 1

    actual_size = stored.stat().st_size
    actual_hash = sha256_file(stored)

    expected_size = int(record["size_bytes"])
    expected_hash = str(record["sha256"]).lower()

    size_ok = actual_size == expected_size
    hash_ok = actual_hash == expected_hash

    print()
    print("CASEOPS // RECORD VERIFICATION")
    print("=" * 60)
    print(f"Record ID:     {record['record_id']}")
    print(f"Evidence:      {stored}")
    print(f"Expected size: {expected_size}")
    print(f"Actual size:   {actual_size}")
    print(f"Expected hash: {expected_hash}")
    print(f"Actual hash:   {actual_hash}")
    print()

    if size_ok and hash_ok:
        print("RESULT: PASS")
        return 0

    print("RESULT: FAIL")

    if not size_ok:
        print("Reason: byte count mismatch")

    if not hash_ok:
        print("Reason: SHA-256 mismatch")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
