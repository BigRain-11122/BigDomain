# closeout_R2405.py - the R2405 verification closeout: the carried battery
# ran on the committed tree, so this window closes its debt row, opens the
# successor, then lands the ledger line THROUGH ledger_line_shape_guard's own
# door, re-derives the export face from the live tree and stamps heartbeat.
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
DEBT = os.path.join(REPO, "state", "debt.md")
EVIDENCE = os.path.join(REPO, "qa", "reconcile-all-R2405-retry.log")
RED_LEG = os.path.join(REPO, "qa", "reconcile-all-R2405.log")

STAMP = "2026-11-03T06:24:00+08:00"
DO = ("R2405 verification: the carried battery ran GREEN on the committed "
      "tree (530/530 suites, 4156 criteria exactly as registered, 1077.7s) "
      "after two birth-site evidence defects were repaired and committed "
      "alone")
ART = ("qa/reconcile-all-R2405-retry.log + qa/reconcile-all-R2405.log")
NEXT = ("claim state/queue/tech.md:478 AC-RDPL1 (repin_dialect_preservation) "
        "and seed its successor")

LEDGER = (
    "R2405 tokens: local=~30k api=0 api_reason=verification window - the "
    "carried reconciling battery ran on the committed tree twice, the first "
    "leg measured two real birth-site evidence defects (a mixed-dialect live "
    "capture and an orphaned retry family), both were repaired and committed "
    "alone, the retry read RUNNER PASS 530/530 suites with criteria 4156 "
    "exactly as pre-registered in 1077.7s, four follow-up sections plus a "
    "regenerated 51024B matrix read VERDICT R2405 PASS, and the debt row was "
    "closed with its successor opened; zero cloud calls and zero external "
    "API touches")

