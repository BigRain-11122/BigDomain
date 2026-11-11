"""state_append_R2639 - the R2639 verification window narrative and tokens.

Every number below was measured off the tree in this window: the red leg on
bytes, the repair predicted-then-landed byte counts, the gate readings and the
retry launch.
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
    "2026-11-11 R2639 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2638, pre-registered 647 suites / 4858"
    " criteria at R2638). The window opened on an interrupted attempt of the"
    " same round: git status carried exactly two untracked files - the"
    " finished red leg qa/reconcile-all-R2638.log and its one-off launcher -"
    " with no index.lock, so the leg was ADOPTED and measured rather than"
    " re-run. Five readings: zero unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed D-/C-/P-/O-/T-/XL- decisions scan read tokens=189"
    " new=0 over 323 rows; the group orders tail moved to 2026-11-11 12:05"
    " (an event-shift T1 row naming three-machine capacity, the bm-b physical"
    " offline and two asset-library false greens) and is judged"
    " knowledge-only for this company; benchmarks_refreshed 2026-11-10 sits"
    " one day inside the seven-day gate. debt_gate read CLAIM-FIRST"
    " item=reconcile-battery-R2638 opened=R2638 first=1 open=43.",

    "2026-11-11 R2639 THE ADOPTED LEG WAS RED AND IS MEASURED NOT QUOTED:"
    " qa/reconcile-all-R2638.log reads 1095192B, utf-8 True, bom=False,"
    " crlf=0, lone_cr=0, nul=0, 8608 lines, 647 real suite rows carrying 647"
    " UNIQUE names, 646 PASS rows and exactly ONE red, and an independent"
    " criteria recount over the per-row fields summing to EXACTLY 4858"
    " against the pre-registered number. The second line that begins FAIL is"
    " the runner own closing summary (FAIL suites 646/647 green, expected"
    " criteria total=4858, suite cap 600s overrides=1) and is named here"
    " rather than counted as a second suite. The red suite is"
    " os-ledger-closeout exit=2 pass-lines=7 fail-lines=1 criteria=8 0.6s and"
    " its failing criterion is AC-LGN8 legacy faces unchanged, live log"
    " closes clean.",

    "2026-11-11 R2639 ROOT CAUSE READ OFF THE SHIPPED FACE: reproduced alone"
    " with python src/os/test_ledger_closeout.py in under a second, then"
    " diagnosed by calling the shipped reader directly - check_closeout"
    " returned verdict NOT_MONOTONIC with previous_round 2638 against a live"
    " log whose own last ledger entry is also round 2638, because state.json"
    " carried TWO ledger entries for round 2638: the R2637 VERIFICATION window"
    " had written its tokens line labelled R2638 (the TICK, not the window -"
    " the same class of defect the R2638 receipt itself disclosed), and the"
    " R2638 product window then wrote its own R2638 line. REPAIRED AT THE"
    " BIRTH SITE with src/os/repair_R2639_round_label.py, which relabels that"
    " one line to the shipped same-round second-window form R2637 second-half"
    " tokens: (the form already present in this log for R2635) - honest about"
    " the round it belongs to and deliberately NOT a ledger entry, so the"
    " one-entry-per-round law holds. The dry run predicted 73623 -> 73635"
    " (+12) and the execute hit it exactly with a byte read-back, and a"
    " second --check read ALREADY (+0) so the repair is idempotent. The red"
    " suite then read SUITE PASS 8/8 alone, ledger_lines --check read VERDICT"
    " CLEAN with new_missing none and new_orphan none, and state_fold --check"
    " read FOLD-CLEAR at 73635B against the 78500B gate with margin 4865 and"
    " 84 live lines. The red leg plus the repair were committed ALONE as"
    " 2b2b5318 so the retry runs on a committed tree.",

    "2026-11-11 R2639 FOLD AND RETRY: fold 695 ran at a true block boundary"
    " after a dry run that agreed exactly - windows 74..84, the COMPLETE R2637"
    " verification block and the COMPLETE R2638 product block, each ending on"
    " its own push line - taking state.json 73635B -> 62259B with margin"
    " 16241, archive VERIFIED, layout AGREE and all 14 tokens preserved"
    " verbatim in the fold summary line. The retry was then launched on that"
    " committed tree: the registry target was re-measured by import at 647"
    " suites / 4858 criteria / 647 unique names BEFORE the launch, and one"
    " refusing one-off launcher Popen-ed src/os/battery_stream.py with"
    " CREATE_NO_WINDOW|DETACHED_PROCESS and its stream and pid in SEPARATE"
    " files under logs/ (pid 48708), so qa/ is written by the single writer"
    " and never by a shell redirection. At closeout the leg is LIVE (64 PASS"
    " suite rows and ZERO FAIL rows at the last read) with its evidence path"
    " qa/reconcile-all-R2638-retry.log not yet written, so"
    " reconcile-battery-R2638 STAYS OPEN at its registered 647/4858 and the"
    " next window ADOPTS this leg and closes the row (the"
    " R2601/R2607/R2614/R2635 precedent).",

    "R2639 honest disclosures: (a) ONE product point on the Executive"
    " Protocol scale - a runnable, idempotent repair face with a --check and"
    " an --execute that a maintainer can re-run - but nothing a CEO could"
    " newly open and no P-47 business surface moved, so every P-47 item still"
    " waits on CEO physical pieces (merchant id, mini-program"
    " appid/secret); (b) the battery is NOT green and is NOT claimed green -"
    " the adopted leg was red on one real defect, that defect is repaired and"
    " proved at its own suite, and the full battery is live at closeout; (c)"
    " THE CLOSEOUT COMMIT LANDS UNDER THE LEG, so under the R2614 discipline"
    " the next window must re-run the export write-sensitive suites on the"
    " FINAL committed tree before it accepts the verdict, and that obligation"
    " is named here rather than discovered later; (d) this window ran past"
    " its twenty-five minute budget and that overrun is named rather than"
    " hidden; (e) the repair is a DATA repair (one label in state.json) and"
    " it is registered nowhere as a suite, so it is a one-off tool like"
    " repair_R2522_round_token.py and repair_dialect_R2530.py; (f) Docker is"
    " absent on this host so no containerised bring-up is claimed; (g)"
    " src/os/scan_five_still.py still crashes at its final [ORD-TOP] print on"
    " the GBK console (a BOM in the group orders row), unchanged and still"
    " carried, because the three judgments above it print first; (h) tasks.md"
    " was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop"
    " still reads InteractiveToken and needs an ELEVATED shell for its S4U"
    " re-registration (carried ceo-pending physical item"
    " loop-s4u-reconcile).",

    "R2639 tokens: local=~11k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face actually read, one debt gate read"
    " naming the battery, one adopted red leg re-measured on seven byte axes"
    " with an independent criteria recount, one red suite reproduced alone and"
    " its cause read off the shipped check face, one birth-site repair written"
    " with a dry run that predicted the exact +12 bytes and an idempotent"
    " re-check, one red suite re-run green and two gates re-read, one fold at"
    " a true block boundary with 14 tokens carried verbatim, one refusing"
    " one-off launcher and one detached retry leg with its target re-measured"
    " by import first, and the state/export closeout; zero cloud calls and"
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
