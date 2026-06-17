#!/usr/bin/env python3
import os, json, markdown, datetime

DOCS_DIR = "docs"
META_DIR = "meta_logs"
NOTES_DIR = "evidence_notes"

os.makedirs(DOCS_DIR, exist_ok=True)

def load_metadata():
    items = []
    if not os.path.exists(META_DIR):
        return items
    for f in os.listdir(META_DIR):
        if f.endswith(".json"):
            with open(os.path.join(META_DIR, f)) as fp:
                items.append(json.load(fp))
    return sorted(items, key=lambda x: x["ts"], reverse=True)

def load_note(evidence_id):
    md_path = os.path.join(NOTES_DIR, f"{evidence_id}.md")
    if not os.path.exists(md_path):
        return "<p>No note found.</p>"
    with open(md_path) as fp:
        return markdown.markdown(fp.read())

def write_index(items):
    html = "<h1>Evidence Ledger</h1><ul>"
    for item in items:
        html += f'<li><a href="{item["id"]}.html">{item["id"]}</a> — {item["ts"]}</li>'
    html += "</ul>"
    with open(os.path.join(DOCS_DIR, "index.html"), "w") as fp:
        fp.write(html)

def write_item_pages(items):
    for item in items:
        note_html = load_note(item["id"])
        html = f"""
        <h1>{item["id"]}</h1>
        <p><b>Timestamp:</b> {item["ts"]}</p>
        <p><b>Original File:</b> {item["original_path"]}</p>
        <p><b>Stored Path:</b> {item["stored_path"]}</p>
        <p><b>SHA256:</b> {item["sha256"]}</p>
        <p><b>Size:</b> {item["size"]} bytes</p>
        <h2>Notes</h2>
        {note_html}
        """
        with open(os.path.join(DOCS_DIR, f"{item['id']}.html"), "w") as fp:
            fp.write(html)

items = load_metadata()
write_index(items)
write_item_pages(items)

print("Site build complete.")
