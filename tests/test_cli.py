"""CLI: generate / run / check exit codes 0, 1 and 2."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import EXIT_ERROR, EXIT_FAIL, EXIT_OK, main as cli_main  # noqa: E402


def _run(argv):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return cli_main(argv)


class TestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="memory-eval-test-")

    def test_generate_writes_corpus(self):
        path = os.path.join(self.tmp, "corpus.json")
        self.assertEqual(_run(["generate", "--out", path]), EXIT_OK)
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        self.assertEqual(len(doc["sessions"]), 12)

    def test_run_writes_report(self):
        path = os.path.join(self.tmp, "report.json")
        self.assertEqual(_run(["run", "--out", path]), EXIT_OK)
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual(report["probe_count"], 22)

    def test_check_pass_on_fresh_report(self):
        path = os.path.join(self.tmp, "report.json")
        self.assertEqual(_run(["run", "--out", path]), EXIT_OK)
        self.assertEqual(_run(["check", "--report", path]), EXIT_OK)

    def test_check_fail_on_tampered_report(self):
        path = os.path.join(self.tmp, "report.json")
        self.assertEqual(_run(["run", "--out", path]), EXIT_OK)
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        report["designs"]["atomic_facts"]["by_family"][
            "rule_application"]["accuracy"] = 0.0
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(report, sort_keys=True))
        self.assertEqual(_run(["check", "--report", path]), EXIT_FAIL)

    def test_check_error_on_missing_file(self):
        self.assertEqual(
            _run(["check", "--report", "/tmp/no-such-report-xyz.json"]),
            EXIT_ERROR)

    def test_check_error_on_malformed_file(self):
        path = os.path.join(self.tmp, "bad.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertEqual(_run(["check", "--report", path]), EXIT_ERROR)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write('{"hello": 1}')
        self.assertEqual(_run(["check", "--report", path]), EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()
