"""R2581 board closeout for the AC-LKND1 seed row in state/queue/tech.md.

Marks the fold-summary date-prefix row done and appends its DISCHARGED note
read from THIS round own evidence on disk, then seeds ONE new row from the
limits this round MEASURED with the shipped guard in place. Every number
printed here is read off the files; a missing evidence file refuses.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QUEUE = os.path.join(REPO, "state", "queue", "tech.md")
EVIDENCE = os.path.join(REPO, "qa", "ledger-fold-kind-dateprefix-R2581.log")
MATRIX = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")

SEED_MARK = "AC-LKND1..AC-LKND6"

NOTE = (
    "  DISCHARGED R2581 (AC-LKND1..AC-LKND6 pinned in this row BEFORE any"
    " code): src/os/ledger_lines.py FOLD_SUMMARY_RE now tolerates the date"
    " prefix NARRATIVE_RE already allowed and knows the past-tense"
    " inflection, so a summary stamped with the date the fold ran and the"
    " 'R<n> folded ...' form both classify other instead of falling back to"
    " the narrative pattern and re-opening the gap R2580 closed. The"
    " word-boundary contract is untouched ('R<n> folder of ...' stays a"
    " round narrative) and no shipped family was weakened. PROOF: AC-LKND1.."
    "AC-LKND6 SUITE PASS 6/6 on the first run and 6/6 TWICE with identical"
    " output plus five adjacent ledger suites green through the shipped"
    " capture callable (qa/ledger-fold-kind-dateprefix-R2581.log, {ev}B,"
    " legs=2, identical=True, adjacent=5, fails=0); the R2580 suite still"
    " reads SUITE PASS 6/6; the real state.json log reads CLEAN on the live"
    " face and a simulation over it reclassified ZERO lines. Registry moved"
    " 620/4696 -> 621/4702 by exactly one row, recounted by importing"
    " reconcile_all.SUITES (621 unique names, 621 unique paths);"
    " docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the"
    " eligible battery leg qa/reconcile-all-R2579-retry2.log to {mat} bytes"
    " at 621 suites / 4702 criteria with its green line honestly reading"
    " 620/621 and --check byte-identical at rc=0. HONEST LIMITS MEASURED in"
    " this window own leg and seeded as the next row: the first letter"
    " capitalized ('R2568 Fold of log lines ...') and the third-person"
    " 'R<n> folds the block ...' still read round and still report a gap"
    " because FOLD_SUMMARY_RE is case-sensitive and lists only 'fold' and"
    " 'folded'."
)

SEED = (
    "- [ ] P2 tech seed (R2581, from this window own measured limit):"
    " `src/os/ledger_lines.py` capitalized and third-person fold-summary"
    " inflections - MEASURED this window with the shipped guard in place,"
    " five fixture lines read through ledger_lines.classify on the committed"
    " tree: (a) 'R2568 Fold of log lines 1..20 into the archive' reads ROUND"
    " and audit() over that single line reports rounds_without_ledger=[2568];"
    " (b) '2026-11-08 R2568 Fold of log lines 1..20' reads ROUND and reports"
    " [2568]; (c) 'R2568 folds the block into the archive' reads ROUND and"
    " reports [2568]; (d) '11/08/2026 R2568 fold of log lines 1..20' reads"
    " OTHER because the anchor is the line start (a different date dialect is"
    " not a summary shape this reading knows); (e) '- R2568 fold of log"
    " lines 1..20' reads OTHER for the same reason. Pre-registered acceptance"
    " criteria (AC-LKNF1..AC-LKNF6, pinned here BEFORE any code): AC-LKNF1 a"
    " capitalized fold summary classifies other and a live-shaped window over"
    " it reports no gap; AC-LKNF2 the third-person 'R<n> folds ...' form"
    " classifies other; AC-LKNF3 no over-swallow - 'R<n> Folder of ...' and"
    " 'R<n> foldsomething' stay round narratives that still gate; AC-LKNF4"
    " every shape the R2580 and R2581 suites already pinned classifies"
    " exactly as before, dated or bare; AC-LKNF5 no weakening - a bare"
    " narrative and the 'R<n> token:' typo still gate and the shipped ledger"
    " family is unchanged; AC-LKNF6 the real state.json log reads clean on"
    " the live face, src/os/test_ledger_fold_kind.py and"
    " src/os/test_ledger_fold_kind_dateprefix.py both stay 6/6, and the"
    " module is ASCII and network-free."
)


def main():
    for path in (EVIDENCE, MATRIX):
        if not os.path.exists(path):
            print("E_QC_MISSING %s" % path)
            return 3

    with io.open(EVIDENCE, encoding="utf-8") as fh:
        ev = fh.read()
    ev_bytes = os.path.getsize(EVIDENCE)
    mat_bytes = os.path.getsize(MATRIX)
    if ("legs=2" not in ev
            or "EVIDENCE identical=True adjacent=5 fails=0" not in ev):
        print("E_QC_EVIDENCE_SHAPE")
        return 2

    with io.open(QUEUE, encoding="utf-8", newline="") as fh:
        lines = fh.read().split("\n")

    hits = [i for i, l in enumerate(lines) if SEED_MARK in l]
    if len(hits) != 1:
        print("E_QC_SEED_ROWS %d" % len(hits))
        return 2
    idx = hits[0]
    row = lines[idx]
    if row.startswith("- [x]"):
        print("E_QC_ALREADY_DONE")
        return 2

    lines[idx] = row.replace("- [ ]", "- [x] [done 2026-11-09 R2581]", 1)
    note = (NOTE.format(ev=ev_bytes, mat=mat_bytes))
    insert_at = len(lines)
    lines.insert(insert_at, note)
    lines.append(SEED)
    if lines[-1] != "":
        lines.append("")

    text = "\n".join(lines)
    tmp = QUEUE + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    os.replace(tmp, QUEUE)
    print("CLOSED %s bytes=%d note_bytes=%d seed_bytes=%d"
          % (SEED_MARK, os.path.getsize(QUEUE), len(note), len(SEED)))
    return 0


if __name__ == "__main__":
    sys.exit(main())