# CaseOps Identifier Intelligence

This module traces identifiers, resolves legal entities, records money-flow edges, and flags source-backed anomalies without treating a numerical or name collision as proof of a relationship.

## Sources

- **GLEIF**: public LEI search, entity-name search, fuzzy completion, and LEI↔ISIN mappings.
- **SEC EDGAR**: public submissions JSON and company ticker/CIK index. Set a descriptive SEC user agent before use.
- **DTCC**: authorization-gated. CaseOps will only call a DTCC endpoint you explicitly configure and are authorized to use.

## One-time Termux setup

From the repository root:

```bash
chmod +x scripts/caseops-id
mkdir -p "$PREFIX/bin"
ln -sf "$PWD/scripts/caseops-id" "$PREFIX/bin/caseops-id"

# SEC asks automated clients to identify themselves.
export CASEOPS_SEC_USER_AGENT="Your Name your-email@example.com"
# Put the export in ~/.bashrc when you are satisfied with it.
```

## Commands

```bash
# Offline classification / checksum validation
caseops-id classify '529900T8BM49AURSDO55'

# LEI / ISIN / CIK tracing
caseops-id trace-id '529900T8BM49AURSDO55'
caseops-id trace-id 'US0378331005'
caseops-id trace-id 'CIK 0000320193'

# Entity resolution. Results are CANDIDATES until documentary evidence bridges them.
caseops-id trace-entity 'Example Corporation'

# A court/MVD/admin number is classified but NOT thrown into market databases merely because it is numeric.
caseops-id trace-id 'J0801TR2026000437'

# Record a documented payment/fee/custody relationship.
caseops-id money-add \
  --from-type PAYMENT --from-value 'receipt-123' \
  --relation paid_to \
  --to-type ENTITY --to-value 'Example Payee' \
  --amount 20 --date 2026-09-29 \
  --evidence-ref 'evidence-...' \
  --status VERIFIED

caseops-id links --subject 'Example Payee'

# Record an identifier conflict from two source records.
caseops-id anomaly-id \
  --subject 'same asserted administrative event' \
  --id-a '12345678' --source-a 'contemporaneous notice' \
  --id-b '12345679' --source-b 'later certified history'
```

## DTCC authorized mode

DTCC APIs are product-specific and may require account setup/entitlements. CaseOps therefore does not guess endpoints or bypass access controls. If you have an authorized API, configure a URL template and token:

```bash
export CASEOPS_DTCC_API_URL='https://authorized.example.dtcc.endpoint/security/{id}'
export CASEOPS_DTCC_BEARER_TOKEN='...'
caseops-id trace-id 'VALID_IDENTIFIER' --dtcc
```

Do **not** commit tokens to Git.

## Evidence model

Every network response is saved under `data/identifier_intel/raw/` and SHA-256 hashed. SQLite records the query, URL, fetch time, response hash, and relationship generated from the source.

Relationship statuses are deliberately explicit:

- `VERIFIED`: source directly supports the edge.
- `CANDIDATE`: algorithmic/entity-resolution candidate requiring corroboration.
- `UNPROVEN`: asserted theory with a missing evidentiary bridge.
- `REJECTED`: investigated collision that was shown unrelated.

The goal is reproducibility: **fact → source → hash → relationship**, not inference-by-number-match.