LOG = [
    ("2026-11-03 R2405 verification window (five-silence scan at open: clean "
     "git status, no .git/index.lock; the ledger carries no unreplied "
     "BigDomain handoff; DEC tokens=92 new=0 against the baseline; the group "
     "orders tail gained OB-20261102-2015-CPUFULL at 2026-11-02 20:15 after "
     "the 11:04 baseline, receipt below; benchmarks refreshed 2026-11-02 "
     "inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 "
     "explore 10/10; debt gate CLAIM-FIRST item=reconcile-battery-R2394 "
     "carried since R2394, deferred for eleven product rounds). The debt gate "
     "had first claim, so the battery ran FIRST with zero product edits (the "
     "R2168 mixed-tree rule)."),
    ("2026-11-03 R2405 battery red leg: RUNNER FAIL 528/530 suites in 988.5s "
     "with two real red suites and no code change from this window "
     "(qa/reconcile-all-R2405.log, 836966B, crlf=0, single writer through "
     "src/os/battery_stream.py). Both were birth-site evidence defects, not "
     "product regressions: (a) reconcile-daily-census cd7 read DRIFT-FLAG "
     "because qa/export-publish-from-import-law-live-R2400.log carried two "
     "CRLF lines inside an 18-LF body (class=other), so the file was "
     "normalized through src/os/evidence_writer.py --fix - payload proved "
     "equal before and after, class now tee, crlf=0, census DRIFT-CLEAN "
     "files=2439 tee=1910 flags=0; (b) os-followup-retry-history refused "
     "E_FRTL_ORPHAN_RETRY because qa/reconcile-all-R2394-retry.log had no "
     "canonical sibling - the R2394 first leg was named R2394b, so the retry "
     "family was orphaned. The file was renamed to its canonical name "
     "reconcile-all-R2394.log with its SHA256 proved identical, and both "
     "suite files then read 8/8 and 6/6 green directly."),
    ("2026-11-03 R2405 evidence repairs committed alone (043f5982) before any "
     "battery retry, and the red leg was preserved rather than deleted. The "
     "retry then read RUNNER PASS (530/530 suites green, reconcile controls "
     "7/7, 1077.7s) in qa/reconcile-all-R2405-retry.log (835510B before the "
     "follow-up append, crlf=0, class=tee), criteria total 4156 exactly as "
     "pre-registered by reading the registry BEFORE the run. Four follow-up "
     "sections ran through src/os/battery_followup.py: matrix first FAILED on "
     "the stale doc and did not rewrite it, suite_matrix regenerated "
     "docs/sandbox-suite-matrix.md to 51024B (530 suites / 4156 criteria, "
     "green=530/530), and the re-run read matrix byte-identical, fingerprint "
     "CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN for "
     "VERDICT R2405 PASS failing=none; the sections were appended (1950B, "
     "eol_ok=True)."),
    ("2026-11-03 R2405 order receipt OB-20261102-2015-CPUFULL (group order "
     "2026-11-02 20:15, CPU full-load across the fleet): read and acknowledged "
     "by number. This company's executable lane is the five-minute OSLoop; it "
     "owns no CPU training queue, so the order names no new local job here and "
     "the CPU work it describes belongs to the fleet compute lanes, not this "
     "repository. No numbered handoff to BigDomain accompanies it in the group "
     "ledger. No action taken beyond this receipt."),
    ("2026-11-03 R2405 honest disclosures: (a) the first probe of this window "
     "ran `reconcile_all.py --help`, which is not a supported flag and became "
     "an evidence path, writing a file literally named --help - the second "
     "recorded occurrence of the R2394 trap; the file was removed before any "
     "commit and no suite ever read it. (b) The same probe was piped through "
     "Select-Object -Last, which buffered all output and got the run cancelled "
     "at the five-minute no-output gate; the real runs used the unbuffered "
     "streamer, and this is named rather than left as a silent retry. (c) The "
     "rename of R2394b to R2394 changes a historical evidence FILENAME while "
     "its bytes are proved identical by SHA256; it is a naming repair, not an "
     "evidence rewrite, and the old name is still quoted in the R2394 log "
     "prose. (d) No product module shipped this window and none is claimed: "
     "the battery was the work."),
    ("2026-11-03 R2405 self-heal check: BigDomain-OSLoop is still registered "
     "with LogonType=InteractiveToken, which the 2026-09-29 machine law "
     "forbids for every lane task; src/os/register_loop_task.ps1 already "
     "passes an explicit S4U principal but needs an elevated shell, and this "
     "session is unelevated, so the task definition was left untouched "
     "(hundred-and-sixtieth consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile in state/debt.md)."),
]

BACKLOG_ROW = (
    "- [x] R2405 verification window: the carried battery ran on the "
    "committed tree. Leg 1 read RUNNER FAIL 528/530 in 988.5s with two real "
    "birth-site evidence defects: a mixed-dialect R2400 live capture "
    "(class=other, 2 CRLF lines in an 18-LF body) and an orphaned retry "
    "family (qa/reconcile-all-R2394-retry.log had no canonical sibling "
    "because the R2394 first leg was named R2394b). Both repaired at birth "
    "and committed ALONE as 043f5982 - the capture normalized through "
    "src/os/evidence_writer.py with its payload proved equal, the leg renamed "
    "to reconcile-all-R2394.log with its SHA256 proved identical - and the "
    "red leg preserved. Retry: RUNNER PASS 530/530 suites plus controls 7/7 "
    "in 1077.7s, criteria 4156 exactly as pre-registered, qa/"
    "reconcile-all-R2405-retry.log (class=tee, crlf=0); matrix regenerated "
    "to 51024B (530/4156 green) after the designed first FAIL; four "
    "follow-up sections PASS, VERDICT R2405 PASS appended (1950B, "
    "eol_ok=True). Debt row reconcile-battery-R2394 closed and successor "
    "reconcile-battery-R2405 opened at 530/4156. Floor FLOOR-MET 5/5 10/10 "
    "10/10. No product module shipped and none is claimed.\n")

