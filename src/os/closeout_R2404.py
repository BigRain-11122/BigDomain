# closeout_R2404.py - the R2404 closeout: state tick + narrative items, then
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

STAMP = "2026-11-03T05:33:00+08:00"
DO = ("R2404 followup_bare_evidence_face: the follow-up CLI now resolves a bare "
      "evidence name through the same measured pile the matrix section guards, "
      "so the operator-walked face stops answering MISSING EVIDENCE")
ART = ("qa/followup-bare-evidence-face-live-R2404.log + "
       "src/os/followup_bare_evidence_face.py")
NEXT = ("run the carried battery on this committed tree (530 suites / 4156 "
        "criteria) and then claim state/queue/tech.md:478 AC-RDPL1")

LEDGER = (
    "R2404 tokens: local=~27k api=0 api_reason=product window - one evidence "
    "resolution module and its six-criteria suite written to criteria pinned "
    "eight rounds earlier, one CLI call site rerouted with the pile law asked "
    "at CALL time, one registry wiring line, one two-leg evidence capture with "
    "three adjacent suites plus six adjacent suites re-run directly, one "
    "read-only live capture that reproduced the old root-join miss on the real "
    "tree and measured a two-level pile limit that seeded the successor row, "
    "one board stamp, one debt note folded inside the existing note at its "
    "predicted +250 bytes, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches")

