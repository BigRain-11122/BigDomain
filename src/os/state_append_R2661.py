"""state_append_R2661 - the R2661 product window narrative and tokens.

Every number below was measured off this tree in this window: the pre-fix and
post-fix limit worlds, the suite and its two captured legs, the registry
recount by import, the matrix byte counts on both sides, the board and debt
byte counts across their shipped writers, and the fold prediction.
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
    "2026-11-12 R2661 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2659, state/queue/tech.md:665 prefix AC-EDXB1, criteria"
    " AC-EDXB1..AC-EDXB6 pinned in that row at R2657 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD 492f0435 equal to origin/main"
    " with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed decisions scan read rows=117 tokens=62 with new=0;"
    " the group orders tail still carries the 2026-11-12 01:5x CEO-PROXY R40"
    " row already recorded as last_order and judged knowledge-only for this"
    " company; benchmarks_refreshed 2026-11-10 sitting two days inside the"
    " seven-day gate. debt_gate read CLAIM-FIRST item=product-face-R2659"
    " opened=R2659 open=45 first=1; queue_head named tech line 665 prefix"
    " AC-EDXB1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10,"
    " 10/10.",
    "R2661 SHIPPED by extending src/os/export_composed_landed_face.py IN"
    " PLACE with ONE new word and ONE named refusal. A UTF-16 body that is a"
    " strict PREFIX of the composed text in the marker own codec is now"
    " UTF16-BOM-CUT with kind=utf16-cut, the code units it lost published as"
    " cut_units, and the whole landing it would have been published as"
    " composed so delta is a number rather than None (AC-EDXB1, AC-EDXB2)."
    " The even-length law could never see this shape because one lost UTF-16"
    " character is two bytes, so the body stays EVEN: MEASURED before any"
    " byte, a landing cut by one code unit read UTF16-BOM-LANDING with"
    " composed=None at disk=24, the SAME word a whole landing earns. A body"
    " that is neither the text nor a head of it keeps UTF16-BOM-LANDING with"
    " no delta and now NAMES the refusal as refusal=NOT-TEXT-NOR-HEAD with"
    " judged=False, so a declined judgement is spoken instead of implied by"
    " an absent count (AC-EDXB3).",
    "R2661 PROOF measured not quoted: AC-EDXB1..AC-EDXB6 read SUITE PASS 6/6"
    " on the FIRST run and 6/6 TWICE with identical criterion lines through"
    " the shipped capture callable (qa/export-composed-landed-bom-precedence-"
    "sixth-wave-R2661.log, 3136 bytes, legs=2 identical=True adjacent=6"
    " fails=0) with SIX adjacent export suites green beside it (fifth wave,"
    " fourth wave, third wave, second wave, bom-precedence, composed/landed)."
    " Post-fix worlds read UTF16-BOM-CUT composed=26 disk=24 delta=-2"
    " cut_units=1 for the LE cut and cut_units=2 for the BE cut, the other"
    " body keeps its word with refusal=NOT-TEXT-NOR-HEAD, and the two worlds"
    " measured at R2657 survive unchanged (the empty-text gap at"
    " composed=2 delta=24 and the even two byte body behind two markers)."
    " AC-EDXB5 re-reads every AC-EDXA, AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW"
    " and AC-EDWV answer on its own fixture, including the legitimate"
    " 0xef-leading MIXED payload that stays TRANSPORT-MIXED with bom=0 and"
    " the clean LF PASS.",
    "R2661 REGISTRY AND DOCUMENT: registry 652 suites / 4888 criteria -> 653"
    " / 4894 by exactly one row, recounted by import (653 unique names, 653"
    " unique paths); docs/sandbox-suite-matrix.md read FAIL stale at the"
    " evidence face BEFORE any byte and was regenerated through the shipped"
    " render to 67021 bytes at 653 rows / 4894 criteria, after which --check"
    " read byte-identical at rc=0 and its green line honestly reads 652/653"
    " because the stamping leg (qa/reconcile-all-R2659.log) predates this"
    " suite.",
    "R2661 BOARD AND DEBT: row 665 was closed through src/os/queue_close_"
    "R2661.py at its predicted and measured 1934893B -> 1939382B with its"
    " DISCHARGED note, and ONE row was seeded from this window own MEASURED"
    " limits as AC-EDXC1..AC-EDXC6 at line 666 (a UTF-16 landing whose body"
    " has the SAME LENGTH as the composed text but a DIFFERENT content reads"
    " a clean UTF16-BOM-LANDING at composed=10 disk=10 delta=0, so the"
    " equal-length branch compares LENGTHS ONLY; a cut leaving a LONE"
    " SURROGATE HALF reads cut_units=1 at body=8, so the count is code units"
    " and never characters; a cut behind the UTF-8 BOM and a UTF-16 marker at"
    " once reads BOM-DOUBLE-MARKER at disk=13 because the double-marker law"
    " runs first; and a UTF-16BE cut by three code units was re-measured"
    " AFTER the fix and reads cut_units=3 composed=16 disk=10 delta=-6, named"
    " rather than claimed); queue_head then read the new head at line 666"
    " prefix AC-EDXC1 claimable=15 and queue_floor read FLOOR-MET at 5/5,"
    " 15/10, 10/10. DEBT through the shipped writers: product-face-R2659"
    " closed at its predicted and measured 211483B -> 211486B (line 390, open"
    " 45->44, done 327->328, readback ok) and reconcile-battery-R2661"
    " appended first=yes at the pre-registered 653 suites / 4894 criteria"
    " (211486B -> 211760B, readback ok), because this window moved one"
    " product src file, one suite and one registry row and the R2168"
    " mixed-tree rule puts the full battery on the committed tree BEFORE any"
    " further product byte.",
    "R2661 ONE LABEL ERROR WAS MADE AND CORRECTED, disclosed rather than"
    " smoothed: this window first named its own artifacts R2659 although the"
    " preceding verification window had already taken that number, so the"
    " evidence log, both limit logs, the two one-off scripts, the board seed"
    " and discharged rows and the debt row were all renamed to R2661 - file"
    " moves by Move-Item, in-place text edits on the two script files, and"
    " targeted single-line edits on state/queue/tech.md rows 665/666/667 and"
    " on the ONE debt row this window opened, with the closed"
    " product-face-R2659 row left at R2659 because that is the round which"
    " opened it. Nothing else was touched and no product byte moved for the"
    " rename.",
    "R2661 honest disclosures: (a) ONE product point on the Executive"
    " Protocol scale - a runnable reader with its own six-criteria suite that"
    " a maintainer can rerun - but nothing a CEO could newly open was built"
    " and no P-47 business surface moved, so every P-47 item still waits on"
    " CEO physical pieces (merchant id, mini-program appid/secret); (b) the"
    " pre-fix worlds are READ from the parent window own evidence"
    " (qa/limits-export-composed-landed-next-R2657.log, 748B, landed at"
    " R2657) rather than re-measured here, because this window wrote the fix"
    " before its first measurement, and that substitution is named; (c) the"
    " successor limit seeded is a REAL hole left open on purpose - the"
    " equal-length branch of the whole-landing compare reads LENGTHS ONLY for"
    " UTF-16, so a wrong payload of the right size still reads clean; (d)"
    " THE BATTERY IS OWED next window at 653 suites / 4894 criteria and was"
    " NOT run here; (e) src/os/scan_five_still.py is still run under"
    " PYTHONIOENCODING=utf-8 because of its [ORD-TOP] GBK crash - WORKED"
    " AROUND, NOT REPAIRED; (f) Docker is absent on this host so no"
    " containerised bring-up of the sandbox faces is claimed; (g) the real"
    " 19.9 debit and the real msgSecCheck still wait on CEO physical items;"
    " (h) tasks.md was not touched, it is the P-47 canonical board; (i)"
    " BigDomain-OSLoop still needs an ELEVATED shell for its S4U"
    " re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",
    "R2661 tokens: local=~22k api=0 api_reason=product window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, one debt gate read and one queue"
    " head plus floor read, one pre-fix re-measurement of the seed worlds,"
    " one in-place extension of the shipped landing reader with one new word"
    " and one named refusal, one six-criteria suite written and registered as"
    " exactly one row, one capture through the shipped callable producing two"
    " identical legs with six adjacent suites green, one registry recount by"
    " import, one designed matrix FAIL then one regeneration checked"
    " byte-identical, one successor limit script measuring four worlds after"
    " the fix, one board row closed and one seeded through their shipped"
    " writers, two debt rows moved through their shipped writers, one round"
    " label corrected across six artifacts after it was found wrong, and the"
    " state/export closeout; zero cloud calls and zero external API touches",
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
