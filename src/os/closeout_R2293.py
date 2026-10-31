"""R2293 closeout: append the verification window items to the state log.

Dry run by default; --execute writes atomically with a read-back proof.
The JSON payload may only change by the intended fields, and the layout is
normalised through state_io.canon so the item indent stays canonical.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state_io  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

NARRATIVE = (
    "2026-10-31 R2293 (five-silence scan clean at open: tree clean with an empty git "
    "status --short and no index.lock; decisions.md carries 289 non-empty rows EQUAL to "
    "the stored 289-row baseline, so no new decision row is presented and zero domain "
    "action is owed; the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied numbered handoffs; the group orders tail is "
    "unchanged at the 2026-10-31 18:23 baseline consumed in R2278; benchmarks refreshed "
    "2026-10-29 inside the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, "
    "the weekly proposal duty is met by BD-PROP-005, the queue floors read FLOOR-MET "
    "main 5/5 tech 10/10 explore 10/10 with queue_head naming line 360 (prefix AC-SER1, "
    "skipped_before=4, claimable=10) as the tech head, and the debt gate named exactly "
    "one first=yes row (product-face-R2293), so this window ran the VERIFICATION that "
    "row demanded with ZERO product edits until green (the R2168 mixed-tree rule). "
    "RESULT: full reconcile battery on the committed R2292 tree 3addd18e with an empty "
    "git status before the run = RUNNER PASS 452/452 suites green plus controls 7/7 in "
    "854.9s with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy zero failed zero "
    "(qa/reconcile-all-R2293.log, 778152B, single writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total 3688 - exactly "
    "the pre-registered +1 suite / +6 criteria against R2291 (451/3682) from the R2292 "
    "os-exempt-review suite, so the prediction matched the measurement with no "
    "correction. Four follow-up sections then ran through src/os/battery_followup.py: "
    "the matrix section FAILED first on the stale doc (on-disk=43512B "
    "regenerated=43590B) and did NOT rewrite it, which is the designed order; "
    "src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md to 452 suites "
    "/ 3688 criteria (43590B) and the re-run read all four sections PASS (matrix "
    "byte-identical, fingerprint CLEAN 5 domains, profile --daily --check "
    "byte-identical, census DRIFT-CLEAN), closing on VERDICT R2293 PASS. Register closed "
    "through its own writer (debt_close line 65, open 2 to 1, done 42 to 43, readback "
    "ok) and product-face-R2294 opened first=yes through debt_append (before 39148B "
    "after 39394B, readback ok) naming the tech head at state/queue/tech.md:360 prefix "
    "AC-SER1, the R2280 stamp_exempt_review seed. Honest score: a 0-point verification "
    "window with no product face."
)

LEDGER = (
    "R2293 tokens: local=~15k api=0 api_reason=verification-only window - one full "
    "reconcile battery with its streamed evidence file, one four-section follow-up "
    "through the shipped callable plus one matrix regeneration from that evidence, two "
    "register writes through the shipped close and append writers, one waterline fold, "
    "and the queue/board/state/export closeout; zero cloud calls and zero external API "
    "touches"
)

SELF_HEAL = (
    "R2293 self-heal check: BigDomain-OSLoop is registered and its principal still reads "
    "LogonType=InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task; src/os/register_loop_task.ps1 already passes an explicit S4U principal and "
    "needs an elevated shell to apply it, and this session runs unelevated, so the "
    "definition of the loop hosting this window was left untouched. Open local-lane item "
    "for an elevated window (fifty-eighth consecutive disclosure, carried as the stale "
    "row loop-s4u-reconcile in state/debt.md)."
)

DISCLOSURES = (
    "R2293 honest disclosures: (a) the battery ran as a detached hidden process because "
    "battery_stream buffers its evidence in memory and writes once at completion, so "
    "every probe before the end legitimately found no file - that was buffering and not "
    "a dead runner, confirmed by the live process and then by the 778152B file. (b) The "
    "FAIL lines inside the battery body are the tamper-control lines that are SUPPOSED "
    "to fail (reconcile, pay-tamper and member-tamper each exit 2 naming their "
    "findings); their exit code is the assertion, no suite failed. (c) This round "
    "shipped no product code, so the register successor names the product face "
    "(stamp_exempt_review) rather than a second verification."
)


def build():
    raw = open(STATE, "rb").read()
    state = json.loads(raw.decode("utf-8"))
    before_items = len(state["log"])
    state["tick"] = 2293
    state["log"].extend([NARRATIVE, LEDGER, SELF_HEAL, DISCLOSURES])
    ensure_ascii = all(b < 0x80 for b in raw)
    text = json.dumps(state, ensure_ascii=ensure_ascii, indent=2)
    text = state_io.canon(text)
    new = text.encode("utf-8")
    return raw, state, before_items, new


def main(argv):
    execute = "--execute" in argv
    raw, state, before_items, new = build()
    print("LOG_ITEMS %d -> %d" % (before_items, len(state["log"])))
    print("TICK %s" % state["tick"])
    print("BEFORE %dB AFTER %dB DELTA %+d" % (len(raw), len(new), len(new) - len(raw)))
    if not execute:
        print("DRY RUN - wrote nothing")
        return 0
    folder = os.path.dirname(STATE)
    temp = os.path.join(folder, ".closeout_R2293.tmp")
    with open(temp, "wb") as sink:
        sink.write(new)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temp, STATE)
    back = open(STATE, "rb").read()
    if back != new:
        print("E_BACK read-back does not match")
        return 3
    if os.path.exists(temp):
        print("E_TEMP residue left")
        return 3
    print("WROTE %dB readback ok temp clean" % len(back))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))