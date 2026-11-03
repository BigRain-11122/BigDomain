"""R2428 closeout: state tick, log lines, export face, backlog, heartbeat."""
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
STAMP = "2026-11-04T05:56:00+08:00"
ROUND = 2428
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2428 product window (five-silence scan clean at open: git status empty at HEAD with no index.lock; the evolution ledger carries zero @BigDomain rows; the content-addressed decisions diff read new=0 against the stored 105-token baseline over 208 rows; the group orders tail max_ts is still 2026-11-04 00:46, equal to last_order, so no new order; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor main 6/5 tech 11/10 explore 10/10 FLOOR-MET with tech head line 491 prefix AC-PICBC1 claimable). The debt gate named CLAIM-FIRST item=product-face-R2428 and the anchor check at HEAD put comma_binding_consumer_wire / AC-PICBC / E_PICBC / os-comma-binding-consumer-wire / test_comma_binding_consumer_wire only in prose and state, zero executable occupancy.",
    "2026-11-04 R2428 SHIPPED src/os/comma_binding_consumer_wire.py plus src/os/test_comma_binding_consumer_wire.py against AC-PICBC1..AC-PICBC6, and moved ONE call site: export_publish_wire_identity.audit_script now asks comma_binding_consumer_wire.wire_audit_script at CALL time. That seam hands a file with NO comma list to export_publish_from_import_law.classify_script unchanged and a file WITH one to the same law classify_line over comma_binding_wire.bindings, so the split, the import grammar and the spelling law each keep exactly one owner. Wired os-comma-binding-consumer-wire(6); the registry MEASURES 542 suites / 4228 criteria, read from reconcile_all.SUITES rather than predicted.",
    "2026-11-04 R2428 the defect is closed with numbers, not described: on one fixture the HEAD identity module reads verdict=UNRESOLVED rc=2 naming comma_pub.py:7 module=(unbound) while the shipped reader reads verdict=WIRE rc=0 naming module=closeout_export_parity_wire, and on the REAL src/os both read WIRE 11/11 with 22 no_publish over 1180 scripts, unchanged. SUITE PASS 6/6 twice with an identical digest plus three adjacent suites green (qa/comma-binding-consumer-wire-R2428.log, 1594B, legs=2 identical=True adjacent=3 fails=0). LIVE qa/comma-binding-consumer-wire-live-R2428.log (2763B) carries the five readings above plus the refusals missing root rc=3 E_PICBC_NO_ROOT and bad flag rc=5 E_PICBC_BAD_FLAGS.",
    "2026-11-04 R2428 board: tech row 491 stamped `[done 2026-11-04 R2428]` with its delivery narrative outside the bracket through src/os/queue_R2428.py, and ONE measured gap row seeded beneath it - comma_binding_sibling_faces (AC-PICBS1..AC-PICBS6), because the SAME fixture measured this window still reads UNRESOLVED rc=2 on export_publish_from_import_law --check and on publish_relative_package_identity --check: the consumer reached the identity face only. queue_head now names line 492 prefix AC-PICBS1 and the gauge stays FLOOR-MET main 6/5 tech 11/10 explore 10/10. Debt register after this window: open=2 done=142, product-face-R2428 closed through the shipped debt_close at its predicted 105512B -> 105515B (readback=ok) and reconcile-battery-R2429 appended first=yes through the shipped debt_append at 105515B -> 106200B (readback=ok) at the measured 542/4228 target.",
    "2026-11-04 R2428 honest disclosures: (a) ONE pre-existing assertion was re-anchored at its birth site with the reason written beside it: test_comma_binding_wire AC-PICBW5 asserted whole-FILE byte equality between the identity module and its HEAD copy, which would have forbidden the very consumer this seed asked for; it now proves refusal codes, exit codes, printed lines and the unchanged row key set, which is what that criterion words - every other assertion was left alone and the suite reads 6/6; (b) the operator error R2427 disclosed repeated here: `python src/sandbox/reconcile_all.py --help` is not a help flag, the runner took `--help` as an evidence path and wrote a file literally named `--help` (13859B) in the repo root - the pipe closed, no python process survived (verified by command line), the stray file was deleted and git status returned to the intended set; (c) the first suite run was RED on AC-PICBC3 because the test expected the three-fixture pile to read WIRE while the bare spelling correctly has no binding - the assertion was set to the measured UNRESOLVED rc=2, no criterion widened; (d) NO battery ran - the R2168 mixed-tree rule makes a battery inside a product window measure a tree about to change, and it is registered as R2429 first=yes; (e) tasks.md untouched, it is the P-47 canonical board and carries no row for this tech slice.",
    "R2428 tokens: local=~24k api=0 api_reason=product window - one consumer module and its six-criteria suite against criteria pinned at R2426, one identity call-site change, one birth-site assertion re-anchor with its reason, one runner wiring line, one two-leg evidence capture with three adjacent suites, one live capture over 1180 real files plus the HEAD-vs-shipped fixture comparison, one board stamp with one measured sibling-face gap seeded, one debt row closed and the successor battery registered through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-04 R2428 self-heal check: BigDomain-OSLoop still exists and its Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell and this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]

