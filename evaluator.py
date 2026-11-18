"""Evaluator: run every probe against every memory design.

For each design, the evaluator builds that design's store from the
same corpus, retrieves the top 3 cards per probe using keyword
overlap + hashed term-vector cosine similarity, hands ONLY the
retrieved card texts to the one fixed agent policy, and scores:

  application accuracy   did the agent's decision match the gold?
                         (the headline metric, per design x family)
  retrieval recall       did any retrieved card come from the probe's
                         needed corpus item? (reported alongside, so
                         recall and application can be compared)

The report is a plain dict of counts, accuracies, and per-probe rows.
It contains no timestamps, so its canonical JSON is byte-stable.
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent  # noqa: E402
from memory_designs import DESIGNS, build_store, retrieve  # noqa: E402

TOP_K = 3
FAMILIES = ("rule_application", "pattern_induction")


def _accuracy(rows: List[Dict]) -> float:
    if not rows:
        return 0.0
    return round(sum(1 for r in rows if r["correct"]) / len(rows), 4)


def evaluate(sessions: List[Dict], probes: List[Dict]) -> Dict:
    designs: Dict[str, Dict] = {}
    for design in DESIGNS:
        cards = build_store(design, sessions)
        rows: List[Dict] = []
        for probe in probes:
            hits = retrieve(cards, probe["text"], top_k=TOP_K)
            decision = agent.decide([c["text"] for c in hits],
                                    probe["text"])
            hit_ids = {item_id for c in hits
                       for item_id in c["source_item_ids"]}
            rows.append({
                "probe_id": probe["id"],
                "family": probe["family"],
                "gold": probe["gold"],
                "decision": decision,
                "correct": decision == probe["gold"],
                "recall_hit": bool(hit_ids & set(probe["needed_ids"])),
                "retrieved_card_ids": [c["card_id"] for c in hits],
            })
        by_family = {}
        for family in FAMILIES:
            fam_rows = [r for r in rows if r["family"] == family]
            by_family[family] = {
                "accuracy": _accuracy(fam_rows),
                "correct": sum(1 for r in fam_rows if r["correct"]),
                "total": len(fam_rows),
                "retrieval_recall": round(
                    sum(1 for r in fam_rows if r["recall_hit"])
                    / len(fam_rows), 4) if fam_rows else 0.0,
            }
        designs[design] = {
            "card_count": len(cards),
            "overall_accuracy": _accuracy(rows),
            "by_family": by_family,
            "probes": rows,
        }
    return {
        "corpus_sessions": len(sessions),
        "probe_count": len(probes),
        "top_k": TOP_K,
        "designs": designs,
    }


def headline(report: Dict) -> Dict:
    """The headline table: accuracy per design x probe family."""
    return {
        design: {family: data["by_family"][family]["accuracy"]
                 for family in FAMILIES}
        for design, data in report["designs"].items()
    }
