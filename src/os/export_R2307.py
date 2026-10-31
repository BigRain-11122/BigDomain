"""export_R2307.py - refresh the CEO-visible face (docs/status-export.json).

Every derived field comes from the live files: self_drive is recomputed by the
shipped consistency checker (F3: never written by hand), the queue counts come
from that same recomputation, and the three CEO lines are the round's own
facts. Newest entries go first in outs/results, as the file already does.

Dry run by default; --execute writes utf-8 and then the consistency checker is
run by the caller.
"""

import datetime
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_export_consistency as CEC  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

DO = ("R2307 product window: the accepted-stamp declaration got its writer - "
      "a new closed row is now rendered in the declaration own shape, validated "
      "by its own reader and joined against the reviewer own live pairs, with "
      "three refusals before any byte changes.")

CURRENT = ("R2307 shipped src/os/stamp_exempt_append.py + its suite: a NEW closed "
           "row can be declared instead of hand-typed into a 380-entry JSON. The "
           "declaration reader is the authority on shape, the live pair join is the "
           "reviewer own, a missing row / duplicate pair / ambiguous pair each "
           "refuse before any byte changes, a dry run predicts the exact post size "
           "and an executed append is one atomic replace proved by read-back. "
           "SUITE PASS 6/6 double-run with five adjacent suites green; wired "
           "os-stamp-exempt-append(6). Live CLI on the real 78774B declaration: both "
           "legs refused as designed and the file stayed byte-identical.")

LATEST = ("qa/stamp-exempt-append-R2307.log (2026-11-01, 850B) + "
          "src/os/stamp_exempt_append.py")

NEXT = ("R2308 product face at the tech head line 370 prefix AC-EOA1 "
        "(evidence_output_audit seed, criteria already pinned in that row); "
        "the full reconcile battery carries as the successor row - window <=48h")

ENTRY = ("R2307 product window: stamp_exempt_append shipped with its six "
         "pre-registered criteria pinned in the tech row before the code - one "
         "writer module plus suite, one real module defect and two this-window test "
         "defects caught before any evidence, two live refusals against the real "
         "78774B declaration with the file proved byte-identical, one gap seed "
         "holding the tech floor, one waterline fold, and zero cloud calls.")

OUT_KEY = "src/os/stamp_exempt_append.py"


def stamp():
    now = datetime.datetime.now().astimezone()
    return now.replace(microsecond=0)


def main(argv):
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    derived, state, _export, pat = CEC.recompute()
    tick = state.get("tick")
    now = stamp()
    before = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    data["export_ts"] = now.isoformat()
    data["do"] = DO
    face = data.get("ceo_face") or {}
    face["current"] = CURRENT
    face["latest_artifact"] = LATEST
    face["last_artifact"] = "qa/stamp-exempt-append-R2307.log"
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = (now + datetime.timedelta(hours=48)).isoformat()
    data["ceo_face"] = face
    drive = data.get("self_drive") or {}
    for key in ("window", "window_days", "log_lines_in_window",
                "idle_fast_mention_lines", "no_pullable_mention_lines",
                "substantive_non_idle_mention_lines", "proposals_total",
                "proposals_open", "queue_main_open", "queue_tech_open",
                "queue_explore_open"):
        if key in derived:
            drive[key] = derived[key]
    data["self_drive"] = drive
    outs = data.get("outs") or []
    if not any(row and row[0] == OUT_KEY for row in outs):
        outs.insert(0, [OUT_KEY, "on", ENTRY])
    data["outs"] = outs
    results = data.get("results") or []
    label = pat["tick_row_label"]
    for row in results:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(tick)
    if not any(row and row[0] == "R2307" for row in results):
        results.insert(0, ["R2307", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2307 before=%dB after=%dB export_ts=%s window=%s lines=%s"
          % (before, after, data["export_ts"], drive.get("window"),
             drive.get("log_lines_in_window")))
    if "--execute" not in argv:
        print("DRY RUN - wrote nothing")
        return 0
    temp = EXPORT + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, EXPORT)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body:
        print("E_READBACK")
        return 3
    if os.path.exists(temp):
        print("E_RESIDUE")
        return 3
    print("WROTE readback ok temp clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))