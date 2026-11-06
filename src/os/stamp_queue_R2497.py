"""stamp_queue_R2497 - stamp the claimed tech row and seed the gap it measured.

Closes state/queue/tech.md line 531 (AC-EDQF1..AC-EDQF6, the R2453 seed claimed
and discharged this window) and seeds one row from this window own measured
limit: a copy of the real export whose queue block was doctored (verdict FLOOR-DEBT,
tech claimable 0) still reads 21/21 PASS on check_export_consistency while
queue_export_freshness_gate reads STALE with drifted=section:shortfall_total,
section:delivered_total,queue:tech - so the face everyone trusts cannot see a
stale queue block at all.

Dry run by default; --execute writes one atomic replace with a byte read-back.
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "..", "..", "state", "queue", "tech.md")

CLAIM_PREFIX = "- [ ] P2 tech seed (R2453, from this window own measured limit):"

DISCHARGED = (
    "  DISCHARGED R2497 (line 531, AC-EDQF1..AC-EDQF6): "
    "src/os/export_driver_queue_face.py plus "
    "src/os/test_export_driver_queue_face.py shipped against the criteria "
    "pinned at R2453. The section the driver publishes IS "
    "queue_floor_export_face.face asked as an attribute at CALL time (patching "
    "that reading moves the section, proved in the suite), and the gross "
    "`queue_floor --check --json` re-derivation was DELETED from "
    "export_R2431.py rather than merely left unused, so the second derivation "
    "no longer exists. The write stages the composed bytes beside the export "
    "and proves them through queue_export_freshness_gate.check BEFORE any "
    "replace, so a queue that moved between the reading and the write refuses "
    "with the gate own verdict word (STALE) and leaves the document "
    "byte-identical with no residue; the section is refreshed IN PLACE so "
    "every already-published key keeps its value and its position. SUITE PASS "
    "6/6 twice with identical verdicts plus five adjacent suites green "
    "(qa/export-driver-queue-face-R2497.log, 2657B, utf-8 LF, crlf=0, "
    "legs=2 identical=True adjacent=5 fails=0). MEASURED on the real tree: the "
    "driver run reads queue=CURRENT with queue_drifted=(none), the face "
    "re-reads CURRENT and the gate reports no drift."
)

SEED = (
    "- [ ] P2 tech seed (R2497, from this window own measured limit): "
    "`src/os/export_consistency_queue_face.py` - check_export_consistency, the "
    "21-check face every window trusts, cannot see the queue block at all. "
    "MEASURED this window: a copy of the real export whose queue block was "
    "doctored (verdict FLOOR-DEBT, tech claimable 0) still reads pass=21 "
    "fail=0, while queue_export_freshness_gate on the same document reads "
    "STALE with drifted=section:shortfall_total, section:delivered_total, "
    "queue:tech. Product: the consistency face asks the shipped gate at CALL "
    "time and publishes the queue verdict beside its twenty-one checks, so a "
    "document edited after the driver published it reads DRIFT rather than "
    "PASS. Criteria AC-ECQF1..AC-ECQF6 pre-registered HERE BEFORE any code: "
    "AC-ECQF1 the queue reading is queue_export_freshness_gate.check asked at "
    "CALL time, never a second comparison; AC-ECQF2 the twenty-one existing "
    "checks keep their names, order and verdicts on every document; AC-ECQF3 "
    "a stale queue block reads DRIFT naming every drifted section field and "
    "queue, and is never folded into the twenty-one; AC-ECQF4 a CURRENT "
    "document keeps exactly today's exit code and printed lines plus one "
    "additional queue line; AC-ECQF5 the reading is pure (writes nothing, "
    "reads no clock) so it can run on every battery leg; AC-ECQF6 pure ASCII, "
    "stdlib only, zero network, own reconcile label and suite. Four anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "export_consistency_queue_face, AC-ECQF, E_ECQF, "
    "os-export-consistency-queue-face, test_export_consistency_queue_face."
)


def plan(text):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(CLAIM_PREFIX)]
    if len(hits) != 1:
        raise SystemExit("E_SQ2497_SHAPE: claim lines found=%d" % len(hits))
    index = hits[0]
    lines[index] = lines[index].replace("- [ ]", "- [x] [done 2026-11-06 "
                                                 "R2497]", 1)
    lines.insert(index + 1, DISCHARGED)
    lines.insert(index + 2, SEED)
    return "\n".join(lines)


def main(argv):
    execute = "--execute" in argv
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        before = handle.read()
    after = plan(before)
    line_no = before.split("\n").index(
        [line for line in before.split("\n")
         if line.startswith(CLAIM_PREFIX)][0]) + 1
    print("PLAN claim_line=%d before=%dB after=%dB"
          % (line_no, len(before.encode("utf-8")), len(after.encode("utf-8"))))
    if not execute:
        print("DRY RUN wrote=no")
        return 0
    directory = os.path.dirname(os.path.abspath(QUEUE))
    fd, temporary = tempfile.mkstemp(prefix=".tech-", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(after)
        os.replace(temporary, QUEUE)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    print("WRITTEN after=%dB readback=%s"
          % (len(back.encode("utf-8")), back == after))
    return 0 if back == after else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))