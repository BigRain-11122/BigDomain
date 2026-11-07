"""append_state_R2540 - record the R2540 battery window in src/os/state.json.

Pure bookkeeping writer: bumps tick, appends the round line, the honest
disclosures line and the token line. Written as a script so the JSON stays
valid and the exact bytes appended are reviewable.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-07 R2540 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2539, pre-registered 599 suites / 4570 criteria), "
    "because the R2168 mixed-tree rule puts an owed battery ahead of any "
    "further product byte after R2539 moved the registry by one row. "
    "Five-silence scan clean at HEAD c610edfb (git status empty, no "
    "index.lock, zero @BigDomain ledger rows, content-addressed decisions diff "
    "new=0 over the stored baseline at 237 rows / 148 tokens, group orders "
    "tail unchanged at 2026-11-07 18:01, benchmarks 2026-11-03 inside the "
    "gate); debt_gate read CLAIM-FIRST item=reconcile-battery-R2539 first=1 "
    "with open=18. The target was re-measured BEFORE the run by importing "
    "reconcile_all.SUITES: 599 suites / 4570 criteria, byte for byte the "
    "registered note. RESULT: qa/reconcile-all-R2539.log (944403B, utf-8, "
    "bom=False, crlf=0, lone_cr=0) closes with \"RUNNER PASS (599/599 suites "
    "green, reconcile controls 7/7, 1500.0s)\", zero FAIL suite rows, and an "
    "independent recount of the 599 PASS suite rows summing to exactly 4570 "
    "criteria, TMP RECLAIM candidates=932 removed=932 reclaimed=326.59 MiB. "
    "The battery ran detached through src/os/battery_stream.py (pid 91328 in "
    "logs/battery-R2539.pid) and was never restarted; the first leg was "
    "green, so no repair and no retry exist. FOLLOW-UP: dry run read VERDICT "
    "FAIL failing=matrix at on-disk 57846B against regenerated 57822B with no "
    "byte written while fingerprint/profile/census all read PASS; "
    "docs/sandbox-suite-matrix.md was then regenerated stamp-aligned from THIS "
    "round own evidence through src/sandbox/suite_matrix.py --stamp-from at "
    "57822 bytes / 599 suites / 4570 criteria with green=599/599 "
    "self-describing, --check read byte-identical, and the re-run read all "
    "four sections PASS for VERDICT R2539 PASS failing=none (APPENDED 1950B "
    "eol_ok=True). DEBT: reconcile-battery-R2539 closed through debt_close "
    "(line 273, open 18->17, done 238->239, 165416B -> 165419B, readback ok) "
    "and product-face-R2540 appended first=yes through debt_append (165419B -> "
    "166562B, readback ok) naming the tech head state/queue/tech.md:577 "
    "prefix AC-PNSP1 so the next window owes a product face; NO successor "
    "battery is owed because this window moved no product byte and the "
    "registry is unmoved at 599/4570, re-read by import. BOARD: the carried "
    "row was closed and the next row opened through src/os/"
    "backlog_prepend_R2540.py at the predicted and measured 881181B; "
    "queue_head still reads line 577 prefix AC-PNSP1 claimable=11 with the "
    "floor MET."
)
HONEST = (
    "2026-11-07 R2540 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this "
    "window; the window bought proof that the R2539 tree is green as "
    "committed, which is what the register owed; (b) the battery ran on the "
    "first leg with no retry and no cleanup needed, so the 599/599 claim is "
    "one run rather than a best-of; (c) the matrix stamp line was carried "
    "from the previous document by --stamp-from rather than re-timed, so the "
    "content is this round while the stamp is provenance-only and the check "
    "compares content only; (d) the decisions scan read rows=237 tokens=148 "
    "new=0 while the stored last_decision_rows field still reads 331 - "
    "reported rather than silently rewritten; (e) Docker is absent on this "
    "host so no containerised bring-up of the sandbox faces is claimed; (f) "
    "the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items (merchant id, mini-program appid/secret); (g) tasks.md was not "
    "touched, it is the P-47 canonical board; (h) the S4U lane reconcile "
    "(loop-s4u-reconcile) still needs an ELEVATED shell and was not "
    "attempted - BigDomain-OSLoop still reads InteractiveToken, which the "
    "2026-09-29 machine law forbids for lane tasks; (i) the local queue face "
    "did not move this window, so the export queue block was re-derived "
    "without a queue move rather than re-gated."
)
TOKENS = (
    "R2540 tokens: local=~9k api=0 api_reason=verification window - "
    "five-silence scan, one pre-run registry recount by import, one full "
    "599-suite battery in a single green leg, one stamp-aligned matrix "
    "regeneration checked byte-identical, one failed-first follow-up dry run "
    "kept as designed, one debt row closed and one appended through their "
    "shipped writers, and the state/export/backlog/heartbeat closeout; zero "
    "cloud calls and zero external API touches"
)


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    before = state["tick"]
    state["tick"] = before + 1
    state["log"].extend([ROUND, HONEST, TOKENS])
    data = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
    with io.open(STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    print("STATE APPEND tick=%d->%d log=%d->%d bytes=%d readback=%s"
          % (before, back["tick"], len(back["log"]) - 3, len(back["log"]),
             os.path.getsize(STATE),
             "ok" if back["log"][-1] == TOKENS else "MISMATCH"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())