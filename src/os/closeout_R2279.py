"""R2279 closeout: append this round rows to state.json, preserving layout.

Same shape as closeout_R2275.py minus the fold (the file measures 63512B
against the 78500B waterline, so a fold is not due and is not run). It
serialises the mutated payload, hands the text to state_io.canon (which
pins the 16-space log item layout and refuses rather than guesses), writes
atomically with a read-back byte proof, then re-parses to prove the
payload only grew by exactly the rows this window appended.

Usage: python src/os/closeout_R2279.py --plan
       python src/os/closeout_R2279.py --execute
"""

import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
sys.path.insert(0, HERE)

import state_io  # noqa: E402

TICK = 2279

ROWS = [
    "2026-10-31 R2279 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger carries "
    "the same @BigDomain patrol rows already paid off with zero unreplied "
    "numbered handoffs; the group orders tail is unchanged at the 2026-10-31 "
    "18:23 baseline consumed in R2278; benchmarks refreshed 2026-10-29 inside "
    "the seven-day gate) - the P1 canonical rows stay blocked-on-CEO, the "
    "weekly proposal duty is met by BD-PROP-005, the queue floors read "
    "FLOOR-MET main 5/5 tech 10/10 explore 10/10 with queue_head naming line "
    "345 (prefix AC-SEX1, skipped_before=4, claimable=10) as the tech head, "
    "and the debt gate named exactly one first=yes row "
    "(reconcile-battery-R2279), so this window ran the VERIFICATION that row "
    "demanded with ZERO product edits until green (the R2168 mixed-tree "
    "rule). RESULT: full reconcile battery on the committed R2278 tree "
    "c2896ff3 with an empty git status before and after = RUNNER PASS 445/445 "
    "suites green plus controls 7/7 in 851.4s with birth-site TMP RECLAIM "
    "932/932 worlds 326.57 MiB busy=0 failed=0 (qa/reconcile-all-R2279.log, "
    "779762B, crlf=0, no BOM, single-writer utf-8 LF through "
    "src/os/battery_stream.py, never a shell redirection), criteria total "
    "3646. Against the R2277 registry of 444 suites / 3640 criteria the "
    "measured delta is +1 suite / +6 criteria, exactly the pre-registered "
    "prediction from the R2278 os-queue-done-stamp suite, so this window "
    "needed no correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section correctly FAILED first on "
    "the stale doc (on-disk=42974B regenerated=43031B) and did NOT rewrite "
    "it, which is the designed order; src/sandbox/suite_matrix.py then "
    "regenerated docs/sandbox-suite-matrix.md to 445 suites / 3646 criteria "
    "(43031B) and the re-run read all four sections PASS (matrix "
    "byte-identical 43031B, fingerprint CLEAN domains=5, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), closing on VERDICT R2279 "
    "PASS with eol_ok=True. The register row was then closed through the "
    "R2274 writer itself (DEBT CLOSE item=reconcile-battery-R2279 round=R2279 "
    "line=51 open=2->1 done=28->29 before=30999B after=31002B wrote=yes "
    "readback=ok) and debt_append opened product-face-R2280 first=yes "
    "(before=31002B after=31781B readback=ok), so the register reads open=2 "
    "done=29 and the gate now reads CLAIM-FIRST product-face-R2280. Honest "
    "score: a 0-point verification window with no product face; state.json "
    "measured 63512B against the 78500B waterline before this closeout, so no "
    "fold was due and none was run.",

    "R2279 tokens: local=~10k api=0 api_reason=verification window on the "
    "debt register first item - one full streamed reconcile battery on the "
    "committed tree, one matrix regeneration plus two follow-up re-runs "
    "through the single callable, two register writes through the shipped "
    "close and append writers, four live gauge readings, and the "
    "backlog/board/state/export closeout; zero cloud calls and zero external "
    "API touches",

    "R2279 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine law "
    "forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (forty-fifth consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md).",

    "R2279 honest disclosures: (a) the first battery invocation was piped "
    "through a truncating selector and was cancelled by the five-minute "
    "no-output rule with zero output; an orphan check proved zero surviving "
    "python processes, zero partial evidence file and a clean tree before the "
    "unpiped rerun whose numbers are above (the R2211 trap re-proven). (b) "
    "The matrix generator stamps a minute-resolution time into the doc, so a "
    "regeneration at 18:59 and a follow-up copy taken at 19:00 differ on that "
    "one line at IDENTICAL length (both 43031B) and the section correctly "
    "read FAIL; no criterion was widened and the doc was not hand-edited - "
    "regenerating and re-running inside the same minute produced the "
    "byte-identical PASS. (c) Three follow-up bodies were appended to the "
    "evidence file (1889B FAIL, 1889B FAIL, 1950B PASS); all legs are "
    "retained rather than trimmed.",
]


def main(argv):
    execute = "--execute" in argv
    raw = io.open(STATE, "rb").read().decode("utf-8")
    before = json.loads(raw)
    after = json.loads(raw)
    after["log"] = list(before["log"]) + ROWS
    after["tick"] = TICK
    text = json.dumps(after, indent=2, ensure_ascii=True)
    canon = state_io.canon(text)
    if json.loads(canon) != after:
        raise SystemExit("ABORT canon moved the payload")
    old_log = list(before["log"])
    if json.loads(canon)["log"][:len(old_log)] != old_log:
        raise SystemExit("ABORT the existing rows moved")
    print("PLAN rows=%d tick=%d before=%dB after=%dB"
          % (len(ROWS), TICK, len(raw.encode("utf-8")),
             len(canon.encode("utf-8"))))
    if not execute:
        return 0
    data = canon.encode("utf-8")
    folder = os.path.dirname(os.path.abspath(STATE))
    handle, temp = tempfile.mkstemp(dir=folder, prefix=".closeout_")
    with os.fdopen(handle, "wb") as sink:
        sink.write(data)
    os.replace(temp, STATE)
    back = io.open(STATE, "rb").read()
    if back != data:
        raise SystemExit("ABORT read-back differs from the write")
    measured = state_io.layout(back.decode("utf-8"))
    print("WROTE bytes=%d log_items=%d layout_ok=%s count_ok=%s"
          % (len(back), measured["log_items"], measured["layout_ok"],
             measured["count_ok"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))