"""stamp_queue_R2448 - stamp the claimed tech row and seed the real gap it
measured.

Closes state/queue/tech.md line 514 (AC-PDR1..AC-PDR6, the R2434 seed claimed
and discharged this window) and seeds one row from this window's own measured
limit: the three export writers the parameter-resolution law now READS are
writers of docs/status-export.json that do not ask the shared payload
derivation, so the audit reads AUDIT-DEBT for the first time.

Dry run by default; --execute writes one atomic replace with a predicted size
and a byte read-back.
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "..", "..", "state", "queue", "tech.md")

CLAIM_PREFIX = "- [ ] P2 tech seed (R2434, from this window own measured limit):"

DISCHARGED = (
    "  DISCHARGED R2448 (line 514, AC-PDR1..AC-PDR6): "
    "src/os/parameter_destination_resolution.py plus "
    "src/os/test_parameter_destination_resolution.py shipped against the "
    "criteria pinned at R2434. Reading: a GENERAL writer that RECEIVES its "
    "destination as a function parameter used to read E_GWDA_UNRESOLVED and "
    "hide among the unread rows. The destination is now resolved through the "
    "module own in-module call sites, and each call-site argument is handed "
    "back to the AUDIT own resolver (one resolver, two readers), so no second "
    "path resolution exists; a call-site argument that is itself a parameter "
    "is followed one hop at a time under a declared MAX_DEPTH, a function with "
    "no in-module call site reads UNRESOLVED naming the function, and a "
    "resolvable one publishes every spelling its call sites pass. MEASURED on "
    "the real tree: PARAM DESTINATION scanned=1106 writers=85 resolved=213 "
    "unresolved=3 (dec_watermark.py write_atomic argument, evidence_writer.py "
    "_restore argument, stamp_exempt_guard.py commit with no in-module call "
    "site). The audit now reads GENERAL DIALECT AUDIT scanned=1106 general=146 "
    "keeps=10 repair=2 unresolved=132 routed=7 unrouted=3 verdict=AUDIT-DEBT "
    "- the three NEW KEEPS rows are closeout_export_parity_wire.py, "
    "queue_export_gate_wire.py and queue_floor_export_face.py, each landing "
    "docs/status-export.json, and none asks the shared derivation, which is "
    "the honest finding this law exists to expose and is seeded as the gap row "
    "below rather than swept. SUITE PASS 6/6 twice with an identical digest "
    "plus three adjacent suites green (qa/parameter-destination-resolution-"
    "R2448.log, 1624B, legs=2 identical=True adjacent=3 fails=0); the audit "
    "own suite was corrected at its birth site because two of its assertions "
    "pinned a live snapshot (KEEPS == 7 and verdict AUDIT-CLEAN) that this "
    "law legitimately moves - the count became a named-subset assertion over "
    "the seven writers that row delivered, and the green became the audit own "
    "derivation law (every offender is a KEEPS row answering no, routed plus "
    "unrouted reconciles to keeps, the verdict word follows the offender "
    "list), so nothing was widened and the live AUDIT-DEBT is named rather "
    "than asserted away. LIVE captures kept as "
    "qa/parameter-destination-resolution-live-R2448.log."
)

SEED = (
    "- [ ] P2 tech seed (R2448, from this window own measured limit): "
    "`src/os/status_export_writer_dialect_wire.py` - the parameter-resolution "
    "law resolved three writers that land `docs/status-export.json` "
    "(closeout_export_parity_wire, queue_export_gate_wire, "
    "queue_floor_export_face) and MEASURED this window none of them asks the "
    "shared payload derivation, so the audit reads AUDIT-DEBT for the first "
    "time (routed=7 unrouted=3). Product: the three writers ask the shared "
    "derivation at their own write sites, so a CRLF export stays CRLF and an "
    "LF export keeps exactly today's bytes, while the audit reads AUDIT-CLEAN "
    "with routed == keeps. Criteria AC-SEWD1..AC-SEWD6 pre-registered HERE "
    "BEFORE any code: AC-SEWD1 the writer set is derived from the audit "
    "reading at CALL time, never a fixed list of three names; AC-SEWD2 a CRLF "
    "docs/status-export.json keeps CRLF through a real writer call with zero "
    "lone LF; AC-SEWD3 an LF export keeps exactly today's bytes; AC-SEWD4 "
    "every one of the three writers keeps its existing refusal code, exit "
    "code and printed line; AC-SEWD5 the audit reads AUDIT-CLEAN with "
    "routed == keeps after the wire; AC-SEWD6 pure ASCII, stdlib only, no "
    "clock, zero network, own reconcile label and suite. Five anchors to "
    "re-check zero-occupancy at HEAD before any code: "
    "status_export_writer_dialect_wire, AC-SEWD, E_SEWD, "
    "os-status-export-writer-dialect-wire, "
    "test_status_export_writer_dialect_wire."
)


def plan(text):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(CLAIM_PREFIX)]
    if len(hits) != 1:
        raise SystemExit("E_SQ2448_SHAPE: claim lines found=%d" % len(hits))
    index = hits[0]
    lines[index] = lines[index].replace("- [ ]", "- [x] [done 2026-11-05 "
                                                 "R2448]", 1)
    lines.insert(index + 1, DISCHARGED)
    lines.insert(index + 2, SEED)
    return "\n".join(lines)


def main(argv):
    execute = "--execute" in argv
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        before = handle.read()
    after = plan(before)
    print("PLAN claim_line=%d before=%dB after=%dB"
          % (before.split("\n").index(
              [line for line in before.split("\n")
               if line.startswith(CLAIM_PREFIX)][0]) + 1,
             len(before.encode("utf-8")), len(after.encode("utf-8"))))
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