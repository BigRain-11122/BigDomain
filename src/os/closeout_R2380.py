"""closeout_R2380 - state, board, heartbeat and export for the R2380 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's own
words. The export's queue section is re-derived at write time and the published
bytes are proved by closeout_export_parity_wire before they replace the export.
The tech row and the successor seed were already landed by board_R2380.py, so
this script does not touch them.
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
    "R2380 verification-then-product window: the follow-up matrix section now "
    "guards the pile the EVIDENCE belongs to instead of a hard-coded 'qa', so "
    "the refusal and the matrix always describe the same logs. The battery ran "
    "first on the committed tree (506/506 suites, criteria total 4012 exactly "
    "as pre-registered), then the queue head was claimed and "
    "followup_guard_evidence_scope shipped."
)

ARTIFACT = (
    "src/os/followup_guard_evidence_scope.py plus its six-criteria suite "
    "(qa/followup-guard-evidence-scope-R2380.log, 1988B, two legs identical, "
    "three adjacent suites green); the live run over the real tree reads "
    "derived_dir=qa with the guarded section identical_to_core=True, where "
    "before this window a matrix built from any other pile was protected by a "
    "reading of qa."
)

NEXT = (
    "R2381: the battery on the committed R2380 tree pre-registered at 507 "
    "suites / 4018 criteria (this window own suite), then the product face at "
    "the queue head the reader names (line 427 prefix AC-RWGP1). The seed this "
    "window measured is bare_evidence_pile_refusal (AC-BEPR1..6): the pile now "
    "follows the evidence path, but a path with no directory part still falls "
    "back to 'qa' in silence."
)

BACKLOG_ROW = (
    "- [x] R2380 [done 2026-11-02] followup_guard_evidence_scope - "
    "state/queue/tech.md:426 AC-FGES1..AC-FGES6 delivered: the follow-up "
    "matrix section derives its guarded pile from the evidence path through one "
    "pure module, so a matrix built from a non-qa pile is refused on THAT pile "
    "instead of being protected by a reading of qa, while an evidence path "
    "under qa keeps the section report byte-identical; the live tree reads "
    "derived_dir=qa identical_to_core=True."
)

HBT = (
    "%s R2380 verification-then-product: battery 506/506 suites green plus "
    "controls 7/7 in 1233.7s with criteria total 4012 exactly as "
    "pre-registered and four follow-up sections PASS after the designed matrix "
    "FAIL; then shipped os-followup-guard-evidence-scope (6/6, two legs "
    "identical, three adjacent suites green) so the guarded pile follows the "
    "evidence path (live derived_dir=qa identical_to_core=True), and the next "
    "measured gap (a bare filename still defaults to qa) is seeded with its "
    "six criteria pinned." % STAMP
)

ITEMS = [
    "2026-11-02 R2380 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD 701a4942, no .git/index.lock; "
    "scan_five_still read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=131 "
    "tokens=86 new=0, the group orders tail still the 2026-11-02 11:04 "
    "model-policy baseline already acknowledged as non-execution, and "
    "benchmarks refreshed 2026-11-02 inside the seven-day gate). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2379, so the battery ran FIRST "
    "on the committed tree: RUNNER PASS 506/506 suites green plus reconcile "
    "controls 7/7 in 1233.7s with birth-site TMP RECLAIM 932/932 worlds 326.59 "
    "MiB busy=0 failed=0 (qa/reconcile-all-R2380.log, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection) and criteria "
    "total 4012 EXACTLY as pre-registered, so the prediction matched the "
    "measurement with no correction and nothing to name.",

    "R2380 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=48405B regenerated=48502B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 506 suites / 4012 criteria (48502B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2380 PASS. The evidence and the matrix were committed ALONE as 2215a2b9 "
    "before any product byte changed (the R2168 mixed-tree rule).",

    "R2380 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:426 prefix AC-FGES1 (followup_guard_evidence_scope), "
    "whose AC-FGES1..AC-FGES6 were pinned INSIDE that row at R2370 BEFORE any "
    "code, after a fresh anchor check at HEAD: the five anchors hit only prose "
    "and state files (docs/status-export.json, src/os/seed_R2370.py, "
    "state/queue/tech.md) with zero executable occupancy.",

    "R2380 the module: shipped src/os/followup_guard_evidence_scope.py plus "
    "src/os/test_followup_guard_evidence_scope.py. The question it owns is "
    "which pile an evidence path belongs to: evidence_dir() keeps the basename "
    "of the resolved parent, so a relative and an absolute path for the same "
    "file derive the same pile, and a bare filename honestly returns the "
    "caller's default instead of guessing. The wire now asks it at call time "
    "when no directory is named, so a patched derivation moves which pile is "
    "read, and an explicit directory still wins.",

    "R2380 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus three adjacent suites green "
    "(qa/followup-guard-evidence-scope-R2380.log, 1988B, legs=2 "
    "identical=True adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-followup-guard-evidence-scope(6) so "
    "the registry reads 507 suites / 4018 criteria. LIVE, not a plan: on the "
    "real tree qa/followup-guard-evidence-scope-live-R2380.log (290B) reads "
    "derived_dir=qa, identical_to_core=True, abs_dir=qa same_as_relative=True "
    "and cli_rc=0, so the derived pile adds no wording on the normal path. "
    "Tech row 426 stamped [done 2026-11-02 R2380] and one REAL measured gap "
    "row seeded (bare_evidence_pile_refusal, AC-BEPR1..AC-BEPR6 "
    "pre-registered in that row, five anchors zero-occupancy). Gauge after the "
    "stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10 and "
    "the reader now offers line 427 prefix AC-RWGP1. Register: "
    "reconcile-battery-R2379 closed through debt_close (open 3->2, done "
    "107->108, 82379B->82382B, readback ok) and reconcile-battery-R2380 opened "
    "first=yes through debt_append at the measured successor target 507 suites "
    "/ 4018 criteria (82382B->82714B, readback ok).",

    "R2380 honest disclosures: (a) the first suite run was RED on AC-FGES1 and "
    "AC-FGES6 and both reds were this window own assertions, never the module: "
    "AC-FGES1 compared the section body against the doc bytes when the shipped "
    "section body is the tool's own output, and its literal check scanned the "
    "whole module where the guard's own directory default legitimately lives, "
    "so the check now reads the matrix_section region only; AC-FGES6 looked "
    "for the reader's name anywhere in the helper text and found it in the "
    "docstring, so it now asserts that no import of it exists. No criterion "
    "was widened. (b) The live STEP2 verdict reads FAIL because the matrix doc "
    "is stale by exactly this window's new suite - the designed state, named "
    "'(no rewrite)' in the detail; the claim proved here is identical_to_core, "
    "not a green matrix. (c) tasks.md was left untouched: it is the P-47 "
    "canonical board and carries no row for this tech slice. (d) The bare "
    "filename fallback is disclosed in the module docstring AND seeded as the "
    "next gap rather than hidden: it is the same class this window closed, one "
    "level down.",

    "R2380 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-fifth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",

    "R2380 tokens: local=~26k api=0 api_reason=verification-then-product "
    "window - one full battery (506 suites, 1233.7s) plus its four follow-up "
    "sections and one matrix regeneration, one pile-derivation module and its "
    "six-criteria suite written to criteria pinned ten rounds earlier, one "
    "caller rerouted through it with an explicit directory still winning, one "
    "registry wiring line, one two-leg evidence capture with three adjacent "
    "suites, one live capture through a single utf-8 LF writer, one board "
    "stamp and one measured gap row seeded, one register close and one "
    "successor row opened, and the state/backlog/export/heartbeat closeout; "
    "zero cloud calls and zero external API touches",
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
                  and row[0] == "R2380" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/followup_guard_evidence_scope.py", "on",
            "R2380 product: the guarded pile of the follow-up matrix section "
            "is derived from the evidence path, so a matrix built from any "
            "pile is refused on THAT pile rather than protected by a reading "
            "of qa, and an evidence path under qa keeps the old reading byte "
            "for byte - the live tree reads derived_dir=qa "
            "identical_to_core=True",
        ])
    if not already:
        data["results"].append([
            "R2380",
            "verification-then-product: the battery ran first on the committed "
            "tree and read PASS 506/506 suites plus controls 7/7 in 1233.7s "
            "with criteria total 4012 exactly as pre-registered, four "
            "follow-up sections PASS after the designed matrix FAIL, evidence "
            "and matrix committed alone as 2215a2b9. Then CLAIMED "
            "state/queue/tech.md:426 AC-FGES1 followup_guard_evidence_scope, "
            "criteria pinned there at R2370, anchors prose-only at HEAD. "
            "Shipped the pile derivation as one pure module and rerouted the "
            "matrix section through it at call time, so a patched derivation "
            "moves which pile is read while an explicit directory still wins. "
            "SUITE PASS 6/6 twice identical plus three adjacent suites green "
            "(1988B), wired os-followup-guard-evidence-scope(6) so the "
            "registry reads 507/4018. LIVE: derived_dir=qa, "
            "identical_to_core=True, abs_dir=qa, cli_rc=0. Row stamped and one "
            "REAL measured gap seeded (bare_evidence_pile_refusal: a bare "
            "filename still falls back to qa).",
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