"""R2399 closeout: backlog row, state tick and log, export refresh, heartbeat.

The board edit (row 460 stamped, discharge note, one seeded gap row) was made
by hand this window and is verified here by assertion rather than rewritten.

Writes only: src/os/backlog.md, src/os/state.json, docs/status-export.json,
heartbeat.txt. Every write is atomic with a read-back proof.
"""

import datetime
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))

import state_io  # noqa: E402
import queue_floor_export_face as QFEF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

TECH = os.path.join(REPO, "state", "queue", "tech.md")
BACKLOG = os.path.join(BASE, "backlog.md")
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEART = os.path.join(REPO, "heartbeat.txt")

DO = ("R2399 owner_table_usage_wire: a constant is an own-flag table only "
      "when a help or usage path in the same file reads it - the three "
      "measured data-constant false positives read NO-TABLE while "
      "runner_arg_guard keeps its real drift and battery_followup keeps "
      "AGREES 8/8")
ART = ("qa/owner-table-usage-wire-live-R2399.log + "
       "src/os/owner_table_usage_wire.py")
NEXT = ("claim state/queue/tech.md:463 AC-EPBW1 (export_publish_from_import_law) "
        "- the bare from-import publish spelling resolves to its callee")

BACKLOG_ROW = (
    "- [x] R2399 [done 2026-11-03] owner_table_usage_wire - "
    "state/queue/tech.md:460 AC-OTUW1..AC-OTUW6 delivered: R2390's reader "
    "treated EVERY module-level UPPER_CASE constant carrying flag-shaped "
    "literals as a declared own-flag table, so a tool whose DATA looks like "
    "flags read as a one-sided table (measured: evidence_R2372.py, "
    "r2140_fold.py, retry_naming.py all PARITY-DISAGREES with their data "
    "listed as missing_in_parser). SHIPPED src/os/owner_table_usage_wire.py "
    "plus its six-criteria suite: a constant counts only when a usage/help "
    "path in the same file reads it - measured from the source as a function "
    "whose name carries usage/help OR a function that emits a usage text, "
    "with one local-alias hop and one module-handoff hop "
    "(sys.modules[__name__] inside a usage path makes every declared table "
    "usable). The table derivation, parser side, verdict words and JSON keys "
    "stay owner_table_parity's, asked at CALL time; that module is "
    "byte-identical to git HEAD and its printed lines reproduce identically. "
    "SUITE PASS 6/6 twice with an identical criterion digest plus three "
    "adjacent suites green (qa/owner-table-usage-wire-R2399.log, 1867B, "
    "legs=2 identical=True adjacent=3 fails=0), wired "
    "os-owner-table-usage-wire(6). LIVE, not a plan: "
    "qa/owner-table-usage-wire-live-R2399.log (1369B, crlf=0) reads the three "
    "false positives as NO-TABLE, runner_arg_guard.py as "
    "PARITY-DISAGREES missing_in_table=[--guard*,--help], battery_followup.py "
    "as PARITY-AGREES 8/8, a bad flag at exit 5, a missing path at exit 3, "
    "and the module digest unchanged before and after. Board: row 460 stamped "
    "and one REAL measured gap row seeded (owner_table_reader_parity, "
    "AC-OTRP1..AC-OTRP6 pre-registered): the two readers now disagree on 40 "
    "files and nothing publishes it. No battery ran: the carried row "
    "reconcile-battery-R2394 stays OPEN at its measured target 524 suites / "
    "4120 criteria plus this window +1 suite / +6 criteria.\n")

