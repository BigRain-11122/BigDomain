"""closeout_R2378 - state, board, heartbeat and export for the R2378 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's own
words. The export's queue section is re-derived at write time and the published
bytes are proved by closeout_export_parity_wire before they replace the export
(the wire this window shipped). The tech row and the successor seed were
already landed by queue_R2378.py, so this script does not touch them.
Dry run by default.
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
import closeout_export_parity_wire as CEPW  # noqa: E402
import queue_floor_export_face as QFE  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(REPO, "heartbeat.txt")

NOW = datetime.now().replace(microsecond=0)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

NEW_DEC_TOKENS = []
DEC_ROWS_NOW = 131

DO = (
    "R2378 verification-then-product window: the export parity finally has a "
    "CALLER. The battery ran first on the committed tree (504/504 suites, "
    "criteria total 4000 exactly as pre-registered), then the queue head was "
    "claimed and closeout_export_parity_wire shipped - the closeout now "
    "stages the bytes it is about to publish, asks the parity over the staged "
    "document, and only replaces the export on AGREES."
)

ARTIFACT = (
    "src/os/closeout_export_parity_wire.py plus its six-criteria suite "
    "(qa/closeout-export-parity-wire-R2378.log, 3023B, two legs identical, "
    "four adjacent suites green); the live run over docs/status-export.json "
    "read WRITTEN reading=AGREES at 80266 bytes with no staged residue, and "
    "closeout_R2377.py now publishes its export through it."
)

NEXT = (
    "R2379: the battery on the committed R2378 tree pre-registered at 505 "
    "suites / 4006 criteria (this window own suite), then the product face at "
    "the queue head the reader names (line 425 prefix AC-RSBF1). The seed this "
    "window measured is export_publish_path_guard (AC-EPPG1..6): of the three "
    "closeout scripts that publish the export, only closeout_R2377.py asks the "
    "parity wire, and nothing reads that."
)

BACKLOG_ROW = (
    "- [x] R2378 [done 2026-11-02] closeout_export_parity_wire - "
    "state/queue/tech.md:424 AC-CEPW1..AC-CEPW6 delivered: the closeout stages "
    "the bytes it is about to publish, asks export_closeout_gate_parity over "
    "the staged document and only replaces the export on AGREES, leaving it "
    "byte-identical on a refusal; closeout_R2377.py now publishes through it "
    "and the live run read WRITTEN/AGREES at 80266 bytes."
)

HBT = (
    "%s R2378 verification-then-product: battery 504/504 suites green plus "
    "controls 7/7 in 1320.0s with criteria total 4000 exactly as "
    "pre-registered and four follow-up sections PASS after the designed matrix "
    "FAIL; then shipped os-closeout-export-parity-wire (6/6, two legs "
    "identical, four adjacent suites green) so the closeout finally asks the "
    "export parity before it publishes (live WRITTEN/AGREES at 80266 bytes), "
    "and the next measured gap (two older closeouts still publish directly) is "
    "seeded with its six criteria pinned." % STAMP
)

ITEMS = [
    "2026-11-02 R2378 state fold 643, measured not assumed: the file stood at "
    "93881B against the 78500B waterline (margin -15381, FOLD-DUE) before this "
    "window own lines, so the fold ran FIRST through src/os/state_fold.py - "
    "log lines 1..31 moved verbatim into logs/state-log-archive-2026-11.md at a "
    "TRUE round-block boundary (the R2366, R2367, R2368 and R2369 blocks), "
    "792 tokens covered with none missing, predicted 66923B and measured "
    "66923B exactly, margin 11577B, backup logs/state-preop-R2378.bak, archive "
    "566157B -> 599685B with its prefix intact.",
    "2026-11-02 R2378 residue after the fold, repaired through the shipped "
    "writer rather than by hand: residue_triage read RESIDUE over 226 live "
    "rounds because the declaration had expired at R2373/R2376 and fold 643 "
    "moved four round blocks out of the live log, so residue_triage_repin was "
    "run once from one live reading (declared_by=R2378, until=R2395, entries "
    "222 -> 226, 65393B -> 66071B, every status taken from the measured "
    "reading) and residue_triage now reads TRIAGED 226/226 with expired=0.",
    "2026-11-02 R2378 verification-then-product window (five-silence scan "
    "clean at open: empty git status at 89f60687, no .git/index.lock; the "
    "content-addressed diff of docs/decisions.md against the stored baseline "
    "read ZERO new tokens over 131 rows, the ledger carries no unreplied "
    "@BigDomain transfer, the group orders tail is the 2026-11-02 11:04 "
    "model-policy baseline already acknowledged as non-execution, and "
    "benchmarks were refreshed 2026-11-02 inside the seven-day gate).",
    "R2378 the debt gate named CLAIM-FIRST item=reconcile-battery-R2376, so "
    "the battery ran FIRST on the committed 89f60687 tree: RUNNER PASS 504/504 "
    "suites green plus reconcile controls 7/7 in 1320.0s with birth-site TMP "
    "RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2378.log, 811592B, crlf=0, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection) and criteria "
    "total 4000 EXACTLY as pre-registered, so the prediction matched the "
    "measurement with no correction and nothing to name.",
    "R2378 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=48308B regenerated=48299B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 504 suites / 4000 criteria (48299B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2378 PASS. The evidence and the matrix were committed ALONE as ac0e183b "
    "before any product byte changed (the R2168 mixed-tree rule).",
    "R2378 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:424 prefix AC-CEPW1 (closeout_export_parity_wire), "
    "whose AC-CEPW1..AC-CEPW6 were pinned INSIDE that row at R2377 BEFORE any "
    "code, after a fresh anchor check at HEAD: closeout_export_parity_wire, "
    "AC-CEPW, E_CEPW, os-closeout-export-parity-wire and "
    "test_closeout_export_parity_wire hit ONLY prose and state files "
    "(docs/status-export.json, src/os/closeout_R2377.py, src/os/state.json, "
    "state/queue/tech.md) with zero executable occupancy.",
    "R2378 the wire: shipped src/os/closeout_export_parity_wire.py plus "
    "src/os/test_closeout_export_parity_wire.py. It stages the bytes it is "
    "about to publish beside the export, asks "
    "export_closeout_gate_parity.check over that staged document (asked as an "
    "attribute at call time, so patching it moves what gets published), and "
    "replaces the export only on AGREES; a refusal removes the staged file and "
    "leaves the export byte-identical, and a passing reading keeps the staged "
    "file because that IS the thing being published. compose() is the parity "
    "own closeout_style, so this file carries no json.dump, no QFE import and "
    "no second formatter, and it imports no clock.",
    "R2378 the real path: src/os/closeout_R2377.py now publishes its export "
    "through CEPW.publish(REPO, EXPORT, text=text) and refuses with "
    "E_EXPORT_PARITY when the reading is not AGREES, so the parity is no "
    "longer a CLI nobody calls. Measured on that script: the dry run reads "
    "EXPORT dry run bytes=80266 queue_verdict=FLOOR-DEBT at exit 0.",
    "R2378 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent suites green "
    "(qa/closeout-export-parity-wire-R2378.log, 3023B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-closeout-export-parity-wire(6) so "
    "the registry reads 505 suites / 4006 criteria. LIVE, not a plan: on the "
    "real tree qa/closeout-export-parity-wire-live-R2378.log (625B) reads the "
    "wire WRITTEN reading=AGREES gate=WRITTEN at 80266 bytes, the freshness "
    "gate CURRENT, the second run byte-identical (80266 -> 80266) and "
    "staged_residue=(none). Tech row 424 stamped [done 2026-11-02 R2378] and "
    "one REAL measured gap row seeded (export_publish_path_guard, "
    "AC-EPPG1..AC-EPPG6 pre-registered in that row, five anchors "
    "zero-occupancy), because two older closeouts still publish directly. "
    "Gauge after the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10 and the reader now offers line 425 prefix AC-RSBF1. "
    "Register: reconcile-battery-R2376 closed through debt_close and "
    "reconcile-battery-R2378 opened first=yes at the measured successor target "
    "505 suites / 4006 criteria.",
    "R2378 honest disclosures: (a) the first battery invocation used two flags "
    "battery_stream.py does not take (--root/--out) and refused at exit 1 "
    "before running anything, so one call was spent learning its CLI rather "
    "than assuming it. (b) The refusal leg is proved on FIXTURES, not live: a "
    "live refusal needs the tree to move between compose and check, so the "
    "live log says WRITTEN and does not imply a live refusal. (c) The live run "
    "published BEFORE this closeout, so the export was refreshed twice in one "
    "window; the second write is this closeout own and both went through the "
    "same wire, which the idempotent step in the live log measures. (d) "
    "queue_R2378.py predicted the queue file at 1481091B and measured 1481092B "
    "- one byte, because the tail already ended in a newline - reported rather "
    "than dressed up. (e) The suite first run was RED on AC-CEPW1b and the red "
    "was this window own fixture: it compared the refused file to the "
    "PUBLISHED file instead of to that file own prior bytes, so the assertion "
    "now compares before/after AND shows an unpatched publish moving the same "
    "fixture. No criterion was widened. (f) tasks.md was left untouched: it is "
    "the P-47 canonical board and carries no row for this tech slice.",
    "R2378 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-third "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
    "R2378 tokens: local=~44k api=0 api_reason=verification-then-product "
    "window - one full battery (504 suites, 1320.0s) plus its four follow-up "
    "sections and one matrix regeneration, one parity wire and its "
    "six-criteria suite written to criteria pinned one round earlier, one real "
    "closeout rerouted through the wire, one registry wiring line, one two-leg "
    "evidence capture with four adjacent suites, one live capture through a "
    "single utf-8 LF writer, one board stamp and one measured gap row seeded, "
    "one register close and one successor row opened, and the "
    "state/backlog/export/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def read_text(path):
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


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
    tokens = list(data.get("last_dec_tokens") or ())
    for token in NEW_DEC_TOKENS:
        if token not in tokens:
            tokens.append(token)
    data["last_dec_tokens"] = tokens
    data["last_decision_rows"] = DEC_ROWS_NOW
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    print("STATE tick=%d items=+%d tokens=%d rows=%d before=%dB predicted=%dB"
          % (tick, len(ITEMS), len(tokens), DEC_ROWS_NOW, before,
             len(text.encode("utf-8"))))
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
                  and row[0] == "R2378" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/closeout_export_parity_wire.py", "on",
            "R2378 product: the closeout now stages the bytes it is about to "
            "publish, asks export_closeout_gate_parity over the staged "
            "document and only replaces the export on AGREES - a refusal "
            "leaves the file byte-identical with no residue, an agreeing "
            "reading writes and reads back, and the live run read "
            "WRITTEN/AGREES at 80266 bytes",
        ])
    if not already:
        data["results"].append([
            "R2378",
            "verification-then-product: the battery ran first on the committed "
            "tree and read PASS 504/504 suites plus controls 7/7 in 1320.0s "
            "with criteria total 4000 exactly as pre-registered, four "
            "follow-up sections PASS after the designed matrix FAIL, evidence "
            "and matrix committed alone as ac0e183b. Then CLAIMED "
            "state/queue/tech.md:424 AC-CEPW1 closeout_export_parity_wire, "
            "criteria pinned there at R2377, anchors prose-only at HEAD. "
            "Shipped the wire: stage, ask the parity, publish on AGREES only, "
            "no residue on refusal, compose owned by the parity closeout_style "
            "so no second formatter exists, and src/os/closeout_R2377.py now "
            "publishes its export through it. SUITE PASS 6/6 twice identical "
            "plus four adjacent suites green (3023B), wired "
            "os-closeout-export-parity-wire(6) so the registry reads 505/4006. "
            "LIVE: WRITTEN reading=AGREES at 80266 bytes, gate CURRENT, second "
            "run byte-identical, no staged residue. Row stamped and one REAL "
            "measured gap seeded (export_publish_path_guard: two older "
            "closeouts still publish directly).",
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
    tick = str(state.get("tick", ""))
    label = CEC._load_patterns()["tick_row_label"]
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == label]
    if len(tick_rows) != 1:
        raise SystemExit("E_TICK_ROW count=%d" % len(tick_rows))
    tick_rows[0][0] = tick
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if not execute:
        print("EXPORT dry run bytes=%d queue_verdict=%s"
              % (len(text.encode("utf-8")), data["queue"]["verdict"]))
        return
    parity, parity_code = CEPW.publish(REPO, EXPORT, text=text)
    if parity_code != 0:
        raise SystemExit("E_EXPORT_PARITY %s" % parity["reading"])
    back = read_text(EXPORT)
    if back != text:
        raise SystemExit("E_EXPORT readback")
    print("EXPORT bytes=%d queue_verdict=%s parity=%s"
          % (len(back.encode("utf-8")), data["queue"]["verdict"],
             parity["reading"]))


def main(argv):
    execute = "--execute" in argv
    state_tick, state = close_state(execute)
    if execute:
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


if __name__ == "__main__":
    main(sys.argv[1:])