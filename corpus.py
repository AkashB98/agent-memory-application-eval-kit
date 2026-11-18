"""Deterministic synthetic session corpus — Northloop Support (fictional).

SYNTHETIC DATA ONLY. No real company, customer, or support data is ever
used. Every session is fabricated from a seeded PRNG so the same seed
always yields the same corpus, byte-for-byte.

The corpus is a fictional support-ops agent's session log. Early sessions
state explicit RULES, several sessions contain repeated WORKED EXAMPLES
showing a handling pattern (never stated as a rule), and the rest is
distractor chatter about unrelated operations.

Each content item carries three renderings, because the three memory
designs in ``memory_designs.py`` store the same sessions differently:

  text        the full wording, as said in the session
  summary     a short per-session summary paraphrase (detail is lost:
              numbers and exact steps are routinely dropped)
  note_parts  observation fragments, in time order, as a note-taker
              following the session might have split them

Item ids are stable: rules are ``R1``..``R4``, worked examples are
``P1-*`` (pattern 1) and ``P2-*`` (pattern 2), chatter is ``C*``.
"""

from __future__ import annotations

import json
import random
from typing import Dict, List

DEFAULT_SEED = 42

# ---------------------------------------------------------------- rules
# Each rule: id, full text, summary paraphrase, chained-note fragments.
RULES: List[Dict] = [
    {
        "id": "R1",
        "text": ("Policy stated by the team lead: orders over $500 need a "
                 "manager note before refund. Refunds at or under $500 "
                 "can be processed directly."),
        "summary": ("The team discussed refunds for large orders and "
                    "noted that a manager note is involved before "
                    "processing them."),
        "note_parts": [
            "Observation: a refund rule was mentioned — orders over a "
            "threshold need a manager note before refund.",
            "Linked observation, noted right after: the threshold for "
            "the manager-note refund rule is $500.",
        ],
    },
    {
        "id": "R2",
        "text": ("Policy stated by the team lead: orders delivered more "
                 "than 30 days ago are not eligible for a refund; offer "
                 "store credit instead. Orders delivered within 30 days "
                 "can be refunded directly."),
        "summary": ("Refund eligibility for older deliveries was "
                    "covered, and the store credit option was mentioned "
                    "for orders outside the eligibility window."),
        "note_parts": [
            "Observation: older delivered orders are not eligible for "
            "a refund; store credit was mentioned instead.",
            "Linked observation, noted right after: the refund "
            "eligibility window discussed was 30 days since delivery.",
        ],
    },
    {
        "id": "R3",
        "text": ("Policy stated by the team lead: damaged items get a "
                 "free replacement before any refund is offered. Only "
                 "offer a refund for a damaged item if the customer "
                 "refuses the replacement."),
        "summary": ("Damaged-item handling was covered, with a "
                    "replacement discussed as the first step before "
                    "other options."),
        "note_parts": [
            "Observation: damaged items get a free replacement before "
            "any refund is offered.",
            "Linked observation: for damaged items, a refund comes "
            "only if the customer refuses the replacement.",
        ],
    },
    {
        "id": "R4",
        "text": ("Policy stated by the team lead: billing disputes must "
                 "be escalated to the billing team. Never refund a "
                 "billing dispute directly."),
        "summary": ("Billing disputes were discussed; they are routed "
                    "to a specialist team rather than handled on the "
                    "support desk."),
        "note_parts": [
            "Observation: billing disputes must be escalated, never "
            "refunded directly by support.",
            "Linked observation: billing disputes go to the billing "
            "team, per the escalation note.",
        ],
    },
]

