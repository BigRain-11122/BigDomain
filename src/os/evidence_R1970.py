# -*- coding: utf-8 -*-
"""R1970 curation cold-board suite evidence driver.

Runs test_curation.py twice via subprocess, captures stdout as
bytes, decodes utf-8, normalizes EOL to LF, and writes both runs
into one evidence log (R1880-family driver discipline: the driver
is the single writer; child stdout is always captured then
re-landed, never inherited). The VERDICT line is derived from the
actual child exit codes and SUITE lines - never hardcoded.
"""
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))  # repo root
SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_curation.py")
OUT = os.path.join(ROOT, "qa", "curation-coldboard-R1970.log")

parts = []
parts.append("R1970 curation cold_board delivery evidence")
parts.append("suite: src/sandbox/ledger/test_curation.py")
parts.append("criteria pre-registered in state/queue/explore.md"
            " (claim written before code; honesty law)")
parts.append("")

results = []
for tag in ("run1", "run2"):
    p = subprocess.run([sys.executable, SUITE],
                       capture_output=True)
    out = p.stdout.decode("utf-8", errors="replace")
    err = p.stderr.decode("utf-8", errors="replace")
    out_lf = out.replace("\r\n", "\n")
    parts.append("--- %s (exit=%d) ---" % (tag, p.returncode))
    parts.append(out_lf.rstrip("\n"))
    if err.strip():
        parts.append("[stderr] " + err.strip())
    parts.append("")
    suite_ok = ("SUITE PASS 24/24" in out_lf
                and p.returncode == 0
                and "FAIL" not in out_lf)
    results.append((tag, p.returncode, suite_ok))

both_pass = all(r[2] for r in results)
parts.append("VERDICT: " + ("PASS" if both_pass else "FAIL")
             + " (runs: " + "; ".join(
                 "%s exit=%d suite_ok=%s" % r
                 for r in results) + ")")
parts.append("")

with io.open(OUT, "w", encoding="utf-8", newline="\n") as h:
    h.write("\n".join(parts))
print("evidence written:", OUT, "verdict:",
      "PASS" if both_pass else "FAIL")
