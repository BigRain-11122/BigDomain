"""R2444 export refresh: derived faces + the three CEO lines, one atomic write.

Every value is derived from the live tree; the self_drive block is asked of the
shipped export_R2431.self_drive() callable rather than re-derived here, so the
round keeps one derivation, and the queue block is asked of queue_floor. This
refresh runs AFTER the state append by design (the R2433 ordering law).
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

STAMP = "2026-11-04T21:52:00+08:00"

DO = ("R2444 product window: comma_binding_identity_face_compare asks all "
      "three publisher faces over one tree and MEASURES each face's "
      "receiver-table seam instead of asserting it, so the second path the "
      "identity face rides (comma_binding_consumer_wire.wire_audit_script) is "
      "now published as a fact - LIVE src/os reads FACES-AGREE with 11 "
      "publishers and the identity face calling receivers_for:33 plus "
      "consumer_wire:33 while both sibling faces call one seam only")

LATEST = ("src/os/comma_binding_identity_face_compare.py + "
          "src/os/test_comma_binding_identity_face_compare.py (commit in this "
          "window, SUITE PASS 6/6 twice with identical digest "
          "6D174EB5708FE9E5, three adjacent comma suites green) + "
          "qa/comma-binding-identity-face-compare-R2444.log + "
          "qa/comma-binding-identity-face-compare-live-R2444.log (real tree "
          "FACES-AGREE 11 publishers 33 rows) + "
          "docs/sandbox-suite-matrix.md regenerated stamp-aligned to 55305B "
          "at 550 suites / 4276 criteria with --check byte-identical, "
          "2026-11-04 21:47 +08:00")

NEXT = ("reconcile-battery-R2445 first: the full battery on the committed "
        "R2444 tree at the pre-registered 550 suites / 4276 criteria, with "
        "the state.json fold (78854B against the 78500B gate) due before that "
        "battery is claimed clean; then the tech head "
        "state/queue/tech.md:512 prefix AC-PFRD1 "
        "(comma_binding_face_row_drift); due 2026-11-06 18:00")

RESULT = (
    "2026-11-04 R2444 product window on the debt gate first=yes item "
    "(product-face-R2444, tech head state/queue/tech.md:510 prefix AC-PICIC1, "
    "criteria pinned there at R2430 BEFORE any code): SHIPPED "
    "src/os/comma_binding_identity_face_compare.py plus its six-criteria "
    "suite. The sibling reading compared the from-import and relative faces "
    "only, while the identity face reaches the comma-aware receiver table "
    "through comma_binding_consumer_wire.wire_audit_script - so a regression "
    "there could move the identity verdict with both siblings still "
    "agreeing. The shipped module asks the three shipped faces at CALL time, "
    "restates no table, and measures each face's seam by wrapping both seam "
    "providers for the duration of that face's own audit: LIVE on src/os the "
    "sibling faces read receivers_for:33 while the identity face reads "
    "receivers_for:33 AND consumer_wire:33, differences=0, verdict=FACES-AGREE "
    "at 11 publishers and 33 rows. SUITE PASS 6/6 twice identical digest "
    "6D174EB5708FE9E5 with three adjacent comma suites green "
    "(qa/comma-binding-identity-face-compare-R2444.log), wired "
    "os-comma-binding-identity-face-compare(6) so the registry reads 550 "
    "suites / 4276 criteria; docs/sandbox-suite-matrix.md regenerated "
    "stamp-aligned to 55305B with --check byte-identical. One REAL gap row "
    "seeded from this window's own limit (AC-PFRD1..AC-PFRD6): the compare "
    "reads verdicts and publisher sets, so MEASURED here a per-line module "
    "rewritten to drifted_wire under an unchanged WIRE verdict still reads "
    "FACES-AGREE rc=0, and the faces do not share a row shape (6/7/8 keys). "
    "Debt: product-face-R2444 closed at 112963B -> 112966B (line=179, open "
    "2->1, done 158->159, readback ok), reconcile-battery-R2445 opened "
    "first=yes at 112966B -> 113460B at the pre-registered 550/4276, and "
    "fold-due-R2445 opened first=no at 113460B -> 113809B because state.json "
    "stands at 78854B against the 78500B gate. Group-layer anomaly reported "
    "read-only and not repaired: the group orders.md tail carries literal "
    "merge-conflict markers, and the cross-repo write ban forbids this "
    "station from touching it.")

OUTS = ("src/os/comma_binding_identity_face_compare.py (new, 3 faces, "
        "measured seams) + src/os/test_comma_binding_identity_face_compare.py "
        "(new, 6/6 twice identical) + src/os/live_R2444.py + "
        "qa/comma-binding-identity-face-compare-R2444.log + "
        "qa/comma-binding-identity-face-compare-live-R2444.log + "
        "src/sandbox/reconcile_all.py (one registry row, 550/4276) + "
        "docs/sandbox-suite-matrix.md (55305B, --check byte-identical) + "
        "state/queue/tech.md (row 510 discharged, real gap seed at 512) + "
        "state/debt.md (one closed, two opened) + docs/status-export.json + "
        "src/os/closeout_R2444.py + src/os/backlog.md + src/os/state.json + "
        "heartbeat.txt")


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
                                   prefix=".r2444-", suffix=".tmp")
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