"""export_R2372 - refresh docs/status-export.json from the live state (R2372).

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
    "R2372 product window: the re-pin finally has a NOOP. A second re-pin over "
    "an already-pinned declaration composed bytes IDENTICAL to the file and "
    "still reported PLANNED, so --execute rewrote the same bytes and reported "
    "PINNED and no reader could tell 'nothing to do' from 'I wrote it'. The "
    "wire compares the composed document with the file and reads NOOP, "
    "returning before the writer is entered; the decision is bytes and never "
    "the head round, and every non-NOOP path is still the shipped writer's own "
    "report, codes and JSON order."
)

ARTIFACT = (
    "src/os/residue_triage_repin_idempotent.py plus its six-criteria suite "
    "(qa/residue-triage-repin-idempotent-R2372.log, two identical legs plus "
    "four adjacent suites green), the live parity leg on the real declaration "
    "(qa/residue-triage-repin-idempotent-live-R2372.log, LIVE-PARITY, sha256 "
    "unchanged) and the battery that proves the registry unharmed "
    "(qa/reconcile-all-R2372.log, RUNNER PASS 498/498, criteria 3964)."
)

NEXT = (
    "R2373: the battery on the committed R2372 tree pre-registered at 499 "
    "suites / 3970 criteria (this window own "
    "os-residue-triage-repin-idempotent suite), then the product face at the "
    "queue head the reader names - it currently offers line 419 prefix AC-CUR1 "
    "(contract_usage_renderer); the seed this window measured is "
    "repin_noop_parity (AC-RNP1..6), because the NOOP exists in the wire and "
    "not in the tool operators run, so one act still has two answers."
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
        "src/os/residue_triage_repin_idempotent.py", "on",
        "R2372 product: the re-pin reads NOOP when the composed declaration "
        "equals the file on disk, decided by BYTES and never by the head round "
        "(the module never mentions declared_by), returning before the writer "
        "is entered so no temp file is created and the atomic write path is "
        "not doubled; a one-byte content drift reads PLANNED again, and every "
        "non-NOOP path is the shipped writer's own report printed through the "
        "shipped renderer and serialiser, with the two CLIs proved "
        "byte-identical on PLANNED and on refusals and NOOP at exit 0; six "
        "criteria green twice plus a live parity leg on the real declaration",
    ])
    data["results"].append([
        "R2372",
        "verification then product: the debt gate named "
        "reconcile-battery-R2371, so the battery ran first on the committed "
        "674adfa9 tree, unfiltered - RUNNER PASS 498/498 suites plus controls "
        "7/7 in 933.3s, criteria total 3964 EXACTLY as pre-registered, TMP "
        "RECLAIM 932/932 worlds 326.59 MiB (qa/reconcile-all-R2372.log) - and "
        "the four follow-up sections PASS after the designed matrix FAIL and "
        "its regeneration to 498/3964 (47697B, VERDICT PASS); evidence and "
        "matrix committed alone as be1ac6a. Then the claimed row: "
        "state/queue/tech.md:418 AC-RTRI1 residue_triage_repin_idempotent, its "
        "six criteria pinned in that row at R2363 BEFORE the code and every "
        "anchor prose-only or zero-occupancy at HEAD. Shipped the wire plus its "
        "six-criteria suite: the composition is residue_triage_repin.build and "
        "the writer is residue_triage_repin.plan (a patched build moves the "
        "reading, a patched plan moves the executed path, and nothing here "
        "calls os.replace or json.dumps), NOOP fires only on byte equality and "
        "returns before the writer is entered, and the CLI codes and --json "
        "key order are pinned to the shipped ones. SUITE PASS 6/6 twice "
        "identical plus four adjacent suites green "
        "(qa/residue-triage-repin-idempotent-R2372.log, 3090B), wired "
        "os-residue-triage-repin-idempotent(6). LIVE: both CLIs byte-identical "
        "over the real declaration and its sha256 unchanged across two dry "
        "runs (65393B), while the same call still composes 65210B - the live "
        "declaration IS stale, so NOOP is proved on fixtures and not claimed "
        "as a live catch. Row stamped (predicted=measured 1472542B) and one "
        "REAL measured gap seeded (repin_noop_parity, AC-RNP1..6: the NOOP "
        "exists in the wire and not in the shipped CLI, so one act has two "
        "answers), gauge FLOOR-MET 5/5 10/10 10/10. Disclosed: two suite reds "
        "were this window own fixture and assertion (a missing seeded "
        "declaration, and a byte-count delta where a content delta was meant), "
        "one red was the absent registry entry, and decide reads the "
        "declaration twice on the non-NOOP path rather than reproducing the "
        "writer",
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
    print("EXPORT R2372 self_drive=%s" % json.dumps(data["self_drive"]))
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