"""R2424 closeout: state tick, log lines, export face, backlog, heartbeat."""
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
STAMP = "2026-11-04T04:52:00+08:00"
ROUND = 2424
GATE = 78500
RESERVE = 6000

LINES = [
    "2026-11-04 R2424 product window (five-silence scan clean at open: git status empty at HEAD 56011e50 with no .git/index.lock; the evolution ledger carries zero @BigDomain rows; the content-addressed decisions diff read 157 rows and 105 tokens with new=0 against the stored baseline; group orders max_ts is the 2026-11-04 00:46 line already acknowledged at R2421, so nothing dispatches this company; benchmarks refreshed 2026-11-03 inside the seven-day gate; queue floor FLOOR-MET main 5/5 tech 10/10 explore 10/10 with tech head line 489 prefix AC-PICB1). The debt gate named CLAIM-FIRST item=product-face-R2424 and the anchor check at HEAD was clean for all five code anchors (git grep -F found the new name only in prose and state rows, zero executable occupancy), so the criteria pinned at R2422 were built against.",
    "2026-11-04 R2424 SHIPPED src/os/plain_import_comma_binding.py plus src/os/test_plain_import_comma_binding.py against AC-PICB1..AC-PICB6, wired os-plain-import-comma-binding(6) so the registry measures 540 suites / 4216 criteria (538+1+1 readings and 4204+6+6 criteria, measured from the registry, not predicted). ONE reading is added and no law is restated: the split is answered by the SHIPPED splitter (plain_import_alias_gate.plain_parts) and the binding by the SHIPPED receiver table (export_publish_wire_identity.import_bindings) asked once for the whole statement and once per part, with both publish-name tables printed beside them, and the suite proves the call-time dependency by patching the splitter and the table and watching the row move.",
    "2026-11-04 R2424 the defect is named with numbers, not described: on `import os, some_wire as publish` the whole-statement receiver reads {\"os\": \"os\"}, the per-part receiver reads {\"os\": \"os\", \"publish\": \"some_wire\"}, dropped=publish, absolute {}, relative {}, verdict UNBOUND - so the comma list binds the name publish on the receiver side and BOTH publish-name tables read nothing, exactly what AC-PICB2 pre-registered, and a file carrying such a line is named ASYMMETRIC instead of being skipped. Real tree seven-file mix: 4 comma lines named (second, first, three-part, dotted), zero bound, 5 dropped bindings; a comma list that binds no publish is not a row at all (AC-PICB3), and an empty tree reads EMPTY at exit 0 (AC-PICB4).",
    "2026-11-04 R2424 evidence and live reading: qa/plain-import-comma-binding-R2424.log (1562B) carries legs=2 identical=True adjacent=3 fails=0 through the shipped capture callable; qa/plain-import-comma-binding-live-R2424.log (559B, class=tee crlf=0 bare_lf=4) reads the REAL src/os as verdict=EMPTY scanned=1170 comma_lines=0 and then a fixture in the same log as ASYMMETRIC with dropped=publish at exit 2. The real tree is clean today, so this window claims the GUARD and explicitly does not claim a live catch - the same discipline R2420 and R2359 applied. Five adjacent suites were run directly as well (debt gate 5/5, queue head 6/6, queue head delivered 6/6, matrix stamp compare 6/6, plain import alias gate 6/6, plus export_publish_wire_identity PASS 9 FAIL 0).",
    "2026-11-04 R2424 board: tech row 489 stamped `[done 2026-11-04 R2424]` with its delivery narrative outside the bracket (the R2358 lesson) through src/os/queue_R2424.py, and ONE measured gap row seeded beneath it - comma_binding_wire (AC-PICBW1..AC-PICBW6), because this module NAMES the dropped part while the table still drops it: callee_of on a comma list returns module \"\" so the identity reading reports UNRESOLVED for a publisher a bare call would resolve. queue_head now names line 490 prefix AC-PICBW1 and the gauge stays FLOOR-MET main 5/5 tech 10/10 explore 10/10.",
    "2026-11-04 R2424 honest disclosures: (a) no battery ran - the R2168 mixed-tree rule means a battery inside a product window measures a tree that is about to change, so the battery is carried to R2425 with the measured target 540 suites / 4216 criteria; (b) the AC-PICB4 assertion in this window own suite first said four dropped bindings and the measurement read five, because a three-part list drops BOTH alias parts - the assertion was corrected to the measurement with the reason written beside it and the pinned AC-PICB4 wording was not touched; (c) the first smoke run of the new module read EMPTY on a fixture written by PowerShell and the cause was the BOM in that fixture, not the module - re-measured from a clean utf-8 fixture before any judgement; (d) the live log needed one transport fix, the child process stdout arriving CRLF, normalised to LF so the census reads class=tee; (e) tasks.md was not touched, it is the P-47 canonical board and carries no row for this window; (f) the stale rows loop-s4u-reconcile and stale-suite-matrix-copy were not discharged here and docs/sandbox-suite-matrix.md is now one suite behind the registry by design, to be regenerated by the R2425 battery window.",
    "R2424 tokens: local=~31k api=0 api_reason=product window - one product module and its six-criteria suite derived by extending the shipped three-table reading to comma lists (no new parser, no new table), one evidence capture with two identical legs and three adjacent suites, one live reading of the real tree plus a fixture, board stamp and one seeded gap, one debt row closed and one battery row opened through their shipped CLIs, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-04 R2424 self-heal check: BigDomain-OSLoop exists and is Ready, and its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an elevated shell while this session is unelevated, so the definition was left untouched again (hundred-and-ninety-fourth consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
]

