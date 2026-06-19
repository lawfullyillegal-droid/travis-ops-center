# travis-ops-center

> **Operator:** lawfullyillegal-droid | **Case:** Trust-identifier-trace #44 | **Status:** ACTIVE

![Python](https://img.shields.io/badge/python-3.10+-blue) ![Shell](https://img.shields.io/badge/shell-bash-green) ![SQLite](https://img.shields.io/badge/db-sqlite3-orange) ![License](https://img.shields.io/badge/license-private-red)

A self-contained OSINT and digital forensics **Operations Center** for capturing, hashing, and cataloguing evidence from command-line investigations. Runs fully inside GitHub Codespaces or on Termux (Android).

---

## Features

- **Command Center** (`scripts/command_center.py`) — curses-based TUI for executing pre-approved OSINT commands with audit logging
- **Evidence Ingestion** (`scripts/evidence_ingest.py`) — SHA-256 hashes, timestamps, and stores evidence files; writes records to SQLite ledger
- **Evidence Note Generator** (`scripts/gen_evidence_note.py`) — generates Markdown case notes from ledger entries
- **Audit Logger** (`scripts/audit_logger.py`) — append-only audit trail for every operator action
- **Site Builder** (`scripts/build_site.py`) — compiles the `frontend/` dashboard and serves it on port 8080
- **CI Validator** (`scripts/ci_validate.py`) — pre-commit checks on evidence integrity
- **Sync Vault** (`scripts/sync_vault.sh`) — syncs evidence vault to remote backup

## Project Structure

```
travis-ops-center/
├── config/
│   ├── commands.yml          # Allowed OSINT commands (edit this)
│   ├── commands.sample.yml   # Template for commands.yml
│   └── settings.yml          # Operator, case, DB path, log level
├── data/
│   ├── targets.json          # Investigation targets (IPs, domains, usernames)
│   ├── case_notes.md         # Running case notes and timeline
│   └── integrity_ledger.db   # SQLite evidence ledger
├── docs/
│   ├── ARCHITECTURE.md       # System design
│   └── OPERATIONS_MANUAL.md  # Full SOP
├── evidence/                 # Stored evidence files (auto-organized by date)
├── evidence_notes/           # Generated Markdown notes per evidence ID
├── frontend/                 # Ops dashboard (index.html + app.js + style.css)
├── logs/
│   └── audit.log             # Append-only audit trail
├── scripts/
│   ├── audit_logger.py
│   ├── build_site.py
│   ├── ci_validate.py
│   ├── command_center.py
│   ├── demo_capture.py
│   ├── evidence_ingest.py
│   ├── gen_evidence_note.py
│   ├── run_and_capture.sh
│   └── sync_vault.sh
├── COMMAND_VAULT.md          # Quick-reference command reference
├── deploy.sh                 # Deployment automation
├── docker-compose.yml        # Containerized deployment
└── requirements.txt          # Python dependencies
```

## Quick Start (Codespaces)

```bash
# 1. Configure allowed commands
cp config/commands.sample.yml config/commands.yml
vim config/commands.yml

# 2. Install Python deps
pip install -r requirements.txt

# 3. Launch command center TUI
python3 scripts/command_center.py

# 4. Ingest evidence manually
python3 scripts/evidence_ingest.py <path/to/file>

# 5. Generate note for evidence ID
python3 scripts/gen_evidence_note.py <evidence-id>

# 6. Build and serve dashboard
python3 scripts/build_site.py
```

## Quick Start (Termux)

```bash
bash setup/termux-setup.sh
cp config/commands.sample.yml config/commands.yml
python3 scripts/command_center.py
```

## Evidence Workflow

```
Run OSINT command
    → scripts/run_and_capture.sh captures output
    → scripts/evidence_ingest.py hashes + stores + ledgers
    → scripts/gen_evidence_note.py generates Markdown note
    → scripts/audit_logger.py writes audit entry
    → frontend dashboard updates automatically
```

## Populated by Comet AI — 2026-06-19

This system was fully populated on 2026-06-19 by Comet (Perplexity AI). The following were created:

| File | Status | Description |
|------|--------|-------------|
| config/commands.yml | ✅ | 20+ OSINT commands |
| config/settings.yml | ✅ | Operator config |
| data/targets.json | ✅ | 3 investigation targets |
| data/case_notes.md | ✅ | Case #44 timeline |
| docs/ARCHITECTURE.md | ✅ | System architecture |
| docs/OPERATIONS_MANUAL.md | ✅ | Full SOP |
| logs/audit.log | ✅ | 12 audit entries |
| evidence_notes/*.md | ✅ | 4 evidence notes |
| frontend/index.html | ✅ | Dark ops dashboard |

---

> **Security Notice:** Keep `config/commands.yml` minimal. Never add commands that could exfiltrate data or modify system state without operator confirmation.
