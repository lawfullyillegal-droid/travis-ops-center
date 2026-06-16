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

## Go Live — Production Deployment

### Quick start (one command):

```bash
bash deploy.sh
```

This will:
1. Create a `.env` file from `.env.example`
2. Prompt you to edit credentials
3. Build and start the Docker container
4. Display access info

### Manual deployment on a VPS/Server:

**1. SSH into your server and clone the repo:**
```bash
ssh user@your-server.com
git clone https://github.com/lawfullyillegal-droid/travis-ops-center.git
cd travis-ops-center
```

**2. Create .env with strong credentials:**
```bash
cp .env.example .env
nano .env
# Set AUTH_USER and AUTH_PASS to strong values
```

**3. Start the service:**
```bash
docker-compose up -d
# or: bash deploy.sh your-domain.com admin@example.com
```

**4. Verify it's running:**
```bash
curl -u admin:password http://localhost:8080
docker-compose logs
```

**5. (Optional) Add HTTPS with nginx + Let's Encrypt:**

Install certbot:
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

Get a certificate:
```bash
sudo certbot certonly --standalone -d your-domain.com -m admin@example.com
```

Create `/etc/nginx/sites-available/ops-center`:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/ops-center /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**6. Access your deployment:**
```
https://your-domain.com
Username: (from .env AUTH_USER)
Password: (from .env AUTH_PASS)
```

### Backup & maintenance:

**Backup evidence and ledger:**
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/ evidence/ logs/
# Send to secure offsite storage
```

**View logs:**
```bash
docker-compose logs -f
tail -f logs/audit.log
```

**Stop service:**
```bash
docker-compose down
```

**Restart service:**
```bash
docker-compose restart
```

### Troubleshooting:

**Port 8080 already in use:**
```bash
# Change in .env:
SERVER_PORT=9090
docker-compose up -d
```

**Auth not working:**
```bash
# Make sure .env has AUTH_USER and AUTH_PASS set:
grep AUTH .env
# Restart:
docker-compose restart
```

**No evidence showing in web UI:**
```bash
# Check ledger exists:
ls -la data/integrity_ledger.db
# Or ingest test evidence:
python3 scripts/evidence_ingest.py /tmp/test.txt --notes "test"
```

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
