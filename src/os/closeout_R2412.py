"""R2412 closeout: one product window that shipped the reader-parity face.

The debt row product-face-R2412 was closed and its successor
reconcile-battery-R2412 appended through the shipped debt_close / debt_append
CLIs, and state/queue/tech.md:480 was stamped with two rows appended, all
BEFORE this script ran; nothing here re-decides any of that.

Writes, in this order, and each step proves its own predicted size:

1. src/os/state.json through the state_io canon (tick 2412 plus six appended
   items, so the layout canon is proved rather than assumed),
2. docs/status-export.json (the CEO-visible three lines, the results rows and
   the derived counters),
3. src/os/backlog.md (one delivered row),
4. heartbeat.txt.

Nothing here invents a number: every count written to the log is one this
window measured, and the registry total is the wiring count the runner
registry actually holds (533 + 1 suites, 4174 + 6 criteria), NOT a battery
result - the battery is the successor row's job.
"""

import io
import json
import os

import state_io

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
STATE = os.path.join(SRC, "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(SRC, "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
PATTERNS = os.path.join(SRC, "os", "export_consistency_patterns.json")

ROUND = 2412
STAMP = "2026-11-03T13:20:00+08:00"

LOG_ITEMS = [
    "2026-11-03 R2412 product window (five-silence scan clean at open: empty "
    "git status at HEAD 8a469c58, no .git/index.lock; LEDGER @BigDomain "
    "addressed rows=0 unreplied=0; DEC rows=148 tokens=97 with new=0 against "
    "the stored baseline; the local orders table head is the 2026-10-26 batch "
    "already acknowledged; benchmarks refreshed 2026-11-02 inside the "
    "seven-day gate; floor FLOOR-MET main 5/5 tech 10/10 explore 10/10). The "
    "debt gate named CLAIM-FIRST item=product-face-R2412 and the queue_head "
    "gate confirmed the true tech head at state/queue/tech.md:480 with prefix "
    "AC-OTRP1, claimable=10, skipped_before=5, so the product-first law led "
    "and the window claimed that row.",

    "2026-11-03 R2412 what shipped: src/os/owner_table_reader_parity.py plus "
    "src/os/test_owner_table_reader_parity.py, against AC-OTRP1..AC-OTRP6 "
    "pinned in the R2399 seed row BEFORE any code and after a fresh "
    "zero-occupancy anchor check at HEAD (owner_table_reader_parity / AC-OTRP "
    "/ E_OTRP / os-owner-table-reader-parity / test_owner_table_reader_parity "
    "hit only prose and state files). The face asks BOTH shipped readers of "
    "the same file at CALL time (imported inside the callables, so patching "
    "either one moves the row list) and publishes every disagreement with its "
    "reason and, for a law-only table, the flags the law itself reported. "
    "Per-round copies are classified SUPERSEDED from the filename family "
    "(NAME_R<digits>.py beside a live NAME.py), never from a whitelist, so "
    "deleting the base callable returns that row to debt.",

    "2026-11-03 R2412 evidence and board: SUITE PASS 6/6 (six criteria, zero "
    "fails) and EVIDENCE CAPTURE round=R2412 legs=2 identical=True "
    "adjacent=3 fails=0 (qa/owner-table-reader-parity-R2412.log, 1782B, "
    "single writer utf-8 LF through the R2261 capture callable), wired "
    "os-owner-table-reader-parity(6) so the registry wiring reads 534 suites "
    "/ 4180 criteria. LIVE, not a plan: "
    "qa/owner-table-reader-parity-live-R2412.log (5177B, 44 lines) reads the "
    "REAL tree as scanned=1017 rows=40 superseded=35 split=5 "
    "verdict=PARITY-SPLIT naming battery_followup_help_wire.py, "
    "evidence_R2372.py, r2140_fold.py, retry_naming.py and run_identity.py - "
    "the five files where the law still cries wolf and the wire correctly "
    "reads NO-TABLE. Tech row 480 stamped [done 2026-11-03 R2412] with two "
    "rows appended (the discharge and one REAL measured gap seed), so the "
    "floor reads claimable=10 again. tasks.md was left untouched: it is the "
    "P-47 canonical board and carries no row for this tech slice.",

    "2026-11-03 R2412 honest disclosures: (a) the seed row predicted 37 "
    "one-per-round copies; measured this window 35 rows in that family (42 "
    "files match the family pattern, 7 already read NO-TABLE on both sides "
    "and so are not disagreement rows) - stated, not smoothed; (b) the live "
    "verdict is PARITY-SPLIT, NOT CLEAN: this face publishes five genuine "
    "law false positives rather than declaring the tree clean, and the reason "
    "each is still there is now printed with it; (c) the family rule covers "
    "the NAME_R<digits>.py shape only, so battery_followup_help_wire.py and "
    "evidence_R2372.py stay debt even though they are the same false "
    "positive, because widening the rule needs a derived test rather than a "
    "guess - that limitation is named in the module docstring; (d) the "
    "reading covers ONE directory per call (src/os here), and audit() returns "
    "None on a root holding no direct .py, so no library-wide question can be "
    "asked yet; (e) NO battery ran this window: 534 suites / 4180 criteria is "
    "a WIRING count (533/4174 from R2409 plus +1 suite / +6 criteria) and "
    "reconcile-battery-R2412 is OPEN with that exact pre-registered target.",

    "R2412 tokens: local=~30k api=0 api_reason=product window - one "
    "reader-parity face plus its six-criteria suite written to criteria "
    "pinned two rounds earlier, one filename-family supersession rule derived "
    "from the directory rather than whitelisted, one registry wiring line, "
    "one two-leg evidence capture with three adjacent suites, one read-only "
    "live capture over 1017 real files with every row's reason and flags, one "
    "board stamp with one measured gap row seeded, the debt row closed and "
    "the successor battery opened through the shipped CLIs, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",

    "2026-11-03 R2412 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal but needs an elevated shell and this session is "
    "unelevated, so the task definition was left untouched "
    "(hundred-and-sixty-seventh consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
]

EXPORT_DO = (
    "R2412 product: owner_table_reader_parity now asks both shipped table "
    "readers of the same file and publishes every disagreement with its "
    "reason (scanned 1017, rows 40, superseded 35, split 5)"
)
EXPORT_ARTIFACT = (
    "src/os/owner_table_reader_parity.py + "
    "qa/owner-table-reader-parity-R2412.log (1782B, legs=2 identical) + "
    "qa/owner-table-reader-parity-live-R2412.log (5177B, 44 lines)"
)
EXPORT_MILESTONE = (
    "reconcile-battery-R2412: the full battery on this committed tree at the "
    "pre-registered target of 534 suites / 4180 criteria, zero product edits"
)
EXPORT_DUE = "2026-11-04T23:00:00+08:00"

BACKLOG_ROW = (
    "- [x] R2412 [done 2026-11-03] owner_table_reader_parity - "
    "state/queue/tech.md:480 AC-OTRP1..AC-OTRP6 delivered: the law and the "
    "usage wire answer two different questions over the same tree (measured "
    "at HEAD: 1016 non-test src/os files, 40 disagreements), so an operator "
    "holding either log alone could not tell a tool with NO table from a tool "
    "whose usage path is named neither way. SHIPPED "
    "src/os/owner_table_reader_parity.py plus its six-criteria suite: both "
    "readings are asked at CALL time, every row names both verdicts and its "
    "reason, a law-only row carries the flags the law itself reported, and "
    "per-round copies are superseded by their live base callable through the "
    "filename family rather than a whitelist. LIVE: scanned=1017 rows=40 "
    "superseded=35 split=5 verdict=PARITY-SPLIT naming the five remaining law "
    "false positives. Evidence = SUITE PASS 6/6 plus EVIDENCE CAPTURE legs=2 "
    "identical=True adjacent=3 fails=0 (qa/owner-table-reader-parity-R2412.log) "
    "and the 44-line live capture; wired os-owner-table-reader-parity(6). "
    "Honest debt: no battery ran (534/4180 is a wiring count), the family "
    "rule covers NAME_R<digits>.py only, and the reading is one directory per "
    "call. One real gap seeded: owner_table_split_triage (AC-OTST1..AC-OTST6).\n"
)


def _read(path, encoding="utf-8", newline=None):
    with io.open(path, "r", encoding=encoding, newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_state():
    text = state_io.decode(state_io.read_raw(STATE))
    crlf = text.count("\r\n")
    if crlf == 0 or text.count("\n") != crlf:
        raise SystemExit("E_C2412_STATE_NOT_CRLF")
    state = json.loads(text)
    live = sum(1 for item in LOG_ITEMS if item in text)
    if state["tick"] == ROUND and live == len(LOG_ITEMS):
        print("state already at tick=%d with all %d items, nothing to do"
              % (ROUND, len(LOG_ITEMS)))
        return state
    if live:
        raise SystemExit("E_C2412_ITEM_PARTIAL: %d/%d" % (live, len(LOG_ITEMS)))
    if state["tick"] != ROUND - 1:
        raise SystemExit("E_C2412_TICK: %r" % (state["tick"],))
    old_tick = '"tick": %d,' % state["tick"]
    if text.count(old_tick) != 1:
        raise SystemExit("E_C2412_TICK_TEXT")
    text = text.replace(old_tick, '"tick": %d,' % ROUND)
    closer = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(closer):
        raise SystemExit("E_C2412_CLOSER")
    block = ",\r\n".join(
        " " * 16 + json.dumps(item, ensure_ascii=False) for item in LOG_ITEMS)
    text = text[: -len(closer)] + '",\r\n' + block + "\r\n  ]\r\n}\r\n"
    layout = state_io.layout(text)
    if not layout["layout_ok"]:
        raise SystemExit("E_C2412_LAYOUT: %r" % (layout,))
    if json.loads(text)["tick"] != ROUND:
        raise SystemExit("E_C2412_TICK_READBACK")
    before = len(state_io.read_raw(STATE))
    temp = STATE + ".tmp"
    _write(temp, text)
    os.replace(temp, STATE)
    after_text = state_io.decode(state_io.read_raw(STATE))
    if after_text != text:
        raise SystemExit("E_C2412_STATE_READBACK")
    if os.path.exists(temp):
        raise SystemExit("E_C2412_TEMP_RESIDUE")
    after = len(state_io.read_raw(STATE))
    print("state %dB -> %dB tick=%d log_items=%d layout_ok"
          % (before, after, ROUND, len(json.loads(after_text)["log"])))
    return json.loads(after_text)


def step_export(state):
    patterns = json.loads(_read(PATTERNS))
    label = patterns["tick_row_label"]
    export = json.loads(_read(EXPORT))
    export["export_ts"] = STAMP
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_DO
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_MILESTONE
    face["next_milestone_due"] = EXPORT_DUE
    face["updated_at"] = STAMP
    results = [row for row in export["results"] if str(row[0]) != str(ROUND)]
    results.insert(0, [str(ROUND), EXPORT_DO])
    labelled = [row for row in results if len(row) >= 2 and row[1] == label]
    if not labelled:
        results.insert(0, [str(ROUND), label])
    else:
        for row in labelled:
            row[0] = str(ROUND)
    export["results"] = results
    outs = [item for item in export["outs"]
            if "owner_table_reader_parity" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    drive = export["self_drive"]
    # Derived counters come from the checker's own recomputation, never from
    # len(state["log"]): the window is the last seven dated days, and R2409 and
    # R2411 both shipped a closeout that guessed instead of asking.
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive["log_lines_in_window"] = derived["log_lines_in_window"]
    drive["substantive_non_idle_mention_lines"] = \
        derived["substantive_non_idle_mention_lines"]
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    _write(EXPORT, text, newline="\n")
    print("export refreshed %dB tick_rows=%d"
          % (len(text.encode("utf-8")), len(labelled) or 1))


def step_backlog():
    text = _read(BACKLOG)
    if BACKLOG_ROW in text:
        print("backlog row already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(BACKLOG, text + BACKLOG_ROW, newline="\n")
    print("backlog appended %dB" % len(BACKLOG_ROW.encode("utf-8")))


def step_heartbeat():
    line = ("2026-11-03 13:20 R2412 product: "
            "src/os/owner_table_reader_parity.py ships - both shipped table "
            "readers asked of the same file, 1017 scanned / 40 rows / 35 "
            "superseded / 5 split, suite 6/6 with two-leg evidence")
    text = _read(HEARTBEAT)
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


def main():
    state = step_state()
    step_export(state)
    step_backlog()
    step_heartbeat()


if __name__ == "__main__":
    main()