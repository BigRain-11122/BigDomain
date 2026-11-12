"""state_append_R2657 - the R2657 product window narrative and tokens.

Every number below was measured off the tree in this window: the pre-fix and
post-fix limit logs, the capture evidence bytes, the registry recount by
import, the matrix byte counts on both sides of the regeneration, the board
byte counts across the row close, and the debt register byte counts.
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
    "2026-11-12 R2657 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2655, state/queue/tech.md:664 prefix AC-EDXA1, criteria"
    " AC-EDXA1..AC-EDXA6 pinned in that row at R2653 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD 956acfb9 equal to origin/main"
    " with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed decisions scan read rows=117 tokens=62 with new=0;"
    " the group orders tail still carries the 2026-11-12 01:5x CEO-PROXY R40"
    " row already recorded as last_order and judged knowledge-only for this"
    " company; benchmarks_refreshed 2026-11-10 sitting two days inside the"
    " seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2655"
    " opened=R2655 carried=2 stale=no open=45 first=1; queue_head named tech"
    " line 664 prefix AC-EDXA1 claimable=15 and queue_floor read FLOOR-MET at"
    " 5/5, 15/10, 10/10.",
    "R2657 THE SHAPES WERE MEASURED BEFORE ANY BYTE with"
    " src/os/limits_export_composed_landed_fifth_wave_R2657.py"
    " (qa/limits-export-composed-landed-fifth-wave-before-R2657.log, 1236"
    " bytes): a_utf16_whole_agree and b_utf16_whole_disagree both read"
    " UTF16-BOM-LANDING with composed=None at disk=26 and disk=30, so"
    " agreement was not decided; c_double_odd_body read BOM-DOUBLE-MARKER with"
    " body=1 at disk=6 and was never named short; d_utf16be_short and"
    " e_utf16_even_two were re-read and already behaved"
    " (UTF16-BOM-SHORT-BODY composed=26 delta=-23 and UTF16-BOM-LANDING), so"
    " they are named rather than claimed; f_clean_lf read PASS.",
    "R2657 SHIPPED by extending src/os/export_composed_landed_face.py IN"
    " PLACE: a whole UTF-16 landing is now COMPARED with the composed text in"
    " the marker own byte order, so an agreeing landing keeps"
    " UTF16-BOM-LANDING and publishes composed=26 delta=0 (AC-EDXA1,"
    " AC-EDXA2) while a landing carrying the text plus extra bytes earns the"
    " new word UTF16-BOM-BODY-GAP with kind=utf16-gap and delta=4 - the"
    " comparison is computed from the marker codec, never from the UTF-8"
    " length, and the fallback keeps the historical word with NO delta for a"
    " body that is merely shorter or longer without carrying the text."
    " The double-marker law now publishes body_short on an ODD body and"
    " renders body_short=1 beside the body count (AC-EDXA3) while the word"
    " stays BOM-DOUBLE-MARKER because AC-EDWZ3 own three byte fixture must"
    " survive (AC-EDXA5). AC-EDXA4 was re-read on both fixtures and kept its"
    " measured answers.",
    "R2657 PROOF measured not quoted: AC-EDXA1..AC-EDXA6 read SUITE PASS 6/6"
    " TWICE with identical criterion lines through the shipped capture"
    " callable (qa/export-composed-landed-bom-precedence-fifth-wave-R2657.log,"
    " 2869 bytes, legs=2 identical=True adjacent=6 fails=0) with SIX adjacent"
    " export suites green beside it (fourth wave 6/6, third wave 6/6, second"
    " wave 6/6, bom-precedence 6/6, composed/landed 6/6, wordspace 6/6). MY"
    " OWN FIRST SUITE RUN WAS RED AND IS NAMED: AC-EDXA5 asserted"
    " bom_gap==BOM-LANDING while the shipped answer has been"
    " BOM-BODY-MISMATCH delta=6 since R2643, so the assertion was corrected to"
    " the shipped word (an EXACT equality read off the shipped first-wave"
    " suite) rather than the code being bent to a wrong expectation.",
    "R2657 ONE PARENT ASSERTION WAS AMENDED AT ITS BIRTH SITE with the reason"
    " written beside it: the first-wave AC-EDWW3 pinned the agreeing UTF-16"
    " landing to delta is None as a NAMED limitation, and AC-EDXA2 deliberately"
    " publishes that delta, so the assertion now demands delta==0 on BOTH byte"
    " orders by EXACT equality - nothing was loosened to a subset and every"
    " other legacy assertion is untouched. REGISTRY 651 suites / 4882"
    " criteria -> 652 / 4888 by exactly one row, recounted by import (652"
    " unique names, 652 unique paths); docs/sandbox-suite-matrix.md read FAIL"
    " stale at the doc evidence face BEFORE any byte and was regenerated"
    " through the shipped render to 66886 bytes at 652 rows / 4888 criteria,"
    " after which --check read byte-identical at rc=0 and its green line"
    " honestly reads 651/652 because the stamping leg predates this suite.",
    "R2657 BOARD AND DEBT: row 664 was closed through src/os/queue_close_R2657"
    " at its predicted and measured 1930587B -> 1934893B with its DISCHARGED"
    " note, and ONE row was seeded from this window own MEASURED limits as"
    " AC-EDXB1..AC-EDXB6 at line 665 (a UTF-16 landing cut by one code unit"
    " still reads a whole landing with composed=None at disk=24, and an even"
    " body that is neither the text nor a head of it is kept as a whole"
    " landing with no judgement at disk=4; the empty-text gap and the even two"
    " byte double-marker body were re-measured AFTER the fix and are named"
    " rather than claimed); queue_head then read the new head at line 665"
    " prefix AC-EDXB1 claimable=15 and queue_floor read FLOOR-MET at 5/5,"
    " 15/10, 10/10. DEBT through the shipped writers: product-face-R2655"
    " closed at its predicted and measured 210720B -> 210723B (line 388, open"
    " 45->44, done 325->326, readback ok) and reconcile-battery-R2657 appended"
    " first=yes at the pre-registered 652 suites / 4888 criteria (210723B ->"
    " 211177B, readback ok), because this window moved one product src file,"
    " one suite and one registry row and the R2168 mixed-tree rule puts the"
    " full battery on the committed tree BEFORE any further product byte.",
    "R2657 RESIDUE READ RATHER THAN ASSUMED: residue_triage --check --round"
    " R2657 reads TRIAGED with residue=1 (the R2165 STAMP-ONLY-OPEN entry) and"
    " the shipped append writer refused with E_RTA_NOT_RESIDUE because this"
    " round is not in the live residue set, so NO declaration was owed or"
    " invented - the refusal is recorded here instead of being worked around.",
    "R2657 honest disclosures: (a) ONE product point on the Executive Protocol"
    " scale - a runnable reader with its own six-criteria suite a maintainer"
    " can rerun - but nothing a CEO could newly open was built and no P-47"
    " business surface moved, so every P-47 item still waits on CEO physical"
    " pieces (merchant id, mini-program appid/secret); (b) the shapes were"
    " MEASURED before any code, so this is a named gap being closed rather"
    " than a new discovery; (c) THE BATTERY IS OWED next window at 652 suites"
    " / 4888 criteria and was NOT run here - the matrix green line keeps the"
    " evidence leg it names rather than a claim from this window; (d) my own"
    " first suite expectation was wrong and is named above rather than"
    " quietly fixed; (e) the UTF-16 comparison only fires when the body IS the"
    " text or carries it as a head, so a cut landing and a foreign payload"
    " still read a bare whole-landing word - seeded as AC-EDXB1/AC-EDXB2"
    " rather than hidden; (f) src/os/scan_five_still.py is still run under"
    " PYTHONIOENCODING=utf-8 because of its [ORD-TOP] GBK crash - WORKED"
    " AROUND, NOT REPAIRED; (g) Docker is absent on this host so no"
    " containerised bring-up of the sandbox faces is claimed; (h) tasks.md was"
    " not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still"
    " reads InteractiveToken and needs an ELEVATED shell for its S4U"
    " re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2657 tokens: local=~26k api=0 api_reason=product window - one five-"
    "silence scan with the content-addressed decisions scan, the group orders"
    " tail and the ledger face read, one debt gate read and one queue head"
    " plus floor read, one limits script written and run BEFORE any code on"
    " eight named worlds and again AFTER it, one in-place extension of the"
    " shipped landing reader with one new word, one agreement flag and one"
    " short-body field, one six-criteria suite written and registered as"
    " exactly one row, one own red assertion corrected against the shipped"
    " answer, one parent assertion amended at its birth site with its reason"
    " inline, one capture through the shipped callable producing two identical"
    " legs with six adjacent suites green, one registry row recounted by"
    " import, one designed FAIL then one regeneration checked byte-identical,"
    " one board row closed and one seeded through their shipped writers, one"
    " residue read that honestly refused, two debt rows moved through their"
    " shipped writers, and the state/export closeout; zero cloud calls and"
    " zero external API touches",
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
    state["last_order"] = "2026-11-12 01:5x"
    state["last_decision_rows"] = 117
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