EXPORT_DO = (
    "R2428 product window: src/os/comma_binding_consumer_wire.py puts the "
    "comma-aware binding table on the identity path - a comma-list publisher "
    "now reads WIRE with its module instead of UNRESOLVED, while every file "
    "without a comma list keeps its rows byte for byte; suite 6/6 twice with "
    "three adjacent suites green and the registry measured at 542 suites / "
    "4228 criteria"
)
EXPORT_ARTIFACT = (
    "src/os/comma_binding_consumer_wire.py + "
    "src/os/test_comma_binding_consumer_wire.py + "
    "qa/comma-binding-consumer-wire-R2428.log (1594B, legs=2 identical=True "
    "adjacent=3 fails=0) + qa/comma-binding-consumer-wire-live-R2428.log "
    "(HEAD UNRESOLVED rc=2 vs shipped WIRE rc=0 on one fixture; real tree "
    "WIRE 11/11)"
)
EXPORT_MILESTONE = (
    "full reconcile battery on the committed R2428 tree with zero product "
    "edits at the measured 542 suites / 4228 criteria, then the product face "
    "the queue head names: state/queue/tech.md:492 prefix AC-PICBS1 "
    "(comma_binding_sibling_faces, AC-PICBS1..AC-PICBS6 seeded at R2428) - "
    "export_publish_from_import_law and publish_relative_package_identity "
    "still read UNRESOLVED for the same comma-list fixture the identity face "
    "now resolves"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2428] R2428 product window: the debt gate named "
    "CLAIM-FIRST item=product-face-R2428 and the anchor check at HEAD found "
    "zero executable occupancy, so src/os/comma_binding_consumer_wire.py plus "
    "its six-criteria suite shipped against AC-PICBC1..AC-PICBC6 (pinned at "
    "R2426 in state/queue/tech.md line 491). The identity path now consumes "
    "the comma-aware table through ONE seam (identity audit_script asks "
    "wire_audit_script at CALL time): a file with no comma list is handed to "
    "the shipped from-import law unchanged and a file with one to the same "
    "law classify_line over comma_binding_wire.bindings, so no split, import "
    "grammar or spelling law is restated. MEASURED LIVE: HEAD identity reads "
    "UNRESOLVED rc=2 on the comma-list fixture where the shipped reader reads "
    "WIRE rc=0 with module=closeout_export_parity_wire; the real src/os reads "
    "WIRE 11/11 with 22 no_publish on both, unchanged. SUITE PASS 6/6 twice "
    "identical plus three adjacent suites green (qa/comma-binding-consumer-"
    "wire-R2428.log, 1594B) and the registry MEASURED at 542 suites / 4228 "
    "criteria. Two product points. Board: row 491 stamped, one measured "
    "sibling-face gap seeded (comma_binding_sibling_faces, AC-PICBS1..6), "
    "floor FLOOR-MET. Battery NOT run: registered as R2429 first=yes at "
    "542/4228.\n",
    "- [ ] [carried 2026-11-04 R2428] R2429 first item: THE BATTERY ON THE "
    "COMMITTED R2428 TREE, zero product edits until green (the R2168 "
    "mixed-tree rule). Pre-registered target MEASURED from the registry this "
    "window: 542 suites / 4228 criteria. Regenerate docs/sandbox-suite-matrix."
    "md only from that green evidence, then the four follow-up sections "
    "through src/os/battery_followup.py. After green, resume the product face "
    "on the tech head the reader names (line 492 prefix AC-PICBS1, "
    "comma_binding_sibling_faces). Still carried: loop-s4u-reconcile (needs an "
    "ELEVATED shell) and the flag-shaped-evidence-path operator trap measured "
    "again this window.\n",
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
            if "comma_binding_consumer_wire" not in str(item)]
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
    line = ("2026-11-04T05:56:00+08:00 tick=2428 R2428 product window - "
            "comma_binding_consumer_wire shipped against AC-PICBC1..6 with "
            "suite 6/6 twice plus three adjacent suites green, registry "
            "measured at 542 suites / 4228 criteria, identity face now reads "
            "WIRE where HEAD read UNRESOLVED, board stamped with one sibling "
            "gap seeded, battery registered as R2429 first=yes")
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