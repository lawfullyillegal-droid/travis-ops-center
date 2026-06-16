#!/usr/bin/env python3
"""Ingest evidence files, compute hash, store copy, and record in SQLite ledger.

Usage: python3 scripts/evidence_ingest.py /path/to/file --notes "short description"
"""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "evidence"
DB_PATH = REPO_ROOT / "data" / "integrity_ledger.db"
os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(DB_PATH.parent, exist_ok=True)

def sha256_of_file(path, chunk_size=8192):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()

def init_db(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS ledger (
        id TEXT PRIMARY KEY,
        ts TEXT,
        filename TEXT,
        stored_path TEXT,
        sha256 TEXT,
        size INTEGER,
        notes TEXT
    )''')
    conn.commit()

def ingest(src_path, notes=""):
    src = Path(src_path).expanduser().resolve()
    if not src.exists():
        raise FileNotFoundError(src)
    sha = sha256_of_file(src)
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    uid = f"evidence-{ts}-{sha[:10]}"
    dest_dir = EVIDENCE_DIR / ts[:8]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uid}{src.suffix}"
    shutil.copy2(src, dest)
    size = dest.stat().st_size

    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)
    conn.execute('INSERT INTO ledger (id,ts,filename,stored_path,sha256,size,notes) VALUES (?,?,?,?,?,?,?)',
                 (uid, ts, src.name, str(dest.relative_to(REPO_ROOT)), sha, size, notes))
    conn.commit()
    conn.close()

    # write metadata JSON next to file
    meta = {
        'id': uid,
        'ts': ts,
        'original_path': str(src),
        'stored_path': str(dest.relative_to(REPO_ROOT)),
        'sha256': sha,
        'size': size,
        'notes': notes,
    }
    meta_path = dest.with_suffix(dest.suffix + '.meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(json.dumps(meta, ensure_ascii=False))
    return meta

def main():
    p = argparse.ArgumentParser()
    p.add_argument('file', help='Path to evidence file')
    p.add_argument('--notes', default='', help='Short notes or description')
    args = p.parse_args()
    meta = ingest(args.file, args.notes)
    # simple audit log via existing audit_logger if available
    try:
        from scripts import audit_logger as audit
        audit.log_entry(f"ingest:{meta['id']}", 0, json.dumps({'sha256':meta['sha256']}), '')
    except Exception:
        pass

if __name__ == '__main__':
    main()
