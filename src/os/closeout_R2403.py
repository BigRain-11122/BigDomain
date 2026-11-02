# closeout_R2403.py - the R2403 closeout: state tick + narrative items, then
# the ledger line lands THROUGH ledger_line_shape_guard's own door, then the
# export face is re-derived from the live tree and the heartbeat is stamped.
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import state_io  # noqa: E402
import ledger_line_shape_guard as LLSG  # noqa: E402
import queue_floor_export_face as QFEF  # noqa: E402
import check_export_consistency as CEC  # noqa: E402

STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
HEART = os.path.join(REPO, "heartbeat.txt")
BACKLOG = os.path.join(BASE, "backlog.md")

STAMP = "2026-11-03T23:55:00+08:00"
DO = ("R2403 runner_abort_face: a battery body now names the suite that killed "
      "it (14 aborted legs found in the real pile, including the R2393 leg that "
      "used to leave silence)")
ART = "qa/runner-abort-face-live-R2403.log + src/os/runner_abort_face.py"
NEXT = ("run the carried battery on this committed tree (529 suites / 4150 "
        "criteria) and then claim state/queue/tech.md:476 AC-FBEF1")

LEDGER = ("R2403 tokens: local=~26k api=0 api_reason=product window - one "
          "abort-face module and its six-criteria suite written to criteria "
          "pinned eight rounds earlier, the registry and suite-line laws asked "
          "of the shipped headroom reading at CALL time, one registry wiring "
          "line, one two-leg evidence capture with three adjacent suites, one "
          "read-only live capture over 549 real battery logs that named 14 "
          "aborted legs including the R2393 leg that previously left silence, "
          "one board stamp plus one measured gap row seeded, and the "
          "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
          "external API touches")

