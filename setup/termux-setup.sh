#!/usr/bin/env bash
set -euo pipefail

# Termux bootstrap installer (safe, minimal)
if command -v pkg >/dev/null 2>&1; then
  PKG=pkg
elif command -v apt >/dev/null 2>&1; then
  PKG=apt
else
  echo "No package manager detected. Install packages manually: git, python, openssh"
  exit 1
fi

echo "Updating package lists..."
$PKG update -y || true

echo "Installing core packages: git, python, openssh, curl"
$PKG install -y git python openssh curl || true

echo "Installing python deps..."
python -m pip install --user pyyaml

echo "Termux setup complete. Ensure you have a GitHub SSH key configured for push/pull."