# ------------------------------------------------------- worked examples
# Pattern 1: a repeat / second-time fault is moved to the priority queue.
# Pattern 2: a delivery more than 5 days late gets the shipping fee
# refunded. Neither pattern is ever stated as a rule anywhere.
EXAMPLES: List[Dict] = [
    {
        "id": "P1-1",
        "pattern": "P1",
        "text": ("Worked example: a customer reported the same charger "
                 "fault for the second time. Handling shown: the ticket "
                 "was moved to the priority queue and a senior "
                 "technician was assigned."),
        "summary": ("A repeat charger fault case was handled during "
                    "the session."),
        "note_parts": [
            "Observation: a customer reported the same charger fault "
            "for the second time.",
            "Linked observation: that repeat case was moved to the "
            "priority queue with a senior technician assigned.",
        ],
    },
    {
        "id": "P1-2",
        "pattern": "P1",
        "text": ("Worked example: a customer said their headset had "
                 "failed again, the second time this month. Handling "
                 "shown: the ticket was moved to the priority queue."),
        "summary": ("A headset case involving a repeat failure was "
                    "worked through."),
        "note_parts": [
            "Observation: a headset failed again, the second time "
            "this month, in this worked case.",
            "Linked observation: the repeat headset case was moved "
            "to the priority queue.",
        ],
    },
    {
        "id": "P1-3",
        "pattern": "P1",
        "text": ("Worked example: a repeat issue — a monitor flicker "
                 "reported for the third time. Handling shown: the "
                 "ticket was moved to the priority queue and flagged "
                 "for a senior review."),
        "summary": ("A monitor flicker case that kept coming back was "
                    "reviewed."),
        "note_parts": [
            "Observation: a monitor flicker was reported for the "
            "third time, a repeat issue.",
            "Linked observation: the repeat monitor case was moved "
            "to the priority queue for senior review.",
        ],
    },
    {
        "id": "P2-1",
        "pattern": "P2",
        "text": ("Worked example: a package arrived 6 days late. "
                 "Handling shown: the shipping fee was refunded — "
                 "recorded as a shipping fee refund — and the customer "
                 "was apologised to."),
        "summary": ("A late delivery case was handled during the "
                    "session."),
        "note_parts": [
            "Observation: a package arrived 6 days late in this "
            "worked case.",
            "Linked observation: for that late package, a shipping "
            "fee refund was issued.",
        ],
    },
    {
        "id": "P2-2",
        "pattern": "P2",
        "text": ("Worked example: a parcel was 8 days late reaching "
                 "the customer. Handling shown: a shipping fee refund "
                 "was issued, described as refunding the shipping fee."),
        "summary": ("Another late parcel case was worked through."),
        "note_parts": [
            "Observation: a parcel was 8 days late in this worked "
            "case.",
            "Linked observation: a shipping fee refund was issued "
            "for the late parcel.",
        ],
    },
    {
        "id": "P2-3",
        "pattern": "P2",
        "text": ("Worked example: a delivery turned up 7 days late. "
                 "Handling shown: the agent refunded the shipping fee "
                 "(a shipping fee refund) and logged the delay."),
        "summary": ("A delayed delivery case was closed out."),
        "note_parts": [
            "Observation: a delivery turned up 7 days late in this "
            "worked case.",
            "Linked observation: the shipping fee was refunded for "
            "that late delivery.",
        ],
    },
]

_CHATTER_TOPICS = [
    "The team swapped weekend rota preferences and joked about the "
    "coffee machine on the third floor.",
    "Someone asked about the new ticket labels and the office "
    "recycling bins.",
    "The standup covered parking permits, a birthday, and the "
    "upcoming office move.",
    "A question about holiday cover and the shared snack drawer "
    "took up the last few minutes.",
    "The team chatted about the internal newsletter and a charity "
    "bake sale.",
    "There was small talk about train delays and the weather turning "
    "colder this week.",
]

# Session plan: (list of item ids to include, in order). Rules appear
# only in early sessions; examples repeat across sessions; the rest of
# each session is chatter.
_SESSION_PLAN = [
    ["R1"],
    ["R2"],
    ["P1-1"],
    ["R3", "P2-1"],
    ["R4"],
    ["P1-2", "P2-2"],
    ["P1-3"],
    ["P2-3"],
    [],
    [],
    [],
    [],
]

_ITEM_INDEX = {item["id"]: item for item in RULES + EXAMPLES}


def generate_sessions(seed: int = DEFAULT_SEED) -> List[Dict]:
    """Return the synthetic sessions, deterministic for ``seed``."""
    rng = random.Random(seed)
    sessions: List[Dict] = []
    chatter_n = 0
    for idx, item_ids in enumerate(_SESSION_PLAN):
        items: List[Dict] = []
        for item_id in item_ids:
            src = _ITEM_INDEX[item_id]
            item = {"id": src["id"], "kind": (
                "rule" if item_id.startswith("R") else "example"),
                "text": src["text"], "summary": src["summary"],
                "note_parts": list(src["note_parts"])}
            if "pattern" in src:
                item["pattern"] = src["pattern"]
            items.append(item)
        # Two chatter items per session, drawn deterministically.
        for _ in range(2):
            chatter_n += 1
            topic = _CHATTER_TOPICS[rng.randrange(len(_CHATTER_TOPICS))]
            items.append({
                "id": f"C{chatter_n}", "kind": "chatter",
                "text": f"Chatter: {topic}",
                "summary": "General team chatter.",
                "note_parts": [f"Observation: {topic}"],
            })
        sessions.append({
            "session_id": idx + 1,
            "day": idx + 1,
            "items": items,
        })
    return sessions


def sessions_to_json(sessions: List[Dict]) -> str:
    return json.dumps({"sessions": sessions}, sort_keys=True) + "\n"
