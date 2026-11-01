"""closeout_R2345 - append this window round to state.json (R2345).

The figures written here are the ones measured this window, not estimates:
the gate that named an already-discharged battery, the register close and the
successor row it opened, the product face and its evidence, the canon repair,
fold 631 predicted against measured, and the queue re-read after the claim.

Dry run by default; --execute writes with a read-back proof and leaves no
temp residue. Pure ASCII source, stdlib only.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")

TICK = 2345
EVIDENCE = os.path.join(ROOT, "qa", "review-window-history-R2345.log")


def read_state():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def build_items():
    round_line = (
        "2026-11-01 R2345 product window (five-silence scan clean at open: "
        "empty git status --short and no .git/index.lock; BOTH decision "
        "readers agree on zero new rows over 65 live tokens - the python twin "
        "reads DEC rows=101 tokens=65 new=0 and the repaired PowerShell gate "
        "reads PASS rows=134 known_tokens=65 row_owner_tokens=54 - so no "
        "decision row was owed; the evolution ledger reads atbd_lines=0 "
        "unreplied_groups=0; the group orders tail is unchanged at the "
        "2026-11-01 10:4x baseline already acked as non-execution; benchmarks "
        "refreshed 2026-11-01 inside the seven-day gate). THE GATE NAMED WORK "
        "THAT WAS ALREADY DONE, and that is this window first finding: "
        "debt_gate read CLAIM-FIRST item=reconcile-battery-R2344 opened=R2343, "
        "while that battery had in fact been run at R2344 - qa/"
        "reconcile-all-R2344.log line 5494 carries RUNNER PASS (479/479 "
        "suites green, reconcile controls 7/7, 922.0s) and line 5434 carries "
        "expected criteria total=3850, exactly the pre-registered target - so "
        "the register was pointing this window at finished work because the "
        "row was never closed. Repaired at the register itself rather than by "
        "re-running fifteen minutes of battery: debt_close closed "
        "reconcile-battery-R2344 at R2345 (open 3->2, done 82->83, "
        "before=67293B after=67296B, readback ok) and debt_append opened "
        "reconcile-battery-R2346 first=yes (before=67296B after=68081B, "
        "readback ok), pre-registered at 480 suites / 3856 criteria. PRODUCT: "
        "claimed the tech head the reader named, state/queue/tech.md:391 "
        "prefix AC-RWH1 (review_window_history), whose AC-RWH1..AC-RWH6 were "
        "pinned INSIDE that row at R2327 BEFORE any code. The row own "
        "zero-occupancy claim was RE-MEASURED at HEAD instead of trusted: the "
        "five names hit ten paths and every one is prose or state "
        "(src/os/closeout_R2327.py, src/os/closeout_R2344.py, "
        "src/os/export_R2344.py, docs/status-export.json, heartbeat.txt, "
        "src/os/backlog.md, src/os/state.json, state/queue/tech.md), with "
        "ZERO executable occupancy and no src/os/review_window_history.py on "
        "disk. DELIVERED src/os/review_window_history.py plus "
        "src/os/test_review_window_history.py: the declarations list is read "
        "as a HISTORY instead of being collapsed into its last row - the "
        "parsed rows come from review_window_decl.shape (this module carries "
        "no second row law and no re.compile) and the agreement is asked of "
        "review_window_decl.resolve, so a DRIFT or UNPINNED reading carries "
        "the resolver own detail verbatim and the two readers cannot disagree "
        "about the same file; a declared_by that goes backwards refuses "
        "E_RWH_REWIND naming BOTH rows and BOTH rounds; every window move is "
        "named with its from/to numbers and both declaring rounds in FILE "
        "order; and a list with no move reads EMPTY-HISTORY rather than "
        "CLEAN, because 'never moved' and 'nothing pinned' may not read the "
        "same. SUITE PASS 6/6 twice with an identical criterion digest through "
        "the shared capture callable (qa/review-window-history-R2345.log, "
        "1294B, legs=2 identical=True adjacent=2, one utf-8 LF single writer) "
        "plus four adjacent os suites run directly and green (review_window "
        "6/6, queue_occupancy 6/6, followup_incomplete_cause 6/6, "
        "evidence_capture 6/6), wired os-review-window-history(6). LIVE on the "
        "real declaration: declarations=1 moves=0 rewind=none window=100 "
        "declared_by=R2305 verdict=EMPTY-HISTORY, RESOLVER AGREES, exit 0 - "
        "the honest reading of a one-row list, not a fabricated pass. BOARD: "
        "the claimed row closed against the files on disk, one real gap row "
        "seeded (review_window_history_wire, AC-RWHW1..AC-RWHW6 pre-registered "
        "in the row before any code, three anchors zero-occupancy at HEAD), "
        "gauge FLOOR-MET main 5/5 tech 10/10 explore 10/10, head now "
        "state/queue/tech.md:392 prefix AC-SEG1. STATE: the file was found off "
        "the write canon at open (73742B, off_indent=58 of 58 items, the same "
        "class repaired at R2338 and R2331), repaired through state_io --fix "
        "--execute with the payload-equality proof (73742B -> 74438B, "
        "CANON-CLEAN, off_indent=0) BEFORE any fold or append: fold 631 then "
        "moved log lines 1..10 - the R2333 and R2334 blocks COMPLETE on a "
        "round-block boundary, nothing cut mid-block, which is the shape the "
        "open debt row fold-block-boundary exists for - verbatim into logs/"
        "state-log-archive-2026-11.md, preop sha16 22e659a308d78d73, 17884 "
        "content bytes, 690 window tokens covered with tokens_missing=[], "
        "predicted 62530B equal to measured 62530B, margin 15970B, canon still "
        "clean at 49 log items."
    )
    tokens_line = (
        "R2345 tokens: local=~18k api=0 api_reason=product window - one live "
        "gate read that exposed a stale register row and closed it through the "
        "register own writer, one product module with its six pre-registered "
        "criteria and its suite (green on the second run after this window own "
        "test fixture was corrected, the module never touched across either "
        "fix), one dogfooded evidence capture with two adjacent suites "
        "captured and two more run directly, one live CLI reading of the real "
        "declaration, one runner wiring line, one queue close and one real gap "
        "row seeded through the anchor check, one canon repair, one "
        "round-block-boundary fold with its archive append and read-back, and "
        "the debt/state/export/heartbeat/board closeout; zero cloud calls and "
        "zero external API touches; the battery carries to R2346"
    )
    self_heal = (
        "R2345 self-heal check: BigDomain-OSLoop is registered and its "
        "principal still reads LogonType=InteractiveToken, which the "
        "2026-09-29 machine law forbids for every lane task; "
        "src/os/register_loop_task.ps1 already passes an explicit S4U "
        "principal and needs an elevated shell to apply, and this session runs "
        "unelevated, so the definition of the loop hosting this window was "
        "left untouched. Open local-lane item for an elevated window "
        "(hundred-and-fifth consecutive disclosure, carried as the stale row "
        "loop-s4u-reconcile in state/debt.md)."
    )
    decision = (
        "R2345 decision gate (D-20260930-19 step 2): the content-addressed "
        "diff of the group decisions.md against the stored baseline read NO "
        "new tokens, confirmed by BOTH readers after the R2344 repair (python "
        "twin: DEC rows=101 tokens=65 new=0; PowerShell gate: DEC PASS "
        "rows=134 known_tokens=65 row_owner_tokens=54), and the evolution "
        "ledger carries no @BigDomain row, so nothing was executed, rejected "
        "or acknowledged this window and the baseline is unchanged."
    )
    honest = (
        "R2345 honest disclosures: (a) the register row this window closed was "
        "discharged by R2344 and left open, and the gate therefore spent one "
        "pass pointing a fresh window at finished work - that is named as the "
        "round first finding rather than quietly re-running the battery, and "
        "the close cites the evidence line numbers it was decided on. (b) The "
        "first suite run did not go red: it CRASHED inside this window own "
        "patched-shape fixture, which handed declared_by back as a string "
        "where the shape contract returns an int, and the first correction "
        "went the WRONG WAY (it changed the correct int patch to a string and "
        "crashed again) before the doctored rows were made to respect the "
        "contract; no criterion was widened and the module source never "
        "changed across either fix. (c) AC-RWH5's wording '0 when the history "
        "is monotonic and unmoved' is read here as: a NAMED move exits 0, "
        "because a reader whose entire purpose is naming moves may not fail on "
        "the thing it names, and EMPTY-HISTORY also exits 0 while 2 is "
        "reserved for a rewind or a DRIFT - an interpretation disclosed rather "
        "than blurred, and pinned by the suite. (d) AC-RWH4 is proved on two "
        "worlds that differ by exactly the top-level window: on the agreeing "
        "one the history reads MOVED while the resolver reads AGREES, and on "
        "the drifting one the history carries 'DRIFT ' plus the resolver own "
        "detail text compared verbatim; the seed row's phrase 'matches the last "
        "row but not the row it replaced' is that MOVED case, NOT a DRIFT, and "
        "it is named here instead of being dressed as a refusal. (e) The fold "
        "created exactly TWO residue rounds (R2333, R2334), and the shipped "
        "append channel refused the first splice because R2345 itself was "
        "still untriaged - its register row is open and it had no log item yet "
        "- so the order is forced: append this log item first, then splice "
        "both rounds through the shipped writer. (f) tasks.md was left "
        "untouched: it is the P-47 canonical board and carries no row for this "
        "tech slice, disclosed rather than silently skipped. (g) The canon "
        "drift is a RECURRING writer defect (R2331, R2338, now R2345 all found "
        "items off the 16-space indent) and the repair is a session-level fix "
        "each time; it is named here because a repair that keeps being needed "
        "is a writer bug, not a housekeeping chore."
    )
    return [round_line, tokens_line, self_heal, decision, honest]


def main(argv):
    state = read_state()
    raw = io.open(STATE, "rb").read()
    print("state before=%dB log=%d tick=%d"
          % (len(raw), len(state["log"]), state["tick"]))
    items = build_items()
    print("append items=%d" % len(items))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    state["tick"] = TICK
    state["log"].extend(items)
    body = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    temp = STATE + ".tmp"
    # state.json canon is CRLF; a bare-LF write trips the STATE eol gate and
    # the next fold refuses E_STATE_LAYOUT (the R2344 birth-site note).
    with io.open(temp, "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(body)
    os.replace(temp, STATE)
    with io.open(STATE, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body or os.path.exists(temp):
        print("E_READBACK")
        return 3
    print("APPENDED state=%dB log=%d tick=%d readback=ok"
          % (len(back.encode("utf-8")), len(state["log"]), state["tick"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))