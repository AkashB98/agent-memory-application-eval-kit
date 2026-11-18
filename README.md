# agent-memory-application-eval-kit

**Agent memory, evaluated by application, not recall: three memory designs are built from the same session corpus, and the headline metric is whether a fixed agent policy can actually *act* on what each design retrieves — with retrieval recall reported alongside, so the gap between finding a memory and using it is measured, not assumed.**

Most memory benchmarks ask whether the right card came back. That is the easy half. A memory can be retrieved and still be useless: a summary that kept the topic but dropped the $500 threshold, a note chain that surfaces the case but not its outcome. This project is the evaluation-engineering answer to that gap — the work applied-AI teams actually do when they choose a memory design: build several designs from **one** corpus, hold the agent **fixed**, generate the test probes **separately** from the corpus, and score the *decision* each design's memory supports, per probe family, with golden evals pinning the whole run so a changed design fails loudly instead of quietly changing the story.

This kit is inspired by "RAG in a Trenchcoat" (BRIDGE, arXiv:2611.22179), which evaluates retrieval by downstream use. It is **not** a replication: the corpus, designs, probes, agent, and scoring here are original, and none of that paper's numbers are used anywhere in this project.

> **Synthetic data only.** Every session and probe is fabricated by seeded generators for a fictional support operation (**Northloop Support**). No real company, customer, or support data is used anywhere in this project.

> **What this does not measure.** The agent is a deterministic scripted stand-in — a single fixed decision function over retrieved text, not a language model. The kit measures whether retrieved context *carries enough for the policy to act on a rule or a pattern*. It says nothing about how an LLM would behave with the same memory.

Stdlib-only Python. Zero network, zero API keys, zero external dependencies.

## Quickstart

```bash
# 1. Generate the synthetic session corpus (12 sessions, seed 42)
python3 cli.py generate --out corpus.json

# 2. Run the full eval: 3 memory designs x 22 probes -> JSON report
python3 cli.py run --out report.json

# 3. CI gate: exit 0 = report matches the golden eval expectations,
#    1 = headline mismatch, 2 = bad input
python3 cli.py check --report report.json

# 4. One-command end-to-end demo (generate -> build -> retrieve ->
#    decide -> score -> check)
python3 demo.py
```

## The measured result (seed 42 corpus, seed 777 probes, top-3 retrieval)

Application accuracy — the headline. 14 rule-application probes, 8 pattern-induction probes:

| Memory design | Cards | Rule application | Pattern induction | Overall |
|---|---|---|---|---|
| `atomic_facts` | 10 | **0.8571** (12/14) | **1.0000** (8/8) | 0.9091 |
| `block_summaries` | 12 | 0.5714 (8/14) | 0.5000 (4/8) | 0.5455 |
| `chained_notes` | 20 | 0.7143 (10/14) | 0.5000 (4/8) | 0.6364 |

Retrieval recall of the needed rule/example, reported alongside:

| Memory design | Rule recall | Pattern recall |
|---|---|---|
| `atomic_facts` | 0.5714 | 1.0000 |
| `block_summaries` | 0.7143 | 1.0000 |
| `chained_notes` | 0.7143 | 1.0000 |

The designs **do** split, and the split is the finding: on pattern induction, `block_summaries` and `chained_notes` retrieve the needed worked examples **perfectly (recall 1.0000)** and still apply them only half the time (accuracy 0.5000) — the summaries kept the case but dropped the handling, and the note chains surface the case notes ahead of the outcome notes, so the fixed policy never sees repeated evidence of what was *done*. On rules the ranking inverts against recall too: `atomic_facts` has the *lowest* rule recall (0.5714) and the *highest* rule accuracy (0.8571), because several probes are negative cases a direct-refund default answers correctly, while the summaries' higher recall still fails whenever the paraphrase dropped the threshold or the escalation step. **Recall ≠ application, in both directions** — that is the result this kit exists to produce, and it is reported exactly as measured: the generator and agent were not re-tuned after the first full run.

