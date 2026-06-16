from flask import Flask, render_template, send_file, abort, Response
from pathlib import Path
import sqlite3
import os

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / 'data' / 'integrity_ledger.db'
AUDIT_LOG = REPO_ROOT / 'logs' / 'audit.log'
EVIDENCE_BASE = REPO_ROOT / 'evidence'

app = Flask(__name__, static_folder=str(REPO_ROOT / 'web' / 'static'))

def get_db_conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_conn()
    rows = []
    if conn:
        cur = conn.cursor()
        cur.execute('SELECT id,ts,filename,stored_path,sha256,size,notes FROM ledger ORDER BY ts DESC')
        rows = cur.fetchall()
        conn.close()
    return render_template('index.html', entries=rows)

@app.route('/evidence/<eid>')
def evidence_detail(eid):
    conn = get_db_conn()
    if not conn:
        abort(404)
    cur = conn.cursor()
    cur.execute('SELECT id,ts,filename,stored_path,sha256,size,notes FROM ledger WHERE id=?', (eid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        abort(404)
    return render_template('evidence.html', entry=row)

@app.route('/file/<eid>')
def serve_file(eid):
    conn = get_db_conn()
    if not conn:
        abort(404)
    cur = conn.cursor()
    cur.execute('SELECT stored_path FROM ledger WHERE id=?', (eid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        abort(404)
    stored = Path(REPO_ROOT) / row['stored_path']
    try:
        # ensure file is within evidence base
        stored.resolve().relative_to(EVIDENCE_BASE.resolve())
    except Exception:
        abort(403)
    if not stored.exists():
        abort(404)
    return send_file(str(stored), as_attachment=True)

@app.route('/logs')
def view_logs():
    if not AUDIT_LOG.exists():
        return Response('No logs found', mimetype='text/plain')
    # stream last 5000 bytes to avoid huge loads
    data = AUDIT_LOG.read_text(encoding='utf-8')
    return Response(data, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
