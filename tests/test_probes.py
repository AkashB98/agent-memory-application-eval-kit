"""Probes: separate seed/module, both families, gold labels, needed ids."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corpus import generate_sessions  # noqa: E402
from probes import generate_probes  # noqa: E402


class TestProbes(unittest.TestCase):
    def setUp(self):
        self.probes = generate_probes()

    def test_deterministic(self):
        self.assertEqual(self.probes, generate_probes())
        self.assertEqual(self.probes, generate_probes(seed=777))

    def test_family_counts(self):
        rule = [p for p in self.probes if p["family"] == "rule_application"]
        pattern = [p for p in self.probes
                   if p["family"] == "pattern_induction"]
        self.assertEqual(len(rule), 14)
        self.assertEqual(len(pattern), 8)
        self.assertEqual(len(self.probes), 22)

    def test_every_probe_has_gold_and_needed_ids(self):
        corpus_ids = {item["id"] for s in generate_sessions()
                      for item in s["items"]}
        for probe in self.probes:
            self.assertTrue(probe["gold"])
            self.assertTrue(probe["needed_ids"])
            self.assertTrue(set(probe["needed_ids"]) <= corpus_ids)

    def test_probe_ids_unique(self):
        ids = [p["id"] for p in self.probes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_both_outcomes_present_per_family(self):
        # Each family mixes cases where a rule/pattern applies with
        # cases where it does not, so a constant policy cannot win.
        for family in ("rule_application", "pattern_induction"):
            golds = {p["gold"] for p in self.probes
                     if p["family"] == family}
            self.assertGreater(len(golds), 2, family)


if __name__ == "__main__":
    unittest.main()
