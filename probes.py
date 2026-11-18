"""Evaluation probes — generated SEPARATELY from the memory corpus.

Probes come from this module only, with their own seed (777, not the
corpus seed 42) and their own templates, so no probe wording is copied
from a session and no probe was visible while the corpus was written.

Two families:

  rule_application   a scenario whose correct action depends on
                     applying a remembered explicit rule (or on seeing
                     that the rule's condition does NOT hold)
  pattern_induction  a new case that follows the pattern shown in the
                     worked examples (or a near case that does not)

Each probe carries the gold decision and the corpus item ids whose
retrieval counts as a recall hit (any one of them).
"""

from __future__ import annotations

import random
from typing import Dict, List

DEFAULT_SEED = 777

_FIRST_NAMES = ["Maya", "Tom", "Priya", "Leo", "Nina", "Omar", "Sue", "Dan"]


def generate_probes(seed: int = DEFAULT_SEED) -> List[Dict]:
    """Return the probe set, deterministic for ``seed``."""
    rng = random.Random(seed)
    name = lambda: rng.choice(_FIRST_NAMES)  # noqa: E731
    probes: List[Dict] = []

    def add(pid, family, text, gold, needed):
        probes.append({"id": pid, "family": family, "text": text,
                       "gold": gold, "needed_ids": list(needed)})

    # --- rule application: R1, manager note over $500 ----------------
    add("Q-R1-a", "rule_application",
        f"Probe: {name()} requests a refund for an order of $620. "
        "The order was delivered 4 days ago and the item is unused. "
        "What should the agent do?",
        "require_manager_note", ["R1"])
    add("Q-R1-b", "rule_application",
        f"Probe: {name()} requests a refund for an order of $240. "
        "The order was delivered 4 days ago and the item is unused. "
        "What should the agent do?",
        "refund_direct", ["R1"])
    add("Q-R1-c", "rule_application",
        f"Probe: {name()} requests a refund for an order of $510. "
        "The order was delivered 2 days ago. What should the agent do?",
        "require_manager_note", ["R1"])
    add("Q-R1-d", "rule_application",
        f"Probe: {name()} requests a refund for an order of $180. "
        "The order was delivered 6 days ago. What should the agent do?",
        "refund_direct", ["R1"])

    # --- rule application: R2, 30-day eligibility window -------------
    add("Q-R2-a", "rule_application",
        f"Probe: {name()} requests a refund for an order of $120. "
        "The order was delivered 45 days ago. What should the agent do?",
        "offer_store_credit", ["R2"])
    add("Q-R2-b", "rule_application",
        f"Probe: {name()} requests a refund for an order of $120. "
        "The order was delivered 10 days ago. What should the agent do?",
        "refund_direct", ["R2"])
    add("Q-R2-c", "rule_application",
        f"Probe: {name()} requests a refund for an order of $90. "
        "The order was delivered 60 days ago. What should the agent do?",
        "offer_store_credit", ["R2"])
    add("Q-R2-d", "rule_application",
        f"Probe: {name()} requests a refund for an order of $90. "
        "The order was delivered 5 days ago. What should the agent do?",
        "refund_direct", ["R2"])

    # --- rule application: R3, damaged items --------------------------
    add("Q-R3-a", "rule_application",
        f"Probe: {name()} reports that a kettle arrived damaged and "
        "asks what can be done. What should the agent do?",
        "offer_free_replacement", ["R3"])
    add("Q-R3-b", "rule_application",
        f"Probe: {name()} reports that a speaker arrived damaged and "
        "asks for help. What should the agent do?",
        "offer_free_replacement", ["R3"])
    add("Q-R3-c", "rule_application",
        f"Probe: {name()} requests a refund for an order of $80. "
        "The item arrived in perfect condition 3 days ago; the "
        "customer changed their mind. What should the agent do?",
        "refund_direct", ["R3"])

    # --- rule application: R4, billing disputes -----------------------
    add("Q-R4-a", "rule_application",
        f"Probe: {name()} opens a billing dispute about a double "
        "charge and asks for a refund. What should the agent do?",
        "escalate_to_billing", ["R4"])
    add("Q-R4-b", "rule_application",
        f"Probe: {name()} raises a billing dispute over an unknown "
        "charge on their card. What should the agent do?",
        "escalate_to_billing", ["R4"])
    add("Q-R4-c", "rule_application",
        f"Probe: {name()} requests a refund for an order of $75. "
        "The order was delivered 3 days ago and there is no billing "
        "issue. What should the agent do?",
        "refund_direct", ["R4"])

    # --- pattern induction: P1, repeat fault -> priority queue --------
    add("Q-P1-a", "pattern_induction",
        f"Probe: {name()} reports the same keyboard fault for the "
        "second time and asks for help. What should the agent do?",
        "move_to_priority_queue", ["P1-1", "P1-2", "P1-3"])
    add("Q-P1-b", "pattern_induction",
        f"Probe: {name()} says a mouse has failed again, the third "
        "time, a repeat issue. What should the agent do?",
        "move_to_priority_queue", ["P1-1", "P1-2", "P1-3"])
    add("Q-P1-c", "pattern_induction",
        f"Probe: {name()} reports a keyboard fault for the first "
        "time and asks for help. What should the agent do?",
        "standard_handling", ["P1-1", "P1-2", "P1-3"])
    add("Q-P1-d", "pattern_induction",
        f"Probe: {name()} asks how to pair a new headset and has a "
        "setup question. What should the agent do?",
        "standard_handling", ["P1-1", "P1-2", "P1-3"])

    # --- pattern induction: P2, >5 days late -> shipping fee refund ---
    add("Q-P2-a", "pattern_induction",
        f"Probe: {name()} says a package arrived 9 days late and "
        "asks what can be done. What should the agent do?",
        "refund_shipping_fee", ["P2-1", "P2-2", "P2-3"])
    add("Q-P2-b", "pattern_induction",
        f"Probe: {name()} says a delivery arrived 6 days late and "
        "asks what can be done. What should the agent do?",
        "refund_shipping_fee", ["P2-1", "P2-2", "P2-3"])
    add("Q-P2-c", "pattern_induction",
        f"Probe: {name()} says a package arrived 2 days late and "
        "asks what can be done. What should the agent do?",
        "standard_handling", ["P2-1", "P2-2", "P2-3"])
    add("Q-P2-d", "pattern_induction",
        f"Probe: {name()} says a package arrived on time and asks "
        "about the warranty. What should the agent do?",
        "standard_handling", ["P2-1", "P2-2", "P2-3"])

    return probes
