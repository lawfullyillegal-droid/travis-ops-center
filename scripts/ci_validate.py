#!/usr/bin/env python3
"""CI validator: scans commands and scripts for blacklisted patterns.

Exits with code 1 if any disallowed pattern is found.
"""
import sys
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
BLACKLIST_FILE = ROOT / "config" / "blacklist.txt"

DEFAULT_BLACKLIST = [
    r"\brm\s+-rf\b",
    r"\bsudo\b",
    r"\bdd\b",
    r"\bmkfs\b",
    r":\|\s*sh\b",
    r"curl\s+.*\|\s*sh",
    r"\bchmod\s+777\b",
    r"\bshutdown\b",
    r"\breboot\b",
]

def load_blacklist():
    patterns = DEFAULT_BLACKLIST.copy()
    if BLACKLIST_FILE.exists():
        for line in BLACKLIST_FILE.read_text(encoding='utf-8').splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            patterns.append(s)
    return [re.compile(p, re.IGNORECASE) for p in patterns]

def scan_text(text, patterns):
    matches = []
    for p in patterns:
        if p.search(text):
            matches.append(p.pattern)
    return matches

def scan_commands(patterns):
    cfg = ROOT / 'config' / 'commands.yml'
    if not cfg.exists():
        return []
    data = yaml.safe_load(cfg.read_text(encoding='utf-8')) or {}
    out = []
    for cmd in data.get('commands', []):
        text = cmd.get('cmd','')
        m = scan_text(text, patterns)
        if m:
            out.append((str(cfg), cmd.get('id','<no-id>'), text, m))
    return out

def scan_scripts(patterns):
    out = []
    for p in ROOT.rglob('*.sh'):
        try:
            txt = p.read_text(encoding='utf-8')
        except Exception:
            continue
        m = scan_text(txt, patterns)
        if m:
            out.append((str(p), m))
    return out

def main():
    patterns = load_blacklist()
    bad = []
    bad += scan_commands(patterns)
    bad_scripts = scan_scripts(patterns)
    if bad_scripts:
        for s,m in bad_scripts:
            print(f"Blacklisted pattern in script {s}: {m}")
    if bad:
        for cfg, cid, text, m in bad:
            print(f"Blacklisted pattern in {cfg} (command id={cid}): {m} -> {text}")
    if bad or bad_scripts:
        print("Validation failed: remove or whitelist the offending commands to proceed.")
        return 1
    print("Validation passed: no blacklisted patterns found.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
