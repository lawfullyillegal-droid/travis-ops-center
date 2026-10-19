from pathlib import Path
from secrets import token_urlsafe
from threading import Lock
from urllib.parse import urlsplit
import subprocess
from flask import request
from secrets import compare_digest
import json
import os
import sqlite3

from flask import Flask, Response, abort, jsonify, render_template, send_file
from flask_httpauth import HTTPBasicAuth

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "integrity_ledger.db"
AUDIT_LOG = REPO_ROOT / "logs" / "audit.log"
EVIDENCE_BASE = REPO_ROOT / "evidence"
REVIEW_DATA_PATH = REPO_ROOT / "review-site" / "data.json"
IDENTIFIER_DB_PATH = REPO_ROOT / "data" / "identifier_intel" / "identifier_intel.db"

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
    return render_template("dashboard.html", git_csrf=GIT_CSRF_TOKEN if AUTH_ENABLED else "")


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



@app.route("/api/review-data")
@auth.login_required
def review_data_api():
    """Return the curated CaseOps review dataset."""
    if not REVIEW_DATA_PATH.is_file():
        return jsonify({
            "cases": [],
            "timeline": [],
            "verified_edges": [],
            "open_questions": [],
            "limits": [],
            "error": "Review dataset not initialized",
        })

    try:
        payload = json.loads(
            REVIEW_DATA_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        return jsonify({
            "error": "Unable to read review dataset",
            "detail": str(exc),
        }), 500

    return jsonify(payload)


@app.route("/api/identifier-summary")
@auth.login_required
def identifier_summary_api():
    """Read-only summary of the identifier intelligence database."""

    empty = {
        "status": "not_initialized",
        "counts": {
            "identifiers": 0,
            "entities": 0,
            "source_snapshots": 0,
            "links": 0,
            "anomalies": 0,
        },
        "recent_links": [],
        "recent_anomalies": [],
    }

    if not IDENTIFIER_DB_PATH.is_file():
        return jsonify(empty)

    try:
        conn = sqlite3.connect(
            f"file:{IDENTIFIER_DB_PATH}?mode=ro",
            uri=True,
        )
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        return jsonify({
            **empty,
            "status": "error",
            "error": str(exc),
        }), 500

    try:
        counts = {}

        for table in (
            "identifiers",
            "entities",
            "source_snapshots",
            "links",
            "anomalies",
        ):
            counts[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        links = conn.execute(
            """
            SELECT
                id,
                from_type,
                from_value,
                relation,
                to_type,
                to_value,
                status,
                confidence,
                source_snapshot_id,
                evidence_ref,
                event_date,
                notes
            FROM links
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

        anomalies = conn.execute(
            """
            SELECT
                id,
                category,
                severity,
                subject,
                description,
                created_at
            FROM anomalies
            ORDER BY id DESC
            LIMIT 50
            """
        ).fetchall()

        return jsonify({
            "status": "ready",
            "counts": counts,
            "recent_links": [dict(row) for row in links],
            "recent_anomalies": [dict(row) for row in anomalies],
        })

    except sqlite3.Error as exc:
        return jsonify({
            **empty,
            "status": "error",
            "error": str(exc),
        }), 500

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



# CASEOPS_GIT_SYNC_V1
# The browser can fetch and fast-forward reviewed code. It cannot stage, commit,
# push or publish local evidence. Writes require configured HTTP Basic credentials.
GIT_CSRF_TOKEN = token_urlsafe(32)
GIT_SYNC_LOCK = Lock()
TRUSTED_GIT_REMOTES = {
    "https://github.com/lawfullyillegal-droid/travis-ops-center.git",
    "https://github.com/lawfullyillegal-droid/travis-ops-center",
    "git@github.com:lawfullyillegal-droid/travis-ops-center.git",
}


class GitSyncFailure(RuntimeError):
    pass


def git_exec(*args, timeout=20):
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=timeout, check=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        # Avoid sending potentially sensitive Git stderr into a public dashboard.
        raise GitSyncFailure("Git command failed; check Termux for details.") from exc


def git_review_snapshot():
    repo = Path(git_exec("rev-parse", "--show-toplevel")).resolve()
    if repo != REPO_ROOT.resolve():
        raise GitSyncFailure("Git checkout does not match CaseOps root.")
    origin = git_exec("remote", "get-url", "origin")
    if origin not in TRUSTED_GIT_REMOTES:
        raise GitSyncFailure("Unexpected origin remote. Inspect in Termux.")
    branch = git_exec("branch", "--show-current")
    head = git_exec("rev-parse", "HEAD")
    # Strictly use the local fetched tracking ref, never an unreviewed pull.
    remote = git_exec("rev-parse", "refs/remotes/origin/main")
    working = git_exec("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    ahead, behind = map(int, git_exec(
        "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"
    ).split())
    incoming = git_exec("diff", "--name-only", "HEAD..refs/remotes/origin/main").splitlines()
    return {
        "branch": branch, "head": head, "remote": remote,
        "ahead": ahead, "behind": behind, "clean": not working,
        "local_change_count": len(working),
        "incoming_files": incoming[:50], "incoming_count": len(incoming),
        "can_update": (branch == "main" and not working and ahead == 0 and behind > 0),
        "write_enabled": AUTH_ENABLED,
        "notice": "Only code is updated. Private evidence is never staged or published.",
    }


def git_request_authorized():
    if not AUTH_ENABLED or not request.is_json:
        return False
    origin = request.headers.get("Origin", "")
    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != request.host:
        return False
    token = request.headers.get("X-CaseOps-CSRF", "")
    return bool(token) and compare_digest(token, GIT_CSRF_TOKEN)


@app.route("/api/git/status")
@auth.login_required
def git_status_api():
    if not AUTH_ENABLED:
        return jsonify({"error": "Start the dashboard using scripts/caseops-web to enable Git controls."}), 403
    try:
        return jsonify(git_review_snapshot())
    except GitSyncFailure as exc:
        return jsonify({"error": str(exc)}), 503


@app.route("/api/git/fetch", methods=["POST"])
@auth.login_required
def git_fetch_api():
    if not git_request_authorized():
        return jsonify({"error": "Authorization required. Restart using scripts/caseops-web."}), 403
    if not GIT_SYNC_LOCK.acquire(blocking=False):
        return jsonify({"error": "Another Git operation is running."}), 409
    try:
        git_review_snapshot()  # Validate origin before network access.
        git_exec("fetch", "--quiet", "origin", "main", timeout=40)
        return jsonify(git_review_snapshot())
    except GitSyncFailure as exc:
        return jsonify({"error": str(exc)}), 503
    finally:
        GIT_SYNC_LOCK.release()


@app.route("/api/git/update", methods=["POST"])
@auth.login_required
def git_update_api():
    if not git_request_authorized():
        return jsonify({"error": "Authorization required. Restart using scripts/caseops-web."}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request."}), 400
    if not GIT_SYNC_LOCK.acquire(blocking=False):
        return jsonify({"error": "Another Git operation is running."}), 409
    try:
        state = git_review_snapshot()
        if not state["can_update"]:
            return jsonify({"error": "Cannot update: check branch, local changes and GitHub history."}), 409
        if data.get("head") != state["head"] or data.get("remote") != state["remote"]:
            return jsonify({"error": "GitHub changed. Check status again before updating."}), 409
        git_exec("merge", "--ff-only", "refs/remotes/origin/main", timeout=40)
        return jsonify({
            "status": "updated", "head": git_exec("rev-parse", "HEAD"),
            "message": "Fast-forward completed. Restart the CaseOps web server to load new code.",
            "restart_required": True,
        })
    except GitSyncFailure as exc:
        return jsonify({"error": str(exc)}), 503
    finally:
        GIT_SYNC_LOCK.release()

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
