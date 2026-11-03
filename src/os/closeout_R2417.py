# closeout_R2417.py - state log append, export refresh, heartbeat.
# One atomic write per file, each proved by a read-back. ASCII only.
import datetime
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")

sys.path.insert(0, BASE)
import check_export_consistency as CHECK  # noqa: E402

TICK = 2417

DO = ("R2417 product: runner_abort_history ages every ABORTED battery body against its own "
      "round's retry family, so an abort that a green leg of the same round already superseded "
      "is named SUPERSEDED with both files instead of reading like live debt; the live read of "
      "the real 2461-log pile splits 21 aborts into 16 LIVE-ABORT and 5 ORPHAN-ABORT and "
      "corrects the seed's own premise")

LATEST = ("src/os/runner_abort_history.py + qa/runner-abort-history-R2417.log (1553B, legs=2 "
          "identical=True adjacent=4 fails=0) + qa/runner-abort-history-live-R2417.log (1917B, "
          "AGES aborted=21 SUPERSEDED=0 LIVE-ABORT=16 ORPHAN-ABORT=5)")

LAST = ("src/os/publish_relative_package_identity.py + "
        "qa/publish-relative-package-identity-R2415.log (1310B, legs=2 identical=True)")

NEXT = ("next window owes the battery the R2417 src/os change opened (536 suites / 4192 "
        "criteria pre-registered against the registry's own read) and then the debt gate: "
        "loop-s4u-reconcile (stale, needs an elevated S4U re-registration) and matrix-stamp-compare "
        "(the follow-up section still byte-compares a freshly stamped render)")

