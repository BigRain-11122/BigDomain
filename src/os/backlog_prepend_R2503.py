"""R2503 closeout: prepend the board entry and append the heartbeat row."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
BACKLOG = os.path.join(BASE, "backlog.md")
HEART = os.path.join(REPO, "heartbeat.txt")

ENTRY = (
    "- [x] [done 2026-11-07 R2503] R2503 PRODUCT window on the tech head the "
    "register named (state/queue/tech.md:540 prefix AC-PLRC1 "
    "patterns_label_readability_render_consumer, criteria AC-PLRC1..AC-PLRC6 "
    "pinned in that row at R2502 BEFORE any code). Five-silence scan clean at "
    "HEAD a265bfab; debt_gate read OPEN-NONE and queue_head named tech line 540 "
    "claimable=10. CLAIM: the R2502 readability gate protected only callers "
    "that chose publish(), while the shipped generator read the patterns file "
    "with json.load and interpolated every label into the CEO-visible "
    "artifact. SHIPPED src/os/patterns_label_readability_render_consumer.py "
    "plus its suite and wired suite_matrix.render() to ask that seam FIRST: "
    "guard() asks patterns_label_readability.gate at CALL time and carries its "
    "verdict and its own code verbatim, so no second classifier exists on the "
    "render path. A suspect file refuses the shipped tool at exit 4 naming "
    "E_PLR_SUSPECT and the label key, writes no artifact byte and leaves no "
    "residue, and --check reads that refusal as readability rather than as the "
    "drift exit 2, while a clean file keeps exit 0 and renders byte-identically "
    "to the committed 55846-byte doc. PROOF: SUITE PASS 6/6 TWICE identical "
    "plus three adjacent suites green (qa/patterns-render-consumer-R2503.log, "
    "5855B, legs=2 identical=True fails=0 adjacent=3) and a live reading plus "
    "one MEASURED limit (qa/patterns-render-consumer-live-R2503.log, 405B). Two "
    "of my own assertions failed first and were repaired as TEST defects, not "
    "loosened. REGISTRY 580/4456 -> 581/4462 by exactly one row; matrix "
    "restamped stamp-aligned from qa/reconcile-all-R2502.log to 55846B at "
    "581/4462 with --check byte-identical and a green line honestly reading "
    "580/581. Board row 540 closed and ONE row seeded from this window own "
    "measurement (AC-PNLT1..AC-PNLT6), floor FLOOR-MET 5/5 10/10 10/10. DEBT: "
    "reconcile-battery-R2503 appended first=no, so the next window owes that "
    "battery at 581 suites / 4462 criteria on the committed tree before any "
    "further product byte."
)

ROW = "2026-11-07T05:3x R2503 tick 2503 product face\n"


def main():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if text.startswith("- [x] [done 2026-11-07 R2503]"):
        payload = text
        print("backlog ALREADY-PRESENT bytes=%d"
              % len(payload.encode("utf-8")))
        ok = True
    else:
        payload = ENTRY + "\n" + text
        io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(payload)
        back = io.open(BACKLOG, encoding="utf-8").read()
        ok = back.startswith("- [x] [done 2026-11-07 R2503]")
        print("backlog %s bytes=%d" % ("OK" if ok else "FAIL",
                                       len(payload.encode("utf-8"))))

    raw = io.open(HEART, "rb").read()
    heart = raw.decode("utf-16") if raw.startswith(b"\xff\xfe") else \
        raw.decode("utf-8")
    if "R2503" not in heart.rsplit("\n", 2)[-2:]:
        if not heart.endswith("\n"):
            heart += "\n"
        heart += ROW
        out = heart.encode("utf-16") if raw.startswith(b"\xff\xfe") else \
            heart.encode("utf-8")
        io.open(HEART, "wb").write(out)
    back = io.open(HEART, "rb").read()
    tail = (back.decode("utf-16") if back.startswith(b"\xff\xfe")
            else back.decode("utf-8")).splitlines()[-1]
    print("heartbeat %s row=%r" % ("OK" if "R2503" in tail else "FAIL", tail))
    return 0 if ok and "R2503" in tail else 2


if __name__ == "__main__":
    sys.exit(main())