"""R2275 closeout: append this round rows to state.json, preserving layout.

Same shape as closeout_R2274.py minus the fold (the file measures 67588B
against the 78500B waterline, so a fold is not due and is not run). It
serialises the mutated payload, hands the text to state_io.canon (which
pins the 16-space log item layout and refuses rather than guesses), writes
atomically with a read-back byte proof, then re-parses to prove the
payload only grew by exactly the rows this window appended.

Usage: python src/os/closeout_R2275.py --plan
       python src/os/closeout_R2275.py --execute
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

TICK = 2275

ROWS = [
    "2026-10-31 R2275 (five-silence scan clean at open: tree clean with an "
    "empty git status --short and no index.lock; decisions.md carries 289 "
    "non-empty rows EQUAL to the stored 289-row baseline, so no new decision "
    "row is presented and zero domain action is owed; the group ledger last "
    "@BigDomain line is the P-20261026-0930 patrol entry already receipted in "
    "R2262 and it carries no unresolved numbered handoff, so zero unreplied; "
    "the group orders tail is unchanged at the 2026-10-31 14:13 baseline "
    "consumed in R2271; benchmarks refreshed 2026-10-29 inside the seven-day "
    "gate) - the P1 canonical rows stay blocked-on-CEO, the weekly proposal "
    "duty is met by BD-PROP-005, the queue floors read FLOOR-MET main 5/5 "
    "tech 10/10 explore 10/10 with queue_head naming line 342 (prefix "
    "AC-QRX1, skipped_before=4, claimable=10) as the tech head, and the debt "
    "gate named exactly one first=yes row (reconcile-battery-R2275), so this "
    "window ran the VERIFICATION that row demanded with ZERO product edits "
    "until green (the R2168 mixed-tree rule). RESULT: full reconcile battery "
    "on the committed R2274 tree b6be0f6f with an empty git status before "
    "and after = RUNNER PASS 443/443 suites green plus controls 7/7 in 828.2s "
    "with birth-site TMP RECLAIM 932/932 worlds 326.57 MiB busy=0 failed=0 "
    "(qa/reconcile-all-R2275.log, 772984B at RUNNER close, single-writer "
    "utf-8 LF through src/os/battery_stream.py, never a shell redirection), "
    "criteria total 3634. Against the R2273 registry of 442 suites / 3628 "
    "criteria the measured delta is +1 suite / +6 criteria, exactly the "
    "pre-registered prediction from the R2274 os-debt-close suite, so this "
    "window needed no correction. Four follow-up sections then ran through "
    "src/os/battery_followup.py: the matrix section correctly FAILED first on "
    "the stale doc (on-disk=42798B regenerated=42867B) and did NOT rewrite "
    "it, which is the designed order; src/sandbox/suite_matrix.py then "
    "regenerated docs/sandbox-suite-matrix.md to 443 suites / 3634 criteria "
    "(42867B) and the re-run read all four sections PASS (matrix "
    "byte-identical 42867B, fingerprint CLEAN domains=5, profile --daily "
    "--check byte-identical, census DRIFT-CLEAN), closing on VERDICT PASS "
    "with the log own EOL self-check eol_ok=True. The register row was then "
    "closed through the R2274 writer itself (DEBT CLOSE item="
    "reconcile-battery-R2275 round=R2275 line=47 open=2->1 done=24->25 "
    "before=28625B after=28628B wrote=yes readback=ok) and debt_append opened "
    "product-face-R2276 first=yes (before=28628B after=29108B readback=ok), "
    "so the register reads open=2 done=25. Honest notes: (a) the first "
    "invocation passed the runner path relative to the repo root while the "
    "streamer resolves it under src/, so it exited rc=2 in 0.1s with zero "
    "suites run and wrote a short log (the R2131 precedent); the corrected "
    "run overwrote that path, so no red battery evidence exists for this "
    "window and none is claimed; (b) state.json measured 67588B against the "
    "78500B waterline before this closeout, so no fold was due and none was "
    "run. Honest score: a 0-point verification window with no product face.",

    "R2275 tokens: local=~9k api=0 api_reason=verification window on the debt "
    "register first item - one full streamed reconcile battery on the "
    "committed tree, one matrix regeneration plus its re-run through the "
    "single follow-up callable, two register writes through the shipped "
    "close and append writers, four live gauge readings, and the "
    "backlog/board/state/export closeout; zero cloud calls and zero external "
    "API touches",

    "R2275 self-heal check: BigDomain-OSLoop is registered and its principal "
    "still reads LogonType=InteractiveToken, which the 2026-09-29 machine "
    "law forbids for every lane task; src/os/register_loop_task.ps1 already "
    "passes an explicit S4U principal and needs an elevated shell to apply "
    "it, and this session runs unelevated, so the definition of the loop "
    "hosting this window was left untouched. Open local-lane item for an "
    "elevated window (forty-first consecutive disclosure, carried as the "
    "stale row loop-s4u-reconcile in state/debt.md).",
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