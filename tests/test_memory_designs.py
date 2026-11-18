"""Memory designs: same corpus, three stores, one query interface."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from corpus import generate_sessions  # noqa: E402
from memory_designs import DESIGNS, build_store, retrieve  # noqa: E402


class TestMemoryDesigns(unittest.TestCase):
    def setUp(self):
        self.sessions = generate_sessions()
        self.stores = {d: build_store(d, self.sessions) for d in DESIGNS}

    def test_three_designs(self):
        self.assertEqual(DESIGNS, ("atomic_facts", "block_summaries",
                                   "chained_notes"))

    def test_card_counts(self):
        self.assertEqual(len(self.stores["atomic_facts"]), 10)
        self.assertEqual(len(self.stores["block_summaries"]), 12)
        self.assertEqual(len(self.stores["chained_notes"]), 20)

    def test_unknown_design_rejected(self):
        with self.assertRaises(ValueError):
            build_store("no_such_design", self.sessions)

    def test_retrieval_interface_and_top_k(self):
        for design, cards in self.stores.items():
            hits = retrieve(cards, "refund for an order delivered "
                                   "45 days ago", top_k=3)
            self.assertEqual(len(hits), 3, design)
            self.assertTrue(all("text" in h for h in hits), design)

    def test_retrieval_deterministic(self):
        for cards in self.stores.values():
            q = "billing dispute about a double charge"
            self.assertEqual(retrieve(cards, q), retrieve(cards, q))

    def test_cards_record_sources(self):
        # Cards built from content items record them; the summary
        # blocks for the four chatter-only sessions (9-12) legitimately
        # have no source items.
        for design, cards in self.stores.items():
            for card in cards:
                if design == "block_summaries" and \
                        card["session_id"] >= 9:
                    self.assertEqual(card["source_item_ids"], [])
                else:
                    self.assertTrue(card["source_item_ids"])


if __name__ == "__main__":
    unittest.main()
