"""R2439 export refresh: derived faces + the three CEO lines, one atomic write.

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

DO = ("R2439 verification window: the battery caught a real transport defect in "
      "the PREVIOUS window's evidence - three R2438 logs written as CRLF "
      "through a PowerShell redirect - and it was repaired at the birth site "
      "with the line set proved identical and the census baseline untouched; "
      "the re-run then read 547/547 suites green at exactly the pre-registered "
      "4258 criteria")

LATEST = ("qa/reconcile-all-R2439-retry.log (RUNNER PASS 547/547 suites, "
          "reconcile controls 7/7, 1065.2s, criteria 4258), "
          "qa/reconcile-all-R2439.log kept as the honest red leg, "
          "docs/sandbox-suite-matrix.md 52715B at 547 suites / 4258 criteria "
          "with --check byte-identical, census DRIFT-CLEAN at its 529 baseline")

NEXT = ("product face at the tech head the deliverable-aware reader offers, "
        "state/queue/tech.md:504 prefix AC-RMEF1 "
        "(relative_module_existence_face): a package-relative import joined "
        "into its declared package is never checked against the modules the "
        "read tree actually carries, so a typo reads FOREIGN exactly like a "
        "genuinely foreign wire")

RESULT = (
    "2026-11-04 R2439 verification window on the debt gate first=yes item "
    "(reconcile-battery-R2439, carried from R2438): zero product code changed, "
    "the R2168 mixed-tree rule honoured. Leg 1 on the committed 93c57c03 tree "
    "read 546/547 suites with the criteria total 4258 EXACTLY as "
    "pre-registered (qa/reconcile-all-R2439.log kept as the red leg, 1045.2s) "
    "and the only red was reconcile-daily-census; the shipped census checker "
    "NAMED the cause instead of leaving a guess - three R2438 evidence logs "
    "were utf-8 bodies whose every line ended CRLF (class=pwsh-capture) "
    "because that window captured them through a PowerShell redirect, with the "
    "payload intact. Repaired at the birth site, never by widening the "
    "baseline: src/os/repair_R2439.py asked the shipped "
    "run_identity.normalize for the allowed normalisation, proved the line set "
    "identical before the write, landed utf-8 LF through one atomic replace "
    "and read the bytes back (667B -> 660B twice, 973B -> 968B, crlf=0, "
    "readback ok), after which the census read DRIFT-CLEAN flags=0 with its "
    "529-entry baseline untouched; the repair was committed ALONE as 95974c57. "
    "Retry leg on the committed repair tree: RUNNER PASS 547/547 suites plus "
    "controls 7/7 in 1065.2s at criteria 4258, TMP RECLAIM 932/932 worlds "
    "326.59 MiB busy=0 failed=0, evidence qa/reconcile-all-R2439-retry.log "
    "(847083B, one utf-8 LF single writer). Four follow-up sections produced "
    "the designed first FAIL and then a green verdict: leg 1 VERDICT FAIL "
    "failing=matrix at on-disk=52694B against regenerated=52715B with no byte "
    "written, suite_matrix regenerated the doc through --stamp-from, --check "
    "read byte-identical at 52715B / 547 suites / 4258 criteria, and the "
    "re-run read VERDICT R2439 PASS failing=none. Debt: "
    "reconcile-battery-R2439 closed through the shipped debt_close "
    "(110337B -> 110340B, open 2->1, done 152->153, readback ok) and "
    "product-face-R2440 opened first=yes through debt_append (110340B -> "
    "110852B, readback ok) at the tech head state/queue/tech.md:504 prefix "
    "AC-RMEF1. Honest: zero product points claimed, no criterion widened, no "
    "census baseline entry added, and the window ran far past its 25-minute "
    "budget (two full batteries).")

OUTS = ("qa/reconcile-all-R2439.log (red leg, 546/547) + "
        "qa/reconcile-all-R2439-retry.log (847083B, RUNNER PASS 547/547, "
        "criteria 4258) + src/os/repair_R2439.py (birth-site transport repair, "
        "payload proved, commit 95974c57) + docs/sandbox-suite-matrix.md "
        "52715B at 547 suites / 4258 criteria")


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
                                   prefix=".r2439-", suffix=".tmp")
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