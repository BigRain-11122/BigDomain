"""R2515 board writer: discharge tech row 552 and seed the next measured gap.

Dry run by default (writes nothing, prints the prediction). --execute writes
once through one atomic replace, proves the predicted size and reads the row
back. Refuses if the row is not the exact seed this round claimed, if a CRLF
transport appears (the file is LF today and must stay LF), or if the seed row
would be written twice.

ASCII source, stdlib only, no network, no clock.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

SEED_HEAD = "- [ ] P2 tech seed (R2513,"
SEED_MARK = "`src/os/probe_seam_forwarding_scope.py`"
OPEN = "- [ ]"
DONE = "- [x] [done 2026-11-07 R2515]"

DISCHARGED = (
    " DISCHARGED R2515 (line 552, AC-PSF1..AC-PSF6 pinned in that row at "
    "R2513 BEFORE any code): src/os/probe_seam_forwarding_scope.py plus its "
    "suite shipped. The hop is DERIVED at CALL time from the probe own "
    "module-level import statements and each helper own syntax tree - no "
    "helper list and no seam name is spelled in the module - so editing ONLY "
    "a helper moves the same probe MISSING-SEAM -> COVERED with no code "
    "change, a differently named helper is followed, and a bare string that "
    "merely names a helper is not an import. A forwarding probe reads "
    "COVERED with the helpers it was followed through named on its row; a "
    "helper that omits a seam makes the probe MISSING-SEAM naming seam and "
    "file and the probe is never imported or run; a module importing helpers "
    "that quiet nothing stays OUT-OF-SCOPE. ONE REGISTERED HOP WAS NOT "
    "ENOUGH: MEASURED this window before shipping that a one-hop reading "
    "INVENTS a MISSING-SEAM when a middle helper names part of the set and "
    "re-exports the rest, so the shipped reading follows local imports "
    "transitively (same root only, cycle-guarded, depth 8) - a strict "
    "superset that can no longer invent a defect. PROOF: AC-PSF1..AC-PSF6 "
    "SUITE PASS 6/6 TWICE identical plus four adjacent readability suites "
    "green (qa/probe-seam-forwarding-scope-R2515.log, 6183B, legs=2 "
    "identical=True fails=0 adjacent=4), and a live leg on the REAL tree "
    "reading SEAMS-FORWARDED over 3 covered probes with the render and doc "
    "digests unchanged, a forwarding fixture COVERED with its helper named "
    "and a stale advancing fixture refused MISSING-SEAM=STPT "
    "(qa/probe-seam-forwarding-scope-live-R2515.log, 1132B, class=tee). "
    "REGISTRY 586/4492 -> 587/4498 by exactly one row "
    "os-probe-seam-forwarding-scope(6), recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from qa/reconcile-all-R2514-retry.log to 56475B at 587 "
    "suites / 4498 criteria with --check byte-identical and its green line "
    "honestly reading 586/587."
)

SEED = (
    "- [ ] P2 tech seed (R2515, from this window own live measurement): "
    "`src/os/probe_seam_lazy_scope.py` - MEASURED this window (lazy fixture "
    "in qa/probe-seam-forwarding-scope-live-R2515.log): a probe that imports "
    "its quieting helper INSIDE a function body reads OUT-OF-SCOPE "
    "quieted=0, because only module-level imports are followed, so a lazy "
    "forwarding probe is invisible again. Product: ONE reading that follows "
    "the quieting through function-level import statements too, on the same "
    "cycle-guarded same-root walk, so a lazy forwarding probe reads COVERED "
    "or MISSING-SEAM on its own row while a module whose function-level "
    "imports quiet nothing still reads OUT-OF-SCOPE. Criteria "
    "AC-PSL1..AC-PSL6 pre-registered HERE BEFORE any code: AC-PSL1 a "
    "function-level import is resolved from the probe own syntax tree at "
    "CALL time, never a hand-written list; AC-PSL2 a probe that imports its "
    "helper inside a function reads COVERED with the helper named; AC-PSL3 a "
    "lazy helper that omits a seam still makes the probe MISSING-SEAM naming "
    "seam and file, and the probe is not run; AC-PSL4 a module whose "
    "function-level imports quiet nothing still reads OUT-OF-SCOPE rather "
    "than being counted as clean; AC-PSL5 the reading stays read-only and "
    "every digest it touches is unchanged; AC-PSL6 pure ASCII, stdlib only, "
    "no clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_lazy_scope, AC-PSL, E_PSL, os-probe-seam-lazy-scope, "
    "test_probe_seam_lazy_scope."
)


def main(argv):
    execute = "--execute" in argv[1:]
    raw = open(QUEUE, "rb").read()
    if b"\r\n" in raw:
        print("FAIL board: E_CR_BOARD the queue is not LF any more")
        return 2
    before = len(raw)
    text = raw.decode("utf-8")
    lines = text.split("\n")
    hits = [i for i, row in enumerate(lines)
            if row.startswith(SEED_HEAD) and SEED_MARK in row]
    if len(hits) != 1:
        print("FAIL board: %d matching seed rows" % len(hits))
        return 2
    at = hits[0]
    row = lines[at]
    if not row.startswith(OPEN):
        print("NOOP row %d is not open" % (at + 1))
        return 0
    if any("probe_seam_lazy_scope" in other for other in lines):
        print("NOOP the successor seed already exists")
        return 0
    lines[at] = row.replace(OPEN, DONE, 1) + DISCHARGED
    lines.insert(at + 1, SEED)
    payload = "\n".join(lines)
    predicted = len(payload.encode("utf-8"))
    print("board row=%d before=%d predicted=%d delta=%d"
          % (at + 1, before, predicted, predicted - before))
    if not execute:
        print("DRY-RUN nothing written")
        return 0
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back_raw = open(QUEUE, "rb").read()
    back = back_raw.decode("utf-8").split("\n")
    ok = (len(back_raw) == predicted and b"\r\n" not in back_raw
          and back[at].startswith(DONE)
          and "DISCHARGED R2515" in back[at]
          and back[at + 1].startswith("- [ ] P2 tech seed (R2515,")
          and "AC-PSL1..AC-PSL6" in back[at + 1])
    print("board %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))