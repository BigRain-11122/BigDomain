"""R2429 closeout: state tick, log lines, export face, backlog, heartbeat."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
STATE = os.path.join(SRC, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
PATTERNS = os.path.join(SRC, "export_consistency_patterns.json")
BACKLOG = os.path.join(SRC, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")
STAMP = "2026-11-04T06:44:25+08:00"
ROUND = 2429
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2429 verification window (five-silence scan clean at open: git status empty at HEAD 6e419140 with no .git/index.lock; the evolution ledger carries zero @BigDomain handoff rows; the content-addressed decisions diff read 157 rows and 105 tokens with new=0 against the stored baseline; the group orders tail max_ts is 2026-11-04 00:46, equal to the stored last_order, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 explore 10/10 with tech head line 492 prefix AC-PICBS1 claimable=10). The debt gate named CLAIM-FIRST item=reconcile-battery-R2429 opened=R2428 carried=1 at the MEASURED target 542 suites / 4228 criteria, so the battery ran FIRST on the committed tree with zero product edits.",
    "2026-11-04 R2429 the first battery leg came back RED ON EVIDENCE, NOT CODE: 541/542 suites green with the criteria total 4228 EXACTLY as pre-registered (qa/reconcile-all-R2429.log kept as the honest red leg, 843117B, TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0), the only red suite being reconcile-daily-census at cd7-live-real-tree exit=2 label=drift where the criterion pre-registers exit=0. qa_writer_census --check named the file and the dialect instead of leaving a guess: qa/comma-binding-consumer-wire-live-R2428.log read class=other over a utf-8 body carrying ONE CRLF line among 19 bare LF ones, i.e. the transport of an ad-hoc live capture, with the payload intact - all six readings the R2428 round reported are present in the file.",
    "2026-11-04 R2429 repair at the BIRTH SITE, never by widening the baseline: src/os/repair_R2429.py asks the shipped run_identity.normalize for the allowed normalisation, proves the line set identical on both sides BEFORE the write, lands utf-8 LF through one atomic replace and reads the bytes back - 1644B -> 1643B, crlf=0, lone_cr=0, 21 lines, readback=ok - after which the census reads files=2483 tee=1954 baselined=529 disappeared=0 flags=0 verdict=DRIFT-CLEAN with the baseline file UNTOUCHED, and the repair was committed ALONE as 32c64f9a before any further byte changed.",
    "2026-11-04 R2429 the retry leg then ran on the committed repair tree: python src/os/battery_stream.py --evidence qa/reconcile-all-R2429-retry.log read RUNNER PASS (542/542 suites green, reconcile controls 7/7, 1099.2s) with a measured criteria total of 4228 - the pre-registered number to the unit - and TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB; the evidence file is 843138B and the census re-read DRIFT-CLEAN after it.",
    "2026-11-04 R2429 the four follow-up sections produced the designed first FAIL and then a green verdict: leg 1 read VERDICT FAIL failing=matrix at on-disk=52086B against regenerated=52215B and wrote no byte, src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round's green evidence through --stamp-from so the render is stamp-aligned to the doc it is compared with, --check read byte-identical at 52215B / 542 suites / 4228 criteria, and the re-run read VERDICT R2429 PASS failing=none (matrix byte-identical 52215B, fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN). Both legs stay appended in the retry evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",
    "2026-11-04 R2429 debt register after this window: open=2 done=143. reconcile-battery-R2429 was closed through the shipped debt_close at its predicted 106200B -> 106203B (measured exactly, line=163, readback=ok) and ONE leader row product-face-R2430 was appended first=yes through the shipped debt_append at 106203B -> 106530B (readback=ok), naming the next window a product face on the tech head state/queue/tech.md:492 prefix AC-PICBS1 (comma_binding_sibling_faces) whose AC-PICBS1..AC-PICBS6 were pinned at R2428 BEFORE any code. NO successor battery was registered: this window's only src write is the one-off repair_R2429.py, which is registered as no suite and moves neither the suite nor the criteria count (the registry still reads 542 / 4228), so the R2168 mixed-tree rule does not fire. Remaining open: loop-s4u-reconcile and product-face-R2430.",
    "2026-11-04 R2429 honest disclosures: (a) this window shipped ZERO product code and claims zero product points - the battery consumed the window exactly as the carried row said it would, and the R2168 mixed-tree rule makes a product edit inside a verification window invalidate the measurement the window exists to produce; (b) the red is the THIRD transport defect the census station has caught and nothing else did, this one a single CRLF line inside an otherwise clean utf-8 LF body; (c) MEASURED and named rather than repeated - the R2428 closeout recorded that live capture at 2763B while the file on disk measured 1644B before this repair and 1643B after it, so that byte count was itself wrong and is corrected here, the same class of error R2423 disclosed; (d) git reported this repair as ONE file changed because the tracked blob for that qa log had already been normalised to LF by the checkin filter, so the repair is real on disk - where the census reads raw bytes - while no blob moved, and that is said rather than dressed up as a content change; (e) the first debt_append call was refused E_DEBTA_BAD_FIELD on the longer note and the shipped CLI was retried with a shorter note instead of editing the register by hand; (f) the window ran far past its 25-minute budget - the red leg plus the retry leg plus the regeneration leg cost well over 35 minutes of battery time - named rather than hidden; (g) tasks.md was not touched, it is the P-47 canonical board and carries no row for this verification window.",
    "R2429 tokens: local=~17k api=0 api_reason=verification window - one full battery on the committed tree at a pre-registered target (542 suites / 4228 criteria) that came back red on a single CRLF line in an evidence log, one birth-site repair through the shipped normalisation law with the payload proved and committed alone, one retry battery to RUNNER PASS at the same criteria count, four follow-up sections with one designed matrix FAIL and one green verdict after a stamp-aligned regeneration, one debt row closed and one leader row opened through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero product code shipped, zero cloud calls and zero external API touches",
    "2026-11-04 R2429 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-seventh consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

EXPORT_DO = (
    "R2429 verification window: the full reconcile battery ran on the "
    "committed R2428 tree at the pre-registered 542 suites / 4228 criteria, "
    "came back red on one CRLF line inside a live-capture evidence log, was "
    "repaired at the birth site through run_identity.normalize with the "
    "payload proved identical, and the retry leg then read RUNNER PASS "
    "542/542 at the same criteria total with all four follow-up sections "
    "green"
)
EXPORT_ARTIFACT = (
    "qa/reconcile-all-R2429.log (red leg, 843117B) + qa/reconcile-all-R2429-"
    "retry.log (RUNNER PASS 542/542, 1099.2s, 843138B) + docs/sandbox-suite-"
    "matrix.md regenerated to 52215B at 542 suites / 4228 criteria with "
    "--check byte-identical + src/os/repair_R2429.py (birth-site dialect "
    "repair, 1644B -> 1643B, crlf=0, readback=ok)"
)
EXPORT_MILESTONE = (
    "product face on the tech head the reader names: state/queue/tech.md:492 "
    "prefix AC-PICBS1 (comma_binding_sibling_faces, AC-PICBS1..AC-PICBS6 "
    "pinned at R2428) - export_publish_from_import_law and "
    "publish_relative_package_identity still read UNRESOLVED on the comma-list "
    "fixture the identity face now resolves"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2429] R2429 verification window: the debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2429 at the measured 542 suites "
    "/ 4228 criteria, so the battery ran FIRST on the committed 6e419140 tree "
    "with zero product edits. Leg 1 was RED ON EVIDENCE, NOT CODE - 541/542 "
    "suites with criteria 4228 exactly as pre-registered, the only red being "
    "reconcile-daily-census cd7-live-real-tree exit=2 - and qa_writer_census "
    "named the file: qa/comma-binding-consumer-wire-live-R2428.log carried ONE "
    "CRLF line inside a utf-8 LF body (class=other), payload intact. Repaired "
    "at the birth site through run_identity.normalize with the line set proved "
    "identical before the write and a read-back after it (1644B -> 1643B, "
    "crlf=0, lone_cr=0) and committed alone as 32c64f9a; the census then read "
    "DRIFT-CLEAN files=2483 tee=1954 baselined=529 flags=0 with the baseline "
    "UNTOUCHED. The retry leg on the committed repair tree read RUNNER PASS "
    "542/542 plus controls 7/7 in 1099.2s at criteria 4228 - the pre-registered "
    "number to the unit - and the four follow-up sections produced the designed "
    "matrix FAIL (on-disk 52086B vs regenerated 52215B, no rewrite) then a "
    "green verdict after a stamp-aligned regeneration (byte-identical 52215B, "
    "fingerprint CLEAN, profile byte-identical, census DRIFT-CLEAN). Register: "
    "battery row closed at its predicted 106200B -> 106203B and "
    "product-face-R2430 opened first=yes at 106203B -> 106530B. Zero product "
    "code shipped, honestly 0 product points.\n",
    "- [ ] [carried 2026-11-04 R2429] R2430 first item: PRODUCT FACE on the "
    "row the reader names - state/queue/tech.md:492 prefix AC-PICBS1 "
    "(comma_binding_sibling_faces), whose AC-PICBS1..AC-PICBS6 were pinned at "
    "R2428 BEFORE any code. Re-read the row rather than trusting this line and "
    "run a fresh zero-occupancy anchor check at HEAD. Measured gap: on the "
    "comma-list fixture the identity face now reads WIRE while "
    "export_publish_from_import_law --check and "
    "publish_relative_package_identity --check still read UNRESOLVED rc=2. "
    "Still carried: loop-s4u-reconcile needs an ELEVATED shell.\n",
]


def _read(path, newline=None):
    with io.open(path, "r", encoding="utf-8", newline=newline) as handle:
        return handle.read()


def _write(path, text, newline=""):
    with io.open(path, "w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)


def step_state():
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import state_io
    state = json.loads(_read(STATE))
    before = state["tick"]
    state["tick"] = before + 1
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = STATE + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, STATE)
    back = json.loads(_read(STATE))
    if back["tick"] != state["tick"] or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    size = os.path.getsize(STATE)
    print("state tick %d -> %d lines=%d bytes=%d"
          % (before, state["tick"], len(state["log"]), size))
    if size > GATE - RESERVE:
        print("WARNING state above gate-reserve, a fold window is due")


def step_export():
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
            if "reconcile-all-R2429" not in str(item)]
    outs.insert(0, EXPORT_ARTIFACT)
    export["outs"] = outs
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    import check_export_consistency
    derived = check_export_consistency.recompute()[0]
    drive = export["self_drive"]
    drive["log_lines_in_window"] = derived["log_lines_in_window"]
    drive["substantive_non_idle_mention_lines"] = \
        derived["substantive_non_idle_mention_lines"]
    import queue_floor
    gauge = queue_floor.gauge(ROOT)
    fresh = dict((row["queue"], row) for row in gauge["queues"])
    for row in export["queue"]["queues"]:
        live_row = fresh.get(row.get("queue"))
        if not live_row:
            continue
        for key, value in live_row.items():
            row[key] = value
    export["queue"]["floors"] = gauge["floors"]
    export["queue"]["verdict"] = gauge["verdict"]
    text = json.dumps(export, ensure_ascii=False, indent=2) + "\n"
    _write(EXPORT, text, newline="\n")
    print("export refreshed %dB queues=%s"
          % (len(text.encode("utf-8")), gauge["verdict"]))


def step_backlog():
    text = _read(BACKLOG)
    added = 0
    for row in BACKLOG_ROWS:
        head = row.split("] ")[0] + "]"
        if head in text and row.split(": ")[0][:60] in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        text += row
        added += 1
    _write(BACKLOG, text, newline="\n")
    print("backlog rows added=%d bytes=%d"
          % (added, len(text.encode("utf-8"))))


def step_heartbeat():
    line = ("2026-11-04T06:44:25+08:00 tick=2429 R2429 verification window - "
            "battery red then green: leg 1 read 541/542 on one CRLF line inside "
            "a live-capture evidence log, repaired at birth site through "
            "run_identity.normalize with payload proved and committed alone, "
            "retry RUNNER PASS 542/542 at criteria 4228 exactly as "
            "pre-registered, four follow-up sections green after a stamp-aligned "
            "matrix regeneration, battery row closed and product-face-R2430 "
            "opened")
    text = _read(HEARTBEAT)
    if line in text:
        print("heartbeat line already present")
        return
    if not text.endswith("\n"):
        text += "\n"
    _write(HEARTBEAT, text + line + "\n", newline="\n")
    print("heartbeat appended")


if __name__ == "__main__":
    step_state()
    step_export()
    step_backlog()
    step_heartbeat()