LOG = [
    ("2026-11-03 R2403 product window (five-silence scan clean at open: empty "
     "git status at HEAD eeab18b8, no .git/index.lock; LEDGER atbd_lines=0 "
     "unreplied=0; DEC row probe read 0 with the heading pattern, so the "
     "stored token baseline (92) was left untouched and no new decision row "
     "was claimed; the group orders tail stays the 2026-11-02 11:04 "
     "model-policy baseline already acknowledged as non-execution; benchmarks "
     "refreshed 2026-11-02 inside the seven-day gate; floor FLOOR-MET main 5/5 "
     "tech 10/10 explore 10/10; debt gate CLAIM-FIRST "
     "item=reconcile-battery-R2394). The product-first law took the window: "
     "R2395..R2402 were product faces and R2394 was verification-only, so the "
     "queue reader was followed rather than the battery. PRODUCT: claimed "
     "state/queue/tech.md:474 prefix AC-RAF1 (runner_abort_face), whose "
     "AC-RAF1..AC-RAF6 were pinned INSIDE that row at R2395 BEFORE any code, "
     "after a fresh anchor check at HEAD (all five anchors hit only prose and "
     "state files, zero executable occupancy)."),
    ("2026-11-03 R2403 product face, what shipped: SHIPPED "
     "src/os/runner_abort_face.py plus src/os/test_runner_abort_face.py. The "
     "headroom reading only knows suites some leg FINISHED, so the suite that "
     "actually killed a battery was the one line the pile never carried - "
     "R2393 leg 3 died on ledger/test_apimarket_report_claims.py after exactly "
     "300s and no suite line was ever written for it, which is why that suite "
     "reads a comfortable 246.8s today. A body now reads COMPLETE when it "
     "carries the runner's own closing verdict line (no abort reading is "
     "written at all), ABORTED when it carries suite lines but no verdict line "
     "- the running suite is derived as the FIRST registry label with no suite "
     "line in the body, never a hard-coded name, and the last echoed line "
     "rides along so an operator sees where it stopped - and UNREADABLE when "
     "it carries neither, so silence is never read as an abort. The registry "
     "labels and the suite-line law are runner_suite_timeout_headroom's, asked "
     "at CALL time, so the tree keeps one owner for both."),
    ("2026-11-03 R2403 evidence and board: SUITE PASS 6/6 twice with an "
     "identical criterion digest plus three adjacent suites green "
     "(qa/runner-abort-face-R2403.log, 1238B, legs=2 identical=True "
     "adjacent=3 fails=0, one utf-8 LF writer through src/os/evidence_capture."
     "py), wired os-runner-abort-face(6) so the registry reads 529 suites / "
     "4150 criteria. LIVE, not a plan: "
     "qa/runner-abort-face-live-R2403.log (1360B, one utf-8 LF writer, "
     "src/os/live_R2403.py) reads the REAL pile as 549 reconcile-all logs = "
     "508 COMPLETE + 14 ABORTED + 27 UNREADABLE, and one of the fourteen is "
     "reconcile-all-R2393-retry2.log naming ledger-apimarket-reportclaims at "
     "seen=319/529 - the exact leg that previously left silence - beside older "
     "aborts such as reconcile-all-R2129-timeout.log "
     "(suite=ledger-apimarket-searchstock) and reconcile-all-R2201-firstfail."
     "log (suite=ledger-apimarket-repeatpurchase). The module digest "
     "db1d2c633fd26b81 is unchanged before and after the capture. Tech row 474 "
     "stamped [done 2026-11-03 R2403] and one REAL measured gap row seeded "
     "(runner_abort_history, AC-RAH1..AC-RAH6 pre-registered in that row): "
     "MEASURED this window, an aborted leg and live debt read identically even "
     "though R2393's own round carries a green retry leg."),
    ("2026-11-03 R2403 honest disclosures: (a) two of this window own suite "
     "legs were RED on their first runs and both reds were this window own "
     "assertions, never the module: AC-RAF3 pinned three spaces before the "
     "echoed body line where the render legitimately strips them, and it "
     "looked for the string 'LAST RUNNER PASS' in the COMPLETE body, which "
     "correctly carries that line as 'VERDICT-LINE RUNNER PASS' instead. No "
     "criterion was widened and no module behaviour changed. (b) The "
     "UNREADABLE branch is deliberately conservative: an abort that happens "
     "BEFORE the first suite line exists reads UNREADABLE rather than ABORTED, "
     "because nothing in such a body names a suite and a guess is worse than "
     "an honest silence; the 27 UNREADABLE logs in the real pile are exactly "
     "that shape and are counted, not repaired. (c) The board edit was "
     "repaired in-window: the first seed insertion matched the NEXT row's "
     "prefix and merged two rows, which was split back apart before any commit "
     "- the floor and the head were then re-read (FLOOR-MET 10/10, head line "
     "476 AC-FBEF1) instead of trusting the edit. (d) The decision-row probe "
     "used a heading pattern that matched nothing on the real file, so this "
     "window reports no new DEC rows and leaves the stored token set as it "
     "was rather than claiming a baseline it did not measure. (e) NO battery "
     "ran this window, so 529 suites / 4150 criteria is a WIRING count "
     "(528/4144 measured at R2402 plus this window +1 suite / +6 criteria); "
     "the register row reconcile-battery-R2394 stays OPEN with that target. "
     "(f) tasks.md was left untouched: it is the P-47 canonical board and "
     "carries no row for this tech slice."),
    ("2026-11-03 R2403 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law forbids "
     "for every lane task; src/os/register_loop_task.ps1 already passes an "
     "explicit S4U principal but needs an elevated shell, and this session is "
     "unelevated, so the task definition was left untouched (hundred-and-"
     "fifty-eighth consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2403 product window: runner_abort_face - the headroom reading only "
    "knows suites some leg FINISHED, so the suite that killed a battery was "
    "the one line the pile never carried (R2393 leg 3 died on ledger/"
    "test_apimarket_report_claims.py at exactly 300s with no suite line). "
    "SHIPPED src/os/runner_abort_face.py plus its six-criteria suite: a body "
    "reads COMPLETE from the runner's own closing verdict line, ABORTED when it "
    "carries suite lines but no verdict line (the running suite is the FIRST "
    "registry label with no suite line - derived, not hard-coded - with the "
    "last echoed line carried), and UNREADABLE when it carries neither; the "
    "registry and suite-line laws are the shipped headroom reading's, asked at "
    "CALL time. SUITE PASS 6/6 twice with an identical digest plus three "
    "adjacent suites green (qa/runner-abort-face-R2403.log, 1238B, legs=2 "
    "identical=True adjacent=3 fails=0), wired os-runner-abort-face(6) so the "
    "registry reads 529 suites / 4150 criteria. LIVE: "
    "qa/runner-abort-face-live-R2403.log reads the REAL pile as 549 logs = 508 "
    "COMPLETE + 14 ABORTED + 27 UNREADABLE, one of the aborts being "
    "reconcile-all-R2393-retry2.log suite=ledger-apimarket-reportclaims "
    "(seen=319/529). Board: row 474 stamped and one measured gap row seeded "
    "(AC-RAH1..6), floor FLOOR-MET 5/5 10/10 10/10. No battery ran: "
    "reconcile-battery-R2394 stays OPEN at 529 suites / 4150 criteria.\n")


def write_atomic(path, text):
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".r2403-",
                                   suffix=".tmp")
    with os.fdopen(handle, "wb") as sink:
        sink.write(text.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, path)


