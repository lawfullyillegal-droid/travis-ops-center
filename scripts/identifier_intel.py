#!/usr/bin/env python3
"""CaseOps Identifier Intelligence.

Purpose
-------
Trace identifiers and legal entities through public/authorized data sources while
preserving provenance and separating VERIFIED links from candidate matches.

Public sources implemented:
* GLEIF LEI API (LEI/entity/ISIN mapping)
* SEC EDGAR data APIs (CIK submissions, company ticker index)

DTCC integration is intentionally authorization-gated. The module will not guess,
scrape around access controls, or treat a numerical collision as a market link.
Configure CASEOPS_DTCC_API_URL and CASEOPS_DTCC_BEARER_TOKEN only for an API you
are authorized to use.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data" / "identifier_intel"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "identifier_intel.db"

GLEIF_BASE = "https://api.gleif.org/api/v1"
SEC_DATA_BASE = "https://data.sec.gov"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

LEI_RE = re.compile(r"^[A-Z0-9]{20}$")
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
CUSIP_RE = re.compile(r"^[A-Z0-9*@#]{9}$")
BIC_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?$")
CIK_RE = re.compile(r"^(?:CIK[-:\s]*)?([0-9]{1,10})$", re.I)
CASEISH_RE = re.compile(r"^(?=.*\d)[A-Z0-9][A-Z0-9._/-]{5,}$", re.I)


@dataclass
class Classification:
    input: str
    normalized: str
    kinds: list[str]
    notes: list[str]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_identifier(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().upper())


def _luhn_ok(number: str) -> bool:
    digits = [int(c) for c in number]
    total = 0
    parity = len(digits) % 2
    for i, digit in enumerate(digits):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def isin_check(value: str) -> bool:
    if not ISIN_RE.fullmatch(value):
        return False
    expanded = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in value)
    return _luhn_ok(expanded)


def _cusip_value(ch: str) -> int:
    if ch.isdigit():
        return int(ch)
    if ch.isalpha():
        return ord(ch) - 55
    return {"*": 36, "@": 37, "#": 38}[ch]


def cusip_check(value: str) -> bool:
    if not CUSIP_RE.fullmatch(value):
        return False
    total = 0
    for idx, ch in enumerate(value[:8]):
        v = _cusip_value(ch)
        if idx % 2 == 1:
            v *= 2
        total += (v // 10) + (v % 10)
    return ((10 - (total % 10)) % 10) == int(value[-1]) if value[-1].isdigit() else False


def classify(value: str) -> Classification:
    raw = value.strip().upper()
    n = normalize_identifier(value)
    kinds: list[str] = []
    notes: list[str] = []
    if LEI_RE.fullmatch(n):
        kinds.append("LEI")
    if ISIN_RE.fullmatch(n):
        if isin_check(n):
            kinds.append("ISIN")
        else:
            notes.append("ISIN-shaped but check digit failed")
    if CUSIP_RE.fullmatch(n):
        if cusip_check(n):
            kinds.append("CUSIP")
        elif len(n) == 9:
            notes.append("CUSIP-shaped but check digit failed")
    if BIC_RE.fullmatch(n):
        kinds.append("BIC")
    m = CIK_RE.fullmatch(n)
    if m:
        explicit_cik = bool(re.match(r"^CIK[-:\s]*", raw, re.I))
        zero_padded_cik = n.isdigit() and len(n) == 10 and n.startswith("0")
        if explicit_cik or zero_padded_cik:
            kinds.append("CIK")
        elif n.isdigit():
            notes.append(
                "Bare numeric identifier is ambiguous; not treated as an SEC CIK without "
                "a CIK prefix or 10-digit zero-padded form"
            )
    if CASEISH_RE.fullmatch(n) and not kinds:
        kinds.append("LOCAL_OR_ADMIN_ID")
        notes.append("Structure alone does not establish a securities-market identifier")
    if not kinds:
        kinds.append("UNKNOWN")
    return Classification(value, n, kinds, notes)


class Store:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.init()

    def init(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS identifiers(
              id INTEGER PRIMARY KEY, normalized TEXT NOT NULL, kind TEXT NOT NULL,
              first_seen TEXT NOT NULL, UNIQUE(normalized, kind));
            CREATE TABLE IF NOT EXISTS entities(
              id INTEGER PRIMARY KEY, canonical_name TEXT NOT NULL, source TEXT,
              source_id TEXT, details_json TEXT, first_seen TEXT NOT NULL,
              UNIQUE(source, source_id));
            CREATE TABLE IF NOT EXISTS source_snapshots(
              id INTEGER PRIMARY KEY, source TEXT NOT NULL, query TEXT NOT NULL,
              fetched_at TEXT NOT NULL, url TEXT, sha256 TEXT NOT NULL,
              raw_path TEXT NOT NULL, http_status INTEGER, UNIQUE(source, sha256));
            CREATE TABLE IF NOT EXISTS links(
              id INTEGER PRIMARY KEY, from_type TEXT NOT NULL, from_value TEXT NOT NULL,
              relation TEXT NOT NULL, to_type TEXT NOT NULL, to_value TEXT NOT NULL,
              status TEXT NOT NULL, confidence REAL NOT NULL, source_snapshot_id INTEGER,
              evidence_ref TEXT, amount REAL, currency TEXT, event_date TEXT, notes TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(source_snapshot_id) REFERENCES source_snapshots(id));
            CREATE TABLE IF NOT EXISTS anomalies(
              id INTEGER PRIMARY KEY, category TEXT NOT NULL, severity TEXT NOT NULL,
              subject TEXT NOT NULL, description TEXT NOT NULL, evidence_json TEXT,
              created_at TEXT NOT NULL);
            """
        )
        self.conn.commit()

    def add_identifier(self, normalized: str, kind: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO identifiers(normalized,kind,first_seen) VALUES(?,?,?)",
            (normalized, kind, now_iso()),
        )
        self.conn.commit()

    def snapshot(self, source: str, query: str, url: str, body: bytes, status: int) -> int:
        digest = sha256_bytes(body)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "_", source)
        path = RAW_DIR / f"{stamp}_{safe_source}_{digest[:12]}.json"
        if not path.exists():
            path.write_bytes(body)
        self.conn.execute(
            """INSERT OR IGNORE INTO source_snapshots
            (source,query,fetched_at,url,sha256,raw_path,http_status)
            VALUES(?,?,?,?,?,?,?)""",
            (source, query, now_iso(), url, digest, str(path.relative_to(REPO_ROOT)), status),
        )
        row = self.conn.execute(
            "SELECT id FROM source_snapshots WHERE source=? AND sha256=?", (source, digest)
        ).fetchone()
        self.conn.commit()
        return int(row["id"])

    def add_link(self, *, from_type: str, from_value: str, relation: str,
                 to_type: str, to_value: str, status: str = "VERIFIED",
                 confidence: float = 1.0, snapshot_id: int | None = None,
                 evidence_ref: str | None = None, amount: float | None = None,
                 currency: str | None = None, event_date: str | None = None,
                 notes: str | None = None) -> None:
        self.conn.execute(
            """INSERT INTO links(from_type,from_value,relation,to_type,to_value,status,
            confidence,source_snapshot_id,evidence_ref,amount,currency,event_date,notes,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (from_type, from_value, relation, to_type, to_value, status, confidence,
             snapshot_id, evidence_ref, amount, currency, event_date, notes, now_iso()),
        )
        self.conn.commit()

    def add_anomaly(self, category: str, severity: str, subject: str,
                    description: str, evidence: Any) -> None:
        self.conn.execute(
            "INSERT INTO anomalies(category,severity,subject,description,evidence_json,created_at) VALUES(?,?,?,?,?,?)",
            (category, severity, subject, description, json.dumps(evidence, ensure_ascii=False), now_iso()),
        )
        self.conn.commit()


class HTTP:
    def __init__(self, store: Store):
        self.store = store
        self.last_sec_request = 0.0

    def get_json(self, source: str, url: str, query: str, headers: dict[str, str] | None = None,
                 sec: bool = False) -> tuple[Any, int]:
        headers = dict(headers or {})
        headers.setdefault("Accept", "application/json")
        headers.setdefault("Accept-Encoding", "identity")
        if sec:
            ua = os.environ.get("CASEOPS_SEC_USER_AGENT", "").strip()
            if not ua:
                raise RuntimeError(
                    "SEC access requires CASEOPS_SEC_USER_AGENT, e.g. 'YourName your-email@example.com'."
                )
            headers["User-Agent"] = ua
            # Stay comfortably below SEC's published ceiling.
            gap = time.monotonic() - self.last_sec_request
            if gap < 0.12:
                time.sleep(0.12 - gap)
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                status = r.status
        except urllib.error.HTTPError as e:
            body = e.read()
            status = e.code
            self.store.snapshot(source, query, url, body, status)
            raise RuntimeError(f"{source} HTTP {status}: {body[:300]!r}") from e
        if sec:
            self.last_sec_request = time.monotonic()
        snapshot_id = self.store.snapshot(source, query, url, body, status)
        return json.loads(body.decode("utf-8")), snapshot_id


class Gleif:
    def __init__(self, http: HTTP):
        self.http = http

    def lei(self, lei: str) -> tuple[dict[str, Any], int]:
        url = f"{GLEIF_BASE}/lei-records/{urllib.parse.quote(lei)}"
        return self.http.get_json("GLEIF", url, lei, {"Accept": "application/vnd.api+json"})

    def search_name(self, name: str, size: int = 10) -> tuple[dict[str, Any], int]:
        q = urllib.parse.urlencode({"page[size]": min(size, 50), "filter[entity.names]": name})
        url = f"{GLEIF_BASE}/lei-records?{q}"
        return self.http.get_json("GLEIF", url, name, {"Accept": "application/vnd.api+json"})

    def fuzzy(self, name: str) -> tuple[dict[str, Any], int]:
        q = urllib.parse.urlencode({"field": "entity.legalName", "q": name})
        url = f"{GLEIF_BASE}/fuzzycompletions?{q}"
        return self.http.get_json("GLEIF", url, name, {"Accept": "application/vnd.api+json"})

    def by_isin(self, isin: str, size: int = 10) -> tuple[dict[str, Any], int]:
        q = urllib.parse.urlencode({"page[size]": min(size, 50), "filter[isin]": isin})
        url = f"{GLEIF_BASE}/lei-records?{q}"
        return self.http.get_json("GLEIF", url, isin, {"Accept": "application/vnd.api+json"})

    def lei_isins(self, lei: str) -> tuple[dict[str, Any], int]:
        url = f"{GLEIF_BASE}/lei-records/{urllib.parse.quote(lei)}/isins"
        return self.http.get_json("GLEIF", url, f"{lei}/isins", {"Accept": "application/vnd.api+json"})


class Sec:
    def __init__(self, http: HTTP):
        self.http = http

    @staticmethod
    def pad_cik(cik: str) -> str:
        m = CIK_RE.fullmatch(cik.strip())
        if not m:
            raise ValueError("Not a CIK")
        return m.group(1).zfill(10)

    def submissions(self, cik: str) -> tuple[dict[str, Any], int]:
        padded = self.pad_cik(cik)
        url = f"{SEC_DATA_BASE}/submissions/CIK{padded}.json"
        return self.http.get_json("SEC_SUBMISSIONS", url, padded, sec=True)

    def company_tickers(self) -> tuple[dict[str, Any], int]:
        return self.http.get_json("SEC_TICKERS", SEC_TICKERS_URL, "company_tickers", sec=True)


def legal_name_from_gleif(record: dict[str, Any]) -> str | None:
    try:
        return record["attributes"]["entity"]["legalName"]["name"]
    except (KeyError, TypeError):
        return None


def glean_lei_record(record: dict[str, Any]) -> dict[str, Any]:
    attrs = record.get("attributes", {})
    entity = attrs.get("entity", {})
    reg = attrs.get("registration", {})
    return {
        "lei": attrs.get("lei") or record.get("id"),
        "legal_name": (entity.get("legalName") or {}).get("name"),
        "status": entity.get("status"),
        "jurisdiction": entity.get("jurisdiction"),
        "legal_address": entity.get("legalAddress"),
        "registration_status": reg.get("status"),
        "initial_registration_date": reg.get("initialRegistrationDate"),
        "last_update_date": reg.get("lastUpdateDate"),
        "next_renewal_date": reg.get("nextRenewalDate"),
    }


def trace_identifier(value: str, store: Store) -> dict[str, Any]:
    c = classify(value)
    for kind in c.kinds:
        store.add_identifier(c.normalized, kind)
    http = HTTP(store)
    gleif, sec = Gleif(http), Sec(http)
    out: dict[str, Any] = {"classification": asdict(c), "results": {}, "warnings": []}

    try:
        if "LEI" in c.kinds:
            data, sid = gleif.lei(c.normalized)
            rec = data.get("data") or {}
            summary = glean_lei_record(rec)
            out["results"]["gleif"] = summary
            if summary.get("legal_name"):
                store.add_link(from_type="LEI", from_value=c.normalized,
                               relation="identifies_legal_entity", to_type="ENTITY",
                               to_value=summary["legal_name"], snapshot_id=sid)
            try:
                isin_data, isin_sid = gleif.lei_isins(c.normalized)
                isins = [x.get("attributes", {}).get("isin") or x.get("id") for x in isin_data.get("data", [])]
                isins = [x for x in isins if x]
                out["results"]["gleif_isins"] = isins
                for isin in isins:
                    store.add_link(from_type="LEI", from_value=c.normalized, relation="mapped_to",
                                   to_type="ISIN", to_value=isin, snapshot_id=isin_sid)
            except Exception as e:
                out["warnings"].append(f"GLEIF ISIN mapping: {e}")

        if "ISIN" in c.kinds:
            data, sid = gleif.by_isin(c.normalized)
            matches = [glean_lei_record(x) for x in data.get("data", [])]
            out["results"]["gleif_isin_matches"] = matches
            for rec in matches:
                if rec.get("lei"):
                    store.add_link(from_type="ISIN", from_value=c.normalized, relation="mapped_to",
                                   to_type="LEI", to_value=rec["lei"], snapshot_id=sid)

        if "CIK" in c.kinds:
            data, sid = sec.submissions(c.normalized)
            summary = {
                "cik": str(data.get("cik", "")).zfill(10),
                "name": data.get("name"), "tickers": data.get("tickers", []),
                "exchanges": data.get("exchanges", []), "former_names": data.get("formerNames", []),
                "sic": data.get("sic"), "sic_description": data.get("sicDescription"),
            }
            out["results"]["sec"] = summary
            if summary.get("name"):
                store.add_link(from_type="CIK", from_value=summary["cik"], relation="identifies_sec_filer",
                               to_type="ENTITY", to_value=summary["name"], snapshot_id=sid)

        if "CUSIP" in c.kinds:
            out["warnings"].append(
                "CUSIP format validated locally. No unauthenticated CUSIP master lookup is assumed; "
                "add an authorized source before asserting issuer/security ownership."
            )
        if "LOCAL_OR_ADMIN_ID" in c.kinds or "UNKNOWN" in c.kinds:
            out["warnings"].append(
                "No market-database query was run solely from this identifier. A numeric/string collision is not a verified link."
            )
    except Exception as e:
        out["warnings"].append(str(e))
    return out


GENERIC_ENTITY_TOKENS = {
    "INC", "INCORPORATED", "LLC", "LTD", "LIMITED", "CORP", "CORPORATION",
    "CO", "COMPANY", "GROUP", "HOLDING", "HOLDINGS", "SERVICES", "SERVICE",
    "INVESTMENT", "INVESTMENTS", "FUND", "TRUST", "THE", "OF", "AND"
}

def entity_tokens(value: str) -> list[str]:
    return re.findall(r"[A-Z0-9]+", value.upper())

def entity_anchor(value: str) -> str | None:
    tokens = [t for t in entity_tokens(value) if t not in GENERIC_ENTITY_TOKENS and len(t) >= 4]
    return tokens[0] if tokens else None

def token_score(a: str, b: str) -> float:
    a_n = re.sub(r"[^A-Z0-9]+", " ", a.upper()).strip()
    b_n = re.sub(r"[^A-Z0-9]+", " ", b.upper()).strip()
    return round(difflib.SequenceMatcher(None, a_n, b_n).ratio(), 4)


def trace_entity(name: str, store: Store, limit: int = 10) -> dict[str, Any]:
    http = HTTP(store)
    gleif, sec = Gleif(http), Sec(http)
    out: dict[str, Any] = {"query": name, "gleif": [], "gleif_fuzzy": [], "sec": [], "warnings": []}

    try:
        data, sid = gleif.search_name(name, limit)
        anchor = entity_anchor(name)
        for rec in data.get("data", []):
            summary = glean_lei_record(rec)
            legal_name = summary.get("legal_name") or ""
            if anchor and anchor not in entity_tokens(legal_name):
                continue
            summary["name_score"] = token_score(name, legal_name)
            out["gleif"].append(summary)
            if len(out["gleif"]) >= limit:
                break
            if summary.get("lei") and summary.get("legal_name"):
                store.add_link(from_type="QUERY", from_value=name, relation="candidate_entity_match",
                               to_type="LEI", to_value=summary["lei"], status="CANDIDATE",
                               confidence=summary["name_score"], snapshot_id=sid,
                               notes=summary["legal_name"])
    except Exception as e:
        out["warnings"].append(f"GLEIF name search: {e}")

    try:
        data, _ = gleif.fuzzy(name)
        for item in data.get("data", [])[:limit]:
            out["gleif_fuzzy"].append({"value": item.get("attributes", {}).get("value")})
    except Exception as e:
        out["warnings"].append(f"GLEIF fuzzy: {e}")

    try:
        data, sid = sec.company_tickers()
        candidates = []
        anchor = entity_anchor(name)
        for item in data.values() if isinstance(data, dict) else []:
            title = item.get("title") or ""
            if anchor and anchor not in entity_tokens(title):
                continue
            score = token_score(name, title)
            if score >= 0.45:
                candidates.append((score, item))
        candidates.sort(key=lambda x: x[0], reverse=True)
        for score, item in candidates[:limit]:
            row = {"cik": str(item.get("cik_str", "")).zfill(10), "name": item.get("title"),
                   "ticker": item.get("ticker"), "name_score": score}
            out["sec"].append(row)
            store.add_link(from_type="QUERY", from_value=name, relation="candidate_sec_match",
                           to_type="CIK", to_value=row["cik"], status="CANDIDATE",
                           confidence=score, snapshot_id=sid, notes=row["name"])
    except Exception as e:
        out["warnings"].append(f"SEC ticker index: {e}")

    return out


def dtcc_authorized_lookup(identifier: str, store: Store) -> dict[str, Any]:
    base = os.environ.get("CASEOPS_DTCC_API_URL", "").strip()
    token = os.environ.get("CASEOPS_DTCC_BEARER_TOKEN", "").strip()
    if not base or not token:
        return {
            "status": "NOT_CONFIGURED",
            "message": "DTCC query skipped. Configure an authorized API URL/token; no access-control bypass is attempted."
        }
    # The exact endpoint contract is product-specific. User supplies a URL template with {id}.
    if "{id}" not in base:
        return {"status": "CONFIG_ERROR", "message": "CASEOPS_DTCC_API_URL must contain {id}."}
    url = base.replace("{id}", urllib.parse.quote(identifier))
    http = HTTP(store)
    try:
        data, sid = http.get_json("DTCC_AUTHORIZED", url, identifier,
                                  {"Authorization": f"Bearer {token}"})
        return {"status": "OK", "snapshot_id": sid, "data": data}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def add_money_edge(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    status = args.status.upper()
    if status not in {"VERIFIED", "CANDIDATE", "UNPROVEN", "REJECTED"}:
        raise ValueError("status must be VERIFIED, CANDIDATE, UNPROVEN, or REJECTED")
    store.add_link(from_type=args.from_type, from_value=args.from_value,
                   relation=args.relation, to_type=args.to_type, to_value=args.to_value,
                   status=status, confidence=args.confidence, evidence_ref=args.evidence_ref,
                   amount=args.amount, currency=args.currency, event_date=args.date, notes=args.notes)
    return {"saved": True, "status": status}


def show_links(store: Store, subject: str | None = None) -> list[dict[str, Any]]:
    if subject:
        rows = store.conn.execute(
            "SELECT * FROM links WHERE from_value=? OR to_value=? ORDER BY id", (subject, subject)
        ).fetchall()
    else:
        rows = store.conn.execute("SELECT * FROM links ORDER BY id DESC LIMIT 200").fetchall()
    return [dict(r) for r in rows]


def anomaly_identifier_conflict(args: argparse.Namespace, store: Store) -> dict[str, Any]:
    description = (
        f"Two source records describe the same asserted event/object with differing identifiers: "
        f"{args.id_a} vs {args.id_b}. Difference requires source-level reconciliation."
    )
    evidence = {"id_a": args.id_a, "source_a": args.source_a,
                "id_b": args.id_b, "source_b": args.source_b}
    store.add_anomaly("IDENTIFIER_CONFLICT", args.severity.upper(), args.subject, description, evidence)
    return {"saved": True, "description": description, "evidence": evidence}


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="identifier_intel.py", description="CaseOps identifier/entity/money-flow tracer")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("classify", help="Classify/validate an identifier without network access")
    s.add_argument("value")

    s = sub.add_parser("trace-id", help="Trace a supported identifier through compatible sources")
    s.add_argument("value")
    s.add_argument("--dtcc", action="store_true", help="also call configured authorized DTCC API")

    s = sub.add_parser("trace-entity", help="Resolve a legal entity across GLEIF and SEC")
    s.add_argument("name")
    s.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("money-add", help="Add a documented money/beneficiary relationship")
    s.add_argument("--from-type", required=True); s.add_argument("--from-value", required=True)
    s.add_argument("--relation", required=True)
    s.add_argument("--to-type", required=True); s.add_argument("--to-value", required=True)
    s.add_argument("--amount", type=float); s.add_argument("--currency", default="USD")
    s.add_argument("--date"); s.add_argument("--evidence-ref")
    s.add_argument("--status", default="VERIFIED")
    s.add_argument("--confidence", type=float, default=1.0)
    s.add_argument("--notes")

    s = sub.add_parser("links", help="Show relationship/money-flow edges")
    s.add_argument("--subject")

    s = sub.add_parser("anomaly-id", help="Record a source-backed identifier discrepancy")
    s.add_argument("--subject", required=True); s.add_argument("--id-a", required=True)
    s.add_argument("--source-a", required=True); s.add_argument("--id-b", required=True)
    s.add_argument("--source-b", required=True); s.add_argument("--severity", default="HIGH")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    store = Store()
    try:
        if args.cmd == "classify":
            result = asdict(classify(args.value))
        elif args.cmd == "trace-id":
            result = trace_identifier(args.value, store)
            if args.dtcc:
                result["dtcc"] = dtcc_authorized_lookup(normalize_identifier(args.value), store)
        elif args.cmd == "trace-entity":
            result = trace_entity(args.name, store, max(1, min(args.limit, 50)))
        elif args.cmd == "money-add":
            result = add_money_edge(args, store)
        elif args.cmd == "links":
            result = show_links(store, args.subject)
        elif args.cmd == "anomaly-id":
            result = anomaly_identifier_conflict(args, store)
        else:
            raise AssertionError(args.cmd)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    finally:
        store.conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
