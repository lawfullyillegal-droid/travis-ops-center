#!/usr/bin/env python3
"""Validate and review a local CASEOPS timeline without fetching source links."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ("date", "docket_scope", "event", "source_status", "source_url")
SCOPES = {"civil", "criminal", "system"}


def read_timeline(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    if reader.fieldnames != list(FIELDS):
        raise ValueError("CSV header must be: " + ",".join(FIELDS))
    rows = []
    for row in reader:
        line = reader.line_num
        if None in row or any(row.get(key) is None for key in FIELDS):
            raise ValueError(f"line {line}: expected exactly five columns")
        if any(not row[key].strip() for key in FIELDS[:-1]):
            raise ValueError(f"line {line}: required fields must not be blank")
        if any(any(ord(char) < 32 and char not in "\n\r\t" for char in value)
               for value in row.values()):
            raise ValueError(f"line {line}: unsupported control character")
        try:
            parsed = date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValueError(f"line {line}: invalid date") from exc
        if parsed.isoformat() != row["date"]:
            raise ValueError(f"line {line}: date must use YYYY-MM-DD")
        if row["docket_scope"] not in SCOPES:
            raise ValueError(f"line {line}: scope must be civil, criminal, or system")
        source_url = row["source_url"].strip()
        if source_url:
            try:
                url = urlsplit(source_url)
                valid_url = (url.scheme == "https" and bool(url.hostname)
                             and url.username is None and url.password is None
                             and not any(char.isspace() for char in source_url))
                url.port
            except ValueError:
                valid_url = False
            if not valid_url:
                raise ValueError(f"line {line}: source_url must be an HTTPS URL without credentials")
        row["source_url"] = source_url
        rows.append(row)
    if not rows:
        raise ValueError("timeline must contain at least one event")
    return sorted(rows, key=lambda row: row["date"]), hashlib.sha256(raw).hexdigest()


def render(rows: list[dict[str, str]], digest: str, include_links: bool = False) -> str:
    counts = Counter(row["docket_scope"] for row in rows)
    lines = ["CASEOPS // TIMELINE", f"Events: {len(rows)} | " + " | ".join(
        f"{scope}: {counts[scope]}" for scope in sorted(SCOPES)),
        f"Range: {rows[0]['date']} to {rows[-1]['date']}", f"CSV SHA-256: {digest}",
        "Source statuses are supplied descriptions; source contents have not been verified.", ""]
    for row in rows:
        # JSON quoting prevents terminal escapes and makes embedded newlines explicit.
        lines.append(f"{row['date']} [{row['docket_scope']}] " + json.dumps(row["event"], ensure_ascii=False))
        lines.append("  Status: " + json.dumps(row["source_status"], ensure_ascii=False))
        if include_links:
            lines.append("  Source: " + json.dumps(row["source_url"], ensure_ascii=False))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--scope", choices=sorted(SCOPES), help="show only one docket scope")
    parser.add_argument("--include-links", action="store_true", help="include private source URLs in output")
    parser.add_argument("--check", action="store_true", help="validate without printing case details")
    args = parser.parse_args(argv)
    try:
        rows, digest = read_timeline(args.csv.expanduser())
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.check:
        print(f"PASS: {len(rows)} events; CSV SHA-256: {digest}")
        return 0
    if args.scope:
        rows = [row for row in rows if row["docket_scope"] == args.scope]
    if not rows:
        print(f"No events for scope: {args.scope}")
        return 0
    print(render(rows, digest, args.include_links), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
