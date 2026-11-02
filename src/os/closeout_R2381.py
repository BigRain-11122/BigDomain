"""closeout_R2381 - state, board, heartbeat and export for the R2381 window.

Every derived count written here comes from check_export_consistency.recompute()
in this run; only the round label and the prose summaries are this window's own
words. The export's queue section is re-derived at write time and the published
bytes are proved by closeout_export_parity_wire before they replace the export.
The tech row and the successor seed were landed by this window's board step, so
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
DEC_ROWS_NOW = 137

DO = (
    "R2381 verification-then-product window: the same declarations list is now "
    "measured across both review-window faces by one parity, so a future edit "
    "to either law can no longer split the declared path and the argument path "
    "in silence. The battery ran first on the committed tree (507/507 suites, "
    "criteria total 4018 exactly as pre-registered), then the queue head was "
    "claimed and review_window_guard_parity shipped."
)

ARTIFACT = (
    "src/os/review_window_guard_parity.py plus its six-criteria suite "
    "(qa/review-window-guard-parity-R2381.log, 2991B, two legs identical, four "
    "adjacent review-window suites green); the live run over the real tree "
    "reads verdict=PARITY-AGREES rewind=no window=100 declared=WINDOW "
    "argument=ARGUMENT-CLEAN agrees=yes."
)

NEXT = (
    "R2382: the battery on the committed R2381 tree pre-registered at 508 "
    "suites / 4024 criteria (this window own suite), then the product face at "
    "the queue head the reader names (line 428 prefix AC-RNP1). The seed this "
    "window measured is review_window_guard_parity_blind_agreement "
    "(AC-RWGB1..6): the parity reads PARITY-AGREES over a declaration NEITHER "
    "face could parse, so agreement-on-ignorance currently reads as agreement."
)

BACKLOG_ROW = (
    "- [x] R2381 [done 2026-11-02] review_window_guard_parity - "
    "state/queue/tech.md:427 AC-RWGP1..AC-RWGP6 delivered: both review-window "
    "faces are imported and asked at call time over ONE declarations list, the "
    "parity asks only the rewind question they share and reads PARITY-AGREES "
    "when both answer alike or PARITY-DISAGREES naming both codes, while the "
    "two different questions they answer (declared window, history word) are "
    "reported without being called a split; the live tree reads AGREES "
    "window=100."
)

HBT = (
    "%s R2381 verification-then-product: battery 507/507 suites green plus "
    "controls 7/7 in 1604.7s with criteria total 4018 exactly as "
    "pre-registered and four follow-up sections PASS after the designed matrix "
    "FAIL; then shipped os-review-window-guard-parity (6/6, two legs "
    "identical, four adjacent review-window suites green) so the declared path "
    "and the argument path are measured against one declaration (live AGREES "
    "window=100), and the next measured gap (both faces unreadable still reads "
    "AGREES) is seeded with its six criteria pinned." % STAMP
)

ITEMS = [
    "2026-11-02 R2381 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD d78ca1d7, no .git/index.lock; "
    "scan_five_still read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=137 "
    "tokens=86 new=0, the group orders tail still the 2026-11-02 11:04 "
    "model-policy baseline already acknowledged as non-execution, and "
    "benchmarks refreshed 2026-11-02 inside the seven-day gate). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2380, so the battery ran FIRST "
    "on the committed tree: RUNNER PASS 507/507 suites green plus reconcile "
    "controls 7/7 in 1604.7s with birth-site TMP RECLAIM 932/932 worlds 326.59 "
    "MiB busy=0 failed=0 (qa/reconcile-all-R2381.log, 813822B, single writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection) and "
    "criteria total 4018 EXACTLY as pre-registered, so the prediction matched "
    "the measurement with no correction and nothing to name.",

    "R2381 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=48502B regenerated=48617B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 507 suites / 4018 criteria (48617B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2381 PASS. The evidence and the matrix were committed ALONE as e3e42226 "
    "before any product byte changed (the R2168 mixed-tree rule).",

    "R2381 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:427 prefix AC-RWGP1 (review_window_guard_parity), "
    "whose AC-RWGP1..AC-RWGP6 were pinned INSIDE that row at R2371 BEFORE any "
    "code, after a fresh anchor check at HEAD: the five anchors hit only prose "
    "and state files (docs/status-export.json, heartbeat.txt, src/os/backlog.md, "
    "the R2371 board/closeout/export helpers, state/debt.md, "
    "state/queue/tech.md) with zero executable occupancy.",

    "R2381 the parity: shipped src/os/review_window_guard_parity.py plus "
    "src/os/test_review_window_guard_parity.py. It asks the ONE question the "
    "two faces share - does this declarations list rewind - and nothing else: "
    "review_window_wire.window_report is the declared side and "
    "review_window_wire_argument_guard.reading the argument side, both asked "
    "as module attributes at call time, so patching either law moves the "
    "verdict and this file carries no second declarations reader, no row "
    "parser and no declared_by comparison. Two-sided rewind reads "
    "PARITY-AGREES with the carried E_RWHW_DECL_HISTORY reported on both "
    "sides; a monotonic list reads PARITY-AGREES with the declared window "
    "carried from the wire and the argument guard's own history word beside it "
    "- two different questions, not a split; a disagreement on either side "
    "reads PARITY-DISAGREES naming both codes.",

    "R2381 evidence and board: SUITE PASS 6/6 twice with an identical "
    "criterion digest plus four adjacent review-window suites green "
    "(qa/review-window-guard-parity-R2381.log, 2991B, legs=2 identical=True "
    "adjacent=4 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-review-window-guard-parity(6) so "
    "the registry reads 508 suites / 4024 criteria. LIVE, not a plan: on the "
    "real tree qa/review-window-guard-parity-live-R2381.log reads "
    "verdict=PARITY-AGREES rewind=no window=100 declared=WINDOW "
    "argument=ARGUMENT-CLEAN agrees=yes with a byte-stable --json over the "
    "eight pinned keys. Tech row 427 stamped [done 2026-11-02 R2381] and one "
    "REAL measured gap row seeded (review_window_guard_parity_blind_agreement, "
    "AC-RWGB1..AC-RWGB6 pre-registered in that row, five anchors "
    "zero-occupancy). Gauge after the stamp and the seed reads FLOOR-MET main "
    "5/5 tech 10/10 explore 10/10 and the reader now offers line 428 prefix "
    "AC-RNP1. Register: reconcile-battery-R2380 closed through debt_close "
    "(line=132, open 3->2, done 108->109, 82714B->82717B, readback ok) and "
    "reconcile-battery-R2381 opened first=yes through debt_append at the "
    "measured successor target 508 suites / 4024 criteria (82717B->82906B, "
    "readback ok).",

    "R2381 honest disclosures: (a) two suite runs were RED and both were this "
    "window own fixtures, never the module: the first AC-RWGP4 leg left the "
    "declared-side patch in place while asserting the other direction, and the "
    "stale patch then also poisoned AC-RWGP5's exit-0 leg, so both worlds now "
    "restore BOTH faces in the same finally block. No criterion was widened. "
    "(b) The disagreement leg is proved on FIXTURES, not live: a live split "
    "needs one law to move between two calls on a frozen tree, which the suite "
    "forces by patching, and the live log says PARITY-AGREES rather than "
    "implying a live catch. (c) The parity deliberately answers AGREES when "
    "neither face detects a rewind, including when neither face can read the "
    "file at all; that was measured this window on a `{not json` declaration "
    "and is seeded as the next gap rather than hidden. (d) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice. (e) The board row and the seed were landed by editing "
    "state/queue/tech.md directly rather than through a board_R2381.py helper; "
    "the edits are the stamp and one appended seed row, disclosed here.",

    "R2381 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-sixth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",

    "R2381 tokens: local=~34k api=0 api_reason=verification-then-product "
    "window - one full battery (507 suites, 1604.7s) plus its four follow-up "
    "sections and one matrix regeneration, one parity module and its "
    "six-criteria suite written to criteria pinned ten rounds earlier, one "
    "registry wiring line, one two-leg evidence capture with four adjacent "
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
                  and row[0] == "R2381" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/review_window_guard_parity.py", "on",
            "R2381 product: one parity hands a single declarations list to "
            "both review-window faces and asks only the question they share "
            "(does it rewind), reading PARITY-AGREES or PARITY-DISAGREES with "
            "both codes named - the live tree reads AGREES window=100",
        ])
    if not already:
        data["results"].append([
            "R2381",
            "verification-then-product: the battery ran first on the committed "
            "tree and read PASS 507/507 suites plus controls 7/7 in 1604.7s "
            "with criteria total 4018 exactly as pre-registered, four "
            "follow-up sections PASS after the designed matrix FAIL, evidence "
            "and matrix committed alone as e3e42226. Then CLAIMED "
            "state/queue/tech.md:427 AC-RWGP1 review_window_guard_parity, "
            "criteria pinned there at R2371, anchors prose-only at HEAD. "
            "Shipped the parity so both faces are imported and asked at call "
            "time over one declaration; a two-sided rewind agrees on the "
            "carried E_RWHW_DECL_HISTORY, a monotonic list agrees with the "
            "declared window and the argument history word both reported, and "
            "any split reads PARITY-DISAGREES naming both codes. SUITE PASS "
            "6/6 twice identical plus four adjacent suites green (2991B), "
            "wired os-review-window-guard-parity(6) so the registry reads "
            "508/4024. LIVE: AGREES, window=100, byte-stable --json over "
            "eight pinned keys. Row stamped and one REAL measured gap seeded "
            "(blind agreement over an unreadable declaration).",
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