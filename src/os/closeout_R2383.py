"""closeout_R2383 - state, backlog, heartbeat and export for the R2383 window.

Every derived count written here comes from check_export_consistency.recompute()
rather than being re-derived by hand. The export's queue section is re-derived
at write time and the published bytes are proved by
closeout_export_parity_wire before they replace the export.
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
    "R2383 verification-then-product window: a tool's OWN argument block "
    "finally has one owner - runner_arg_guard.guard_usage() was a hand-written "
    "literal and battery_followup_help_wire.usage_text() composed its own flag "
    "line from format strings, so a third tool had to copy one of the two "
    "shapes; both now render through own_usage_block_renderer and both "
    "published texts stay byte-identical. The battery ran first on the "
    "committed tree (509/509 suites, criteria total 4030 exactly as "
    "pre-registered)."
)

ARTIFACT = (
    "src/os/own_usage_block_renderer.py plus its six-criteria suite "
    "(qa/own-usage-block-renderer-R2383.log, 1797B, two legs identical, three "
    "adjacent suites green) and the reroute of src/os/runner_arg_guard.py and "
    "src/os/battery_followup_help_wire.py through it; the live capture reads "
    "VERDICT LIVE-COLLAPSED with both published blocks byte-identical and both "
    "CLIs moving when the renderer is patched "
    "(qa/own-usage-block-renderer-live-R2383.log, 333B)."
)

NEXT = (
    "R2384: the battery on the committed R2383 tree pre-registered at 510 "
    "suites / 4036 criteria (this window own renderer suite), then the product "
    "face the queue head names (line 431 prefix AC-EPPG1, "
    "export_publish_path_guard). The seed this window MEASURED is "
    "owner_table_parity (AC-OTP1..AC-OTP6): the block is rendered from ONE "
    "shape but its table is still hand-written beside the parser that accepts "
    "the flags, so a flag added to the loop never appears in the help."
)

BACKLOG_ROW = (
    "- [x] R2383 [done 2026-11-02] own_usage_block_renderer - "
    "state/queue/tech.md:429 AC-OUB1..AC-OUB6 delivered: a tool's own argument "
    "block now has ONE owner (lead, derived metavar, flag order and the honest "
    "`(none)`), imported by both the guard and the help wire, so patching it "
    "moves both blocks while every already-published line stays byte-identical; "
    "the live capture reads LIVE-COLLAPSED."
)

HBT = (
    "%s R2383 verification-then-product: battery 509/509 suites green plus "
    "controls 7/7 in 1319.2s with criteria total 4030 exactly as pre-registered "
    "and four follow-up sections PASS after the designed matrix FAIL; then "
    "shipped os-own-usage-block-renderer (6/6, two legs identical, three "
    "adjacent suites green) so the guard's own block and the help wire's own "
    "block are rendered by one module (live LIVE-COLLAPSED, both published "
    "texts byte-identical), and the next measured gap (the table is still "
    "hand-written beside the parser) is seeded with its six criteria pinned."
    % STAMP
)

ITEMS = [
    "2026-11-02 R2383 verification-then-product window (five-silence scan "
    "clean at open: empty git status at HEAD f0a06f50, no .git/index.lock; "
    "scan_five_still read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=137 "
    "tokens=86 new=0 over the stored baseline, the group orders tail still the "
    "2026-11-02 11:04 model-policy baseline already acknowledged as "
    "non-execution, and benchmarks refreshed 2026-11-02 inside the seven-day "
    "gate). The debt gate named CLAIM-FIRST item=reconcile-battery-R2382, so "
    "the battery ran FIRST on the committed tree: RUNNER PASS 509/509 suites "
    "green plus reconcile controls 7/7 in 1319.2s with birth-site TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2383.log, "
    "817184B, single writer utf-8 LF through src/os/battery_stream.py, never a "
    "shell redirection) and criteria total 4030 EXACTLY as pre-registered, so "
    "the prediction matched the measurement with no correction and nothing to "
    "name.",
    "R2383 follow-up sections and matrix: the four sections ran through "
    "src/os/battery_followup.py and the matrix section FAILED first on the "
    "stale doc (on-disk=48712B regenerated=48794B) and did NOT rewrite it, "
    "which is the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 509 suites / 4030 criteria (48794B) and "
    "the re-run read all four PASS (matrix byte-identical, fingerprint CLEAN 5 "
    "domains, profile --check byte-identical, census DRIFT-CLEAN) for VERDICT "
    "R2383 PASS. The evidence and the matrix were committed ALONE as b44e9032 "
    "before any product byte was committed (the R2168 mixed-tree rule).",
    "R2383 product face, the row the reader named: CLAIMED "
    "state/queue/tech.md:429 prefix AC-OUB1 (own_usage_block_renderer), whose "
    "AC-OUB1..AC-OUB6 were pinned INSIDE that row at R2373 BEFORE any code, "
    "after a fresh anchor check at HEAD: the five anchors hit only prose and "
    "state files (docs/status-export.json, heartbeat.txt, src/os/backlog.md, "
    "the R2373 board/closeout/export/heartbeat helpers, src/os/state.json, "
    "state/queue/tech.md) with zero executable occupancy.",
    "R2383 the collapse: shipped src/os/own_usage_block_renderer.py plus "
    "src/os/test_own_usage_block_renderer.py, and both callers now render "
    "through it - runner_arg_guard.guard_usage() keeps no literal and "
    "battery_followup_help_wire.usage_text() keeps no format string, so "
    "patching OUB.block moves BOTH own-blocks. The module owns the lead, the "
    "continuation indent, the positional marker, the metavar DERIVED from the "
    "option key and the honest '(none)'; AC-OUB2 forced TWO flag spellings to "
    "survive because the published texts genuinely differ (the guard brackets "
    "its own flags, the wire does not), so the spelling is a declared spec "
    "field rather than a second format string.",
    "R2383 evidence and board: SUITE PASS 6/6 twice with an identical criterion "
    "digest plus three adjacent suites green "
    "(qa/own-usage-block-renderer-R2383.log, 1797B, legs=2 identical=True "
    "adjacent=3 fails=0, single writer utf-8 LF through "
    "src/os/evidence_capture.py), wired os-own-usage-block-renderer(6) so the "
    "registry reads 510 suites / 4036 criteria. LIVE, not a plan: "
    "qa/own-usage-block-renderer-live-R2383.log (333B) reads STEP1 "
    "guard_block_matches_published=True, STEP2 wire_head_matches_published="
    "True, STEP3 wire_ends_with_one_newline=True, STEP4 patched_guard="
    "'PATCHED' patched_wire='PATCHED\\n', STEP5 restored_guard_matches=True, "
    "STEP6 head literals absent from both callers, VERDICT LIVE-COLLAPSED. Tech "
    "row 429 stamped [done 2026-11-02 R2383] and one REAL measured gap row "
    "seeded (owner_table_parity, AC-OTP1..AC-OTP6 pre-registered in that row, "
    "five anchors zero-occupancy): the block is rendered from one shape but the "
    "table it is rendered from is still typed by hand beside the parser loop "
    "that accepts the flags, so a new flag never reaches the help. Gauge after "
    "the stamp and the seed reads FLOOR-MET main 5/5 tech 10/10 explore 10/10 "
    "and the reader now offers line 431 prefix AC-EPPG1. Register: "
    "reconcile-battery-R2382 closed through debt_close (line=134, open 3->2, "
    "done 110->111, 83154B->83157B, readback ok) and reconcile-battery-R2383 "
    "opened first=yes through debt_append at the measured successor target 510 "
    "suites / 4036 criteria (83157B->83413B, readback ok).",
    "R2383 state housekeeping, measured not assumed: the file stood at 79473B "
    "against the 78500B waterline (margin -973, FOLD-DUE), so fold 645 ran "
    "FIRST through src/os/state_fold.py at a TRUE round-block boundary (lines "
    "1..11, cutting BEFORE the R2374 narrative line, so the R2373 and R2374 "
    "blocks moved whole), predicted 70838B and measured 70838B exactly, margin "
    "7662B, 815 tokens covered with none missing, backup logs/state-preop-"
    "R2383.bak, archive 629295B -> 645160B with its prefix intact. The fold "
    "created residue for the two moved blocks as the law predicts, so "
    "residue_triage_repin was run once from ONE live reading (declared_by=R2383, "
    "until=R2400, R2379 and R2380 dropped because they are no longer live) and "
    "residue_triage --check now reads TRIAGED with 0 residue.",
    "R2383 honest disclosures: (a) AC-OUB1's first run was RED and the red was "
    "this window own assertion, never the module: it banned any occurrence of "
    "'usage: %s' / 'runner_arg_guard.py [--json]' / '\"[--help]\"' in the two "
    "callers, and all three hits were legitimate - a docstring EXAMPLE of the "
    "published block and the help token the wire passes to the renderer as "
    "data. The assertion now pins the real law (no caller spells the block's "
    "own head or continuation literal) and no criterion was widened. (b) "
    "AC-OUB2 forced a second spec field (brackets) because the guard brackets "
    "its own flags and the wire does not; the honest reading is one OWNER of "
    "the shape, not one spelling, and that is what this window built. (c) The "
    "fold window includes two prior fold summaries beside the two round blocks "
    "- reported rather than dressed up as a pure round window. (d) tasks.md was "
    "left untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice. (e) This window overran its 25-minute budget because the "
    "battery alone measured 1319.2s; the product face was still shipped rather "
    "than deferred, because the evidence tree was committed and clean before "
    "any product byte changed.",
    "R2383 self-heal check: BigDomain-OSLoop is still registered with "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for "
    "every lane task; src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal but needs an elevated shell, and this session is unelevated, "
    "so the task definition was left untouched (hundred-and-thirty-eighth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md).",
    "R2383 tokens: local=~30k api=0 api_reason=verification-then-product window "
    "- one full battery (509 suites, 1319.2s) plus its four follow-up sections "
    "and one matrix regeneration, one renderer module and its six-criteria "
    "suite written to criteria pinned ten rounds earlier, two callers rerouted "
    "through it with byte-identical published text, one registry wiring line, "
    "one two-leg evidence capture with three adjacent suites, one live capture "
    "through a single utf-8 LF writer, one board stamp and one measured gap row "
    "seeded, one register close and one successor row opened, one waterline "
    "fold at a true block boundary and one residue re-pin from a single live "
    "reading, and the state/backlog/export/heartbeat closeout; zero cloud calls "
    "and zero external API touches",
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
                  and row[0] == "R2383" for row in data["results"])
    if not already:
        data["outs"].append([
            "src/os/own_usage_block_renderer.py", "on",
            "R2383 product: a tool's own argument block now has one owner - the "
            "guard's literal and the help wire's composed flag line both render "
            "through it, with the derived metavar, the honest (none) and the "
            "declared bracket spelling, while every published line stays "
            "byte-identical",
        ])
    if not already:
        data["results"].append([
            "R2383",
            "verification-then-product: the battery ran first on the committed "
            "tree and read PASS 509/509 suites plus controls 7/7 in 1319.2s "
            "with criteria total 4030 exactly as pre-registered, four "
            "follow-up sections PASS after the designed matrix FAIL, evidence "
            "and matrix committed alone as b44e9032. Then CLAIMED "
            "state/queue/tech.md:429 AC-OUB1 own_usage_block_renderer, criteria "
            "pinned there at R2373, anchors prose-only at HEAD. Shipped one "
            "renderer imported by both CLIs so neither writes a format string "
            "for its own block; SUITE PASS 6/6 twice identical plus three "
            "adjacent suites green (1797B), wired os-own-usage-block-renderer(6) "
            "so the registry reads 510/4036. LIVE: LIVE-COLLAPSED with both "
            "published blocks byte-identical and both CLIs moving when the "
            "renderer is patched. Row stamped and one REAL measured gap seeded "
            "(the table is still hand-written beside the parser). Fold 645 at a "
            "true block boundary, predicted=measured 70838B, one residue re-pin.",
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