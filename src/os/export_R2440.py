"""R2440 export refresh: derived faces + the three CEO lines, one atomic write.

Every value is derived from the live tree; the self_drive block is asked of the
shipped export_R2431.self_drive() callable rather than re-derived here, so the
round keeps one derivation. This refresh runs AFTER the state append by design
(the R2433 ordering law).
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

DO = ("R2440 product window: a package-relative publish joined onto a declared "
      "package is now checked against the modules the read tree actually "
      "carries, so a typo reads MISSING-MODULE (naming the joined text and the "
      "package) instead of reading FOREIGN exactly like a genuinely foreign "
      "wire - while a join with a file behind it and a run with no package "
      "keep the parent reading")

LATEST = ("src/os/relative_module_existence_face.py + "
          "src/os/test_relative_module_existence_face.py (SUITE PASS 6/6 twice, "
          "qa/relative-module-existence-face-R2440.log 1510B, legs=2 "
          "identical=True adjacent=4 fails=0), "
          "qa/relative-module-existence-face-live-R2440.log (539B, REAL src/os: "
          "corpus=1216, publishers=11, missing=0), docs/sandbox-suite-matrix.md "
          "52828B at 548 suites / 4264 criteria with --check byte-identical")

NEXT = ("reconcile battery on the committed R2440 tree at the pre-registered "
        "548 suites / 4264 criteria (the R2168 mixed-tree rule owes it because "
        "this window changed product src bytes), then the product face at the "
        "tech head the deliverable-aware reader offers; due 2026-11-06 18:00")

RESULT = (
    "2026-11-04 R2440 product window on the debt gate first=yes item "
    "(product-face-R2440, tech head state/queue/tech.md:504 prefix AC-RMEF1, "
    "criteria AC-RMEF1..AC-RMEF6 pinned in that row at R2415 BEFORE any code): "
    "SHIPPED src/os/relative_module_existence_face.py plus its six-criteria "
    "suite. The reading is publish_relative_package_identity own audit asked at "
    "CALL time and the join is that module own join_package, so no second "
    "classifier and no second join exist; the one new fact is the module corpus "
    "MEASURED off the read tree own .py files and the one new word is "
    "MISSING-MODULE, printed with the joined text and the declared package when "
    "a join has no file behind it. A join WITH a file behind it keeps the "
    "parent reading with verdict, rows and counts compared against the parent "
    "audit, and NO declared package keeps the parent reading byte for byte "
    "while measuring no corpus at all. SUITE PASS 6/6 twice with an identical "
    "digest plus four adjacent suites green (qa/relative-module-existence-"
    "face-R2440.log, 1510B, legs=2 identical=True adjacent=4 fails=0), wired "
    "os-relative-module-existence-face(6) so the registry reads 548 suites / "
    "4264 criteria, matrix regenerated through --stamp-from to 52828B at "
    "548/4264 with --check byte-identical. LIVE on the REAL src/os with "
    "--package src.os (539B): corpus=1216, scanned=1214, publishers=11 "
    "wire=11, relative=0, missing=0 - the tree carries no package-relative "
    "publish line, so the MISSING-MODULE case is proved on fixtures only and is "
    "NOT claimed as a live catch. Board: row 504 stamped, TWO real gap rows "
    "seeded from this window own measured limits (relative_module_corpus_scope, "
    "AC-RMSC1..6 and relative_package_presence_refusal, AC-RMPP1..6), and a "
    "stale delivered row (494 AC-BEDP1, shipped at R2432) closed at the round "
    "that delivered it so the floor reads FLOOR-MET 5/5 10/10 10/10 with "
    "discounted=0. Debt: product-face-R2440 closed through the shipped "
    "debt_close (110852B -> 110855B, line=174, open 2->1, done 153->154, "
    "readback ok) and reconcile-battery-R2441 opened first=yes through "
    "debt_append at the pre-registered 548/4264 (110855B -> 111148B, readback "
    "ok). Honest: two product points for a runnable internal reading, no "
    "CEO-visible artifact rebuilt, one first-draft key-order defect caught by "
    "AC-RMEF5 and fixed in the module with no criterion widened.")

OUTS = ("src/os/relative_module_existence_face.py (module corpus + "
        "MISSING-MODULE reading) + src/os/test_relative_module_existence_"
        "face.py (6 criteria) + qa/relative-module-existence-face-R2440.log "
        "(1510B, legs=2 identical=True adjacent=4 fails=0) + "
        "qa/relative-module-existence-face-live-R2440.log (539B real tree) + "
        "docs/sandbox-suite-matrix.md 52828B at 548/4264 + state/queue/tech.md "
        "(row 504 stamped, 2 gap rows seeded, stale row 494 closed) + "
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
                                   prefix=".r2440-", suffix=".tmp")
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