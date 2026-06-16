#!/usr/bin/env python3
"""Generate an Obsidian note for an ingested evidence item.

Usage: python3 scripts/gen_evidence_note.py <evidence-id>
"""
import sys
import sqlite3
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "integrity_ledger.db"
VAULT_DIR = REPO_ROOT  # assume repo root is the vault; adjust if different
NOTES_DIR = VAULT_DIR / "evidence_notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

def find_entry(eid):
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute('SELECT id,ts,filename,stored_path,sha256,size,notes FROM ledger WHERE id=?', (eid,))
    row = cur.fetchone()
    conn.close()
    return row

def make_note(row):
    eid, ts, filename, stored_path, sha256, size, notes = row
    note_path = NOTES_DIR / f"{eid}.md"
    content = f"# Evidence {eid}\n\n- **Timestamp:** {ts}\n- **Original filename:** {filename}\n- **Stored path:** {stored_path}\n- **SHA256:** {sha256}\n- **Size:** {size}\n- **Notes:** {notes}\n\n## Quick links\n- [Open file]({stored_path})\n\n"
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return note_path

def main():
    if len(sys.argv) < 2:
        print('Usage: gen_evidence_note.py <evidence-id>')
        return 2
    eid = sys.argv[1]
    row = find_entry(eid)
    if not row:
        print('Not found in ledger')
        return 1
    note = make_note(row)
    print(f'Wrote note: {note}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
