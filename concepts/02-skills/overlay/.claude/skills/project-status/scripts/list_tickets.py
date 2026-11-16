#!/usr/bin/env python3
"""Print one line per ticket: id and title. Always exits 0."""

from pathlib import Path

tickets = sorted(Path("tickets").glob("T*.md"))
for ticket in tickets:
    first = ticket.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    print(f"  - {first}")
if not tickets:
    print("  (none)")
