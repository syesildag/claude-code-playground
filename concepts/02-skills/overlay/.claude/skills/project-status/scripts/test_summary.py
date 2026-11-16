#!/usr/bin/env python3
"""Print a one-line test summary.

Always exits 0: a non-zero exit inside a skill's !`command` would abort the whole skill invocation.
"""

import subprocess
import sys

try:
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True, timeout=120)
    lines = [line for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
    ran = next((line for line in lines if line.startswith("Ran ")), "Ran ? tests")
    print(f"{ran} → {lines[-1] if lines else 'no output'}")
except Exception as exc:  # noqa: BLE001 - never fail the skill
    print(f"could not run tests: {exc}")
