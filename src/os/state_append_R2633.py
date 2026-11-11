"""state_append_R2633 - the R2633 product window's own record.

Every number was read off the tree after the work landed.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "2026-11-11 R2633 PRODUCT window on the queue head the debt gate named"
    " first (product-face-R2632, state/queue/tech.md:654 prefix AC-EDMJ1,"
    " AC-EDMJ1..AC-EDMJ6 pinned there at R2630 BEFORE any code). Five"
    " readings at open: git status EMPTY with no index.lock, ZERO unreplied"
    " @BigDomain rows in cph4/evolution-ledger.md (31 BigDomain mentions,"
    " none unreplied through the shipped scan), the content-addressed D-/C-/"
    " P-/O-/T-/XL- decisions scan read tokens=191 against a 232-token"
    " baseline with new=0 over 447 rows, the group orders tail still at the"
    " 2026-11-11 06:0x committee row already judged knowledge-only for this"
    " company (a bm-b physical power-on reminder), and benchmarks_refreshed"
    " 2026-11-10 sitting one day inside the seven-day gate. debt_gate read"
    " CLAIM-FIRST item=product-face-R2632 opened=R2632 first=1 open=43;"
    " queue_head named tech line 654 prefix AC-EDMJ1 claimable=15 and"
    " queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2633 PRODUCT SHIPPED: the row walk of src/os/suite_matrix_reconcile.py"
    " now REFUSES to absorb a block it cannot classify. A table-shaped run"
    " that opens with a header and carries NO separator of its own width ENDS"
    " the first table and names itself - STRAY-HEADER with BOTH widths when a"
    " separator of another width follows (E_EDMJ_STRAY), HEADER-UNSEPARATED"
    " naming the absent separator when none follows (E_EDMJ_UNSEP) - and the"
    " answer carries the first table own doc_rows rather than an inflated"
    " number. The header is recognised by its CELLS: a matrix data row always"
    " carries a numeric criteria cell and a numeric seconds cell, so a pipe"
    " row whose cells are ALL non-numeric is a header, while AC-EDMI1 own"
    " malformed row (non-numeric FIRST cell, numeric 4th and 6th) is still"
    " ONE non-row and never ends the table. MEASURED BEFORE any byte on this"
    " tree with src/os/limits_matrix_reconcile_row_membership_next_R2630.py:"
    " narrow-separator header delta +1, no-separator header delta +1, two"
    " adjacent malformed rows -2, numeric footer 0. MEASURED AFTER with"
    " src/os/limits_matrix_reconcile_second_table_separator_R2633.py"
    " (qa/limits-matrix-reconcile-second-table-separator-R2633.log): both"
    " header shapes delta 0 with problem=(6, 2) and (6, None), the two"
    " adjacent malformed rows still -2 with no problem, the numeric footer"
    " still 0. Proof: AC-EDMJ1..AC-EDMJ6 SUITE PASS 6/6 TWICE identical"
    " through the shipped capture callable"
    " (qa/suite-matrix-reconcile-second-table-separator-R2633.log, 2597"
    " bytes, legs=2 identical=True adjacent=6 fails=0, digest"
    " FB8528404DDBA127) with six adjacent matrix suites green beside it"
    " (row-membership, row-shape, fence-table, fence-rows, table-shape,"
    " shape, each 6/6 rc=0). REGISTRY 644/4840 -> 645/4846 by exactly one"
    " row, recounted by import, and docs/sandbox-suite-matrix.md was"
    " regenerated from that registry through the shipped write face at the"
    " R2631 green leg to 65960 bytes / 645 rows / 4846 criteria, after which"
    " --check read byte-identical at rc=0 and the live report read"
    " DOC-CURRENT. Board 654 closed with its DISCHARGED block and AC-EDMK1.."
    "AC-EDMK6 seeded from this window own measured limit; queue_head now"
    " names line 658 prefix AC-EDWT1 and queue_floor still reads FLOOR-MET."
    " DEBT through the shipped writers: product-face-R2632 closed (line 372,"
    " open 43->42, done 311->312) and reconcile-battery-R2633 appended"
    " first=yes, because one registry row and one product src byte moved, so"
    " the R2168 mixed-tree rule puts a FULL BATTERY at the pre-registered 645"
    " suites / 4846 criteria on the committed tree BEFORE any further product"
    " byte.",
    "R2633 honest disclosures: (a) the window is a P2 tech face on a"
    " reconciliation reader rather than a CEO-visible product surface, so no"
    " product point on the Executive Protocol scale is claimed beyond the"
    " working face itself; (b) ONE own defect was caught in the suite and"
    " repaired at its birth site rather than by loosening an assertion -"
    " AC-EDMJ4 first handed the check face a fixture whose ROW COUNT differed"
    " and read ROWS-MISMATCH where the content word was needed, so the"
    " fixture became a count-preserving content difference; (c) the capture"
    " callable refused a SECOND invocation with E_EVC_EXISTS rather than"
    " overwriting the green evidence, so the file on disk is the first"
    " measured leg pair and no rewrite is claimed; (d) two driver errors were"
    " made and fixed inside the shipped faces' own rules - the round label"
    " must read R2633 and the suite path is resolved against the repo root -"
    " and neither touched product logic; (e) this window ran past its"
    " twenty-five minute budget and that overrun is named rather than hidden;"
    " (f) the matrix document green line honestly reads 644/645 because the"
    " stamping leg predates this suite, and that is the shipped self-describing"
    " form rather than a defect; (g) the real 19.9 debit and the real"
    " msgSecCheck still wait on CEO physical items; (h) BigDomain-OSLoop still"
    " reads InteractiveToken and needs an ELEVATED shell for its S4U"
    " re-registration (carried ceo-pending physical item loop-s4u-reconcile);"
    " (i) tasks.md was not touched, it is the P-47 canonical board.",
    "R2633 tokens: local=~21k api=0 api_reason=product window - five quiet"
    " readings at open with the content-addressed decisions scan, the group"
    " orders tail and the ledger face; one debt gate read and one queue head"
    " plus floor read on all three lines; one pre-fix limit re-measurement"
    " reproducing +1/+1 and one post-fix measurement reading 0/0 with both"
    " problems named; one module edit adding the stray-header law and"
    " doc_rows_scan; one suite written and registered as exactly one row; one"
    " designed suite FAIL at AC-EDMJ4 repaired at its birth site then 6/6;"
    " one capture through the shipped callable producing two identical legs"
    " with six adjacent suites green; one document regeneration through the"
    " shipped write face and one byte-identical --check; one board row closed"
    " with its DISCHARGED block and one seed row pinned; one debt row closed"
    " and one opened through their shipped writers; one successor limit"
    " measured (numbered second-table header counted as a data row, delta"
    " +2); and the state/export/heartbeat closeout; zero cloud calls and zero"
    " external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"])
    print("APPEND tick=%d lines=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
