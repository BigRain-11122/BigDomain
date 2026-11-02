"""closeout_R2374 - state, board, heartbeat and export for the R2374 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's
own words. The export's queue section is re-derived at write time through
queue_floor_export_face.apply, never copied. Dry run by default.
"""

import io
import json
import os
import sys
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import check_export_consistency as CEC  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
TECH = os.path.join(REPO, "state", "queue", "tech.md")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

NOW = datetime.now().replace(microsecond=0)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2374 verification-then-product window: the battery on the committed "
    "R2373 tree read RUNNER PASS 500/500 suites plus controls 7/7 in 1089.1s "
    "with criteria total 3976 EXACTLY as pre-registered, and the CEO-visible "
    "export finally publishes a queue line - docs/status-export.json now "
    "carries queue_floor_reading_wire.published, the discounted claimable and "
    "every discounted row included."
)

ARTIFACT = (
    "docs/status-export.json now carries a live queue section (CLI leg: STALE "
    "-> WRITTEN 72523B -> CURRENT, matches_live=True), shipped with "
    "src/os/queue_floor_export_face.py and its six-criteria suite "
    "(qa/queue-floor-export-face-R2374.log, two identical legs plus three "
    "adjacent suites green), plus the battery that proves the registry "
    "unharmed (qa/reconcile-all-R2374.log, RUNNER PASS 500/500, criteria "
    "3976)."
)

NEXT = (
    "R2375: the battery on the committed R2374 tree pre-registered at 501 "
    "suites / 3982 criteria (this window own os-queue-floor-export-face "
    "suite), then the product face at the queue head the reader names; the "
    "seed this window measured is queue_export_freshness_gate (AC-QEF1..6), "
    "because the export's queue section can age silently - "
    "check_export_consistency never opens it."
)

