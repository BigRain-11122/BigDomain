"""R2581 state.json tick/log append (product window on tech line 626 AC-LKND1)."""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

TICK = 2581
LAST_ORDER = "2026-11-09 00:59"

LINES = [
    "2026-11-09 R2581 PRODUCT window on the queue row the debt gate named"
    " (product-face-R2580, state/queue/tech.md:626 prefix AC-LKND1, criteria"
    " AC-LKND1..AC-LKND6 pinned in that row at R2580 BEFORE any code)."
    " Five-silence at open: git status EMPTY at HEAD 1a514249 equal to"
    " origin/main with no index.lock, zero @BigDomain rows in"
    " cph4/evolution-ledger.md, the content-addressed D-/C- decisions scan"
    " read 161 tokens against the stored 197-token baseline with new=0, the"
    " group orders tail had moved to 2026-11-09 00:59 with TWO rows in front"
    " of it (00:30 BigStream word-anchor repair and 00:59 BigStream TTS"
    " dispatch) which were read and judged knowledge-only for this company,"
    " benchmarks 2026-11-03 inside the seven-day gate. The debt gate read"
    " CLAIM-FIRST item=product-face-R2580 first=1 open=33 with no battery"
    " owed, and queue_floor read FLOOR-MET at 5/5, 12/10, 10/10.",
    "2026-11-09 R2581 DISCLOSED BEFORE THE CODE: src/os/queue_head.py read"
    " state/queue/tech.md:626 as NO-CRITERIA because it asks the prefix law"
    " in src/os/queue_row.py, whose SOFT_RE wants 'Criteria AC-...' and"
    " cannot see the parenthetical form 'criteria (AC-LKND1..AC-LKND6, pinned"
    " here ...)' the R2580 window authored - which is exactly why the debt"
    " gate had to name the row by hand. The blind spot was NOT repaired this"
    " round (it would reclassify seven older prose rows and move the queue"
    " order); it is named here, and this window own seed was re-phrased to"
    " the recognised form and re-measured through queue_row.scan_row as"
    " prefixed FORM-2 AC-LKNF1 before the closeout.",
    "2026-11-09 R2581 SHIPPED src/os/ledger_lines.py FOLD_SUMMARY_RE extended"
    " plus src/os/test_ledger_fold_kind_dateprefix.py. MEASURED before any"
    " code on the committed tree: '2026-11-08 R2568 fold of log lines 1..20'"
    " and 'R2568 folded the block into the archive' both classified round and"
    " audit() over each reported rounds_without_ledger=[2568], re-opening the"
    " exact gap R2580 closed. The guard now tolerates the date prefix"
    " NARRATIVE_RE already allowed and knows the past-tense inflection, so"
    " both are other; the word boundary is untouched ('R2568 folder of log"
    " lines' stays round and still gates) and a narrative that merely"
    " mentions the fold later in the line ('R2568 the fold disclosure"
    " shipped') stays round and still gates. A simulation over the real 65"
    " line log reclassified ZERO lines and kept it CLEAN.",
    "2026-11-09 R2581 PROOF measured not quoted: AC-LKND1..AC-LKND6 SUITE"
    " PASS 6/6 on the first run and 6/6 TWICE with identical output plus five"
    " adjacent ledger suites green (fold_kind 6/6, lines 8/8, archive 8/8,"
    " baseline 8/8, closeout 8/8) through the shipped capture callable"
    " (qa/ledger-fold-kind-dateprefix-R2581.log, 1560B, legs=2,"
    " identical=True, adjacent=5, fails=0, digest 060493330530B3EA); the R2580"
    " suite still reads SUITE PASS 6/6 inside AC-LKND6. REGISTRY 620/4696 ->"
    " 621/4702 by exactly one row, recounted by importing"
    " reconcile_all.SUITES (621 unique names, 621 unique paths);"
    " docs/sandbox-suite-matrix.md was regenerated stamp-aligned from the"
    " eligible battery leg qa/reconcile-all-R2579-retry2.log to 61681 bytes at"
    " 621 suites / 4702 criteria with its green line honestly reading 620/621"
    " and --check byte-identical at rc=0. BOARD: row 626 closed through"
    " src/os/queue_close_R2581.py at its measured 1820642B -> 1823890B with"
    " its DISCHARGED note, and ONE row was seeded from this window own"
    " MEASURED limits (a capitalized 'R2568 Fold of log lines' and the"
    " third-person 'R2568 folds the block' both still read round and report a"
    " gap; a different date dialect and a leading bullet read other for the"
    " line-start anchor) as AC-LKNF1..AC-LKNF6 at line 629; queue_head re-read"
    " line 615 prefix AC-PNAM1 claimable=12 and queue_floor read FLOOR-MET at"
    " 5/5, 12/10, 10/10. DEBT through the shipped writers:"
    " product-face-R2580 closed at its predicted and measured 184652B ->"
    " 184655B (line 331, open 33->32, done 280->281, readback ok),"
    " reconcile-battery-R2581 appended first=yes at the pre-registered 621"
    " suites / 4702 criteria (184655B -> 184828B) and product-face-R2581"
    " appended first=no (184828B -> 185016B), both readback ok, so the gate"
    " now names that battery first and the next window owes it on this"
    " committed tree BEFORE any further product byte.",
    "2026-11-09 R2581 honest disclosures: (a) TWO product points on the"
    " Executive Protocol scale - a runnable guard fix with its own"
    " six-criteria suite and a bounded live reading a maintainer can rerun -"
    " but NOTHING a CEO could newly open was built and no P-47 business"
    " surface moved, so every P-47 item still waits on CEO physical pieces"
    " (merchant id, mini-program appid/secret); (b) the two gaps were"
    " MEASURED at R2580 in that window own leg and re-measured here before"
    " any code, so this is a repair of a disclosed gap rather than a new"
    " discovery; (c) my own first evidence guard was wrong - the closer"
    " looked for 'legs=2 identical=True adjacent=5' while the shipped"
    " capture writes 'EVIDENCE identical=True adjacent=5 fails=0' - and the"
    " closer REFUSED rather than writing, which is the shipped fail-closed"
    " face working; the guard was corrected to the measured shape; (d) the"
    " queue_row parenthetical blind spot is disclosed above and was NOT"
    " repaired in this window; (e) Docker is absent on this host so no"
    " containerised bring-up of the sandbox faces is claimed; (f) the real"
    " 19.9 debit and the real msgSecCheck still wait on CEO physical items;"
    " (g) tasks.md was not touched, it is the P-47 canonical board; (h)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2581 tokens: local=~13k api=0 api_reason=product window - one"
    " five-silence scan with the decisions token scan, the group orders tail"
    " and the ledger face actually read, one debt gate read naming the"
    " product row, one queue head and floor read, one parser blind spot"
    " measured and disclosed, one pre-measurement of the two gap shapes on"
    " the committed tree, one guard extension shipped with its six"
    " pre-registered criteria, one suite green 6/6 and twice through the"
    " shipped capture callable plus five adjacent ledger suites, one"
    " zero-reclassification simulation over the real log, one registry row"
    " recounted by import, one stamp-aligned matrix regeneration checked"
    " byte-identical, one board row closed and one seeded through their"
    " shipped writers, three debt rows moved through their shipped writers,"
    " and the state/export/heartbeat closeout; zero cloud calls and zero"
    " external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2581 PRODUCT window" in text:
        raise SystemExit("already present")
    tail = "\n ]\n}"
    if text.count(tail) != 1:
        raise SystemExit("log tail anchor not unique")
    chunk = "".join(",\n  " + json.dumps(line, ensure_ascii=True)
                    for line in LINES)
    text = text.replace(tail, chunk + tail, 1)
    payload = json.loads(text)
    for line in LINES:
        assert line in payload["log"], "line missing after insert"
    assert payload["tick"] == TICK - 1, payload["tick"]
    payload["tick"] = TICK
    payload["last_order"] = LAST_ORDER
    text = json.dumps(payload, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("LOG appended=%d log=%d tick=%d bytes=%d crlf=%d" % (
        len(LINES), len(payload["log"]), payload["tick"],
        len(text.encode("utf-8")), text.count("\r")))
    return 0


if __name__ == "__main__":
    sys.exit(main())