"""R2513 board writer: discharge tech row 551 and seed the next measured gap.

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

SEED_HEAD = "- [ ] P2 tech seed (R2511,"
SEED_MARK = "`src/os/probe_seam_registry.py`"
OPEN = "- [ ]"
DONE = "- [x] [done 2026-11-07 R2513]"

DISCHARGED = (
    " DISCHARGED R2513 (line 551, AC-PSMR1..AC-PSMR6 pinned in that row at "
    "R2511 BEFORE any code): src/os/probe_seam_registry.py plus its suite "
    "shipped. The seam set is DERIVED from the SHIPPED render at CALL time - "
    "every global name the render own code object asks, kept only when that "
    "global really carries a callable guard - so the module source spells "
    "none of them, a seam added to the render appears the moment it is asked "
    "and a global that stops carrying a guard leaves the set. Each module in "
    "the root that QUIETS at least one seam is a PROBE and reads COVERED, or "
    "MISSING-SEAM naming the seam it forgets and its own file - and is never "
    "imported, so a stale probe is named rather than run. A module that "
    "names no seam reads OUT-OF-SCOPE rather than being counted as clean, a "
    "source that will not parse reads UNREADABLE rather than being skipped, "
    "and a file whose name carries a round token is a one-shot script of that "
    "round and reads HISTORICAL. A probe is never asked to quiet its OWN "
    "seam, which the owner answers through its own depth flag, so no invented "
    "defect is reported. PROOF: AC-PSMR1..AC-PSMR6 SUITE PASS 6/6 TWICE with "
    "an identical digest plus three adjacent readability suites green "
    "(qa/probe-seam-registry-R2513.log, 4885B, legs=2 identical=True "
    "fails=0 adjacent=3) and a live leg reading the REAL tree SEAMS-COVERED "
    "over 3 covered probes with a stale fixture refused as MISSING-SEAM "
    "(qa/probe-seam-registry-live-R2513.log, 849B, class=tee). REGISTRY "
    "585/4486 -> 586/4492 by exactly one row os-probe-seam-registry(6), "
    "recounted by importing reconcile_all.SUITES; docs/sandbox-suite-matrix.md "
    "was regenerated stamp-aligned from qa/reconcile-all-R2512-retry.log to "
    "56372B at 586 suites / 4492 criteria with --check byte-identical and its "
    "green line honestly reading 585/586."
)

SEED = (
    "- [ ] P2 tech seed (R2513, from this window own live measurement): "
    "`src/os/probe_seam_forwarding_scope.py` - MEASURED this window: a probe "
    "that quiets the render seams through a SHARED HELPER module names no "
    "seam itself, so probe_seam_registry reads it OUT-OF-SCOPE while the "
    "helper reads COVERED (fixture read: forwarding_probe.py OUT-OF-SCOPE "
    "quieted=0 beside quiet_helper.py COVERED quieted=5). The forwarding "
    "shape is therefore invisible and a stale probe that forwards would never "
    "be named. Product: ONE reading that follows the quieting one hop through "
    "the module the probe imports and answers the probe with the seams it "
    "really quiets, so a forwarding probe reads COVERED or MISSING-SEAM on "
    "its own row, while a module that imports helpers which quiet nothing "
    "still reads OUT-OF-SCOPE. Criteria AC-PSF1..AC-PSF6 pre-registered HERE "
    "BEFORE any code: AC-PSF1 the forwarding hop is derived from the probe "
    "own import statements and the helper own syntax tree at CALL time, never "
    "a hand-written helper list; AC-PSF2 a probe that quiets every seam "
    "through one helper reads COVERED with the helper named; AC-PSF3 a probe "
    "forwarding to a helper that omits a seam reads MISSING-SEAM naming that "
    "seam and the probe file, and the probe is not run; AC-PSF4 a module that "
    "imports helpers which quiet nothing still reads OUT-OF-SCOPE rather than "
    "being counted as clean; AC-PSF5 the reading stays read-only and every "
    "digest it touches is unchanged; AC-PSF6 pure ASCII, stdlib only, no "
    "clock, zero network, its own reconcile label and its own suite. Five "
    "anchors to re-check zero-occupancy at HEAD before any code: "
    "probe_seam_forwarding_scope, AC-PSF, E_PSF, "
    "os-probe-seam-forwarding-scope, test_probe_seam_forwarding_scope."
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
    if any("probe_seam_forwarding_scope" in other for other in lines):
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
          and "DISCHARGED R2513" in back[at]
          and back[at + 1].startswith("- [ ] P2 tech seed (R2513,")
          and "AC-PSF1..AC-PSF6" in back[at + 1])
    print("board %s measured=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back_raw),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))