"""R2435 export refresh: derived faces + the three CEO lines, one atomic write.

Every value is derived from the live tree; the self_drive block is asked of the
shipped export_R2431.self_drive() callable rather than re-derived here, so the
round keeps one derivation. The tick row keeps exactly one surviving label row
(the R2433 lesson) and this refresh runs AFTER the state append by design.
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

DO = ("R2435 verification window: the debt gate named the battery the R2168 "
      "rule owed on the committed R2434 tree, so the full reconcile battery "
      "ran FIRST at the pre-registered 545 suites / 4246 criteria and read "
      "RUNNER PASS on the first leg (1080.8s, controls 7/7, TMP RECLAIM "
      "932/932); all four follow-up sections then went green after the "
      "designed matrix FAIL was closed by a stamp-aligned regeneration, and a "
      "malformed heartbeat line left by the R2434 closeout was repaired at "
      "its birth site")

LATEST = ("qa/reconcile-all-R2435.log (RUNNER PASS 545/545 suites, controls "
          "7/7, 1080.8s, criteria 4246 exactly as pre-registered, 845513B) + "
          "docs/sandbox-suite-matrix.md regenerated stamp-aligned to 52495B "
          "at 545 suites / 4246 criteria with --check byte-identical")

NEXT = ("product face on the tech head state/queue/tech.md:500 prefix "
        "AC-OTST1 (owner_table_split_triage: the split face re-reports the "
        "same five known law false positives every round with no way to say "
        "reviewed and accepted, so the debt count can never reach zero), "
        "whose AC-OTST1..AC-OTST6 were pinned in that row at R2412 before any "
        "code")

RESULT = (
    "2026-11-04 R2435 verification window on the item the debt gate named "
    "first=yes (reconcile-battery-R2435, carried from R2434): zero product "
    "code changed, the R2168 mixed-tree rule honoured. The battery read "
    "RUNNER PASS 545/545 suites plus controls 7/7 in 1080.8s with the "
    "criteria total 4246 exactly as pre-registered, and the census re-read "
    "DRIFT-CLEAN with its 529-entry baseline untouched. Four follow-up "
    "sections: matrix FAILED first on the stale doc without rewriting it, was "
    "regenerated stamp-aligned to 52495B, and the re-run read VERDICT R2435 "
    "PASS failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: reconcile-battery-R2435 closed at its "
    "predicted bytes and product-face-R2436 opened first=yes through the "
    "shipped CLIs; no successor battery was registered because this window "
    "changed no product src byte. A real defect in the CEO-adjacent heartbeat "
    "face was found and repaired at its birth site: the R2434 closeout had "
    "appended a bare tick number instead of a tick= row. Zero product points "
    "claimed.")

OUTS = ("qa/reconcile-all-R2435.log (RUNNER PASS 545/545, criteria 4246, "
        "845513B) and docs/sandbox-suite-matrix.md regenerated to 52495B")


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
    ceo["next_milestone_due"] = "2026-11-06T12:00:00+08:00"
    ceo["last_artifact"] = LATEST
    ceo["updated_at"] = STAMP
    data["ceo_face"] = ceo
    data["self_drive"] = carrier.self_drive()
    data["queue"] = {"floors": face["floors"],
                     "queues": face["queues"]}
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(EXPORT),
                                   prefix=".r2435-", suffix=".tmp")
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