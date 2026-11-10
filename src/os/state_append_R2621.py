"""R2621 product closeout append: the table-aware row law and the named fence
law, its six-criteria suite, the document regeneration, the board and the debt.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-11 R2621 PRODUCT window on the queue head the debt gate named (product-face-R2620, state/queue/tech.md:650 prefix AC-EDMG1, criteria AC-EDMG1..AC-EDMG6 pinned in that row at R2616 BEFORE any code). Five readings at open: git status EMPTY at HEAD 1d9a00c4 equal to origin/main with no index.lock, ZERO @BigDomain rows in cph4/evolution-ledger.md, the content-addressed D-/C-/T- decisions scan read 184 file tokens against the 225-token baseline with new=0 over 426 rows, the group orders tail unchanged at its 2026-11-10 03:52 row so last_order stands, and benchmarks_refreshed 2026-11-10 inside the seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2620 first=1 open=40 with NO battery owed, queue_head named tech line 650 prefix AC-EDMG1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "2026-11-11 R2621 THE THREE LIMITS WERE RE-MEASURED BEFORE ANY PRODUCT BYTE through src/os/limits_matrix_reconcile_fence_table_R2621.py against private copies of the REAL document (qa/limits-matrix-reconcile-fence-table-R2621.log, 391B, utf-8 LF after a transcode of the shell own UTF-16), and every one matched the row: (a) a data-shaped row in a SECOND unfenced table was counted, doc_rows 641 -> 642 against a 641-row registry, verdict ROWS-MISMATCH; (b) a fence opened and never closed was never named, delta 0 with verdict STALE-CONTENT and shape_named=False; (c) a four-backtick fence carrying a three-backtick line toggled TWICE, delta 1 and verdict ROWS-MISMATCH. So this is a repair of a disclosed gap, not a new discovery.",
    "2026-11-11 R2621 SHIPPED src/os/suite_matrix_reconcile.py extended IN PLACE plus src/os/test_suite_matrix_reconcile_fence_table.py. doc_rows is now TABLE-AWARE as well as fence-aware: rows are counted only inside the FIRST table introduced by the shipped matrix title, a blank line inside that table is tolerated (the artefact of deleting a row) and a real second header ENDS the first table. A new fence_scan names two malformations the blind toggle hid: an opening mark never closed is refused as FENCE-UNCLOSED naming the LINE it was opened on, and a closing mark SHORTER than the mark that opened the block is refused as FENCE-NESTED naming BOTH widths. report() asks the fence law before any row count, write() refuses to rewrite a document with either malformation, and the CLI prints one word with the offending line or both markers.",
    "2026-11-11 R2621 PROOF measured not quoted: AC-EDMG1..AC-EDMG6 SUITE PASS 6/6 on the first run after the document regeneration and 6/6 TWICE with identical output plus TWO adjacent suites green (the R2616 fence-rows parent 6/6 and the R2608 fence suite 6/6) through the shipped capture writer src/os/capture_R2621.py (qa/suite-matrix-reconcile-fence-table-R2621.log, 3400B, utf-8 bom=False crlf=0 lone_cr=0 nul=0, legs=2, identical=True, adjacent=2, fails=0). The same three shapes re-read through the CHANGED law inside that leg read delta 0 on all three with FENCE-UNCLOSED and FENCE-NESTED both NAMED. My own first run was 2/6 and two of those three reds were mechanical rather than legal: the registry had moved by one row while the document had not (healed by regenerating it through the shipped write face) and my own registration literal did not match the multi-line registry format (repaired in the TEST).",
    "2026-11-11 R2621 REGISTRY, DOCUMENT, BOARD AND DEBT: the registry moved by ONE row to 642 suites / 4828 criteria, recounted by importing reconcile_all.SUITES rather than trusted (642 unique names, 642 unique paths). docs/sandbox-suite-matrix.md read ROWS-MISMATCH BY DESIGN BEFORE any byte was written (doc-rows=641 against registry-rows=642 at 4828 criteria, rc=2) and was then regenerated through the shipped write face at the R2616 green leg to 65597 bytes at 642 rows, after which --check read DOC-CURRENT at rc=0. Board row 650 was closed through src/os/queue_close_R2621.py at its predicted and measured 1890138B -> 1894548B with its DISCHARGED note, and ONE row was seeded from this window own MEASURED limits as AC-EDMH1..AC-EDMH6 at line 652 (ONE malformed data row inside the matrix table collapses the count to ZERO, delta -642, because the scan breaks on the first non-data row as if it were another table header; a TILDE fence and a bare row after the last table were measured delta 0 and are named as already safe rather than claimed); queue_head then read the new head at line 652 prefix AC-EDMH1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10. DEBT through the shipped writers: product-face-R2620 closed at its predicted and measured 198259B -> 198262B (line 363, open 40->39, done 305->306, readback ok), reconcile-battery-R2621 appended first=yes at the pre-registered 642 suites / 4828 criteria (198262B -> 198559B) and product-face-R2621 appended first=no (198559B -> 198786B), both readback ok, so the gate now names that battery first and the next window owes it on this committed tree BEFORE any further product byte.",
    "R2621 honest disclosures: (a) TWO product points on the Executive Protocol scale - a runnable law extension with its own six-criteria suite and a live document a maintainer can open - but NOTHING a CEO could newly open was built and no P-47 business surface moved, so every P-47 item still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) the three gaps were MEASURED at R2616 in that window own leg and re-measured here BEFORE any code, so this repairs a disclosed gap rather than discovering one; (c) my own first suite run read 2/6 and the R2616 parent read 3/6 for the SAME mechanical reason - the registry had 642 rows while the document still carried 641 - and that was healed by regenerating the document through the shipped write face, not by loosening an assertion; (d) ONE genuine defect of my own new law was caught by the R2616 parent on its first run and repaired in the CODE: the first table scan ended on a blank line, so a document that merely DELETED a row read zero rows; that regression is why AC-EDMH1 exists as the successor seed; (e) the battery is OWED next window and the matrix document carries the honest 641/642 green line from the R2616 leg until that leg regenerates it; (f) TWO evidence files were written by a shell redirection in UTF-16 and were TRANSCODED to utf-8 by src/os/transcode_R2621.py rather than re-measured - the bytes are the measured output and only the encoding changed, which is named rather than smoothed; (g) Docker is absent on this host so no containerised sandbox bring-up is claimed; (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2621 tokens: local=~34k api=0 api_reason=product window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face actually read, one debt gate plus queue head and floor read, one limits script measuring the three seeded shapes on private copies BEFORE any code, one face extended in place with its six pre-registered criteria, one own regression caught by the parent suite and repaired in the code, one suite green 6/6 twice identical plus two adjacent suites through the shipped capture writer, one registry row recounted by import on four axes, one designed document mismatch then one regeneration through the shipped write face judged DOC-CURRENT, one board row closed and one seeded through their shipped writers, three debt rows moved through their shipped writers, one transcoder for two shell-written logs, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    touched_tick = False
    for index in range(start):
        stripped = lines[index].strip()
        if stripped.startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            touched_tick = True
    if not touched_tick:
        print("REFUSED no tick line")
        return 6
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
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2621_")
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
