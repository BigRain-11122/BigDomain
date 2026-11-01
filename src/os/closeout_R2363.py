"""closeout_R2363 - the round ledger for the re-pin writer window.

Closes the tech row that shipped, seeds its measured successor, bumps the tick,
appends the log lines this window owes, prepends the backlog row, appends the
heartbeat line and refreshes the CEO face of docs/status-export.json.

Dry run by default; --execute writes utf-8 with LF and reads every file back.
"""

import io
import json
import os
import sys
import tempfile
from datetime import datetime

import state_io

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

TICK = 2363
STAMP = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

TECH_HEAD = ("- [ ] P2 tech seed (R2353, from this window own measured pain): "
             "`src/os/residue_triage_repin.py`")

TECH_CLOSE = (
    " [done 2026-11-02 R2363] DELIVERED as the R2363 product window: the "
    "declaration finally has a general re-pin writer, the act that was done by "
    "a round script with the round and the until window as constants. "
    "`residue_triage_repin` takes the entry set, the status tuple and the judge "
    "from residue_triage (the suite patches its loader and its live reading and "
    "both move the plan; the module carries no second declaration reader and no "
    "status tuple), plans by number (round, until, entries before/after, every "
    "measured status with its count, dropped rounds, predicted bytes), writes "
    "nothing without --execute, refuses E_RTRP_DISAGREES when a declared status "
    "has moved, refuses E_RTRP_UNMATCHED rather than retiring a round this "
    "writer does not own, and the executed write is ONE os.replace that proves "
    "its predicted size and re-reads TRIAGED. SUITE PASS 6/6 twice with an "
    "identical criterion digest (qa/residue-triage-repin-R2363.log, 918B, "
    "legs=2 identical=True) plus three adjacent residue suites green, wired "
    "os-residue-triage-repin(6). LIVE ACTION: the real declaration was "
    "re-pinned at R2363 from one live reading - 211 entries (DELIVERED 191 / "
    "STAMP-ONLY-OPEN 20), 63026B -> 62266B exactly as predicted, no temp "
    "residue, and residue_triage now reads TRIAGED 211/211 at exit 0 "
    "(qa/residue-triage-repin-live-R2363.log).")


def render_seed():
    return (
        "- [ ] P2 tech seed (R2363, from this window own live measurement): "
        "`src/os/residue_triage_repin_idempotent` - the re-pin has no NOOP: "
        "measured immediately after this window own live write, a second plan "
        "composes bytes identical to the file on disk (predicted 62266 == "
        "on_disk 62266) and still reads PLANNED, and --execute would rewrite "
        "those same 62266 bytes and report PINNED, so a caller cannot tell "
        "\"nothing to do\" from \"I changed the declaration\" and every "
        "ledger-style reader sees a write where there was none. Product: the "
        "re-pin reads NOOP when the composed document equals the on-disk "
        "bytes, writes nothing, and names the round it agreed with. Criteria "
        "AC-RTRI1..AC-RTRI6 pre-registered HERE BEFORE any code: AC-RTRI1 an "
        "already-pinned declaration reads NOOP with executed=False and the "
        "file digest unchanged; AC-RTRI2 the NOOP reading is decided by "
        "BYTES, not by the head round, so a declaration re-pinned at an older "
        "round with identical content still reads NOOP; AC-RTRI3 a one-byte "
        "drift in the composition reads PLANNED again rather than NOOP; "
        "AC-RTRI4 the CLI exit codes and the pinned --json key order are "
        "unchanged for every non-NOOP path, and NOOP is exit 0 with its own "
        "verdict value; AC-RTRI5 the single atomic write path is not doubled "
        "- the NOOP branch returns before any temp file is created; AC-RTRI6 "
        "pure ASCII, stdlib only, zero network, no clock, the composition and "
        "the writer still imported from residue_triage_repin rather than "
        "re-implemented. Five anchors zero-occupancy at HEAD 2026-11-02: "
        "residue_triage_repin_idempotent, AC-RTRI, E_RTRI, "
        "os-residue-triage-repin-idempotent, "
        "test_residue_triage_repin_idempotent.\n")


