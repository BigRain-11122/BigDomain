"""R2323 closeout helper: close the claimed tech row at line 379 with its
window stamp and the discharge note, then report the new claimable gauge.

One predicted byte delta, one atomic replace, a read-back proof and no temp
residue. Pure ASCII, stdlib only, no network, writes nothing else.
"""

import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TECH = os.path.join(BASE, "state", "queue", "tech.md")
TMP = TECH + ".tmp-r2323"

HEAD = "- [ ] P2 tech seed (R2302, from this window own live finding):"

NOTE = (" [done 2026-11-01 R2323] CLAIMED state/queue/tech.md:379, the R2302 "
        "orphan_trace seed whose AC-OTR1..AC-OTR6 were pinned there BEFORE "
        "the code. DELIVERED src/os/orphan_trace.py + "
        "src/os/test_orphan_trace.py: every ORPHAN round from "
        "evidence_variants is now resolved against its own variant legs - "
        "TRACE-EXISTS names EVERY leg carrying a RUNNER line with that leg's "
        "own runner token, its own verdict token and its digest, plus the "
        "first such leg in NAME order as the standing-in leg; NO-TRACE names "
        "a round whose legs carry no runner line at all; an empty orphan list "
        "reads NO-ORPHAN at exit 0; and a leg that cannot be decoded refuses "
        "the whole reading with E_OTR_UNDECODABLE rather than being counted "
        "as an empty leg. The RUNNER token and the decoding ladder are asked "
        "of followup_history and the orphan list, the round and the "
        "leg-to-round pairing of evidence_variants, so neither law has a "
        "second owner. SUITE PASS 6/6 twice with an identical criterion "
        "digest, five adjacent os suites green, qa/orphan-trace-R2323.log "
        "1342B as one utf-8 LF single writer through the evidence_capture "
        "callable, wired os-orphan-trace(6). LIVE: ORPHAN TRACE rounds=1 "
        "legs=2 trace_exists=1 no_trace=0 verdict=TRACE-FOUND - R2136 stands "
        "in through reconcile-all-R2136c.log (RUNNER PASS) while "
        "reconcile-all-R2136b.log reads RUNNER FAIL, so the round is "
        "recoverable by a rename and that is now a reading instead of a hand "
        "inspection of two 675KB logs. The battery carries to R2324 as the "
        "successor row.")


def main():
    with io.open(TECH, encoding="utf-8") as handle:
        before = handle.read()
    lines = before.split("\n")
    target = lines[378]
    if not target.startswith(HEAD):
        raise SystemExit("E_C2323_HEAD %s" % target[:60])
    if target.endswith(" "):
        raise SystemExit("E_C2323_TRAILING")
    lines[378] = "- [x]" + target[len("- [ ]"):] + NOTE
    after = "\n".join(lines)
    predicted = len(after.encode("utf-8"))
    with io.open(TMP, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(after)
    written = os.path.getsize(TMP)
    if written != predicted:
        os.remove(TMP)
        raise SystemExit("E_C2323_PREDICT %d != %d" % (written, predicted))
    os.replace(TMP, TECH)
    if os.path.exists(TMP):
        raise SystemExit("E_C2323_TEMP %s" % TMP)
    back = os.path.getsize(TECH)
    if back != predicted:
        raise SystemExit("E_C2323_READBACK %d != %d" % (back, predicted))
    print("tech before=%dB after=%dB row379 now CLOSED"
          % (len(before.encode("utf-8")), back))


if __name__ == "__main__":
    main()