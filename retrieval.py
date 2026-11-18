"""Retrieval shared by every memory design.

Retrieval is keyword overlap + hashed term-vector cosine similarity:
a query scores a card by (a) how many distinct query terms appear in
the card, and (b) the cosine similarity between hashed term vectors —
each term is hashed into a fixed 64-slot vector by counting, and the
two count vectors are compared by cosine. That is the whole method;
it is a small deterministic stand-in for semantic search, built only
from the standard library.

Ties break on card id, so retrieval is fully deterministic.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Dict, List

VECTOR_SLOTS = 64
_TOKEN_RE = re.compile(r"[a-z0-9$]+")

STOPWORDS = frozenset({
    "a", "an", "the", "was", "were", "is", "are", "to", "of", "for",
    "and", "or", "in", "on", "by", "with", "what", "should", "do",
    "does", "did", "it", "its", "this", "that", "their", "them",
    "they", "be", "been", "has", "had", "have", "can", "could",
})


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower())
            if t not in STOPWORDS and len(t) > 1]


def hashed_vector(tokens: List[str]) -> List[float]:
    vec = [0.0] * VECTOR_SLOTS
    for tok in tokens:
        digest = hashlib.md5(tok.encode("utf-8")).digest()
        slot = int.from_bytes(digest[:4], "little") % VECTOR_SLOTS
        vec[slot] += 1.0
    return vec


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def score_card(query_tokens: List[str], query_vec: List[float],
               card: Dict) -> float:
    """keyword overlap + hashed term-vector cosine similarity."""
    card_tokens = tokenize(card["text"])
    overlap = len(set(query_tokens) & set(card_tokens))
    return overlap + cosine(query_vec, hashed_vector(card_tokens))


def retrieve(cards: List[Dict], query: str, top_k: int = 3) -> List[Dict]:
    """Return the top-``top_k`` cards for ``query``, deterministically."""
    q_tokens = tokenize(query)
    q_vec = hashed_vector(q_tokens)
    scored = [(score_card(q_tokens, q_vec, card), card["card_id"], card)
              for card in cards]
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [card for _, _, card in scored[:top_k]]
