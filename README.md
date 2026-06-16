# travis-ops-center — Termux + Obsidian + GitHub command center scaffold

This repository contains templates to build a safe, git-backed Obsidian vault and a Termux-friendly interactive command center with auditing.

Quick start (on Termux):

1. Install dependencies:

```bash
cd ~/travis-ops-center
bash setup/termux-setup.sh
```

2. Copy the sample commands and edit allowed commands:

```bash
cp config/commands.sample.yml config/commands.yml
# edit config/commands.yml to include only safe commands you trust
```

3. Run the command center:

```bash
python3 scripts/command_center.py
```

4. Sync your vault to GitHub:

```bash
./scripts/sync_vault.sh "Device sync"
```

Obsidian integration:
- Use the Obsidian Git community plugin or point your vault to this repo.
- DO NOT enable automatic execution of untrusted scripts from notes.

Evidence workflow (basic):

1. Ingest an evidence file (copies file, records hash):

```bash
python3 scripts/evidence_ingest.py /path/to/file --notes "describe evidence"
```

2. Generate an Obsidian note for the evidence:

```bash
python3 scripts/gen_evidence_note.py evidence-YYYYMMDDT...-<hashprefix>
```

3. Run a script and capture its output as evidence:

```bash
./scripts/run_and_capture.sh scripts/my_script.py "capture run for case"
```


Security notes:
- This scaffold intentionally requires you to list allowed commands in `config/commands.yml` so you can avoid executing risky tools.
- The audit logs are written to `logs/audit.log` as JSONL.
