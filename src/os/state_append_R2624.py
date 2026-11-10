"""R2624 state append: five log lines, one tick and the order watermark.

The round re-measured a disclosed row-law gap, repaired it at its birth site,
closed the seed row, seeded the successor row and moved three debt rows.
Every line below carries a measured number rather than a quoted one.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import state_io  # noqa: E402

PATH = os.path.join(HERE, "state.json")
NEW_ORDER = "2026-11-11 03:52"

LINES = [
    "2026-11-11 R2624 PRODUCT window on the queue head the debt gate named "
    "(product-face-R2623, state/queue/tech.md:652 prefix AC-EDMH1, criteria "
    "AC-EDMH1..AC-EDMH6 pinned in that row at R2621 BEFORE any code). Five "
    "readings at open: git status EMPTY at HEAD f271f7fc equal to origin/main "
    "with no index.lock, ZERO unreplied @BigDomain rows in "
    "cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0), the "
    "content-addressed decisions scan read tokens=182 with new=0 over 307 "
    "rows, the group orders tail max_ts read 2026-11-11 03:52 - an event-shift "
    "row carrying CEO-PROXY and PT-20261026 rows, knowledge-only for this "
    "company, so last_order advances to it - and benchmarks_refreshed "
    "2026-11-10 sits inside the seven-day gate. debt_gate read CLAIM-FIRST "
    "item=product-face-R2623 first=1 open=41 with NO battery owed, queue_head "
    "named tech line 652 prefix AC-EDMH1 claimable=15 and queue_floor read "
    "FLOOR-MET at 5/5, 15/10, 10/10.",

    "2026-11-11 R2624 THE GAP WAS RE-MEASURED BEFORE ANY BYTE with "
    "src/os/limits_matrix_reconcile_row_shape_R2624.py against private copies "
    "of the real document (qa/limits-matrix-reconcile-row-shape-R2624.log): a "
    "four-cell data row and a seven-cell data row inside the matrix table "
    "each read doc_rows 0 against a 642-row registry (delta -642, "
    "ROWS-MISMATCH) where the honest answer for one bad row is 641, while a "
    "genuine second-table header read delta 0 and a separator row inside the "
    "table read delta 0. SHIPPED src/os/suite_matrix_reconcile.py: a new "
    "DATA_HEAD_RE law treats a pipe+digits+pipe row that does not carry six "
    "cells as ONE non-row, so the count falls by one instead of to zero, a "
    "genuine second-table header still ENDS the first table and a separator "
    "row inside it still neither restarts nor ends it; every R2621 answer "
    "survives on the same fixtures.",

    "2026-11-11 R2624 PROOF measured not quoted: AC-EDMH1..AC-EDMH6 SUITE "
    "PASS 6/6 TWICE with identical criterion lines through the shipped "
    "capture callable (qa/suite-matrix-reconcile-row-shape-R2624.log, 1645B, "
    "legs=2 identical=True adjacent=2 fails=0, digest "
    "7B480522AEE30916) with the R2621 fence-table and the R2604 shape suites "
    "green beside it, and the same capture re-read after the change measuring "
    "delta -1 for both wrong-cell shapes. REGISTRY 642/4828 -> 643/4834 by "
    "exactly one row, recounted by import (643 unique names, 643 unique "
    "paths); docs/sandbox-suite-matrix.md was regenerated through the shipped "
    "write face from that registry at the R2622 green leg to 65699 bytes / "
    "643 rows and then read DOC-CURRENT at rc=0. BOARD: row 652 closed "
    "through src/os/queue_close_R2624.py at its predicted and measured "
    "1894548B -> 1898873B with its DISCHARGED note, and ONE row was seeded "
    "from this window own MEASURED limits as AC-EDMI1..AC-EDMI6 at line 653; "
    "queue_head re-read line 653 prefix AC-EDMI1 claimable=15 and queue_floor "
    "read FLOOR-MET at 5/5, 15/10, 10/10. DEBT through the shipped writers: "
    "product-face-R2623 was closed at its predicted and measured 199481B -> "
    "199484B (line 366, open 41->40, done 307->308, readback ok), "
    "reconcile-battery-R2624 was appended first=yes at the pre-registered 643 "
    "suites / 4834 criteria (199484B -> 199823B) and product-face-R2624 "
    "appended first=no (199823B -> 200288B), both readback ok, so the gate now "
    "names that battery first and the next window owes it on this committed "
    "tree BEFORE any further product byte (the R2168 mixed-tree rule).",

    "R2624 honest disclosures: (a) TWO product points on the Executive "
    "Protocol scale - a runnable row-law fix with its own six-criteria suite "
    "and a document a maintainer can open - but NOTHING a CEO could newly "
    "open was built and no P-47 business surface moved, so every P-47 item "
    "still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) the gap was MEASURED at R2621 in that window own leg "
    "and re-measured here before any code, so this is a repair of a disclosed "
    "gap rather than a new discovery; (c) my own first evidence capture "
    "digested the EMPTY string (E3B0C44298FC1C14) because this suite printed "
    "its criterion markers indented, so the markers were moved to column 0, "
    "the stale evidence deleted and the capture re-taken - disclosed rather "
    "than presented as a clean first try; (d) the document had to be "
    "regenerated BEFORE the suite could read green, because the registry "
    "moved by one row and the doctored fixtures then read STALE-CONTENT "
    "rather than ROWS-MISMATCH; (e) the shipped five-still scan crashed on a "
    "GBK console while printing a BOM from the group orders line - a display "
    "defect of that tool, not a reading failure, and its three readings are "
    "reported above as measured; (f) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed; (g) tasks.md was "
    "not touched, it is the P-47 canonical board; (h) BigDomain-OSLoop still "
    "needs an ELEVATED shell for its S4U re-registration (carried ceo-pending "
    "physical item loop-s4u-reconcile).",

    "R2624 tokens: local=~26k api=0 api_reason=product window - one "
    "five-silence scan with the content-addressed decisions scan, the group "
    "orders tail and the ledger face actually read, one debt gate plus queue "
    "head and floor read, one limits script measuring three shapes on private "
    "copies BEFORE any code, one row-law extension shipped in place with its "
    "own six pre-registered criteria, one suite green 6/6 and twice identical "
    "through the shipped capture after repairing my own empty-digest capture, "
    "one registry row recounted by import, one document regenerated through "
    "the shipped write face and checked DOC-CURRENT, one board row closed and "
    "one seeded through their shipped writers, three debt rows moved through "
    "their shipped writers, one fold at a true round block boundary with the "
    "archive verified, and the state/export/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def main():
    text = state_io.decode(state_io.read_raw(PATH))
    data = state_io.parse(text)
    expected = json.loads(json.dumps(data))
    expected["log"] = list(data["log"]) + list(LINES)
    expected["tick"] = int(data["tick"]) + 1
    expected["last_order"] = NEW_ORDER
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
    if state_io.parse(out) != expected:
        print("REFUSED payload moved")
        return 3
    payload = out.encode("utf-8")
    handle, temp = tempfile.mkstemp(dir=HERE, prefix=".r2624_")
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


if __name__ == "__main__":
    sys.exit(main())