ROW_TEXT = ("R2403 runner_abort_face shipped - a battery body names the suite "
            "that killed it (real pile: 549 logs, 14 ABORTED, 27 UNREADABLE); "
            "registry 529/4150")


def fix_results(data):
    """The two derived rows the checker pins: the tick row and this round row."""
    pat = json.load(io.open(
        os.path.join(BASE, "export_consistency_patterns.json"),
        encoding="utf-8"))
    label = pat["tick_row_label"]
    tick = json.load(io.open(STATE, encoding="utf-8"))["tick"]
    results = data.setdefault("results", [])
    named = [row for row in results
             if isinstance(row, list) and len(row) >= 2 and row[1] == label]
    if len(named) != 1:
        sys.stdout.write("E_RESULTS: tick row count=%d\n" % len(named))
        return 2
    named[0][0] = str(tick)
    if not any(isinstance(row, list) and str(row[0]) == str(tick)
               and row[1] != label for row in results):
        results.insert(0, [str(tick), ROW_TEXT])
    sys.stdout.write("RESULTS tick_row=%s round_row=%s\n"
                     % (named[0][0], results[0][0]))
    return 0


def main():
    if "--results-only" in sys.argv:
        data = json.load(io.open(EXPORT, encoding="utf-8"))
        if fix_results(data) != 0:
            return 2
        write_atomic(EXPORT,
                     json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        sys.stdout.write("EXPORT results refreshed bytes=%d\n"
                         % os.path.getsize(EXPORT))
        return 0

    tech = io.open(os.path.join(REPO, "state", "queue", "tech.md"),
                   encoding="utf-8", newline="").read()
    stamped = tech.count("- [x] [done 2026-11-03 R2403]")
    seeded = tech.count("AC-RAH1..AC-RAH6")
    if stamped != 1 or seeded < 1:
        sys.stdout.write("E_BOARD stamped=%d rah=%d\n" % (stamped, seeded))
        return 2
    sys.stdout.write("BOARD verified stamped=1 seed_mentions=%d\n" % seeded)

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if not backlog.startswith("- [x] R2403"):
        write_atomic(BACKLOG, BACKLOG_ROW + backlog)
        sys.stdout.write("BACKLOG row prepended\n")

    before = io.open(STATE, encoding="utf-8", newline="").read()
    state = json.loads(before)
    state["tick"] = int(state.get("tick", 0)) + 1
    for item in LOG:
        if item in state["log"]:
            sys.stdout.write("E_STATE duplicate item\n")
            return 2
        state["log"].append(item)
    text = state_io.canon(json.dumps(state, ensure_ascii=False, indent=2)
                          + "\n")
    raw = text.encode("utf-8")
    write_atomic(STATE, text)
    if open(STATE, "rb").read() != raw:
        sys.stdout.write("E_STATE read-back differs\n")
        return 2
    readback = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE tick=%d log_items=%d bytes=%d -> %d\n"
                     % (readback["tick"], len(readback["log"]),
                        len(before.encode("utf-8")), len(raw)))

    verdict = LLSG.append_ledger_line(STATE, LEDGER, execute=True)
    sys.stdout.write("LEDGER door verdict=%s predicted=%s wrote=%s\n"
                     % (verdict["verdict"], verdict.get("predicted_bytes"),
                        verdict.get("wrote")))
    if verdict["verdict"] != "ACCEPTED" or verdict.get("wrote") != "yes":
        return 2
    final = json.load(io.open(STATE, encoding="utf-8"))
    sys.stdout.write("STATE after ledger tick=%d log_items=%d bytes=%d\n"
                     % (final["tick"], len(final["log"]),
                        os.path.getsize(STATE)))

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
    if fix_results(data) != 0:
        return 2
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ART
    face["last_artifact"] = ART
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-05T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2403 product window runner_abort_face shipped; "
              "battery carried\n" % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())