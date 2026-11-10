"""state_append_R2631 - append this round's log lines through the shipped dialect.

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
    "2026-11-11 R2631 VERIFICATION window on the battery the debt gate named first (reconcile-battery-R2630, pre-registered 644 suites / 4840 criteria at R2630 because that window moved product src bytes and one registry row, so the R2168 mixed-tree rule puts the full battery on the committed tree BEFORE any further product byte). Five readings at open: git status EMPTY at HEAD 44f7f3a9 equal to origin/main with no index.lock, ZERO unreplied @BigDomain rows in cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0 through the shipped scan_five_still face), the content-addressed D-/C- decisions scan read tokens=189 with new=0 over 323 rows, the group orders tail still at the 2026-11-11 06:0x row already judged knowledge-only at R2628, and benchmarks_refreshed 2026-11-10 sits one day inside the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2630 opened=R2630 carried=1 stale=no open=43 first=1; queue_head named tech line 654 prefix AC-EDMJ1 claimable=15 and queue_floor read FLOOR-MET at 5/5, 15/10, 10/10.",
    "2026-11-11 R2631 THE TARGET WAS RE-MEASURED BY IMPORT AND THE OLDEST AVAILABLE LEG WAS MEASURED SHORT, so the new leg is genuinely owed rather than re-labelled: reconcile_all.SUITES read 644 suites / 4840 criteria at launch through the shipped accessor, byte for byte the registered number, while the newest evidence leg on disk (qa/reconcile-all-R2627.log, 1092115B, 06:37 today) closes on RUNNER PASS (643/643 suites green, reconcile controls 7/7, 2454.3s) - exactly one suite short of the tree this window stands on, because R2630 added that row after that leg ran. A prior leg can therefore NOT be adopted here, and the R2584/R2607 practice of adopting an interrupted attempt's finished leg does not apply because no battery process was live at open (checked by command line on every python process).",
    "2026-11-11 R2631 THE LEG WAS LAUNCHED DETACHED THROUGH A REFUSING LAUNCHER AND IS STILL RUNNING AT CLOSEOUT, WHICH IS DISCLOSED RATHER THAN DRESSED UP AS GREEN: src/os/launch_battery_R2631.py refuses when the registry has moved from 644/4840 or when the evidence file already exists, Popen'ed src/os/battery_stream.py with CREATE_NO_WINDOW|DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP, and put the stream and the pid in SEPARATE files under logs/ (battery-R2631.stream, battery-R2631.pid) so qa/ is written by the single shipped writer and never by a shell redirection. pid 88352 with its reconcile_all child 60032 were confirmed live by command line at 07:08:08 and again at 07:09:57, the stream measuring 136998 bytes over 762 lines with its newest line reading 'PASS suite pay-v3-real exit=0 pass-lines=9 fail-lines=0 criteria=9 3.7s'. A full leg has measured 2454-4100s in this repository against this window 25-minute budget and the observed rate at closeout is about 12% of a full leg in eight minutes, so the debt row reconcile-battery-R2630 STAYS OPEN at its registered 644/4840 and the next window adopts the leg and closes the row (the R2607 precedent) instead of a green claim this window cannot make.",
    "2026-11-11 R2631 ONE LONG-STANDING ARTIFACT IS NAMED RATHER THAN SMOOTHED: the stream first line reads 'no evidence path: shell-capture mode, evidence dialect follows the caller', which is a line the inner runner reconcile_all prints on its own and which prior windows have disclosed in the same shape, not a launcher that dropped its --evidence argument - the launcher process command line was read back and does carry '--evidence ...\\qa\\reconcile-all-R2631.log'. The line is recorded here because a reader who opens the stream first will see it and should not have to guess.",
    "R2631 FOLD AND LEDGER, disclosed: state.json read 78226B against the 78500B waterline at open, i.e. FOLD-CLEAR with only 274B of margin, which could not carry this round's own lines, so fold 688 was run through the shipped face src/os/state_fold_run.py over the COMPLETE R2630 block (items 95..102, ending on its push and export receipt) at 78226B -> 70921B with margin 7579 and 95 live lines, archive VERIFIED and layout AGREE, its 6 tokens preserved verbatim (AC-EDMG1 AC-EDMI1 AC-EDMI6 AC-EDMJ1 AC-EDMJ6 R-MET). The first dry run was REFUSED with token-missing because that summary carried only four of the six, and the predicate refused rather than writing - the shipped fail-closed face working, corrected by re-reading the window token set through state_fold.plan_fold instead of guessing. ledger_lines --check read VERDICT CLEAN before and after the fold.",
    "R2631 honest disclosures: (a) ZERO product points on the Executive Protocol scale - no product src byte was written, because the debt gate puts the owed battery before any further product work and that leg is still running; (b) the battery is NOT green and is NOT claimed green - it is live at closeout with its evidence file not yet written, so the debt row stays open at 644/4840 and docs/sandbox-suite-matrix.md keeps whatever honest reading it already carried; (c) the newest existing leg was measured at 643/643 rather than assumed stale, which is what makes the new leg a real debt rather than a bookkeeping repeat; (d) the proposal track is clear for this window without a new entry: BD-PROP-007 (battery handoff receipt, window 11-08~11-14) is already open and describes exactly this handoff shape, so filing a second one would be an inflated count; (e) the one-off launcher was committed rather than deleted so the 644/4840 guard it enforced stays re-readable, which is the R2607 choice and not the R2584 one; (f) Docker is absent on this host so no containerised sandbox bring-up is claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (h) tasks.md was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop still reads InteractiveToken and needs an ELEVATED shell for its S4U re-registration (carried ceo-pending physical item loop-s4u-reconcile).",
    "R2631 tokens: local=~9k api=0 api_reason=verification window - one five-silence scan with the content-addressed decisions scan, the group orders tail and the ledger face actually read, one debt gate read naming the battery, one queue head and floor read, one registry target re-measured by import on both axes, one newest-leg reading measured at 643/643 against the 644 tree, one detached battery launched through a refusing one-off launcher with its stream and pid in separate files and its liveness re-read twice, one fold refused by its own token predicate then corrected and run to CLEAR, one ledger check CLEAN, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
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
