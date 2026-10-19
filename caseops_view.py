#!/usr/bin/env python3
"""Local, read-only CaseOps file and source browser for Termux."""
from __future__ import annotations

import csv
import hashlib
import html
import mimetypes
import os
import shutil
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HOME = Path.home()
CASE = Path(os.getenv("CASEOPS_CASE_ROOT", HOME / "SecurityLab/Cases/Kingman")).expanduser()
REPO = Path(os.getenv("CASEOPS_REPO_ROOT", HOME / "caseops")).expanduser()
DOWNLOAD = Path(os.getenv("CASEOPS_DOWNLOAD_ROOT", HOME / "storage/shared/Download")).expanduser()
PORT = int(os.getenv("CASEOPS_VIEW_PORT", "8766"))
DISCOVERY = ("Conduent_discovery_output", "CaseOps_Mohave_Conduent_output", "CaseRecords_discovery_output")
EXTENSIONS = {".pdf", ".txt", ".md", ".csv", ".json", ".html", ".docx", ".png", ".jpg", ".jpeg", ".log", ".xml"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def file_id(path: Path) -> str:
    return hashlib.sha256(str(path).encode()).hexdigest()[:20]


def inventory() -> dict[str, tuple[str, Path]]:
    found: dict[str, tuple[str, Path]] = {}
    roots = [("Kingman", CASE), ("CaseOps evidence", REPO / "evidence")]
    roots += [(name, DOWNLOAD / name) for name in DISCOVERY]
    for label, root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if any(part in SKIP for part in path.parts) or path.is_symlink() or not path.is_file():
                continue
            if path.suffix.lower() not in EXTENSIONS:
                continue
            found[file_id(path)] = (label, path)
            if len(found) >= 3000:
                return found
    if DOWNLOAD.is_dir():
        for path in DOWNLOAD.iterdir():
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in EXTENSIONS:
                found[file_id(path)] = ("Downloads", path)
    return found


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for folder in DISCOVERY:
        for filename in ("normalized_cross_reference.csv", "name_mentions.csv"):
            path = DOWNLOAD / folder / filename
            if not path.is_file():
                continue
            try:
                with path.open(encoding="utf-8-sig", newline="") as handle:
                    for row in csv.DictReader(handle):
                        row["_dataset"] = folder
                        rows.append(row)
                        if len(rows) >= 5000:
                            return rows
            except (OSError, UnicodeError, csv.Error) as exc:
                rows.append({"official_name": f"Could not read {filename}: {exc}", "_dataset": folder})
    return rows


def safe_url(value: str) -> str:
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
            return value.strip()
    except ValueError:
        pass
    return ""


STYLE = """
<style>
:root{color-scheme:dark}body{margin:0;background:#08111d;color:#e8f2fa;font:15px system-ui,sans-serif}
header{background:#11243a;padding:18px 4vw;position:sticky;top:0;z-index:2;border-bottom:1px solid #31516e}
h1{margin:0 0 8px;font-size:1.5rem}h2{margin:0 0 12px}p{line-height:1.5}
input{box-sizing:border-box;width:100%;padding:12px;background:#07111e;color:white;border:1px solid #57718a;border-radius:8px;font-size:1rem}
main{padding:18px 4vw;max-width:1400px;margin:auto}.cards{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}
.card,.panel{background:#102238;border:1px solid #2c4965;border-radius:10px;padding:14px}
.card{min-width:140px}.card strong{display:block;font-size:1.5rem;color:#78dcff}.panel{margin:18px 0;overflow:auto}
table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:10px;border-bottom:1px solid #2b435b;vertical-align:top}
th{color:#8ebbd2}a{color:#7edbff;overflow-wrap:anywhere}small,.muted{color:#a8b9c8}
.tag{display:inline-block;background:#18374b;border-radius:5px;padding:2px 7px;white-space:nowrap}
tr[hidden]{display:none}code{overflow-wrap:anywhere}button{background:#1a5873;color:white;border:0;padding:9px 13px;border-radius:7px}
</style>
"""


def page(title: str, body: str, script: str = "") -> bytes:
    return (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title>{STYLE}</head><body>{body}{script}</body></html>').encode("utf-8")


def home_page() -> bytes:
    files = inventory()
    rows = source_rows()
    basename_map: dict[str, list[str]] = {}
    for ident, (_, path) in files.items():
        basename_map.setdefault(path.name.casefold(), []).append(ident)

    file_html = []
    for ident, (label, path) in sorted(files.items(), key=lambda item: (item[1][0], item[1][1].name.casefold())):
        try:
            size = f"{path.stat().st_size:,}"
        except OSError:
            size = "?"
        file_html.append(f'<tr class="searchable"><td><a href="/detail?id={ident}">{esc(path.name)}</a></td>'
                         f'<td><span class="tag">{esc(label)}</span></td><td>{size}</td></tr>')

    source_html = []
    for row in rows:
        name = row.get("normalized_name") or row.get("official_name") or "Unnamed"
        relation = row.get("documented_relationship") or row.get("record_kind") or "mention"
        target = row.get("parent_entity") or row.get("organization") or "—"
        filing = row.get("source_filing") or row.get("source_accession") or "—"
        source_file = Path(row.get("source_file") or "").name
        matches = basename_map.get(source_file.casefold(), []) if source_file else []
        local = f'<a href="/detail?id={matches[0]}">{esc(source_file)}</a>' if len(matches) == 1 else esc(source_file or "—")
        url = safe_url(row.get("source_url") or "")
        online = f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">Open source</a>' if url else "No online link"
        source_html.append(f'<tr class="searchable"><td>{esc(name)}</td><td>{esc(relation)} &rarr; {esc(target)}</td>'
                           f'<td>{esc(filing)}</td><td>{local}<br>{online}</td><td>{esc(row.get("_dataset"))}</td></tr>')

    missing = [str(root) for root in (CASE, REPO / "evidence", *(DOWNLOAD / name for name in DISCOVERY)) if not root.is_dir()]
    missing_html = (f'<p class="muted">Not found yet: {esc("; ".join(missing))}</p>' if missing else "")
    body = (f'<header><h1>CASEOPS // LOCAL SOURCE VIEW</h1><input id="search" type="search" '
            f'placeholder="Search names, relationships, filings, and files" autofocus></header><main>'
            f'<div class="cards"><div class="card"><strong>{len(files)}</strong>local files</div>'
            f'<div class="card"><strong>{len(rows)}</strong>discovery rows</div>'
            f'<div class="card"><strong>Local</strong>127.0.0.1:{PORT}</div></div>'
            f'<p class="muted">Rows are leads from your CSVs. A name match alone does not prove a relationship. '
            f'Only files in the listed local folders appear here.</p>{missing_html}'
            f'<section class="panel"><h2>Names and source paths</h2><table><thead><tr><th>Name</th><th>Recorded link</th>'
            f'<th>Filing</th><th>Source</th><th>Dataset</th></tr></thead><tbody>{"".join(source_html) or "<tr><td colspan=5>No discovery CSV rows found.</td></tr>"}</tbody></table></section>'
            f'<section class="panel"><h2>Local file inventory</h2><table><thead><tr><th>File</th><th>Folder</th><th>Bytes</th>'
            f'</tr></thead><tbody>{"".join(file_html) or "<tr><td colspan=3>No local files found.</td></tr>"}</tbody></table></section></main>')
    script = """<script>document.getElementById('search').addEventListener('input',e=>{
      const q=e.target.value.toLocaleLowerCase();document.querySelectorAll('tr.searchable').forEach(r=>{
        r.hidden=!r.textContent.toLocaleLowerCase().includes(q);
      });});</script>"""
    return page("CaseOps local sources", body, script)


def file_detail(ident: str) -> bytes | None:
    item = inventory().get(ident)
    if not item:
        return None
    label, path = item
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        size = path.stat().st_size
    except OSError:
        return None
    related = [row for row in source_rows() if Path(row.get("source_file") or "").name.casefold() == path.name.casefold()]
    snippets = []
    for row in related[:40]:
        snippets.append(f'<li>{esc(row.get("normalized_name") or row.get("official_name"))} — '
                        f'{esc(row.get("source_filing") or row.get("record_kind") or "mention")}</li>')
    body = (f'<header><h1>{esc(path.name)}</h1><a href="/">Back to source view</a></header><main>'
            f'<section class="panel"><p>Folder: {esc(label)}</p><p>Local path: <code>{esc(path)}</code></p>'
            f'<p>Size: {size:,} bytes</p><p>SHA-256: <code>{digest.hexdigest()}</code></p>'
            f'<p><a href="/file?id={ident}">Open file on this phone</a></p></section>'
            f'<section class="panel"><h2>CSV references to this filename ({len(related)})</h2>'
            f'<ul>{"".join(snippets) or "<li>No matching CSV source filename.</li>"}</ul></section></main>')
    return page(path.name, body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        host = self.headers.get("Host", "")
        if host not in {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}:
            self.send_error(403)
            return
        request = urlsplit(self.path)
        ident = parse_qs(request.query).get("id", [""])[0]
        if request.path == "/":
            data = home_page()
            kind = "text/html; charset=utf-8"
        elif request.path == "/detail":
            data = file_detail(ident)
            kind = "text/html; charset=utf-8"
        elif request.path == "/file":
            item = inventory().get(ident)
            if not item:
                self.send_error(404)
                return
            path = item[1]
            try:
                handle = path.open("rb")
                size = path.stat().st_size
            except OSError:
                self.send_error(404)
                return
            kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if kind in {"text/html", "image/svg+xml", "application/xml", "text/xml"}:
                kind = "text/plain; charset=utf-8"
            with handle:
                self.send_response(200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.end_headers()
                try:
                    shutil.copyfileobj(handle, self.wfile, 1024 * 1024)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            return
        else:
            self.send_error(404)
            return
        if data is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"CaseOps local source view: http://127.0.0.1:{PORT}/")
    print("Keep this Termux session open. Press Ctrl+C to stop. No files are uploaded.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
