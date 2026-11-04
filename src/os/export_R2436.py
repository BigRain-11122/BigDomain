"""R2436 export refresh: derived faces + the three CEO lines, one atomic write.

Every value is derived from the live tree; the self_drive block is asked of the
shipped export_R2431.self_drive() callable rather than re-derived here, so the
round keeps one derivation. This refresh runs AFTER the state append by design.
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

DO = ("R2436 product window: owner_table_split_triage shipped against "
      "AC-OTST1..AC-OTST6 pinned at R2412, so the split face can now be told "
      "a known law false positive was reviewed - a dated {tool, reason, "
      "since_round} row moves it to TRIAGED while still printing both "
      "verdicts and the law flags, and an entry that no longer matches reads "
      "STALE instead of being silently kept")

LATEST = ("src/os/owner_table_split_triage.py + state/owner_table_triage.json "
          "+ qa/owner-table-split-triage-live-R2436.log (real src/os reading: "
          "scanned=1068 rows=41 superseded=35 split=0 triaged=6 stale=0 "
          "verdict=TRIAGE-CLEAN) + suite 6/6 twice identical "
          "(qa/owner-table-split-triage-R2436-a.log / -b.log)")

NEXT = ("reconcile-battery-R2436 first=yes: the full battery on the committed "
        "R2436 tree at the pre-registered 546 suites / 4252 criteria, then the "
        "four follow-up sections and a stamp-aligned matrix check")

RESULT = (
    "2026-11-04 R2436 product window on the item the debt gate named first=yes "
    "(product-face-R2436, tech head state/queue/tech.md:500 prefix AC-OTST1): "
    "src/os/owner_table_split_triage.py plus its six-criteria suite and a "
    "shipped declaration landed against criteria pinned at R2412 before any "
    "code. A declaration row shaped exactly {tool, reason, since_round} that "
    "matches a LIVE disagreement on tool AND reason moves it to TRIAGED while "
    "the row stays printed with both verdicts and the law own flags; an entry "
    "that matches nothing reads STALE with why=no-live-disagreement or "
    "reason-differs, so a tool that now agrees on both sides is never counted "
    "clean by accident, and a reason change returns the row to the split. "
    "Proved: SUITE PASS 6/6 on the first run then twice identical (689B, sha16 "
    "023a446b91304ce9), three adjacent suites green, runner wired "
    "os-owner-table-split-triage(6) at 546 suites / 4252 criteria; LIVE on the "
    "real src/os reads TRIAGE-CLEAN split=0 triaged=6 stale=0 over the six "
    "measured law false positives. Disclosed: TRIAGE-CLEAN is a triage verdict "
    "and not a parity proof; the seed prose said five rows and this window "
    "measured six; the matrix doc was regenerated to 52596B and reads "
    "green=545/546 because this suite has no line in the R2435 evidence; no "
    "battery ran and reconcile-battery-R2436 is owed next.")

OUTS = ("src/os/owner_table_split_triage.py, state/owner_table_triage.json, "
        "qa/owner-table-split-triage-live-R2436.log and the two suite legs")


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
                                   prefix=".r2436-", suffix=".tmp")
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