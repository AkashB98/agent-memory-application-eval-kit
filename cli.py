"""CLI: generate | run | check.

SYNTHETIC DATA ONLY — Northloop Support is a fictional operation and
every session and probe handled here is fabricated sample data.

Exit codes:
  check : 0 = report matches the golden eval expectations,
          1 = report does not match, 2 = bad input
  others: 0 = success, 2 = usage / IO error
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corpus import generate_sessions, sessions_to_json  # noqa: E402
from evaluator import evaluate, headline  # noqa: E402
from probes import generate_probes  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_ERROR = 0, 1, 2
EXPECTED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "evals", "expected.json")


def canonical(payload) -> str:
    return json.dumps(payload, sort_keys=True)


def build_report() -> dict:
    return evaluate(generate_sessions(), generate_probes())


def _write_out(args, text: str, summary: str) -> int:
    if getattr(args, "out", None):
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
            return EXIT_ERROR
        print(summary)
    else:
        print(text, end="")
    return EXIT_OK


def cmd_generate(args) -> int:
    sessions = generate_sessions(seed=args.seed)
    return _write_out(args, sessions_to_json(sessions),
                      f"generated {len(sessions)} synthetic sessions "
                      f"(seed={args.seed}) -> {args.out}")


def cmd_run(args) -> int:
    report = build_report()
    return _write_out(args, canonical(report) + "\n",
                      f"eval report ({report['probe_count']} probes x "
                      f"{len(report['designs'])} designs) -> {args.out}")


def _load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except (ValueError, OSError) as exc:
        return None, f"cannot read {path}: {exc}"


def cmd_check(args) -> int:
    report, err = _load_json(args.report)
    if err:
        print(f"error: {err}")
        return EXIT_ERROR
    if not isinstance(report, dict) or "designs" not in report:
        print("error: report has no 'designs' section")
        return EXIT_ERROR
    expected, err = _load_json(EXPECTED_PATH)
    if err:
        print(f"error: {err}")
        return EXIT_ERROR
    try:
        actual = headline(report)
    except (KeyError, TypeError) as exc:
        print(f"error: malformed report: {exc}")
        return EXIT_ERROR
    if actual == expected.get("headline"):
        print(f"check PASS: headline matches golden expectations "
              f"{actual}")
        return EXIT_OK
    print(f"check FAIL: headline {actual} != golden "
          f"{expected.get('headline')}")
    return EXIT_FAIL


def cmd_demo(args) -> int:
    import demo as demo_mod
    try:
        demo_mod.main()
    except AssertionError as exc:
        print(f"demo FAILED: {exc}", file=sys.stderr)
        return EXIT_FAIL
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent-memory-application-eval-kit",
        description="Evaluate agent memory designs by application, "
                    "not recall (Northloop Support sample data).")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="generate the synthetic corpus")
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--out", default=None)
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("run", help="run the full eval -> JSON report")
    r.add_argument("--out", default=None)
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("check", help="CI gate: exit 0 match / 1 mismatch "
                                     "/ 2 bad input")
    c.add_argument("--report", required=True)
    c.set_defaults(func=cmd_check)

    sub.add_parser("demo", help="run the end-to-end demo").set_defaults(
        func=cmd_demo)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