ITEMS = [
    "2026-11-02 R2374 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD ee2bab1e, no .git/index.lock; "
    "scan read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=165 "
    "tokens=81 new=0 against the widened baseline, the group orders tail "
    "still the 2026-11-01 10:4x model-policy baseline already acknowledged "
    "as non-execution, and benchmarks refreshed 2026-11-02 inside the "
    "seven-day gate). The debt gate named CLAIM-FIRST "
    "item=reconcile-battery-R2373, so the battery ran FIRST on the committed "
    "tree: RUNNER PASS 500/500 suites plus controls 7/7 in 1089.1s with "
    "criteria total 3976 EXACTLY as pre-registered and birth-site TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2374.log, "
    "808379B, crlf=0, single writer utf-8 LF through src/os/battery_stream.py, "
    "never a shell redirection), so the prediction matched the measurement "
    "with no correction and nothing to name.",
    "R2374 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=47836B regenerated=47905B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 500 suites / 3976 criteria (47905B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN "
    "5 domains, profile --check byte-identical, census DRIFT-CLEAN) for "
    "VERDICT R2374 PASS. The evidence and the matrix were committed ALONE as "
    "16430e6c before any product byte changed (the R2168 mixed-tree rule).",
    "R2374 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:420 prefix AC-QFE1 (queue_floor_export_face), whose "
    "AC-QFE1..AC-QFE6 were pinned INSIDE that row at R2368 BEFORE any code, "
    "after a fresh anchor check at HEAD: queue_floor_export_face, AC-QFE, "
    "E_QFE, os-queue-floor-export-face and test_queue_floor_export_face hit "
    "ONLY prose and state files (docs/status-export.json, src/os/backlog.md, "
    "src/os/closeout_R2368.py, src/os/closeout_R2373.py, "
    "src/os/export_R2368.py, src/os/export_R2373.py, "
    "src/os/heartbeat_and_backlog_R2368.py, src/os/state.json, "
    "state/queue/tech.md, state/debt.md) with zero executable occupancy.",
    "R2374 the wire: shipped src/os/queue_floor_export_face.py plus "
    "src/os/test_queue_floor_export_face.py. The section it writes IS "
    "queue_floor_reading_wire.published(root) - the whole report in the key "
    "order that module fixes - so the discounted claimable and every "
    "discounted row (line + prefix) reach the export unchanged. Nothing is "
    "re-derived: no row parser, no queue-file scan, no second status "
    "vocabulary, no canned number. compose() reads the live tree every call "
    "(a changed queue moves the bytes), write() is one atomic replace with a "
    "read-back proof, and the CLI refuses to call a stale export CURRENT.",
    "R2374 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus three adjacent suites green "
    "(qa/queue-floor-export-face-R2374.log, 1731B, legs=2 identical=True "
    "adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-queue-floor-export-face(6) so the "
    "registry reads 501 suites / 3982 criteria. LIVE, not a plan: on the "
    "real tree qa/queue-floor-export-face-live-R2374.log (617B, crlf=0) reads "
    "STALE at contact (rc=2, the export carried no queue section at all), "
    "WRITTEN at 72523B with matches_live=True, then CURRENT at rc=0 - i.e. "
    "the defect the seed described was real and is now closed on the CEO- "
    "visible face. Tech row 420 stamped [done 2026-11-02 R2374] and one REAL "
    "measured gap row seeded (queue_export_freshness_gate, AC-QEF1..AC-QEF6 "
    "pre-registered in that row, five anchors zero-occupancy): the export now "
    "carries the section, but check_export_consistency validates only the "
    "twelve self_drive fields and never opens the queue block, so the section "
    "can age silently after a queue edit and only a manual CLI run notices. "
    "Gauge after the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10. Register: reconcile-battery-R2373 closed through "
    "debt_close (open 3->2, done 102->103, 80360B->80363B, readback ok) and "
    "reconcile-battery-R2374 opened first=yes through debt_append at the "
    "measured successor target 501 suites / 3982 criteria (80363B->80840B, "
    "readback ok).",
    "R2374 honest disclosures: (a) this window overran its 25-minute budget "
    "by a wide margin because the battery alone cost 1089.1s and the matrix "
    "regeneration plus the product face came after it; the product face was "
    "still shipped rather than deferred because the evidence tree was "
    "committed and clean before any product byte changed. (b) The suite's "
    "AC-QFE3 proves the consistency checker still reads 21/21 by pointing it "
    "at a temporary copy carrying the new section, because the real export is "
    "written later in the window - the point is the checker tolerates the "
    "field, not that the live file was already written when the assertion "
    "ran. (c) AC-QFE2's fixtures carry a synthetic discount of one row per "
    "queue because the live queue carries none today (delivered_total=0), so "
    "the discounted path is proved on fixtures and is NOT claimed as a live "
    "catch. (d) tasks.md was left untouched: it is the P-47 canonical board "
    "and carries no row for this tech slice, disclosed rather than silently "
    "skipped. (e) The new gap row deliberately measures the freshness seam "
    "this window created rather than inventing an unrelated shape - the "
    "section has a writer and no watchdog, and saying so is more honest than "
    "dressing it up as new.",
    "R2374 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an "
    "explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twenty-ninth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md).",
    "R2374 tokens: local=~29k api=0 api_reason=verification-then-product "
    "window - one full battery (500 suites, 1089.1s) plus its four follow-up "
    "sections and one matrix regeneration, one export-face module and its "
    "six-criteria suite written to criteria pinned six rounds earlier, one "
    "registry wiring line, one two-leg evidence capture with three adjacent "
    "suites, one live three-step capture (STALE -> WRITTEN 72523B -> CURRENT) "
    "through a single utf-8 LF writer, one board stamp and one measured gap "
    "row seeded, one register close and one successor row opened, one export "
    "refresh deriving the queue section at write time, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2374] verification-then-product-R2374: the debt "
    "gate named CLAIM-FIRST item=reconcile-battery-R2373, so the battery ran "
    "FIRST on the committed ee2bab1e tree - RUNNER PASS 500/500 suites plus "
    "controls 7/7 in 1089.1s with criteria total 3976 EXACTLY as "
    "pre-registered and birth-site TMP RECLAIM 932/932 (qa/reconcile-all-"
    "R2374.log, 808379B, crlf=0, single writer utf-8 LF through "
    "src/os/battery_stream.py); the four follow-up sections ran through "
    "src/os/battery_followup.py, the matrix section FAILED first on the stale "
    "doc and did not rewrite it, suite_matrix regenerated "
    "docs/sandbox-suite-matrix.md to 500 suites / 3976 criteria (47905B) and "
    "the re-run read all four PASS for VERDICT R2374 PASS; evidence and "
    "matrix committed alone as 16430e6c before any product byte changed (the "
    "R2168 mixed-tree rule). PRODUCT: claimed state/queue/tech.md:420 prefix "
    "AC-QFE1 (queue_floor_export_face), criteria pinned in that row at R2368 "
    "BEFORE any code and every anchor prose-only at HEAD. SHIPPED "
    "src/os/queue_floor_export_face.py: the section it writes IS "
    "queue_floor_reading_wire.published (patched reading moves the export), "
    "carrying the discounted claimable plus every discounted row (line + "
    "prefix) and delivered_total, with no second parser, no queue-file scan, "
    "no canned number; compose() re-reads the live tree on every call so a "
    "changed queue moves the bytes, write() is one atomic replace with a "
    "read-back proof, and the CLI reads STALE rather than CURRENT when the "
    "export disagrees. SUITE PASS 6/6 twice with an identical criterion "
    "digest plus three adjacent suites green (qa/queue-floor-export-face-"
    "R2374.log, 1731B), wired os-queue-floor-export-face(6) so the registry "
    "reads 501/3982. LIVE: qa/queue-floor-export-face-live-R2374.log (617B, "
    "crlf=0) reads STALE rc=2 at contact because the export carried no queue "
    "section at all, WRITTEN 72523B with matches_live=True, then CURRENT rc=0 "
    "- the seed's measured defect is closed on the CEO-visible face. Row 420 "
    "stamped and one REAL measured gap seeded (queue_export_freshness_gate, "
    "AC-QEF1..6: check_export_consistency never opens the queue block, so the "
    "section can age silently), gauge FLOOR-MET 5/5 10/10 10/10. Register: "
    "battery-R2373 closed, battery-R2374 opened first=yes at 501 suites / "
    "3982 criteria. Disclosed: the window overran its budget because the "
    "battery cost 1089.1s; AC-QFE2's discount path is proved on fixtures "
    "because the live queue delivers nothing today; tasks.md untouched "
    "because the P-47 board carries no row for this slice."
)

