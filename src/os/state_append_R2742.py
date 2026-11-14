"""state_append_R2742 - append this window's log lines through the canonical writer."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2742

LINES = [
    "2026-11-15 R2742 PRODUCT window on AC-DFOB1..AC-DFOB6 (state/queue/tech.md:703, "
    "pinned at R2501 BEFORE any code): shipped src/os/export_parity_difference_order_field.py "
    "plus its six-criteria suite and one evidence driver. Five readings at open: git status "
    "EMPTY at HEAD 4829e853 equal to origin/main with no index.lock; ZERO unreplied @BigDomain "
    "rows in the group ledger (its 30 BigDomain mentions are generic audit lines); the "
    "content-addressed decisions face read base=267 cur=65 new=0; the group orders tail is the "
    "carried 2026-11-14 closeout block, older than the 01:3x baseline; benchmarks_refreshed "
    "2026-11-14 inside the seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2741, "
    "queue_head read tech line=703 prefix AC-DFOB1 claimable=11, queue_floor read FLOOR-MET.",

    "R2742 THE BLIND SPOT WAS RE-MEASURED ON THE SHIPPED LAW BEFORE ANY BYTE and it is exactly "
    "as the R2501 seed claimed: export_closeout_gate_parity.first_difference reads the shape "
    "word bytes for {\"x\": 1, \"y\": 2} against {\"y\": 2, \"x\": 1} while a value difference "
    "reads y. This face asks that law ON ITS MODULE at CALL time, publishes the answer unchanged "
    "in differs, and adds order_field naming the FIRST KEY THAT MOVED, proved in BOTH orders on "
    "four shapes (two-key x then y, three-key b then c, nested a.x then a.y, list rows[0].x then "
    "rows[0].y); a value difference keeps the shipped field and claims no order, byte-identical "
    "text reads IDENTICAL, an unparseable pair keeps the shape word, and a whitespace-only "
    "difference is named FORMAT rather than VALUE so the verdict is never reached without a "
    "measurement.",

    "R2742 PROOF: AC-DFOB1..AC-DFOB6 SUITE PASS 6/6 twice through its own process with an "
    "IDENTICAL digest DC582D20F8A0EA12 (qa/export-parity-difference-order-field-R2742b.log, "
    "8139B, utf-8, landed BY the shipped capture callable) and three adjacent suites green at "
    "rc=0. The first evidence leg landed at ...R2742.log is KEPT as a red artifact and is not "
    "hidden: two adjacent suites read FAIL at rc=0 because the verdict expression demanded a "
    "'SUITE PASS' line and one of them prints its own suite label while the other prints no "
    "suite line at all; the verdict was repaired at that birth site to trust the exit code and "
    "veto only on a printed FAIL row, and the corrected log landed at a NEW path ending R2742b "
    "rather than relaunching over the same one.",

    "R2742 LIVE ON THE REAL DOCUMENT: docs/status-export.json against itself reads IDENTICAL "
    "differs=(none) at 411953B, and the SAME document re-emitted in sorted key order reads "
    "differs=bytes ORDER-ONLY order_field=export_ts at 410805B - so on the actual CEO-facing "
    "artifact the shipped law alone answered nothing and this face names the key. REGISTRY "
    "675/5026 -> 676/5032 measured BY IMPORT on four axes (676 unique names, 676 unique paths); "
    "suite_matrix --check first read stale with NO byte written, and after a stamp-aligned "
    "regeneration citing qa/reconcile-all-R2739.log the document reads 71635B at 676 suites / "
    "5032 criteria with --check byte-identical rc=0, carrying green=675/676 because the new "
    "suite has not yet run inside a battery - named here so a reader does not read it as drift.",

    "R2742 BOARD AND DEBT THROUGH THE SHIPPED WRITERS: tech row 703 closed DISCHARGED R2742 "
    "(717 lines, 1996473B) and the MEASURED head is now state/queue/tech.md:713 prefix AC-LKNF1 "
    "with claimable 10 and queue_floor still MET 5/5 10/10 10/10, so no seed was owed. "
    "product-face-R2741 closed (open 36->35, readback ok); reconcile-battery-R2742 appended "
    "first=yes because this window moved product src and one registry row, so the R2168 "
    "mixed-tree rule owes a full battery on the committed tree BEFORE the next product byte; "
    "product-face-R2742 was appended first=no naming row 704 and was then CLOSED AND REPLACED by "
    "product-face-R2742b because queue_head reads row 704 as NO-CRITERIA (its criteria live in "
    "prose), so the successor names the head that measurement actually returns. debt_gate now "
    "reads CLAIM-FIRST reconcile-battery-R2742.",

    "R2742 ONE OWN DEFECT WAS BORN HERE AND WAS REPAIRED AT ITS BIRTH SITE, beside the evidence "
    "verdict one named above: the AC-DFOB5 read-only scanner flagged sys.stdout.write and "
    "str.replace as disk mutations, so a read-only face read FAIL. The rule was restated per "
    "RECEIVER (console writes allowed, os.replace separated from str.replace, mutation verbs "
    "blocked outright) and the criterion was not loosened - the face still has exactly one "
    "open() call and it is read-binary.",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == TICK
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    sys.stdout.write("APPENDED tick=%s log %d->%d ok=%s\n"
                     % (back.get("tick"), before, len(back.get("log") or []),
                        ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
