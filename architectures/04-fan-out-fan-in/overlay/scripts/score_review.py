#!/usr/bin/env python3
"""Score a review file for recall of the issues deliberately planted in the taskboard app.

  python3 scripts/score_review.py work/review.md

A finding counts when one line names the right file and describes the issue (by keyword). Crude, but
deterministic and the same for every architecture. That's what makes the comparison fair.
"""

import re
import sys
from pathlib import Path

PLANTED = [
    ("T01 done counter compares against 'complete'", r"service", r"complete|done.{0,40}(count|stat)|stat.{0,40}done"),
    ("T04 XSS: titles not HTML-escaped", r"report", r"xss|escap|inject|sanitiz"),
    ("T03 non-atomic save can corrupt the board", r"store", r"atomic|truncat|corrupt|partial|data loss|crash"),
    ("N+1: `list` reloads the board once per task", r"cli", r"n\+1|reload|re-?read|get\(|per task|each task|o\(n"),
    ("Convention: export_html has no type hints", r"report", r"type hint|annotat|typed"),
]


def main() -> int:
    if len(sys.argv) != 2 or not Path(sys.argv[1]).exists():
        print(__doc__)
        return 2
    lines = Path(sys.argv[1]).read_text(encoding="utf-8").lower().splitlines()
    found = 0
    for label, file_pattern, issue_pattern in PLANTED:
        hit = any(re.search(file_pattern, line) and re.search(issue_pattern, line) for line in lines)
        found += hit
        print(f"  {'✔' if hit else '✘'} {label}")
    print(f"recall: {found}/{len(PLANTED)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
