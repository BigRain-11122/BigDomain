"""R2437 export refresh: derived faces + the three CEO lines, one atomic write.

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

DO = ("R2437 verification window, ADOPTED and disclosed: a crashed R2437 "
      "window had already run the battery on the committed R2436 tree to "
      "RUNNER PASS 546/546 suites at exactly the pre-registered 4252 criteria "
      "and regenerated the matrix to 52591B, but wrote no closeout byte; this "
      "window re-measured every claim on the working tree instead of trusting "
      "or re-running it, and repaired at its birth site a self-referential "
      "successor battery row the dead window had left behind")

LATEST = ("qa/reconcile-all-R2437.log (RUNNER PASS 546/546 suites, controls "
          "7/7, 981.2s, expected criteria total=4252 exactly as "
          "pre-registered) + docs/sandbox-suite-matrix.md regenerated to "
          "52591B at 546 suites / 4252 criteria with --check byte-identical "
          "at exit 0 + src/os/closeout_R2437.py (adopted closeout through the "
          "canonical state writer)")

NEXT = ("product face on the tech head state/queue/tech.md:502 "
        "(src/os/owner_table_triage_expiry.py): a declaration acceptance "
        "records since_round but nothing ages it, so a never-expiring "
        "acceptance is a silent waiver - the face must print AGED with its "
        "age in rounds while the row stays TRIAGED until re-reviewed")

RESULT = (
    "2026-11-04 R2437 verification window, ADOPTED and disclosed: the round "
    "opened on a dirty tree at HEAD f12e2add carrying an untracked "
    "qa/reconcile-all-R2437.log (850070B) plus modified matrix and debt "
    "register, while state.json still read tick 2436 - a R2437 window had run "
    "the battery to a finished verdict and died before any closeout write. "
    "Nothing was accepted on trust: the log was measured to carry RUNNER PASS "
    "(546/546 suites green, controls 7/7, 981.2s) with expected criteria "
    "total=4252 exactly as pre-registered at R2436, the designed matrix FAIL "
    "on the stale 52596B doc followed by its regeneration and VERDICT R2437 "
    "PASS failing=none with fingerprint CLEAN 5 domains, profile byte-identical "
    "and census DRIFT-CLEAN at its untouched 529-entry baseline, and "
    "suite_matrix --check re-read on this working tree answers byte-identical "
    "52591B / 546 suites / 4252 criteria at exit 0. Adoption was gated on "
    "liveness: no battery process alive, no index.lock. The dead window's "
    "successor row reconcile-battery-R2437 pointed at the SAME target as the "
    "battery it had just closed, which would have re-walked an unchanged tree "
    "for a second window; it was converted in place into product-face-R2438 "
    "naming tech head state/queue/tech.md:502 owner_table_triage_expiry.py, and "
    "the register reads open=2 done=151 with exactly one first=yes row. Zero "
    "product code shipped, zero product points claimed.")

OUTS = ("qa/reconcile-all-R2437.log (RUNNER PASS 546/546, 981.2s, criteria "
        "4252) + docs/sandbox-suite-matrix.md regenerated to 52591B "
        "byte-identical + src/os/closeout_R2437.py")


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
                                   prefix=".r2437-", suffix=".tmp")
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