EXPORT_DO = (
    "R2424 product window: plain_import_comma_binding ships so a comma-"
    "separated import that binds publish is NAMED instead of silently "
    "dropped - the whole-statement receiver answer, the per-part one and the "
    "two publish-name tables are printed side by side; suite 6/6 twice "
    "identical plus three adjacent suites green, registry 540 suites / 4216 "
    "criteria"
)
EXPORT_ARTIFACT = (
    "src/os/plain_import_comma_binding.py + "
    "src/os/test_plain_import_comma_binding.py "
    "(qa/plain-import-comma-binding-R2424.log, legs=2 identical=True; "
    "qa/plain-import-comma-binding-live-R2424.log, 559B class=tee)"
)
EXPORT_MILESTONE = (
    "reconcile-battery-R2425: the full battery on the committed R2424 tree at "
    "the measured target 540 suites / 4216 criteria, then one product face on "
    "the tech head state/queue/tech.md line 490 prefix AC-PICBW1 "
    "(comma_binding_wire, AC-PICBW1..AC-PICBW6 pinned at R2424)"
)
EXPORT_DUE = "2026-11-05T22:00:00+08:00"

BACKLOG_ROWS = [
    "- [x] [done 2026-11-04 R2424] R2424 product window: the debt gate named "
    "CLAIM-FIRST item=product-face-R2424 and the anchor check was clean for "
    "all five code anchors, so src/os/plain_import_comma_binding.py plus its "
    "six-criteria suite shipped against AC-PICB1..AC-PICB6 (pinned at R2422 "
    "in state/queue/tech.md line 489). The module adds ONE reading and no law: "
    "the parts come from the shipped splitter, the bindings from the shipped "
    "receiver table asked once whole and once per part, and the two "
    "publish-name tables are printed beside them, so `import os, some_wire as "
    "publish` reads receiver {\"os\": \"os\"} against receiver_parts {\"os\": "
    "\"os\", \"publish\": \"some_wire\"} with dropped=publish and verdict "
    "UNBOUND - named, not skipped. SUITE PASS 6/6 twice identical plus three "
    "adjacent suites green (qa/plain-import-comma-binding-R2424.log, 1562B) "
    "and five adjacent suites green directly, wired "
    "os-plain-import-comma-binding(6) so the registry reads 540 suites / 4216 "
    "criteria measured from the registry. LIVE reads the REAL src/os as EMPTY "
    "scanned=1170 comma_lines=0 (the guard, not claimed as a live catch) with "
    "a fixture in the same log naming the drop at exit 2. Two product points. "
    "Board: row 489 stamped with the narrative outside the bracket, one "
    "measured gap row seeded (comma_binding_wire, AC-PICBW1..6), floor "
    "FLOOR-MET. Battery NOT run: carried to R2425 at 540 suites / 4216 "
    "criteria.\n",
    "- [ ] [carried 2026-11-04 R2424] R2425 first item: THE BATTERY ON THE "
    "COMMITTED R2424 TREE, zero product edits until green (the R2168 "
    "mixed-tree rule). Pre-registered target MEASURED from the registry this "
    "window: 540 suites / 4216 criteria. Regenerate docs/sandbox-suite-matrix.md "
    "only from that green evidence (`python src/sandbox/suite_matrix.py "
    "--evidence <that green log>`), then the four follow-up sections through "
    "src/os/battery_followup.py. After green, resume the product face on the "
    "tech head the reader names (line 490 prefix AC-PICBW1, "
    "comma_binding_wire). Still carried and needing an ELEVATED shell: "
    "BigDomain-OSLoop reads LogonType=InteractiveToken (state/debt.md row "
    "loop-s4u-reconcile); stale-suite-matrix-copy also remains open.\n",
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
            if "plain_import_alias_gate" not in str(item)]
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
    line = ("2026-11-04T04:52:00+08:00 tick=2424 R2424 product window - "
            "plain_import_comma_binding ships so a comma-separated import that "
            "binds publish is named with both receiver answers, suite 6/6 "
            "twice identical plus adjacent green, registry 540 suites / 4216 "
            "criteria measured; board stamped and one gap seeded, battery "
            "carried to R2425")
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