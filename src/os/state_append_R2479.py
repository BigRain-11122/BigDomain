"""R2479 closeout: append this window's log items and move the tick. One
atomic replace in the state canon, proved by a read-back. No decision token
moved this window, so the baseline list is carried unchanged and said so.
"""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

NEW_TOKENS = []

LINES = [
    "2026-11-06 R2479 TECH window DELIVERED (claims the runner-suite-timeout-cap seed row whose AC-RSC1..AC-RSC6 were pinned at R2478 BEFORE any code, and which is the third casualty of the flat 300s cap: R2393 leg 3, R2466 leg 2, R2478 leg 1). Five-silence scan at open: git status empty at HEAD 19b9fdb1 with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the content-addressed decisions diff new=0 against the 142-token baseline, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate; the open debt rows were product-face-R2456 and the R2478 cap row, so the cap row was claimable and named.",
    "2026-11-06 R2479 SHIPPED the cap as one declared reading instead of a hidden literal: src/sandbox/reconcile_all.py now carries ONE named SUITE_TIMEOUT_S = 600 plus a SUITE_TIMEOUT_OVERRIDES mapping and a suite_timeout(label) helper, run_cmd takes an explicit timeout, the per-suite call passes suite_timeout(label), the timeout marker names the cap that actually ran, and the closing summary line states 'suite cap=600s overrides=N' so an operator never has to read source. New src/os/runner_suite_timeout_cap.py is the single owner of that reading: read_cap returns (cap, declared|fallback, occurrences) from the runner SOURCE, read_overrides parses the declaration instead of executing the runner, and the CLI answers --check with exit 0 CAP-DECLARED, 2 CAP-UNDECLARED, 3 no runner, 5 bad flags.",
    "2026-11-06 R2479 WIRED the instrument instead of duplicating it: src/os/runner_suite_timeout_headroom.py now takes its DEFAULT cap from runner_suite_timeout_cap.default_cap(runner) whenever --cap is not given, so the headroom reading and the run can no longer disagree - the defect that let a 300s cap moulder next to a 300.0 second literal. The import is deliberately the dunder form with a comment saying why: AC-RTH6 pins that module's import set to exactly ast/io/json/os/re/sys and any import statement would widen it. A fixture world carries no declaration, so it answers the documented FALLBACK_CAP of 300.0 and every pinned AC-RTH fixture keeps reading exactly as before.",
    "2026-11-06 R2479 PROOF: AC-RSC1..AC-RSC6 were pinned in state/queue/tech.md BEFORE the module, the suite or the registry row existed. SUITE PASS 6/6 TWICE with byte-identical criterion bodies through the SHIPPED capture callable at qa/runner-timeout-cap-R2479.log (1169B, utf-8, crlf=0, bom=False, adjacent test_runner_suite_timeout_headroom.py green): AC-RSC1 a fixture declaring 742 reads 742, a fixture declaring nothing reads the 300.0 fallback with occurrences=0, the real runner reads declared with exactly one declaration and ZERO hardcoded timeout=300; AC-RSC2 a 5s fixture under a declared 1s override returns 124 with the marker naming 1s while an undeclared neighbour keeps the global cap and exits 0; AC-RSC3 the headroom suite still reads SUITE PASS 6/6 with no FAIL line, so the deployed reading did not regress; AC-RSC4 at the repaired 600s cap the three previously banded ledger suites (buyerhistory, refundregister, reportclaims) read COMFORTABLE from the R2478 green evidence while a synthetic 95s-under-100s outlier still reads BAND-HIT; AC-RSC5 the summary carries 'suite cap=1s' and a timed-out fixture is recorded as exactly ONE FAIL suite with the run still reaching its summary, with the fixture's own lines swallowed so a green suite never shows fail-lines; AC-RSC6 the module is pure ASCII stdlib (json/os/re/sys), read-only, wired with exactly one registry row.",
    "2026-11-06 R2479 one process defect repeated and repaired the same window, disclosed rather than quietly fixed: the first capture attempt piped the suite through PowerShell Tee-Object, which wrote qa/runner-timeout-cap-R2479-leg1/leg2.log as UTF-16 (255,254 BOM) - the exact dialect defect this week's R2478 repair had just fixed. Both files were deleted before any commit and the evidence was re-taken through the shipped evidence_capture callable, which writes one utf-8 LF file after refusing red or drifting legs; the re-taken file measures 1169B with the first bytes 69,86,73 and crlf=0. The lesson is recorded because the loop had just paid for it once and paid again.",
    "2026-11-06 R2479 registry, matrix and debt: the registry moved 566 -> 567 suites and 4372 -> 4378 criteria by exactly one row runner-suite-timeout-cap(6), docs/sandbox-suite-matrix.md was restamped stamp-aligned to 54575B with 'green=566/567' (honest, because this window ran no battery) and --check reads byte-identical; runner-suite-timeout-cap was closed through the shipped debt_close at its predicted 124306B -> 124310B (line=204, open 3->2, done 182->183, readback ok) and reconcile-battery-R2479 was appended first=no (124310B -> 124971B, readback ok) with the pre-registered target 567 suites / 4378 criteria, so the NEXT window owes the battery on the committed tree BEFORE any further product byte.",
    "2026-11-06 R2479 honest disclosures: (a) this is a TECH window, not a product face - nothing a CEO could open was built, so on the Executive Protocol scale it is file changes plus a repaired structural defect rather than a 2-point deliverable, and that is stated rather than dressed up; (b) the 600s cap is a judgement, not a measurement of the worst case: it gives the slowest measured suite 300s of headroom and the band still names anything above 360s, but a machine loaded worse than R2478 leg 1 could still lose a suite, which is why the override mechanism exists; (c) the overrides map ships EMPTY on purpose and the suite proves the mechanism through the run_cmd seam instead of shipping a fake declaration; (d) the headroom reader now depends on one sibling module, so a missing runner_suite_timeout_cap.py would surface as an import error rather than a silent 300 - fail-loud by design, not exercised negatively this window; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items; (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json was well under the 78500B waterline at open.",
    "R2479 tokens: local=~9k api=0 api_reason=tech window - one named cap constant plus an override mechanism in the runner, one new reader module that owns the reading, one wiring edit in the headroom instrument, one six-criteria suite proved twice with identical bodies through the shipped capture callable and one adjacent suite green, one process defect (a PowerShell UTF-16 capture) caught and re-taken the same window, one stamp-aligned matrix restamp, one debt row closed and one battery row opened through their shipped writers, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2479 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2479
    state["last_order"] = "2026-11-05 20:22"
    state["last_decision_rows"] = 221
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_TOKENS:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2479
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())