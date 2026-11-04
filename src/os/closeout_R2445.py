"""closeout_R2445 - state / backlog / heartbeat closeout for the R2445
verification window (reconcile-battery-R2445).

Writes the state log through state_io.canon with a byte read-back, prepends
the backlog row, appends the heartbeat row, and refuses any drift. Run with
--execute to write; the default is a dry run.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

STATE = os.path.join(BASE, "state.json")
BACKLOG = os.path.join(BASE, "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2445
DEC_ROWS = 239
ORDER_TS = "2026-11-04 14:35"

LOG = [
    "2026-11-04 R2445 verification window (five-silence scan at open: git "
    "status empty at HEAD 15719180 with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions "
    "diff read 239 rows and 118 tokens with new=0 and gone=0 against the "
    "stored baseline; benchmarks were refreshed 2026-11-03 inside the "
    "seven-day gate; the queue gauge read FLOOR-MET main 5/5 tech 10/10 "
    "explore 10/10 and the deliverable-aware reader offered "
    "state/queue/tech.md:512 prefix AC-PFRD1). Two NEW group order rows "
    "landed after the stored baseline and each was judged against this "
    "company's execution face: OB-20261104-140817-341 dispatches bm-a for the "
    "fleet artifact push, and OB-20261104-1435-GIMMEALL-NAMING dispatches "
    "bm-a/bm-b/bm-c/bm-m for the MiniGame variant naming sweep - neither "
    "carries a BigDomain action, so both are ACKNOWLEDGED-NO-ACTION and the "
    "baseline was advanced to 2026-11-04 14:35. The debt gate named "
    "CLAIM-FIRST item=reconcile-battery-R2445 carried from R2444 at the "
    "pre-registered 550 suites / 4276 criteria, so the battery ran FIRST on "
    "the committed tree with zero product edits (the R2168 mixed-tree rule).",

    "2026-11-04 R2445 the first battery leg came back RED on the "
    "CEO-VISIBLE matrix face: 549/550 suites green with the criteria total "
    "4276 EXACTLY as pre-registered (qa/reconcile-all-R2445.log kept as the "
    "honest red leg, 851226B, 1257.8s, TMP RECLAIM 932/932 worlds 326.59 MiB "
    "busy=0 failed=0), the only red suite being os-matrix-stamp-compare at "
    "AC-MSC4, whose own detail printed check=2 against the module's live "
    "verdict PASS (agrees=False). The cause was read off the tool rather than "
    "guessed: suite_matrix --check refused with an evidence-face line - "
    "doc-recorded=qa/comma-binding-identity-face-compare-R2444.log against "
    "check-resolved=qa/reconcile-all-R2443-retry.log - so the R2444 "
    "regeneration had pointed --evidence at its own product suite log instead "
    "of a battery log, and the check resolves only ELIGIBLE (all-green) "
    "battery evidence.",

    "2026-11-04 R2445 the retry leg ran BEFORE any repair and came back red "
    "for the same single reason (qa/reconcile-all-R2445-retry.log, 851228B, "
    "1416.0s, 549/550 at criteria 4276), which proved the red was "
    "deterministic and self-perpetuating rather than a flake: the doc can "
    "only satisfy AC-MSC4 when its recorded evidence is the same file the "
    "check will resolve, and that file must itself be an eligible green "
    "battery log for the CURRENT registry.",

    "2026-11-04 R2445 repair at the BIRTH SITE, and one wrong first attempt "
    "disclosed rather than hidden: the first regeneration used "
    "qa/reconcile-all-R2445-retry.log (a RED log) and produced a 53068B doc "
    "that the check then refused with the same face line, i.e. it made the "
    "record honest about the wrong face. The second attempt rendered from the "
    "only eligible evidence on disk, qa/reconcile-all-R2443-retry.log, "
    "through the shipped generator with --stamp-from: 53113B at 550 suites / "
    "4276 criteria, after which suite_matrix --check read PASS byte-identical "
    "(53113 bytes, 550 suites, 4276 criteria) and test_matrix_stamp_compare "
    "re-ran SUITE PASS 6/6 with AC-MSC4 green. The doc repair was committed "
    "ALONE as 2ed31668 before any further byte changed, and no criterion was "
    "widened and no checker relaxed - only the document it judges.",

    "2026-11-04 R2445 the FINAL leg then ran on the committed repair tree and "
    "read RUNNER PASS (550/550 suites green, reconcile controls 7/7, "
    "1387.4s) with a measured criteria total of 4276 - the pre-registered "
    "number to the unit - and TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2445-final.log, 854459B). The three legs are "
    "kept side by side on disk: one red, one red, one green, in that order.",

    "2026-11-04 R2445 the four follow-up sections produced the designed first "
    "FAIL and then a green verdict: leg 1 read VERDICT FAIL failing=matrix at "
    "on-disk=53113B against regenerated=53114B and wrote no byte, "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md "
    "from THIS round green evidence through --stamp-from so the render is "
    "stamp-aligned to the doc it is compared with, --check read byte-identical "
    "at 53114B / 550 suites / 4276 criteria with green=550/550, and the re-run "
    "read VERDICT R2445 PASS failing=none (matrix byte-identical 53114B, "
    "fingerprint CLEAN domains=5, profile byte-identical, census "
    "DRIFT-CLEAN). Both legs stay appended in the evidence tail (1889B FAIL "
    "then 1950B PASS, eol_ok=True).",

    "2026-11-04 R2445 debt register after this window: open=2 done=160. "
    "reconcile-battery-R2445 was closed through the shipped debt_close at its "
    "predicted 113809B -> 113812B (measured exactly, line=180, open 3->2, "
    "done 159->160, readback=ok) and ONE leader row product-face-R2446 was "
    "appended first=yes through the shipped debt_append at 113812B -> 114246B "
    "(readback=ok), naming the next window a product face on the tech head "
    "state/queue/tech.md:512 prefix AC-PFRD1 "
    "(comma_binding_face_row_drift), whose AC-PFRD1..AC-PFRD6 were pinned in "
    "that row at R2444 BEFORE any code. NO successor battery was registered: "
    "this window changed no product src byte and moved neither the registry "
    "suite nor the criteria count (still 550 / 4276), so the R2168 rule does "
    "not fire. Remaining open: loop-s4u-reconcile and product-face-R2446.",

    "2026-11-04 R2445 honest disclosures: (a) this window shipped ZERO "
    "product code and claims zero product points - the battery consumed the "
    "window exactly as the carried row said it would; (b) the red is the "
    "NINTH defect this battery has caught and nothing else would have, and "
    "the first one in which the PREVIOUS window's matrix regeneration named "
    "an evidence face the check can never resolve, so the artifact and its "
    "own checker disagreed about which log they described; (c) the window ran "
    "far past its 25-minute budget - three full batteries at 1257.8s, 1416.0s "
    "and 1387.4s plus the follow-up legs - named rather than hidden; (d) the "
    "first repair attempt was wrong and is recorded above rather than "
    "silently overwritten; (e) the ordering law is restated for the next "
    "writer: a matrix regeneration must name an evidence file that is both "
    "ELIGIBLE (all green) and the one the check will resolve, because a "
    "render from a red product-suite log reads as a face mismatch even when "
    "every line in it is true; (f) tasks.md was not touched, it is the P-47 "
    "canonical board and carries no row for this verification window; (g) "
    "src/os/state.json stood at 78918B against the 78500B waterline BEFORE "
    "this closeout (margin -418B, verdict FOLD-DUE), so the fold is named as "
    "due rather than performed here; the next writer must fold at a TRUE "
    "round-block boundary, and a fold that creates residue rounds must "
    "reconcile state/residue_triage.json in the same window.",

    "2026-11-04 R2445 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal and needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again "
    "(two-hundred-and-twelfth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile).",

    "2026-11-04 R2445 push: pending at closeout write; recorded after the "
    "push attempt so the line states what actually happened.",
]

TOKENS = (
    "R2445 tokens: local=~14k api=0 api_reason=verification window - three "
    "full batteries on committed trees (two red at a pre-registered 550 "
    "suites / 4276 criteria whose only red was the previous window's matrix "
    "regeneration naming an ineligible evidence face, one green at the same "
    "criteria count after a birth-site document repair committed alone), four "
    "follow-up sections with one designed matrix FAIL and one green "
    "stamp-aligned verdict, one debt row closed and one leader row opened "
    "through their shipped CLIs, and the state/export/backlog/heartbeat "
    "closeout; zero product code shipped, zero cloud calls and zero external "
    "API touches")

BACKLOG_ROW = (
    "- [x] [done 2026-11-04 R2445] R2445 verification window on the debt gate "
    "first=yes item (reconcile-battery-R2445, carried from R2444 at the "
    "pre-registered 550 suites / 4276 criteria): zero product code changed, "
    "the R2168 mixed-tree rule honoured. Leg 1 on the committed 15719180 tree "
    "read 549/550 suites at criteria 4276 exactly as pre-registered "
    "(qa/reconcile-all-R2445.log kept as the red leg, 1257.8s) and the only "
    "red was os-matrix-stamp-compare AC-MSC4, whose detail printed check=2 "
    "against the module verdict PASS: suite_matrix --check named the cause as "
    "an evidence-face mismatch - the doc recorded the R2444 product suite log "
    "while the check resolves qa/reconcile-all-R2443-retry.log, because only "
    "ELIGIBLE all-green battery logs are resolvable. The retry leg ran BEFORE "
    "any repair and reproduced the same single red (1416.0s, 549/550 at "
    "4276), proving the red deterministic. Repaired at the birth site by "
    "rendering the doc from the only eligible evidence face through the "
    "shipped generator with --stamp-from (53113B, 550/4276, --check PASS "
    "byte-identical, suite 6/6 with AC-MSC4 green) and the repair was "
    "committed ALONE as 2ed31668; the first regeneration attempt pointed at "
    "the RED retry log and is disclosed as wrong rather than hidden. Final "
    "leg on the committed repair tree: RUNNER PASS 550/550 plus controls 7/7 "
    "in 1387.4s at criteria 4276 exactly, TMP RECLAIM 932/932 "
    "(qa/reconcile-all-R2445-final.log, 854459B). Four follow-ups gave the "
    "designed matrix FAIL at 53113B vs 53114B, a stamp-aligned regeneration "
    "to 53114B / 550 / 4276 with --check byte-identical, and VERDICT R2445 "
    "PASS failing=none (fingerprint CLEAN 5 domains, profile byte-identical, "
    "census DRIFT-CLEAN). Debt: battery closed through the shipped debtor at "
    "113809B -> 113812B (line=180, open 3->2, done 159->160, readback ok) and "
    "product-face-R2446 opened first=yes at 113812B -> 114246B naming "
    "state/queue/tech.md:512 AC-PFRD1; no successor battery owed because only "
    "a document changed. Two new group orders (OB-20261104-140817-341 fleet "
    "push to bm-a, OB-20261104-1435-GIMMEALL-NAMING MiniGame naming to "
    "bm-a/b/c/m) acknowledged with no BigDomain action and the baseline "
    "advanced to 2026-11-04 14:35. Zero product points claimed."
)

HEARTBEAT_ROW = (
    "2026-11-04T23:15:00+08:00 tick=2445 R2445 verification window - "
    "reconcile-battery-R2445 ran red twice then green on committed trees: the "
    "single red both times was os-matrix-stamp-compare AC-MSC4, where the R2444 "
    "matrix regeneration recorded its own product suite log as the evidence "
    "face while the check only resolves eligible all-green battery logs; "
    "repaired at the birth site by rendering from the one eligible face "
    "through --stamp-from (53113B, check PASS byte-identical, suite 6/6) and "
    "committed alone as 2ed31668, then the final leg read RUNNER PASS 550/550 "
    "plus controls 7/7 in 1387.4s at criteria 4276 with four follow-ups "
    "VERDICT R2445 PASS after a stamp-aligned regeneration to 53114B [via "
    "BigDomain-OSLoop]")


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
        raise SystemExit("E_R2445_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d" % (TICK, len(LOG) + 1))
        for line in LOG:
            print("  LOG %s" % line[:100])
        print("  TOKENS %s" % TOKENS[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2445_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_order"] = ORDER_TS
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2445_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2445-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d layout_ok=%s crlf=%d bare_lf=%d"
          % (TICK, size, len(payload["log"]), layout["layout_ok"],
             layout["crlf"], layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2445] R2445 verification window" in backlog:
        raise SystemExit("E_R2445_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2445-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2445 " in beat:
        raise SystemExit("E_R2445_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2445-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))