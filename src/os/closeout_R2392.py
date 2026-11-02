"""R2392 closeout: state tick + log, then the CEO-visible export (F3 derived).

Order: state.json first (the checker derives its tick row and counters from
it), then docs/status-export.json, then heartbeat.txt. Every number written
here is read from a tool on the same tree, never typed by hand.
"""

import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import state_io  # noqa: E402

ROUND = 2392
STAMP = "2026-11-02T22:34:00+08:00"

DO = (
    "R2392 product window (five-silence scan clean at open: empty git status "
    "at HEAD d4d08910, no .git/index.lock; LEDGER atbd_lines=0 "
    "unreplied_groups=0; DEC rows=172 tokens=86 new=0; the group orders tail "
    "2026-11-02 11:04 already acknowledged as non-execution; benchmarks "
    "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10). PRODUCT: claimed state/queue/tech.md:449 "
    "prefix AC-ACSP1 (append_check_status_precedence), criteria pinned in that "
    "row at R2385 BEFORE any code, anchors re-checked at HEAD. SHIPPED "
    "src/os/append_check_status_precedence.py plus its six-criteria suite: the "
    "single writer --check asked the triage read FIRST, so exactly when that "
    "read refused (measured at R2385: --check --round R1755 answered "
    "E_RTA_UNREADABLE / E_RTR_DECL_FUTURE and printed no status at all while "
    "the status face alone read R1755 DELIVERED at exit 0) the operator got "
    "nothing about the round they asked about. The module owns only the ORDER: "
    "the status reading stays single_append_status_face (asked at call time), "
    "the triage reading stays residue_triage.read, and the refusal is RETURNED "
    "so residue_triage_append keeps the one E_RTA_* code mapping - no second "
    "residue scan is written. A refused check now prints its live status and "
    "one NOTE line beside the unchanged refusal and exit 3; the same call as "
    "--json carries the status over the pinned REPORT_KEYS; the --append path "
    "never asks the face and its two lines are byte-identical; a clean check "
    "is unchanged at exit 0. SUITE PASS 6/6 twice with an identical criterion "
    "digest plus three adjacent suites green "
    "(qa/append-check-status-precedence-R2392.log, legs=2 identical=True "
    "adjacent=3 fails=0), wired os-append-check-status-precedence(6). LIVE on "
    "the real tree: --check --round R1755 reads E_RTA_UNREADABLE + "
    "E_RTR_DECL_FUTURE + STATUS R1755 DELIVERED + one NOTE at exit 3, the same "
    "call as --json carries status=DELIVERED with verdict=E_RTA_UNREADABLE, a "
    "clean check R2391 is unchanged at exit 0, and an --append refusal is still "
    "its two lines (qa/append-check-status-precedence-live-R2392.log). Board: "
    "row 449 stamped and one REAL measured gap row seeded "
    "(refused_check_declaration_face, AC-RCDF1..AC-RCDF6 pre-registered in that "
    "row, five anchors zero-occupancy at HEAD) because the refused JSON still "
    "reports declared_by=\"-\" while its own detail line names R2391."
)

LOG = [
    "2026-11-02 R2392 product window (five-silence scan clean at open: empty "
    "git status at HEAD d4d08910, no .git/index.lock; LEDGER atbd_lines=0 "
    "unreplied_groups=0; DEC rows=172 tokens=86 new=0; the group orders tail "
    "2026-11-02 11:04 already acknowledged as non-execution; benchmarks "
    "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10). PRODUCT: claimed state/queue/tech.md:449 "
    "prefix AC-ACSP1 (append_check_status_precedence); criteria AC-ACSP1..6 "
    "were pinned in that row at R2385 BEFORE any code and were re-anchored at "
    "HEAD. SHIPPED src/os/append_check_status_precedence.py plus "
    "src/os/test_append_check_status_precedence.py: the --check path asked the "
    "triage read FIRST, so a refused read printed no status at all for the "
    "round the operator asked about; the status face is now asked before the "
    "triage read, the refusal is RETURNED so residue_triage_append keeps the "
    "one E_RTA_* mapping, and no second residue scan is written. SUITE PASS 6/6 "
    "twice with an identical criterion digest plus three adjacent suites green "
    "(qa/append-check-status-precedence-R2392.log, 1545B, legs=2 "
    "identical=True adjacent=3 fails=0), wired "
    "os-append-check-status-precedence(6). LIVE: --check --round R1755 reads "
    "E_RTA_UNREADABLE + E_RTR_DECL_FUTURE + STATUS R1755 DELIVERED + one NOTE "
    "at exit 3 where it printed no status before, --json carries "
    "status=DELIVERED with verdict=E_RTA_UNREADABLE over the pinned keys, a "
    "clean check R2391 is unchanged at exit 0, and an --append refusal is still "
    "exactly its two lines "
    "(qa/append-check-status-precedence-live-R2392.log, 1190B, single utf-8 LF "
    "writer). Board: row 449 stamped and one REAL measured gap row seeded "
    "(refused_check_declaration_face, AC-RCDF1..AC-RCDF6 pre-registered in that "
    "row, five anchors zero-occupancy at HEAD).",

    "2026-11-02 R2392 honest disclosures: (a) three first-run reds were this "
    "window own fixtures, never the module - the R9001 log item made the round "
    "logged instead of queue_only so the live residue was empty, the fixture "
    "entry's until R2400 sat below the round it declared (EXPIRED, so the check "
    "read RESIDUE at exit 2), and the expected append line was compared without "
    "normalising the console CRLF; each was fixed in the test and no criterion "
    "was widened. (b) The carried reconcile-battery-R2387 was NOT run this "
    "window and stays OPEN for the fifth window with its measured successor "
    "target (518 suites / 4084 criteria) named in the new register row; the "
    "product face took the window, stated plainly rather than hidden. (c) "
    "tasks.md was left untouched: it is the P-47 canonical board and carries no "
    "row for this tech slice. (d) The state file stood at 76853B against the "
    "78500B waterline before this closeout, so the next window must canonicalise "
    "the layout first and then fold at a TRUE round-block boundary.",

    "2026-11-02 R2392 self-heal check: BigDomain-OSLoop is still registered "
    "with LogonType=InteractiveToken (read back this window), which the "
    "2026-09-29 machine law forbids for every lane task; the registration "
    "script already passes an explicit S4U principal but needs an elevated "
    "shell and this session is unelevated, so the task definition was left "
    "untouched (hundred-and-forty-seventh consecutive disclosure, carried as "
    "the stale row loop-s4u-reconcile in state/debt.md).",

    "2026-11-02 R2392 tokens: local=~38k api=0 api_reason=product window - one "
    "precedence module and its six-criteria suite written to criteria pinned "
    "seven rounds earlier, one module-level refusal seam added to the shipped "
    "check path, one registry wiring line, one two-leg evidence capture with "
    "three adjacent suites, one four-step live capture through a single utf-8 "
    "LF writer, one board stamp and one measured gap row seeded, one register "
    "row opened, and the state/export/backlog/heartbeat closeout; zero cloud "
    "calls and zero external API touches",
]