HBT = (
    "R2374 (tick 2374): verification then product - the debt gate named "
    "reconcile-battery-R2373, so the battery ran first on the committed "
    "ee2bab1e tree and read RUNNER PASS 500/500 suites plus controls 7/7 in "
    "1089.1s with criteria total 3976 exactly as pre-registered and TMP "
    "RECLAIM 932/932 worlds 326.59 MiB (qa/reconcile-all-R2374.log, 808379B, "
    "crlf=0); four follow-up sections PASS after the designed matrix FAIL and "
    "its regeneration to 500/3976 at 47905B, VERDICT R2374 PASS, evidence and "
    "matrix committed alone as 16430e6c. Then the CEO-visible export finally "
    "published a queue line: queue_floor_export_face writes "
    "queue_floor_reading_wire.published itself - discounted claimable plus "
    "every discounted row - re-derived on every call, one atomic write with a "
    "read-back proof, and a CLI that reads STALE rather than CURRENT on "
    "disagreement (six criteria green twice plus three adjacent suites, live "
    "STALE -> WRITTEN 72523B -> CURRENT); row 420 stamped, one measured gap "
    "seeded (queue_export_freshness_gate), gauge FLOOR-MET 5/5 10/10 10/10."
)

GAP_ROW = (
    "- [ ] P2 tech seed (R2374, from this window own measured gap): "
    "`src/os/queue_export_freshness_gate.py` - the export now carries a queue "
    "section derived at write time, but NOTHING checks that section is still "
    "the live reading: check_export_consistency validates the twelve "
    "self_drive fields and never opens the queue block, so the section can "
    "age silently after a queue edit and only a manual CLI run notices. "
    "Product: one gate that recomputes the live section and compares it with "
    "the export, naming every drifted queue and refusing to call a stale "
    "block CURRENT. Criteria AC-QEF1..AC-QEF6 pre-registered HERE BEFORE any "
    "code: AC-QEF1 the gate's live side IS queue_floor_export_face.face "
    "(patching it moves the verdict); AC-QEF2 a drifted claimable OR a "
    "drifted delivered row names that queue and refuses; AC-QEF3 an export "
    "with no queue section reads MISSING and never CURRENT; AC-QEF4 the gate "
    "writes nothing and reads no clock; AC-QEF5 exit 0 = CURRENT, 2 = STALE "
    "with the drifted names, 3 = missing file, 5 = bad flags; AC-QEF6 pure "
    "ASCII, stdlib only, no network, own reconcile label. Anchors "
    "zero-occupancy at HEAD 2026-11-02: queue_export_freshness_gate, AC-QEF, "
    "E_QEF, os-queue-export-freshness-gate, test_queue_export_freshness_gate."
)


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def stamp_tech():
    text = read_text(TECH)
    lines = text.split("\n")
    if len(lines) <= 419:
        raise SystemExit("E_TECH short lines=%d" % len(lines))
    row = lines[419]
    if "AC-QFE1" not in row:
        raise SystemExit("E_TECH row 420 is not the AC-QFE1 seed")
    if not row.startswith("- [ ] "):
        print("TECH row 420 already stamped")
        return
    stamped = row.replace("- [ ] ", "- [x] [done 2026-11-02 R2374] ", 1)
    lines[419] = stamped
    lines.insert(420, GAP_ROW)
    before = len(text.encode("utf-8"))
    text2 = "\n".join(lines)
    back = write_text(TECH, text2)
    if back != text2:
        raise SystemExit("E_TECH readback")
    print("TECH before=%dB after=%dB" % (before, len(text2.encode("utf-8"))))