Two honest failure notes from the per-probe rows: the two rule probes `atomic_facts` misses (the over-$500 manager-note cases) are pure retrieval misses — the rule card never reaches the top 3, crowded out by cards sharing the probe's delivery wording; and the chained design's store-credit cases retrieve both linked notes yet the fixed policy's window extraction does not join the threshold across the link. Both are pinned in the report rather than explained away.

## How it works

**One corpus, three designs.** `corpus.py` fabricates 12 sessions of a fictional support-ops agent (seed 42): four explicit **rules** stated in early sessions (a $500 manager-note threshold for refunds, a 30-day refund-eligibility window with store credit beyond it, free replacement first for damaged items, billing disputes escalated — never refunded), six **worked examples** showing two patterns that are never stated as rules (a repeat fault is moved to the priority queue; a delivery more than 5 days late gets its shipping fee refunded), and distractor chatter. `memory_designs.py` builds three stores from those same sessions: **atomic_facts** (one extracted fact/rule/example per card, chatter dropped), **block_summaries** (one summary block per session — the paraphrase is all that survives), and **chained_notes** (observation notes linked in time order, one item sometimes split across two linked notes).

**Retrieval.** Every design answers the same query interface. Retrieval is keyword overlap + hashed term-vector cosine similarity: distinct query terms found in the card, plus the cosine between 64-slot hashed term-count vectors. Top 3 cards per probe, ties broken on card id, fully deterministic.

**One fixed agent.** `agent.py` is a single decision function that reads ONLY the retrieved memory texts and the probe text. It extracts what it needs from the text in front of it — a dollar threshold stated near a manager-note rule, a day window stated near store credit, an escalation step, a replacement step — and it treats a pattern as learned only on *repeated* evidence (the same handling appearing at least twice in the retrieved text). It contains no branch on which design produced the memory; a unit test and golden eval E4 grep the module's source for design names to keep that true.

