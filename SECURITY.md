# Operational Security

This repository contains tooling for evidence handling and authorized investigation workflows. Treat code, evidence, and credentials as separate trust domains.

## Data handling

- Do not commit raw evidence, email exports, personal records, credentials, tokens, private keys, or local `.env` files by default.
- Store evidence in controlled local/private storage and record hashes/manifests in source control when appropriate.
- `.gitignore` prevents new accidental additions; it does **not** remove material already committed in Git history.
- If a secret was committed, rotate/revoke it. Removing the file from the latest commit is not sufficient.
- Review repository visibility before placing case-specific or personally identifying material in GitHub.

## Network and OSINT commands

Use reconnaissance or scanning functions only on systems, networks, accounts, and data for which you have authorization. The command vault is an allow-list, not proof of authorization.

## Deployment

- Loopback-only (`127.0.0.1`) is the default.
- Docker/server deployments require `AUTH_USER` and `AUTH_PASS`.
- Put remote deployments behind a VPN or authenticated TLS reverse proxy.
- Do not use `ALLOW_INSECURE_NO_AUTH=1` on an untrusted network.

## Evidence integrity

Preserve original files. Hash copies at ingestion, retain timestamps, and document transformations separately from originals.