LIVE = (
    "2026-11-02 R2363 product window (five-silence scan at open: empty git "
    "status --short at 68cc69fc, no .git/index.lock; scan_five_still read "
    "LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=112 tokens=74 new=0, "
    "so no decision row was owed; the group orders tail still reads the "
    "2026-11-01 10:4x model-policy baseline already acknowledged as "
    "non-execution; benchmarks refreshed 2026-11-01, inside the seven-day "
    "gate). THE GATE NAMED THE CARRIED BATTERY AND THE PRODUCT LAW OUTRANKED "
    "IT: debt_gate read CLAIM-FIRST item=reconcile-battery-R2362 opened=R2361 "
    "carried=2, and the register row must stay open because a window that does "
    "not run the battery cannot close it - but the tree was clean, the battery "
    "it names had already been measured on the edited R2362 tree (491/491 "
    "suites, 3922 criteria, qa/reconcile-battery-R2362.log) and only the "
    "committed-tree formality remained, while the queue head carried a real "
    "product face. So this window took the product face and LEFT THE ROW OPEN "
    "with its target named. CLAIMED state/queue/tech.md:410 prefix AC-RTRP1 "
    "(residue_triage_repin), whose AC-RTRP1..AC-RTRP6 were pinned INSIDE that "
    "row at R2353 BEFORE any code, and the zero-occupancy anchor check was "
    "re-run at HEAD (residue_triage_repin / AC-RTRP / E_RTRP / "
    "os-residue-triage-repin / test_residue_triage_repin: only prose in "
    "backlog.md, closeout_R2353.py and state.json; zero executable occupancy). "
    "SHIPPED src/os/residue_triage_repin.py plus src/os/test_residue_triage_"
    "repin.py."
)

HOLE = (
    "R2363 the suite found a real hole in the first draft, and it was repaired "
    "in the module rather than by widening the criterion: residue_triage.judge "
    "reports EXPIRED AHEAD OF DISAGREES, so an entry whose until had passed AND "
    "whose live status had moved would have been re-pinned at the new status "
    "without ever being named - the exact laundering AC-RTRP3 forbids. The "
    "module now compares every declared status against the live reading BEFORE "
    "it asks judge, so E_RTRP_DISAGREES names both statuses and the re-pin "
    "round at any expiry; judge still supplies the UNMATCHED set. Measured on "
    "the live declaration: disagrees=0 before the write, so nothing was "
    "laundered this window."
)

LIVE_ACT = (
    "R2363 live action, not a plan: the real declaration was re-pinned at "
    "R2363 from ONE live reading - entries 211 -> 211, DELIVERED 191 / "
    "STAMP-ONLY-OPEN 20, 63026B -> 62266B exactly as predicted, no .tmp-rtrep "
    "residue, and residue_triage --check --round R2363 then read TRIAGED "
    "211/211 at exit 0 (qa/residue-triage-repin-live-R2363.log). This is the "
    "first executed use of the writer and it is what makes the writer's "
    "prediction a measurement rather than a claim."
)

SELF_HEAL = (
    "R2363 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition was left untouched. Open "
    "local-lane item for an elevated window (hundred-and-nineteenth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md)."
)

DECISION_GATE = (
    "R2363 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, and the evolution ledger carries no @BigDomain row, so "
    "nothing was executed, rejected or acknowledged this window and the "
    "baseline was left unchanged rather than widened without cause."
)

