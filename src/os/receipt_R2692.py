"""R2692 receipt line: push, export and the two gates re-read after it."""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    tick = int(data.get("tick", 0))
    lines = [
        "R2692 push and export: git push origin main read 873fab8f..67183ce9 "
        "main -> main and git rev-parse read HEAD equal to origin/main at "
        "67183ce9 with an EMPTY git status, so the dialect-marked face, its "
        "six-criteria suite, the two byte-identical evidence legs with two "
        "adjacent suites, the one registry row, the restamped matrix, the "
        "closed board row, the seeded AC-PNAQ1..AC-PNAQ6 row, the two debt "
        "rows and the log-block layout repair are all delivered; this receipt "
        "line lands in the follow-up commit it describes. The export was "
        "refreshed AFTER the state append and after the tick advance (the "
        "R2449/R2433 ordering law) through the shipped driver "
        "src/os/export_R2635.py to 406207B at tick 2684 with queue=CURRENT and "
        "queue_drifted=(none), and check_export_consistency read pass=21 "
        "fail=0 VERDICT PASS with the three CEO-visible lines derived rather "
        "than typed; it is re-derived again AFTER this line so the window own "
        "log count agrees with the document it is counted in. state_fold "
        "--check read FOLD-CLEAR at 76990B against the 78500B gate with margin "
        "1510 and 69 live log lines after fold 712 took the file 81056B -> "
        "76990B at a true round-block boundary (items 3..8, the complete R2683 "
        "verification block ending on its push line) with 2 tokens carried "
        "verbatim and the archive VERIFIED, and ledger_lines --check read "
        "VERDICT CLEAN with new_missing none and new_orphan none. ONE OWN "
        "DEFECT WAS BORN IN THE PREVIOUS WINDOW AND SURFACED HERE, AND IT IS "
        "NAMED RATHER THAN SMOOTHED: the R2691 closeout and this window first "
        "append wrote THIRTEEN log item lines at a 16-space indent "
        "(state_io.ITEM_INDENT) inside a log block whose own items sit at 2, "
        "so state_fold.split_layout refused the real file with E_SF_BAD_LAYOUT "
        "- it derives the indent from the first item and refuses a file whose "
        "items disagree. The repair is at the birth site and moves no content: "
        "every item line inside the block was rewritten to the indent the "
        "first item already used with the parse asserted EQUAL before and "
        "after (src/os/repair_layout_R2692.py, 81056 bytes, 13 lines moved) "
        "and state_io.ITEM_INDENT was set to 2 so the next appender cannot "
        "re-break it. The debt gate now names reconcile-battery-R2692 "
        "first=yes at the pre-registered 661 suites / 4942 criteria, so the "
        "next window owes that FULL battery on the committed tree BEFORE any "
        "further product byte, and the queue head this window leaves behind is "
        "state/queue/tech.md line 682 prefix AC-PNAQ1 with claimable 14 and "
        "the queue floor FLOOR-MET 5/5, 14/10, 10/10.",
    ]
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data.get("log") or []) + lines
    doc_lines = state_io._lf_lines(text)
    start, end = state_io._log_block(doc_lines)
    if not doc_lines[end - 1].strip().endswith(","):
        doc_lines[end - 1] = doc_lines[end - 1].rstrip() + ","
    inserted = [" " * state_io.ITEM_INDENT +
                json.dumps(item, ensure_ascii=False) for item in lines]
    out = state_io.EOL.join(doc_lines[:end] + inserted + doc_lines[end:])
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2692r_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(payload)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, PATH)
    if state_io.read_raw(PATH) != payload:
        print("REFUSED read-back mismatch")
        return 4
    print("RECEIPT ok bytes=%d log_len=%d" %
          (len(payload), len(expected["log"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
