#!/usr/bin/env python3
"""Deterministic stop gates for the TDD workflow.

Each gate prints PASS or FAIL with evidence, saves it to work/gates/<gate>.txt, and exits 0 on PASS, 1 on FAIL.
"I ran the tests and they passed" is a claim. This script's output is a gate.

  python3 scripts/gate.py baseline   record which tests already fail before any change
  python3 scripts/gate.py red        new tests exist and fail; no test module failed to import
  python3 scripts/gate.py green      every RED test now passes and nothing that passed before broke
  python3 scripts/gate.py review     work/review.md has a verdict and no [blocking] findings
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

GATES = Path("work") / "gates"


def run_tests() -> tuple[dict[str, str], str]:
    proc = subprocess.run([sys.executable, "-m", "unittest"], capture_output=True, text=True, timeout=300)
    out = proc.stdout + proc.stderr
    status = {m.group(2): m.group(1) for m in re.finditer(r"^(FAIL|ERROR): \S+ \(([\w.]+)\)", out, re.M)}
    return status, out


def exception_lines(out: str, ids: set[str]) -> list[str]:
    """For each failing test in `ids`: its name and exception line, e.g. 'test_x → AssertionError: 0 != 2'.

    That's the evidence of *why* a test fails. In a traceback the exception line is the one that starts at column 0
    with the exception class name. Assertion diffs (`- … / ? ^`) come after it.
    """
    lines = []
    for block in re.split(r"^={10,}$", out, flags=re.M)[1:]:
        header = re.search(r"^(FAIL|ERROR): (\S+) \(([\w.]+)\)", block, re.M)
        if not header or header.group(3) not in ids:
            continue
        exc = re.search(r"^([A-Za-z_][\w.]*(?:Error|Exception|Warning)\b.*)$", block, re.M)
        lines.append(f"{header.group(1)} {header.group(2)}  →  {exc.group(1)[:160] if exc else '?'}")
    return lines


def load(name: str) -> dict:
    path = GATES / f"{name}.json"
    if not path.exists():
        sys.exit(f"gate: run `python3 scripts/gate.py {name}` first")
    return json.loads(path.read_text(encoding="utf-8"))


def finish(name: str, ok: bool, summary: str, evidence: list[str], data: dict | None = None) -> int:
    GATES.mkdir(parents=True, exist_ok=True)
    verdict = "PASS" if ok else "FAIL"
    text = f"GATE {name.upper()}: {verdict}  ({datetime.now():%Y-%m-%d %H:%M:%S})\n{summary}\n" + \
        "".join(f"  - {line}\n" for line in evidence)
    (GATES / f"{name}.txt").write_text(text, encoding="utf-8")
    if data is not None:
        (GATES / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(text, end="")
    return 0 if ok else 1


def gate_baseline() -> int:
    status, _ = run_tests()
    return finish("baseline", True, f"{len(status)} test(s) already failing before any change.",
                  sorted(status), {"failing": status})


def gate_red() -> int:
    baseline = load("baseline")["failing"]
    status, out = run_tests()
    new = {tid: s for tid, s in status.items() if tid not in baseline}
    broken_modules = [tid for tid in new if "_FailedTest" in tid]
    if broken_modules:
        return finish("red", False, "A test module failed to import (syntax error, or a missing name imported at "
                      "module level). Import new names inside the test methods instead.", broken_modules)
    if not new:
        return finish("red", False, "No new failing test. RED needs at least one test that fails before the change.",
                      [])
    return finish("red", True, f"{len(new)} new failing test(s):", exception_lines(out, set(new)) or sorted(new),
                  {"new_failing": sorted(new)})


def gate_green() -> int:
    baseline = load("baseline")["failing"]
    red = load("red")["new_failing"]
    status, out = run_tests()
    still_red = [tid for tid in red if tid in status]
    regressions = [tid for tid in status if tid not in baseline and tid not in red]
    ok = not still_red and not regressions
    evidence = [f"still failing (RED): {t}" for t in still_red] + [f"regression: {t}" for t in regressions]
    summary = f"{len(red)} RED test(s) now pass; no regressions." if ok else "GREEN not reached."
    return finish("green", ok, summary, evidence or [line for line in out.strip().splitlines()[-1:]])


def gate_review() -> int:
    review = Path("work") / "review.md"
    if not review.exists():
        return finish("review", False, "work/review.md does not exist.", [])
    text = review.read_text(encoding="utf-8")
    blocking = [line.strip() for line in text.splitlines() if re.search(r"\[blocking\]", line, re.I)]
    has_verdict = re.search(r"VERDICT:\s*(PASS|FAIL)", text)
    ok = bool(has_verdict) and not blocking
    summary = f"{len(blocking)} blocking finding(s)." if has_verdict else "No VERDICT line in work/review.md."
    return finish("review", ok, summary, blocking)


def main() -> int:
    gates = {"baseline": gate_baseline, "red": gate_red, "green": gate_green, "review": gate_review}
    if len(sys.argv) != 2 or sys.argv[1] not in gates:
        print(__doc__)
        return 2
    return gates[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
