"""R2630 state append: six log lines, one tick, and the unchanged watermarks.

This window shipped ONE product face on the queue head the debt gate named
(product-face-R2628, state/queue/tech.md:653 prefix AC-EDMI1) and closed the
board row it discharged. Every number below was measured this window rather
than quoted from a note.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
NEW_ORDER = "2026-11-11 06:0x"

NEW_TOKENS = []

LINES = [
    "2026-11-11 R2630 PRODUCT window on the queue head the debt gate named "
    "(product-face-R2628, state/queue/tech.md:653 prefix AC-EDMI1, criteria "
    "AC-EDMI1..AC-EDMI6 pinned in that row at R2624 BEFORE any code). Five "
    "readings at open: git status EMPTY at HEAD 99d24dc2 equal to origin/main "
    "with no index.lock, ZERO unreplied @BigDomain rows in "
    "cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0), the "
    "content-addressed D-/C- decisions scan read tokens=189 with new=0 over "
    "323 rows, the group orders tail still at the 2026-11-11 06:0x row already "
    "judged knowledge-only at R2628, and benchmarks_refreshed 2026-11-10 sits "
    "one day inside the seven-day gate. debt_gate read CLAIM-FIRST "
    "item=product-face-R2628 opened=R2628 carried=2 stale=no open=42 first=1 "
    "with NO battery owed; queue_head named tech line 653 prefix AC-EDMI1 "
    "claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",

    "2026-11-11 R2630 THE GAP WAS RE-MEASURED BEFORE ANY CODE, through "
    "src/os/limits_matrix_reconcile_row_membership_R2630.py against private "
    "copies of the real document: a malformed matrix row whose FIRST CELL is "
    "not numeric gave doc_rows 0 against a 643-row registry (delta -643), "
    "because the scan decided table membership by a digit in the first cell. "
    "Three neighbour shapes were measured the same way and NAMED AS ALREADY "
    "CORRECT rather than claimed as gaps: a genuine second-table header stayed "
    "at delta 0, the footer/total row stayed at delta 0 and a malformed LAST "
    "row stayed at -1.",

    "2026-11-11 R2630 SHIPPED src/os/suite_matrix_reconcile.py extended "
    "in place plus its six-criteria suite "
    "src/os/test_suite_matrix_reconcile_row_membership.py. Table membership is "
    "now decided by the SEPARATOR row a header carries (a new "
    "is_second_table_header asks whether the next significant row is a "
    "separator of the SAME cell count) instead of by a digit in the first "
    "cell: a row no such separator follows is ONE non-row - a malformed data "
    "row, or the footer/total row - so every well-formed row after it is still "
    "counted and the count falls by one instead of collapsing, while a row "
    "that IS followed by a separator of its own width still ENDS the first "
    "table (the AC-EDMG1 law, re-proved on its own fixture). The header test "
    "runs BEFORE the data-shaped test so a genuine header carrying a numeric "
    "first cell is still read as a header. The shipped check face is asked "
    "exactly once per reading, unchanged.",

    "2026-11-11 R2630 PROOF measured not quoted: AC-EDMI1..AC-EDMI6 SUITE "
    "PASS 6/6 on the first run and 6/6 TWICE with identical criterion lines "
    "through the shipped capture callable (qa/suite-matrix-reconcile-row-"
    "membership-R2630.log, 1857 bytes, utf-8 LF, legs=2 identical=True "
    "adjacent=3 fails=0, digest 416AB5BAA29629DE) with SIX adjacent matrix "
    "suites green beside it (row-shape, table-shape, fence, fence-table, shape "
    "and the base reconcile suite, each 6/6 rc=0). The same limits script "
    "re-run AFTER the change reads delta -1 for the shape that used to "
    "collapse, with the three neighbour shapes unmoved. ONE measurement is "
    "named rather than smoothed: the first suite run read ROWS-MISMATCH on "
    "every criterion because the registry had already moved to 644 while the "
    "document still carried 643 rows - the shipped face telling the truth - so "
    "docs/sandbox-suite-matrix.md was regenerated through the shipped write "
    "face at the R2627 green leg (65817 bytes, 644 rows, 4840 criteria) BEFORE "
    "the evidence was captured, after which the shipped check read "
    "byte-identical at rc=0. REGISTRY 643/4834 -> 644/4840 by exactly one row, "
    "recounted by import.",

    "2026-11-11 R2630 BOARD AND DEBT: queue row 653 was closed through "
    "src/os/queue_close_R2630.py at its predicted and measured 1898873B -> "
    "1903678B with its DISCHARGED note, and ONE successor row was seeded as "
    "AC-EDMJ1..AC-EDMJ6 at line 654 from TWO limits MEASURED after the fix "
    "(qa/limits-matrix-reconcile-row-membership-next-R2630.log, 327 bytes): a "
    "second-table header whose separator carries a DIFFERENT cell count reads "
    "delta +1 and one carrying NO separator reads delta +1, while two adjacent "
    "non-numeric malformed rows read -2 and a numeric footer row reads 0 and "
    "are named as already correct. queue_head then read line 654 prefix "
    "AC-EDMJ1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, "
    "10/10. DEBT through the shipped writers: product-face-R2628 closed at its "
    "predicted and measured 200661B -> 200664B (line 369, open 42->41, "
    "done 309->310, readback ok), reconcile-battery-R2630 appended first=yes "
    "at the pre-registered 644 suites / 4840 criteria (200664B -> 201008B) and "
    "product-face-R2630 appended first=no (201008B -> 201294B), both readback "
    "ok, so the gate now names that battery first and the next window owes it "
    "on this committed tree BEFORE any further product byte.",

    "R2630 honest disclosures: (a) TWO product points on the Executive "
    "Protocol scale - a runnable reading with its own six-criteria suite and a "
    "measured before/after pair a maintainer can rerun - but NOTHING a CEO "
    "could newly open was built and no P-47 business surface moved, so every "
    "P-47 item still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) the gap was MEASURED at R2624 in that window own leg "
    "and re-measured here before any code, so this is a repair of a disclosed "
    "gap rather than a new discovery; (c) the pre-fix reading lives in this "
    "round log rather than in a file, because the same limits script was "
    "re-run after the change and overwrote its own output - named here instead "
    "of presented as a preserved artifact; (d) the two successor shapes both "
    "read +1 and are seeded rather than fixed; (e) Docker is absent on this "
    "host so no containerised bring-up of the sandbox faces is claimed; (f) "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items; (g) tasks.md was not touched, it is the P-47 canonical board; (h) "
    "BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell "
    "(carried ceo-pending physical item loop-s4u-reconcile).",

    "R2630 tokens: local=~14k api=0 api_reason=product window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, one debt gate plus queue "
    "head and floor read, one limits script measuring four shapes on private "
    "copies BEFORE any code, one in-place extension shipped with its six "
    "pre-registered criteria, one suite green 6/6 on the first run and twice "
    "through the shipped capture callable plus six adjacent suites, one "
    "registry row recounted by import, one designed document regeneration "
    "checked byte-identical, one successor limits script measuring four more "
    "shapes, one board row closed and one seeded through their shipped "
    "writers, three debt rows moved through their shipped writers, and the "
    "state/export/heartbeat closeout; zero cloud calls and zero external API "
    "touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    merged = sorted(set(list(data["last_dec_tokens"]) + NEW_TOKENS))
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    expected["last_order"] = NEW_ORDER
    expected["last_dec_tokens"] = merged
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    item_indent = None
    for line in lines[start + 1:end]:
        stripped = line.strip()
        if stripped.startswith('"'):
            item_indent = len(line) - len(line.lstrip(" "))
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = [" " * item_indent + json.dumps(item, ensure_ascii=False) + ","
                for item in LINES[:-1]]
    inserted.append(" " * item_indent
                    + json.dumps(LINES[-1], ensure_ascii=False))
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    out = _retick(out, data["tick"], expected["tick"])
    out = _reorder(out, data["last_order"], NEW_ORDER)
    out = _retokens(out, merged)
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2630_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s tokens=%d"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"], len(merged)))
    return 0


def _retick(text, old, new):
    needle = '"tick": %d' % int(old)
    if needle not in text:
        raise SystemExit("REFUSED tick field not found as %r" % needle)
    return text.replace(needle, '"tick": %d' % int(new), 1)


def _reorder(text, old, new):
    needle = '"last_order": %s' % json.dumps(old, ensure_ascii=False)
    if needle not in text:
        raise SystemExit("REFUSED order field not found as %r" % needle)
    return text.replace(needle, '"last_order": %s'
                        % json.dumps(new, ensure_ascii=False), 1)


def _retokens(text, merged):
    lines = state_io._lf_lines(text)
    head = None
    tail = None
    for index, line in enumerate(lines):
        if line.strip().startswith('"last_dec_tokens"'):
            head = index
        elif head is not None and line.strip().startswith("]"):
            tail = index
            break
    if head is None or tail is None:
        raise SystemExit("REFUSED last_dec_tokens block not found")
    closing = lines[tail]
    indent = len(lines[head + 1]) - len(lines[head + 1].lstrip(" "))
    block = [" " * indent + json.dumps(tok, ensure_ascii=False) + ","
             for tok in merged[:-1]]
    block.append(" " * indent + json.dumps(merged[-1], ensure_ascii=False))
    return state_io.EOL.join(lines[:head + 1] + block + [closing]
                             + lines[tail + 1:])


if __name__ == "__main__":
    sys.exit(main())
