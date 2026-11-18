"""Agent policy: fixed, memory-only, and — critically — no branching
on which memory design produced the retrieved text."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestNoDesignBranching(unittest.TestCase):
    def test_agent_source_names_no_design(self):
        with open(os.path.join(ROOT, "agent.py"), encoding="utf-8") as fh:
            source = fh.read().lower()
        for forbidden in ("atomic_facts", "block_summaries",
                          "chained_notes", "atomic", "chained"):
            self.assertNotIn(forbidden, source)

    def test_agent_takes_only_texts(self):
        # Same memory text in, same decision out — there is no
        # design argument to pass even if a caller wanted to.
        import inspect
        params = list(inspect.signature(agent.decide).parameters)
        self.assertEqual(params, ["memory_texts", "probe_text"])


class TestDecide(unittest.TestCase):
    RULE = ("Policy stated: orders over $500 need a manager note "
            "before refund.")

    def test_manager_note_applied_over_threshold(self):
        decision = agent.decide(
            [self.RULE],
            "Probe: a refund for an order of $620, delivered 4 days ago.")
        self.assertEqual(decision, "require_manager_note")

    def test_manager_note_not_applied_under_threshold(self):
        decision = agent.decide(
            [self.RULE],
            "Probe: a refund for an order of $240, delivered 4 days ago.")
        self.assertEqual(decision, "refund_direct")

    def test_no_memory_no_rule_application(self):
        decision = agent.decide(
            ["Chatter about the coffee machine."],
            "Probe: a refund for an order of $620, delivered 4 days ago.")
        self.assertEqual(decision, "refund_direct")

    def test_store_credit_window(self):
        memory = [("orders delivered more than 30 days ago are not "
                   "eligible for a refund; offer store credit instead")]
        decision = agent.decide(
            memory,
            "Probe: a refund for an order of $120, delivered 45 days ago.")
        self.assertEqual(decision, "offer_store_credit")

    def test_damaged_replacement(self):
        decision = agent.decide(
            ["damaged items get a free replacement before any refund"],
            "Probe: a kettle arrived damaged and asks what can be done.")
        self.assertEqual(decision, "offer_free_replacement")

    def test_billing_escalation(self):
        decision = agent.decide(
            ["billing disputes must be escalated to the billing team"],
            "Probe: a billing dispute about a double charge.")
        self.assertEqual(decision, "escalate_to_billing")

    def test_pattern_needs_repeated_evidence(self):
        one = ["a repeat case was moved to the priority queue"]
        two = one + ["another repeat case was moved to the priority queue"]
        probe = ("Probe: the same keyboard fault for the second time")
        self.assertEqual(agent.decide(one, probe), "standard_handling")
        self.assertEqual(agent.decide(two, probe),
                         "move_to_priority_queue")

    def test_late_pattern_threshold(self):
        memory = ["a shipping fee refund was issued",
                  "another shipping fee refund was issued"]
        self.assertEqual(
            agent.decide(memory, "Probe: a package arrived 9 days late"),
            "refund_shipping_fee")
        self.assertEqual(
            agent.decide(memory, "Probe: a package arrived 2 days late"),
            "standard_handling")

    def test_deterministic(self):
        args = ([self.RULE], "Probe: a refund for an order of $620.")
        self.assertEqual(agent.decide(*args), agent.decide(*args))


if __name__ == "__main__":
    unittest.main()
