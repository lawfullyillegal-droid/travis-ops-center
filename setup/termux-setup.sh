#!/usr/bin/env bash
set -euo pipefail

# Run from any directory; fail visibly instead of reporting incomplete installs as success.
REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v pkg >/dev/null 2>&1; then
  echo "This installer requires Termux. On a server, create a Python venv and install requirements.txt."
  exit 1
fi

echo "Updating package lists..."
pkg update -y

echo "Installing core packages: git, python, openssh, curl"
pkg install -y git python openssh curl

echo "Installing python deps..."
python -m venv "$REPO_ROOT/.venv"
"$REPO_ROOT/.venv/bin/python" -m pip install -r "$REPO_ROOT/requirements.txt"
"$REPO_ROOT/.venv/bin/python" -m pip check

echo "Termux setup complete. Activate the environment with:"
printf 'source %q\n' "$REPO_ROOT/.venv/bin/activate"

