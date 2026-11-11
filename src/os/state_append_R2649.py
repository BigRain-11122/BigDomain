"""state_append_R2649 - the R2649 product window narrative and tokens.

Every number below was measured off the tree in this window: the evidence file
re-measured on bytes, the registry recounted by import, the matrix byte counts
on both sides of the regeneration, and the debt register byte counts.
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
NEW_DEC = ("D-20261112-01", "D-20261112-02", "D-20261112-03",
           "D-20261112-04", "D-20261112-05", "D-20261112-06")

LINES = [
    "2026-11-12 R2649 PRODUCT window on the queue head the debt gate named"
    " (product-face-R2647, state/queue/tech.md:662 prefix AC-EDWY1, criteria"
    " AC-EDWY1..AC-EDWY6 pinned in that row at R2646 BEFORE any code). Five"
    " readings at open: git status EMPTY at HEAD fbb28bc1 with no index.lock;"
    " ZERO unreplied @BigDomain rows in cph4/evolution-ledger.md"
    " (atbd_lines=0 unreplied_groups=0); the content-addressed D-/C-/P-/O-/T-/"
    " XL- scan read 339 rows and tokens=195 with new=6"
    " (D-20261112-01..06, already judged knowledge-only at R2647); the group"
    " orders tail carries a NEW 2026-11-12 01:5x CEO-PROXY R40 row (three"
    " fleet flags rooted in bm-b being physically offline plus the"
    " station_drive supply break, no @BigDomain dispatch, judged"
    " knowledge-only for this company); benchmarks_refreshed 2026-11-10"
    " sitting two days inside the seven-day gate. debt_gate read CLAIM-FIRST"
    " item=product-face-R2647 opened=R2647 carried=2 stale=no first=1 open=44;"
    " queue_head named tech line 662 prefix AC-EDWY1 claimable=15 and"
    " queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2649 THE SIX SHAPES WERE MEASURED BEFORE ANY BYTE WAS WRITTEN with"
    " src/os/limits_export_composed_landed_third_wave_R2649.py against private"
    " files (qa/limits-export-composed-landed-third-wave-before-R2649.log,"
    " 881B): a truncated prefix over a MIXED body that is NOT the composed"
    " text read TRANSPORT-MIXED with bom=0, a BOM-only landing against"
    " non-empty text read BOM-EMPTY-PAYLOAD with composed=None, a prefix with"
    " an empty body read BOM-TRUNCATED at delta=2, a UTF-8 BOM followed by a"
    " UTF-16 marker read BOM-BODY-MISMATCH at delta=-10, a legitimate"
    " 0xef-leading MIXED payload read TRANSPORT-MIXED and a UTF-16 marker with"
    " one zero byte read UTF16-BOM-LANDING - byte for byte the seed row"
    " numbers.",
    "R2649 SHIPPED three new landing words into"
    " src/os/export_composed_landed_face.py in the SAME single-word pinned"
    " order, plus one field law: BOM-DOUBLE-MARKER (two markers on one"
    " landing, judged before the BOM-only law), BOM-CUT-NO-BODY (a strict"
    " prefix with nothing behind it, judged before any truncation law), and"
    " BOM-TRUNCATED-MIXED-GAP (a cut whose body HEAD is the composed text but"
    " which carries extra bytes, judged beside the matching-cut word); the"
    " BOM-only law now CARRIES the composed count and its delta when the text"
    " is not empty, so an empty payload is a comparison and not an unqualified"
    " word. The gap word is PREFIX-GUARDED (the composed text must be the HEAD"
    " of the cut body), which is why the legitimate 0xef-leading MIXED payload"
    " stays TRANSPORT-MIXED with bom=0 and is not accused of being a cut"
    " marker. Added src/os/test_export_composed_landed_bom_precedence_third_"
    "wave.py as the AC-EDWY1..AC-EDWY6 suite, wired once into the runner at"
    " six criteria.",
    "R2649 PROOF measured not quoted: AC-EDWY1..AC-EDWY6 read SUITE PASS 6/6"
    " on the first run and 6/6 TWICE with identical criterion lines through"
    " the shipped capture callable src/os/capture_R2649.py"
    " (qa/export-composed-landed-bom-precedence-third-wave-R2649.log, 4159B,"
    " utf-8, bom=False, crlf=0, nul=0, SIX suite-pass lines, digest"
    " 259FB0CF0D5C32DD, adjacent=4 fails=0) with FOUR adjacent export suites"
    " green beside it (second wave 6/6, bom-precedence 6/6, wordspace 6/6,"
    " composed/landed 6/6). ONE OWN DEFECT WAS CAUGHT AND REPAIRED AT ITS"
    " BIRTH SITE BEFORE the capture: the suite read a KeyError on a report"
    " dict that legitimately has no bom_kind key, so the read became"\
    " .get() rather than the assertion being dropped, and all evidence was"
    " taken after the repair.",
    "R2649 REGISTRY, DOCUMENT, BOARD AND DEBT: the registry stands at 650"
    " suites / 4876 criteria recounted by import (649 -> 650 suites, 4870 ->"
    " 4876 criteria, one row, 650 unique names, 650 unique paths);"
    " docs/sandbox-suite-matrix.md read ROWS-MISMATCH at 649 against 650 rows"
    " BEFORE any byte was written and was then regenerated through the shipped"
    " write face to 66616B at 650 rows / 4876 criteria, after which --check"
    " read DOC-CURRENT at rc=0. Row 662 was closed through"
    " src/os/queue_close_R2649.py at its predicted and measured 1923085B ->"
    " 1926624B with its DISCHARGED note, and ONE row was seeded from this"
    " window own MEASURED limits as AC-EDWZ1..AC-EDWZ6 at line 663 (a UTF-16"
    " marker with one zero byte reads UTF16-BOM-LANDING at disk=3 with"
    " composed=None on both an empty and a non-empty text, and two markers"
    " WITH a body read BOM-DOUBLE-MARKER at disk=8 with composed=None, while a"
    " prefix-only landing against non-empty text already reads"
    " BOM-CUT-NO-BODY with composed=12 delta=-10 and is named rather than"
    " claimed); queue_head then read the new head at line 663 prefix AC-EDWZ1."
    " DEBT through the shipped writers: product-face-R2647 noted DISCHARGED"
    " R2649 at its predicted and measured 208229B -> 208701B and closed at"
    " 208704B (line 383, open 44->43, done 321->322, readback ok),"
    " reconcile-battery-R2649 appended first=yes at the pre-registered 650"
    " suites / 4876 criteria (208704B -> 208996B, readback ok) and"
    " product-face-R2649 appended first=no (208996B -> 209269B, readback ok),"
    " so the gate now names that battery first.",
    "R2649 honest disclosures: (a) TWO product points on the Executive"
    " Protocol scale - a runnable face with its own six-criteria suite and a"
    " bounded live reading a maintainer can rerun - but NOTHING a CEO could"
    " newly open was built and no P-47 business surface moved, so every P-47"
    " item still waits on CEO physical pieces (merchant id, mini-program"
    " appid/secret); (b) the fourth-wave gap this row leaves open is"
    " MEASURED, not guessed - the UTF-16 one-byte remnant and the body behind"
    " two markers are the two shapes no field describes, and both are seeded"
    " with their numbers; (c) my own suite defect was a KeyError on a report"
    " dict without a bom_kind key, repaired at its birth site before any"
    " evidence was captured; (d) THE BATTERY IS OWED next window and was NOT"
    " run here because this window moved product src bytes and one registry"
    " row; (e) src/os/scan_five_still.py still crashes at its final [ORD-TOP]"
    " print on the GBK console, so the scan was run under PYTHONIOENCODING="
    " utf-8 - WORKED AROUND, NOT REPAIRED; (f) Docker is absent on this host"
    " so no containerised bring-up of the sandbox faces is claimed; (g)"
    " tasks.md was not touched, it is the P-47 canonical board; (h)"
    " BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED"
    " shell for its S4U re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",
    "R2649 tokens: local=~23k api=0 api_reason=product window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, one new group order row and six"
    " decision tokens judged knowledge-only, one debt gate read and one queue"
    " head plus row read, one limits script measuring seven worlds BEFORE any"
    " code, one module extension with three words and one field law, one"
    " six-criteria suite written and registered as exactly one row, one own"
    " suite defect repaired at its birth site, one capture through the shipped"
    " callable producing two identical legs with four adjacent suites, one"
    " designed matrix ROWS-MISMATCH then one regeneration checked DOC-CURRENT,"
    " one successor limits script measuring six worlds after the fix, one"
    " board row closed and one seeded through their shipped writers, three"
    " debt movements through their shipped writers, and the state/export"
    " closeout; zero cloud calls and zero external API touches",
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
    state["last_decision_rows"] = 339
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
          and reread["tick"] == state["tick"]
          and all(t in reread["last_dec_tokens"] for t in NEW_DEC))
    print("APPEND tick=%d lines=%d tokens=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), len(reread["last_dec_tokens"]), before,
             len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