LOG = [
    ("2026-11-03 R2404 product window (five-silence scan clean at open: empty "
     "git status, no .git/index.lock; LEDGER atbd_lines=0 unreplied_groups=0; "
     "DEC rows=140 tokens=92 new=0; the group orders tail stays the "
     "2026-11-02 11:04 model-policy baseline already acknowledged as "
     "non-execution; benchmarks refreshed 2026-11-02 inside the seven-day "
     "gate; floor FLOOR-MET main 5/5 tech 10/10 explore 10/10; debt gate "
     "CLAIM-FIRST item=reconcile-battery-R2394 carried since R2394). The "
     "product-first law took the window for the tenth round running and that "
     "deferral is named rather than buried: R2395..R2398 were product faces "
     "that left the battery row standing, and this window shipped the queue "
     "head the reader walked to. PRODUCT: claimed state/queue/tech.md:476 "
     "prefix AC-FBEF1 (followup_bare_evidence_face), whose AC-FBEF1..AC-FBEF6 "
     "were pinned INSIDE that row at R2396 BEFORE any code, after a fresh "
     "anchor check at HEAD (five anchors: followup_bare_evidence_face, "
     "AC-FBEF, E_FBEF, os-followup-bare-evidence-face, "
     "test_followup_bare_evidence_face - all prose-only, zero executable "
     "occupancy)."),
    ("2026-11-03 R2404 product face, what shipped: SHIPPED "
     "src/os/followup_bare_evidence_face.py plus "
     "src/os/test_followup_bare_evidence_face.py. R2396 made the matrix "
     "SECTION hand its tool the pile the guard measured, but the follow-up CLI "
     "never asked that law: battery_followup.main joined the name to the root, "
     "so `battery_followup.py --dry-run --evidence "
     "reconcile-all-R2394-retry.log` answered MISSING EVIDENCE at exit 3 and "
     "never reached a section - the defect was invisible from the only face an "
     "operator walks. One reading now answers the argument the four sections "
     "receive: a bare name resolves through matrix_evidence_pile_consistency "
     "asked at CALL time to <pile>/<basename>, a name carrying a directory is "
     "handed through byte for byte, a file that already sits at the root keeps "
     "the operator's own string so its report does not move, and a name the "
     "pile law cannot place refuses with THAT law's own code instead of a "
     "guessed pile. battery_followup.main now goes through it, which is the "
     "whole point: the CLI face and the section face name one file."),
    ("2026-11-03 R2404 evidence and board: SUITE PASS 6/6 twice with an "
     "identical criterion digest plus three adjacent suites green "
     "(qa/followup-bare-evidence-face-R2404.log, 2299B, legs=2 identical=True "
     "adjacent=3 fails=0, one utf-8 LF writer through src/os/evidence_capture.py), "
     "and six adjacent suites were re-run directly and all green "
     "(os-battery-followup 6/6, os-matrix-evidence-pile-consistency 6/6, "
     "os-bare-evidence-pile-refusal 6/6, os-battery-followup-help-wire 6/6, "
     "os-followup-section-foreign-wire 6/6, "
     "os-followup-guard-evidence-scope 6/6), wired "
     "os-followup-bare-evidence-face(6) so the registry reads 530 suites / "
     "4156 criteria. LIVE, not a plan: "
     "qa/followup-bare-evidence-face-live-R2404.log (1010B, crlf=0, bare_cr=0, "
     "one utf-8 LF writer) reads the REAL tree as bare="
     "reconcile-all-R2394-retry.log pile=qa argument=qa\\<name> exists=yes, "
     "while the OLD join root/<name> measures exists=no - exactly the MISSING "
     "EVIDENCE the seed row described; the same name WITH its directory reads "
     "unchanged=yes; the module CLI answers rc=0 on the resolvable and rc=3 "
     "E_BEPR_NOT_FOUND on a name that lives nowhere; a bad flag reads rc=5 "
     "E_FBEF_BAD_ARGS; and the module digest 4d18d15c8bebc93a is unchanged "
     "before and after. Tech row 476 stamped [done 2026-11-03 R2404] and one "
     "REAL measured gap row seeded (bare_evidence_deep_pile, AC-BEDP1..AC-BEDP6 "
     "pre-registered in that row): MEASURED this window on a stand-in root, a "
     "bare name whose only copy lives at qa/rounds/<name> reads "
     "file-exists=yes verdict=REFUSED code=E_BEPR_NOT_FOUND, because the pile "
     "measurement only walks the root and its one-level subdirectories."),
    ("2026-11-03 R2404 honest disclosures: (a) NO battery ran this window for "
     "the tenth consecutive round, so 530 suites / 4156 criteria is a WIRING "
     "count (529/4150 measured at R2403 plus this window +1 suite / +6 "
     "criteria) and the register row reconcile-battery-R2394 stays OPEN with "
     "that target folded inside its existing note at the predicted +250 bytes. "
     "That is a carried obligation, not a discharged one. (b) The suite was "
     "GREEN on its first leg after the module was written, but AC-FBEF6 went "
     "RED and the criterion was right: the reconcile label was not in the "
     "runner because the registry entry had not been added yet - the entry was "
     "added and the suite re-read 6/6 without touching the criterion. (c) The "
     "first draft of the module carried a dead conditional in exit_code() that "
     "read a key the report never sets; it was removed before the suite ran, "
     "so no leg ever measured it, and it is named here rather than left as a "
     "silent edit. (d) The tree's own two-leg capture ran BEFORE the registry "
     "line existed. The evidence file records adjacent=3 fails=0 for the three "
     "suites it names, and AC-FBEF6 re-reads the runner text at capture time "
     "afterwards; the file was NOT re-captured because its criteria text did "
     "not change and no digest is claimed for it. (e) tasks.md was left "
     "untouched: it is the P-47 canonical board and carries no row for this "
     "tech slice."),
    ("2026-11-03 R2404 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
     "forbids for every lane task; src/os/register_loop_task.ps1 already "
     "passes an explicit S4U principal but needs an elevated shell, and this "
     "session is unelevated, so the task definition was left untouched "
     "(hundred-and-fifty-ninth consecutive disclosure, carried as the stale "
     "row loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2404 product window: followup_bare_evidence_face - the matrix "
    "section already handed its tool the measured pile, but the follow-up CLI "
    "joined a bare evidence name to the root, so `--evidence "
    "reconcile-all-R2394-retry.log` answered MISSING EVIDENCE at exit 3 and "
    "never reached a section (measured at R2396, reproduced live this window: "
    "root/<name> exists=no while qa/<name> exists=yes). SHIPPED "
    "src/os/followup_bare_evidence_face.py plus its six-criteria suite: one "
    "reading answers the argument the four sections receive, asking "
    "matrix_evidence_pile_consistency at CALL time, so a bare name resolves to "
    "<pile>/<basename>, a directory-carrying name is handed through byte for "
    "byte, a root-resident name keeps the operator's own string, and an "
    "unplaceable name refuses with the pile law's own code. SUITE PASS 6/6 "
    "twice identical plus three adjacent suites green "
    "(qa/followup-bare-evidence-face-R2404.log, 2299B, legs=2 identical=True "
    "adjacent=3 fails=0) and six adjacent suites green when re-run directly, "
    "wired os-followup-bare-evidence-face(6) so the registry reads 530/4156. "
    "LIVE: qa/followup-bare-evidence-face-live-R2404.log reads pile=qa "
    "argument=qa\\<name> exists=yes against OLD-JOIN exists=no, CLI rc=0/3/5 "
    "by case, digest unchanged. Board: row 476 stamped and one measured gap "
    "row seeded (bare_evidence_deep_pile AC-BEDP1..6: a bare name at "
    "qa/rounds/<name> still refuses E_BEPR_NOT_FOUND though it exists), floor "
    "FLOOR-MET 5/5 10/10 10/10. No battery ran: reconcile-battery-R2394 stays "
    "OPEN at 530 suites / 4156 criteria.\n")

ROW_TEXT = ("R2404 followup_bare_evidence_face shipped - the follow-up CLI "
            "resolves a bare evidence name through the measured pile (live: "
            "qa/<name> exists=yes where the old root join read exists=no); "
            "registry 530/4156")


def write_atomic(path, text):
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".r2404-",
                                   suffix=".tmp")
    with os.fdopen(handle, "wb") as sink:
        sink.write(text.encode("utf-8"))
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, path)


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
    stamped = tech.count("- [x] [done 2026-11-03 R2404]")
    seeded = tech.count("AC-BEDP1..AC-BEDP6")
    if stamped != 1 or seeded < 1:
        sys.stdout.write("E_BOARD stamped=%d bedp=%d\n" % (stamped, seeded))
        return 2
    sys.stdout.write("BOARD verified stamped=1 seed_mentions=%d\n" % seeded)

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if not backlog.startswith("- [x] R2404"):
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
    heart += ("%s tick=%d R2404 product window followup_bare_evidence_face "
              "shipped; battery carried\n" % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())