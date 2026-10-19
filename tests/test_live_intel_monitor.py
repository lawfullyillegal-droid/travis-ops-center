import sys
import types
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
try:
    import identifier_intel
except ImportError:
    # Standalone package tests validate pure functions even before the upgrade
    # is installed into the pre-existing CaseOps repo.
    fake = types.ModuleType('identifier_intel')
    fake.Store = object
    fake.HTTP = object
    fake.Sec = object
    fake.Gleif = object
    fake.glean_lei_record = lambda item: item
    fake.DATA_DIR = Path('/tmp/caseops-placeholder')
    sys.modules['identifier_intel'] = fake
from live_intel_monitor import normalize_cik, normalize_lei, recent_filings, annual_metric, changes_for, render_html

class MonitorTests(unittest.TestCase):
    def test_cik_normalization(self):
        self.assertEqual(normalize_cik('CIK 1677703'), '0001677703')
        with self.assertRaises(ValueError):
            normalize_cik('123abc')

    def test_lei_validation(self):
        self.assertEqual(normalize_lei(' 549300SFJ2D2CYY6CQ11 '), '549300SFJ2D2CYY6CQ11')
        with self.assertRaises(ValueError):
            normalize_lei('too-short')

    def test_sec_recent_alignment(self):
        sub = {'filings': {'recent': {'accessionNumber':['x','y'], 'form':['8-K','3'],
                   'filingDate':['2026-10-19','2026-10-18'], 'primaryDocument':['a.htm','b.htm']}}}
        self.assertEqual(recent_filings(sub), [{'accession':'x','form':'8-K','filed':'2026-10-19','document':'a.htm'}])

    def test_annual_numbers_compare_same_duration(self):
        values = {'facts': {'us-gaap': {'Assets': {'units': {'USD':[
            {'form':'10-K','end':'2024-12-31','val':100,'filed':'2025-03-01'},
            {'form':'10-K','end':'2025-12-31','val':125,'filed':'2026-03-01'}]}}}}}
        self.assertEqual(annual_metric(values, 'assets', ['Assets'])['year_over_year_pct'], 25.0)

    def test_new_filing_not_flagged_as_revision(self):
        new = {'filings':[{'accession':'a'}], 'financials':{}}
        self.assertEqual(changes_for('sec','X',new,{},True), [])
        self.assertEqual(changes_for('sec','X',new,{'filings':[]},False)[0]['type'],'NEW_SEC_FILINGS')

    def test_html_escapes_untrusted_text(self):
        html = render_html({'created_at':'2026-10-19', 'subjects':{'id':{'company_name':'<script>alert(1)</script>'}}, 'events':[], 'errors':[]})
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

if __name__ == '__main__':
    unittest.main()
