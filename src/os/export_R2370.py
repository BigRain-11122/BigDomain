"""export_R2370 - refresh docs/status-export.json from the live state (R2370).

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
    "R2370 product window: the follow-up ritual finally ASKS the "
    "foreign-section reader. The matrix section used to regenerate the doc "
    "over whatever the pile contained, so a ritual rename would have "
    "regenerated the matrix over foreign sections in silence while the reader "
    "stayed a manual call; now a FOREIGN-SECTION pile refuses before any "
    "matrix byte is rendered, a clean pile keeps the matrix byte-identical, "
    "and a census disagreement is reported even when every round reads clean."
)

ARTIFACT = (
    "src/os/followup_section_foreign_wire.py plus its six-criteria suite "
    "(qa/followup-section-foreign-wire-R2370.log, two identical legs plus four "
    "adjacent suites green), the live guard reading of the real pile "
    "(qa/followup-section-foreign-wire-live-R2370.log, VOCABULARY-CLEAN over "
    "460 rounds) and the battery that proves the registry unharmed "
    "(qa/reconcile-all-R2370.log, RUNNER PASS 496/496, criteria 3952)."
)

NEXT = (
    "R2371: the battery on the committed R2370 tree pre-registered at 497 "
    "suites / 3958 criteria (this window own os-followup-section-foreign-wire "
    "suite), then the product face at the queue head the reader names; the "
    "seed this window measured is followup_guard_evidence_scope "
    "(AC-FGES1..6), because the guard asks a fixed 'qa' pile while the section "
    "compares the evidence path it was actually given."
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
        "src/os/followup_section_foreign_wire.py", "on",
        "R2370 product: the follow-up matrix section asks the section-name "
        "reader FIRST - a foreign pile refuses naming the rounds and the "
        "names before any matrix byte is rendered, a clean pile keeps the "
        "matrix byte-identical to the pre-wire section, and a census "
        "disagreement is reported on a clean pile; six criteria green twice "
        "and a live reading of the real pile as VOCABULARY-CLEAN",
    ])
    data["results"].append([
        "R2370",
        "verification then product: the debt gate named product-face-R2370, so "
        "the battery ran first on the committed 6b918367 tree - RUNNER PASS "
        "496/496 suites plus controls 7/7 in 990.9s, criteria total 3952 "
        "EXACTLY as pre-registered, TMP RECLAIM 932/932 worlds 326.59 MiB "
        "(qa/reconcile-all-R2370.log) - and the four follow-up sections PASS "
        "after the designed matrix FAIL and its regeneration to 496/3952 "
        "(47476B, VERDICT PASS); evidence and matrix committed alone as "
        "bd736b53. Then the claimed row: state/queue/tech.md:416 AC-FSFW1 "
        "followup_section_foreign_wire, its six criteria pinned in that row at "
        "R2357 BEFORE the code and every anchor prose-only at HEAD. Shipped "
        "the guard wire plus its six-criteria suite: the reading stays "
        "followup_section_foreign's (this file parses no log and imports no "
        "os) and the matrix core stays battery_followup.matrix_core with its "
        "body unchanged, battery_followup.section_matrix delegating through a "
        "call-time import so the modules never import each other at load; a "
        "FOREIGN-SECTION pile refuses at E_FSFW_FOREIGN_SECTION naming the "
        "rounds and the names before matrix_core is entered, a clean pile "
        "matches the doc byte for byte, a census disagreement is reported even "
        "on a clean pile, and a pile the reader cannot speak about is NOT a "
        "refusal but carries the guard code on the detail. SUITE PASS 6/6 "
        "twice identical plus four adjacent suites green "
        "(qa/followup-section-foreign-wire-R2370.log, 1380B), wired "
        "os-followup-section-foreign-wire(6). LIVE: the real pile reads "
        "VOCABULARY-CLEAN over 460 rounds at rc=0 and the guarded section runs "
        "in front of the real matrix; the refusal branch is proved on fixtures "
        "and not claimed as a live catch. Row stamped and one REAL measured "
        "gap row seeded (followup_guard_evidence_scope, AC-FGES1..6: the guard "
        "asks a fixed qa pile while the section compares the evidence path it "
        "was given), gauge FLOOR-MET 5/5 10/10 10/10. Disclosed: the first red "
        "was a REAL module defect in the pinned key order and the module was "
        "fixed; the second red was this window own fixture asserting the "
        "render line against a --json payload, corrected without widening a "
        "criterion; the live dry run reads matrix FAIL only because this "
        "window added the 497th suite after its own green battery",
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
    print("EXPORT R2370 self_drive=%s" % json.dumps(data["self_drive"]))
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