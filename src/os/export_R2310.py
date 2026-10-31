"""export_R2310.py - refresh the CEO-visible face (docs/status-export.json).

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

DO = ("R2310 product window: the stamp residue became a dated declaration - "
      "the 185 rounds that were re-triaged by hand every window are now one "
      "pinned file the reader judges, with an expiry that hands a round back "
      "the moment it needs reviewing again.")

CURRENT = ("R2310 shipped src/os/residue_triage.py + its suite + the pinned "
           "state/residue_triage.json (185 entries, until=R2330). The residue "
           "list and every status are imported from stamp_residue itself, an "
           "entry for a round the live list no longer carries is inert, a "
           "status disagreement names both readings and keeps the debt, an "
           "expired entry returns its round naming the until round, and a "
           "missing declaration reads UNPINNED with the full debt. SUITE PASS "
           "6/6 double-run with five adjacent suites green; wired "
           "os-residue-triage(6). Live: residue=185 triaged=185 untriaged=0 "
           "verdict=TRIAGED.")

LATEST = ("qa/residue-triage-R2310.log (2026-11-01, 1341B) + "
          "src/os/residue_triage.py")

NEXT = ("R2311 battery on the committed tree with the suite matrix "
        "regenerated to 462 suites / 3748 criteria; the next product face at "
        "the tech head follows - window <=48h")

ENTRY = ("R2310 product window: residue_triage shipped with its six "
         "pre-registered criteria pinned in the tech row before the code - one "
         "reader, one suite, one pinned declaration over 185 live rounds and "
         "one closeout writer, a real expiry defect caught by AC-RTR4 before "
         "any evidence and fixed in the module, one tech row closed with one "
         "successor seed holding the floor, and zero cloud calls.")

OUT_KEY = "src/os/residue_triage.py"


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
    face["last_artifact"] = "qa/residue-triage-R2310.log"
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
    if not any(row and row[0] == "R2310" for row in results):
        results.insert(0, ["R2310", ENTRY])
    data["results"] = results
    body = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    after = len(body.encode("utf-8"))
    print("EXPORT R2310 before=%dB after=%dB export_ts=%s window=%s lines=%s"
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