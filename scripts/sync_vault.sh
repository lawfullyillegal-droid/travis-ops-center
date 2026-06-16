#!/usr/bin/env bash
set -euo pipefail

# Safe git-based vault sync helper
# Usage: ./sync_vault.sh [commit-message]

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

MSG="${1:-"Update from device"}"

if ! command -v git >/dev/null 2>&1; then
  echo "git not found"
  exit 1
fi

echo "Fetching remote changes..."
git fetch --all --prune

echo "Merging remote changes (fast-forward only)..."
git pull --ff-only || true

if git status --porcelain | grep . >/dev/null 2>&1; then
  echo "Committing local changes..."
  git add -A
  git commit -m "$MSG" || true
  echo "Pushing to origin..."
  git push origin HEAD
else
  echo "No changes to commit."
fi

echo "Sync complete."
