"""state_append_R2653 - the R2653 product window narrative and tokens.

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
NEW_DEC = (
    "D-20261112-07",
    "D-20261112-08",
    "D-20261112-09",
    "D-20261112-10",
    "D-20261112-11",
    "D-20261112-12",
)

LINES = [
    "2026-11-12 R2653 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2651, state/queue/tech.md:663 prefix AC-EDWZ1, criteria"
    " AC-EDWZ1..AC-EDWZ6 pinned in that row at R2649 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD c2eb3156 equal to origin/main"
    " with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed decisions scan read rows=117 tokens=62 with new=6"
    " (D-20261112-07..12); the group orders tail still carries the 2026-11-12"
    " 01:5x CEO-PROXY R40 row already recorded as last_order and judged"
    " knowledge-only for this company; benchmarks_refreshed 2026-11-10 sitting"
    " two days inside the seven-day gate. debt_gate read CLAIM-FIRST"
    " item=product-face-R2651 opened=R2651 carried=2 stale=no open=45 first=1;"
    " queue_head named tech line 663 prefix AC-EDWZ1 claimable=15 and"
    " queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2653 THE SIX NEW DECISIONS WERE JUDGED KNOWLEDGE-ONLY and named:"
    " D-07 is the batch-58 collection review over eight faces, D-08 is the"
    " promise-carrier law born from three unlanded promises, D-09 is the"
    " ledger-split hard execution with its byte-conservation law, D-10 is the"
    " third overdue cloud-gate wiring with its 12:00 execution window, D-11"
    " re-bases the disk-burn criterion onto a landed baseline file, and D-12"
    " files MiniGame's negative disable evidence. None carries a BigDomain"
    " execution face and none was executed here; the baseline advanced by"
    " exactly those six tokens.",
    "R2653 THE FOUR SHAPES WERE MEASURED BEFORE ANY BYTE:"
    " src/os/limits_export_composed_landed_next_R2649.py re-run in this window"
    " (qa/limits-export-composed-landed-fourth-wave-before-R2653.log, 787"
    " bytes) read a_utf16_one_byte and b_utf16_one_byte_text as"
    " UTF16-BOM-LANDING with composed=None at disk=3, c_double_marker_body as"
    " BOM-DOUBLE-MARKER with composed=None delta=None at disk=8, and"
    " d_cut_only_vs_text / e_cut1_vs_text as BOM-CUT-NO-BODY with composed=12"
    " at delta -10 and -11 - byte for byte the numbers the seed row pinned at"
    " R2649, so the last two are named as already correct rather than claimed.",
    "R2653 SHIPPED by extending src/os/export_composed_landed_face.py IN PLACE:"
    " a UTF-16 body is an EVEN number of bytes, so an ODD remnant now earns"
    " UTF16-BOM-SHORT-BODY with kind=utf16-short and its own body size instead"
    " of being called a whole landing (AC-EDWZ1), that remnant carries the"
    " count it was measured against - the whole landing it would have been,"
    " marker included, in the marker own byte order - so delta is published"
    " rather than None (AC-EDWZ2), and the double-marker law now describes"
    " what sits BEHIND both markers through body and body_transport while the"
    " word itself stays BOM-DOUBLE-MARKER and the single-word order is"
    " unchanged (AC-EDWZ3). AC-EDWZ4 was re-read on both cut fixtures and kept"
    " composed=12 with deltas -10 and -11.",
    "R2653 PROOF measured not quoted: AC-EDWZ1..AC-EDWZ6 read SUITE PASS 6/6 on"
    " the FIRST run and 6/6 TWICE with identical criterion lines through the"
    " shipped capture callable (qa/export-composed-landed-bom-precedence-"
    "fourth-wave-R2653.log, 3772 bytes, legs=2 identical=True adjacent=5"
    " fails=0) with FIVE adjacent export suites green by rc beside it (third"
    " wave 6/6, second wave 6/6, bom-precedence 6/6, wordspace 6/6,"
    " composed/landed 6/6).",
    "R2653 ONE PARENT ASSERTION WAS AMENDED AT ITS BIRTH SITE with the reason"
    " written beside it: the third-wave suite pinned the one byte remnant to"
    " UTF16-BOM-LANDING as a NAMED limitation, and AC-EDWZ1 deliberately"
    " replaces that word, so its assertion now demands the new word by EXACT"
    " equality - nothing was loosened to a subset and every other legacy"
    " assertion is untouched. REGISTRY 650 suites / 4876 criteria -> 651 /"
    " 4882 by exactly one row, recounted by import (651 unique names, 651"
    " unique paths); docs/sandbox-suite-matrix.md read ROWS-MISMATCH 650"
    " against 651 BEFORE any byte and was regenerated through the shipped"
    " write face to 66751 bytes at 651 rows / 4882 criteria, after which"
    " --check read DOC-CURRENT at rc=0.",
    "R2653 BOARD AND DEBT: row 663 was closed through src/os/queue_close_R2653"
    " at its predicted and measured 1926624B -> 1930587B with its DISCHARGED"
    " note, and ONE row was seeded from this window own MEASURED limits as"
    " AC-EDXA1..AC-EDXA6 at line 664 (a whole UTF-16 landing that agrees and"
    " one that disagrees read the SAME word with composed=None at disk=26 and"
    " 30; an odd body behind two markers reads body=1 at disk=6; a UTF-16BE"
    " short remnant and an even two byte body were re-measured AFTER the fix"
    " and are named rather than claimed); queue_head then read the new head at"
    " line 664 prefix AC-EDXA1 claimable=15 and queue_floor read FLOOR-MET at"
    " 5/5, 15/10, 10/10. DEBT through the shipped writers:"
    " product-face-R2651 closed at its predicted and measured 209830B ->"
    " 209833B (line 386, open 45->44, done 323->324, readback ok) and"
    " reconcile-battery-R2653 appended first=yes at the pre-registered 651"
    " suites / 4882 criteria (209833B -> 210136B, readback ok), because this"
    " window moved one product src file and one registry row and the R2168"
    " mixed-tree rule puts the full battery on the committed tree BEFORE any"
    " further product byte.",
    "R2653 RESIDUE AND ONE TRANSPORT REPAIR: the R2653 round had to be"
    " declared before the owed battery, and both shipped residue writers"
    " refused with their shape code because the declaration file had lost its"
    " trailing newline (934 bytes ending in a bare }, against the pinned"
    " closer). ONE byte was appended to restore the pinned layout - no value"
    " was touched, the file only regained its terminator - and the shipped"
    " append writer then landed R2653=DELIVERED at 935B -> 1207B with"
    " readback, after which residue_triage --check --round R2653 reads"
    " TRIAGED untriaged=0 unmatched=0 expired=0.",
    "R2653 honest disclosures: (a) ONE product point on the Executive Protocol"
    " scale - a runnable reader with its own six-criteria suite that a"
    " maintainer can rerun - but nothing a CEO could newly open was built and"
    " no P-47 business surface moved, so every P-47 item still waits on CEO"
    " physical pieces (merchant id, mini-program appid/secret); (b) the four"
    " shapes were MEASURED before any code, so this is a named gap being"
    " closed rather than a new discovery; (c) THE BATTERY IS OWED next window"
    " at 651 suites / 4882 criteria and was NOT run here - the matrix green"
    " line keeps the evidence leg it names rather than a claim from this"
    " window; (d) src/os/scan_five_still.py still crashes at its final"
    " [ORD-TOP] print on the GBK console, so the scan was run under"
    " PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT REPAIRED; (e) Docker is"
    " absent on this host so no containerised bring-up of the sandbox faces is"
    " claimed; (f) tasks.md was not touched, it is the P-47 canonical board;"
    " (g) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell for its S4U re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",
    "R2653 tokens: local=~24k api=0 api_reason=product window - one five-"
    "silence scan with the content-addressed decisions scan, the group orders"
    " tail and the ledger face read, six new decision tokens judged, one debt"
    " gate read and one queue head plus floor read, one limits script"
    " re-measured BEFORE any code on four named shapes, one in-place extension"
    " of the shipped landing reader with one new word and two body fields, one"
    " six-criteria suite written and registered as exactly one row, one parent"
    " assertion amended at its birth site with its reason inline, one capture"
    " through the shipped callable producing two identical legs with five"
    " adjacent suites green, one registry row recounted by import, one designed"
    " ROWS-MISMATCH then one regeneration checked DOC-CURRENT, one board row"
    " closed and one seeded through their shipped writers, two debt rows moved"
    " through their shipped writers, one residue declaration landed after a"
    " one-byte transport repair, and the state/export closeout; zero cloud"
    " calls and zero external API touches",
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
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_DEC:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = 117
    state["last_order"] = "2026-11-12 01:5x"
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
    print("APPEND tick=%d lines=%d tokens=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), len(reread["last_dec_tokens"]), before,
             len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
