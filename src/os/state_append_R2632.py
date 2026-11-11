"""state_append_R2632 - append this round's log lines through the shipped dialect.

Every number in these lines was MEASURED on this tree in this window. The
writer routes the payload through general_writer_dialect_audit.payload_for so
the file keeps its indent=1, no-trailing-newline ASCII layout.
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
    "2026-11-11 R2632 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2630, pre-registered 644 suites / 4840 criteria at R2630). Five readings at open: git status EMPTY at HEAD 8433133a equal to origin/main with no index.lock, ZERO unreplied @BigDomain rows in cph4/evolution-ledger.md, the content-addressed D-/C- decisions scan read tokens=188 with new=0 over 323 rows, the group orders tail still carrying the 2026-11-11 06:0x committee row already judged knowledge-only for this company (a bm-b physical power-on reminder), and benchmarks_refreshed 2026-11-10 sitting one day inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2630 opened=R2630 carried=2 stale=no open=43 first=1; queue_head named tech line 654 prefix AC-EDMJ1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10 with main open=6 done=5 gated=1 claimable=5, tech open=16 done=480 gated=1 claimable=15 and explore open=10 done=239 claimable=10.",
    "2026-11-11 R2632 THE CARRIED LEG WAS ADOPTED AND ITS GREEN IS MEASURED NOT QUOTED: the battery R2631 launched at 07:06:02 (launcher pid 88352 with its reconcile_all child 60032, both confirmed live at open by command line) finished this window, and its evidence was measured on bytes rather than trusted from a stream tail - qa/reconcile-all-R2631.log reads 1092945B before the follow-up block and 1094896B after the 1951B append, utf-8 with bom=False, crlf=0, lone_cr=0, nul=0 over 8583 lines, closing on 'RUNNER PASS (644/644 suites green, reconcile controls 7/7, 2815.9s)' with 'BATTERY rc=0 2816.1s' beneath it, ZERO FAIL suite rows, 644 PASS suite rows carrying 644 UNIQUE names, and an INDEPENDENT recount over their own criteria fields summing to EXACTLY 4840 (digest C74C09A0961B8F1716BC9645). The registry was re-measured by import BEFORE and AFTER through reconcile_all.SUITES and read 644 suites / 4840 criteria / 644 unique names / 644 unique paths, byte for byte the number R2630 pre-registered, so the prediction matched the measurement with no delta to name.",
    "2026-11-11 R2632 FOLLOW-UP, DEBT AND BOARD in the designed order: the dry run read matrix FAIL first BY DESIGN at on-disk 65817B against regenerated 65817B with NO byte written while fingerprint read PASS CLEAN domains=5, profile read PASS byte-identical and census read PASS DRIFT-CLEAN, for VERDICT R2631 FAIL failing=matrix - the sizes are IDENTICAL and the difference is CONTENT (the evidence column and the green count), which is named here so no reader thinks a size check caught it; docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS round own green leg through src/sandbox/suite_matrix.py --evidence qa/reconcile-all-R2631.log --stamp-from docs/sandbox-suite-matrix.md to 65817B at 644 suites / 4840 criteria with its green line honestly reading 644/644 self-describing, --check then read byte-identical at rc=0, and the four sections re-ran to VERDICT R2631 PASS failing=none (APPENDED 1951B eol_ok=True). DEBT through the shipped writers: reconcile-battery-R2630 was closed at its predicted and measured 201294B -> 201297B (line 370, open 43->42, done 310->311, readback ok) and product-face-R2632 was appended first=yes (201297B -> 202091B, readback ok) naming the next window a PRODUCT face on the queue head state/queue/tech.md:654 prefix AC-EDMJ1, whose AC-EDMJ1..AC-EDMJ6 were pinned in that row at R2630 BEFORE any code. NO successor battery is owed: this window moved no product src byte and no registry row, and the registry stands unmoved at 644 suites / 4840 criteria recounted by import. queue_head re-read line 654 claimable=15 and queue_floor re-read FLOOR-MET; no queue row was opened or closed, because a verification window writes no board row.",
    "R2632 FOLD AND LEDGER, disclosed: state.json read 77540B against the 78500B waterline at open, i.e. FOLD-CLEAR with only 960B of margin, which could not carry this round's own lines, so fold 689 was run through the shipped face src/os/state_fold_run.py over the COMPLETE R2631 block (items 96..103, ending on its push and export receipt) at 77540B -> 69848B with margin 8652 and 96 live lines, archive VERIFIED and layout AGREE. The first dry run was REFUSED with token-missing because my summary carried five of the eight tokens the window actually holds, and the predicate refused rather than writing - the shipped fail-closed face working; the set was then re-read through state_fold.plan_fold (AC-EDMG1 AC-EDMI1 AC-EDMI6 AC-EDMJ1 AC-EDMJ6 BD-PROP-007 D-CLEAR R-MET) instead of guessed and the dry run then agreed exactly before the execute. The file CRLF newline dialect was read from the plan rather than assumed.",
    "R2632 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product src byte was written; the deliverable is a green 644/4840 battery on disk, a matrix document whose evidence column names THIS round own leg, one closed debt row and one opened, and nothing a CEO could newly open; (b) the leg was AUTHORED BY R2631 and is ADOPTED here, not built here - it is presented as an adopted leg, not as this window own work; (c) this window ran FAR past its 25-minute budget because the leg took 2815.9s (about 47 minutes) and it waited rather than repeating the R2631 outcome of closing with the battery still live, and that overrun is named rather than hidden; (d) the shell tool cancelled one 300-second wait at its five-minute silence limit, and the measurement printed before the cancellation is exactly the one carrying the green closing line, so nothing had to be re-run; (e) the stream first-line artifact ('no evidence path: shell-capture mode') was already named at R2631 and is not re-described here; (f) Docker is absent on this host so no containerised sandbox bring-up is claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2632 tokens: local=~8k api=0 api_reason=verification window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face actually read, one debt gate read naming the battery, one queue head and floor read on all three lines, one live battery adopted and measured on bytes with its encoding counters, an independent suite recount and a criteria recount to exactly 4840, one registry target re-measured by import on both axes before and after, one designed matrix FAIL at identical bytes with the content difference named, one stamp-aligned regeneration from this round own green leg checked byte-identical, one four-section follow-up to a PASS verdict, one debt row closed and one opened through their shipped writers, one fold refused by its own token predicate then corrected from the plan and run to CLEAR, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
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
