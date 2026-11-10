"""R2616 product closeout append: the fence-aware row law and header-text
table identity, its six-criteria suite, the document regeneration, the board
and the debt."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
NEW_ORDER = "2026-11-10 03:52"

LINES = [
    "2026-11-10 R2616 PRODUCT window on the queue head the debt gate and the queue both named (product-face-R2615, state/queue/tech.md:646 prefix AC-EDMF1, criteria AC-EDMF1..AC-EDMF6 pinned in that row at R2608 BEFORE any code). Five readings at open: git status EMPTY at HEAD ea808bba equal to origin/main with no index.lock, ZERO @BigDomain rows in cph4/evolution-ledger.md, the content-addressed D-/C- decisions scan read 181 file tokens against the stored 222-token baseline with new=0 over 426 rows, the group orders tail had moved to 2026-11-10 03:52 carrying FIVE event rows (CLOCK-SKEW plus STARVED-EXEC on bm-b, the bm-c idle-gate self-lock and its FIXED repair, the fallback-card silence root cause, and the R29b self-refutation) which were READ and judged knowledge-only for this company because none names BigDomain, so last_order moves to 2026-11-10 03:52 with that judgement recorded rather than left at 11-09; benchmarks 2026-11-10 current inside the seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2615 first=1 open=39 with NO battery owed (registry unmoved at 640/4816 by import), queue_head named tech line 646 prefix AC-EDMF1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "2026-11-10 R2616 THE FOUR LIMITS WERE RE-MEASURED BEFORE ANY PRODUCT BYTE through src/os/limits_matrix_reconcile_fence_rows_next_R2616.py against private copies of the REAL document (qa/limits-matrix-reconcile-fence-rows-next-R2616.log), and every one matched the row: (a) a data-shaped row inside a ``` block was counted, doc_rows 640 -> 641 against a 640-row registry, so a document that only QUOTED a row read ROWS-MISMATCH; (b) the same table repeated WITHOUT its separator row counted as TWO titles (mixed titles=2 -> TITLE-REPEATED-able) because the table signature carried the separator width; (c) two bare titles introduced no table and read ONE title; (d) the write path over a starved walk read CEILING-STARVED and changed no byte, so (c) and (d) are NAMED as already correct rather than claimed as gaps.",
    "2026-11-10 R2616 SHIPPED src/os/suite_matrix_reconcile.py extended IN PLACE plus src/os/test_suite_matrix_reconcile_fence_rows.py, and the same four limits re-read through the changed law: (a) doc_rows 641 -> 641, delta 0, quoted_counted=False; (b) mixed titles=1, TITLE-REPEATED=False; (c) titles=1 unchanged; (d) CEILING-STARVED written=False bytes_changed=False unchanged. The row scan now toggles on the ``` marker and skips everything inside a fence, so a quoted data row is example text and not a matrix row; and a table is identified by its HEADER TEXT and WIDTH instead of by its separator width, so the same table repeated without its separator row is the SAME table while a table with DIFFERENT header text is still a second table and still refuses TITLE-REPEATED naming the count.",
    "2026-11-10 R2616 PROOF measured not quoted: AC-EDMF1..AC-EDMF6 SUITE PASS 6/6 on the first coherent run and 6/6 TWICE with identical output plus THREE adjacent suites green through the shipped capture callable (qa/suite-matrix-reconcile-fence-rows-R2616.log, 1824B, legs=2, identical=True, adjacent=3, fails=0, digest 8BF6A2A18FFF1898); the adjacent readings are os-suite-matrix-reconcile-fence 6/6, os-suite-matrix-reconcile-shape 6/6 and the sandbox matrix suite 16/16. A BOUNDED live leg on the REAL tree read-only (qa/suite-matrix-reconcile-fence-rows-live-R2616.log) reads doc 65483B with rows_outside_fence=641 rows_inside_fence=0, registry 641/4822, titles=1 and verdict DOC-CURRENT exit=0, and measures the SAME two fixtures on the same tree: a quoted data row reads rows_inside=1 while doc_rows stays 641 and the verdict falls back to the shipped check own content word STALE-CONTENT rather than ROWS-MISMATCH, and the same-header-no-separator repeat reads titles=1 instead of TITLE-REPEATED.",
    "2026-11-10 R2616 REGISTRY, DOCUMENT, BOARD AND DEBT: the registry moved by ONE row to 641 suites / 4822 criteria, recounted by importing reconcile_all.SUITES rather than trusted (641 unique names, 641 unique paths). docs/sandbox-suite-matrix.md was regenerated through this face own shipped write path to 65483 bytes at 641 rows / 4822 criteria keeping the document stamp and its recorded provenance, and the shipped check face then read DOC-CURRENT at rc=0 with the multi-backtick fence line now quoted rather than drifted. Board row 646 was closed through src/os/queue_close_R2616.py at its predicted and measured 1886244B -> 1887978B with its DISCHARGED note, and ONE row was seeded from this window own MEASURED limits as AC-EDMG1..AC-EDMG6 at line 650 (a second UNFENCED table data row is still counted delta 1; an UNCLOSED fence is never named and reads STALE-CONTENT delta 0; a four-backtick fence carrying a three-backtick line toggles TWICE and counts a quoted row delta 1 -> ROWS-MISMATCH); queue_head then read the new head at line 650 prefix AC-EDMG1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10. DEBT through the shipped writers: product-face-R2615 closed at its predicted and measured 197249B -> 197252B (line 360, open 39->38, done 303->304, readback ok), reconcile-battery-R2616 appended first=yes at the pre-registered 641 suites / 4822 criteria (197252B -> 197624B) and product-face-R2616 appended first=no (197624B -> 197826B), both readback ok, so the gate now names that battery first and the next window owes it on this committed tree BEFORE any further product byte (the R2168 mixed-tree rule, because this window moved product src bytes, one registry row and the document).",
    "R2616 honest disclosures: (a) TWO product points on the Executive Protocol scale - a runnable law extension with its own six-criteria suite and a bounded live reading a maintainer can rerun - but NOTHING a CEO could newly open was built and no P-47 business surface moved, so every P-47 item still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) the four gaps were MEASURED at R2608 in that window own leg and re-measured here before any code, so this is a repair of a disclosed gap rather than a new discovery; (c) AC-EDMF1 own DOC-CURRENT case patches the SHIPPED check face green for that ONE reading, because the criterion is about the ROW LAW and not about the shipped face - the same fixture is then measured with the check face UNTOUCHED (STALE-CONTENT) and AC-EDMF4 proves the check face is still asked exactly once per reading (measured check-asked=1 code=2 on a content-doctored copy); that patch is disclosed here rather than buried; (d) my own first suite run read 3/6, not because the law was wrong but because I had added a registry row and left the document one row behind, so the doc was regenerated through the shipped write face before any claim, and two of my own fixtures were wrong (the narrow-separator doctor picked the four-cell SUMMARY table instead of the six-cell matrix table, and the content doctor searched for 'PASS' in a state cell that reads 'green') - both were repaired in the TEST and no assertion was loosened; (e) a data row inside a SECOND table is still counted, which is the measured limit seeded as AC-EDMG1 rather than hidden; (f) Docker is absent on this host so no containerised bring-up of the sandbox faces is claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items; (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2616 tokens: local=~24k api=0 api_reason=product window - one five-silence scan with the content-addressed decisions diff, the ledger face and the group orders tail actually read and five new event rows judged knowledge-only, one debt gate plus queue head and floor read, one limits script measuring four seeded shapes on private copies BEFORE any code, one face extended in place with its six pre-registered criteria, the same four limits re-read through the changed law, one suite green 6/6 twice identical plus three adjacent suites through the shipped capture callable, one bounded read-only live leg measuring the same fixtures on the real tree, one registry row recounted by import, one document regenerated through the shipped write face and judged DOC-CURRENT, one board row closed and one seeded through their shipped writers, three debt rows moved through their shipped writers, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    expected["last_order"] = NEW_ORDER
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    touched_tick = touched_order = False
    for index in range(start):
        stripped = lines[index].strip()
        if stripped.startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            touched_tick = True
        elif stripped.startswith('"last_order":'):
            lines[index] = ' "last_order": %s,' % json.dumps(NEW_ORDER)
            touched_order = True
    if not touched_tick:
        print("REFUSED no tick line")
        return 6
    if not touched_order:
        print("REFUSED no last_order line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    # MEASURED, not assumed: this file writes its log items at indent 2,
    # while state_io.ITEM_INDENT is 16 and the block opener sits at indent 1.
    # Using either constant breaks the layout reader (E_SF_BAD_LAYOUT log item
    # lines do not match log length), so the indent is taken from an item
    # already on disk.
    item_indent = None
    for line in lines[start:end]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and not stripped.startswith('"log"'):
            item_indent = len(line) - len(stripped)
            break
    if item_indent is None:
        print("REFUSED no item line to measure the indent")
        return 6
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * item_indent +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2616_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    after = state_io.report(PATH)
    print("APPEND ok tick=%d bytes=%d log_len=%d layout_ok=%s"
          % (expected["tick"], after["bytes"], after["log_len"],
             after["layout_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
