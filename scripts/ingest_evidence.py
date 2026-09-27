#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "evidence"
DEFAULT_MANIFEST_DIR = REPO_ROOT / "manifests"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_record_id(now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    token = uuid.uuid4().hex[:8].upper()
    return f"EVID-{stamp}-{token}"


def safe_destination(directory: Path, original_name: str, record_id: str) -> Path:
    candidate = directory / original_name

    if not candidate.exists():
        return candidate

    src = Path(original_name)
    return directory / f"{src.stem}-{record_id}{src.suffix}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a source file into the CASEOPS evidence store."
    )

    parser.add_argument("source", type=Path)
    parser.add_argument("--operator", default=os.environ.get("USER", "unknown"))
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_EVIDENCE_DIR,
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=DEFAULT_MANIFEST_DIR,
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=None,
        help="Optional explicit manifest path.",
    )

    args = parser.parse_args()

    source = args.source.expanduser().resolve()

    if not source.is_file():
        raise SystemExit(f"ERROR: source file not found: {source}")

    now = utc_now()
    record_id = build_record_id(now)

    evidence_dir = args.evidence_dir.expanduser()
    manifest_dir = args.manifest_dir.expanduser()

    # Organize locally by UTC year/month.
    target_dir = evidence_dir / now.strftime("%Y") / now.strftime("%m")
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    original_hash = sha256_file(source)
    original_size = source.stat().st_size

    destination = safe_destination(
        target_dir,
        source.name,
        record_id,
    )

    # Exclusive creation prevents accidental overwrite.
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst, length=1024 * 1024)

    copied_hash = sha256_file(destination)
    copied_size = destination.stat().st_size

    if copied_hash != original_hash or copied_size != original_size:
        destination.unlink(missing_ok=True)
        raise SystemExit("ERROR: copied evidence failed integrity verification")

    try:
        stored_path = destination.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        stored_path = str(destination.resolve())

    manifest = {
        "schema": "caseops-evidence-record/v1",
        "record_id": record_id,
        "ingested_at_utc": now.isoformat().replace("+00:00", "Z"),
        "original_filename": source.name,
        "source_path_at_ingest": str(source),
        "stored_path": stored_path,
        "size_bytes": copied_size,
        "sha256": copied_hash,
        "operator": args.operator,
        "acquisition_notes": args.notes,
        "classification": "source_evidence",
        "hash_algorithm": "SHA-256",
    }

    if args.manifest_out:
        manifest_path = args.manifest_out.expanduser()

        if not manifest_path.is_absolute():
            manifest_path = REPO_ROOT / manifest_path
    else:
        manifest_path = manifest_dir / f"{record_id}.json"

    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    if manifest_path.exists():
        raise SystemExit(f"ERROR: manifest already exists: {manifest_path}")

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print()
    print("CASEOPS // EVIDENCE INGESTED")
    print("=" * 60)
    print(f"Record ID: {record_id}")
    print(f"Original:  {source}")
    print(f"Stored:    {destination}")
    print(f"Bytes:     {copied_size}")
    print(f"SHA-256:   {copied_hash}")
    print(f"Manifest:  {manifest_path}")
    print()

    # Final line is machine-readable for shell scripts.
    print(manifest_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
