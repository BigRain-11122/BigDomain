"""stamp_queue_R2450 - stamp the claimed tech row and seed the real gap it
measured.

Closes state/queue/tech.md line 516 (AC-SEWD1..AC-SEWD6, the R2448 seed
claimed and discharged this window) and seeds one row from this window own
measured limit: the transport proof runs the QUEUE-FLOOR writer only, so two
of the three derived writers are not proved by it. MEASURED this window,
queue_export_gate_wire keeps CRLF on a fixture (lone_lf=0) without being
asserted, and closeout_export_parity_wire REFUSES on a bare fixture (its
parity gate needs a coherent closeout world), so its CRLF write path cannot be
exercised by a copy at all.

Dry run by default; --execute writes one atomic replace with a predicted size
and a byte read-back.
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "..", "..", "state", "queue", "tech.md")

CLAIM_PREFIX = "- [ ] P2 tech seed (R2448, from this window own measured limit):"

DISCHARGED = (
    "  DISCHARGED R2450 (line 516, AC-SEWD1..AC-SEWD6): "
    "src/os/status_export_writer_dialect_wire.py plus "
    "src/os/test_status_export_writer_dialect_wire.py shipped against the "
    "criteria pinned at R2448, and the three writers themselves were wired at "
    "their own write sites (queue_floor_export_face.write, "
    "queue_export_gate_wire.publish, closeout_export_parity_wire.publish) to "
    "ask general_writer_dialect_audit.payload_for before landing bytes, so the "
    "dialect is decided by the shared law rather than by the running writer. "
    "MEASURED on the real tree: STATUS EXPORT WRITERS derived=3 routed=3 "
    "unrouted=0 transport=LF/CRLF audit=AUDIT-CLEAN verdict=WIRED with the "
    "writer set read off the audit at CALL time (no name list in the module), "
    "the audit reading GENERAL DIALECT AUDIT scanned=1114 general=146 keeps=10 "
    "repair=2 unresolved=132 routed=10 unrouted=0 verdict=AUDIT-CLEAN (the "
    "R2448 debt close by construction), and the transport proof on the real "
    "document lf=98405B today-exact=True crlf=98802B lone-lf=0 crlf-kept=True. "
    "The three writers keep their own refusal contracts and their own suites "
    "still pass (6/6, 6/6, 16/16) - asserted inside this wire suite rather "
    "than re-transcribed here. SUITE PASS 6/6 twice with an identical digest "
    "plus three adjacent suites green (qa/status-export-writer-dialect-wire-"
    "R2450.log, 1693B, legs=2 identical=True adjacent=3 fails=0); live "
    "capture kept as qa/status-export-writer-dialect-wire-live-R2450.log. The "
    "honest limit this window measured is seeded as the gap row below rather "
    "than swept."
)

SEED = (
    "- [ ] P2 tech seed (R2450, from this window own measured limit): "
    "`src/os/status_export_writer_transport_scope.py` - the wire derives three "
    "writers but its transport proof runs the QUEUE-FLOOR writer only, so a "
    "CRLF regression in the other two would not be caught here. MEASURED this "
    "window: queue_export_gate_wire.publish on a CRLF copy reads WRITTEN "
    "lone_lf=0 crlf=yes (it works, but nothing asserts it), and "
    "closeout_export_parity_wire.publish REFUSES on a bare fixture at exit 2 "
    "with the document left byte-identical, because its parity gate needs a "
    "coherent closeout world, so its CRLF write path cannot be exercised by a "
    "copy at all. Product: the proof set is the same derived set, each writer "
    "is asked in its own publishable world, and a writer that refuses on the "
    "fixture is published as UNPROVABLE with its refusal code instead of being "
    "silently dropped. Criteria AC-SEWS1..AC-SEWS6 pre-registered HERE BEFORE "
    "any code: AC-SEWS1 the proved writer set is derived from the same audit "
    "reading at CALL time, never a fixed writer name; AC-SEWS2 a CRLF copy "
    "through each derived writer that can publish on a fixture returns CRLF "
    "with zero lone LF, and a writer that refuses is named UNPROVABLE rather "
    "than dropped; AC-SEWS3 an LF copy through each proving writer keeps "
    "exactly today's bytes; AC-SEWS4 an UNPROVABLE writer is published with "
    "its refusal code and its document is left byte-identical; AC-SEWS5 the "
    "reading gains a per-writer transport line while the existing keys stay "
    "unchanged; AC-SEWS6 pure ASCII, stdlib only, no clock, zero network, own "
    "reconcile label and suite. Five anchors to re-check zero-occupancy at "
    "HEAD before any code: status_export_writer_transport_scope, AC-SEWS, "
    "E_SEWS, os-status-export-writer-transport-scope, "
    "test_status_export_writer_transport_scope."
)


def plan(text):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(CLAIM_PREFIX)]
    if len(hits) != 1:
        raise SystemExit("E_SQ2450_SHAPE: claim lines found=%d" % len(hits))
    index = hits[0]
    lines[index] = lines[index].replace("- [ ]", "- [x] [done 2026-11-05 "
                                                 "R2450]", 1)
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