LOG = [
    ("2026-11-03 R2417 product window (five-silence scan at open found a DIRTY tree, not a "
     "quiet one, and that is the first finding: git status carried a modified "
     "src/sandbox/reconcile_all.py plus three untracked files whose timestamps read 17:17-17:18, "
     "i.e. an earlier attempt at this same round that never committed, with no BigDomain python "
     "process alive (checked by command line before touching anything) and no index.lock. The "
     "ledger carries no @BigDomain row (zero unreplied); the content-addressed decisions diff "
     "reads 105 tokens with new=0; benchmarks refreshed 2026-11-03 inside the seven-day gate; the "
     "tech queue head read line=484 prefix=AC-RAH1 claimable=11 against a floor of 10. Instead of "
     "discarding the interrupted work or re-deriving it, this window AUDITED it, re-ran every "
     "proof from scratch, and only then kept it - so every number below was measured now, not "
     "inherited."),
    ("2026-11-03 R2417 what shipped: src/os/runner_abort_history.py plus "
     "src/os/test_runner_abort_history.py, against AC-RAH1..AC-RAH6 pinned in state/queue/tech.md "
     "line 484 at R2403 BEFORE any code. The gap is measured: runner_abort_face names the suite a "
     "body died on, but nothing said whether that abort still matters. One reading pairs an "
     "ABORTED body with its own round's retry family and answers SUPERSEDED (a leg of the same "
     "round ended RUNNER PASS, both file names published, exit 0), LIVE-ABORT (no green leg, exit "
     "2), ORPHAN-ABORT (the name carries no canonical round token, so no family is invented for "
     "it, exit 3), NOT-ABORTED and UNREADABLE. Every law is asked at CALL time: the abort verdict "
     "and the PASS word are runner_abort_face's own, the family and leg order are "
     "followup_retry_legs' leg_names, the canonical stem scope is followup_history's NAME_RE, and "
     "the round token in a name is round_evidence's file_round - no second parser in the tree."),
    ("2026-11-03 R2417 evidence and board: SUITE PASS 6/6 twice with an identical digest plus "
     "four adjacent suites green (qa/runner-abort-history-R2417.log, 1553B, legs=2 "
     "identical=True adjacent=4 fails=0), wired os-runner-abort-history(6) in "
     "src/sandbox/reconcile_all.py so the registry reads 536 suites / 4192 criteria. LIVE, not a "
     "plan: qa/runner-abort-history-live-R2417.log (1917B, one utf-8 LF writer) ages the REAL "
     "pile of 2461 logs = 754 COMPLETE + 21 ABORTED + 1686 UNREADABLE as 16 LIVE-ABORT and 5 "
     "ORPHAN-ABORT, with the module digest a24e8b744b7ac98c unchanged across the read. Tech row "
     "484 stamped [done 2026-11-03 R2417] with its discharge line; the claim moved tech claimable "
     "11 -> 10, still at its floor, so no filler row was seeded and the gauge reads FLOOR-MET "
     "main 5/5 tech 10/10 explore 10/10."),
    ("2026-11-03 R2417 honest disclosures: (a) the seed's own premise is CORRECTED by "
     "measurement, not smoothed - it claimed reconcile-all-R2393-retry2.log has a green sibling "
     "leg, but its family is 2 other legs and NEITHER ended RUNNER PASS (that round's retry leg "
     "read 518/519), so the abort is genuine live debt and SUPERSEDED=0 on the real pile; "
     "SUPERSEDED is therefore proved on fixtures only and is not claimed as a live catch. (b) The "
     "17:17-17:18 files were produced by an interrupted earlier attempt at this round; they were "
     "kept only after this window re-ran the suite, the two-leg capture and the live read itself, "
     "and the second leg was written by the shipped evidence_capture callable, not by hand. (c) NO "
     "battery ran this window: 536 suites / 4192 criteria is a WIRING count (535/4186 at R2415 "
     "plus this window +1 suite / +6 criteria) and reconcile-battery-R2417 is owed next on the "
     "committed tree. (d) tasks.md was not touched - it is the P-47 canonical board and carries no "
     "row for this tech slice. (e) ORPHAN-ABORT is 5 and every one of them is a reconcile-daily-* "
     "log, i.e. genuinely outside the battery naming scope, not a defect."),
    ("2026-11-03 R2417 self-heal check: BigDomain-OSLoop still exists and is Running, but its "
     "Principal.LogonType reads Interactive, which the 2026-09-29 machine law forbids for every "
     "lane task; src/os/register_loop_task.ps1 passes an explicit S4U principal and needs an "
     "elevated shell, and this session is unelevated, so the definition was left untouched "
     "(hundred-and-seventy-second consecutive disclosure, carried as the stale row "
     "loop-s4u-reconcile in state/debt.md)."),
    ("R2417 tokens: local=~19k api=0 api_reason=product window - one ageing face and its "
     "six-criteria suite kept from an interrupted attempt only after a full re-proof (suite, "
     "two-leg capture, live read), one runner wiring line, one board stamp with its discharge "
     "line, one live read over 2461 real evidence bodies that refuted the seed's own premise, and "
     "the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches"),
]


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_atomic(path, text):
    temp = path + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.replace(temp, path)
    with io.open(path, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != text:
        raise SystemExit("READBACK MISMATCH %s" % path)
    return len(text.encode("utf-8"))


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def main():
    state = read_json(STATE)
    state["tick"] = TICK
    state.setdefault("log", []).extend(LOG)
    state_bytes = write_atomic(STATE, dump(state))
    print("STATE tick=%d log_items=%d bytes=%d" % (TICK, len(state["log"]), state_bytes))

    derived, state_again, export, pat = CHECK.recompute()
    export["export_ts"] = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))).replace(microsecond=0).isoformat()
    export["do"] = DO
    face = export.setdefault("ceo_face", {})
    face["current"] = DO
    face["latest_artifact"] = LATEST
    face["last_artifact"] = LAST
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = "2026-11-04T23:00:00+08:00"
    face["updated_at"] = export["export_ts"]
    export["self_drive"] = derived
    label = pat["tick_row_label"]
    results = [row for row in export.get("results", [])
               if not (isinstance(row, list) and len(row) >= 2 and row[1] == label)]
    export["results"] = [[str(TICK), label], [str(TICK), DO]] + results
    export_bytes = write_atomic(EXPORT, dump(export))
    print("EXPORT bytes=%d tick=%d" % (export_bytes, state_again["tick"]))

    with io.open(HEART, "a", encoding="utf-8", newline="\n") as handle:
        handle.write("%s tick=%d round=R2417 product=runner_abort_history\n"
                     % (export["export_ts"], TICK))
    print("HEARTBEAT appended tick=%d" % TICK)

    lines, npass, nfail = CHECK.check()
    print("\n".join(lines[-3:]))
    print("CHECK pass=%d fail=%d" % (npass, nfail))
    return 0 if nfail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())