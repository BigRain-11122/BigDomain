"""closeout_R2360 - the round ledger for the carried-battery window.

Bumps the tick, appends the log lines this window owes, prepends the backlog
row, appends the heartbeat line and writes state.json through state_io's canon.
Dry run by default; --execute writes utf-8 with LF.
"""

import io
import json
import os
import sys
import tempfile

import state_io

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
HEARTBEAT = os.path.join(ROOT, "heartbeat.txt")

TICK = 2360
STAMP = "2026-11-02T03:36:10"

LIVE = (
    "2026-11-02 R2360 verification window (five-silence scan clean at open: "
    "empty git status --short at bc4334fa, no .git/index.lock; scan_five_still "
    "read LEDGER atbd_lines=0 unreplied_groups=0 and DEC rows=112 tokens=74 "
    "new=0, so no decision row was owed; the group orders tail still reads the "
    "2026-11-01 10:4x model-policy baseline already acknowledged as "
    "non-execution; benchmarks refreshed 2026-11-01, inside the seven-day "
    "gate). THE DEBT GATE NAMED THE CARRIED BATTERY (CLAIM-FIRST "
    "item=reconcile-battery-R2360 opened=R2359, its row bare with no note, so "
    "the target was measured from the registry rather than trusted) and this "
    "window took it with ZERO product edits until green (the R2168 mixed-tree "
    "rule). BATTERY on the committed R2359 tree: RUNNER PASS 489/489 suites "
    "green plus reconcile controls 7/7 in 881.8s with criteria total 3910 "
    "EXACTLY as pre-registered from the R2359 os-review-window-history-wire "
    "suite, and birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 "
    "failed=0 (qa/reconcile-all-R2360.log, 799502B, single writer utf-8 LF "
    "through src/os/battery_stream.py, never a shell redirection). Four "
    "follow-up sections ran through src/os/battery_followup.py: the matrix "
    "section FAILED first on the stale doc (on-disk=46823B "
    "regenerated=46795B) and did NOT rewrite it, which is the designed order; "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md to "
    "489 suites / 3910 criteria at 46795B with green=489/489 against this "
    "round own evidence leg, and the re-run read all four PASS (matrix "
    "byte-identical 46795B, fingerprint CLEAN 5 domains, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), closing VERDICT R2360 PASS."
)

MATRIX_DELTA = (
    "R2360 matrix delta named, not swept: the doc shrank 28 bytes (46823B -> "
    "46795B) with identical 489 suites / 3910 criteria, and git diff shows why "
    "- 301 rows rewritten because the per-suite durations and the evidence "
    "line changed from the R2358-retry leg (which the R2359 regeneration had "
    "used, its row reading 488/488 green) to this round own R2360 leg, its row "
    "now reading 489/3910 green at 489/489 suites. No suite entered or left the "
    "registry, so the delta is the evidence leg and never a drift."
)

SELF_HEAL = (
    "R2360 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition was left untouched. Open "
    "local-lane item for an elevated window (hundred-and-eighteenth "
    "consecutive disclosure, carried as the stale row loop-s4u-reconcile in "
    "state/debt.md)."
)

DECISION_GATE = (
    "R2360 decision gate (D-20260930-19 step 2): the content-addressed diff "
    "of the group decisions.md against the stored baseline read new=0 over "
    "112 rows and 74 tokens, and the evolution ledger carries no @BigDomain "
    "row, so nothing was executed, rejected or acknowledged this window and "
    "the baseline was left unchanged rather than widened without cause."
)

HONEST = (
    "R2360 honest disclosures: (a) NO product face shipped and the window "
    "scores 0 product points; the register first=yes item was the carried "
    "battery and it ran, which is the gate own claim rather than a substitute "
    "for product work. (b) THE FIRST ATTEMPT NEVER REACHED THE BATTERY: the "
    "run was started with its stdout filtered through a pipeline, the filter "
    "buffered every line, the tool cancelled the command on five minutes of "
    "silence, and because battery_stream writes its evidence file only after "
    "the child exits, the killed run left no log at all - no surviving python "
    "process was found and the tree stayed clean. The rerun was started "
    "unfiltered so each line streamed; the same trap is recorded as the "
    "R2348 runner_arg_guard finding and this window repeats it, disclosed "
    "rather than hidden. (c) The matrix FAIL on the first follow-up pass was "
    "the designed order and not a defect; the byte delta is named above and "
    "was proved by git diff rather than by assumption. (d) tasks.md was left "
    "untouched: it is the P-47 canonical board and carries no row for this "
    "tech slice, disclosed rather than silently skipped. (e) The register row "
    "closed this window was opened bare at R2359 with no note, so the "
    "pre-registered target was reconstructed from the registry and the "
    "R2359 matrix; the measurement matched it exactly, which is the only "
    "reason that reconstruction is safe to report."
)

