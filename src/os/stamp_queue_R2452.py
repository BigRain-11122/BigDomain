"""stamp_queue_R2452 - stamp the claimed tech row and seed the real gap it
measured.

Closes state/queue/tech.md line 518 (AC-SEWS1..AC-SEWS6, the R2450 seed
claimed and discharged this window) and seeds one row from this window own
measured limit: closeout_export_parity_wire REFUSES to publish a CRLF-dialect
export (refusal 2/DISAGREES, document byte-identical), because the closeout
recipe composes LF text while the gate wire keeps the target dialect, so the
two recipes disagree on transport rather than on content.

Dry run by default; --execute writes one atomic replace with a predicted size
and a byte read-back.
"""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(BASE, "..", "..", "state", "queue", "tech.md")

CLAIM_PREFIX = "- [ ] P2 tech seed (R2450, from this window own measured limit):"

DISCHARGED = (
    "  DISCHARGED R2452 (line 518, AC-SEWS1..AC-SEWS6): "
    "src/os/status_export_writer_transport_scope.py plus "
    "src/os/test_status_export_writer_transport_scope.py shipped against the "
    "criteria pinned at R2450, and the proved set is the dialect wire own "
    "derived set read off the shipped audit at CALL time, with each writer "
    "asked through its OWN entry point discovered by surface (write, else "
    "publish) over an LF copy and a CRLF copy in a private fixture world. "
    "MEASURED on the real tree: scope=SCOPE-PARTIAL proved=2 "
    "unprovable=closeout_export_parity_wire.py, with queue_export_gate_wire "
    "and queue_floor_export_face PROVED (lf=102887B crlf=103292B lone-lf=0 "
    "agree=yes for both), and the third writer published as UNPROVABLE "
    "refusal=2/DISAGREES rather than dropped - the R2450 limit is now a named "
    "reading instead of an untested writer. SUITE PASS 6/6 twice with an "
    "identical digest plus three adjacent suites green "
    "(qa/status-export-writer-transport-scope-R2452.log, 2076B, legs=2 "
    "identical=True adjacent=3 fails=0); live capture kept as "
    "qa/status-export-writer-transport-scope-live-R2452.log (559B, one utf-8 "
    "LF body, zero CRLF). A REAL birth-site defect was found and repaired "
    "before this row closed: status_export_writer_dialect_wire.transport had "
    "the queues root hardcoded to \".\" so its own transport proof read the "
    "process cwd - the R2451 repair fixed the suite call sites only - and the "
    "root is now passed through from check(), proved by the same suite "
    "reading 6/6 from BOTH the repository root and src/os."
)

SEED = (
    "- [ ] P2 tech seed (R2452, from this window own measured limit): "
    "`src/os/closeout_export_parity_dialect_wire.py` - "
    "closeout_export_parity_wire cannot publish a CRLF-dialect export at all. "
    "MEASURED this window: on a CRLF copy of the real export the closeout "
    "wire reads REFUSED at exit 2 with the document byte-identical and the "
    "parity reading DISAGREES/bytes, while its LF leg writes normally "
    "(WRITTEN, agree=yes), so the refusal is transport-only and not content "
    "drift - closeout_style composes LF text while the gate wire keeps the "
    "target dialect, so the two recipes disagree on line endings. That makes "
    "the closeout path unable to land ANY CRLF export, which is the exact "
    "dialect the R2450 wire exists to preserve. Product: the closeout recipe "
    "asks the shipped dialect law at CALL time so it composes in the target "
    "own transport, and the parity proves content rather than line endings. "
    "Criteria AC-CEPD1..AC-CEPD6 pre-registered HERE BEFORE any code: "
    "AC-CEPD1 the closeout composition lands the target own dialect, asked "
    "through the shipped audit at CALL time, never by a hardcoded newline; "
    "AC-CEPD2 a CRLF-dialect export publishes through the closeout wire "
    "(WRITTEN, zero lone LF, bytes equal to the LF composition with CRLF "
    "endings); AC-CEPD3 an LF export keeps exactly today's bytes through the "
    "same call; AC-CEPD4 the checker is not relaxed - a doctored document "
    "with one changed value still reads DISAGREES with its own difference "
    "name and is left byte-identical; AC-CEPD5 the existing reading keys keep "
    "their values and the transport reading is an additional key; AC-CEPD6 "
    "pure ASCII, stdlib only, no clock, zero network, own reconcile label and "
    "suite. Four anchors to re-check zero-occupancy at HEAD before any code: "
    "closeout_export_parity_dialect_wire, AC-CEPD, E_CEPD, "
    "os-closeout-export-parity-dialect-wire, "
    "test_closeout_export_parity_dialect_wire."
)


def plan(text):
    lines = text.split("\n")
    hits = [i for i, line in enumerate(lines) if line.startswith(CLAIM_PREFIX)]
    if len(hits) != 1:
        raise SystemExit("E_SQ2452_SHAPE: claim lines found=%d" % len(hits))
    index = hits[0]
    lines[index] = lines[index].replace("- [ ]", "- [x] [done 2026-11-05 "
                                                 "R2452]", 1)
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