def prepend_backlog():
    text = read_text(BACKLOG)
    if BACKLOG_ROW[:60] in text:
        print("BACKLOG already carries this row")
        return
    back = write_text(BACKLOG, BACKLOG_ROW + "\n" + text)
    if not back.startswith(BACKLOG_ROW):
        raise SystemExit("E_BACKLOG readback")
    print("BACKLOG bytes=%d" % len(back.encode("utf-8")))


def append_heartbeat():
    text = read_text(HEARTBEAT)
    if HBT[:40] in text:
        print("HEARTBEAT already carries this row")
        return
    if text and not text.endswith("\n"):
        text += "\n"
    back = write_text(HEARTBEAT, text + HBT + "\n")
    print("HEARTBEAT bytes=%d" % len(back.encode("utf-8")))


def close_state(execute):
    raw = read_text(STATE)
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    if ITEMS[0][:40] in raw:
        print("STATE already carries this window, tick=%s" % data.get("tick"))
        return int(data.get("tick", 0)), data
    tick = int(data.get("tick", 0)) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    print("STATE tick=%d items=+%d before=%dB predicted=%dB"
          % (tick, len(ITEMS), before, len(text.encode("utf-8"))))
    if not execute:
        return tick, data
    back = write_text(STATE, text)
    if back != text:
        raise SystemExit("E_STATE readback")
    return tick, data


