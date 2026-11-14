"""R2724 one-off: prepend the adoption closeout and the next-window line.

The board lagged while the R2723 product and launch windows ran, so the two
lines that were owed are written here rather than pretended away.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
BOARD = os.path.join(BASE, "backlog.md")

DONE = (
    "- [x] [done 2026-11-14 R2724] [was the R2723 launch line; this board "
    "lagged while the R2723 product and launch windows ran] DISCHARGED: the "
    "battery reconcile-battery-R2723 was ADOPTED by its evidence path "
    "qa/reconcile-all-R2723.log (672/672 suites green, criteria 5008, RUNNER "
    "PASS 6319.1s, zero FAIL rows), the matrix was restamped stamp-aligned from "
    "that leg, the four-section verdict read PASS failing=none and the debt row "
    "was closed through the shipped debtor; no successor battery is owed "
    "because the registry is unmoved at 672 suites / 5008 criteria."
)

NEXT = (
    "- [ ] [R2724] next window: a PRODUCT face, and it is UNBLOCKED - debt_gate "
    "reads CLAIM-FIRST item=product-face-R2724 first=1 because this window "
    "closed reconcile-battery-R2723 on a measured 672/5008 green leg and "
    "therefore owes NO successor battery. Take queue head state/queue/tech.md "
    "line 695 prefix AC-EPDU1 (claimable 13, floor FLOOR-MET 5/5 13/10 10/10) "
    "with criteria AC-EPDU1..AC-EPDU6 pinned in that row at R2723 BEFORE any "
    "code: an earned shape whose code is outside the six known shapes is "
    "invisible to the detector while the first code still names it (patched to "
    "answer E_EBOM_UTF16 the face published that code beside shapes "
    "nul,utf8,tail and CODES[shapes[0]] read E_EBOM_NUL). Re-read the row with "
    "python src/os/queue_head.py --head tech rather than trusting this line, "
    "measure the row own limit on private worlds BEFORE writing the face, ship "
    "ONE face with its pre-registered suite behind the shipped reading, prove "
    "it twice through the shipped capture callable with an IDENTICAL digest, "
    "run the adjacent probe suites, and add a bounded live leg that measures "
    "the SAME fixture on BOTH readers. THAT WINDOW WILL MOVE THE REGISTRY by "
    "one row (672 suites / 5008 criteria to 673 / 5014), so a full battery on "
    "the committed tree becomes owed BEFORE the next product byte (the R2168 "
    "mixed-tree rule) and the matrix must be restamped stamp-aligned from the "
    "green leg that closes it. Carried: Docker is absent on this host; "
    "tasks.md is the P-47 canonical board and is not ours to edit; "
    "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell "
    "for its S4U re-registration (ceo-pending physical item loop-s4u-reconcile)."
)


def main():
    with io.open(BOARD, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    lines = text.splitlines()
    head = [DONE, NEXT, ""]
    if lines[:1] == [DONE]:
        print("REFUSED already stamped")
        return 3
    out = "\n".join(head + lines) + "\n"
    payload = out.encode("utf-8")
    with io.open(BOARD, "wb") as fh:
        fh.write(payload)
    with io.open(BOARD, "rb") as fh:
        back = fh.read()
    if back != payload:
        print("REFUSED read-back mismatch")
        return 4
    print("BOARD ok bytes=%d lines=%d" % (len(payload), len(out.splitlines())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
