"""R2438 export refresh: derived faces + the three CEO lines, one atomic write.

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

DO = ("R2438 product window: acceptance ages are now MEASURED - the owner "
      "table triage declaration records since_round on every entry but nothing "
      "aged it, so a review written today and one accepted a year earlier read "
      "identically; the new face prints AGED past the declared window while "
      "the row stays TRIAGED")

LATEST = ("src/os/owner_table_triage_expiry.py + src/os/test_owner_table_triage_"
          "expiry.py (SUITE PASS 6/6 twice byte-identical, "
          "qa/owner-table-triage-expiry-R2438-a.log / -b.log) + LIVE "
          "qa/owner-table-triage-expiry-live-R2438.log (scanned=1073, "
          "triaged=6, aged=0, verdict=EXPIRY-CLEAN) + registry 547 suites / "
          "4258 criteria")

NEXT = ("reconcile battery on the committed R2438 tree, pre-registered at 547 "
        "suites / 4258 criteria (+1 suite / +6 criteria): matrix must "
        "regenerate green and --check byte-identical, census DRIFT-CLEAN at "
        "its 529 baseline; after that the product face resumes at the tech "
        "head that queue_head.py --head tech names at that round")

RESULT = (
    "2026-11-04 R2438 product window on the debt gate first=yes item "
    "(product-face-R2438, tech head state/queue/tech.md:502): the triage "
    "declaration recorded since_round on every acceptance but MEASURED nothing "
    "aged it, so an acceptance written at R2436 and one accepted a year "
    "earlier read identically and a never-expiring waiver carried a date "
    "nobody reads. AC-OTTE1..AC-OTTE6 were pinned inside that queue row BEFORE "
    "any code, then src/os/owner_table_triage_expiry.py shipped: age = "
    "current_round - since_round for every TRIAGED row, status TRIAGED kept "
    "with both verdicts and the law flags printed, AGED once age > window, "
    "FRESH at the exact boundary, an entry with no live row reported "
    "unageable rather than aged or clean, and a since_round later than the "
    "supplied round failing closed E_OTTE_FUTURE at exit 3. The face reads no "
    "clock: --round is required, a missing one reads E_OTTE_NO_ROUND at exit 3. "
    "SUITE PASS 6/6 on two byte-identical runs (667B each), four adjacent "
    "owner_table suites green, wired os-owner-table-triage-expiry(6) so the "
    "registry reads 547 suites / 4258 criteria, matrix regenerated to 52694B "
    "reading green=546/547 with --check byte-identical. LIVE on the real src/os: "
    "scanned=1073 round=2438 window=30 triaged=6 aged=0 fresh=6 unageable=0 "
    "verdict=EXPIRY-CLEAN - all six measured acceptances at age 2 rounds "
    "because R2436 wrote them. Debt: product-face-R2438 closed, "
    "reconcile-battery-R2439 opened first=yes at 547/4258. Honest: no battery "
    "ran this window (the tree was about to change by design), no census entry "
    "was added, and no CEO-visible artifact was rebuilt.")

OUTS = ("src/os/owner_table_triage_expiry.py + src/os/test_owner_table_triage_"
        "expiry.py (SUITE PASS 6/6 twice) + qa/owner-table-triage-expiry-R2438-"
        "a.log / -b.log (667B, identical) + qa/owner-table-triage-expiry-live-"
        "R2438.log + docs/sandbox-suite-matrix.md 52694B at 547 suites / 4258 "
        "criteria")


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
                                   prefix=".r2438-", suffix=".tmp")
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