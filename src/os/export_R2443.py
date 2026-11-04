"""R2443 export refresh: derived faces + the three CEO lines, one atomic write.

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

DO = ("R2443 verification window: the full reconcile battery on the committed "
      "R2442 tree came back RED on the R2442 suite's own block oracle (it "
      "compared an ordinary render against the stamp-aligned shipped doc), "
      "was repaired at its birth site so the provenance line is excluded on "
      "both sides while every other header/label line stays byte-compared, "
      "and the retry read 549/549 suites green at the pre-registered 4270 "
      "criteria")

LATEST = ("src/os/test_matrix_stamp_provenance_line.py repair (commit "
          "23901bcf, block() excludes the stamp_from line on both sides, "
          "suite back to 6/6) + qa/reconcile-all-R2443-retry.log (RUNNER PASS "
          "549/549 suites, controls 7/7, 1328.1s, criteria 4270 exactly) + "
          "qa/reconcile-all-R2443.log (the honest red leg) + "
          "docs/sandbox-suite-matrix.md regenerated stamp-aligned to 52990B "
          "at 549 suites / 4270 criteria with --check byte-identical, "
          "2026-11-04 21:12 +08:00")

NEXT = ("product window on the tech head state/queue/tech.md:510 prefix "
        "AC-PICIC1 (comma_binding_identity_face_compare): all three "
        "publisher faces asked over one tree so a split against the identity "
        "face cannot hide behind an agreeing pair (product-face-R2444 "
        "first=yes); due 2026-11-06 18:00")

RESULT = (
    "2026-11-04 R2443 verification window on the debt gate first=yes item "
    "(reconcile-battery-R2443 carried from R2442 at the pre-registered 549 "
    "suites / 4270 criteria): zero product code changed, the R2168 "
    "mixed-tree rule honoured. Leg 1 on the committed b55c6a2a tree read "
    "548/549 suites with the criteria total 4270 exactly as pre-registered "
    "(qa/reconcile-all-R2443.log kept as the red leg, 1258.9s, TMP RECLAIM "
    "932/932 against 326.59 MiB) and the only red was "
    "os-matrix-stamp-provenance-line at AC-MSPL1: the R2442 suite compared "
    "an ORDINARY render against the SHIPPED doc, which R2442 had "
    "regenerated stamp-aligned, so the doc legitimately carries a provenance "
    "line the ordinary render must not - an oracle that silently assumed the "
    "shipped artifact stays a plain render forever, while the product's own "
    "'records nothing extra' assertion still passed. Repaired at the BIRTH "
    "SITE, never by widening a criterion: block() excludes the stamp_from "
    "line on BOTH sides while every other header/label line stays "
    "byte-compared, and the ordinary render's lack of that line is still "
    "asserted on its own; the suite re-ran 6/6 at exit 0 and the repair was "
    "committed ALONE as 23901bcf. Retry on the committed repair tree: "
    "RUNNER PASS 549/549 suites plus controls 7/7 in 1328.1s at criteria "
    "4270 exactly, TMP RECLAIM 932/932 "
    "(qa/reconcile-all-R2443-retry.log). The four follow-up sections gave "
    "the designed first FAIL (matrix on-disk 52994B against regenerated "
    "52990B, no byte written), a stamp-aligned regeneration of "
    "docs/sandbox-suite-matrix.md to 52990B / 549 suites / 4270 criteria "
    "with --check byte-identical, and a re-run reading VERDICT R2443 PASS "
    "failing=none (fingerprint CLEAN domains=5, profile byte-identical, "
    "census DRIFT-CLEAN); both legs stay appended in the evidence tail. "
    "Debt: reconcile-battery-R2443 closed through the shipped debt_close at "
    "112389B -> 112392B (line=178, open 2->1, done 157->158, readback ok) "
    "and product-face-R2444 opened first=yes through debt_append at 112392B "
    "-> 112963B naming the tech head state/queue/tech.md:510 AC-PICIC1; no "
    "successor battery was registered because only a test file changed and "
    "the registry still reads 549 suites / 4270 criteria. Honest: zero "
    "product points claimed for this window.")

OUTS = ("src/os/test_matrix_stamp_provenance_line.py (birth-site repair, "
        "commit 23901bcf) + qa/reconcile-all-R2443.log (red leg, 855436B) + "
        "qa/reconcile-all-R2443-retry.log (green leg, RUNNER PASS 549/549) + "
        "docs/sandbox-suite-matrix.md (52990B at 549/4270, --check "
        "byte-identical) + docs/status-export.json (re-derived, 21/21 "
        "consistency) + state/debt.md (one closed, one opened) + "
        "src/os/closeout_R2443.py + src/os/backlog.md + src/os/state.json + "
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
                                   prefix=".r2443-", suffix=".tmp")
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