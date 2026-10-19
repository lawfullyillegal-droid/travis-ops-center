# CaseOps public corporate intelligence: operations runbook

Updated 2026-10-19. This is source code and an operator plan, **not a claim that jobs are running**. A connected GitHub integration returned a `403 Resource not accessible by integration` when creating a branch. Install and push through your existing Termux Git credentials.

## System boundary

`travis-ops-center` and `federal-suit-2026` are currently **public GitHub repositories**. Keep private evidence, contact details, case identifiers, trust details, and unredacted legal filings outside those repositories. The included watchlist contains only public corporate identifier records. Do not add your private identifiers to `config/public_intel_watchlist.json` or to the public GitHub workflow.

Existing CaseOps `identifier_intel.py` already normalizes LEI, CIK, ISIN and CUSIP shapes; saves HTTP response bytes with SHA-256 in `data/identifier_intel/raw/`; logs provenance in SQLite; and marks entity-name matches as candidates. This upgrade runs repeatable official API reads and creates annual-number comparisons using the original evidence store.

## Termux turnkey

Download the ZIP into Android Downloads and extract it. In Termux, run:

```bash
cd "$HOME/storage/shared/Download/caseops-live-upgrade"
bash install.sh
export CASEOPS_SEC_USER_AGENT='Your real name your-confirmed-email@example.com'
caseops-live run
caseops-live report
```

If using `unzip` manually: `pkg install unzip -y; cd ~/storage/shared/Download; unzip caseops-live-upgrade.zip`.

If the repo is not present: `git clone https://github.com/lawfullyillegal-droid/travis-ops-center.git ~/caseops` before running the installer. If you have an existing repo, do not clone over it.

Optional foreground monitoring while Android permits the process to run:

```bash
caseops-live loop --interval-hours 6
```

**Android may suspend Termux**, so GitHub Actions is the more reliable periodic runner after publication.

To review and push PUBLIC code on a separate feature branch:

```bash
caseops-live publish
```

This command asks for explicit confirmation, commits only six approved public code files, and requires the GitHub remote to match `lawfullyillegal-droid/travis-ops-center`. It does not merge into `main` or upload case evidence.

## GitHub Actions (after PR merge)

Workflow `.github/workflows/public-intel-monitor.yml` supports manual runs and a nominal 6-hour schedule; GitHub scheduled runs can be delayed. Set repository **Actions variable** `CASEOPS_SEC_USER_AGENT` to an identifying user agent with a working contact email. SEC calls will otherwise be skipped and logged as source errors, while GLEIF can still work.

For optional Slack notifications, set the repository **Actions secret** `CASEOPS_SLACK_WEBHOOK` to a Slack incoming-webhook URL. Never put that URL in Git, documents, messages, or the watchlist. GitHub Actions cache restores the previous *public corporate* baseline, and report files are attached to workflow runs for 30 days. **On a public repository, treat workflow reports and logs as public information.**

SEC fair-access policy is 10 requests/second across clients; this monitor serializes queries, uses only official data APIs, and watches a small fixed identifier list. For large-scale backfill, obtain official bulk data files instead of high-volume crawling. GLEIF supports official LEI/name search and periodic updated data; this package checks targeted records rather than scraping website HTML.

## Operational detail

- `SEC submissions JSON`: newest filing accession, form, filed date, primary document.
- `SEC companyfacts JSON`: selects annual 10-K observations for revenue, net income, assets, liabilities, operating income, and cash from operations. All values retain dates, units, accession, concept and source URL.
- `Annual YoY`: compares annual periods approximately one year apart and only within the same US-GAAP concept and unit; 25%+ movements are flagged **for review**, not as proof of wrongdoing. Different reporting durations are not mixed.
- `GLEIF LEI`: legal name, entity status, jurisdiction, registration status, update/renewal dates.
- `Change detection`: new accession numbers, restated same-period figures, and LEI field changes relative to previous successful scan. Initial baseline is not mislabeled as a new filing. API errors preserve prior state.
- Provenance: source response, SHA-256, URL, and UTC fetch date in the existing SQLite store. Report files live under `data/identifier_intel/monitor/`, which must remain Git-ignored.

Potential software improvements later: precise restatement-series tracking, SEC XBRL dimensional contexts, direct authorized public-entity ownership graphs, restricted case-ledger bridge, confidence scoring, and local private source ingestion.

## Case records index (review separately; NOT in the hosted public scans)

| Track | Verified/observed information | Missing for authoritative latest status |
|---|---|---|
| Mohave Justice Court 2026 | Case J0801TR2026000437, a 2026 driving-while-suspended charge; 2026-09-29 case materials indicate not-guilty plea and release conditions | Obtain current docket/minute orders and next appearance from court directly; old data cannot establish October 19 status |
| Mohave 2024/MVD | J0801TR2024000143 related civil traffic and separate SR22-based A.R.S. § 28-4087 withdrawal; historic TTEAP / FARE | Exact current suspension action and reinstatement requirements; certified court-to-MVD transmission and payment ledger |
| Ventura records | Public-records request #26-646 closed 2026-03-10; requester challenged missing specific case records 2026-03-16; other requests including #26-1400 | Check each actual portal status; distinguish Sheriff/Probation/city police custody; retain source emails |
| Aztec Constructors/UCC | 2025-08-28 opposing counsel requested filing UCC-3 terminations; requester replied he would remove the filings. Prior rescission/apology communications exist. | Current California Secretary of State UCC status and exact filing numbers; do not call them valid active liens without current official search |
| Charles Brown trust | Name given by operator, identity/document details not established from the sources checked | Exact executed trust document, legal trust name, trustee authority, jurisdiction and authentic identifier; do not conflate with Ryle trust |
| Federal civil claims | Draft complaint packages and `federal-suit-2026` code repository located | Court-stamped complaint, case number, service status and current federal docket; a draft/repo is not proof of filing |

## Workspace assignments

- **GitHub:** public reviewed source code and sanitized architecture only; keep evidence in restricted local directories.
- **Termux:** run monitor, hash originals, maintain custody ledger and local reports.
- **Notion:** case work queue, neutral matter IDs, status and links; do not paste private evidence into broadly shared pages.
- **Google Drive:** source documents with controlled sharing and version history.
- **Gmail:** original institutional messages and request threads.
- **Slack:** optional alert feed of public-corporate changes and review tasks; no personal records in public channels.
- **Vercel / Versal:** use only for a sanitized public presentation layer. The Flask dashboard is not confirmed Vercel-ready; deploy reviewed static sanitized pages instead.
- **WPWriter / Descript:** optional public-facing content and media after legal review, not a source of case status or a place for privileged evidence.

## Source-of-truth hierarchy

1. Certified court/agency documents and up-to-date signed docket orders.
2. Original emails/filings + timestamped receipts and official portals.
3. Hash-verified source copies.
4. GitHub CaseOps summaries and spreadsheets.
5. Hypotheses and algorithmic candidates, clearly labeled as unproven.

No CIK/LEI/CUSIP number match automatically proves trust property, securities ownership, conversion of a traffic fine, corruption, or liability. Claims need a documented transaction chain.
