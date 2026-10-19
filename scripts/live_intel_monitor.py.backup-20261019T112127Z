#!/usr/bin/env python3
"""Public-corporate SEC/GLEIF monitor for CaseOps (no private-case data in hosted runs)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from identifier_intel import Store, HTTP, Sec, Gleif, glean_lei_record, DATA_DIR  # noqa: E402

OUTPUT = DATA_DIR / 'monitor'
WATCHLIST = ROOT / 'config' / 'public_intel_watchlist.json'
FORM_TYPES = {'8-K', '8-K/A', '10-K', '10-K/A', '10-Q', '10-Q/A', 'DEF 14A', 'S-8'}
METRICS = {
    'revenue': ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues',
                'SalesRevenueNet', 'RevenueFromContractWithCustomerIncludingAssessedTax'],
    'net_income': ['NetIncomeLoss'],
    'assets': ['Assets'],
    'liabilities': ['Liabilities'],
    'operating_income': ['OperatingIncomeLoss'],
    'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
}
STOCK = {'assets', 'liabilities'}


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return default


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    temp.replace(path)


def normalize_cik(value):
    digits = re.sub(r'^(?:CIK)\s*', '', str(value).strip(), flags=re.I)
    if not digits.isdigit() or len(digits) > 10:
        raise ValueError('CIK must contain 1–10 digits')
    return digits.zfill(10)


def normalize_lei(value):
    result = re.sub(r'\s+', '', str(value).upper())
    if not re.fullmatch(r'[A-Z0-9]{20}', result):
        raise ValueError('LEI must have exactly 20 alphanumeric characters')
    return result


def recent_filings(submissions, count=30):
    recent = ((submissions.get('filings') or {}).get('recent') or {})
    accessions = recent.get('accessionNumber') or []
    forms = recent.get('form') or []
    dates = recent.get('filingDate') or []
    primary = recent.get('primaryDocument') or []
    out = []
    for i, accession in enumerate(accessions):
        form = forms[i] if i < len(forms) else ''
        if form not in FORM_TYPES:
            continue
        out.append({'accession': str(accession), 'form': str(form),
                    'filed': str(dates[i]) if i < len(dates) else '',
                    'document': str(primary[i]) if i < len(primary) else ''})
        if len(out) >= count:
            break
    return out


def annual_metric(companyfacts, metric, concepts):
    facts = (companyfacts.get('facts') or {}).get('us-gaap') or {}
    candidates = []
    chosen = None
    for concept in concepts:
        units = ((facts.get(concept) or {}).get('units') or {}).get('USD') or []
        rows = []
        for item in units:
            if item.get('form') not in {'10-K', '10-K/A'}:
                continue
            end, start = item.get('end'), item.get('start')
            if not end or not isinstance(item.get('val'), (int, float)):
                continue
            try:
                end_date = dt.date.fromisoformat(end)
                if metric not in STOCK:
                    if not start or not (300 <= (end_date - dt.date.fromisoformat(start)).days <= 380):
                        continue
                elif start:
                    continue
            except ValueError:
                continue
            rows.append({'end': end, 'start': start, 'filed': item.get('filed', ''),
                         'form': item.get('form'), 'accession': item.get('accn'),
                         'value': item['val'], 'unit': 'USD', 'concept': concept})
        if rows:
            candidates = rows
            chosen = concept
            break
    if not candidates:
        return {'concept': None, 'observations': [], 'year_over_year_pct': None}
    by_end = {}
    for item in candidates:
        e = item['end']
        if e not in by_end or item['filed'] > by_end[e]['filed']:
            by_end[e] = item
    latest = sorted(by_end.values(), key=lambda x: x['end'], reverse=True)[:2]
    yoy = None
    if len(latest) == 2:
        a, b = latest[0], latest[1]
        days = (dt.date.fromisoformat(a['end']) - dt.date.fromisoformat(b['end'])).days
        if 330 <= days <= 400 and b['value']:
            yoy = round((a['value'] - b['value']) / abs(b['value']) * 100, 2)
    return {'concept': chosen, 'observations': latest, 'year_over_year_pct': yoy}


def summarize_financials(data):
    return {name: annual_metric(data, name, concepts) for name, concepts in METRICS.items()}


def changes_for(label, subject, current, prior, first_run):
    changes = []
    if label == 'sec':
        new_filings = [f for f in current.get('filings', [])
                       if f['accession'] not in {x['accession'] for x in prior.get('filings', [])}]
        if not first_run and new_filings:
            changes.append({'type': 'NEW_SEC_FILINGS', 'subject': subject, 'count': len(new_filings),
                            'details': new_filings[:8]})
        for name, metric in current.get('financials', {}).items():
            previous_metric = (prior.get('financials') or {}).get(name) or {}
            new_ob = (metric.get('observations') or [{}])[0]
            old_ob = (previous_metric.get('observations') or [{}])[0]
            # Compare identical reporting period/concept, not a new fiscal period to an old one.
            if (not first_run and new_ob and old_ob and
                new_ob.get('end') == old_ob.get('end') and
                new_ob.get('concept') == old_ob.get('concept') and
                new_ob.get('value') != old_ob.get('value')):
                changes.append({'type': 'REPORTED_FIGURE_REVISED', 'subject': subject,
                                'metric': name, 'period_end': new_ob['end'],
                                'old': old_ob.get('value'), 'new': new_ob.get('value')})
    else:
        for field in ('legal_name', 'entity_status', 'registration_status', 'last_update_date'):
            if not first_run and current.get(field) != prior.get(field):
                changes.append({'type': 'GLEIF_RECORD_CHANGED', 'subject': subject,
                                'field': field, 'old': prior.get(field), 'new': current.get(field)})
    return changes


def scan(watchlist, previous, store):
    client = HTTP(store)
    sec, gleif = Sec(client), Gleif(client)
    first_run = not bool(previous.get('subjects'))
    result = {'created_at': utc_now(), 'kind': 'public_corporate_intelligence',
              'initial_baseline': first_run, 'subjects': {}, 'events': [], 'errors': [],
              'rules': {'annual_yoy_review_threshold_percent': 25,
                        'numeric_change_requires_same_period_and_concept': True}}
    if not isinstance(watchlist.get('watch'), list):
        raise ValueError('Watchlist must contain a watch array')
    for item in watchlist['watch']:
        label = str(item.get('label') or '').strip()
        kind = item.get('kind')
        if not label or kind not in ('cik', 'lei'):
            raise ValueError('Each watch item requires label and kind=cik or lei')
        key = f'{kind}:{normalize_cik(item["value"]) if kind == "cik" else normalize_lei(item["value"])}'
        old = (previous.get('subjects') or {}).get(key, {})
        try:
            if kind == 'cik':
                cik = normalize_cik(item['value'])
                submissions, submission_id = sec.submissions(cik)
                financials = {}
                companyfacts_error = None
                try:
                    url = f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'
                    facts, facts_id = client.get_json('SEC_COMPANYFACTS', url, cik, sec=True)
                    financials = summarize_financials(facts)
                except Exception as exc:
                    companyfacts_error = str(exc)
                    result['errors'].append({'subject': label, 'source': 'SEC_COMPANYFACTS', 'detail': str(exc)})
                current = {'label': label, 'kind': 'cik', 'identifier': cik,
                           'company_name': submissions.get('name'),
                           'tickers': submissions.get('tickers', []),
                           'filings': recent_filings(submissions), 'financials': financials,
                           'source_url': f'https://data.sec.gov/submissions/CIK{cik}.json',
                           'companyfacts_url': f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
                           'companyfacts_error': companyfacts_error}
                result['events'] += changes_for('sec', label, current, old, first_run or not old)
                for name, metric in financials.items():
                    pct = metric.get('year_over_year_pct')
                    if pct is not None and abs(pct) >= 25 and (not old or ((old.get('financials') or {}).get(name) or {}).get('year_over_year_pct') != pct):
                        result['events'].append({'type': 'ANNUAL_YOY_REVIEW', 'subject': label,
                                                 'metric': name, 'percent': pct,
                                                 'note': 'Financial signal only; not evidence of misconduct'})
                if not old:
                    store.add_link(from_type='CIK', from_value=cik,
                                   relation='identifies_sec_filer', to_type='ENTITY',
                                   to_value=str(submissions.get('name', label)), snapshot_id=submission_id)
            else:
                lei = normalize_lei(item['value'])
                record, snapshot_id = gleif.lei(lei)
                summary = glean_lei_record(record.get('data') or {})
                current = {'label': label, 'kind': 'lei', 'identifier': lei,
                           'legal_name': summary.get('legal_name'),
                           'entity_status': summary.get('status'),
                           'registration_status': summary.get('registration_status'),
                           'last_update_date': summary.get('last_update_date'),
                           'next_renewal_date': summary.get('next_renewal_date'),
                           'jurisdiction': summary.get('jurisdiction'),
                           'source_url': f'https://api.gleif.org/api/v1/lei-records/{lei}'}
                result['events'] += changes_for('lei', label, current, old, first_run or not old)
                if not old and summary.get('legal_name'):
                    store.add_link(from_type='LEI', from_value=lei,
                                   relation='identifies_legal_entity', to_type='ENTITY',
                                   to_value=summary['legal_name'], snapshot_id=snapshot_id)
            result['subjects'][key] = current
        except Exception as exc:
            # Preserve prior state so transient failures do not erase the baseline.
            result['errors'].append({'subject': label, 'source': kind.upper(), 'detail': str(exc)})
            if old:
                result['subjects'][key] = old
    return result


def render_html(report):
    escape = html.escape
    cards = []
    for key, rec in sorted(report.get('subjects', {}).items()):
        url = rec.get('source_url', '')
        caption = escape(str(rec.get('company_name') or rec.get('legal_name') or rec.get('label', '')))
        view = '<a href="' + escape(url, quote=True) + '">Official record</a>' if url.startswith('https://') else ''
        body = f'<h2>{escape(key)} — {caption}</h2><p>{view}</p>'
        for name, metric in rec.get('financials', {}).items():
            pts = metric.get('observations') or []
            values = ', '.join(f"{p['end']}: ${p['value']:,.0f}" for p in pts)
            yoy = metric.get('year_over_year_pct')
            body += f'<p><strong>{escape(name)}</strong>: {escape(values or "No annual data")}'+(f' (YoY {yoy:+.2f}%)' if yoy is not None else '')+'</p>'
        if rec.get('kind') == 'lei':
            body += '<p>Entity: ' + escape(str(rec.get('entity_status'))) + ' / Registration: ' + escape(str(rec.get('registration_status'))) + '</p>'
        if rec.get('filings'):
            body += '<p>Recent filings: '+escape('; '.join(f"{f['filed']} {f['form']} {f['accession']}" for f in rec['filings'][:7]))+'</p>'
        cards.append('<section>'+body+'</section>')
    events = ''.join('<li>'+escape(json.dumps(e, ensure_ascii=False))+'</li>' for e in report.get('events', []))
    errors = ''.join('<li>'+escape(json.dumps(e, ensure_ascii=False))+'</li>' for e in report.get('errors', []))
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>CaseOps Public Identifier Monitor</title><style>body{max-width:980px;margin:2rem auto;padding:1rem;'
            'font:16px/1.5 system-ui;background:#101923;color:#e8eef4}section{padding:1rem 1.3rem;margin:1rem 0;'
            'background:#1c2d3c;border-radius:12px}a{color:#85d7ff}h1{color:#dcf9ff}li{margin:.5rem 0}small{color:#b3c5d1}</style>'
            '<h1>CaseOps — Public Corporate Identifier Monitor</h1><p>Fetched at '+escape(report['created_at'])+'</p>'
            '<small>Annual numbers are SEC-reported USD facts. Year-over-year comparisons require comparable reporting periods. '
            'Candidate associations do not establish a court or trust connection.</small>'
            + ''.join(cards) + '<h2>Review events</h2><ul>'+(events or '<li>No new changes detected, or first baseline</li>')+'</ul>'
            +'<h2>Source errors</h2><ul>'+(errors or '<li>None</li>')+'</ul></html>')


def notify_slack(report):
    url = os.getenv('CASEOPS_SLACK_WEBHOOK', '').strip()
    if not url:
        return None
    if not (url.startswith('https://hooks.slack.com/services/') or url.startswith('https://hooks.slack-gov.com/services/')):
        return 'Slack webhook URL must be an official Slack incoming-webhook URL'
    event_count = len(report['events'])
    error_count = len(report['errors'])
    if not event_count and not error_count:
        return None
    message = (f'CaseOps public SEC/GLEIF scan: {event_count} review events, {error_count} source errors. '
               f'Timestamp {report["created_at"]}; inspect the local or Actions report before drawing conclusions.')
    req = urllib.request.Request(url, data=json.dumps({'text': message}).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12):
            return None
    except (urllib.error.URLError, OSError) as exc:
        return f'Slack delivery failed: {exc}'


def run_once(watchlist_path=WATCHLIST, output_dir=OUTPUT):
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / 'state.json'
    prev = load_json(state_path, {})
    store = Store()
    try:
        report = scan(load_json(watchlist_path, {}), prev, store)
    finally:
        store.conn.close()
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    save_json(output_dir / 'latest.json', report)
    save_json(output_dir / f'report-{stamp}.json', report)
    save_json(state_path, {'created_at': report['created_at'], 'subjects': report['subjects']})
    (output_dir / 'index.html').write_text(render_html(report), encoding='utf-8')
    failure = notify_slack(report)
    if failure:
        print('WARNING:', failure, file=sys.stderr)
    print(f'Scan {report["created_at"]}: {len(report["subjects"])} subjects, '
          f'{len(report["events"])} review events, {len(report["errors"])} source errors')
    print(f'Report: {output_dir / "index.html"}')
    return 0 if report['subjects'] else 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['run', 'loop', 'status'], nargs='?', default='run')
    p.add_argument('--watchlist', type=Path, default=WATCHLIST)
    p.add_argument('--interval-hours', type=float, default=6.0)
    p.add_argument('--output-dir', type=Path, default=OUTPUT)
    args = p.parse_args()
    if args.command == 'status':
        report = load_json(args.output_dir / 'latest.json', {})
        if not report:
            print('No local monitor run yet; use caseops-live run')
            return 1
        print(json.dumps({'at': report['created_at'], 'subjects': list(report['subjects']),
                          'events': report['events'], 'errors': report['errors']}, indent=2))
        return 0
    if args.command == 'loop':
        if not 0.5 <= args.interval_hours <= 168:
            p.error('--interval-hours must be between 0.5 and 168')
        while True:
            run_once(args.watchlist, args.output_dir)
            time.sleep(args.interval_hours * 3600)
    return run_once(args.watchlist, args.output_dir)


if __name__ == '__main__':
    raise SystemExit(main())