def refresh_export(execute, state):
    data = json.loads(read_text(EXPORT))
    derived, _state, _export, _pat = CEC.recompute()
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    already = any(isinstance(row, list) and len(row) >= 2
                  and row[0] == "R2374" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/queue_floor_export_face.py", "on",
        "R2374 product: the CEO-visible export finally publishes the one "
        "queue reading - the section it writes IS "
        "queue_floor_reading_wire.published, so the discounted claimable and "
        "every discounted row (line + prefix) travel unchanged, re-derived on "
        "every call with one atomic write and a read-back proof, and the CLI "
        "reads STALE rather than CURRENT when the export disagrees; six "
        "criteria green twice plus a live leg that caught the real missing "
        "section (STALE rc=2 -> WRITTEN 72523B -> CURRENT)",
    ])
    if not already:
        data["results"].append([
        "R2374",
        "verification then product: the debt gate named "
        "reconcile-battery-R2373, so the battery ran first on the committed "
        "ee2bab1e tree - RUNNER PASS 500/500 suites plus controls 7/7 in "
        "1089.1s with criteria total 3976 EXACTLY as pre-registered and TMP "
        "RECLAIM 932/932 (qa/reconcile-all-R2374.log, 808379B, crlf=0); four "
        "follow-up sections PASS after the designed matrix FAIL and its "
        "regeneration to 500/3976 at 47905B, VERDICT R2374 PASS, evidence and "
        "matrix committed alone as 16430e6c. Then the claimed row: "
        "state/queue/tech.md:420 AC-QFE1 queue_floor_export_face, its six "
        "criteria pinned there at R2368 BEFORE the code and every anchor "
        "prose-only at HEAD. Shipped the module plus its six-criteria suite: "
        "the section IS queue_floor_reading_wire.published, so the discounted "
        "claimable plus every discounted row reach the export unchanged, with "
        "no second parser, no queue-file scan and no canned number; compose() "
        "re-reads the tree on every call and write() is one atomic replace "
        "with a read-back proof. SUITE PASS 6/6 twice identical plus three "
        "adjacent suites green (qa/queue-floor-export-face-R2374.log), wired "
        "os-queue-floor-export-face(6) so the registry reads 501/3982. LIVE: "
        "STALE rc=2 at contact because the export carried no queue section "
        "at all, WRITTEN 72523B matches_live=True, then CURRENT rc=0. Row 420 "
        "stamped and one REAL measured gap seeded (queue_export_freshness_"
        "gate: check_export_consistency never opens the queue block, so the "
        "section can age silently), gauge FLOOR-MET 5/5 10/10 10/10. "
        "Register: battery-R2373 closed, battery-R2374 opened first=yes at "
        "501/3982. Disclosed: the window overran its budget because the "
        "battery cost 1089.1s; AC-QFE2's discount path is proved on fixtures "
        "because the live queue delivers nothing today.",
    ])
    data["self_drive"] = {
        "window": derived["window"],
        "window_days": derived["window_days"],
        "log_lines_in_window": derived["log_lines_in_window"],
        "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
        "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            derived["substantive_non_idle_mention_lines"],
        "proposals_total": derived["proposals_total"],
        "proposals_open": derived["proposals_open"],
        "queue_main_open": derived["queue_main_open"],
        "queue_tech_open": derived["queue_tech_open"],
        "queue_explore_open": derived["queue_explore_open"],
    }
    QFE.apply(data, REPO)
    data["export_ts"] = STAMP
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    if len(tick_rows) != 1:
        raise SystemExit("E_EXP_TICK rows=%d" % len(tick_rows))
    tick_rows[0][0] = str(state["tick"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT predicted=%dB queue_claimable=%s"
          % (len(text.encode("utf-8")),
             [row["claimable"] for row in data["queue"]["queues"]]))
    if not execute:
        return
    back = write_text(EXPORT, text)
    if back != text:
        raise SystemExit("E_EXPORT readback")
    print("EXPORT written bytes=%d" % len(back.encode("utf-8")))


def main(argv):
    execute = "--execute" in argv
    state_tick, state = close_state(execute)
    if execute:
        # The board is stamped BEFORE the export is derived: the stamp moves a
        # queue row from open to delivered, so the published queue section must
        # be read from the final tree, not from the pre-stamp one.
        stamp_tech()
        prepend_backlog()
        append_heartbeat()
        state = json.loads(read_text(STATE))
    refresh_export(execute, state)
    if execute:
        report, n_pass, n_fail = CEC.check()
        print("CHECK pass=%d fail=%d" % (n_pass, n_fail))
        for line in report:
            print("  " + line)
        if n_fail:
            raise SystemExit("E_EXPORT_CONSISTENCY")
    else:
        print("DRY RUN: pass --execute to write")
    print("CLOSEOUT tick=%d done" % state_tick)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))