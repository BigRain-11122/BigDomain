"""state_append_R2647 - the R2647 verification window narrative and tokens.

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

LINES = [
    "2026-11-12 R2647 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2646, pre-registered 649 suites / 4870"
    " criteria at R2646 because that window moved product src bytes and one"
    " registry row). Five readings at open: git status carried TWO untracked"
    " files, the retry leg and the one-off launcher of an INTERRUPTED ATTEMPT"
    " of this same round, with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed D-/C-/P-/O-/T-/XL- scan read 339 rows and tokens=195"
    " with new=6 (D-20261112-01..06); the group orders tail still carries the"
    " 2026-11-11 20:15 BigStream mv0001 v727 row already judged knowledge-only"
    " for this company; benchmarks_refreshed 2026-11-10 sitting two days inside"
    " the seven-day gate. debt_gate read CLAIM-FIRST"
    " item=reconcile-battery-R2646 opened=R2646 carried=1 stale=no first=1"
    " open=44; queue_head named tech line 662 prefix AC-EDWY1 claimable=15 and"
    " queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "R2647 THE SIX NEW DECISIONS WERE JUDGED KNOWLEDGE-ONLY and named:"
    " D-20261112-01 the batch-57 collection review (its BigDomain row is the"
    " EXPIRED orders conflict-marker report, no-op written off), D-02 the T0"
    " cloud gate that became dead code in the bm-b scripts, D-03 the MiniGame"
    " dual task still Disabled outside the expected-disabled list, D-04 the"
    " group ledger double oversize whose execution face is the cph4 rotation"
    " tool, D-05 the BigCompute status-face freshness caps, and D-06 the"
    " council batch-57 retrospective. None of the six names a BigDomain"
    " execution face; the baseline advanced by exactly those six tokens.",
    "R2647 THE LEG THE INTERRUPTED ATTEMPT LAUNCHED HAD ALREADY FINISHED AND"
    " WAS ADOPTED, NOT RESTARTED: no reconcile writer was live by command line"
    " match, qa/reconcile-all-R2647-retry.log sat on disk at 1097573B before"
    " this window touched it, its stream closed on RUNNER PASS (649/649 suites"
    " green, reconcile controls 7/7, 3557.4s), and its FIRST leg"
    " qa/reconcile-all-R2647.log 1097735B was RED at 646/649 and is KEPT in git"
    " as evidence - three red export suites"
    " (os-status-export-writer-dialect-wire, os-queue-floor-export-face,"
    " os-export-consistency-queue-face) carrying four failed assertions.",
    "R2647 THE RED CAUSE WAS CLOSED AT ITS BIRTH SITE BY THE SAME INTERRUPTED"
    " ATTEMPT AND ITS FIX IS ADOPTED AND DELIVERED HERE: commit fd21c734"
    " re-derives the export tick row AFTER the state tick advance (2643 ->"
    " 2644) and regenerates docs/status-export.json, and that commit was"
    " UNPUSHED at open (HEAD fd21c734 against origin/main 12b73533) - this"
    " window pushes it, so the local-only state is named rather than hidden."
    " The target was re-measured BY IMPORT before anything was judged:"
    " reconcile_all.SUITES read 649 suites / 4870 criteria / 649 unique names /"
    " 649 unique paths, byte for byte the pre-registered number.",
    "R2647 THE EVIDENCE WAS MEASURED ON BYTES AND NOT QUOTED:"
    " qa/reconcile-all-R2647-retry.log is 1099524B after the follow-up block"
    " (1097573B at adoption), utf-8 with bom=False, crlf=0, lone_cr=0, nul=0,"
    " 8624 lines, ZERO FAIL suite rows, 649 real suite rows carrying 649 UNIQUE"
    " names, and an INDEPENDENT criteria recount over the per-row criteria"
    " fields summing to EXACTLY 4870 against the pre-registered 649/4870. The"
    " leg ran 01:53:51-02:53:08 while the newest commit predates it (fd21c734"
    " at 00:02:14), so NO commit landed under it and the R2614 re-run"
    " discipline is satisfied by measurement rather than by assertion.",
    "R2647 FOLLOW-UP RAN IN THE DESIGNED ORDER: the dry run read VERDICT FAIL"
    " failing=matrix at on-disk=66441B against regenerated=66467B with NO byte"
    " written while fingerprint read CLEAN domains=5, profile read"
    " byte-identical and census read DRIFT-CLEAN; docs/sandbox-suite-matrix.md"
    " was then regenerated stamp-aligned from THIS round own green leg to 66467"
    " bytes at 649 suites / 4870 criteria with its green line honestly reading"
    " 649/649 self-describing, and --check read byte-identical at rc=0; the"
    " write leg then read all four sections PASS for VERDICT R2647 PASS"
    " failing=none (APPENDED 1951B eol_ok=True).",
    "R2647 DEBT AND BOARD through the shipped writers:"
    " reconcile-battery-R2646 closed at its predicted and measured 207809B ->"
    " 207812B (line 381, open 44->43, done 320->321, readback ok) and"
    " product-face-R2647 opened first=yes at the predicted 207812B -> 208229B"
    " (readback ok) naming the next window a PRODUCT face on the queue head"
    " state/queue/tech.md:662 prefix AC-EDWY1"
    " (export_composed_landed_face BOM precedence third wave, criteria"
    " AC-EDWY1..AC-EDWY6 pinned there at R2646 BEFORE any code); NO successor"
    " battery is owed because this window moved no product src byte and the"
    " registry is unmoved at 649 suites / 4870 criteria, re-measured by import."
    " The one-off launcher src/os/launch_battery_R2647.py was DELETED before"
    " the commit instead of being staged. STATE: fold 697 at a true block"
    " boundary (items 76..92, the complete R2643 block ending on its push line"
    " plus the complete R2645 block ending on its tokens line) after a dry run"
    " that agreed exactly, 79470B -> 65518B with 14 tokens carried, archive"
    " VERIFIED and FOLD-CLEAR margin 12982.",
    "R2647 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - no product byte was written, because the debt gate puts"
    " the owed battery before any further product work and this window spent"
    " its budget adopting and closing that leg; (b) the leg AND its birth-site"
    " repair commit were AUTHORED BY AN INTERRUPTED ATTEMPT OF THIS SAME ROUND"
    " and are adopted rather than presented as this window own work - both were"
    " re-measured at HEAD before any judgement, and the repair commit being"
    " UNPUSHED at open is stated above; (c) src/os/scan_five_still.py still"
    " crashes at its final [ORD-TOP] print on the GBK console, so the scan was"
    " run under PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT REPAIRED, and the"
    " repair stays carried because touching product src now would owe another"
    " battery; (d) Docker is absent on this host so no containerised bring-up"
    " of the sandbox faces is claimed; (e) the real 19.9 debit and the real"
    " msgSecCheck still wait on CEO physical items (merchant id, mini-program"
    " appid/secret); (f) tasks.md was not touched, it is the P-47 canonical"
    " board; (g) BigDomain-OSLoop still reads InteractiveToken and needs an"
    " ELEVATED shell for its S4U re-registration (carried ceo-pending physical"
    " item loop-s4u-reconcile).",
    "R2647 tokens: local=~11k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, six new decision tokens"
    " judged, one debt gate read and one queue head plus floor read, one"
    " liveness check by command line with zero reconcile writers, one"
    " byte-level re-measurement of the adopted evidence on seven axes plus a"
    " registry recount by import on four axes, one red-leg re-measurement"
    " naming its three failing suites, one HEAD/origin and commit-time"
    " comparison proving no commit landed under the leg, one dry-run fold at a"
    " true block boundary that agreed exactly then folded 697 with 14 tokens"
    " carried, one designed matrix FAIL with no byte written, one stamp-aligned"
    " regeneration checked byte-identical, one four-section write leg to a PASS"
    " verdict, one debt row closed and one opened through their shipped"
    " writers, one untracked launcher deleted before the commit, and the"
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