**Probes, generated separately.** `probes.py` is a separate module with its own seed (777) and its own templates: 14 **rule-application** probes (a scenario whose correct action depends on applying a remembered rule — including negative cases where the rule's condition does not hold) and 8 **pattern-induction** probes (a new case following a worked-example pattern, or a near case that does not). Each probe carries a gold decision and the corpus item ids that count as a recall hit.

**Scoring.** `evaluator.py` reports application accuracy per design × probe family as the headline, retrieval recall alongside it, and a per-probe row (gold, decision, correct, recall hit, retrieved card ids) for every miss you want to inspect. The report contains no timestamps, so its canonical JSON is byte-stable: md5 `088aa249c7bf202303e418798070899a`, byte-identical across 3 verified CLI runs.

## Architecture

| Module | Job |
|---|---|
| `corpus.py` | Deterministic synthetic session corpus (seed 42): 4 explicit rules in early sessions, 6 worked examples across 2 unstated patterns, distractor chatter; each item carries its full text, a summary paraphrase, and chained-note fragments |
| `probes.py` | The evaluation probes (separate module, seed 777): 14 rule-application + 8 pattern-induction probes, each with a gold decision and needed corpus item ids |
| `memory_designs.py` | The three stores built from the same corpus — `atomic_facts`, `block_summaries`, `chained_notes` — behind one query interface |
| `retrieval.py` | keyword overlap + hashed term-vector cosine similarity, top-k with deterministic tie-breaking |
| `agent.py` | The one fixed agent policy: a deterministic decision function over retrieved text only; no design-name branching (grep-tested) |
| `evaluator.py` | Builds each store, retrieves top 3 per probe, runs the fixed policy, scores application accuracy per design × family plus retrieval recall, and emits the byte-stable report |
| `cli.py` | `generate` / `run` (full eval → JSON report) / `check` (CI exit 0 = matches golden expectations, 1 = mismatch, 2 = bad input) / `demo` |
| `demo.py` | End-to-end narrative with asserts: determinism, store sizes, headline table, report md5 stability, check exit codes |
| `fixtures/` | The seeded corpus (`sample_corpus.json`) and the full seeded eval report (`sample_report.json`) |

## Evals

`python3 evals/run_evals.py` → **8/8 golden evals**, report committed at `evals/eval_report.json` (md5 `8f74bbddd090628aee9a5bb1f0198413`, byte-identical across 3 verified runs). The golden expectations live in `evals/expected.json` and were recorded from the first full run:

- **E1** corpus determinism — seed 42 session JSON pinned
- **E2** probes deterministic and separate (seed 777; 14 rule + 8 pattern)
- **E3** store sizes pinned (10 atomic / 12 block / 20 chained cards)
- **E4** agent module has no design-name branching (source grep)
- **E5** headline metrics equal the golden expectations, exactly as recorded
- **E6** recall ≠ application pinned (block/chained pattern recall 1.0, accuracy 0.5)
- **E7** report md5-stable across 3 runs
- **E8** CLI `check` exit codes 0 / 1 / 2

Unit tests: `python3 -m unittest discover -s tests` → **43 hermetic tests**, including a no-network enforcement test (sockets stubbed), the agent no-design-branching grep test, hand-built agent cases for every rule and both patterns (including the repeated-evidence requirement), corpus/probe determinism and separation, store construction, report determinism with an md5-stability test across 3 runs, and CLI exit codes.

## Development loop — what the checks actually caught

1. **A test's own premise was wrong, and fixing it made the suite better.** The first "every card records its sources" test failed on the summary blocks for sessions 9–12 — correctly: those sessions are chatter-only, so their blocks legitimately have no source items. The test now pins exactly that (empty sources for chatter-only blocks, non-empty everywhere else) instead of asserting a blanket rule the design never promised.
2. **The first full run was kept, not tuned.** The measured table above is the first complete run's output. The misses it contains — a rule card crowded out of the top 3 by delivery-wording overlap, a threshold split across two linked notes that the policy does not join — are the kind of failures a memory eval exists to surface, so they are pinned by the golden evals and documented here rather than engineered away by re-tuning the generator until the table looked cleaner.

## Scope and honest limits

- **The agent is a scripted stand-in, not an LLM.** Its parsing is literal: it finds thresholds and steps stated in words it knows, and it cannot paraphrase-match, infer a missing number, or join facts split across cards beyond its fixed windows. A real model would fail differently — probably better on paraphrase, worse on consistency. The kit compares *memory designs under a fixed reader*; it does not rank readers.
- **One small corpus, two patterns, four rules.** 12 sessions and 22 probes are enough to demonstrate the method and pin it with evals, not enough to generalise the ranking. The designs' ordering here is a property of this corpus and this reader, and the README claims the method, not a universal winner.
- **Retrieval is a small deterministic stand-in.** Keyword overlap + hashed term-vector cosine similarity has no stemming and no semantics: "order" and "orders" are different terms, and wording overlap can crowd out the needed card (it does, twice). That weakness is part of what the eval measures, and it is held constant across designs.
- **Recall is scored against design provenance.** A card counts as a recall hit if it was *built from* the needed item — even when, as with the summaries, its text dropped the detail that mattered. That is deliberate: it is exactly how a design can post perfect recall and failing application.

## POC framing

As a proof of concept for a forward-deployed engagement, this kit is the evaluation harness you would put in front of a customer before arguing about memory architecture: bring your own session corpus in the same shape, keep the agent and probes fixed, and the design choice becomes a measured table — accuracy by use case family, recall alongside — instead of a matter of taste. The deliverable is the discipline: designs compared on what the agent can *do* with their memory, probes the corpus never saw, and a check gate that turns "the memory got worse" into a failing build.

## Why this project

It takes the author's applied-AI building practice — agent tooling, evaluation harnesses, analytics discipline from GA4/KPI work — and rebuilds a live research question (how should an agent remember?) as an evaluation-engineering artifact: one corpus, three designs, a fixed reader, separately generated probes, and golden evals. The same discipline a forward-deployed engineer brings to a customer problem: make the comparison fair, make the outputs reproducible, and make the failure modes exit codes.
