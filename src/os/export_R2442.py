"""R2442 export refresh: derived faces + the three CEO lines, one atomic write.

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

STAMP = carrier.STAMP

DO = ("R2442 product window: a render told to borrow another document's "
      "stamp now RECORDS that borrow inside the artifact and --check reads "
      "it back, so a borrowed-stamp doc is no longer byte-for-byte "
      "indistinguishable from an ordinary render - while an ordinary render "
      "keeps today's bytes and a doc written before this law still checks "
      "green")

LATEST = ("src/os/matrix_stamp_provenance_line.py (one law, two directions: "
          "segment() writes the provenance line, recorded_source() reads it "
          "back) + qa/matrix-stamp-provenance-line-R2442.log (3787B, SUITE "
          "PASS 6/6 twice, legs=2 identical=True, adjacent=3 fails=0) + "
          "qa/matrix-stamp-provenance-line-live-R2442.log (463B, crlf=0) + "
          "docs/sandbox-suite-matrix.md regenerated stamp-aligned to 52994B "
          "at 549 suites / 4270 criteria with --check byte-identical")

NEXT = ("verification window on the committed R2442 tree: the full reconcile "
        "battery at the pre-registered 549 suites / 4270 criteria "
        "(reconcile-battery-R2443 first=yes), then back to the product face "
        "the reader offers at state/queue/tech.md:510 prefix AC-PICIC1; due "
        "2026-11-06 18:00")

RESULT = (
    "2026-11-04 R2442 product window on the debt gate first=yes item "
    "(product-face-R2442, tech head state/queue/tech.md:508 prefix AC-MSPL1 "
    "matrix_stamp_provenance_line, AC-MSPL1..AC-MSPL6 pinned there at R2418 "
    "BEFORE any code): MEASURED at R2418 that --stamp-from let a render "
    "borrow another document's stamp while the artifact could not say so - "
    "the generation command line was a fixed format string naming only "
    "--evidence. SHIPPED src/os/matrix_stamp_provenance_line.py: ONE law "
    "with two directions, segment() rendering the line an artifact must "
    "carry for a given source and recorded_source() reading that same line "
    "back, with the label owned by suite_matrix_patterns.json and a patterns "
    "file without it failing closed. Wired at suite_matrix's own two call "
    "sites, so --check on a stamp-aligned doc recovers the borrow instead of "
    "reporting drift, and an artifact written before this law still checks "
    "byte-identical. MEASURED on real renders: ordinary 52827B with no "
    "provenance line and its header/label block byte-identical to the "
    "shipped doc, stamp-from 52871B naming its source, --check PASS on all "
    "three states. SUITE PASS 6/6 twice with an identical digest plus three "
    "adjacent suites green (qa/matrix-stamp-provenance-line-R2442.log, "
    "3787B), wired os-matrix-stamp-provenance-line(6) so the registry reads "
    "549 suites / 4270 criteria; the shipped matrix was regenerated "
    "stamp-aligned to 52994B at 549/4270 with --check byte-identical. Board: "
    "row 508 stamped, one REAL gap row seeded (matrix_stamp_from_liveness, "
    "AC-MSFL1..AC-MSFL6: a recorded source is never checked for existence), "
    "floor FLOOR-MET 5/5 10/10 10/10, head now line 510 AC-PICIC1. Debt: "
    "product-face-R2442 and fold-due-R2442 closed, reconcile-battery-R2443 "
    "opened first=yes at the pre-registered 549/4270. Honest: two product "
    "points for an internal artifact-level reading, no CEO-visible business "
    "surface rebuilt.")

OUTS = ("src/os/matrix_stamp_provenance_line.py + "
        "src/os/test_matrix_stamp_provenance_line.py + "
        "src/sandbox/suite_matrix.py (two call sites) + "
        "src/sandbox/suite_matrix_patterns.json (label) + "
        "src/sandbox/reconcile_all.py (wiring) + "
        "qa/matrix-stamp-provenance-line-R2442.log (3787B) + "
        "qa/matrix-stamp-provenance-line-live-R2442.log (463B) + "
        "docs/sandbox-suite-matrix.md (52994B at 549/4270) + "
        "docs/status-export.json (re-derived, 21/21 consistency) + "
        "state/queue/tech.md (row 508 stamped, one seed) + "
        "state/debt.md (two closed, one opened) + src/os/backlog.md + "
        "src/os/state.json + heartbeat.txt")


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
                                   prefix=".r2442-", suffix=".tmp")
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