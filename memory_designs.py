"""Three memory designs built from the same session corpus.

Each design turns the identical sessions into its own store of cards
and answers the same query interface (``retrieve(query, top_k)`` via
the shared retrieval module). The designs differ only in *what a card
contains*:

  atomic_facts     one extracted fact / rule / worked example per card;
                   chatter is dropped at extraction time
  block_summaries  one summary block per session; the summary
                   paraphrase is the card text, so detail the summary
                   dropped is not in memory at all
  chained_notes    observation notes in time order, each note linked
                   to the previous one; a single item may be split
                   across two linked notes

Every card records the corpus item ids it was built from
(``source_item_ids``) purely so the evaluator can score retrieval
recall; the agent never sees them.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retrieval import retrieve as _retrieve  # noqa: E402

DESIGNS = ("atomic_facts", "block_summaries", "chained_notes")


def build_atomic_facts(sessions: List[Dict]) -> List[Dict]:
    cards = []
    for session in sessions:
        for item in session["items"]:
            if item["kind"] == "chatter":
                continue
            cards.append({
                "card_id": f"atomic-{item['id']}",
                "session_id": session["session_id"],
                "text": item["text"],
                "source_item_ids": [item["id"]],
            })
    return cards


def build_block_summaries(sessions: List[Dict]) -> List[Dict]:
    cards = []
    for session in sessions:
        parts = [item["summary"] for item in session["items"]
                 if item["kind"] != "chatter"]
        text = (f"Session {session['session_id']} summary: "
                + " ".join(parts)) if parts else \
            f"Session {session['session_id']} summary: team operations."
        cards.append({
            "card_id": f"block-{session['session_id']}",
            "session_id": session["session_id"],
            "text": text,
            "source_item_ids": [item["id"] for item in session["items"]
                                if item["kind"] != "chatter"],
        })
    return cards


def build_chained_notes(sessions: List[Dict]) -> List[Dict]:
    cards = []
    previous_id = None
    for session in sessions:
        for item in session["items"]:
            if item["kind"] == "chatter":
                continue
            for part_idx, part in enumerate(item["note_parts"]):
                card_id = f"chain-{item['id']}-{part_idx + 1}"
                link = (f" (follows {previous_id})"
                        if previous_id else " (first note)")
                cards.append({
                    "card_id": card_id,
                    "session_id": session["session_id"],
                    "text": part + link,
                    "source_item_ids": [item["id"]],
                })
                previous_id = card_id
    return cards


_BUILDERS = {
    "atomic_facts": build_atomic_facts,
    "block_summaries": build_block_summaries,
    "chained_notes": build_chained_notes,
}


def build_store(design: str, sessions: List[Dict]) -> List[Dict]:
    if design not in _BUILDERS:
        raise ValueError(f"unknown memory design: {design}")
    return _BUILDERS[design](sessions)


def retrieve(cards: List[Dict], query: str, top_k: int = 3) -> List[Dict]:
    """The one query interface every design answers."""
    return _retrieve(cards, query, top_k=top_k)
