"""export_R2373 - refresh docs/status-export.json from the live state (R2373).

Every count written here is derived in this run through
check_export_consistency.recompute(); only the round label and the three prose
summaries are this window's own words. Dry run by default; --execute writes
with a read-back proof.
"""

import io
import json
import os
import sys
from datetime import datetime, timedelta

import check_export_consistency as CEC

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

NOW = datetime.now().replace(microsecond=0)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%S+08:00")
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2373 product window: the runner contract finally has ONE usage "
    "renderer. The guard rendered a two-line usage block and the help wire "
    "rendered a second one-line block from the same contract, so a third tool "
    "would have made three. contract_usage_renderer now owns the vocabulary - "
    "the three required keys, the flag spelling and the honest (none) - in the "
    "two shapes both published texts need, and the guard exports it as "
    "usage_text/contract_line so neither CLI writes a format string while every "
    "already-published line stays byte-identical."
)

ARTIFACT = (
    "src/os/contract_usage_renderer.py plus its six-criteria suite "
    "(qa/contract-usage-renderer-R2373.log, two identical legs plus three "
    "adjacent suites green), the live leg proving both CLIs answer through the "
    "one module with both texts byte-identical to R2366 "
    "(qa/contract-usage-renderer-live-R2373.log, LIVE-COLLAPSED) and the "
    "battery that proves the registry unharmed (qa/reconcile-all-R2373-"
    "retry.log, RUNNER PASS 499/499, criteria 3970)."
)

NEXT = (
    "R2374: the battery on the committed R2373 tree pre-registered at 500 "
    "suites / 3976 criteria (this window own os-contract-usage-renderer "
    "suite), then the product face at the queue head the reader names - it "
    "currently offers line 420 prefix AC-QFE1 (queue_floor_export_face); the "
    "seed this window measured is own_usage_block_renderer (AC-OUB1..6), "
    "because a tool's OWN argument block is still a hand-written literal and "
    "the wire composes its own flag line from strings."
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    execute = "--execute" in argv
    data = read_json(EXPORT)
    derived, _state, _export, _pat = CEC.recompute()
    window = derived["window"]
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "src/os/contract_usage_renderer.py", "on",
        "R2373 product: one usage renderer for a CLI contract - the required "
        "keys, the flag spelling and the honest (none) now have one owner, in "
        "the two shapes the already-published texts need (block for the "
        "guard, inline for the wire's house line), with the guard as the "
        "exported door; a missing key refuses with its own code instead of "
        "rendering a partial block; six criteria green twice plus a live leg "
        "where both CLIs answer through the module and both texts are "
        "byte-identical to R2366",
    ])
    data["results"].append([
        "R2373",
        "verification then product: the debt gate named "
        "reconcile-battery-R2372, so the battery ran first on the committed "
        "ee2bab1e tree - and it was RED ON EVIDENCE, NOT CODE: 498/499 suites, "
        "both failures reading reconcile-daily-census cd7 DRIFT-FLAG, because "
        "the R2372 live evidence carried six CRLF lines inside a file the "
        "census reads as one utf-8 LF dialect. Repaired at the birth site "
        "(one transport-EOL normalisation in evidence_R2372.py, file "
        "regenerated, payload identical except the two byte-count lines) and "
        "the census read DRIFT-CLEAN with the baseline untouched; the retry on "
        "the committed repair tree read RUNNER PASS 499/499 plus controls 7/7 "
        "in 1267.0s, criteria total 3970 EXACTLY as pre-registered, TMP RECLAIM "
        "932/932, four follow-up sections PASS after the designed matrix FAIL "
        "and its regeneration to 499/3970 at 47836B (VERDICT PASS), evidence "
        "and matrix committed alone as 4b2b4f7d. Then the claimed row: "
        "state/queue/tech.md:419 AC-CUR1 contract_usage_renderer, its six "
        "criteria pinned there at R2366 BEFORE the code and every anchor "
        "prose-only at HEAD. Shipped the renderer plus its six-criteria suite: "
        "one owner of the contract vocabulary in the two published shapes, a "
        "missing key refusing with E_CUR_CONTRACT_MISSING_<KEY> (guard exit 3, "
        "wire keeps its published E_BFH_NO_CONTRACT at exit 5), and the wire "
        "asking runner_arg_guard.contract_line so the guard stays the exported "
        "door. SUITE PASS 6/6 twice identical plus three adjacent suites green "
        "(qa/contract-usage-renderer-R2373.log), wired "
        "os-contract-usage-renderer(6) so the registry reads 500/3976. LIVE: "
        "LIVE-COLLAPSED with block_guard_equals_module and "
        "wire_house_identical both True. Row stamped and one REAL measured gap "
        "seeded (own_usage_block_renderer: a tool's own argument block is still "
        "hand-written), gauge FLOOR-MET 5/5 10/10 10/10, reader now offers line "
        "420 AC-QFE1. Register: battery-R2372 closed, battery-R2373 opened "
        "first=yes at 500/3976. Disclosed: the first battery invocation died "
        "to the Out-Null no-output trap with zero survivors and zero evidence; "
        "AC-CUR2 forced two shapes to survive; the window overran its budget.",
    ])
    data["self_drive"] = {
        "window": window,
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
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    if len(tick_rows) != 1:
        raise SystemExit("E_EXP_TICK rows=%d" % len(tick_rows))
    tick_rows[0][0] = str(_state["tick"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT R2373 self_drive=%s" % json.dumps(data["self_drive"]))
    print("EXPORT bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    back = io.open(EXPORT, "r", encoding="utf-8", newline="").read()
    print("EXPORT written readback=%s" % (back == text))
    return 0 if back == text else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))