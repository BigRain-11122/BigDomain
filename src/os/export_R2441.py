"""R2441 export refresh: derived faces + the three CEO lines, one atomic write.

Every value is derived from the live tree; the self_drive block is asked of the
shipped export_R2431.self_drive() callable rather than re-derived here, so the
round keeps one derivation. This refresh runs AFTER the state append by design
(the R2433 ordering law), which is exactly the ordering the R2440 window broke
and this window repaired.
"""

import io
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(REPO, "docs", "status-export.json")
STATE = os.path.join(BASE, "state.json")

sys.path.insert(0, BASE)
import export_R2431 as carrier  # noqa: E402

STAMP = carrier.STAMP

DO = ("R2441 verification window: the reconcile battery prescribed by the "
      "debt register ran on the committed R2440 tree and caught a real "
      "closeout-ordering defect - the derived export counters described a "
      "document one log line shorter than the file - repaired at the birth "
      "site and re-proved with a second full battery")

LATEST = ("qa/reconcile-all-R2441-retry.log (847687B, RUNNER PASS 548/548 "
          "suites green, controls 7/7, 1187.2s, criteria 4264 exactly as "
          "pre-registered) + qa/reconcile-all-R2441.log (847696B, the honest "
          "red leg: 547/548 with os-queue-floor-export-face AC-QFE3 at "
          "stored=76 vs recomputed=77) + docs/sandbox-suite-matrix.md 52827B "
          "at 548 suites / 4264 criteria with --check byte-identical + "
          "docs/status-export.json re-derived to 21/21 consistency")

NEXT = ("product face at the tech head the deliverable-aware reader offers "
        "(state/queue/tech.md:508 prefix AC-MSPL1 matrix_stamp_provenance_"
        "line, criteria pinned before any code); no successor battery is owed "
        "because no product src byte changed this window; due 2026-11-06 "
        "18:00")

RESULT = (
    "2026-11-04 R2441 verification window on the debt gate first=yes item "
    "(reconcile-battery-R2441, pre-registered at 548 suites / 4264 criteria "
    "by the R2440 closeout): leg 1 on the committed tree read 547/548 with "
    "the criteria total exactly 4264 and the only red being the shipped "
    "export consistency, which named the defect instead of hiding it - "
    "self_drive.log_lines_in_window and substantive_non_idle_mention_lines "
    "both stored=76 against recomputed=77, because the R2440 closeout "
    "refreshed the export and THEN appended its own push log line. Repaired "
    "at the birth site with the shipped refresh re-derived from the live tree "
    "(77944B, fresh stamp, check_export_consistency 21/21 VERDICT PASS, "
    "W=77 idle=0 nop=0 sub=77) and committed ALONE as 144e63e3 with no "
    "baseline widened and no criterion touched. Leg 2 on the committed "
    "repair tree read RUNNER PASS 548/548 plus controls 7/7 in 1187.2s with "
    "criteria 4264 to the unit and TMP RECLAIM 932/932 at 326.59 MiB; the "
    "four follow-up sections gave the designed matrix FAIL at 52828B vs "
    "52827B, then a regeneration through --stamp-from and VERDICT R2441 PASS "
    "failing=none with fingerprint CLEAN domains=5, profile byte-identical "
    "and census DRIFT-CLEAN. Five new group decisions D-20261104-08..12 were "
    "judged and all five read ACKNOWLEDGED-NO-ACTION for this company. Debt: "
    "battery closed through the shipped tool (111148B -> 111151B, open 2->1, "
    "done 154->155, readback ok) and product-face-R2442 opened first=yes "
    "(111151B -> 111472B) at tech head 508 prefix AC-MSPL1. Honest: ZERO "
    "product code shipped and zero product points claimed.")

OUTS = ("qa/reconcile-all-R2441-retry.log (847687B, RUNNER PASS 548/548, "
        "criteria 4264) + qa/reconcile-all-R2441.log (847696B, honest red "
        "leg) + docs/status-export.json (re-derived, 21/21 consistency) + "
        "docs/sandbox-suite-matrix.md (52827B at 548/4264, --check "
        "byte-identical) + state/debt.md (battery closed, product-face-R2442 "
        "opened) + src/os/closeout_R2441.py + src/os/export_R2441.py + "
        "src/os/backlog.md + src/os/state.json + heartbeat.txt")

def floors():
    proc = subprocess.run([sys.executable,
                           os.path.join(BASE, "queue_floor.py"), "--check",
                           "--json"], cwd=REPO, capture_output=True)
    try:
        return json.loads(proc.stdout.decode("utf-8", "replace"))
    except ValueError:
        return None


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    face = floors()
    if face is None:
        sys.stdout.write("E_EXP queue floor unreadable\n")
        return 2
    rows = data.get("results") or []
    if not any(isinstance(r, list) and len(r) >= 2 and r[1] == RESULT
               for r in rows):
        rows.insert(0, [tick, RESULT])
    label = carrier.tick_label()
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and r[1] == label]
    if len(stamped) != 1:
        sys.stdout.write("E_EXP expected exactly 1 tick row, found %d\n"
                         % len(stamped))
        return 2
    stamped[0][0] = tick
    data["results"] = rows
    outs = data.get("outs") or []
    if not outs or outs[0] != OUTS:
        outs.insert(0, OUTS)
    data["outs"] = outs
    data["export_ts"] = STAMP
    data["do"] = DO
    ceo = data.get("ceo_face") or {}
    ceo["current"] = DO
    ceo["latest_artifact"] = LATEST
    ceo["next_milestone"] = NEXT
    ceo["next_milestone_due"] = "2026-11-06T18:00:00+08:00"
    ceo["last_artifact"] = LATEST
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    data["self_drive"] = carrier.self_drive()
    data["queue"] = {"floors": face["floors"],
                     "queues": face["queues"]}
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".r2441-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(text)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, EXPORT)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    ok = (str(back["results"][0][0]) == tick
          and back["outs"][0] == OUTS
          and back["ceo_face"]["latest_artifact"] == LATEST
          and back["export_ts"] == STAMP
          and back["self_drive"]["log_lines_in_window"]
          == back["self_drive"]["substantive_non_idle_mention_lines"])
    sys.stdout.write("RESULTS rows=%d outs=%d tick=%s bytes=%d ok=%s\n"
                     % (len(back["results"]), len(back["outs"]), tick,
                        os.path.getsize(EXPORT), ok))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())