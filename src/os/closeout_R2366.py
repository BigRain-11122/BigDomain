"""closeout_R2366.py - append this window's items and fold the log if needed.

One-off for the round. The state file is written through the shipped canon
rules (state_io.canon: one item line per log entry, CRLF, 16-space items) and
the fold, if one is due, runs through state_fold.fold rather than by hand.

Usage: python src/os/closeout_R2366.py
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
GATE = 78500
RESERVE = 6000

NEW_DEC = ["D-20261102-07", "D-20261102-08", "D-20261102-09",
           "D-20261102-10", "D-20261102-11", "D-20261102-12",
           "D-20261102-13"]

ITEMS = [
    "2026-11-02 R2366 product window (five-silence scan clean at open: empty "
    "git status --short at ee715015, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=124 tokens=81 new=7, "
    "the group orders tail still the 2026-11-01 10:4x model-policy baseline "
    "already acknowledged as non-execution, benchmarks refreshed 2026-11-01 "
    "inside the seven-day gate). THE GATE NAMED FINISHED WORK AND THAT WAS THE "
    "WINDOW FIRST FINDING: debt_gate --check read CLAIM-FIRST "
    "item=product-face-R2365 opened=R2364 while R2365 had shipped it, so the "
    "row was verified by MEASUREMENT (src/os/queue_floor_delivered_wire.py, "
    "its suite, qa/queue-floor-delivered-wire-R2365.log and its live leg all "
    "on disk, os-queue-floor-delivered-wire wired in the runner, tech row 411 "
    "stamped done) and closed through its own writer (debt_close: open 3->2, "
    "done 95->96, 76141B -> 76144B, readback ok) instead of re-running work. "
    "PRODUCT: claimed the queue head the reader then named, state/queue/tech.md"
    ":412 prefix AC-BFH1 (battery_followup_help_wire), whose AC-BFH1..AC-BFH6 "
    "were pinned INSIDE that row at R2365 BEFORE any code; the anchor check was "
    "re-run at HEAD and E_BFH, os-battery-followup-help-wire and "
    "test_battery_followup_help_wire were git grep -F zero-occupancy while "
    "battery_followup_help_wire and AC-BFH appeared only in prose and state "
    "files - recorded as such rather than reported as a clean null.",
    "R2366 the wire and the caller: shipped src/os/battery_followup_help_wire.py"
    " plus src/os/test_battery_followup_help_wire.py, and "
    "src/os/battery_followup.py now carries module-level TAKES and FLAGS (its "
    "parser own tables, lifted so the wire renders from THEM) and raises "
    "HelpAsked on --help/-h, which main answers at exit 0 with the wire usage "
    "block. Both halves of that block are IMPORTED: the house line comes from "
    "reconcile_all.CLI_CONTRACT read through runner_arg_guard.load_contract "
    "(the guard own importer), and the flag lines come from battery_followup "
    "TAKES/FLAGS, so no second flag table and no second importer is written. "
    "The wire validates the three keys it actually reads and refuses "
    "E_BFH_NO_CONTRACT rather than raising a bare KeyError from inside a "
    "renderer. MEASURED: SUITE PASS 6/6 twice with an identical criterion "
    "digest 7e6881b726a46311 (qa/battery-followup-help-wire-R2366.log, 1411B, "
    "legs=2 identical=True, single utf-8 LF writer through "
    "src/os/evidence_R2366.py - never a shell redirect), os-battery-followup "
    "STILL 6/6 and os-run-argument-guard 6/6 unchanged, wired "
    "os-battery-followup-help-wire(6).",
    "R2366 live action, not a plan: `python src/os/battery_followup.py --help` "
    "on the real tree now answers at exit 0 with the derived usage block and a "
    "house line reading `reconcile_all.py [evidence_log_path] flags=(none)` "
    "(qa/battery-followup-help-wire-live-R2366.log, 380B), where the same call "
    "was exit 5 E_BFU_BAD_ARGS before this window. The unknown-flag path was "
    "measured on the wire CLI, which refuses at exit 2 naming the token, while "
    "the follow-up own unknown-flag code stays 5 - see disclosures (b).",
    "R2366 board: tech row 412 stamped done ([done 2026-11-02 R2366], bracket "
    "payload 22 chars inside the queue_done_stamp 60-char law) and one REAL "
    "measured gap row seeded (contract_usage_renderer, AC-CUR1..AC-CUR6 "
    "pre-registered in that row, five anchors zero-occupancy at HEAD): "
    "runner_arg_guard renders one usage block and this window wire renders a "
    "second one from the same kind of contract, measured live by the guard own "
    "--guard-help, so the tree carries two formatters for one shape. Tech "
    "claimable went 10 -> 9 on the stamp and 9 -> 10 on the seed, floor reads "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 with delivered=0.",
    "R2366 tokens: local=~34k api=0 api_reason=product window - one product "
    "wire and its six-criteria suite written to criteria pinned one round "
    "earlier, one caller changed to route its answer through the wire, one "
    "live verification that a stale register row was already discharged, one "
    "register close and one successor battery row opened at a measured target, "
    "two evidence legs with an identical criterion digest plus a live capture, "
    "three adjacent suites re-run green, one queue row stamped and one measured "
    "gap row seeded, and the state/export/heartbeat/board closeout; zero cloud "
    "calls and zero external API touches",
    "R2366 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this window "
    "was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-second consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2366 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read SEVEN new tokens "
    "(D-20261102-07..13) and every one was read in full. D-07 is the collection "
    "batch and records this company as an explicit no-op (mtime 10-29 05:15); "
    "D-08 is the line-triage decision/threshold decoupling, D-09 the duanju "
    "line supply gap, D-10 the LANE-REGISTRY delivery and its UNVERIFIABLE "
    "change_time judgement, D-11 the 20 UNEXPECTED-DISABLED split into a "
    "KnownDisabled whitelist, D-12 the external-audit kill-or-deliver ruling "
    "and D-13 the Biggame Art/Builds directory gap. None dispatches this "
    "company: executed 0, rejected 0, acknowledged as non-execution 7, and the "
    "baseline is widened to all seven so they cannot re-flag.",
    "R2366 honest disclosures: (a) the register row this window closed had been "
    "left open by R2365 after R2365 shipped it - the R2345/R2354 shape again - "
    "and it is named as the round first finding rather than quietly re-run. (b) "
    "AC-BFH3 is discharged on the WIRE own CLI (exit 2 naming the token, the "
    "guard refusal contract), NOT by re-pinning battery_followup own "
    "unknown-flag code: AC-BFU5 already pins that code at 5 and the printed "
    "line byte for byte, and AC-BFH4 demands every other code and line stay "
    "byte-identical, so moving it to 2 would rewrite an already-pinned "
    "criterion - AC-BFU5 re-ran 6/6 and is the proof nothing moved. (c) The "
    "first suite run was RED on AC-BFH4 and the red was this window own "
    "fixture, not the module: it compared the CLI stdout to the module own "
    "renderer without allowing for the platform CRLF translation that every CLI "
    "in this tree gets, so the comparison now normalises the transport EOL and "
    "nothing else; the criterion was not widened. (d) The second RED was "
    "AC-BFH5 pinning the --json key order from memory instead of from the "
    "emitted dict; the pinned tuple was corrected to the measured order. (e) "
    "The first draft of usage_text printed the value flags without their "
    "placeholders, which reads as `--evidence --label ...` and is a poor answer "
    "to the question this window exists to answer, so the metavar is now "
    "derived from each option own key - the criterion digest did not move "
    "(7e6881b726a46311 both before and after). (f) src/os/seed_R2366.py "
    "reported readback=False while the row HAD landed correctly: its own guard "
    "counted the string AC-CUR1, which appears twice inside the row it wrote. "
    "The file was verified independently (row present, file ends on it, tech "
    "floor rose to 10/10) and the false negative is reported here rather than "
    "edited away. (g) tasks.md was left untouched: it is the P-47 canonical "
    "board and carries no row for this tech slice, disclosed rather than "
    "silently skipped.",
]


def read_state():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_state(text):
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    return back


def block_boundaries(log):
    """Log indexes (1-based) that END a round block: a tokens line."""
    out = []
    for index, line in enumerate(log):
        if re.match(r"^(?:\d{4}-\d{2}-\d{2} )?R\d+ tokens:", line.strip()):
            out.append(index + 1)
    return out


def main():
    raw = read_state()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    tick = data.get("tick", 0) + 1
    data["tick"] = tick
    data["last_decision_rows"] = 124
    tokens = data.get("last_dec_tokens", [])
    added = [tok for tok in NEW_DEC if tok not in tokens]
    data["last_dec_tokens"] = tokens + added
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    write_state(text)
    size = len(text.encode("utf-8"))
    print("STATE tick=%d items=+%d tokens=+%d before=%dB after=%dB"
          % (tick, len(ITEMS), len(added), before, size))

    guard = 0
    while True:
        measure = state_fold.measure(size, GATE)
        if not measure["fold_needed"]:
            print("FOLD none needed bytes=%d margin=%d"
                  % (size, measure["margin"]))
            break
        current = read_state()
        state = json.loads(current)
        log = state["log"]
        ends = block_boundaries(log)
        target = GATE - RESERVE
        chosen = None
        for end in ends:
            if end >= len(log):
                continue
            window = log[:end]
            found = set()
            for line in window:
                found |= set(state_fold.PAT.findall(line))
            rounds = sorted(set(re.findall(r"R(\d{4})", " ".join(window))))
            summary = ("Fold %d: log lines 1..%d folded verbatim into the "
                       "archive at a TRUE round-block boundary; rounds %s; "
                       "tokens %s"
                       % (642 + guard, end, ",".join("R" + r for r in rounds),
                          " ".join(sorted(found))))
            try:
                plan, folded = state_fold.plan_fold(
                    current.encode("utf-8"), state, 1, end, summary,
                    reserve=0, gate=GATE)
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                print("FOLD plan refused end=%d %s" % (end, exc))
                continue
            if not plan["token_ok"]:
                print("FOLD token gap end=%d missing=%d"
                      % (end, len(plan["tokens_missing"])))
                continue
            if plan["predicted_bytes"] <= target:
                chosen = (end, summary, plan)
        if chosen is None:
            print("FOLD none fits target=%d bytes=%d" % (target, size))
            break
        end, summary, plan = chosen
        result = state_fold.fold(REPO, "R2366", 642 + guard, 1, end, summary,
                                 reserve=0, gate=GATE, execute=True)
        size = os.path.getsize(STATE)
        print("FOLD %d window=1..%d lines=%d predicted=%dB measured=%dB "
              "log=%d" % (642 + guard, end, plan["window_lines"],
                          plan["predicted_bytes"], size,
                          result.get("folded_log_len", -1)
                          if isinstance(result, dict) else -1))
        guard += 1
        if guard > 6:
            print("FOLD guard tripped")
            break
    final = state_fold.measure(os.path.getsize(STATE), GATE)
    print("FINAL bytes=%d margin=%d fold_needed=%s verdict=%s"
          % (final["bytes"], final["margin"], final["fold_needed"],
             final["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())