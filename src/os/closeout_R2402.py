# closeout_R2402.py - the R2402 closeout: state tick + narrative items, then
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

STAMP = "2026-11-03T23:40:00+08:00"
DO = ("R2402 relative_import_publish_binding: a PACKAGE-RELATIVE import binds "
      "its local name, so an in-package publisher is no longer reported as an "
      "unbound call")
ART = "qa/relative-import-publish-binding-live-R2402.log + src/os/relative_import_publish_binding.py"
NEXT = ("run the carried battery on this committed tree (528 suites / 4144 "
        "criteria) and then claim state/queue/tech.md:474 AC-RAF1")

LEDGER = ("R2402 tokens: local=~34k api=0 api_reason=product window - one "
          "relative-binding notion and its six-criteria suite written to "
          "criteria pinned nine rounds earlier, the parent law asked at CALL "
          "time for every classification, one registry wiring line, one "
          "two-leg evidence capture with three adjacent suites, one read-only "
          "live capture that reads the REAL tree WIRE 11/11 with relative=0 and "
          "shows the relative spelling named on a fixture, one board stamp with "
          "two measured gap rows seeded so the floor reads 10/10, one fold at a "
          "true round-block boundary plus its residue re-pin, and the "
          "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
          "external API touches")

LOG = [
    ("2026-11-03 R2402 product window (five-silence scan clean at open: empty "
     "git status at HEAD d38254ce, no .git/index.lock; LEDGER @BigDomain "
     "unreplied=0; DEC rows=140 tokens=92 new=0; the group orders tail stays "
     "the 2026-11-02 11:04 model-policy baseline already acknowledged as "
     "non-execution; benchmarks refreshed 2026-11-02 inside the seven-day "
     "gate; debt gate CLAIM-FIRST item=reconcile-battery-R2394; floor read "
     "FLOOR-DEBT tech 9/10). The product-first law took the window: R2395.."
     "R2401 were product faces and R2394 was verification-only, so the queue "
     "reader was followed rather than the battery. PRODUCT: claimed "
     "state/queue/tech.md:465 prefix AC-RIPB1 (relative_import_publish_"
     "binding), whose AC-RIPB1..AC-RIPB6 were pinned INSIDE that row at R2400 "
     "BEFORE any code, after a fresh anchor check at HEAD (all five anchors hit "
     "only prose and state files, zero executable occupancy)."),
    ("2026-11-03 R2402 product face, what shipped: SHIPPED src/os/relative_"
     "import_publish_binding.py plus src/os/test_relative_import_publish_"
     "binding.py. The from-import law matched `from M import publish` through "
     "the identity module's dotted-module patterns, which require a word "
     "character after `from`, so a PACKAGE-RELATIVE import bound nothing and "
     "the call read kind=bare state=UNRESOLVED - a real in-package publisher "
     "reported as an unbound call. ONE added notion binds the relative name "
     "with the module text exactly as the file wrote it (`.`, `..`, `.wire`, "
     "`..pkg.sub`) and every classification is the parent law's classify_line "
     "asked at CALL time with the merged name table, so there is still exactly "
     "one publish classifier in the tree and the attribute half is still the "
     "guard's own law. A bound-but-unplaceable relative module reads state "
     "RELATIVE, a distinct word from FOREIGN and from UNRESOLVED, because the "
     "import DID bind the name but the package is not resolvable from one file; "
     "that is the seed's \"names the relative form it cannot place\" branch "
     "rather than inventing an absolute module."),
    ("2026-11-03 R2402 evidence and board: SUITE PASS 6/6 (seven assertions) "
     "twice with an identical criterion digest plus three adjacent suites green "
     "(qa/relative-import-publish-binding-R2402.log, 1452B, legs=2 "
     "identical=True adjacent=3 fails=0, one utf-8 LF writer through "
     "src/os/evidence_capture.py), wired os-relative-import-publish-binding(6) "
     "so the registry reads 528 suites / 4144 criteria. LIVE, not a plan: "
     "qa/relative-import-publish-binding-live-R2402.log (649B) reads the REAL "
     "src/os as verdict=WIRE code=0 scanned=2137 publishers=11 wire=11 "
     "relative=0 no_publish=15 from_import=0 bare=0, the parent law over the "
     "same 2137 files with exactly the same 11/11, a relative fixture as "
     "verdict=RELATIVE code=2 kind=from_import module=.wire line=10, and the "
     "same fixture through the parent law still kind=bare state=UNRESOLVED - so "
     "the repair is prospective on this tree and proved on fixtures, not "
     "claimed as a live catch. Tech row 465 stamped [done 2026-11-03 R2402] and "
     "TWO REAL measured gap rows seeded (publish_relative_package_identity "
     "AC-PRPI1..AC-PRPI6 and relative_import_alias_gate AC-RIAG1..AC-RIAG6), so "
     "the floor reads FLOOR-MET main 5/5 tech 10/10 explore 10/10."),
    ("2026-11-03 R2402 honest disclosures: (a) three of this window own suite "
     "legs were RED on their first runs and one red was a REAL module "
     "ordering defect, not a criterion: AC-RIPB5 caught the JSON row keys in "
     "the order kind,receiver,module,state,relative,line,text where the pinned "
     "CALL_KEYS say kind,receiver,module,state,line,relative,text, so "
     "classify_script now builds the row in the pinned order instead of "
     "mutating the parent's dict; the other two reds were this window own "
     "assertions (the anchor check read the module docstring's own mention of "
     "the parent patterns, and a fixture line number was pinned at 11 where the "
     "measured call sits at 10). No criterion was widened. (b) AC-RIPB4 also "
     "had to name its root correctly: the parent's verdict over a mixed world "
     "is FOREIGN, so the parent-vs-parent comparison runs on a relative-only "
     "world where UNRESOLVED is the honest expected word. (c) The relative "
     "table binds only an alias of the imported name `publish`, while the "
     "ABSOLUTE table binds the alias of any imported name; AC-RIPB3 requires "
     "that asymmetry for the relative side, and it is now a seeded row "
     "(relative_import_alias_gate) rather than a quiet difference. (d) NO "
     "battery ran this window, so 528 suites / 4144 criteria is a WIRING count "
     "(527/4138 measured at R2401 plus this window +1 suite / +6 criteria); "
     "the register row reconcile-battery-R2394 stays OPEN with that target. "
     "(e) tasks.md was left untouched: it is the P-47 canonical board and "
     "carries no row for this tech slice."),
    ("2026-11-03 R2402 closeout housekeeping, measured not assumed: state.json "
     "stood at 84539B against the 78500B waterline, so fold 649 ran through "
     "src/os/state_fold.py at a TRUE round-block boundary - log items 1..22, "
     "the cut landing on R2392's own ledger line so no round block is split - "
     "with a summary naming all 56 window tokens (token_missing=[]), predicted "
     "60419B and measured 60419B exactly, margin 18081B, and 61 log items left "
     "live. The fold created residue for the five rounds it moved, so "
     "residue_triage_repin ran once from ONE live reading (declared_by=R2402, "
     "until=R2412, entries 244 -> 249, 69372B -> 70256B exactly as planned, "
     "dropped=0) and residue_triage now reads TRIAGED 249/249."),
    ("2026-11-03 R2402 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law forbids "
     "for every lane task; src/os/register_loop_task.ps1 already passes an "
     "explicit S4U principal but needs an elevated shell, and this session is "
     "unelevated, so the task definition was left untouched (hundred-and-"
     "fifty-seventh consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2402 product window: relative_import_publish_binding - a "
    "PACKAGE-RELATIVE import (`from . import publish`, `from .wire import "
    "publish`) now binds its local name and reads from_import with the relative "
    "module text instead of bare/UNRESOLVED, because the identity module's "
    "patterns require a dotted module name and a package-relative import "
    "matched nothing (measured at R2400 on a fixture, still true at HEAD). "
    "SHIPPED src/os/relative_import_publish_binding.py plus its six-criteria "
    "suite: ONE added notion (the relative binding table, with the local name "
    "being the ALIAS so the alias law holds) and every classification is the "
    "parent law's classify_line asked at CALL time with the merged table, so "
    "there is still one publish classifier; a bound-but-unplaceable relative "
    "module reads state RELATIVE, a distinct word from FOREIGN and UNRESOLVED. "
    "SUITE PASS 6/6 twice with an identical criterion digest plus three "
    "adjacent suites green (qa/relative-import-publish-binding-R2402.log, "
    "1452B, legs=2 identical=True adjacent=3 fails=0), wired "
    "os-relative-import-publish-binding(6) so the registry reads 528 suites / "
    "4144 criteria. LIVE: qa/relative-import-publish-binding-live-R2402.log "
    "reads the REAL src/os as WIRE 11/11 over 2137 files with relative=0, the "
    "parent law reading exactly the same, and a relative fixture as RELATIVE "
    "module=.wire where the parent law still reads bare/UNRESOLVED. Board: row "
    "465 stamped and two measured gap rows seeded (AC-PRPI1..6, AC-RIAG1..6), "
    "floor FLOOR-MET 5/5 10/10 10/10. No battery ran: reconcile-battery-R2394 "
    "stays OPEN at 528 suites / 4144 criteria.\n")


def write_atomic(path, text):
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".r2402-",
                                   suffix=".tmp")
    with os.fdopen(handle, "wb") as sink:
        sink.write(text.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, path)


ROW_TEXT = ("R2402 relative_import_publish_binding shipped - a "
            "PACKAGE-RELATIVE import binds its local name and reads "
            "from_import with the relative module text instead of "
            "bare/UNRESOLVED; real tree WIRE 11/11, registry 528/4144")


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
    stamped = tech.count("- [x] [done 2026-11-03 R2402]")
    seeded = tech.count("AC-RIPB..") + tech.count("AC-PRPI1..AC-PRPI6")
    if stamped != 1 or tech.count("AC-PRPI1..AC-PRPI6") != 1 \
            or tech.count("AC-RIAG1..AC-RIAG6") != 1:
        sys.stdout.write("E_BOARD stamped=%d prpi=%d riag=%d\n"
                         % (stamped, tech.count("AC-PRPI1..AC-PRPI6"),
                            tech.count("AC-RIAG1..AC-RIAG6")))
        return 2
    sys.stdout.write("BOARD verified stamped=1 seeded=2\n")

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if not backlog.startswith("- [x] R2402"):
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
    heart += ("%s tick=%d R2402 product window "
              "relative_import_publish_binding shipped; battery carried\n"
              % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())