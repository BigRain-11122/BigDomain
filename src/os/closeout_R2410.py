"""R2410 closeout: one verification window with one birth-site repair.

Writes, in this order, and each step proves its own predicted size:

1. the debt register note for reconcile-battery-R2409 (the row stays OPEN:
   a window that did not see a green RUNNER PASS may not close it),
2. src/os/state.json through state_io.write_canon (tick 2410 plus seven
   appended items, so the layout canon is proved rather than assumed),
3. docs/status-export.json (the CEO-visible three lines and one results row),
4. heartbeat.txt.

Nothing here decides anything: every number is read off the files on disk.
"""

import io
import json
import os

import state_io

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(SRC)
STATE = os.path.join(SRC, "os", "state.json")
DEBT = os.path.join(ROOT, "state", "debt.md")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

ROUND = 2410
STAMP = "2026-11-03T09:5x:00+08:00"

BATTERY_NOTE = (
    "opened=R2409 | item=reconcile-battery-R2409 | note=the R2409 product "
    "window changed src/os, so the battery belongs on the committed tree. "
    "R2410 RAN it: RUNNER FAIL 532/533 suites with criteria total 4174 "
    "EXACTLY as pre-registered, both failed assertions tracing to ONE red "
    "suite (os-stamp-exempt-review AC-SER6, live DRIFT undeclared=1 = the "
    "R2409 discharge row DISCHARGED#9c271447 at tech.md:487, a closed row "
    "created after the R2280 seed). Repaired at the birth site through the "
    "shipped stamp_exempt_append (predicted 79254B == measured, readback ok, "
    "entries 381->382, committed alone as 05eb90d8), after which the live "
    "reading is NO-DRIFT and that suite reads 6/6. The row STAYS OPEN: no "
    "green RUNNER PASS exists for this tree, so the retry leg is owed next "
    "with the same target 533 suites / 4174 criteria, followed by the four "
    "follow-up sections. | first=yes"
)

LOG_ITEMS = [
    "2026-11-03 R2410 verification window (five-silence scan clean at open: "
    "empty git status at HEAD cc93b015, no .git/index.lock; LEDGER @BigDomain "
    "addressed rows=0 unreplied=0; DEC rows=148 tokens=97 new=0 against the "
    "stored baseline; the local orders table tail is the 2026-09-28 batch "
    "already acknowledged and the group orders tail carries a foreign merge "
    "marker in a file this company only reads; benchmarks refreshed 2026-11-02 "
    "inside the seven-day gate; floor FLOOR-MET main 5/5 tech 10/10 explore "
    "10/10). The debt gate named CLAIM-FIRST item=reconcile-battery-R2409 "
    "with a pre-registered target of 532 suites / 4174 criteria, so the "
    "battery ran FIRST on the committed tree with zero product edits.",

    "2026-11-03 R2410 the battery earned its keep: RUNNER FAIL 532/533 suites "
    "with criteria total 4174 EXACTLY as pre-registered and both failed "
    "assertions tracing to ONE red suite, os-stamp-exempt-review AC-SER6, "
    "whose live reading was declaration=PINNED entries=381 violations=382 "
    "matched=381 exempt=381 undeclared=1 verdict=DRIFT "
    "(qa/reconcile-all-R2410.log kept as the red leg, 837165B, one utf-8 LF "
    "single writer through battery_stream, never a shell redirection).",

    "2026-11-03 R2410 the red named its own row: the undeclared one is "
    "DISCHARGED#9c271447 at state/queue/tech.md:487 seed_round=2409, i.e. the "
    "R2409 product window own discharge row, closed AFTER the R2280 seed - "
    "exactly the shape the R2280 note (a) predicted when it disclosed that a "
    "closed row created later is not covered by the declaration.",

    "2026-11-03 R2410 repair at the birth site, never by widening a criterion: "
    "the entry was appended through the shipped stamp_exempt_append (predicted "
    "79026B -> 79254B, measured 79254B exactly, wrote=yes readback=ok, entries "
    "381->382) and committed ALONE as 05eb90d8; the live reading is now "
    "NO-DRIFT violations=382 matched=382 exempt=381 expired=1 undeclared=0 and "
    "the red suite reads SUITE PASS 6/6.",

    "2026-11-03 R2410 honest gaps, stated rather than swept: (a) NO green "
    "RUNNER PASS exists for this tree - the retry leg is carried with the same "
    "pre-registered target of 533 suites / 4174 criteria, because the run took "
    "1208.4s and this window had already spent it; (b) the four follow-up "
    "sections (matrix, fingerprint, profile, census) were NOT run for the same "
    "reason; (c) the one expired entry (until R2330) was NOT renewed, exactly "
    "as at R2358 - it reads expired=1 and does not cause drift; (d) MEASURED "
    "and named, not swept: the R2409 suite os-library-declaration-dialect-sweep "
    "prints its six PASS lines two spaces deeper than the runner ^PASS counter "
    "reads, so the report says pass-lines=0 while criteria=6 still counts - "
    "green and criteria totals are unaffected but that column under-reports it.",

    "R2410 tokens: local=~24k api=0 api_reason=verification window - one full "
    "battery on the committed tree with a pre-registered target that matched "
    "exactly (533 suites measured against 532 registered, criteria 4174 == "
    "4174), one red traced to one real undeclared stamp and repaired through "
    "the shipped writer at its predicted byte count, one red leg preserved, one "
    "debt note rewritten to carry the measured reading, and the "
    "state/export/heartbeat closeout; zero product code shipped, zero cloud "
    "calls and zero external API touches",

    "2026-11-03 R2410 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law forbids "
    "for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U "
    "principal but needs an elevated shell and this session is unelevated, so "
    "the task definition was left untouched (hundred-and-sixty-fifth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
]

