"""R2535 closeout: heartbeat row and backlog entry, both proved by read-back."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
HEART = os.path.join(REPO, "heartbeat.txt")
BOARD = os.path.join(BASE, "backlog.md")

HEART_ROW = ("2026-11-07 19:41 R2535 product window: nested subscript scope "
             "shipped (two-key chain resolves with every key, refusals carry "
             "the hop), registry 597/4558")

BOARD_ROW = (
    "- [x] [done 2026-11-07 R2535] R2535 PRODUCT window on the tech head the "
    "register named (product-face-R2534, state/queue/tech.md:571 prefix "
    "AC-PCNS1 probe_seam_nested_subscript_scope, criteria AC-PCNS1..AC-PCNS6 "
    "pinned in that row at R2533 BEFORE any code). Five-silence scan at open "
    "was clean apart from a content-addressed decisions diff of NINE tokens, "
    "every one of which is an inline reference inside an older row own prose, "
    "so all nine were ACKNOWLEDGED with no execution face and the baseline "
    "advanced by union; the debt gate read CLAIM-FIRST product-face-R2534 "
    "first=1 with no battery owed and queue_head named line 571 claimable=11; "
    "all five anchors were re-checked at zero occupancy before any code. "
    "SHIPPED src/os/probe_seam_nested_subscript_scope.py plus its "
    "six-criteria suite: a for-loop whose iterable is a CHAIN of two or more "
    "constant string subscripts on a literal container resolves when the "
    "result holds EXACTLY ONE element and carries the chain with EVERY key, "
    "while a missing key, an integer index into a tuple, a call, a format and "
    "a comprehension step are NAMED with the HOP that broke (key@hop2, "
    "index@hop2, call@hop2, format@hop2, comprehension@hop1) instead of a bare "
    "shape word, a two-element result is NAMED ambiguous and never resolved to "
    "its first element, and an index step is never followed. The shipped "
    "subscript tables and law are asked FIRST and never overwritten and the "
    "seam classifier is still the shipped registry single quiets. PROOF: "
    "AC-PCNS1..AC-PCNS6 SUITE PASS 6/6 TWICE with byte-identical output and "
    "exit 0 on both legs plus five adjacent probe suites green "
    "(qa/probe-seam-nested-subscript-scope-R2535.log, 8446B, legs=2 "
    "identical=True fails=0 adjacent=5) and a live leg on the REAL tree "
    "reading SEAMS-NESTED-SUBSCRIPT-COVERED over 1447 probes (3 covered, 177 "
    "out-of-scope, 1267 historical, missing=0) with all three digests "
    "unchanged, where the SAME fixture is followed by this face and still "
    "reads refused=nested under the shipped subscript face "
    "(qa/probe-seam-nested-subscript-scope-live-R2535.log, 672B, crlf=0). "
    "REGISTRY 596/4552 -> 597/4558 by one row recounted by import; "
    "docs/sandbox-suite-matrix.md regenerated stamp-aligned from the eligible "
    "battery leg qa/reconcile-all-R2533.log to 57572 bytes at 597/4558 with "
    "green=596/597 self-describing and --check byte-identical. BOARD: row 571 "
    "closed at predicted and measured 1721378B and ONE row seeded from this "
    "window own measured limit (a NAME step bound to a str constant is NAMED "
    "with its hop but never resolved) as AC-PNKB1..AC-PNKB6, head now line "
    "573, queue_floor FLOOR-MET 5/5 11/10 10/10. DEBT: product-face-R2534 "
    "closed (line 266, open 15->14, done 233->234) and reconcile-battery-R2535 "
    "opened first=yes at 597/4558 so the next window owes that battery before "
    "any product byte, with product-face-R2535 opened first=no; the residue "
    "declaration had expired at R2535 with two rounds no longer live and was "
    "re-pinned through its idempotent writer to R2545 (302->301 entries, "
    "dropped R2525 and R2527), after which residue_triage read R2535 TRIAGED. "
    "HONEST: two product points and nothing a CEO could newly open; THREE "
    "defects were measured in my own first pass and fixed in the CODE rather "
    "than in the assertions (the helper walk was delegated to the wrong "
    "shipped face and died with AttributeError, a function-body chain could "
    "not see a module-level literal container, and a format step was named "
    "call); the fold is still DUE at 111814B and was refused on token coverage "
    "rather than forced; Docker is absent, the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items, the S4U lane reconcile "
    "still needs an elevated shell, and tasks.md was not touched."
)


def main():
    with io.open(HEART, "r", encoding="utf-8", newline="") as handle:
        heart = handle.read()
    if HEART_ROW not in heart:
        if not heart.endswith("\n"):
            heart += "\n"
        heart += HEART_ROW + "\n"
        with io.open(HEART, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(heart)
    with io.open(HEART, "r", encoding="utf-8") as handle:
        back = handle.read().split("\n")
    heart_ok = HEART_ROW in back
    with io.open(BOARD, "r", encoding="utf-8") as handle:
        text = handle.read()
    board_ok = True
    if not text.startswith(BOARD_ROW):
        with io.open(BOARD, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(BOARD_ROW + "\n" + text)
        with io.open(BOARD, "r", encoding="utf-8") as handle:
            board_ok = handle.read().startswith(BOARD_ROW)
    print("closeout heartbeat=%s backlog=%s"
          % ("OK" if heart_ok else "FAIL", "OK" if board_ok else "FAIL"))
    return 0 if (heart_ok and board_ok) else 2


if __name__ == "__main__":
    sys.exit(main())