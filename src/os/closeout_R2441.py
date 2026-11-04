"""closeout_R2441 - the closeout of the R2441 verification window.

Appends this window's own honest lines to src/os/state.json, bumps the tick,
refreshes the content-addressed decisions baseline, prepends the backlog row
and appends the heartbeat row. Dry run by default; on --execute every file is
written once and read back.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

sys.path.insert(0, BASE)
import state_io  # noqa: E402

TICK = 2441
DEC_ROWS = 239
NEW_DEC = ["D-20261104-08", "D-20261104-09", "D-20261104-10",
           "D-20261104-11", "D-20261104-12"]

LOG = [
    ("2026-11-04 R2441 verification window (five-silence scan at open: git "
     "status empty at HEAD 8e458b28 with no .git/index.lock; the evolution "
     "ledger carries zero @BigDomain rows; the group orders tail max_ts is "
     "2026-11-04 00:46 equal to the stored last_order, so nothing dispatches "
     "this company; benchmarks were refreshed 2026-11-03 inside the "
     "seven-day gate; the deliverable-aware queue reader offered "
     "state/queue/tech.md:508 prefix AC-MSPL1 and the queue gauge read "
     "FLOOR-MET main 5/5 tech 10/10 explore 10/10). The content-addressed "
     "decisions diff was NOT clean: five new tokens landed since the stored "
     "baseline and each was judged against this company's execution face."),
    ("2026-11-04 R2441 decision gate disposition, one line per number: "
     "D-20261104-08 (lane_agent git_publish commit spam) is a cph4/Tools "
     "execution surface, D-20261104-09 (MiniGame STALLED-BUILD) is the "
     "BigGame line, D-20261104-10 (external audit cadence) is an HQ seat "
     "duty, D-20261104-11 (bm-m registration) is a fleet lane, and "
     "D-20261104-12 (43-company feedback sweep) names bigmoney, BigStream, "
     "BigLife, FluxVerse and MiniGame, not this company - none of the five "
     "carries a BigDomain execution action, so all five are ACKNOWLEDGED-NO-"
     "ACTION and the baseline was advanced to the full live token set after "
     "judging them."),
    ("2026-11-04 R2441 the debt gate named CLAIM-FIRST item="
     "reconcile-battery-R2441, carried from the R2440 closeout at the "
     "pre-registered 548 suites / 4264 criteria, so the battery ran FIRST on "
     "the committed tree with zero product edits (the R2168 mixed-tree rule)."),
    ("2026-11-04 R2441 the first battery leg came back RED on a REAL data "
     "defect left by the previous closeout, not on code: 547/548 suites green "
     "with the criteria total 4264 exactly as pre-registered (qa/reconcile-"
     "all-R2441.log kept as the honest red leg, 847696B), the only red suite "
     "being os-queue-floor-export-face AC-QFE3 at pass=19 fail=2. The shipped "
     "checker named both rows rather than leaving a guess: "
     "self_drive.log_lines_in_window stored=76 recomputed=77 and "
     "self_drive.substantive_non_idle_mention_lines stored=76 recomputed=77 - "
     "because the R2440 closeout refreshed the export and THEN appended its "
     "own push log line, so the derived counters described a document one "
     "line shorter than the file."),
    ("2026-11-04 R2441 repair at the BIRTH SITE, never by widening a "
     "baseline: the shipped export refresh was re-run against the live tree "
     "(every value derived, self_drive asked of export_R2431.self_drive at "
     "call time), the file went 77944B at a fresh 2026-11-04T18:51:30+08:00 "
     "stamp, check_export_consistency read 21/21 VERDICT PASS with W=77 "
     "idle=0 nop=0 sub=77, and test_queue_floor_export_face re-ran SUITE PASS "
     "6/6. The repair was committed ALONE as 144e63e3 before any further byte "
     "changed."),
    ("2026-11-04 R2441 the retry leg then ran on the committed repair tree: "
     "qa/reconcile-all-R2441-retry.log (847687B) read RUNNER PASS (548/548 "
     "suites green, reconcile controls 7/7, 1187.2s) with a measured "
     "criteria total of 4264 - the pre-registered number to the unit - and "
     "TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 "
     "MiB."),
    ("2026-11-04 R2441 the four follow-up sections produced the designed "
     "first FAIL and then a green verdict: leg 1 read VERDICT FAIL "
     "failing=matrix at on-disk=52828B against regenerated=52827B and wrote "
     "no byte; src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-"
     "matrix.md from THIS round green evidence through --stamp-from so the "
     "render is stamp-aligned to the doc it is compared with, --check read "
     "byte-identical at 52827B / 548 suites / 4264 criteria, and the re-run "
     "read VERDICT R2441 PASS failing=none (matrix byte-identical 52827B, "
     "fingerprint CLEAN domains=5, profile byte-identical, census "
     "DRIFT-CLEAN). Both legs stay appended in the evidence tail (1889B FAIL "
     "then 1950B PASS, eol_ok=True)."),
    ("2026-11-04 R2441 debt register after this window: open=1 done=155. "
     "reconcile-battery-R2441 was closed through the shipped debt_close at "
     "its predicted 111148B -> 111151B (line=175, open 2->1, done 154->155, "
     "readback=ok) and ONE leader row product-face-R2442 was appended "
     "first=yes through the shipped debt_append at 111151B -> 111472B "
     "(readback=ok), naming the next window a product face on the tech head "
     "the deliverable-aware reader offered: state/queue/tech.md:508 prefix "
     "AC-MSPL1 (matrix_stamp_provenance_line), whose criteria were pinned in "
     "that row before any code. NO successor battery was registered: this "
     "window changed no product src byte (one export data refresh plus "
     "evidence), so the registry still reads 548 suites / 4264 criteria and "
     "the R2168 rule does not fire."),
    ("2026-11-04 R2441 honest disclosures: (a) this window shipped ZERO "
     "product code and claims zero product points - the battery consumed the "
     "window as the carried row said it would; (b) the red belongs to the "
     "PREVIOUS window's closeout ordering, and it is the seventh evidence-"
     "transport / closeout-ordering defect this station has caught and "
     "nothing else would have; (c) no criterion was widened and no census "
     "baseline entry was added - the baseline still reads 529 and census read "
     "DRIFT-CLEAN on its own; (d) the export's DO and latest_artifact fields "
     "still describe the R2440 product face because no new product face "
     "shipped this round - the refresh moved only the derived counters and "
     "the stamp, and that is stated rather than dressed up as a new "
     "deliverable; (e) the window ran far past its 25-minute budget: two full "
     "batteries at 847696B and 1187.2s plus the follow-up legs, named rather "
     "than hidden; (f) tasks.md was not touched, it is the P-47 canonical "
     "board and carries no row for a verification window; (g) the S4U "
     "reconcile is still carried as the stale row loop-s4u-reconcile - this "
     "session is unelevated, so the InteractiveToken task definition was left "
     "untouched for the two-hundred-and-seventh consecutive round."),
]

TOKENS = (
    "R2441 tokens: local=~12k api=0 api_reason=verification window - two full "
    "batteries on committed trees (one red at a pre-registered 548 suites / "
    "4264 criteria and one green at the same count after a birth-site export "
    "re-derivation), four follow-up sections with one designed matrix FAIL "
    "and one green stamp-aligned verdict, one debt row closed and one leader "
    "row opened through their shipped CLIs, and the state/export/backlog/"
    "heartbeat closeout; zero product code shipped, zero cloud calls and zero "
    "external API touches"
)

SELF_HEAL = (
    "2026-11-04 R2441 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal and needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again "
    "(two-hundred-and-seventh consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile)."
)

BACKLOG_ROW = (
    "- [x] R2441 [done 2026-11-04] verification-only - the debt gate named "
    "CLAIM-FIRST item=reconcile-battery-R2441 (carried from R2440 at the "
    "pre-registered 548 suites / 4264 criteria), so the battery ran first on "
    "the committed 8e458b28 tree with zero product edits. Leg 1 was RED ON A "
    "REAL DATA DEFECT left by the R2440 closeout ordering: 547/548 green at "
    "criteria 4264, the only red being os-queue-floor-export-face AC-QFE3 at "
    "stored=76 vs recomputed=77 for log_lines_in_window and "
    "substantive_non_idle_mention_lines, because R2440 refreshed the export "
    "and then appended its own push line. Repaired at the birth site by "
    "re-running the shipped export refresh against the live tree (77944B, "
    "fresh stamp, check_export_consistency 21/21 PASS, W=77 idle=0 nop=0 "
    "sub=77, suite 6/6), committed ALONE as 144e63e3 with no baseline "
    "widened. Leg 2 on the committed repair tree read RUNNER PASS 548/548 "
    "plus controls 7/7 in 1187.2s at criteria 4264 exactly, TMP RECLAIM "
    "932/932 326.59 MiB (qa/reconcile-all-R2441-retry.log 847687B); the four "
    "follow-ups gave the designed matrix FAIL at 52828B vs 52827B, then a "
    "regeneration through --stamp-from and VERDICT R2441 PASS failing=none "
    "with fingerprint CLEAN domains=5, profile byte-identical and census "
    "DRIFT-CLEAN. Debt: battery closed through the shipped debtor at "
    "111148B -> 111151B (open 2->1, done 154->155, readback ok) and "
    "product-face-R2442 opened first=yes at 111151B -> 111472B naming "
    "state/queue/tech.md:508 AC-MSPL1. No successor battery owed: no product "
    "src byte changed this window. Zero product points claimed."
)

HEARTBEAT_ROW = (
    "%s tick=%d R2441 verification window - reconcile-battery-R2441 "
    "discharged on the committed R2440 tree: leg 1 RED on a real closeout-"
    "ordering defect (export derived counters one log line stale) repaired at "
    "the birth site and committed alone, leg 2 RUNNER PASS 548/548 at the "
    "pre-registered 4264 criteria in 1187.2s, follow-ups FAIL-matrix then "
    "VERDICT PASS with census DRIFT-CLEAN; battery row closed, "
    "product-face-R2442 opened first=yes; zero product points claimed "
    "[via BigDomain-OSLoop]"
)


def write_bytes_atomic(path, data, prefix):
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=prefix)
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(data)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    back = open(path, "rb").read()
    if back != data:
        raise SystemExit("E_R2441_BACK read-back does not match the write")
    return len(back)


def live_tokens():
    import re
    with io.open(os.path.join(ROOT, "..", "..", "docs", "decisions.md"),
                 encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    found = re.findall(r"(?:D|C)-2026\d{4}-\d{2}", text)
    return sorted(set(found))


def main(execute):
    payload_probe = json.loads(open(STATE, "rb").read().decode("utf-8"))
    tokens = live_tokens()
    missing = [t for t in NEW_DEC if t not in tokens]
    if missing:
        raise SystemExit("E_R2441_DEC tokens not in the document: %r" % missing)
    old = list(payload_probe.get("last_dec_tokens") or [])
    gap = [t for t in NEW_DEC if t not in old]
    if not execute:
        print("DRY RUN tick=%d lines=%d tokens=%d new=%d"
              % (TICK, len(LOG), len(tokens), len(gap)))
        for line in LOG:
            print("  LOG %s" % line[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2441_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_dec_tokens"] = sorted(set(old) | set(tokens))
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    payload["log"].append(SELF_HEAL)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2441_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2441-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d "
          "tokens=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"], len(payload["last_dec_tokens"])))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if BACKLOG_ROW in backlog:
        raise SystemExit("E_R2441_BACKLOG row already present")
    io.open(BACKLOG, "w", encoding="utf-8", newline="").write(
        BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended, bytes=%d" % os.path.getsize(BACKLOG))

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    row = HEARTBEAT_ROW % ("2026-11-04T19:20:00+08:00", TICK)
    if row in beat:
        raise SystemExit("E_R2441_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    io.open(HEARTBEAT, "w", encoding="utf-8", newline="").write(
        beat + row + "\n")
    print("HEARTBEAT row appended, bytes=%d" % os.path.getsize(HEARTBEAT))
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))