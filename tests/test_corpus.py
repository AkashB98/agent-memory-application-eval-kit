"""Corpus: determinism, rules early, examples repeated, chatter present."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corpus import generate_sessions  # noqa: E402


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.sessions = generate_sessions()

    def test_deterministic(self):
        self.assertEqual(self.sessions, generate_sessions())
        self.assertEqual(self.sessions, generate_sessions(seed=42))

    def test_shape(self):
        self.assertEqual(len(self.sessions), 12)
        for session in self.sessions:
            self.assertIn("items", session)

    def test_four_rules_all_in_early_sessions(self):
        rule_sessions = {}
        for session in self.sessions:
            for item in session["items"]:
                if item["kind"] == "rule":
                    rule_sessions[item["id"]] = session["session_id"]
        self.assertEqual(sorted(rule_sessions), ["R1", "R2", "R3", "R4"])
        self.assertTrue(all(sid <= 5 for sid in rule_sessions.values()))

    def test_each_pattern_has_three_examples(self):
        counts = {"P1": 0, "P2": 0}
        for session in self.sessions:
            for item in session["items"]:
                if item["kind"] == "example":
                    counts[item["pattern"]] += 1
        self.assertEqual(counts, {"P1": 3, "P2": 3})

    def test_patterns_never_stated_as_rules(self):
        rule_text = " ".join(
            item["text"] for s in self.sessions for item in s["items"]
            if item["kind"] == "rule").lower()
        self.assertNotIn("priority queue", rule_text)
        self.assertNotIn("shipping fee", rule_text)

    def test_chatter_present_and_labelled(self):
        chatter = [item for s in self.sessions for item in s["items"]
                   if item["kind"] == "chatter"]
        self.assertEqual(len(chatter), 24)

    def test_items_carry_three_renderings(self):
        for session in self.sessions:
            for item in session["items"]:
                self.assertTrue(item["text"])
                self.assertTrue(item["summary"])
                self.assertTrue(item["note_parts"])


if __name__ == "__main__":
    unittest.main()
