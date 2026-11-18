"""Golden evals for agent-memory-application-eval-kit.

SYNTHETIC DATA ONLY (fictional Northloop Support sessions and probes).
Every eval is deterministic: run_evals.py writes eval_report.json and
the file must be byte-identical across runs. No timestamps or temp
paths enter the report — only names, booleans, pinned counts, the
honest headline metrics, and hashes.

The headline eval (E5) asserts the generated report's metrics equal
the values in ``expected.json`` — whatever they honestly are. They
were recorded from the first full run and were NOT tuned towards.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli import EXIT_ERROR, EXIT_FAIL, EXIT_OK, main as cli_main  # noqa: E402
from corpus import generate_sessions, sessions_to_json  # noqa: E402
from evaluator import evaluate, headline  # noqa: E402
from memory_designs import DESIGNS, build_store  # noqa: E402
from probes import generate_probes  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = []


def check(name, passed, detail=""):
    RESULTS.append({"name": name, "passed": bool(passed), "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return passed


def _run_cli(argv):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return cli_main(argv)


def main():
    print("== golden evals: agent-memory-application-eval-kit ==")
    sessions = generate_sessions()
    probes = generate_probes()
    report = evaluate(sessions, probes)

    # E1: corpus determinism (bytes pinned)
    text1 = sessions_to_json(generate_sessions())
    text2 = sessions_to_json(generate_sessions())
    md5 = hashlib.md5(text1.encode()).hexdigest()
    check("E1 corpus determinism (seed=42, 12 sessions)",
          text1 == text2 and len(sessions) == 12,
          f"corpus_md5={md5}")

    # E2: probe determinism and family split (separate seed 777)
    check("E2 probes deterministic (seed=777, 14 rule + 8 pattern)",
          generate_probes() == probes and len(probes) == 22
          and sum(1 for p in probes if p["family"] == "rule_application") == 14
          and sum(1 for p in probes if p["family"] == "pattern_induction") == 8)

    # E3: store sizes per design
    sizes = {d: len(build_store(d, sessions)) for d in DESIGNS}
    check("E3 store sizes (10 atomic / 12 block / 20 chained)",
          sizes == {"atomic_facts": 10, "block_summaries": 12,
                    "chained_notes": 20}, f"{sizes}")

    # E4: the agent module names no design (no design branching)
    with open(os.path.join(ROOT, "agent.py"), encoding="utf-8") as fh:
        agent_source = fh.read().lower()
    check("E4 agent module has no design-name branching",
          all(name not in agent_source for name in
              ("atomic_facts", "block_summaries", "chained_notes")))

    # E5: headline metrics equal the golden expectations, as recorded
    with open(os.path.join(HERE, "expected.json"), encoding="utf-8") as fh:
        expected = json.load(fh)
    actual = headline(report)
    check("E5 headline metrics equal golden expectations",
          actual == expected["headline"],
          json.dumps(actual, sort_keys=True))

    # E6: recall != application, pinned on the block design's patterns
    block = report["designs"]["block_summaries"]["by_family"]["pattern_induction"]
    chained = report["designs"]["chained_notes"]["by_family"]["pattern_induction"]
    check("E6 recall != application (block/chained pattern recall 1.0, "
          "accuracy 0.5)",
          block["retrieval_recall"] == 1.0 and block["accuracy"] == 0.5
          and chained["retrieval_recall"] == 1.0
          and chained["accuracy"] == 0.5,
          f"block recall={block['retrieval_recall']} acc={block['accuracy']}")

    # E7: report md5 stable across 3 runs
    md5s = {hashlib.md5(json.dumps(
        evaluate(generate_sessions(), generate_probes()),
        sort_keys=True).encode()).hexdigest() for _ in range(3)}
    check("E7 report md5-stable across 3 runs", len(md5s) == 1,
          f"report_md5={sorted(md5s)[0]}")

    # E8: CLI check exit codes 0 / 1 / 2
    tmp = tempfile.mkdtemp(prefix="memory-eval-evals-")
    good_path = os.path.join(tmp, "report.json")
    with open(good_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, sort_keys=True) + "\n")
    tampered = json.loads(json.dumps(report))
    tampered["designs"]["atomic_facts"]["by_family"][
        "rule_application"]["accuracy"] = 0.0
    bad_path = os.path.join(tmp, "tampered.json")
    with open(bad_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(tampered, sort_keys=True) + "\n")
    codes = (_run_cli(["check", "--report", good_path]),
             _run_cli(["check", "--report", bad_path]),
             _run_cli(["check", "--report", "/tmp/no-such-report-xyz.json"]))
    check("E8 CLI check exit codes 0/1/2",
          codes == (EXIT_OK, EXIT_FAIL, EXIT_ERROR), f"codes={codes}")

    passed = sum(1 for r in RESULTS if r["passed"])
    total = len(RESULTS)
    summary_doc = {"passed": passed, "total": total,
                   "all_passed": passed == total, "evals": RESULTS}
    with open(os.path.join(HERE, "eval_report.json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(summary_doc, sort_keys=True) + "\n")
    print(f"\n{passed}/{total} evals passed -> evals/eval_report.json")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