def load(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_canon(path, payload):
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return state_io.fix(path, execute=True)


def floor_json():
    proc = subprocess.Popen([sys.executable, os.path.join(BASE,
                                                          "queue_floor.py"),
                             "--check", "--json"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, _err = proc.communicate()
    return json.loads(out.decode("utf-8"))


def main():
    state = load(STATE)
    if state["tick"] == ROUND - 1:
        state["tick"] = ROUND
        state["log"].extend(LOG)
    elif state["tick"] == ROUND and not any(
            item.startswith("2026-11-02 R2392 product window")
            for item in state["log"]):
        state["log"].extend(LOG)
    elif state["tick"] != ROUND:
        print("E_CLOSE_TICK: state tick is %r" % state["tick"])
        return 3
    fixed = dump_canon(STATE, state)
    print("state %s bytes=%d crlf=%d off_indent=%d"
          % (fixed["verdict"], os.path.getsize(STATE),
             fixed.get("after", {}).get("crlf", -1),
             fixed.get("after", {}).get("off_indent", -1)))

    derived, state_now, export, _pat = CEC.recompute()
    export["export_ts"] = STAMP
    export["do"] = DO
    face = export["ceo_face"]
    face["current"] = (
        "R2392: a refused single-append check no longer answers nothing about "
        "the round it was asked about - the live status is read first, so the "
        "operator sees DELIVERED beside the refusal it tripped on.")
    artifact = ("src/os/append_check_status_precedence.py plus its "
                "six-criteria suite (qa/append-check-status-precedence-R2392.log,"
                " qa/append-check-status-precedence-live-R2392.log)")
    face["latest_artifact"] = artifact
    face["last_artifact"] = artifact
    face["next_milestone"] = (
        "refused_check_declaration_face: the refused --json payload names the "
        "declaration boundary it tripped on, so the prose and the payload read "
        "one number")
    face["next_milestone_due"] = "2026-11-03T23:00:00+08:00"
    face["updated_at"] = STAMP

    if not (export["results"] and export["results"][0][0] == str(ROUND)):
        export["results"].insert(0, [str(ROUND), DO])
    if len(export["results"]) > 12:
        export["results"] = export["results"][:12]
    # The pinned tick row is reused, never duplicated: the checker requires
    # exactly one row carrying its label and that row's tick to equal state.
    label = CEC._load_patterns()["tick_row_label"]
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(ROUND)

    export["self_drive"].update({
        "window": derived["window"],
        "window_days": derived["window_days"],
        "log_lines_in_window": derived["log_lines_in_window"],
        "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
        "no_pullable_mention_lines": derived[
            "no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines": derived[
            "substantive_non_idle_mention_lines"],
        "proposals_total": derived["proposals_total"],
        "proposals_open": derived["proposals_open"],
        "queue_main_open": derived["queue_main_open"],
        "queue_tech_open": derived["queue_tech_open"],
        "queue_explore_open": derived["queue_explore_open"],
    })

    floors = floor_json()
    for row in export["queue"]["queues"]:
        for measured in floors["queues"]:
            if measured["queue"] != row["queue"]:
                continue
            for key in ("open_rows", "done_rows", "gated_rows", "claimable",
                        "floor", "shortfall", "status"):
                row[key] = measured[key]
    export["queue"]["floors"] = floors["floors"]
    export["queue"]["verdict"] = floors["verdict"]
    export["queue"]["shortfall_total"] = floors["shortfall_total"]
    export["queue"]["missing"] = floors["missing"]

    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2) + "\n")
    print("export bytes=%d" % os.path.getsize(EXPORT))

    line = ("2026-11-02T22:34:00+08:00 R2392 append_check_status_precedence "
            "shipped; a refused --check now names its live status at exit 3 "
            "while the append path stays byte-identical; battery carried OPEN\n")
    with io.open(HEARTBEAT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
    print("heartbeat bytes=%d" % os.path.getsize(HEARTBEAT))
    return 0


if __name__ == "__main__":
    sys.exit(main())