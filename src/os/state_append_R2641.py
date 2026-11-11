"""state_append_R2641 - the R2641 verification window narrative and tokens.

Every number below was measured off the tree in this window: the adopted leg
on bytes, the criteria recount, the registry import, the three export suites,
the matrix byte counts and the debt register byte counts.
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
    "2026-11-11 R2641 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2638, pre-registered 647 suites / 4858"
    " criteria at R2638). Five readings at open: git status EMPTY at HEAD"
    " 469c5785 with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed D-/C-/P-/O-/T-/XL- decisions scan read tokens=189"
    " new=0 over 323 rows; the group orders tail still at the 2026-11-11"
    " 12:05 event-shift T1 row already judged knowledge-only for this"
    " company; benchmarks_refreshed 2026-11-10 one day inside the seven-day"
    " gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2638"
    " opened=R2638 carried=3 stale=yes first=1 open=43, and the leg R2639"
    " launched was LIVE at open (pid 48708 with its reconcile_all child,"
    " stream 493038B) so it was ADOPTED AND NOT RELAUNCHED (the"
    " R2601/R2607/R2614/R2635 precedent).",

    "R2641 THE ADOPTED LEG CLOSED GREEN AND WAS MEASURED NOT QUOTED: the"
    " stream closed at 20:42 on 'RUNNER PASS (647/647 suites green,"
    " reconcile controls 7/7, 4078.7s)' followed by 'BATTERY rc=0 4079.0s'"
    " after TMP RECLAIM candidates=697 removed=697 busy=0 failed=0"
    " reclaimed=241.16 MiB. The evidence file qa/reconcile-all-R2638-retry.log"
    " was then measured on BYTES BEFORE any follow-up byte was appended:"
    " 1095241B, utf-8 True, bom=False, crlf=0, lone_cr=0, nul=0, 8608 lines,"
    " 647 suite rows carrying 647 UNIQUE names, 647 PASS rows and ZERO FAIL"
    " rows, ZERO non-zero exits, and an INDEPENDENT criteria recount over the"
    " per-row fields summing to EXACTLY 4858 against the pre-registered"
    " 647/4858. The registry was re-measured by importing reconcile_all.SUITES"
    " at 647 suites / 4858 criteria / 647 unique names / 647 unique paths,"
    " byte for byte the pre-registered target.",

    "R2641 R2614 DISCIPLINE HONOURED because one closeout commit (469c5785)"
    " landed UNDER the leg: the three export write-sensitive suites were"
    " re-run on the FINAL committed tree and read SUITE PASS 6/6"
    " (os-status-export-writer-dialect-wire), SUITE PASS 6/6"
    " (os-queue-floor-export-face) and SUMMARY pass=15 fail=0 at rc=0"
    " (os-export-consistency-queue-face, which prints a SUMMARY rather than a"
    " suite line), and ledger_lines --check read VERDICT CLEAN with"
    " new_missing none and new_orphan none.",

    "R2641 FOLLOW-UP IN THE DESIGNED ORDER: the dry run read matrix FAIL"
    " first by design (on-disk 66167B against regenerated 66204B, NO byte"
    " written) while fingerprint read CLEAN domains=5, profile read"
    " byte-identical PASS and census read DRIFT-CLEAN; docs/sandbox-suite-"
    "matrix.md was then regenerated stamp-aligned from THIS round own green"
    " leg through the shipped suite_matrix face to 66204B at 647 suites /"
    " 4858 criteria with its green line honestly reading 647/647"
    " self-describing, --check then read byte-identical at rc=0, and the four"
    " sections re-ran to VERDICT R2641 PASS failing=none (APPENDED 1951B"
    " eol_ok=True, evidence 1097192B after).",

    "R2641 BOARD AND DEBT: reconcile-battery-R2638 was closed through the"
    " shipped debtor at its predicted and measured 205603B -> 205606B"
    " (line 377, open 43->42, done 316->317, readback ok), and"
    " product-face-R2641 was appended first=yes at the predicted 205606B ->"
    " 206399B (readback ok) naming the next window a PRODUCT face on the"
    " queue head state/queue/tech.md:660 prefix AC-EDWW1 (BOM precedence:"
    " body gap under a BOM, BOM plus MIXED, UTF-16 BOM, truncated BOM); the"
    " debt gate then read CLAIM-FIRST item=product-face-R2641 first=1 open=43."
    " NO successor battery is owed because this window moved no product src"
    " byte and the registry is unmoved at 647 suites / 4858 criteria,"
    " re-measured by import. tasks.md was not touched, it is the P-47"
    " canonical board.",

    "R2641 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written because the debt gate put"
    " the owed battery before any further product work, and this window"
    " deliverables are a CLOSED debt row and a matrix document regenerated"
    " from a fully green 647/647 leg that a maintainer can open; (b) the leg"
    " was AUTHORED BY R2639 and is ADOPTED here rather than presented as this"
    " window own work; (c) this window ran far past its twenty-five minute"
    " budget because the leg measured 4078.7s (68 minutes) against it, and"
    " that overrun is named rather than hidden; (d) two TIMING shapes were"
    " observed inside the leg and are named WITHOUT repair - the nested"
    " apimarket report suite (test_apimarket_report_refundregister with five"
    " children) again ran close to the 600s per-suite cap and the probe-seam"
    " walrus suites took 145-228s each, so no cap byte was changed and no"
    " failure is claimed; (e) Docker is absent on this host so no"
    " containerised bring-up is claimed; (f) src/os/scan_five_still.py still"
    " renders mojibake at its final [ORD-TOP] print on the GBK console (a BOM"
    " in the group orders row), unchanged and still carried, because the"
    " three judgments above it print first; (g) the real 19.9 debit and the"
    " real msgSecCheck still wait on CEO physical items (merchant id,"
    " mini-program appid/secret); (h) BigDomain-OSLoop still reads"
    " InteractiveToken and needs an ELEVATED shell for its S4U"
    " re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",

    "R2641 tokens: local=~9k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, one debt gate read"
    " naming the battery, one live leg polled in bounded waits until its"
    " closing line at 4078.7s, one byte-level re-measurement of the evidence"
    " on seven axes with an independent criteria recount, one registry"
    " recount by import on four axes, three export write-sensitive suites"
    " plus the ledger check re-run on the FINAL committed tree, one designed"
    " matrix FAIL with no byte written, one stamp-aligned regeneration checked"
    " byte-identical, one four-section write leg to a PASS verdict, one debt"
    " row closed and one opened through their shipped writers, and the"
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
