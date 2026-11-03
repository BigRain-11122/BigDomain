"""R2426 closeout: state tick, log lines, export face, backlog, heartbeat."""
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
STAMP = "2026-11-04T05:16:00+08:00"
ROUND = 2426
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2426 product window (five-silence scan clean at open: git status empty at HEAD 231de093 with no .git/index.lock; the evolution ledger carries zero @BigDomain rows; the content-addressed decisions diff read 157 rows and 105 tokens with new=0 against the stored baseline; the group orders tail max_ts is the 2026-11-04 00:46 OB-20261104-004657-271 de-AI line already judged not-this-company, so the baseline stands; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 explore 10/10 with tech head line 490 prefix AC-PICBW1 claimable=10). The debt gate named CLAIM-FIRST item=product-face-R2426 and the anchor check at HEAD put comma_binding_wire / AC-PICBW / E_PICBW only in prose and state (backlog, closeout_R2424, closeout_R2425, queue_R2424), zero executable occupancy, so the criteria pinned at R2424 were built against.",
    "2026-11-04 R2426 SHIPPED src/os/comma_binding_wire.py plus src/os/test_comma_binding_wire.py against AC-PICBW1..AC-PICBW6, wired os-comma-binding-wire(6) so the registry MEASURES 541 suites / 4222 criteria (540/4216 at R2425 plus this window one suite and six criteria, read from reconcile_all.SUITES, not predicted). ONE seam is closed and no law is added: the parts of a comma list are asked of the SHIPPED splitter (plain_import_comma_binding.parts_of), the per-part question is the SHIPPED composition (part_statement), the receiver table is export_publish_wire_identity.import_bindings and the callee law is that same module own callee_of - all at CALL time, with the suite proving it by patching the splitter and the table and watching the row move, so there is still exactly one import table and one publish-call law in the tree.",
    "2026-11-04 R2426 the defect is named with numbers, not described: on `import os, some_wire as wiremod` plus `wiremod.publish(...)` the shipped table binds {'os': 'os'} only, callee_of answers module '' and the identity reading answers UNRESOLVED, while this wire answers module some_wire and reads BOUND (resolved=1 unresolved=0 at exit 0). SUITE PASS 6/6 twice with an identical digest plus three adjacent suites green (qa/comma-binding-wire-R2426.log, 1626B, legs=2 identical=True adjacent=3 fails=0). LIVE qa/comma-binding-wire-live-R2426.log reads the REAL src/os as verdict=EMPTY scanned=1175 compared=1173 parity=1167 comma_files=6 comma_lines=6 resolved=0 unresolved=0 - six comma lists exist but none binds a publisher, so this window claims the GUARD and does NOT claim a live catch - while a fixture in the same log reads RESOLVED with table_module=(unbound) beside wire_module=some_wire.",
    "2026-11-04 R2426 board: tech row 490 stamped `[done 2026-11-04 R2426]` with its delivery narrative outside the bracket through src/os/queue_R2426.py, and ONE measured gap row seeded beneath it - comma_binding_consumer_wire (AC-PICBC1..AC-PICBC6), because the same live log measures that the identity face on that very fixture still answers EMPTY publishers=0: the new wire resolves a publisher that no shipped reading consumes. queue_head now names line 491 prefix AC-PICBC1 and the gauge stays FLOOR-MET main 5/5 tech 10/10 explore 10/10.",
    "2026-11-04 R2426 debt register after this window: open=2 done=139. product-face-R2426 was closed through the shipped debt_close at its predicted 104274B -> 104277B (measured exactly, readback=ok) and reconcile-battery-R2427 was appended first=yes through the shipped debt_append at its predicted 104277B -> 104802B (readback=ok), naming the next window a full battery on the committed R2426 tree at the pre-registered 541 suites / 4222 criteria. Remaining open: loop-s4u-reconcile and stale-suite-matrix-copy, neither discharged here.",
    "2026-11-04 R2426 honest disclosures: (a) the seed premise was CORRECTED by measurement, not repeated - it spelled the defect as `import os, some_wire as publish` with a BARE `publish(` call, and callee_of reads ATTRIBUTE calls only, so that spelling could never resolve through this law at all; the real shape is the house alias receiver (import os, closeout_export_parity_wire as CEPW then CEPW.publish(...)), so the wire re-reads EVERY comma list and the module header names the correction; (b) the first suite run was RED on AC-PICBW3 because the test expected resolve() to report the wire answer as table_module when no table bindings were supplied - resolve() now reports '' when the table was not asked (a fabricated comparison would hide the difference) and the test asserts both faces, no criterion widened; (c) the first verdict logic read RESOLVED on a tree with six comma lists and zero comma-bound publishers; corrected by measurement to EMPTY, so a guard is never dressed as a catch; (d) NO battery ran - the R2168 mixed-tree rule makes a battery inside a product window measure a tree that is about to change, so it is carried to R2427; (e) tasks.md was not touched, it is the P-47 canonical board and carries no row for this tech slice.",
    "R2426 tokens: local=~22k api=0 api_reason=product window - one wire module and its six-criteria suite written against criteria pinned two rounds earlier, one runner wiring line, one two-leg evidence capture with three adjacent suites, one live capture over 1175 real files plus a resolving fixture and an identity-face comparison, one board stamp with one measured consumer gap seeded, one debt row closed and the successor battery registered through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-04 R2426 self-heal check: BigDomain-OSLoop exists and its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-sixth consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

