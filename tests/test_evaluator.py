"""Evaluator: determinism, report shape, recall alongside application."""

import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corpus import generate_sessions  # noqa: E402
from evaluator import evaluate, headline  # noqa: E402
from probes import generate_probes  # noqa: E402


class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.report = evaluate(generate_sessions(), generate_probes())

    def test_deterministic(self):
        again = evaluate(generate_sessions(), generate_probes())
        self.assertEqual(self.report, again)

    def test_report_md5_stable_across_three_runs(self):
        md5s = set()
        for _ in range(3):
            blob = json.dumps(
                evaluate(generate_sessions(), generate_probes()),
                sort_keys=True)
            md5s.add(hashlib.md5(blob.encode()).hexdigest())
        self.assertEqual(len(md5s), 1)

    def test_shape(self):
        self.assertEqual(self.report["corpus_sessions"], 12)
        self.assertEqual(self.report["probe_count"], 22)
        self.assertEqual(self.report["top_k"], 3)
        self.assertEqual(sorted(self.report["designs"]),
                         ["atomic_facts", "block_summaries",
                          "chained_notes"])

    def test_headline_covers_every_design_and_family(self):
        table = headline(self.report)
        for design in ("atomic_facts", "block_summaries", "chained_notes"):
            for family in ("rule_application", "pattern_induction"):
                self.assertIn(family, table[design])
                self.assertGreaterEqual(table[design][family], 0.0)
                self.assertLessEqual(table[design][family], 1.0)

    def test_recall_reported_alongside_accuracy(self):
        for data in self.report["designs"].values():
            for fam in data["by_family"].values():
                self.assertIn("accuracy", fam)
                self.assertIn("retrieval_recall", fam)
                self.assertEqual(fam["correct"] + (
                    fam["total"] - fam["correct"]), fam["total"])

    def test_recall_is_not_application(self):
        # The measured point of the kit: at least one design retrieves
        # the needed pattern examples perfectly while applying them
        # only half the time.
        block = self.report["designs"]["block_summaries"]["by_family"]
        self.assertEqual(block["pattern_induction"]["retrieval_recall"],
                         1.0)
        self.assertEqual(block["pattern_induction"]["accuracy"], 0.5)


if __name__ == "__main__":
    unittest.main()
