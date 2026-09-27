from pathlib import Path
from secrets import compare_digest
import os
import sqlite3

from flask import Flask, Response, abort, jsonify, render_template, send_file
from flask_httpauth import HTTPBasicAuth

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "integrity_ledger.db"
AUDIT_LOG = REPO_ROOT / "logs" / "audit.log"
EVIDENCE_BASE = REPO_ROOT / "evidence"

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1").strip() or "127.0.0.1"
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))
AUTH_USER = os.getenv("AUTH_USER", "").strip()
AUTH_PASS = os.getenv("AUTH_PASS", "")
ALLOW_INSECURE_NO_AUTH = os.getenv("ALLOW_INSECURE_NO_AUTH", "0") == "1"

if bool(AUTH_USER) != bool(AUTH_PASS):
    raise RuntimeError("Set both AUTH_USER and AUTH_PASS, or leave both empty.")

AUTH_ENABLED = bool(AUTH_USER and AUTH_PASS)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}

if not AUTH_ENABLED and SERVER_HOST not in LOOPBACK_HOSTS and not ALLOW_INSECURE_NO_AUTH:
    raise RuntimeError(
        "Refusing unauthenticated non-loopback bind. "
        "Set AUTH_USER/AUTH_PASS or bind SERVER_HOST=127.0.0.1."
    )

app = Flask(__name__, static_folder=str(REPO_ROOT / "web" / "static"))
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    if not AUTH_ENABLED:
        return True
    return compare_digest(str(username), AUTH_USER) and compare_digest(str(password), AUTH_PASS)


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def get_db_conn():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
@auth.login_required
def index():
    return render_template("dashboard.html")


@app.route("/api/ledger")
@auth.login_required
def ledger_api():
    conn = get_db_conn()
    if not conn:
        return jsonify([])
    try:
        rows = conn.execute(
            "SELECT id,ts,filename,stored_path,sha256,size,notes "
            "FROM ledger ORDER BY ts DESC"
        ).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.route("/evidence/<eid>")
@auth.login_required
def evidence_detail(eid):
    conn = get_db_conn()
    if not conn:
        abort(404)
    try:
        row = conn.execute(
            "SELECT id,ts,filename,stored_path,sha256,size,notes "
            "FROM ledger WHERE id=?",
            (eid,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        abort(404)
    return render_template("evidence.html", entry=row)


@app.route("/file/<eid>")
@auth.login_required
def serve_file(eid):
    conn = get_db_conn()
    if not conn:
        abort(404)
    try:
        row = conn.execute("SELECT stored_path FROM ledger WHERE id=?", (eid,)).fetchone()
    finally:
        conn.close()

    if not row:
        abort(404)

    stored = REPO_ROOT / row["stored_path"]
    try:
        stored.resolve().relative_to(EVIDENCE_BASE.resolve())
    except Exception:
        abort(403)

    if not stored.is_file():
        abort(404)

    return send_file(str(stored), as_attachment=True)


@app.route("/logs")
@auth.login_required
def view_logs():
    if not AUDIT_LOG.exists():
        return Response("No logs found", mimetype="text/plain")

    tail_bytes = 5000
    with AUDIT_LOG.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - tail_bytes))
        data = handle.read().decode("utf-8", errors="replace")

    return Response(data, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
