"""export_R2371 - refresh docs/status-export.json from the live state (R2371).

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
    "R2371 product window: the explicit --window path finally ASKS the "
    "history. `exempt_review --window N` used to take the caller's number and "
    "age every accepted entry without ever noticing that the declarations list "
    "is not a history; now a list whose declared_by rewinds refuses with the "
    "declared path's own E_RWHW_DECL_HISTORY naming both rounds, before any "
    "entry is aged, while a monotonic, UNPINNED or DRIFT declaration keeps its "
    "reading byte-identical."
)

ARTIFACT = (
    "src/os/review_window_wire_argument_guard.py plus its six-criteria suite "
    "(qa/review-window-wire-argument-guard-R2371.log, two identical legs plus "
    "four adjacent suites green), the live reading of the real declarations "
    "list (qa/review-window-wire-argument-guard-live-R2371.log, "
    "ARGUMENT-CLEAN / EMPTY-HISTORY / window=100, declaration sha256 "
    "unchanged) and the battery that proves the registry unharmed "
    "(qa/reconcile-all-R2371.log, RUNNER PASS 497/497, criteria 3958)."
)

NEXT = (
    "R2372: the battery on the committed R2371 tree pre-registered at 498 "
    "suites / 3964 criteria (this window own "
    "os-review-window-wire-argument-guard suite), then the product face at the "
    "queue head the reader names - it currently offers line 418 prefix "
    "AC-RTRI1 (residue_triage_repin_idempotent); the seed this window measured "
    "is review_window_guard_parity (AC-RWGP1..6), because the declared and "
    "argument paths now refuse the same file with the same code and nothing "
    "measures that the pair agrees over ONE declaration."
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
        "src/os/review_window_wire_argument_guard.py", "on",
        "R2371 product: the explicit --window argument path asks "
        "review_window_history FIRST, so a declarations list whose declared_by "
        "rewinds refuses with the declared path's own E_RWHW_DECL_HISTORY "
        "naming both rounds before any entry is aged; the rewind law is "
        "imported at call time and the code is carried through the wire's own "
        "mapping, a monotonic or UNPINNED or DRIFT declaration keeps its "
        "reading byte-identical, and the declaration bytes stay untouched; six "
        "criteria green twice plus a live reading of the real list",
    ])
    data["results"].append([
        "R2371",
        "verification then product: the debt gate named "
        "reconcile-battery-R2370, so the battery ran first on the committed "
        "5d9485d2 tree - RUNNER PASS 497/497 suites plus controls 7/7 in "
        "987.8s, criteria total 3958 EXACTLY as pre-registered, TMP RECLAIM "
        "932/932 worlds 326.59 MiB (qa/reconcile-all-R2371.log) - and the four "
        "follow-up sections PASS after the designed matrix FAIL and its "
        "regeneration to 497/3958 (47582B, VERDICT PASS); evidence and matrix "
        "committed alone as 5d9485d2. Then the claimed row: "
        "state/queue/tech.md:417 AC-RWAG1 "
        "review_window_wire_argument_guard, its six criteria pinned in that "
        "row at R2359 BEFORE the code and every anchor prose-only or "
        "zero-occupancy at HEAD. Shipped the guard plus its six-criteria "
        "suite: the history law is imported at call time (proved by patching "
        "it and watching both the library report and the CLI move) and the "
        "refusal code is carried through review_window_wire.carry_history_code, "
        "so `exempt_review --window N` refuses a rewinding list with the same "
        "E_RWHW_DECL_HISTORY the declared path uses, naming both rounds; "
        "UNPINNED, DRIFT, a moved list and an unreadable file all leave the "
        "explicit window's reading byte-identical because that window is the "
        "caller's, and the refusal lands before any entry is aged with zero "
        "counts and WINDOW-REFUSED while the declaration bytes are untouched. "
        "SUITE PASS 6/6 twice identical plus four adjacent suites green "
        "(qa/review-window-wire-argument-guard-R2371.log, 3426B), wired "
        "os-review-window-wire-argument-guard(6). LIVE: the real declarations "
        "list reads ARGUMENT-CLEAN / EMPTY-HISTORY / window=100 / "
        "declared_by=R2305 at exit 0 and both exempt_review paths read 9 "
        "entries 0 stale with the declaration sha256 unchanged. Row stamped "
        "and one REAL measured gap row seeded (review_window_guard_parity, "
        "AC-RWGP1..6: the two paths now refuse the same file with the same "
        "code but nothing measures that they agree over one declaration), "
        "gauge FLOOR-MET 5/5 10/10 10/10. Disclosed: the first battery "
        "invocation was cancelled by a truncating pipe (the known trap) with "
        "zero survivors and no evidence file before the direct-stream rerun; "
        "three suite reds were this window own assertions and fixtures, "
        "corrected to the measured truth without widening a criterion; and one "
        "REAL module defect was found on the way - the refusal detail now "
        "carries the history code exactly as the declared path does",
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
    print("EXPORT R2371 self_drive=%s" % json.dumps(data["self_drive"]))
    print("EXPORT bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))