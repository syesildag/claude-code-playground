#!/usr/bin/env python3
"""Generate work/proof.html: the evidence for a TDD run (gates, diff, review) on one page.

  python3 scripts/proof_page.py tickets/T02-add-priority.md

Everything is HTML-escaped. This page is itself an HTML export, so ticket T04's lesson applies here too.
"""

import subprocess
import sys
from datetime import datetime
from html import escape
from pathlib import Path

GATES = ("baseline", "red", "green", "review")


def run(*cmd: str) -> str:
    return subprocess.run(list(cmd), capture_output=True, text=True).stdout.strip()


def main() -> int:
    ticket = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    title = ticket.read_text(encoding="utf-8").splitlines()[0].lstrip("# ") if ticket and ticket.exists() else "TDD run"
    rows = []
    for gate in GATES:
        path = Path("work/gates") / f"{gate}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else f"GATE {gate.upper()}: MISSING"
        verdict = "pass" if ": PASS" in text.splitlines()[0] else "fail"
        rows.append(f'<tr class="{verdict}"><td>{escape(gate)}</td><td>{verdict.upper()}</td>'
                    f"<td><pre>{escape(text)}</pre></td></tr>")
    review = Path("work/review.md")
    review_html = escape(review.read_text(encoding="utf-8")) if review.exists() else "(no review)"
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True)
    lines = [line for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
    final_tests = lines[-1] if lines else "(no test output)"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Proof: {escape(title)}</title>
<style>
 body{{font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1f2328}}
 table{{border-collapse:collapse;width:100%}} td{{border:1px solid #d0d7de;padding:.4rem;vertical-align:top}}
 tr.pass td:nth-child(2){{color:#1a7f37;font-weight:700}} tr.fail td:nth-child(2){{color:#cf222e;font-weight:700}}
 pre{{white-space:pre-wrap;margin:0;font-size:13px}}
</style></head><body>
<h1>Proof: {escape(title)}</h1>
<p>Generated {datetime.now():%Y-%m-%d %H:%M:%S} · branch <code>{escape(run("git", "branch", "--show-current"))}</code></p>
<h2>Gates</h2><table>{''.join(rows)}</table>
<h2>Final test run</h2><pre>{escape(final_tests)}</pre>
<h2>Diff</h2><pre>{escape(run("git", "diff", "HEAD", "--stat"))}</pre>
<h2>Cold review</h2><pre>{review_html}</pre>
</body></html>
"""
    out = Path("work/proof.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
