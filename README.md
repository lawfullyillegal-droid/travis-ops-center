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

## Deployment

### Docker (recommended for servers/always-on)

**Local development:**
```bash
docker-compose up --build
# open http://localhost:8080
```

**On a server (Linux/VPS):**
```bash
git clone https://github.com/lawfullyillegal-droid/travis-ops-center.git
cd travis-ops-center
docker-compose up -d
# access via http://<server-ip>:8080
```

**With reverse proxy (nginx) for HTTPS:**
```nginx
server {
  listen 443 ssl http2;
  server_name your-domain.com;
  ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

### Manual deployment (no Docker):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 web/app.py
```

## Authentication & Security

**IMPORTANT:** The web UI has NO authentication by default. Before exposing it publicly:

1. **Use a firewall** — only allow trusted IPs
2. **Run behind a reverse proxy** — use nginx/Apache with authentication
3. **Add HTTP Basic Auth** (optional enhancement):
   ```bash
   pip install Flask-HTTPAuth
   # Then edit web/app.py to add @auth.login_required decorators
   ```
4. **Use VPN or SSH tunneling** — don't expose directly to the internet

**Recommend:** Keep it on an internal network or access via VPN only.
