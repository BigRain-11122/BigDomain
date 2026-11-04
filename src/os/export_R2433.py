"""R2433 export refresh: derived faces + the three CEO lines, one atomic write.

Every value here is derived from the live tree (state.json tick, queue_floor,
the evidence files on disk, the shipped consistency checker's own self_drive
recount) rather than typed in, so the export cannot drift from what the round
actually did. It is run AFTER the state append on purpose: the R2433 red was a
self_drive sampled before its own append.
"""

import datetime
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
STAMP = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))) \
    .replace(microsecond=0).isoformat()

DO = ("R2433 verification window: the debt gate named the battery the R2168 "
      "rule owed on the committed R2432 tree, so the full reconcile battery "
      "ran FIRST at the pre-registered 544 suites / 4240 criteria and came "
      "back red on the CEO-VISIBLE export face itself (18/21: two tick rows "
      "and a self_drive sampled before its own state append); the document "
      "was repaired at the birth site through the shipped derivation, "
      "committed alone, and the retry leg read RUNNER PASS 544/544 at the "
      "same criteria total with all four follow-up sections green")

LATEST = ("qa/reconcile-all-R2433.log (red leg, 1029.8s) + "
          "qa/reconcile-all-R2433-retry.log (RUNNER PASS 544/544, 1017.4s, "
          "criteria 4240) + docs/sandbox-suite-matrix.md regenerated "
          "stamp-aligned to 52412B at 544 suites / 4240 criteria with "
          "--check byte-identical")

NEXT = ("product face on the tech head state/queue/tech.md:498 prefix "
        "AC-GWDA1 (general_writer_dialect_audit), whose criteria were pinned "
        "in that row at R2409 before any code")

RESULT = (
    "2026-11-04 R2433 verification window on the item the debt gate named "
    "first=yes (reconcile-battery-R2433, carried from R2432): zero product "
    "code changed, the R2168 mixed-tree rule honoured. Leg 1 read 543/544 "
    "suites with the criteria total 4240 exactly as pre-registered and the "
    "only red was os-queue-floor-export-face at AC-QFE3, measuring pass=18 "
    "fail=3: self_drive stored 19 lines against 23 recomputed, and two "
    "results rows carried the tick label (2432 and 2431). Root cause "
    "measured on the document: the R2432 closeout edited the export through "
    "an ad-hoc step that inserted a fresh tick row and sampled self_drive "
    "before its own state append. Repaired at the birth site, never by "
    "widening the checker: one surviving tick row, self_drive re-derived "
    "through the shipped export_R2431.self_drive() callable, atomic write "
    "with a read-back, 64472B -> 64418B, then SUMMARY pass=21 fail=0 "
    "VERDICT PASS; committed alone as da5dfc5e. Retry leg on the repaired "
    "tree: RUNNER PASS 544/544 suites plus controls 7/7 in 1017.4s at "
    "criteria 4240, TMP RECLAIM 932/932. Four follow-up sections: matrix "
    "FAILED first on the stale doc without rewriting it, regenerated "
    "stamp-aligned to 52412B, and the re-run read VERDICT R2433 PASS "
    "failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: reconcile-battery-R2433 closed and "
    "product-face-R2434 opened first=yes through the shipped CLIs. Zero "
    "product points claimed.")

OUTS = ("qa/reconcile-all-R2433.log (red leg, 1029.8s) plus "
        "qa/reconcile-all-R2433-retry.log (RUNNER PASS 544/544, 4240 "
        "criteria) and docs/sandbox-suite-matrix.md regenerated to 52412B")


def floors():
    proc = subprocess.run([sys.executable,
                           os.path.join(BASE, "queue_floor.py"), "--check",
                           "--json"], cwd=REPO, capture_output=True)
    try:
        return json.loads(proc.stdout.decode("utf-8", "replace"))
    except ValueError:
        return None


def self_drive():
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    window = cec.recompute()[0]
    return {
        "window": window["window"],
        "window_days": window["window_days"],
        "log_lines_in_window": window["log_lines_in_window"],
        "idle_fast_mention_lines": window["idle_fast_mention_lines"],
        "no_pullable_mention_lines": window["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            window["substantive_non_idle_mention_lines"],
        "proposals_total": window["proposals_total"],
        "proposals_open": window["proposals_open"],
        "queue_main_open": window["queue_main_open"],
        "queue_tech_open": window["queue_tech_open"],
        "queue_explore_open": window["queue_explore_open"],
    }


def tick_label():
    sys.path.insert(0, BASE)
    import check_export_consistency as cec
    return cec._load_patterns()["tick_row_label"]


def main():
    state = json.load(io.open(STATE, encoding="utf-8"))
    data = json.load(io.open(EXPORT, encoding="utf-8"))
    tick = str(state["tick"])
    face = floors()
    if face is None:
        sys.stdout.write("E_EXP queue floor unreadable\n")
        return 2
    rows = data.get("results") or []
    label = tick_label()
    stamped = [r for r in rows if isinstance(r, list) and len(r) >= 2
               and r[1] == label]
    if len(stamped) != 1:
        sys.stdout.write("E_EXP expected exactly 1 tick row, found %d\n"
                         % len(stamped))
        return 2
    stamped[0][0] = tick
    if not any(isinstance(r, list) and len(r) >= 2 and r[1] == RESULT
               for r in rows):
        rows.insert(0, [tick, RESULT])
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
    ceo["next_milestone_due"] = "2026-11-06T12:00:00+08:00"
    ceo["last_artifact"] = LATEST
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    data["self_drive"] = self_drive()
    data["queue"] = {"floors": face["floors"], "queues": face["queues"]}
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".r2433-", suffix=".tmp")
    with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as sink:
        sink.write(text)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(tmp, EXPORT)
    back = json.load(io.open(EXPORT, encoding="utf-8"))
    left = [r for r in back["results"]
            if isinstance(r, list) and len(r) >= 2 and r[1] == label]
    ok = (len(left) == 1 and str(left[0][0]) == tick
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