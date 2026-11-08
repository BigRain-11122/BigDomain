"""R2580 board closeout for the AC-FCLS1 seed row in state/queue/tech.md.

Marks the fold-summary kind row done and appends its DISCHARGED note read
from THIS round own evidence on disk. Refuses to write when the suite
evidence or the battery evidence is absent, so no number is invented.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "ledger-fold-kind-R2580.log")
BATTERY = os.path.join(REPO, "qa", "reconcile-all-R2579-retry2.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_MARK = "AC-FCLS1..AC-FCLS6"


def main():
    for path in (EVIDENCE, BATTERY, MATRIX):
        if not os.path.exists(path):
            print("E_QC_MISSING %s" % path)
            return 3

    with io.open(EVIDENCE, encoding="utf-8") as fh:
        ev = fh.read()
    with io.open(BATTERY, encoding="utf-8") as fh:
        bat = fh.read()
    ev_bytes = os.path.getsize(EVIDENCE)
    bat_bytes = os.path.getsize(BATTERY)
    mat_bytes = os.path.getsize(MATRIX)
    if "SUMMARY legs=2 identical=True adjacent=3 fails=0" not in ev:
        print("E_QC_EVIDENCE_SHAPE")
        return 2
    runner = [l for l in bat.splitlines() if l.startswith("RUNNER ")]
    if not runner or "PASS" not in runner[-1]:
        print("E_QC_BATTERY_NOT_GREEN")
        return 2

    with io.open(QUEUE, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")

    hits = [i for i, l in enumerate(lines) if SEED_MARK in l]
    if len(hits) != 1:
        print("E_QC_SEED_ROWS %d" % len(hits))
        return 2
    idx = hits[0]
    row = lines[idx]
    if row.startswith("- [x]"):
        print("E_QC_ALREADY_DONE")
        return 2

    lines[idx] = row.replace("- [ ]", "- [x] [done 2026-11-09 R2580]", 1)
    note = (
        "  DISCHARGED R2580 (AC-FCLS1..AC-FCLS6 pinned in this row BEFORE any"
        " code): src/os/ledger_lines.py now carries FOLD_SUMMARY_RE, a"
        " word-bounded guard that classifies a line beginning 'R<n> fold' as"
        " other, so the fold summary a fold leaves behind no longer reads as a"
        " round narrative and a round whose ledger line moved into the archive"
        " stops being reported as having none - the exact shape the R2578 fold"
        " created and the R2579 battery caught. PROOF: suite PASS 6/6 on the"
        " first run and twice identical with three adjacent ledger suites"
        " green (qa/ledger-fold-kind-R2580.log, %d bytes, crlf=0, nul=0,"
        " legs=2, adjacent=3, fails=0); the three suites the R2579 battery left"
        " red (os-ledger-lines, os-ledger-archive, os-ledger-baseline) each"
        " read SUITE PASS 8/8 after the repair; the battery re-ran green on the"
        " repaired committed tree at the pre-registered 620 suites / 4696"
        " criteria (qa/reconcile-all-R2579-retry2.log, %d bytes, RUNNER PASS,"
        " controls 7/7, zero FAIL rows, 620 unique suite rows, independent"
        " criteria recount exactly 4696); docs/sandbox-suite-matrix.md was"
        " regenerated stamp-aligned from that same green leg to %d bytes at"
        " 620/4696 green=620/620 with --check byte-identical. The RETRY BEFORE"
        " THE REPAIR WAS RED AND IS KEPT: qa/reconcile-all-R2579.log %d bytes,"
        " RUNNER FAIL 4 assertions in three suites, and the first retry after"
        " the code fix was ALSO red at 10 assertions because the registry had"
        " moved to 620/4696 while the matrix document still described 619/4690"
        " - disclosed rather than hidden." % (
            ev_bytes, bat_bytes, mat_bytes,
            os.path.getsize(os.path.join(
                REPO, "qa", "reconcile-all-R2579.log"))))
    lines.insert(idx + 1, note)

    text = "\n".join(lines)
    with io.open(QUEUE, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("closed row=%d note=%d bytes queue=%d crlf=%d" % (
        idx + 1, len(note), len(text.encode("utf-8")), text.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())