import csv
import hashlib
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

spec = importlib.util.spec_from_file_location("timeline", Path(__file__).resolve().parents[1] / "scripts/caseops_timeline.py")
timeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timeline)


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "timeline.csv"
        self.rows = [
            ["2026-09-24", "criminal", "Order, attachment", "Attachment needs review", "https://mail.google.com/private"],
            ["2026-09-14", "civil", "Clerk response", "Source communication", "https://example.org/source"],
        ]

    def write(self, rows=None, fields=None):
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields or timeline.FIELDS)
            writer.writerows(self.rows if rows is None else rows)

    def test_preserves_status_and_sorts_without_changing_source(self):
        self.write()
        before = self.path.read_bytes()
        rows, digest = timeline.read_timeline(self.path)
        self.assertEqual(rows[0]["docket_scope"], "civil")
        self.assertEqual(rows[1]["source_status"], "Attachment needs review")
        self.assertEqual(digest, hashlib.sha256(before).hexdigest())
        self.assertEqual(self.path.read_bytes(), before)
        report = timeline.render(rows, digest)
        self.assertNotIn("https://", report)
        self.assertIn("https://mail.google.com/private", timeline.render(rows, digest, True))

    def test_invalid_rows_fail(self):
        for column, value in [(0, "2026-02-30"), (0, "20260924"), (1, "merged"),
                              (2, ""), (2, "escape\x1b"), (4, "http://example.org"),
                              (4, "https://user:pass@example.org"), (4, "https://example.org:bad")]:
            with self.subTest(column=column, value=value):
                row = self.rows[0].copy()
                row[column] = value
                self.write([row])
                with self.assertRaises(ValueError):
                    timeline.read_timeline(self.path)

    def test_rejects_empty_bad_header_and_extra_columns(self):
        for rows, fields in [([], None), (self.rows, ["bad"]), ([self.rows[0] + ["extra"]], None)]:
            with self.subTest(rows=rows, fields=fields):
                self.write(rows, fields)
                with self.assertRaises(ValueError):
                    timeline.read_timeline(self.path)

    def test_cli_check_and_scope(self):
        self.write()
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(timeline.main([str(self.path), "--check"]), 0)
        self.assertNotIn("Clerk", output.getvalue())
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(timeline.main([str(self.path), "--scope", "civil"]), 0)
        self.assertIn("Clerk response", output.getvalue())
        self.assertNotIn("Order, attachment", output.getvalue())
        with redirect_stderr(io.StringIO()):
            self.assertEqual(timeline.main([str(self.path) + ".missing"]), 1)


if __name__ == "__main__":
    unittest.main()
