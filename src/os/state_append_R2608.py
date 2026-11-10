"""R2608 product-window closeout append: the shipped fence face and its proof."""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")

LINES = [
    "2026-11-10 R2608 PRODUCT window on the queue head the debt gate named (product-face-R2607, state/queue/tech.md:640 prefix AC-EDME1, criteria AC-EDME1..AC-EDME6 pinned there at R2606 BEFORE any code). Five readings at open: git status EMPTY at HEAD c5982070 equal to origin/main with no index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions scan unmoved, the group orders tail unchanged at the 2026-11-09 00:59 BigStream row, benchmarks 2026-11-03 at the edge of the seven-day gate; debt_gate read CLAIM-FIRST product-face-R2607 first=1 open=38, queue_head named tech line 640 prefix AC-EDME1 claimable=15 and queue_floor read FLOOR-MET 5/5 15/10 10/10.",
    "2026-11-10 R2608 THE FOUR LIMITS WERE RE-MEASURED BEFORE ANY CODE by re-running src/os/limits_suite_matrix_reconcile_shape_next_R2606.py and every one matched the row: a mixed-punctuation separator read shape=(6, None) and SEPARATOR-MISSING, a fenced matrix title read titles=2 and TITLE-REPEATED, a trailing-space bare title read titles=2 and TITLE-REPEATED, and --ceiling 1 over a pile with no PASS leg read RED-LEG with walk bounded=True decoded=1.",
    "2026-11-10 R2608 SHIPPED an in-place extension of src/os/suite_matrix_reconcile.py plus its own six-criteria suite src/os/test_suite_matrix_reconcile_fence.py: is_separator_row accepts ANY mix of punctuation characters as a separator (so '-=-=' is read and a width disagreement still refuses as HEADER-SHAPE naming BOTH widths); a new title_tables() reads the document line by line with fence state, so a title inside a fenced block is quoted text and a title that introduces no table is no title at all, and matrix_title_count now counts DISTINCT (header text, header width, separator width) signatures while matrix_shape reads the FIRST table outside fences; and a new _walk_miss() gives a walk that reached its DECLARED ceiling its own CEILING-STARVED word naming the ceiling on the read, the write and the compose paths while a pile whose every candidate was decoded keeps RED-LEG. TWO R2606 assertions were amended at their birth sites and that is named rather than hidden: the row-drop fixture pinned one literal data row INCLUDING its seconds, so it went inert the moment R2607 restamped the document and it now removes the first data row through the shipped row law, and the bounded-walk assertion moved from RED-LEG to CEILING-STARVED because AC-EDME4 renames exactly that state.",
    "2026-11-10 R2608 PROOF measured not quoted: AC-EDME1..AC-EDME6 SUITE PASS 6/6 on the first clean run and 6/6 TWICE with identical output through the shipped capture callable src/os/capture_R2608.py (qa/suite-matrix-reconcile-fence-R2608.log, 3305 bytes, legs=2, identical=True, adjacent=2, fails=0), with the R2606 shape suite and the R2601 reconciliation suite both green beside it, and a read-only live leg on the REAL tree reading DOC-CURRENT at 639/639 rows and 4810 criteria (qa/suite-matrix-reconcile-fence-live-R2608.log). REGISTRY 638/4804 -> 639/4810 by exactly one row, recounted by importing reconcile_all.SUITES (639 unique names, 639 unique paths); docs/sandbox-suite-matrix.md was regenerated from the CURRENT registry through this face own --write at the R2607 green leg to 65248 bytes at 639 rows and --check then read byte-identical.",
    "2026-11-10 R2608 BOARD AND DEBT through the shipped writers: row 640 was closed through src/os/queue_close_R2608.py at its predicted and measured 1878809B -> 1883309B with its DISCHARGED note, and ONE row was seeded from limits MEASURED this window as AC-EDMF1..AC-EDMF6 at line 642 (a data row inside a fence is still counted by the row law at doc_rows=640 against a 639-row registry; two titles with the SAME header text, one with and one without a separator row, count as 2 because the signature carries the separator width; two bare titles read 1 and the starved write path changes no byte, so those two are named as already correct rather than claimed); queue_head then read the new head at line 642 prefix AC-EDMF1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10. DEBT: product-face-R2607 was closed at its predicted and measured 196346B -> 196349B (line 358, open 39->38, done 301->302, readback ok) and reconcile-battery-R2608 was appended first=yes at the pre-registered 639 suites / 4810 criteria (196349B -> 196563B, readback ok), so the gate now names that battery first and the next window owes it on this committed tree BEFORE any further product byte.",
    "R2608 honest disclosures: (a) ONE product point on the Executive Protocol scale - a runnable face with its own six-criteria suite plus a live reading a maintainer can rerun - but NOTHING a CEO could newly open was built and no P-47 business surface moved, so every P-47 item still waits on CEO physical pieces (merchant id, mini-program appid/secret); (b) the four gaps were MEASURED at R2606 and re-measured here BEFORE any code, so this is a repair of a disclosed gap rather than a new discovery; (c) TWO pre-registered R2606 assertions had to change and both are named above - one because a literal row fixture went inert under a restamp, one because AC-EDME4 deliberately renames the bounded-walk state, so the R2606 suite is amended rather than described as untouched; (d) the row law is still NOT fence-aware and a separator-less same-header repeat still splits one table into two titles, which are the two successor limits seeded as AC-EDMF1/AC-EDMF2; (e) Docker is absent on this host so no containerised bring-up is claimed; (f) tasks.md was not touched, it is the P-47 canonical board; (g) BigDomain-OSLoop still needs an ELEVATED shell for its S4U re-registration (carried as the ceo-pending physical item loop-s4u-reconcile).",
    "R2608 tokens: local=~24k api=0 api_reason=product window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face actually read, one debt gate plus queue head and floor read, one re-measure of the four limits before any code, one face extension and one new six-criteria suite, two capture legs plus two adjacent suites, one live leg on the real tree, one registry row recounted by import, one document regenerated through the face own write, one board row closed and one seeded through its shipped writer, two debt rows moved through their shipped writers, one successor limits script measuring four shapes, two amended suite assertions disclosed, one fold at a true block boundary, and the state/export closeout; zero cloud calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["tick"] = int(data["tick"]) + 1
    expected["log"] = list(data["log"]) + list(LINES)
    lines = state_io._lf_lines(text)
    start, end = state_io._log_block(lines)
    for index in range(start):
        if lines[index].strip().startswith('"tick":'):
            lines[index] = ' "tick": %d,' % expected["tick"]
            break
    else:
        print("REFUSED no tick line")
        return 6
    if not lines[end - 1].strip().endswith(","):
        lines[end - 1] = lines[end - 1].rstrip() + ","
    inserted = []
    for index, item in enumerate(LINES):
        suffix = "," if index < len(LINES) - 1 else ""
        inserted.append(" " * state_io.ITEM_INDENT +
                        json.dumps(item, ensure_ascii=False) + suffix)
    out = state_io.EOL.join(lines[:end] + inserted + lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2608_")
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