EXPORT_DO = (
    "R2426 product window: src/os/comma_binding_wire.py closes the comma-list "
    "receiver seam - the shipped table drops every part after the first, so a "
    "publisher aliased on a comma import read UNRESOLVED; the wire asks the "
    "shipped splitter and adds only the dropped parts, suite 6/6 twice with "
    "three adjacent suites green and the registry measured at 541 suites / "
    "4222 criteria"
)
EXPORT_ARTIFACT = (
    "src/os/comma_binding_wire.py + src/os/test_comma_binding_wire.py + "
    "qa/comma-binding-wire-R2426.log (1626B, legs=2 identical=True adjacent=3 "
    "fails=0) + qa/comma-binding-wire-live-R2426.log (real tree EMPTY, fixture "
    "RESOLVED)"
)
EXPORT_MILESTONE = (
    "full reconcile battery on the committed R2426 tree with zero product "
    "edits at the pre-registered 541 suites / 4222 criteria, then the product "
    "face the queue head names: state/queue/tech.md:491 prefix AC-PICBC1 "
    "(comma_binding_consumer_wire, AC-PICBC1..AC-PICBC6 pinned at R2426) - the "
    "new wire resolves a comma-list publisher that no shipped reading consumes "
    "yet, measured on one fixture where the identity face still answers EMPTY"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2426] R2426 product window: the debt gate named "
    "CLAIM-FIRST item=product-face-R2426 and the anchor check at HEAD found "
    "zero executable occupancy, so src/os/comma_binding_wire.py plus its "
    "six-criteria suite shipped against AC-PICBW1..AC-PICBW6 (pinned at R2424 "
    "in state/queue/tech.md line 490). The module closes ONE seam and adds no "
    "law: parts from the shipped splitter (plain_import_comma_binding."
    "parts_of), the per-part question from the shipped composition "
    "(part_statement), the table from export_publish_wire_identity."
    "import_bindings and the callee from that module own callee_of, all at "
    "CALL time - so `import os, some_wire as wiremod` + `wiremod.publish(...)` "
    "reads table_module \"\" (UNRESOLVED) through the table and wire_module "
    "some_wire (BOUND) through this wire. SUITE PASS 6/6 twice identical plus "
    "three adjacent suites green (qa/comma-binding-wire-R2426.log, 1626B) and "
    "the registry MEASURED at 541 suites / 4222 criteria. LIVE reads the REAL "
    "src/os as EMPTY scanned=1175 compared=1173 parity=1167 comma_files=6 "
    "comma_lines=6 resolved=0 unresolved=0 (the guard, not claimed as a live "
    "catch) with a fixture in the same log reading RESOLVED, and the identity "
    "face on that fixture still reading EMPTY publishers=0. Two product "
    "points. Board: row 490 stamped, one measured consumer gap seeded "
    "(comma_binding_consumer_wire, AC-PICBC1..6), floor FLOOR-MET. Battery NOT "
    "run: carried to R2427 at 541 suites / 4222 criteria.\n",
    "- [ ] [carried 2026-11-04 R2426] R2427 first item: THE BATTERY ON THE "
    "COMMITTED R2426 TREE, zero product edits until green (the R2168 "
    "mixed-tree rule). Pre-registered target MEASURED from the registry this "
    "window: 541 suites / 4222 criteria. Regenerate docs/sandbox-suite-matrix."
    "md only from that green evidence (python src/sandbox/suite_matrix.py "
    "--evidence <that green log>), then the four follow-up sections through "
    "src/os/battery_followup.py. After green, resume the product face on the "
    "tech head the reader names (line 491 prefix AC-PICBC1, "
    "comma_binding_consumer_wire). Still carried and needing an ELEVATED "
    "shell: BigDomain-OSLoop reads LogonType=InteractiveToken (state/debt.md "
    "row loop-s4u-reconcile); stale-suite-matrix-copy also remains open.\n",
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
    state["last_order"] = "2026-11-04 00:46"
    state["last_decision_rows"] = 157
    state["benchmarks_refreshed"] = "2026-11-03"
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
            if "comma_binding_wire" not in str(item)]
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
    line = ("2026-11-04T05:16:00+08:00 tick=2426 R2426 product window - "
            "comma_binding_wire shipped against AC-PICBW1..6 with suite 6/6 "
            "twice plus three adjacent suites green, registry measured at 541 "
            "suites / 4222 criteria, live real tree EMPTY with a resolving "
            "fixture, board stamped with one consumer gap seeded, battery "
            "carried to R2427")
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