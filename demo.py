"""End-to-end demo: generate -> build stores -> retrieve -> decide ->
score -> check.

SYNTHETIC DATA ONLY (fictional Northloop Support sessions and probes).
Runs fully offline. Every stage asserts; the printed table is the
actual measured result, whatever it is.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import EXIT_FAIL, EXIT_OK, build_report, main as cli_main  # noqa: E402
from corpus import generate_sessions  # noqa: E402
from evaluator import evaluate, headline  # noqa: E402
from memory_designs import DESIGNS, build_store  # noqa: E402
from probes import generate_probes  # noqa: E402


def main() -> None:
    print("== 1. generate synthetic corpus (seed=42) and probes (seed=777) ==")
    sessions = generate_sessions()
    probes = generate_probes()
    assert sessions == generate_sessions(), "corpus must be deterministic"
    assert probes == generate_probes(), "probes must be deterministic"
    assert len(sessions) == 12 and len(probes) == 22
    print(f"   {len(sessions)} sessions, {len(probes)} probes "
          f"(14 rule-application, 8 pattern-induction)")

    print("\n== 2. build the three memory stores from the same corpus ==")
    for design in DESIGNS:
        cards = build_store(design, sessions)
        print(f"   {design}: {len(cards)} cards")

    print("\n== 3. run the eval: one fixed agent policy, all designs ==")
    report = evaluate(sessions, probes)
    again = evaluate(sessions, probes)
    assert report == again, "eval must be deterministic"
    table = headline(report)
    for design in DESIGNS:
        fam = report["designs"][design]["by_family"]
        print(f"   {design}: rule {fam['rule_application']['accuracy']:.2f} "
              f"(recall {fam['rule_application']['retrieval_recall']:.2f}), "
              f"pattern {fam['pattern_induction']['accuracy']:.2f} "
              f"(recall {fam['pattern_induction']['retrieval_recall']:.2f})")
    print(f"   headline: {json.dumps(table, sort_keys=True)}")

    print("\n== 4. report bytes are md5-stable ==")
    blob1 = json.dumps(build_report(), sort_keys=True)
    blob2 = json.dumps(build_report(), sort_keys=True)
    md5 = hashlib.md5(blob1.encode()).hexdigest()
    assert blob1 == blob2
    print(f"   report md5 {md5}")

    print("\n== 5. CLI check gate exit codes ==")
    tmp = tempfile.mkdtemp(prefix="memory-eval-demo-")
    good_path = os.path.join(tmp, "report.json")
    with open(good_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(report, sort_keys=True) + "\n")
    tampered = json.loads(json.dumps(report))
    first = sorted(tampered["designs"])[0]
    tampered["designs"][first]["by_family"]["rule_application"]["accuracy"] = 0.0
    bad_path = os.path.join(tmp, "tampered.json")
    with open(bad_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(tampered, sort_keys=True) + "\n")
    code_ok = cli_main(["check", "--report", good_path])
    code_fail = cli_main(["check", "--report", bad_path])
    code_err = cli_main(["check", "--report", "/tmp/no-such-report-xyz.json"])
    print(f"   matching={code_ok} tampered={code_fail} missing-file={code_err}")
    assert code_ok == EXIT_OK and code_fail == EXIT_FAIL and code_err == 2

    print("\nDemo OK: corpus, stores, retrieval, agent, scoring and "
          "check gate verified.")


if __name__ == "__main__":
    main()
