# CASEOPS timeline workflow

Keep timeline CSVs in the ignored `caseops-local/` directory or outside the checkout.
The timeline tool uses Python's standard library, works offline, and never opens
source URLs. No dependency installation is needed for this command.

```bash
mkdir -p caseops-local
# Copy your timeline CSV into caseops-local using your file manager.
python scripts/caseops_timeline.py caseops-local/timeline.csv --check
python scripts/caseops_timeline.py caseops-local/timeline.csv
python scripts/caseops_timeline.py caseops-local/timeline.csv --scope civil
python scripts/caseops_timeline.py caseops-local/timeline.csv --scope criminal
```

The exact CSV header is:

```csv
date,docket_scope,event,source_status,source_url
```

Dates use `YYYY-MM-DD`; scopes are `civil`, `criminal`, or `system`.
The first four fields must be nonempty. `source_url` may be blank when no online link exists; when provided, it must use HTTPS without embedded credentials. Quote fields containing commas, quotes, or newlines using normal CSV
quoting. Events are displayed chronologically; the source file is never rewritten.

Statuses are preserved verbatim. A scheduled appearance does not establish its
outcome, and receipt of an order does not establish the attachment's contents.
Civil and criminal entries retain their separate scopes.

Source links are omitted from display unless you pass `--include-links`. Event
descriptions and statuses can still contain private information: the default
report is for local review and is not an automatically sanitized publication.
`--check` prints only the event count and input-file SHA-256.

The digest identifies the CSV's exact bytes, including line endings and ordering.
It does not authenticate source communications or establish the truth of an event.
Changing bytes changes the digest. A GitHub commit containing a digest is a
reference point; checking it requires the corresponding original file.

## GitHub review

Commit code, tests, and reviewed documentation on a feature branch. Keep case
CSVs, Gmail links, and reports local. Before pushing, inspect the staged paths
with `git diff --cached --name-only` and review the staged changes with
`git diff --cached`. Ignore rules do not remove previously tracked files.

The validation workflow runs timeline tests and checks installer syntax along
with the existing command and web checks. Actual package installation must also
be exercised on a Termux device.
