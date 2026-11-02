# seed_R2370.py - stamp this window's claimed tech row and append one REAL
# measured successor seed, through one atomic write with a read-back proof.
#
# Why a script: state/queue/tech.md is 1.4MB and the seed row must land as ONE
# utf-8 LF line at the tail with the claimed row stamped by its own prefix. A
# rewrite through io is the only way to do both in one pass without a shell
# redirect (the ps-utf16 trap).

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(ROOT, "state", "queue", "tech.md")

OLD_PREFIX = "- [ ] P2 tech seed (R2357, from this window own measured gap):"
NEW_PREFIX = "- [x] [done 2026-11-02 R2370] P2 tech seed (R2357, from this " \
             "window own measured gap):"

SEED = (
    "- [ ] P2 tech seed (R2370, from this window own measured seam): "
    "`src/os/followup_guard_evidence_scope` - the guard asks a FIXED pile. "
    "Measured this window in the wire just shipped: "
    "`followup_section_foreign_wire.matrix_section(root, evidence, call)` takes "
    "the evidence path the operator named and guards the literal directory "
    "'qa', so a matrix regenerated from any OTHER pile is protected by a "
    "reading of a pile it is not comparing - the refusal speaks about qa while "
    "the doc is built from elsewhere. The section own suite passed because the "
    "qa-shaped pile is the one it was given. Product: the guard reads the pile "
    "the EVIDENCE belongs to (its own directory), so the refusal and the matrix "
    "always describe the same logs, and a caller that names qa keeps today's "
    "reading byte for byte. Criteria AC-FGES1..AC-FGES6 pre-registered HERE "
    "BEFORE any code: AC-FGES1 the guarded directory is derived from the "
    "evidence path and a patched derivation moves which pile is read (no "
    "literal 'qa' decision in the section); AC-FGES2 an evidence path under qa "
    "keeps the section report byte-identical to the R2370 wire, so the change "
    "adds no new wording on the normal path; AC-FGES3 an evidence file in a "
    "directory whose pile reads FOREIGN-SECTION REFUSES, proving the guard "
    "follows the MEASURED pile and not a constant; AC-FGES4 a relative and an "
    "absolute evidence path for the same file read the same pile, so the "
    "refusal never depends on the working directory; AC-FGES5 CLI codes 0/2/3/5 "
    "and a byte-stable --json over the pinned GUARD_KEYS are unchanged; "
    "AC-FGES6 pure ASCII, stdlib only, zero network, no clock, the reading "
    "still imported from followup_section_foreign, plus its own reconcile "
    "label. Five anchors zero-occupancy at HEAD 2026-11-02: "
    "followup_guard_evidence_scope, AC-FGES, E_FGES, "
    "os-followup-guard-evidence-scope, test_followup_guard_evidence_scope."
)


def main():
    raw = io.open(QUEUE, "rb").read()
    text = raw.decode("utf-8")
    before_bytes = len(raw)
    before_lines = text.count("\n")
    if text.count(OLD_PREFIX) != 1:
        print("REFUSED: claimed prefix found %d times" % text.count(OLD_PREFIX))
        return 2
    if SEED.split("`")[1] in text:
        print("REFUSED: seed face already present")
        return 2
    text = text.replace(OLD_PREFIX, NEW_PREFIX, 1)
    if not text.endswith("\n"):
        text = text + "\n"
    text = text + SEED + "\n"
    payload = text.encode("utf-8")
    with io.open(QUEUE, "wb") as handle:
        handle.write(payload)
    check = io.open(QUEUE, "rb").read().decode("utf-8")
    stamped = NEW_PREFIX in check and OLD_PREFIX not in check
    seeded = check.rstrip("\n").endswith(SEED)
    lines = check.count("\n")
    print("bytes %d -> %d (delta %+d) lines %d -> %d"
          % (before_bytes, len(payload), len(payload) - before_bytes,
             before_lines, lines))
    print("stamped=%s seeded=%s crlf=%d"
          % (stamped, seeded, check.count("\r\n")))
    if not (stamped and seeded and check.count("\r\n") == 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())