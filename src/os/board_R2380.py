"""R2380 board: stamp the claimed tech row, seed one REAL measured gap row.

The claimed row is state/queue/tech.md:426 (AC-FGES1..AC-FGES6). Stamping it
drops tech claimable to 9 against the floor of 10, so one real gap row is
seeded from this window own measured seam: the pile derivation now follows the
evidence path, but an evidence path with NO directory part silently falls back
to DEFAULT_DIR 'qa' - the same class this window closed, one level down.

One atomic replace, predicted size proven, read-back, no temp residue.
ASCII source, stdlib only, no clock, no network.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")

STAMP_OLD = "- [ ] P2 tech seed (R2370, from this window own measured seam):"
STAMP_NEW = "- [x] [done 2026-11-02 R2380] P2 tech seed (R2370, from this window own measured seam):"

SEED = (
    "- [ ] P2 tech seed (R2380, from this window own measured seam): "
    "`src/os/bare_evidence_pile_refusal.py` - the guarded pile now follows the "
    "evidence path, but a path with NO directory part falls back to DEFAULT_DIR "
    "'qa' in silence, so the guard can once more speak about a pile the file "
    "does not belong to. Measured this window in the module: "
    "followup_guard_evidence_scope.evidence_dir('x.log') returns 'qa' because "
    "os.path.dirname gives an empty string, and the suite never exercises it. "
    "Product: an evidence path with no directory part is DERIVED from where the "
    "file actually is under the root (or REFUSED with its own code when the "
    "file is absent), so a caller that names a bare filename gets the pile the "
    "file lives in and never a constant. Criteria AC-BEPR1..AC-BEPR6 "
    "pre-registered HERE BEFORE any code: AC-BEPR1 a bare filename derives the "
    "pile by STAT-ing it under the root, and a patched resolver moves which "
    "pile is read (no 'qa' fallback left in the derivation); AC-BEPR2 an "
    "evidence path under qa keeps today's derived answer byte for byte; "
    "AC-BEPR3 a bare filename that exists in a FOREIGN-SECTION pile REFUSES "
    "naming that pile, proving the answer is measured and not defaulted; "
    "AC-BEPR4 a bare filename that exists nowhere refuses with its own code at "
    "exit 2 rather than reading a pile it cannot prove; AC-BEPR5 CLI codes "
    "0/2/3/5 and the byte-stable --json over the pinned GUARD_KEYS stay "
    "unchanged; AC-BEPR6 pure ASCII, stdlib only, zero network, no clock, plus "
    "its own reconcile label. Five anchors zero-occupancy at HEAD 2026-11-02: "
    "bare_evidence_pile_refusal, AC-BEPR, E_BEPR, "
    "os-bare-evidence-pile-refusal, test_bare_evidence_pile_refusal."
)


def main():
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if STAMP_NEW in text:
        print("ALREADY-STAMPED")
        return 1
    if text.count(STAMP_OLD) != 1:
        print("STAMP TARGET COUNT %d" % text.count(STAMP_OLD))
        return 1
    stamped = text.replace(STAMP_OLD, STAMP_NEW)
    if not stamped.endswith("\n"):
        stamped += "\n"
    after = stamped + SEED + "\n"
    predicted = len(after.encode("utf-8"))
    tmp = QUEUE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(after)
    os.replace(tmp, QUEUE)
    with io.open(QUEUE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    measured = len(back.encode("utf-8"))
    residue = os.path.exists(tmp)
    print("before=%dB predicted=%dB measured=%dB match=%s residue=%s"
          % (len(text.encode("utf-8")), predicted, measured,
             back == after, residue))
    return 0 if back == after and not residue else 1


if __name__ == "__main__":
    sys.exit(main())