# Travis Ops Center

A Termux- and server-friendly control plane for **evidence hashing, audit logging, allow-listed command execution, and a local web dashboard**.

## Current role

`travis-ops-center` is the primary runtime hub. Related repositories are mapped in [`docs/REPOSITORY_MAP.md`](docs/REPOSITORY_MAP.md) so features can be consolidated without destroying history.

## Security model

- Local web bind defaults to `127.0.0.1`.
- Docker/server deployments require HTTP Basic Auth credentials.
- Raw evidence, databases, logs, `.env`, and private keys are ignored by default.
- Evidence files are hashed with SHA-256 at ingestion.
- Network/OSINT commands remain operator-confirmed and should be used only on authorized targets.

See [`SECURITY.md`](SECURITY.md).

## Components

- `scripts/evidence_ingest.py` — copy + SHA-256 + SQLite ledger
- `scripts/gen_evidence_note.py` — Markdown note generation
- `scripts/audit_logger.py` — append-only operator log
- `scripts/command_center.py` — curses UI over the reviewed command allow-list
- `web/app.py` — authenticated evidence dashboard/API
- `scripts/build_site.py` — optional static evidence-site generator
- `.github/workflows/validate-commands.yml` — CI validation and smoke tests

## Termux quick start

```bash
bash setup/termux-setup.sh
source .venv/bin/activate
# Review the existing config/commands.yml before running the command center.
python scripts/command_center.py
```

Run the local dashboard:

```bash
SERVER_HOST=127.0.0.1 python web/app.py
```

Open `http://127.0.0.1:8080`.

## CASEOPS timeline

Review local case timelines offline with separate civil, criminal, and system
scopes. Source statuses stay as supplied, and source links are hidden by default.

```bash
python scripts/caseops_timeline.py /path/to/timeline.csv --check
python scripts/caseops_timeline.py /path/to/timeline.csv --scope civil
```

See [the timeline workflow](docs/CASEOPS_TIMELINE.md) for the CSV schema,
privacy controls, and digest limitations.

## Docker/server deployment

```bash
cp .env.example .env
nano .env
# Set AUTH_USER and AUTH_PASS
bash deploy.sh
```

The host-side Docker bind defaults to `127.0.0.1:8080`. Use a VPN or authenticated TLS reverse proxy before exposing it beyond the machine.

## Evidence ingestion

```bash
python scripts/evidence_ingest.py /path/to/file --notes "description"
python scripts/gen_evidence_note.py <evidence-id>
```

Evidence and runtime databases are intentionally excluded from Git by default. Git should track code, reviewed configuration, manifests, and sanitized publication artifacts—not accidentally publish raw case material.

## Repository hygiene

If sensitive data was committed before these ignore rules existed, `.gitignore` does not remove it from history. Review Git history and repository visibility separately before treating the repository as private or sanitized.