HONEST = (
    "R2363 honest disclosures: (a) the carried battery did NOT run and the "
    "register row reconcile-battery-R2362 stays OPEN with its measured target "
    "named (the registry it must walk is 491 suites / 3922 criteria, measured "
    "on the R2362 tree; the committed head adds nothing, so a run should read "
    "the same numbers and any larger delta must be named). (b) The first "
    "draft of the module would have laundered an expired-and-moved status; the "
    "suite's AC-RTRP3 caught it on the first run and the fix is in the module, "
    "with no criterion widened - the red run is disclosed here because the "
    "green run alone would hide the defect. (c) The suite then failed twice "
    "more on THIS WINDOW's own fixtures, not on the module: a synthetic "
    "declaration was built with round strings where residue_triage hands back "
    "ints, and a world was passed its tech rows in the declaration slot; both "
    "were corrected in the test. (d) The live re-pin shrinks the file 760B "
    "because the on-disk declaration carried expanded entry blocks from an "
    "earlier dumper while this writer renders one canonical layout - the entry "
    "set is identical (211/211, statuses counted) and the shrink is named "
    "rather than presented as a saving. (e) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice, "
    "disclosed rather than silently skipped."
)

TOKENS = (
    "R2363 tokens: local=~26k api=0 api_reason=product window - one product "
    "writer and its six-criteria suite written to criteria pinned two rounds "
    "earlier (three suite runs: one red on a real module hole, two red on this "
    "window own fixtures), one evidence capture with two identical legs and "
    "three adjacent suites, one LIVE executed re-pin of the real declaration "
    "with its read-back, one queue row closed and one measured gap row seeded, "
    "one runner wiring line, and the state/export/heartbeat/board closeout; "
    "zero cloud calls and zero external API touches"
)

ITEMS = [LIVE, HOLE, LIVE_ACT, TOKENS, SELF_HEAL, DECISION_GATE, HONEST]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2363] product-face-R2363: state/queue/tech.md:410 "
    "AC-RTRP1 residue_triage_repin - the declaration finally has a general "
    "re-pin writer. The debt gate named the carried battery "
    "(reconcile-battery-R2362, carried=2) and the product-first law outranked "
    "it: the row stays OPEN with its measured target named (491 suites / 3922 "
    "criteria), because a window that does not run a battery cannot close its "
    "row. Shipped src/os/residue_triage_repin.py + "
    "src/os/test_residue_triage_repin.py with AC-RTRP1..AC-RTRP6 pinned in that "
    "tech row at R2353 BEFORE the code and re-anchored at HEAD. The entry set, "
    "the status tuple and the judge are residue_triage own, the dry run is the "
    "default and writes no byte, a moved status refuses E_RTRP_DISAGREES, an "
    "unmatched round refuses E_RTRP_UNMATCHED unless the caller says to drop "
    "it, and the executed write is ONE os.replace that proves its predicted "
    "size and re-reads TRIAGED. The first draft was RED on AC-RTRP3 for a REAL "
    "reason - judge reports EXPIRED ahead of DISAGREES, so an expired entry "
    "with a moved status would have been laundered - and the module was fixed, "
    "not the criterion. SUITE PASS 6/6 twice identical (qa/residue-triage-"
    "repin-R2363.log, 918B, legs=2 identical=True) plus three adjacent suites "
    "green, wired os-residue-triage-repin(6). LIVE: the real declaration was "
    "re-pinned at R2363 (211 entries, DELIVERED 191 / STAMP-ONLY-OPEN 20, "
    "63026B -> 62266B exactly predicted, no temp residue) and reads TRIAGED "
    "211/211. Queue row closed, one measured gap row seeded "
    "(residue_triage_repin_idempotent, AC-RTRI1..AC-RTRI6: a second re-pin "
    "composes the identical 62266 bytes and still says PLANNED). Two product "
    "points."
)

EXPORT_DO = (
    "R2363 product window: the triage declaration finally has a general re-pin "
    "writer (src/os/residue_triage_repin.py) that plans by number, writes "
    "nothing by default, refuses a moved status before it can be laundered and "
    "proves its own size on one atomic replace; the real declaration was "
    "re-pinned at R2363 from one live reading (211 entries, 63026B -> 62266B, "
    "TRIAGED 211/211). The carried battery row stays open with its target "
    "named."
)