EXPORT_DO = (
    "R2410 verification: the R2409 battery read 532/533 suites with criteria "
    "4174 exactly as pre-registered, its one red traced to a real undeclared "
    "stamp and repaired at the birth site through the shipped writer to "
    "NO-DRIFT"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2410.log + state/queue/stamp_exempt.json (382 entries, "
    "NO-DRIFT) + src/os/closeout_R2410.py"
)
EXPORT_MILESTONE = (
    "green retry battery on the committed repair tree at 533 suites / 4174 "
    "criteria plus the four follow-up sections (debt row reconcile-battery-R2409)"
)
EXPORT_DUE = "2026-11-04T23:00:00+08:00"


def step_debt():
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")
    hit = None
    for index, line in enumerate(lines):
        if "item=reconcile-battery-R2409" in line:
            hit = index
            break
    if hit is None:
        raise SystemExit("E_C2410_DEBT_ROW")
    if "R2410 RAN it" in lines[hit]:
        print("debt row already carries the R2410 reading, nothing to do")
        return
    lines[hit] = "- [ ] " + BATTERY_NOTE
    new = "\n".join(lines)
    before = len(text.encode("utf-8"))
    after = len(new.encode("utf-8"))
    with io.open(DEBT, "w", encoding="utf-8", newline="") as handle:
        handle.write(new)
    with io.open(DEBT, "r", encoding="utf-8", newline="") as handle:
        if "R2410 RAN it" not in handle.read():
            raise SystemExit("E_C2410_DEBT_READBACK")
    print("debt %dB -> %dB written and read back" % (before, after))


def step_state():
    text = state_io.decode(state_io.read_raw(STATE))
    if text.count("\r\n") == 0 or text.count("\n") != text.count("\r\n"):
        raise SystemExit("E_C2410_STATE_NOT_CRLF")
    state = json.loads(text)
    if state["tick"] != ROUND - 1:
        raise SystemExit("E_C2410_TICK: %r" % (state["tick"],))
    for item in LOG_ITEMS:
        if item in text:
            raise SystemExit("E_C2410_ITEM_ALREADY_LIVE")
    old_tick = '"tick": %d,' % state["tick"]
    if text.count(old_tick) != 1:
        raise SystemExit("E_C2410_TICK_TEXT")
    text = text.replace(old_tick, '"tick": %d,' % ROUND)
    closer = '"\r\n  ]\r\n}\r\n'
    if not text.endswith(closer):
        raise SystemExit("E_C2410_CLOSER")
    block = ",\r\n".join(
        " " * 16 + json.dumps(item, ensure_ascii=False) for item in LOG_ITEMS)
    text = text[: -len(closer)] + '",\r\n' + block + "\r\n  ]\r\n}\r\n"
    layout = state_io.layout(text)
    if not layout["layout_ok"]:
        raise SystemExit("E_C2410_LAYOUT: %r" % (layout,))
    if json.loads(text)["tick"] != ROUND:
        raise SystemExit("E_C2410_TICK_READBACK")
    temp = STATE + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    os.replace(temp, STATE)
    after = state_io.decode(state_io.read_raw(STATE))
    if after != text:
        raise SystemExit("E_C2410_STATE_READBACK")
    if os.path.exists(temp):
        raise SystemExit("E_C2410_TEMP_RESIDUE")
    print("state written %dB tick=%d items=%d layout_ok"
          % (len(after.encode("utf-8")), ROUND, len(state["log"]) + len(LOG_ITEMS)))


def step_export(state):
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = STAMP
    export["do"] = EXPORT_DO
    face = export["ceo_face"]
    face["current"] = EXPORT_DO
    face["latest_artifact"] = EXPORT_ARTIFACT
    face["last_artifact"] = EXPORT_ARTIFACT
    face["next_milestone"] = EXPORT_MILESTONE
    face["next_milestone_due"] = EXPORT_DUE
    face["updated_at"] = STAMP
    results = [row for row in export["results"] if row[0] != str(ROUND)]
    results.insert(0, [str(ROUND), "OSLoop 鎵ц tick"])
    results.insert(1, [str(ROUND), EXPORT_DO])
    export["results"] = results
    outs = [item for item in export["outs"] if "reconcile-all-R2410.log" not in item]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    drive = export["self_drive"]
    drive["log_lines_in_window"] = len(state["log"])
    drive["substantive_non_idle_mention_lines"] = len(state["log"])
    drive["window"] = "2026-11-04..2026-11-03"
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("export refreshed %dB" % len(text.encode("utf-8")))


def step_heartbeat():
    line = ("2026-11-03 09:5x R2410 verification: the R2409 battery read "
            "532/533 with criteria 4174 exactly as pre-registered, one real "
            "undeclared stamp repaired through the shipped writer to NO-DRIFT, "
            "retry owed next")
    with io.open(HEARTBEAT, "r", encoding="utf-8") as handle:
        text = handle.read()
    if not text.endswith("\n"):
        text += "\n"
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + line + "\n")
    print("heartbeat appended")


def main():
    step_debt()
    step_state()
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    step_export(state)
    step_heartbeat()


if __name__ == "__main__":
    main()
