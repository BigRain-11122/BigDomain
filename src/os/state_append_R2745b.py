"""state_append_R2745b - record the R2745 window through the canonical writer."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
TICK = 2745

LINES = [
    "2026-11-15 R2745 MONITORED-WAIT window that turned into a MEASURED LEDGER "
    "REPAIR, zero product bytes by the R2168 mixed-tree rule because "
    "reconcile-battery-R2742 is still OPEN and its leg is still running. Five "
    "readings at open: git status EMPTY at HEAD cabbc3e2 equal to origin/main with "
    "no index.lock; ZERO unreplied @BigDomain rows in the group ledger "
    "(atbd_lines=0 unreplied_groups=0); the content-addressed decisions face read "
    "rows=131 tokens=67 new=0 so no decision row was executed; the group orders "
    "tail is the carried 2026-11-14 00:30 main-control row, older than the 01:3x "
    "baseline and therefore knowledge-only; benchmarks_refreshed 2026-11-14 inside "
    "the seven-day gate. debt_gate read CLAIM-FIRST item=reconcile-battery-R2742 "
    "first=1 open=11, queue_head read tech line=713 prefix AC-LKNF1 claimable=10, "
    "queue_floor read FLOOR-MET main 5/5 tech 10/10 explore 10/10 shortfall=0, and "
    "leg_status read LEG-ALIVE-NO-EVIDENCE pid=64528 pass=644 fail=5 remaining=32 "
    "target=676 with no evidence file and no closing BATTERY rc= line.",

    "R2745 THE FIVE RED ROWS WERE ONE BIRTH SITE AND IT WAS REPAIRED THERE, "
    "measured rather than guessed: os-ledger-fold-kind read FAIL AC-FCLS6, and "
    "ledger_lines.audit on the live file read clean=False "
    "rounds_without_ledger=[2742] with ledger_without_round=[] and errors=[] - six "
    "R2742 narrative lines sat live, no R2742 tokens line sat live, and the "
    "archive held none either (its tail still ends at R2729), so the R2742 "
    "closeout simply never wrote its ledger line. Repaired by "
    "src/os/state_append_R2745.py through the canonical writer "
    "state_io.write_document: the line is inserted at index 80, its own "
    "chronological place, and its api_reason says in plain words that R2745 "
    "RECONSTRUCTED it, that local is an ESTIMATE (~13k) drawn from the actions that "
    "window recorded, and that api=0 is certain because its own disclosures record "
    "zero cloud calls and zero external API touches. Readback: log 89->90 tick 2745 "
    "ok=True; state_io --check CANON-CLEAN 83035B crlf=100 bare_lf=0 lone_cr=0 "
    "log_items=90 off_indent=0; and all five previously red suites re-ran GREEN on "
    "the repaired live tree - os-ledger-lines 8/8, os-ledger-archive 8/8, "
    "os-ledger-baseline 8/8, os-ledger-fold-kind 6/6, "
    "os-ledger-fold-kind-dateprefix 6/6. Under the R2738 precedent a red row "
    "repaired mid-leg is NOT evidence about the repaired tree, so the adopting "
    "window must re-run those five rather than read this leg green on them.",

    "R2745 THE FOLD CALIBER CONFLICT IS NOW LOCATED TO TWO LINES OF CODE INSTEAD OF "
    "DESCRIBED, and that is the only thing carried forward from the R2744 refusal: "
    "logs_toolkit.split_ps_layout requires exactly sixteen spaces before each log "
    "item quote and cmd_fold hardcodes its inserted summary literal at sixteen "
    "spaces, while the canonical writer state_io.write_document emits TWO-space "
    "items and state_io --check calls them CANON-CLEAN off_indent=0 - so the hint "
    "logs_toolkit eol --fix-indent can never be right for this file, because it "
    "rewrites items to sixteen and state_io then reads CANON-DRIFT off_indent=88, "
    "which is exactly what R2744 measured. The repair is to derive the item indent "
    "FROM THE DOCUMENT in split_ps_layout (accepting the canonical two-space "
    "caliber beside the legacy sixteen and still refusing an eight-space or "
    "otherwise mismatched block, so AC-LF1 and AC-FI5 keep gating) and to use that "
    "detected indent for the summary literal, then re-canon and fold. It was NOT "
    "done at R2745 for one measured reason: os-logs-toolkit had not yet run inside "
    "the live leg (no such row in the stream), so patching it now would make that "
    "leg measurement ambiguous rather than clean. state.json stands at 83035B "
    "against the 78500B waterline and both this gap and the waterline stay RED and "
    "declared.",

    "R2745 WHAT THIS WINDOW DID NOT DO, by law and by choice: (a) no product src "
    "byte, no registry row, no queue row and no matrix stamp moved while the leg "
    "runs, so the registry is unmoved at 676 suites / 5032 criteria and NO "
    "successor battery is owed on top of the one already open; (b) the leg was NOT "
    "adopted and its stream was NOT read as a verdict, because 644 of 676 with a "
    "closing line absent is neither green nor red; (c) the dead per-round export "
    "hook in src/os/export_R2431.py is STILL OWED and now overdue by TEN windows, "
    "carried on the board with its three R2731 criteria; (d) no proposal was "
    "written because docs/proposals.md already carries BD-PROP-009 this week with "
    "its two-week visit on 2026-11-28, and a second proposal inside the quota would "
    "be the fourth idle form; (e) no HQ-FEEDBACK line was added, P-32 is a "
    "zero-inflation rule and the last P2 line is still fresh.",

    "R2745 honest disclosures: (a) ZERO product points by the Executive Protocol "
    "scale - a reconstruction, five re-run suites and a located root cause are "
    "evidence and unblocking, not something a CEO can newly open, and every P-47 "
    "business face still waits on CEO physical pieces (merchant id, mini-program "
    "appid/secret); (b) the reconstructed R2742 ledger line carries an ESTIMATED "
    "local token count and says so inside its own api_reason rather than passing an "
    "estimate off as a measurement; (c) the missing ledger line is this register "
    "own defect class (a closeout that wrote five facts lines and no ledger), not a "
    "tool bug, and the raw materials for it were still on disk because nothing had "
    "folded that block; (d) the five green re-runs are on the repaired live tree "
    "and this window claims no battery green; (e) src/os still carries hundreds of "
    "one-off closeout scripts, pre-existing bloat this window neither created nor "
    "cleaned, and this window added two; (f) tasks.md was not touched, it is the "
    "P-47 canonical board; (g) Docker is absent on this host; (h) BigDomain-OSLoop "
    "still reads InteractiveToken and needs an ELEVATED shell for its S4U "
    "re-registration (carried ceo-pending physical item loop-s4u-reconcile).",

    "R2745 tokens: local=~11k api=0 api_reason=monitored-wait plus one measured "
    "repair - one five-silence scan with the debt gate, the queue head, the queue "
    "floor and the shipped scan face, one leg_status read plus a FAIL-name census "
    "over the stream, one ledger audit that named the missing round, one root-cause "
    "read of the two offending lines, one canonical-writer restore with readback, "
    "five suites re-run green on the repaired tree, one board rewrite and one "
    "export driver, and the closeout commit; zero cloud calls and zero external API "
    "touches",
]


def main():
    raw = state_io.read_raw(STATE)
    data = state_io.parse(state_io.decode(raw))
    before = len(data["log"])
    data["log"].extend(LINES)
    data["tick"] = TICK
    state_io.write_document(STATE, data)
    back = json.load(io.open(STATE, encoding="utf-8"))
    ok = (back.get("tick") == TICK
          and len(back.get("log") or []) == before + len(LINES)
          and back["log"][-len(LINES):] == LINES)
    sys.stdout.write("APPENDED tick=%s log %d->%d ok=%s\n"
                     % (back.get("tick"), before, len(back.get("log") or []), ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
