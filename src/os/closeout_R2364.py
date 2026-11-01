"""Closeout for round R2364 (verification window).

Appends the round items to state.json, bumps the tick, and writes the file
back through the state canon with a predicted size and a read-back proof.
Pure stdlib, ASCII only, no clock, no network.
"""

import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "src", "os"))

import state_fold
import state_io

STATE = os.path.join(BASE, "src", "os", "state.json")
ROUND = 2364

ITEMS = [
    "2026-11-02 R2364 verification window (five-silence scan clean at open: "
    "empty git status --short at 1610c9d1, no .git/index.lock; scan_five_still "
    "read LEDGER atbd_lines=0 unreplied_groups=0, DEC rows=112 tokens=74 new=0, "
    "so no decision row was owed; the group orders tail still reads the "
    "2026-11-01 10:4x model-policy baseline already acknowledged as "
    "non-execution; benchmarks refreshed 2026-11-01, inside the seven-day "
    "gate). THE CARRIED BATTERY RAN FIRST, ON THE COMMITTED TREE, and the row "
    "it discharges had been carried two windows (reconcile-battery-R2362, "
    "opened R2361, the register reading it stale): debt_gate read CLAIM-FIRST "
    "at open, git status was empty at 1610c9d1 (the R2168 mixed-tree rule), "
    "and the R2362 battery had been measured on an EDITED tree, so the "
    "committed-tree run had genuinely never happened for that tree. MEASURED: "
    "RUNNER PASS 492/492 suites green plus reconcile controls 7/7 in 884.6s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.59 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2364.log, single writer utf-8 LF through "
    "src/os/battery_stream.py, launched unfiltered so every line streamed - "
    "the R2348/R2360 truncating-pipe trap avoided). THE PREDICTION MATCHED "
    "EXACTLY: criteria total 3928 against the pre-registered 492/3928 (R2362 "
    "read 491/3922 on its edited tree plus this window one suite and six "
    "criteria from os-residue-triage-repin), so there is no correction and no "
    "swept delta to name. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section FAILED first on the stale "
    "doc (on-disk=46996B regenerated=47070B) and did NOT rewrite it, which is "
    "the designed order; src/sandbox/suite_matrix.py regenerated "
    "docs/sandbox-suite-matrix.md to 492 suites / 3928 criteria (47070B) and "
    "the re-run read all four PASS (matrix byte-identical 47070B, fingerprint "
    "CLEAN 5 domains, profile --check byte-identical, census DRIFT-CLEAN), "
    "closing VERDICT R2364 PASS.",

    "R2364 tokens: local=~12k api=0 api_reason=verification window - one full "
    "reconcile battery on the committed tree (884.6s), one designed matrix "
    "FAIL and its regeneration, a four-section re-run through their own "
    "callables, two register writes through their own writers, and the "
    "state/export/heartbeat/board closeout; zero cloud calls and zero external "
    "API touches",

    "R2364 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already passes "
    "an explicit S4U principal and needs an elevated shell to apply, and this "
    "session runs unelevated, so the definition of the loop hosting this "
    "window was left untouched. Open local-lane item for an elevated window "
    "(hundred-and-twentieth consecutive disclosure, carried as the stale row "
    "loop-s4u-reconcile in state/debt.md).",

    "R2364 decision gate (D-20260930-19 step 2): the content-addressed diff of "
    "the group decisions.md against the stored baseline read new=0 over 112 "
    "rows and 74 tokens, and the evolution ledger carries no @BigDomain row, "
    "so nothing was executed, rejected or acknowledged this window and the "
    "baseline was left unchanged rather than widened without cause.",

    "R2364 honest disclosures: (a) NO product face shipped and the window "
    "scores 0 product points; the register first=yes item was the carried "
    "battery and it ran. (b) The battery row had been carried two windows with "
    "the register already reading it stale, and the reason it kept being "
    "deferred is named rather than buried: its R2362 numbers came from an "
    "edited tree, so the committed-tree run was still owed and this window "
    "owed it. (c) A bounded wait loop used to watch this window own battery "
    "printed nothing by design and was cancelled by the shell tool after five "
    "silent minutes; the battery kept streaming on its own and was NEVER "
    "re-run, so nothing was lost and no second run is being presented as one. "
    "(d) debt_append refused this window first successor note with "
    "E_DEBTA_BAD_FIELD because the note carried '=' characters inside "
    "'rc=5' and 'rc=0'; the note was rewritten without them and no criterion "
    "was widened - the register own field law forbids what prose naturally "
    "writes. (e) The tech floor reads 9/10 at both open and close, which is "
    "pre-existing (no claim dropped it this window) and no row was seeded to "
    "paper over it; the successor row names the queue head AC-FDW1 plus a "
    "second real gap measured this window (battery_followup answers a bare "
    "--help with a bad-args code while the sibling runner answers it as a "
    "question). (f) tasks.md was left untouched: it is the P-47 canonical "
    "board and carries no row for a verification window, disclosed rather "
    "than silently skipped.",
]


def main():
    raw = io.open(STATE, encoding="utf-8").read()
    data = json.loads(raw)
    data["tick"] = ROUND
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = state_io.canon(text)
    predicted = len(text.encode("utf-8"))
    with io.open(STATE, "w", encoding="utf-8", newline="") as sink:
        sink.write(text)
    back = io.open(STATE, encoding="utf-8").read()
    measured = len(back.encode("utf-8"))
    if measured != predicted:
        print("E_R2364_PREDICT predicted=%d measured=%d"
              % (predicted, measured))
        return 3
    if json.loads(back)["tick"] != ROUND:
        print("E_R2364_TICK")
        return 3
    gate = state_fold.measure(measured, BASE)
    count = len(json.loads(back)["log"])
    print("CLOSEOUT R2364 bytes=%d items=%d tick=%d"
          % (measured, count, ROUND))
    print("WATERLINE %s" % json.dumps(gate, sort_keys=True))
    rep = state_io.report(STATE)
    print("LAYOUT eol_ok=%s layout_ok=%s items_off_indent=%s"
          % (rep["eol_ok"], rep["layout_ok"], rep["items_off_indent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())