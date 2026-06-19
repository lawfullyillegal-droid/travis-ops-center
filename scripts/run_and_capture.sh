#!/usr/bin/env bash
set -euo pipefail

# Run a python script, capture stdout/stderr to evidence outputs, and log to ledger via evidence_ingest.py
# Usage: ./scripts/run_and_capture.sh path/to/script.py "optional notes"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$REPO_ROOT/evidence/outputs"
mkdir -p "$OUT_DIR"

SCRIPT="$1"
NOTES="${2:-run output from $SCRIPT}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT_FILE="$OUT_DIR/output-$TS.txt"

python3 "$SCRIPT" > "$OUT_FILE" 2>&1 || true

echo "Captured output to $OUT_FILE"

# ingest the output file into the ledger (creates copy under evidence as well)
python3 "$REPO_ROOT/scripts/evidence_ingest.py" "$OUT_FILE" --notes "$NOTES"