EXPORT_LATEST = (
    "src/os/residue_triage_repin.py + src/os/test_residue_triage_repin.py "
    "(AC-RTRP1..AC-RTRP6, SUITE PASS 6/6 twice identical), "
    "state/residue_triage.json re-pinned at R2363 (211 entries, TRIAGED), "
    "evidence qa/residue-triage-repin-R2363.log and qa/residue-triage-repin-"
    "live-R2363.log - written 2026-11-02 R2363."
)

EXPORT_NEXT = (
    "R2364: the carried reconcile battery on the committed R2363 tree (target "
    "491 suites / 3922 criteria plus this window one suite and six criteria = "
    "492 / 3928), then the seeded idempotent re-pin face, within 48h."
)


def write_atomic(path, text):
    """Atomic utf-8 LF write with a byte read-back."""
    payload = text.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".clo_r2363_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(path, "rb") as check:
        back = check.read()
    if back != payload:
        raise SystemExit("E_CLO_BACK read-back mismatch on %s" % path)
    return len(payload)


def close_queue():
    with io.open(TECH, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "[done 2026-11-02 R2363]" in text:
        print("TECH already carries this round")
        return
    if text.count(TECH_HEAD) != 1:
        raise SystemExit("E_CLO_TECH head matched %d times"
                         % text.count(TECH_HEAD))
    opened = TECH_HEAD.replace("- [ ] ", "- [x] [done 2026-11-02 R2363] ", 1)
    text = text.replace(TECH_HEAD, opened + TECH_CLOSE, 1)
    if not text.endswith("\n"):
        text += "\n"
    text += render_seed()
    print("TECH bytes %d, row closed and successor seeded"
          % write_atomic(TECH, text))


def execute():
    raw = state_io.read_raw(STATE)
    text = state_io.decode(raw)
    data = state_io.parse(text)
    if LIVE not in (data.get("log") or []):
        if data.get("tick") != TICK - 1:
            raise SystemExit("E_CLO_TICK tick=%r expected=%d"
                             % (data.get("tick"), TICK - 1))
        data["tick"] = TICK
        data["log"].extend(ITEMS)
        payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        new_text = state_io.canon(payload)
        before = len(text.encode("utf-8"))
        after = len(new_text.encode("utf-8"))
        print("STATE bytes %d -> %d (delta %+d)"
              % (before, after, write_atomic(STATE, new_text) - before))
    else:
        print("STATE already carries this round (tick=%r)" % data.get("tick"))

    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        backlog = handle.read()
    if "- [done 2026-11-02 R2363]" in backlog:
        raise SystemExit("E_CLO_BACKLOG already has this row")
    write_atomic(BACKLOG, BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended")

    with io.open(HEARTBEAT, "r", encoding="utf-8") as handle:
        beat = handle.read()
    if not beat.endswith("\n"):
        beat += "\n"
    write_atomic(HEARTBEAT, beat + "%d %s\n" % (TICK, STAMP))
    print("HEARTBEAT appended")

    close_queue()

    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    face = document.get("ceo_face") or {}
    face["current"] = EXPORT_DO
    face["latest_artifact"] = EXPORT_LATEST
    face["next_milestone"] = EXPORT_NEXT
    document["ceo_face"] = face
    document["do"] = EXPORT_DO
    document["export_ts"] = STAMP
    write_atomic(EXPORT, json.dumps(document, ensure_ascii=False, indent=1)
                 + "\n")
    print("EXPORT refreshed at %s" % STAMP)


def main(argv):
    if "--execute" in argv:
        execute()
        return 0
    print("DRY RUN: %d log items, tick %d, backlog row, heartbeat line, "
          "queue close + seed, export face" % (len(ITEMS), TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))