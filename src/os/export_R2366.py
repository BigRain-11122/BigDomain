"""export_R2366 - refresh docs/status-export.json from the live state (R2366).

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

NOW = datetime.strptime("2026-11-02T06:24:39", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T06:24:39+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2366 product window: the follow-up CLI now answers a bare --help as a "
    "QUESTION at exit 0 instead of calling the operator wrong with a bad-args "
    "exit 5, and it answers from two imported contracts - the runner CLI "
    "contract through the guard own importer, and the follow-up own flag "
    "tables - so no second flag table exists in the tree."
)

ARTIFACT = (
    "src/os/battery_followup_help_wire.py plus its six-criteria suite "
    "(qa/battery-followup-help-wire-R2366.log, two identical legs at criterion "
    "digest 7e6881b726a46311) and the live answer it was built for "
    "(qa/battery-followup-help-wire-live-R2366.log: exit 0 with the derived "
    "usage block and the house contract line)."
)

NEXT = (
    "R2367: the battery the R2168 mixed-tree rule defers, pre-registered at "
    "494 suites / 3940 criteria (the matrix doc at HEAD still reads 492/3928 "
    "from the R2364 leg, plus the R2365 os-queue-floor-delivered-wire suite "
    "and this window os-battery-followup-help-wire suite, six criteria each), "
    "then the product face the queue head names."
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
        "src/os/battery_followup_help_wire.py", "on",
        "R2366 product: the follow-up CLI answers --help at exit 0 from two "
        "imported contracts (runner CLI_CONTRACT via the guard importer, and "
        "its own parser flag tables), so the help text cannot drift from "
        "either CLI while every other exit code and printed line stays "
        "byte-identical; six criteria green twice and one live answer",
    ])
    data["results"].append([
        "R2366",
        "product window: state/queue/tech.md:412 AC-BFH1 "
        "battery_followup_help_wire - the follow-up CLI finally answers the "
        "question an operator asks. The debt gate read CLAIM-FIRST "
        "item=product-face-R2365 and that turned out to be FINISHED work "
        "(R2365 had shipped it), so the row was verified by measurement "
        "(module, suite, two evidence logs and the runner wiring all on disk) "
        "and closed through debt_close instead of being re-run - the "
        "R2345/R2354 shape, named as the round first finding. The claimed "
        "tech row 412 had its AC-BFH1..AC-BFH6 pinned at R2365 BEFORE any "
        "code, re-anchored at HEAD (E_BFH and both file names zero-occupancy; "
        "battery_followup_help_wire and AC-BFH only in prose and state). "
        "SHIPPED src/os/battery_followup_help_wire.py plus its six-criteria "
        "suite, and battery_followup.py now carries module-level TAKES/FLAGS "
        "and raises HelpAsked on --help, answered at exit 0 through the wire. "
        "The house half of the usage block is imported from "
        "reconcile_all.CLI_CONTRACT through runner_arg_guard.load_contract, "
        "the flag half from the parser own tables, and the wire validates the "
        "three keys it reads so a short contract refuses E_BFH_NO_CONTRACT "
        "instead of raising a KeyError inside a renderer. SUITE PASS 6/6 "
        "twice identical (qa/battery-followup-help-wire-R2366.log, 1411B, "
        "single utf-8 LF writer), os-battery-followup and "
        "os-run-argument-guard still 6/6 unchanged, wired "
        "os-battery-followup-help-wire(6). LIVE: "
        "battery_followup.py --help answers exit 0 with the derived usage and "
        "the house line reconcile_all.py [evidence_log_path] flags=(none) "
        "(qa/battery-followup-help-wire-live-R2366.log, 380B), where the same "
        "call was exit 5 E_BFU_BAD_ARGS before. Seven new group decision rows "
        "D-20261102-07..13 read in full and NONE dispatches this company "
        "(collection no-op, line triage, duanju, LANE-REGISTRY, disabled-task "
        "whitelist, external audit, Biggame Art/Builds); baseline widened. "
        "Row stamped, one REAL measured gap seeded (contract_usage_renderer, "
        "AC-CUR1..6 - the guard and this wire now render two usage blocks for "
        "one shape), floor FLOOR-MET 5/5 10/10 10/10. Disclosed: the first "
        "closeout fold picked a tokens LINE as its boundary, archiving this "
        "round own narrative, and the second picked one inside the R2365 "
        "block, which read rounds_without_ledger=2365; repaired at the birth "
        "site (archive section trimmed, state restored byte-exact from the "
        "fold backup, refold at the true boundary log_len-8 = line 69, "
        "predicted=measured 16702B, 771 tokens covered, log=9, ledger CLEAN), "
        "then the nine fold-created residue rounds were spliced in ONE atomic "
        "replace through the shipped reader/shape/composer/judge "
        "(213->222 entries, 62765B->65393B measured, TRIAGED 222/222)",
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
    print("EXPORT R2366 self_drive=%s" % json.dumps(data["self_drive"]))
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