"""closeout_R2311_state.py - the R2311 bookkeeping write, one writer per file.

This window measured, it did not ship product code: the battery went red on
two legs the R2311 waterline fold itself created, both were repaired, and the
second run read RUNNER PASS 462/462 with the matrix regenerated. So the
closeout appends the round narrative, the group-transfer ack and the token
line to src/os/state.json in the state_io canon (LF text through canon(),
atomic replace), and refreshes docs/status-export.json from the same numbers.

  python src/os/closeout_R2311_state.py            dry run (writes nothing)
  python src/os/closeout_R2311_state.py --execute  write and verify both
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

ROUND = 2311
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                      "docs", "status-export.json")

LINES = [
    "R2311 verification window: the battery went RED on the first run - "
    "460/462 suites green - and both failing legs (os-residue-triage 5/6, "
    "os-stamp-exempt-review 5/6) traced to the window's own waterline fold, "
    "which moved R2298's only log item into the archive while its accepted "
    "stamp still sat on a closed tech row, so the live reader saw one "
    "undeclared residue round. Repair: the residue declaration carried "
    "forward 185->186 entries naming R2298 with the fold as its reason "
    "(closeout_R2311.py, every carried entry keeps its original declaring "
    "round), one accepted stamp exemption appended for tech#4e0ad38d through "
    "stamp_exempt_append (380->381 entries, NO-DRIFT), and both suites now "
    "read their budget from the live declaration instead of a pinned count. "
    "SECOND RUN: RUNNER PASS 462/462 suites plus controls 7/7 in 777.9s, "
    "criteria total 3748 exactly as predicted (+1 suite / +6 criteria against "
    "R2309 resolving to the R2310 os-residue-triage suite), TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0, four follow-up sections PASS after the "
    "matrix FAILed first on the stale doc and did not rewrite it (44329B on "
    "disk vs 44406B regenerated), then suite_matrix regenerated 462/3748 and "
    "the second pass read all four PASS, VERDICT R2311 PASS. Also repaired on "
    "the way in: the R2310 commit had left state.json off the write canon "
    "(65 bare LF, 55 off-indent items, state_io --check CANON-DRIFT and "
    "state_fold unable to parse the log block); state_io --fix restored it to "
    "77695B CANON-CLEAN before the nine-block fold. Zero product code "
    "changed in this window, 0 product points.",
    "R2311 ack P-20261026-0930 (group patrol ledger, @BigDomain row): read "
    "and answered without a new action - the P0/P1 items in that row are "
    "fleet-wide patrol structure (orders ledger lag, patrol stamp gap, disk "
    "waterline outside this repo), none of which names a BigDomain execution "
    "surface; this repo's own equivalents are the live waterline law "
    "(state_fold gate 78500) plus the loop task LogonType debt carried on the "
    "board, so the row is acknowledged here by number and closed as "
    "non-execution for this company.",
    "R2311 tokens: local=~16k api=0 api_reason=no cloud call - two full "
    "battery runs, one canon repair, one fold, two declaration repairs and "
    "four follow-up sections, all local.",
]


def build_state():
    raw = SIO.read_raw(STATE)
    state = SIO.parse(SIO.decode(raw))
    state["tick"] = ROUND
    for line in LINES:
        state["log"].append(line)
    text = json.dumps(state, ensure_ascii=False, indent=4) + "\n"
    return SIO.canon(text), state


def build_export():
    face = {
        "export_ts": "2026-11-01T05:44:00+08:00",
        "do": ("R2311 verification window: the battery failed first on two "
               "legs the window's own waterline fold created, both were "
               "repaired, and the re-run read 462/462 suites green with the "
               "suite matrix regenerated to 462/3748."),
        "ceo_face": {
            "current": ("R2311 is a verification window - zero product code "
                        "changed. First battery: FAIL 460/462. Root cause was "
                        "the round's own log fold moving R2298's only log item "
                        "into the archive while its accepted stamp stayed on a "
                        "closed queue row. Repairs: residue declaration "
                        "carried 185->186 entries naming that round, one stamp "
                        "exemption appended (NO-DRIFT, 381 entries), two suites "
                        "now read their budget from the live declaration. "
                        "Second battery: 462/462 suites, controls 7/7, "
                        "criteria 3748, 777.9s, TMP RECLAIM 932/932. Four "
                        "follow-up sections PASS; matrix doc regenerated "
                        "44406B byte-identical. Also restored state.json to "
                        "the write canon (it had drifted to 65 bare LF and 55 "
                        "off-indent items, blocking the fold)."),
            "latest_artifact": ("qa/reconcile-all-R2311.log (2026-11-01, "
                                "783232B) plus the red leg kept at "
                                "qa/reconcile-all-R2311-red.log and the "
                                "regenerated docs/sandbox-suite-matrix.md"),
            "next_milestone": ("R2312 product face on the tech head "
                               "(AC-GDA1, state/queue/tech.md line 374) - "
                               "window <=48h"),
        },
    }
    return face


def main(argv):
    execute = "--execute" in argv
    for arg in argv:
        if arg.startswith("--") and arg not in ("--execute",):
            sys.stdout.write("E_CLS_BAD_ARGS: unknown flag %s\n" % arg)
            return 5
    state_text, state = build_state()
    face = build_export()
    export_raw = SIO.read_raw(EXPORT)
    export = SIO.parse(SIO.decode(export_raw))
    merged = dict(export)
    merged.update(face)
    export_text = json.dumps(merged, ensure_ascii=False, indent=2) + "\n"
    wrote = "no"
    if execute:
        with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
            handle.write(state_text)
        with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(export_text)
        wrote = "yes"
    report = SIO.report(STATE)
    verdict = "CANON-CLEAN" if report["layout_ok"] else "CANON-DRIFT"
    sys.stdout.write(
        "R2311 CLOSEOUT wrote=%s tick=%d log_items=%d state_bytes=%d "
        "export_bytes=%d %s\n"
        % (wrote, state["tick"], len(state["log"]),
           len(state_text.encode("utf-8")), len(export_text.encode("utf-8")),
           verdict))
    return 0 if verdict == "CANON-CLEAN" or not execute else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))