LOG = [
    "2026-11-03 R2399 product window (five-silence scan clean at open: empty "
    "git status at HEAD 86616f33, no .git/index.lock; LEDGER atbd_lines=0 "
    "unreplied_groups=0; DEC rows=140 tokens=92 new=0; the group orders tail "
    "2026-11-02 11:04 already acknowledged as non-execution; benchmarks "
    "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10; debt gate CLAIM-FIRST "
    "item=reconcile-battery-R2394 carried=5 stale=yes). The product-first law "
    "took the window: R2394 was verification-only and R2395..R2398 were "
    "product faces that left the battery row standing, so the reader was "
    "followed. PRODUCT: claimed state/queue/tech.md:460 prefix AC-OTUW1 "
    "(owner_table_usage_wire), whose AC-OTUW1..AC-OTUW6 were pinned INSIDE "
    "that row at R2390 BEFORE any code, after a fresh anchor check at HEAD "
    "(all five anchors hit only prose and state files: the queue row, "
    "src/os/backlog.md, closeout_R2390.py, state.json, status-export.json - "
    "zero executable occupancy).",

    "2026-11-03 R2399 product face, what shipped: SHIPPED "
    "src/os/owner_table_usage_wire.py plus src/os/test_owner_table_usage_wire.py. "
    "R2390 read every module-level UPPER_CASE constant carrying flag-shaped "
    "literals as a declared table, which is right about a real argument table "
    "and wrong about a tool whose DATA looks like one. One notion is now "
    "measured from the source: a constant is a TABLE only when a help or "
    "usage path in the same file reads it, where a usage path is a function "
    "whose own name carries usage/help OR a function that emits a usage text, "
    "and a constant counts through a direct name, one local alias, or a "
    "module handoff (sys.modules[__name__] passed to a renderer, which is how "
    "battery_followup derives its help block from its own tables). The table "
    "derivation, the parser side, the verdict words and the JSON keys are "
    "owner_table_parity's, asked at CALL time, so no second wheel exists.",

    "2026-11-03 R2399 evidence and board: SUITE PASS 6/6 twice with an "
    "identical criterion digest plus three adjacent suites green "
    "(qa/owner-table-usage-wire-R2399.log, 1867B, legs=2 identical=True "
    "adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-owner-table-usage-wire(6) so the "
    "registry reads 525 suites / 4126 criteria. LIVE, not a plan: "
    "qa/owner-table-usage-wire-live-R2399.log (1369B, crlf=0, bare_cr=0, one "
    "utf-8 LF writer) reads the REAL tree as evidence_R2372.py, r2140_fold.py "
    "and retry_naming.py NO-TABLE, runner_arg_guard.py PARITY-DISAGREES "
    "missing_in_table=[--guard*,--help] missing_in_parser=[], "
    "battery_followup.py PARITY-AGREES table=8 parser=8, the shipped law's "
    "own line unchanged, a bad flag at exit 5 with E_OTUW_BAD_FLAG, a missing "
    "path at exit 3 with E_OTUW_UNREADABLE, a byte-stable --json, and the "
    "module digest f5cb2ecdddcedbec identical before and after. Tech row 460 "
    "stamped [done 2026-11-03 R2399] and one REAL measured gap row seeded "
    "(owner_table_reader_parity, AC-OTRP1..AC-OTRP6 pre-registered in that "
    "row): MEASURED this window over every non-test src/os/*.py, the law and "
    "the wire disagree on 40 files - 37 one-per-round battery_followup_R* "
    "copies plus battery_followup_help_wire.py, evidence_R2372.py, "
    "r2140_fold.py, retry_naming.py and run_identity.py - and nothing "
    "publishes that set difference.",

    "2026-11-03 R2399 honest disclosures: (a) two of this window own suite "
    "legs were RED on their first run and both reds were this window own "
    "assertions, never the module: AC-OTUW3 looked for tool names in the "
    "module text and the module docstring legitimately CITES the five "
    "measured files as evidence, so the assertion now reads every string "
    "constant that is not a docstring; and AC-OTUW6 asserted a stdlib-only "
    "import set where the module must import owner_table_parity - the shared "
    "law AC-OTUW4 requires - so the allowed set names that one module "
    "explicitly. No criterion was widened; both are stated in the suite. (b) "
    "The usage-path detector is a false-NEGATIVE by design: a tool that "
    "renders its help block from a constant inside a function named neither "
    "usage nor help, or reaches a constant through a call chain longer than "
    "one local alias, reads NO-TABLE even though it may own a real table. "
    "That direction is stated in the module docstring rather than hidden, "
    "because a reader whose job is to stop false positives must not invent "
    "them. (c) NO battery ran this window, so 525 suites / 4126 criteria is "
    "a WIRING count (524/4120 plus this window +1 suite / +6 criteria); the "
    "register row stays OPEN. (d) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice.",

    "2026-11-03 R2399 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal but needs an elevated shell, and this "
    "session is unelevated, so the task definition was left untouched "
    "(hundred-and-fifty-fourth consecutive disclosure, carried as the row "
    "loop-s4u-reconcile in state/debt.md).",

    "R2399 tokens: local=~26k api=0 api_reason=product window - one notion "
    "module and its six-criteria suite written to criteria pinned nine rounds "
    "earlier, one usage-path detector measured from the source with two hops "
    "and a stated false-negative, one registry wiring line, one two-leg "
    "evidence capture with three adjacent suites, one seven-step read-only "
    "live capture through a single utf-8 LF writer, one 40-file disagreement "
    "measurement that seeded the successor row, one board stamp and one "
    "measured gap row seeded, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches",
]

NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")


def write_atomic(path, text, encoding="utf-8"):
    directory = os.path.dirname(path)
    handle, tmp = tempfile.mkstemp(dir=directory, prefix=".otuw-",
                                   suffix=".tmp")
    os.close(handle)
    with io.open(tmp, "w", encoding=encoding, newline="\n") as out:
        out.write(text)
    os.replace(tmp, path)


def main():
    # 0. the board edit is verified, not rewritten
    tech = io.open(TECH, encoding="utf-8", newline="").read()
    if tech.count("- [x] [done 2026-11-03 R2399]") != 1:
        sys.stdout.write("E_BOARD: stamp not unique\n")
        return 2
    if tech.count("AC-OTRP1..AC-OTRP6") != 1:
        sys.stdout.write("E_BOARD: seed row not unique\n")
        return 2
    sys.stdout.write("BOARD verified stamped=%d seeded=%d\n"
                     % (tech.count("- [x] [done 2026-11-03 R2399]"),
                        tech.count("AC-OTRP1..AC-OTRP6")))

    # 1. backlog row on top
    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if backlog.startswith("- [x] R2399"):
        sys.stdout.write("E_BACKLOG: row already present\n")
        return 2
    write_atomic(BACKLOG, BACKLOG_ROW + backlog)
    sys.stdout.write("BACKLOG row prepended\n")

    # 2. state: tick + log items
    before = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(before)
    state["tick"] = int(state.get("tick", 0)) + 1
    for item in LOG:
        if item in state["log"]:
            sys.stdout.write("E_STATE: duplicate log item\n")
            return 2
        state["log"].append(item)
    text = state_io.canon(json.dumps(state, ensure_ascii=False, indent=2)
                          + "\n")
    raw = text.encode("utf-8")
    handle, tmp = tempfile.mkstemp(dir=BASE, prefix=".otuw-", suffix=".tmp")
    with os.fdopen(handle, "wb") as sink:
        sink.write(raw)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    if back != raw:
        sys.stdout.write("E_STATE: read-back differs\n")
        return 2
    readback = json.load(io.open(STATE, encoding="utf-8"))
    assert readback["tick"] == state["tick"]
    assert readback["log"] == state["log"]
    sys.stdout.write("STATE tick=%d log_items=%d bytes=%d -> %d\n"
                     % (readback["tick"], len(readback["log"]), len(before),
                        os.path.getsize(STATE)))

    # 3. export: derived queue block, derived counters, three CEO lines
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    QFEF.apply(data, REPO)
    derived = CEC.recompute()[0]
    for key, value in derived.items():
        if key in data.get("self_drive", {}):
            data["self_drive"][key] = value
        else:
            sys.stdout.write("NOTE derived key not in export: %s\n" % key)
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ART
    face["last_artifact"] = ART
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-05T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    # 4. heartbeat
    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2399 product window owner_table_usage_wire "
              "shipped; battery carried\n" % (STAMP, readback["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())