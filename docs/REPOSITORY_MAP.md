# Repository Map

Use this map to reduce duplicated functionality without destroying evidence or development history.

| Repository | Role | Direction |
|---|---|---|
| `travis-ops-center` | Primary operations control plane | Active; consolidate runtime, evidence indexing, dashboard, Termux workflows here |
| `federal-suit-2026` | Case-specific archive/tooling | Keep isolated from the runtime; do not make it a dependency of the control plane |
| `evidence-ledger` | Legacy ledger/publication prototype | Treat as legacy/read-only until sensitive content and publication intent are reviewed |
| `legal-command-center` | Earlier dashboard prototype | Port only proven UI/features, then consider archival after feature parity |
| `INVESTIGATOR-DESK` | Analysis/parser utilities | Reuse selected parser modules through explicit interfaces; avoid duplicating the whole app |
| `Fast-Track-Academy` | Education platform | Keep separate; unrelated data and dependency boundary |

## Consolidation rules

1. No destructive history rewrites during consolidation.
2. No raw case evidence copied between repos unless deliberately reviewed.
3. New shared runtime work lands in `travis-ops-center`.
4. Reusable parsers become small modules with tests and documented inputs/outputs.
5. Public-facing repos contain sanitized/publication-ready material only.
6. Case-specific material and private evidence should use access controls appropriate to the data.
