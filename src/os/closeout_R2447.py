"""closeout_R2447 - state / backlog / heartbeat closeout for the R2447
verification window (reconcile-battery-R2447).

Writes the state log through state_io.canon with a byte read-back, prepends
the backlog row, appends the heartbeat row, advances the decisions baseline,
and refuses any drift. Run with --execute to write; the default is a dry run.
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

TICK = 2447
DEC_ROWS = 186
ORDER_TS = "2026-11-04 23:32"
NEW_DEC_TOKENS = [
    "D-20261105-01",
    "D-20261105-02",
    "D-20261105-03",
    "D-20261105-04",
    "D-20261105-05",
]

LOG = [
    "2026-11-05 R2447 verification window (five-silence scan at open: git "
    "status empty at HEAD 54535c88 with no .git/index.lock; the evolution "
    "ledger carries zero @BigDomain rows; the content-addressed decisions diff "
    "read 186 rows and 123 tokens with five NEW tokens against the stored "
    "baseline; the group orders tail max_ts is 2026-11-04 23:32 equal to the "
    "stored last_order, so nothing dispatches this company; benchmarks were "
    "refreshed 2026-11-03 inside the seven-day gate; the queue gauge read "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 and the deliverable-aware "
    "reader offered state/queue/tech.md:514 prefix AC-PDR1). The debt gate "
    "named CLAIM-FIRST item=reconcile-battery-R2447 carried from R2446 at the "
    "pre-registered 551 suites / 4282 criteria, so the battery ran FIRST on "
    "the committed tree with zero product edits (the R2168 mixed-tree rule).",

    "2026-11-05 R2447 decision gate disposition, one line per number: "
    "D-20261105-01 (44-line company-state harvest) records this company own "
    "P1 report of the group orders.md conflict and carries no execution "
    "action for BigDomain; D-20261105-02 (a stalled interactive rebase) names "
    "another repository; D-20261105-03 (group docs/orders.md conflict markers) "
    "is the GROUP layer's repair and this company already reported it under "
    "the cross-repo write ban, so BigDomain may not touch that file; "
    "D-20261105-04 (quant machine-state resume) is the Bigmoney line; and "
    "D-20261105-05 (BigCompute port timeout) is the compute line. None of the "
    "five carries a BigDomain execution action, so all five are "
    "ACKNOWLEDGED-NO-ACTION and the baseline was advanced to the full live "
    "token set after judging them.",

    "2026-11-05 R2447 the battery read RUNNER PASS on the FIRST leg: 551/551 "
    "suites green plus reconcile controls 7/7 in 1493.3s with a measured "
    "criteria total of 4282 - the pre-registered number to the unit - and TMP "
    "RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB "
    "(qa/reconcile-all-R2447.log, 851847B, one utf-8 LF single writer through "
    "src/os/battery_stream.py). No red leg exists for this round because none "
    "was produced, and that is stated rather than implied.",

    "2026-11-05 R2447 the four follow-up sections produced the designed first "
    "FAIL and then a green verdict: leg 1 read SECTION matrix FAIL at "
    "on-disk=53223B against regenerated=53196B and wrote no byte, "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from "
    "THIS round eligible green evidence (qa/reconcile-all-R2447.log) through "
    "--stamp-from so the render is stamp-aligned to the doc it is compared "
    "with, --check read byte-identical at 53196B / 551 suites / 4282 criteria, "
    "and the re-run read VERDICT R2447 PASS failing=none (matrix "
    "byte-identical 53196B, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN). Both legs stay appended in the "
    "evidence tail (1889B FAIL then 1950B PASS, eol_ok=True).",

    "2026-11-05 R2447 the matrix became self-describing for the first time in "
    "three windows: it was regenerated from THIS round own battery evidence "
    "rather than a borrowed older leg, so its own green line reads 551/551 "
    "instead of the 550/551 the R2446 render honestly had to carry. The R2445 "
    "ordering law is stated again for the next writer: a matrix regeneration "
    "must name an evidence file that is BOTH eligible (all green) and the one "
    "--check will resolve.",

    "2026-11-05 R2447 debt register after this window: open=2 done=162. "
    "reconcile-battery-R2447 was closed through the shipped debt_close at its "
    "predicted 114707B -> 114710B (measured exactly, line=183, open 3->2, done "
    "161->162, readback=ok) and ONE leader row product-face-R2448 was appended "
    "first=yes through the shipped debt_append at 114710B -> 115405B "
    "(readback=ok), naming the next window a product face on the tech head "
    "state/queue/tech.md:514 prefix AC-PDR1 "
    "(parameter_destination_resolution), whose AC-PDR1..AC-PDR6 were pinned in "
    "that row at R2434 BEFORE any code. NO successor battery was registered: "
    "this window changed no product src byte and moved neither the registry "
    "suite nor the criteria count (still 551 / 4282), so the R2168 mixed-tree "
    "rule does not fire. Remaining open: loop-s4u-reconcile and "
    "product-face-R2448.",

    "2026-11-05 R2447 honest disclosures: (a) this window shipped ZERO product "
    "code and claims zero product points - the battery consumed the window "
    "exactly as the carried row said it would; (b) no red was produced this "
    "round, so unlike the last eight verification windows there is no defect "
    "to name as caught - the honest reading is that the previous window's "
    "shipping discipline held; (c) the window ran far past its 25-minute "
    "budget: one full battery at 1493.3s plus the follow-up legs, named rather "
    "than hidden; (d) the group docs/orders.md still carries literal "
    "merge-conflict markers in its tail, which this station may not repair "
    "under the cross-repo write ban - it is read-only and already reported; "
    "(e) tasks.md was not touched, it is the P-47 canonical board and carries "
    "no row for a verification window; (f) src/os/state.json stood at 62948B "
    "against the 78500B waterline before this closeout (margin 15552B), so no "
    "fold was due; (g) the export's DO and latest_artifact fields still "
    "describe the R2446 product face because no new product face shipped this "
    "round - the refresh moves only the derived counters and the stamp, and "
    "that is stated rather than dressed up as a new deliverable.",

    "2026-11-05 R2447 self-heal check: BigDomain-OSLoop still exists and its "
    "Principal.LogonType reads InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 passes an "
    "explicit S4U principal and needs an elevated shell while this session is "
    "unelevated, so the definition was left untouched again "
    "(two-hundred-and-fourteenth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile).",

    "2026-11-05 R2447 push: pending at closeout write; recorded after the push "
    "attempt so the line states what actually happened.",
]

TOKENS = (
    "R2447 tokens: local=~10k api=0 api_reason=verification window - one full "
    "battery on the committed tree at a pre-registered 551 suites / 4282 "
    "criteria (green on the first leg), four follow-up sections with one "
    "designed matrix FAIL and one green stamp-aligned verdict rendered from "
    "this round own eligible evidence, one debt row closed and one leader row "
    "opened through their shipped CLIs, and the state/export/backlog/heartbeat "
    "closeout; zero product code shipped, zero cloud calls and zero external "
    "API touches")

BACKLOG_ROW = (
    "- [x] [done 2026-11-05 R2447] R2447 verification window on the debt gate "
    "first=yes item (reconcile-battery-R2447, carried from R2446 at the "
    "pre-registered 551 suites / 4282 criteria): zero product code changed, "
    "the R2168 mixed-tree rule honoured. The battery ran FIRST on the "
    "committed 54535c88 tree with an empty git status and read RUNNER PASS on "
    "the FIRST leg - 551/551 suites green plus reconcile controls 7/7 in "
    "1493.3s with a measured criteria total of 4282 EXACTLY as pre-registered, "
    "TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 "
    "MiB (qa/reconcile-all-R2447.log, 851847B, one utf-8 LF single writer "
    "through src/os/battery_stream.py). No red leg exists for this round "
    "because none was produced, stated rather than implied. The four follow-up "
    "sections produced the designed order: SECTION matrix FAIL at on-disk "
    "53223B against regenerated 53196B with no byte written, then a "
    "regeneration through --stamp-from from THIS round own eligible green "
    "evidence, --check byte-identical at 53196B / 551 suites / 4282 criteria, "
    "and the re-run VERDICT R2447 PASS failing=none (matrix byte-identical, "
    "fingerprint CLEAN domains=5, profile byte-identical, census DRIFT-CLEAN); "
    "both legs stay in the evidence tail. The matrix is self-describing for "
    "the first time in three windows - its own green line reads 551/551 "
    "because it names this round own battery rather than a borrowed older leg. "
    "Debt: reconcile-battery-R2447 closed through the shipped debt_close at "
    "its predicted 114707B -> 114710B (measured exactly, line=183, open 3->2, "
    "done 161->162, readback ok) and product-face-R2448 opened first=yes "
    "through debt_append at 114710B -> 115405B (readback ok) naming the tech "
    "head state/queue/tech.md:514 prefix AC-PDR1 "
    "parameter_destination_resolution, whose AC-PDR1..AC-PDR6 were pinned in "
    "that row at R2434 BEFORE any code; no successor battery owed because no "
    "product src byte changed and the registry count is unmoved at 551/4282. "
    "Five new group decision rows (D-20261105-01..05) were judged and all five "
    "read ACKNOWLEDGED-NO-ACTION (company-state harvest, another repo's "
    "rebase, the GROUP layer's own orders.md conflict this company already "
    "reported, the Bigmoney line, the BigCompute line), with the baseline "
    "advanced. Zero product points claimed."
)

HEARTBEAT_ROW = (
    "2026-11-05T01:08:00+08:00 tick=2447 R2447 verification window - the "
    "carried battery ran on the committed tree and read RUNNER PASS on the "
    "first leg: 551/551 suites green plus controls 7/7 in 1493.3s at a "
    "measured criteria total of 4282, exactly the pre-registered number, with "
    "no red leg produced; the four follow-up sections gave the designed matrix "
    "FAIL at 53223B against 53196B with no rewrite, then a stamp-aligned "
    "regeneration from THIS round own eligible evidence (the matrix own green "
    "line now reads 551/551 for the first time in three windows), --check "
    "byte-identical and VERDICT R2447 PASS; debt closed at predicted bytes and "
    "the next product face named at tech head AC-PDR1 "
    "[via BigDomain-OSLoop]")


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
        raise SystemExit("E_R2447_BACK read-back does not match the write")
    return len(back)


def main(execute):
    if not execute:
        print("DRY RUN tick=%d log_lines=%d new_dec=%d"
              % (TICK, len(LOG) + 1, len(NEW_DEC_TOKENS)))
        for line in LOG:
            print("  LOG %s" % line[:100])
        print("  TOKENS %s" % TOKENS[:100])
        return 0

    raw = open(STATE, "rb").read()
    payload = json.loads(raw.decode("utf-8"))
    if payload["tick"] != TICK - 1:
        raise SystemExit("E_R2447_TICK state reads %s, expected %d"
                         % (payload["tick"], TICK - 1))
    payload["tick"] = TICK
    payload["last_decision_rows"] = DEC_ROWS
    payload["last_order"] = ORDER_TS
    tokens = sorted(set(list(payload["last_dec_tokens"]) + NEW_DEC_TOKENS))
    payload["last_dec_tokens"] = tokens
    payload["log"].extend(LOG)
    payload["log"].append(TOKENS)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    canonical = state_io.canon(text)
    if json.loads(canonical) != payload:
        raise SystemExit("E_R2447_PAYLOAD canon moved the payload")
    size = write_bytes_atomic(STATE, canonical.encode("utf-8"),
                              ".r2447-state-")
    layout = state_io.layout(canonical)
    print("STATE tick=%d bytes=%d log_len=%d tokens=%d layout_ok=%s crlf=%d "
          "bare_lf=%d" % (TICK, size, len(payload["log"]), len(tokens),
                          layout["layout_ok"], layout["crlf"],
                          layout["bare_lf"]))

    backlog = io.open(BACKLOG, encoding="utf-8", newline="").read()
    if "R2447] R2447 verification window" in backlog:
        raise SystemExit("E_R2447_BACKLOG row already present")
    write_bytes_atomic(BACKLOG, (BACKLOG_ROW + "\n" + backlog).encode(
        "utf-8"), ".r2447-backlog-")
    print("BACKLOG row prepended")

    beat = io.open(HEARTBEAT, encoding="utf-8", newline="").read()
    if "tick=2447 " in beat:
        raise SystemExit("E_R2447_HEARTBEAT row already present")
    if not beat.endswith("\n"):
        beat += "\n"
    write_bytes_atomic(HEARTBEAT, (beat + HEARTBEAT_ROW + "\n").encode(
        "utf-8"), ".r2447-beat-")
    print("HEARTBEAT row appended")
    return 0


if __name__ == "__main__":
    sys.exit(main("--execute" in sys.argv[1:]))