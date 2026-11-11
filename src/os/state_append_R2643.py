"""state_append_R2643 - the R2643 product window narrative and tokens.

Every number below was measured off the tree in this window: the four shapes
before any byte, the suite and both parents through the shipped capture, the
registry import, the matrix byte count, the export verdict and the debt
register byte counts.
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
    "2026-11-11 R2643 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2641, state/queue/tech.md:660 prefix AC-EDWW1, criteria"
    " AC-EDWW1..AC-EDWW6 pinned in that row at R2638 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD d9b907ee equal to"
    " origin/main with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed D-/C-/P-/O-/T-/XL- decisions scan read tokens=189"
    " new=0 over 323 rows; the group orders tail moved to 2026-11-11 20:15"
    " (a BigStream mv0001 v727 row naming D03b and E04 takes, knowledge-only"
    " for this company); benchmarks_refreshed 2026-11-10 one day inside the"
    " seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2641"
    " opened=R2641 carried=2 stale=no first=1 open=43; queue_head named tech"
    " line 660 prefix AC-EDWW1 claimable=15 and queue_floor read FLOOR-MET at"
    " 5/5, 15/10, 10/10.",

    "R2643 THE FOUR SHAPES WERE RE-MEASURED BEFORE ANY BYTE with the R2638"
    " limit script src/os/limits_export_composed_landed_next_R2638.py, byte"
    " for byte the seed row numbers: a BOM landing whose body disagreed with"
    " the composed text read BOM-LANDING at delta=6 (a real content gap named"
    " as a BOM landing), a BOM landing carrying MIXED separators read"
    " BOM-LANDING with transport=mixed (the transport surviving only as a"
    " field), a UTF-16LE BOM read COMPOSED-MISMATCH at delta=14 and a"
    " truncated two byte BOM prefix read COMPOSED-MISMATCH at delta=2, while"
    " the EMPTY landing already read EMPTY-LANDING and is named as already"
    " correct rather than claimed as this window work.",

    "R2643 SHIPPED an IN-PLACE extension of src/os/export_composed_landed_face.py"
    " plus its own suite src/os/test_export_composed_landed_bom_precedence.py:"
    " four words are added (BOM-BODY-MISMATCH, BOM-TRANSPORT-MIXED,"
    " UTF16-BOM-LANDING, BOM-TRUNCATED) and the pinned order becomes EMPTY,"
    " UTF-16 BOM, TRUNCATED BOM, BOM (mixed / body gap / clean), MIXED, then"
    " the composed/landed compare, so a landing still earns exactly ONE word."
    " Two laws keep it honest: a truncated prefix is called truncated only"
    " when the REST of the payload really is the composed text, so a"
    " legitimate 0xef-leading UTF-8 payload is not accused, and a UTF-16"
    " marker is named as a marker without pretending a UTF-16 body can be"
    " measured against a UTF-8 composed text.",

    "R2643 PROOF measured not quoted: AC-EDWW1..AC-EDWW6 SUITE PASS 6/6"
    " twice identical through the shipped capture callable"
    " (qa/export-composed-landed-bom-precedence-R2643.log, 2121B, legs=2"
    " identical=True adjacent=2 fails=0) with BOTH parents green beside it"
    " (the AC-EDWV wordspace suite 6/6 and the AC-EDWT composed/landed suite"
    " 6/6), and the real export still reads VERDICT PASS at 403179B after the"
    " change with check_export_consistency reading pass=21 fail=0 VERDICT"
    " PASS, so no healthy face was reddened.",

    "R2643 ONE OWN DEFECT WAS MEASURED AND REPAIRED AT ITS BIRTH SITE INSIDE"
    " THIS WINDOW: the first suite run read AC-EDWW4 FAIL because the prefix"
    " walk took the SHORTEST matching strict prefix, so a two byte cut was"
    " measured as a one byte cut and read COMPOSED-MISMATCH; the longest"
    " matching prefix now wins, AC-EDWW4 asserts BOTH cuts, and the evidence"
    " file was captured AFTER the repair rather than beside the broken code.",

    "R2643 REGISTRY, DOCUMENT AND BOARD: the registry stands at 648 suites /"
    " 4864 criteria recounted by import (647 -> 648 suites, 4858 -> 4864"
    " criteria, 648 unique names and 648 unique paths) for exactly one new"
    " row. docs/sandbox-suite-matrix.md read ROWS-MISMATCH BEFORE any byte"
    " (doc-rows=647 against registry-rows=648 at 4864 criteria) and was then"
    " regenerated through the shipped write face from the R2638 green leg to"
    " 66331 bytes at 648 rows, after which --check read DOC-CURRENT at rc=0."
    " Row 660 was closed through src/os/queue_close_R2643.py at its predicted"
    " and measured 1914778B -> 1918709B with its DISCHARGED note, and ONE row"
    " was seeded from this window own MEASURED limits as AC-EDWX1..AC-EDWX6"
    " at line 661 (a truncated prefix under a MIXED body reads TRANSPORT-MIXED"
    " and loses the truncation fact; a UTF-16 marker with no body reads"
    " UTF16-BOM-LANDING; a BOM-only landing reads BOM-LANDING at delta=0; a"
    " UTF-16 payload with NO BOM reads COMPOSED-MISMATCH at delta=12; and a"
    " legitimate 0xef-start payload plus a clean LF landing both read PASS and"
    " are named as already correct); queue_head then read the new head at line"
    " 661 prefix AC-EDWX1 claimable=15 and queue_floor read FLOOR-MET at 5/5,"
    " 15/10, 10/10.",

    "R2643 DEBT through the shipped writers: product-face-R2641 closed at its"
    " predicted and measured 206399B -> 206402B (line 378, open 43->42,"
    " done 317->318, readback ok) and reconcile-battery-R2643 appended"
    " first=yes at the predicted 206402B -> 206693B (readback ok) at the"
    " pre-registered 648 suites / 4864 criteria, because this window moved"
    " product src bytes and one registry row and the R2168 mixed-tree rule"
    " puts the full battery on the committed tree BEFORE any further product"
    " byte.",

    "R2643 honest disclosures: (a) ONE product point on the Executive Protocol"
    " scale - a runnable face with its own six-criteria suite that a"
    " maintainer can rerun - but nothing a CEO could newly open and no P-47"
    " business surface moved, so every P-47 item still waits on CEO physical"
    " pieces (merchant id, mini-program appid/secret); (b) the four shapes"
    " were already MEASURED at R2638 and re-measured here, so this is a named"
    " gap being closed rather than a new discovery; (c) the export driver"
    " still collapses every non-PASS word into COMPOSED-MISMATCH, so the four"
    " new words live at the face and the CLI and are NOT yet surfaced in the"
    " driver RESULTS line - that is named rather than dressed up as wiring;"
    " (d) the battery is OWED next window at 648/4864 and was NOT run here,"
    " so the matrix document green line honestly reads 647/648 until that leg"
    " lands; (e) src/os/scan_five_still.py still crashes at its final"
    " [ORD-TOP] print on the GBK console (a BOM in the group orders row),"
    " unchanged and still carried, because the three judgments above it print"
    " first; (f) Docker is absent on this host so no containerised bring-up is"
    " claimed; (g) tasks.md was not touched, it is the P-47 canonical board;"
    " (h) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell for its S4U re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",

    "R2643 tokens: local=~20k api=0 api_reason=product window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, one debt gate read and"
    " one queue head plus floor read, one re-measurement of the four shapes"
    " before any code, one in-place extension of the shipped face plus one"
    " six-criteria suite, one own defect measured and repaired at its birth"
    " site with the evidence captured after, one capture through the shipped"
    " callable producing two identical legs with both parents green, one"
    " registry row recounted by import on four axes, one designed matrix"
    " ROWS-MISMATCH then one regeneration checked DOC-CURRENT, one real-export"
    " regression plus the consistency checker, one successor limits script"
    " measured after the fix and written as UTF-8 LF by the script itself, one"
    " board row closed and one seeded through their shipped writers, two debt"
    " rows moved through their shipped writers, and the state/export closeout;"
    " zero cloud calls and zero external API touches",
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
