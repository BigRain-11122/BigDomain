"""R2581 closeout bookkeeping: heartbeat line and backlog done entry."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
HB = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")

HEARTBEAT = (
    "2026-11-09T02:05+08:00 R2581 product: FOLD_SUMMARY_RE now tolerates the"
    " date prefix and the past-tense inflection, so a dated or folded"
    " fold-summary reads other instead of re-opening the R2580 gap;"
    " AC-LKND1..AC-LKND6 green 6/6 twice plus five adjacent ledger suites"
    " (1560B, legs=2, identical=True, adjacent=5); registry 621/4702"
    " recounted by import, matrix 61681B green=620/621 byte-identical; board"
    " row 626 closed with one measured seed AC-LKNF1..AC-LKNF6 at line 629;"
    " debt battery-R2581 owed first=yes"
)

ENTRY = (
    "- [x] [done 2026-11-09 R2581] R2581 PRODUCT window on the row the debt"
    " gate named (product-face-R2580, state/queue/tech.md:626 prefix"
    " AC-LKND1, criteria pinned at R2580 BEFORE any code). SHIPPED"
    " src/os/ledger_lines.py FOLD_SUMMARY_RE extended plus"
    " src/os/test_ledger_fold_kind_dateprefix.py: the guard now tolerates the"
    " date prefix NARRATIVE_RE already allowed and knows the past-tense"
    " inflection, so a dated fold summary and the 'R<n> folded ...' form"
    " classify other instead of falling back to the narrative pattern and"
    " reporting that round as having no ledger; the word boundary is"
    " untouched ('R<n> folder of log lines' stays round and still gates) and"
    " a narrative that merely mentions the fold later in the line stays round"
    " and still gates. PROOF: AC-LKND1..AC-LKND6 SUITE PASS 6/6 on the first"
    " run and 6/6 TWICE identical plus five adjacent ledger suites green"
    " (qa/ledger-fold-kind-dateprefix-R2581.log, 1560B, legs=2,"
    " identical=True, adjacent=5, fails=0); the R2580 suite still reads 6/6; a"
    " simulation over the real 65-line log reclassified ZERO lines and kept"
    " it CLEAN. REGISTRY 620/4696 -> 621/4702 recounted by import (621 unique"
    " names, 621 unique paths); matrix regenerated stamp-aligned from"
    " qa/reconcile-all-R2579-retry2.log to 61681B at 621/4702 with its green"
    " line honestly 620/621 and --check byte-identical. BOARD: row 626 closed"
    " at its measured 1820642B -> 1823890B, ONE row seeded as"
    " AC-LKNF1..AC-LKNF6 at line 629 (capitalized and third-person fold"
    " summaries still read round; another date dialect and a leading bullet"
    " read other for the line-start anchor), queue_head line 615 AC-PNAM1"
    " claimable=12, floor FLOOR-MET 5/5 12/10 10/10. DEBT:"
    " product-face-R2580 closed (184652B -> 184655B, line 331, open 33->32,"
    " done 280->281), reconcile-battery-R2581 opened first=yes at 621/4702 and"
    " product-face-R2581 opened first=no, all readback ok. HONEST: two product"
    " points, nothing a CEO could newly open; the queue_row parenthetical"
    " blind spot that hid row 626 from queue_head is disclosed and NOT"
    " repaired this round."
)


def main():
    with io.open(HB, "w", encoding="utf-8", newline="") as fh:
        fh.write(HEARTBEAT)
    with io.open(BACKLOG, encoding="utf-8", newline="") as fh:
        text = fh.read()
    if "R2581 PRODUCT window" in text:
        print("backlog already carries R2581")
        return 0
    text = ENTRY + "\n" + text
    with io.open(BACKLOG, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("heartbeat bytes=%d backlog bytes=%d"
          % (len(HEARTBEAT), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())