ROW_TEXT = ("R2405 verification window - battery green on the committed tree "
            "(530/530 suites, 4156 criteria, 1077.7s) after two evidence "
            "defects were repaired and committed alone; four follow-ups PASS")


def write_atomic(path, text):
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".r2405-",
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


def fix_debt():
    text = io.open(DEBT, encoding="utf-8", newline="").read()
    marker = "- [ ] opened=R2394 | item=reconcile-battery-R2394 |"
    if marker not in text:
        sys.stdout.write("E_DEBT marker missing\n")
        return 2
    lines = text.splitlines(True)
    out = []
    closed = False
    opened = False
    for line in lines:
        if line.startswith(marker):
            body = line.rstrip("\n")
            body += (" | closed=R2405 | closing note=the battery ran on the "
                     "committed tree this window: leg 1 red 528/530 on two "
                     "birth-site evidence defects (mixed-dialect R2400 live "
                     "capture, orphaned R2394 retry family) both repaired and "
                     "committed alone as 043f5982, leg 2 green RUNNER PASS "
                     "530/530 suites with criteria 4156 exactly as registered "
                     "in 1077.7s (qa/reconcile-all-R2405-retry.log), four "
                     "follow-up sections plus a 51024B matrix read VERDICT "
                     "R2405 PASS")
            line = body.replace("- [ ]", "- [x]", 1) + "\n"
            closed = True
        out.append(line)
        if closed and not opened and line.startswith("- [x] opened=R2394"):
            out.append(
                "- [ ] opened=R2405 | item=reconcile-battery-R2405 | "
                "first=yes | note=the battery for the CURRENT tree ran GREEN "
                "this window (530 suites / 4156 criteria, RUNNER PASS "
                "530/530 plus controls 7/7 in 1077.7s in "
                "qa/reconcile-all-R2405-retry.log, follow-ups VERDICT R2405 "
                "PASS). No product change followed it, so the successor "
                "target is 530 suites / 4156 criteria until a product window "
                "adds a suite; runs FIRST next window on the committed tree "
                "with zero product edits.\n")
            opened = True
    if not closed or not opened:
        sys.stdout.write("E_DEBT closed=%s opened=%s\n" % (closed, opened))
        return 2
    write_atomic(DEBT, "".join(out))
    sys.stdout.write("DEBT closed=R2394 opened=R2405 bytes=%d\n"
                     % os.path.getsize(DEBT))
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

    for path, needle in ((EVIDENCE, "VERDICT R2405 PASS"),
                         (EVIDENCE, "RUNNER PASS (530/530 suites green"),
                         (RED_LEG, "RUNNER FAIL")):
        if not os.path.exists(path):
            sys.stdout.write("E_EVIDENCE missing %s\n" % os.path.basename(path))
            return 2
        blob = io.open(path, encoding="utf-8", errors="replace").read()
        if needle not in blob:
            sys.stdout.write("E_EVIDENCE %s lacks %r\n"
                             % (os.path.basename(path), needle))
            return 2
    sys.stdout.write("EVIDENCE red leg preserved and retry green with follow-ups\n")

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if not backlog.startswith("- [x] R2405"):
        write_atomic(BACKLOG, BACKLOG_ROW + backlog)
        sys.stdout.write("BACKLOG row prepended\n")

    if fix_debt() != 0:
        return 2

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
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = STAMP
    write_atomic(EXPORT, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.write("EXPORT refreshed bytes=%d\n" % os.path.getsize(EXPORT))

    heart = io.open(HEART, encoding="utf-8", newline="").read()
    if not heart.endswith("\n"):
        heart += "\n"
    heart += ("%s tick=%d R2405 verification window - battery green on the "
              "committed tree after two evidence repairs\n"
              % (STAMP, final["tick"]))
    write_atomic(HEART, heart)
    sys.stdout.write("HEARTBEAT appended\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())