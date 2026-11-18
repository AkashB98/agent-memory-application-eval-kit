"""The fixed agent policy — one decision function for every memory.

This is a deterministic scripted stand-in for an agent, not a language
model: it measures whether the retrieved memory text carries enough
for a fixed policy to act on, and it says nothing about how a real
LLM would behave.

``decide`` reads ONLY the retrieved memory texts and the probe text.
It has no idea which store the memory came from and contains no
branch on any store's identity — a unit test greps this module's
source to keep that true.
"""

from __future__ import annotations

import re
from typing import List

# Decision labels
REQUIRE_MANAGER_NOTE = "require_manager_note"
REFUND_DIRECT = "refund_direct"
OFFER_STORE_CREDIT = "offer_store_credit"
OFFER_FREE_REPLACEMENT = "offer_free_replacement"
ESCALATE_TO_BILLING = "escalate_to_billing"
MOVE_TO_PRIORITY_QUEUE = "move_to_priority_queue"
REFUND_SHIPPING_FEE = "refund_shipping_fee"
STANDARD_HANDLING = "standard_handling"

_MONEY_RE = re.compile(r"\$(\d+(?:\.\d+)?)")
_DELIVERED_RE = re.compile(r"delivered\s+(\d+)\s+days?\s+ago")
_LATE_RE = re.compile(r"(\d+)\s+days?\s+late")
_REPEAT_CUES = ("second time", "third time", "failed again",
                "repeat issue", "same fault", "same charger fault",
                "same keyboard fault", "kept coming back")


def _money(text: str):
    match = _MONEY_RE.search(text)
    return float(match.group(1)) if match else None


def _manager_note_threshold(memory: str):
    """Extract a dollar threshold stated near a manager-note rule."""
    for match in re.finditer(r"manager note", memory):
        window = memory[max(0, match.start() - 90):match.end() + 90]
        amounts = _MONEY_RE.findall(window)
        if amounts:
            return float(amounts[0])
    return None


def _window_days(memory: str):
    """Extract an eligibility window in days stated near store credit."""
    for match in re.finditer(r"store credit", memory):
        window = memory[max(0, match.start() - 120):match.end() + 120]
        found = re.search(r"(\d+)\s+days?", window)
        if found:
            return int(found.group(1))
    return None


def _count_phrase(memory: str, phrases) -> int:
    return sum(memory.count(p) for p in phrases)


def decide(memory_texts: List[str], probe_text: str) -> str:
    """Decide one probe from retrieved memory text alone."""
    memory = " ".join(memory_texts).lower()
    probe = probe_text.lower()

    is_refund_ask = "refund" in probe
    amount = _money(probe)
    delivered = _DELIVERED_RE.search(probe)
    days_since_delivery = int(delivered.group(1)) if delivered else None
    late = _LATE_RE.search(probe)
    days_late = int(late.group(1)) if late else None

    # Billing disputes: act only if memory carries the escalation.
    if "billing dispute" in probe or "billing dispute" in probe_text.lower():
        if "billing" in memory and "escalat" in memory:
            return ESCALATE_TO_BILLING
        return STANDARD_HANDLING

    # Damaged items: act only if memory carries the replacement step.
    if "damaged" in probe:
        if "damaged" in memory and "replacement" in memory:
            return OFFER_FREE_REPLACEMENT
        return STANDARD_HANDLING

    # Refund asks: apply any remembered refund rules whose condition
    # the probe actually meets.
    if is_refund_ask:
        if days_since_delivery is not None:
            window = _window_days(memory)
            if window is not None and days_since_delivery > window:
                return OFFER_STORE_CREDIT
        if amount is not None and "manager note" in memory:
            threshold = _manager_note_threshold(memory)
            if threshold is not None:
                if amount > threshold:
                    return REQUIRE_MANAGER_NOTE
            else:
                # A manager-note step is remembered but its threshold
                # is not in the retrieved text: a cautious fixed
                # policy asks for the note rather than guessing.
                return REQUIRE_MANAGER_NOTE
        return REFUND_DIRECT

    # Repeat-fault pattern: needs repeated evidence in memory, not a
    # single mention, before the policy treats it as a pattern.
    if any(cue in probe for cue in _REPEAT_CUES):
        if _count_phrase(memory, ("priority queue",)) >= 2:
            return MOVE_TO_PRIORITY_QUEUE
        return STANDARD_HANDLING

    # Late-delivery pattern: same repeated-evidence requirement, and
    # the lateness in the probe must clear the examples' range.
    if days_late is not None:
        evidence = _count_phrase(
            memory, ("shipping fee refund", "shipping fee was refunded",
                     "refunded the shipping fee", "refund shipping"))
        if days_late > 5 and evidence >= 2:
            return REFUND_SHIPPING_FEE
        return STANDARD_HANDLING

    return STANDARD_HANDLING