TOKENS = (
    "R2360 tokens: local=~9k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (881.8s) after one cancelled "
    "attempt that wrote nothing, one designed matrix FAIL and its "
    "regeneration, a four-section re-run through their own callables, one "
    "matrix delta named by git diff, two register writes through their own "
    "writers, and the state/export/heartbeat/board closeout; zero cloud calls "
    "and zero external API touches"
)

ITEMS = [LIVE, MATRIX_DELTA, TOKENS, SELF_HEAL, DECISION_GATE, HONEST]

BACKLOG_ROW = (
    "- [x] [done 2026-11-02 R2360] verification window: the debt gate named "
    "the carried battery (CLAIM-FIRST reconcile-battery-R2360, opened bare at "
    "R2359) and it ran FIRST on the committed bc4334fa tree with zero product "
    "edits (the R2168 mixed-tree rule). RUNNER PASS 489/489 suites plus "
    "controls 7/7 in 881.8s with criteria total 3910 exactly as pre-registered "
    "from the R2359 os-review-window-history-wire suite and TMP RECLAIM "
    "932/932 worlds 326.59 MiB busy=0 failed=0 (qa/reconcile-all-R2360.log, "
    "799502B, single writer utf-8 LF through src/os/battery_stream.py). Four "
    "follow-up sections PASS after the designed matrix FAIL and its "
    "regeneration to 489/3910 at 46795B: matrix byte-identical, fingerprint "
    "CLEAN 5 domains, profile byte-identical, census DRIFT-CLEAN -> VERDICT "
    "R2360 PASS. The matrix 28-byte shrink is NAMED, not swept: same 489 "
    "suites / 3910 criteria, 301 rows rewritten because the evidence leg moved "
    "from the R2358-retry log to this round own battery log (git diff "
    "disclosed). The first attempt never reached the battery - a filtered "
    "pipeline buffered the stream, the tool cancelled on five minutes of "
    "silence, and battery_stream writes evidence only at close, so it left no "
    "log and no process; the rerun streamed unfiltered. Register: battery row "
    "closed and reconcile-battery-R2361 opened first=yes. Zero product code, "
    "0 product points. Next product head: state/queue/tech.md:403 prefix "
    "AC-SGS1 (stamp_exempt_seed_guard_wire), criteria pinned there at R2346 "
    "before any code."
)


def write_atomic(path, text):
    """Atomic utf-8 LF write with a byte read-back (payload may change here)."""
    payload = text.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".clo_r2360_")
    try:
        with os.fdopen(handle, "wb") as sink:
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise
    with io.open(path, "rb") as check:
        back = check.read()
    if back != payload:
        raise SystemExit("E_CLO_BACK read-back mismatch on %s" % path)
    return len(payload)


def execute():
    raw = state_io.read_raw(STATE)
    text = state_io.decode(raw)
    data = state_io.parse(text)
    already = LIVE in (data.get("log") or [])
    if not already:
        if data.get("tick") != TICK - 1:
            raise SystemExit("E_CLO_TICK tick=%r expected=%d"
                             % (data.get("tick"), TICK - 1))
        data["tick"] = TICK
        data["log"].extend(ITEMS)
        payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        new_text = state_io.canon(payload)
        before = len(text.encode("utf-8"))
        after = len(new_text.encode("utf-8"))
        print("STATE bytes %d -> %d (delta %+d)"
              % (before, after, write_atomic(STATE, new_text) - before))
    else:
        print("STATE already carries this round (tick=%r)" % data.get("tick"))

    with io.open(BACKLOG, "r", encoding="utf-8") as handle:
        backlog = handle.read()
    if "- [done 2026-11-02 R2360]" in backlog:
        raise SystemExit("E_CLO_BACKLOG already has this row")
    write_atomic(BACKLOG, BACKLOG_ROW + "\n" + backlog)
    print("BACKLOG row prepended")

    with io.open(HEARTBEAT, "r", encoding="utf-8") as handle:
        beat = handle.read()
    if not beat.endswith("\n"):
        beat += "\n"
    write_atomic(HEARTBEAT, beat + "%d %s\n" % (TICK, STAMP))
    print("HEARTBEAT appended")


def main(argv):
    if "--execute" in argv:
        execute()
        return 0
    print("DRY RUN: %d log items, tick %d, backlog row and heartbeat line"
          % (len(ITEMS), TICK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))