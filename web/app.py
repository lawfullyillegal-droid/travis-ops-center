from flask import Flask, render_template, send_file, abort, Response, jsonify
from flask_httpauth import HTTPBasicAuth
from pathlib import Path
import sqlite3
import os

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / 'data' / 'integrity_ledger.db'
AUDIT_LOG = REPO_ROOT / 'logs' / 'audit.log'
EVIDENCE_BASE = REPO_ROOT / 'evidence'

app = Flask(__name__, static_folder=str(REPO_ROOT / 'web' / 'static'))
auth = HTTPBasicAuth()

# Optional authentication (enable via AUTH_USER env var)
ENABLED_AUTH = os.getenv('AUTH_USER') and os.getenv('AUTH_PASS')
AUTH_USER = os.getenv('AUTH_USER', 'admin')
AUTH_PASS = os.getenv('AUTH_PASS', 'password')

@auth.verify_password
def verify_password(username, password):
    if not ENABLED_AUTH:
        return True
    return username == AUTH_USER and password == AUTH_PASS

def get_db_conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
@auth.login_required
def index():
    return render_template('dashboard.html')

@app.route('/api/ledger')
@auth.login_required
def ledger_api():
    conn = get_db_conn()
    if not conn:
        return jsonify([])
    cur = conn.cursor()
    cur.execute('SELECT id,ts,filename,stored_path,sha256,size,notes FROM ledger ORDER BY ts DESC')
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/evidence/<eid>')
@auth.login_required
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
@auth.login_required
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
@auth.login_required
def view_logs():
    if not AUDIT_LOG.exists():
        return Response('No logs found', mimetype='text/plain')
    # stream last 5000 bytes to avoid huge loads
    data = AUDIT_LOG.read_text(encoding='utf-8')
    return Response(data, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('SERVER_PORT', 8080)), debug=False)
