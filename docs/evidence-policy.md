# CASEOPS Evidence Integrity Policy

## Purpose

This repository provides tooling for evidence intake, hashing,
verification, manifests, and auditability.

The system distinguishes between:

1. Source evidence
2. Derived artifacts
3. Human analysis
4. AI-generated analysis

A cryptographic hash can demonstrate that checked bytes match the
bytes previously hashed. A hash alone does not establish authorship,
truthfulness, authenticity, admissibility, or legal sufficiency.

## Source Evidence

A source record is an original file or a byte-for-byte preserved copy
of an acquired record.

Source evidence must not be edited in place after intake.

Every source record should have:

- unique record ID
- UTC ingestion timestamp
- original filename
- stored evidence path
- byte count
- SHA-256 digest
- operator identifier when available
- acquisition/source notes when available

## Immutability

Do not:

- overwrite a source evidence file
- alter a source file after hashing
- silently replace a manifest
- treat a modified copy as the original

If a corrected or new copy is received, ingest it as a new record with
a new record ID and new SHA-256 value.

## Derived Artifacts

OCR output, transcripts, redactions, thumbnails, conversions,
summaries, reports, and extracted text are derived artifacts.

Derived artifacts should identify the record ID of the source from
which they were created.

## AI Output

AI-generated material is analysis, not source evidence.

AI output must:

- remain separate from original source evidence
- be treated as draft material until independently reviewed
- never overwrite source evidence
- never alter a source manifest
- never be represented as a verbatim source unless verified against
  the underlying record

AI work belongs under:

    drafts/ai/

Human-reviewed analytical work may be placed under:

    drafts/human/

## Public Repository Warning

This repository is public.

Do not commit:

- confidential evidence
- passwords or credentials
- private API keys
- personal identifiers that should remain private
- privileged communications
- sealed or protected records
- sensitive investigative material

Actual evidence is Git-ignored by default.

Manifests may be committed only after reviewing them for information
that should not be public.

## Verification

Verify a record with:

    python3 scripts/verify_record.py manifests/RECORD.json

PASS means the current file's SHA-256 digest and byte count match the
manifest.

FAIL means an integrity exception exists and should be investigated
before relying on that copy.

## Git

Git history is an audit mechanism for source code, policies, and
manifests.

Git is not a substitute for maintaining independent evidence backups
or proper acquisition documentation.
