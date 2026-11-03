"""R2413 closeout: a verification window that turned into one birth-site repair.

Nothing here re-decides the battery: the run, the single red and the repair are
this window's measurements and are written down as measured.

Writes, in this order, each step proving its own predicted size:

1. state/debt.md (note_appended_R2413 on the OPEN reconcile-battery-R2412 row,
   so the red and its repair are carried in the register itself),
2. src/os/state.json through the layout law (tick 2413 plus six items),
3. docs/status-export.json (the CEO-visible three lines and derived counters),
4. src/os/backlog.md (one delivered row),
5. heartbeat.txt.

No number here is invented: 534 suites / 4180 criteria is the MEASURED battery
total (it equals the pre-registered target, so there is no delta to name), and
the repair's byte counts are the ones the shipped writer printed.
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
DEBT = os.path.join(ROOT, "state", "debt.md")

ROUND = 2413
STAMP = "2026-11-03T10:35:00+08:00"

NOTE_ANCHOR = (
    "Two carried gaps stay open and are named rather than re-carried "
    "silently: the os-library-declaration-dialect-sweep suite still prints "
    "its six PASS lines two spaces deeper than the runner PASS counter "
    "(criteria still counted, column under-reports), and the expired "
    "stamp-exemption entry until R2330 is still un-renewed and causes no "
    "drift."
)

NOTE_APPEND = (
    " ; note_appended_R2413: the battery RAN on this committed tree with zero "
    "product edits and read RUNNER FAIL over 534 of 534 suite lines with "
    "criteria total 4180 EXACTLY as pre-registered (no delta to explain) and "
    "ONE red, os-stamp-exempt-review AC-SER6, whose live reading was "
    "entries=382 violations=383 matched=382 undeclared=1 verdict=DRIFT. The "
    "red named its own row: state/queue/tech.md:489 "
    "tech:DISCHARGED#f1bd5eac seed=2412, the R2412 discharge row closed after "
    "the R2280 seed - the same shape R2410 repaired once already. Repaired at "
    "the BIRTH SITE through the shipped stamp_exempt_append (predicted "
    "79254B -> 79445B, measured 79445B exactly, entries 382 -> 383, "
    "wrote=yes readback=ok) after which the live reading is NO-DRIFT "
    "undeclared=0. The row therefore STAYS OPEN: no green RUNNER PASS exists "
    "for this tree, the retry leg is owed next with the SAME target of 534 "
    "suites / 4180 criteria because a declaration repair adds no suite and no "
    "criterion, and the four follow-up sections have still not run."
)

LOG_ITEMS = [
    "2026-11-03 R2413 verification window (five-silence scan clean at open: "
    "empty git status at HEAD 2ff8b3b6, no .git/index.lock; LEDGER @BigDomain "
    "addressed rows=0 unreplied=0; DEC rows=148 tokens=97 with new=0 against "
    "the stored baseline; ORD max_ts=2026-11-02 with no dispatching row for "
    "this company; benchmarks refreshed 2026-11-02 inside the seven-day "
    "gate). The debt gate named CLAIM-FIRST item=reconcile-battery-R2412 "
    "with the pre-registered target of 534 suites / 4180 criteria, so the "
    "battery ran FIRST on the committed tree with zero product edits.",

    "2026-11-03 R2413 the run itself, disclosed rather than tidied: the first "
    "invocation was piped through a truncating selector, produced no output "
    "for five minutes, was cancelled by the shell tool's no-output rule and "
    "left NO evidence file and NO surviving process (verified by command "
    "line before relaunching). The battery was then launched detached with "
    "stdout to a scratch file outside qa/ so progress could be polled, while "
    "the evidence itself was written only by src/os/battery_stream.py - the "
    "R2211 trap re-proven, this time with the survivor check run before the "
    "rerun.",

    "2026-11-03 R2413 the battery measured: RUNNER FAIL with 534 suite lines "
    "and criteria total 4180 EXACTLY the pre-registered target, one red suite "
    "os-stamp-exempt-review whose AC-SER6 read declaration=PINNED entries=382 "
    "violations=383 matched=382 exempt=381 expired=1 missing=0 undeclared=1 "
    "verdict=DRIFT (918.7s, evidence qa/reconcile-all-R2413.log kept as the "
    "red leg, 837944B). The red named its own row: state/queue/tech.md:489 "
    "tech:DISCHARGED#f1bd5eac seed=2412, i.e. the R2412 window's own discharge "
    "row, closed AFTER the R2280 seed - exactly the shape the R2280 note (a) "
    "predicted and R2410 repaired once.",

    "2026-11-03 R2413 repair at the birth site, never by widening a "
    "criterion: the entry was appended through the shipped "
    "stamp_exempt_append (predicted 79254B -> 79445B, measured 79445B "
    "exactly, entries 382 -> 383, wrote=yes readback=ok) and the live reading "
    "is now NO-DRIFT violations=383 matched=383 exempt=382 expired=1 "
    "undeclared=0.",

    "2026-11-03 R2413 honest gaps, stated rather than swept: (a) NO green "
    "RUNNER PASS exists for this tree, so reconcile-battery-R2412 stays OPEN "
    "with the SAME target of 534 suites / 4180 criteria - a declaration "
    "repair adds no suite and no criterion - and the retry leg is owed next; "
    "(b) the four follow-up sections (matrix, fingerprint, profile, census) "
    "were NOT run, because they follow a green leg; (c) the expired "
    "stamp-exemption entry (until R2330) was NOT renewed, exactly as at "
    "R2358, R2410 and R2411 - it reads expired=1 and causes no drift; (d) "
    "MEASURED and named, not swept: the R2409 suite "
    "os-library-declaration-dialect-sweep still prints its six PASS lines two "
    "spaces deeper than the runner PASS counter, so that column under-reports "
    "it while criteria=6 still counts - unchanged and still unfixed.",

    "R2413 tokens: local=~18k api=0 api_reason=verification window - one full "
    "battery on the committed tree at a pre-registered target that matched "
    "exactly (534 suites / 4180 criteria), one red traced to one real "
    "undeclared stamp and repaired through the shipped writer at its "
    "predicted byte count with a read-back, one red leg preserved, one "
    "register note appended so the debt row carries the measurement, and the "
    "state/export/backlog/heartbeat closeout; zero product code shipped, "
    "zero cloud calls and zero external API touches",

    "2026-11-03 R2413 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal but needs an elevated shell and this session is "
    "unelevated, so the task definition was left untouched "
    "(hundred-and-sixty-eighth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
]

EXPORT_DO = (
    "R2413 verification: full battery on the committed tree read 534/534 "
    "suite lines at the pre-registered 4180 criteria; the one red "
    "(undeclared R2412 discharge stamp) repaired through the shipped writer "
    "at its predicted bytes, live NO-DRIFT"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2413.log (837944B, red leg) + "
    "state/queue/stamp_exempt.json (383 entries, 79445B, live NO-DRIFT)"
)
EXPORT_MILESTONE = (
    "reconcile-battery-R2412 retry: one green RUNNER PASS over the same 534 "
    "suites / 4180 criteria on the repaired committed tree, then the four "
    "follow-up sections"
)
EXPORT_DUE = "2026-11-04T23:00:00+08:00"

BACKLOG_ROW = (
    "- [x] [done 2026-11-03 R2413] verification window: the debt gate named "
    "CLAIM-FIRST item=reconcile-battery-R2412 with a pre-registered target of "
    "534 suites / 4180 criteria, so the battery ran FIRST on the committed "
    "2ff8b3b6 tree with zero product edits - RUNNER FAIL with 534 suite lines "
    "and criteria total 4180 EXACTLY as pre-registered, one red suite "
    "os-stamp-exempt-review (AC-SER6: entries=382 violations=383 "
    "matched=382 undeclared=1 verdict=DRIFT) naming state/queue/tech.md:489 "
    "tech:DISCHARGED#f1bd5eac seed=2412, the R2412 window own discharge row. "
    "Repaired at the BIRTH SITE through the shipped stamp_exempt_append "
    "(predicted 79254B -> 79445B, measured exactly, entries 382 -> 383, "
    "wrote=yes readback=ok), after which the live reading is NO-DRIFT "
    "undeclared=0. The red leg is kept as qa/reconcile-all-R2413.log "
    "(837944B). Honest gaps: NO green RUNNER PASS exists for this tree, so "
    "reconcile-battery-R2412 stays OPEN with the same target (a declaration "
    "repair adds no suite), the four follow-up sections were not run because "
    "they follow a green leg, and the expired stamp entry (until R2330) was "
    "not renewed and causes no drift. Zero product code shipped, honestly "
    "scored 0 product points.\n"
)


def _read(path, encoding="utf-8", newline=None):
    with io.open(path, "r", encoding=encoding, newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_debt():
    text = _read(DEBT, newline="")
    if "note_appended_R2413" in text:
        print("debt note already present")
        return
    if text.count(NOTE_ANCHOR) != 1:
        raise SystemExit("E_C2413_DEBT_ANCHOR: %d" % text.count(NOTE_ANCHOR))
    before = len(text.encode("utf-8"))
    text = text.replace(NOTE_ANCHOR, NOTE_ANCHOR + NOTE_APPEND)
    after = len(text.encode("utf-8"))
    _write(DEBT, text, newline="")
    back = _read(DEBT, newline="")
    if "note_appended_R2413" not in back:
        raise SystemExit("E_C2413_DEBT_READBACK")
    print("debt %dB -> %dB note_appended_R2413" % (before, after))


def step_state():
    text = state_io.decode(state_io.read_raw(STATE))
    crlf = text.count("\r\n")
    if crlf == 0 or text.count("\n") != crlf:
        raise SystemExit("E_C2413_STATE_NOT_CRLF")
    state = json.loads(text)
    live = sum(1 for item in LOG_ITEMS if item in text)
    if state["tick"] == ROUND and live == len(LOG_ITEMS):
        print("state already at tick=%d with all %d items, nothing to do"
              % (ROUND, len(LOG_ITEMS)))
        return state
    if live:
        raise SystemExit("E_C2413_ITEM_PARTIAL: %d/%d" % (live, len(LOG_ITEMS)))
    if state["tick"] != ROUND - 1:
        raise SystemExit("E_C2413_TICK: %r" % (state["tick"],))
    old_tick = '"tick": %d,' % state["tick"]
    if text.count(old_tick) != 1:
        raise SystemExit("E_C2413_TICK_TEXT")
    text = text.replace(old_tick, '"tick": %d,' % ROUND)
    closer = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(closer):
        raise SystemExit("E_C2413_CLOSER")
    block = ",\r\n".join(
        " " * 16 + json.dumps(item, ensure_ascii=False) for item in LOG_ITEMS)
    text = text[: -len(closer)] + '",\r\n' + block + "\r\n  ]\r\n}\r\n"
    layout = state_io.layout(text)
    if not layout["layout_ok"]:
        raise SystemExit("E_C2413_LAYOUT: %r" % (layout,))
    if json.loads(text)["tick"] != ROUND:
        raise SystemExit("E_C2413_TICK_READBACK")
    before = len(state_io.read_raw(STATE))
    temp = STATE + ".tmp"
    _write(temp, text)
    os.replace(temp, STATE)
    after_text = state_io.decode(state_io.read_raw(STATE))
    if after_text != text:
        raise SystemExit("E_C2413_STATE_READBACK")
    if os.path.exists(temp):
        raise SystemExit("E_C2413_TEMP_RESIDUE")
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
            if "reconcile-all-R2413" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    drive = export["self_drive"]
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
    line = ("2026-11-03 10:35 R2413 verification: battery on the committed "
            "tree read 534/534 suite lines at the pre-registered 4180 "
            "criteria; the one red (undeclared R2412 discharge stamp) "
            "repaired through stamp_exempt_append at 79445B predicted == "
            "measured, live NO-DRIFT 383 entries")
    text = _read(HEARTBEAT)
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


def main():
    step_debt()
    state = step_state()
    step_export(state)
    step_backlog()
    step_heartbeat()


if __name__ == "__main__":
    main()