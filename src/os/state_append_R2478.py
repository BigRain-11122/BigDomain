"""R2478 closeout: append this verification window's log items and move the
tick. One atomic replace in the state canon, proved by a read-back. No
decision token moved this window (the content-addressed diff read zero new),
so the baseline list is carried unchanged and said so.
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
    "2026-11-05 R2478 VERIFICATION window on the battery R2477 owed (reconcile-battery-R2477, pre-registered at 566 suites / 4372 criteria), because the R2168 mixed-tree rule puts the battery ahead of any further product byte. Five-silence scan at open: git status empty at HEAD 23179787 with no .git/index.lock, zero @BigDomain rows in the evolution ledger, the content-addressed decisions diff reading new=0 against the 142-token baseline, the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, benchmarks refreshed 2026-11-03 inside the seven-day gate, and the tech head AC-PFKC1 with claimable rows so no idle declaration was available. The debt gate read open=3 with reconcile-battery-R2477 first=no among them, so the battery ran FIRST and no product byte was touched.",
    "2026-11-05 R2478 BATTERY LEG 1 RED at 564/566 suites in 1603.6s on the committed tree 23179787 with an empty git status before the run: TWO red suites, and both were real rather than a loose assertion. (a) reconcile-daily-census exit=2 with cd7-live-real-tree naming drift(exit=2) - the shipped writer-census drift detector flagged THREE R2477 evidence captures as new dialects: start-all-live-R2477.log as ps-utf16 and both start-all-R2477-leg1/leg2.log as utf-8-sig with CRLF, so the R2477 window wrote its own proof outside the one UTF-8 LF single-writer law. (b) ledger-apimarket-reportclaims exit=124 - the flat 300s per-suite cap, not an assertion failure.",
    "2026-11-05 R2478 DEFECT (a) REPAIRED AT ITS BIRTH SITE, never by widening the census baseline: src/os/repair_R2478.py decodes each capture, PROVES the line set identical to the decoded original through run_identity.normalize (payload_equal=True on all three), then rewrites UTF-8 LF with one atomic os.replace and a byte read-back - start-all-live 922B utf-16-bom -> 447B, leg1 and leg2 103B utf-8-sig -> 93B each, crlf=0 bom=False on every read-back. Proof after the repair: qa_writer_census.py --check reads flags=0 verdict DRIFT-CLEAN (files=2569 tee=2040 baselined=529) and the suite reads SUITE PASS 8/8 alone in 6s with cd7 at exit=0 label=ok. The repair was committed ALONE as b4e1ac93 before any battery leg 2 was launched, so the green leg walks the repaired tree.",
    "2026-11-05 R2478 DEFECT (b) MEASURED, NOT FIXED, and the reason is stated rather than hidden: ledger-apimarket-reportclaims passes 8/8 alone in 198s (with its three children rc=0) but lost the 300s cap at 300.1s inside a loaded battery, and the SHIPPED headroom reader already reads three ledger suites in the warning band - buyerhistory 232.2s, refundregister 268.1s, reportclaims 300.1s against a 300s cap - so this is the third casualty of the same flat cap (R2393 leg 3 and R2466 leg 2 are the earlier two) rather than a new bug. A bare cap raise is NOT a legal fix here: the deployed os-runner-suite-timeout-headroom fixture pins the 300s default AS A READING (AC-RTH3 expects a 194.9s leg to read BAND-HIT), so raising the runner cap alone would silently make that instrument lie. Landed instead: one debt row runner-suite-timeout-cap through the shipped debt_append (123367B -> 124306B, readback ok, first=no) and one tech seed row with AC-RSC1..AC-RSC6 pinned BEFORE any code in src/os/seed_queue_R2478.py (tech.md 528 -> 529 lines, once=True, lf_only=True), whose shape is one named cap constant read from the runner source by the reader plus a declared per-suite override.",
    "2026-11-05 R2478 BATTERY LEG 2 GREEN on the repaired committed tree b4e1ac93: RUNNER PASS 566/566 suites green plus reconcile controls 7/7 in 1224.2s and the closing summary line reads 'PASS suites 566/566 green, expected criteria total=4372', i.e. EXACTLY the total pre-registered at R2477, so the prediction matched the measurement. Birth-site TMP RECLAIM candidates=932 removed=932 busy=0 failed=0 reclaimed 326.59 MiB. Evidence qa/reconcile-all-R2478-leg2.log written by ONE utf-8 LF single writer through src/os/battery_stream.py, launched detached and unfiltered into logs/battery-R2478leg2-stdout.log so the R2211/R2268/R2348/R2453/R2461 filtering-pipe trap was not re-paid. Both legs are kept: qa/reconcile-all-R2478.log is the red leg 1 and it is committed rather than deleted, because the repair has to be readable against what it repaired.",
    "2026-11-05 R2478 the four follow-up sections produced the designed order: the dry run read SECTION matrix FAIL matrix mismatch on-disk=54461B regenerated=54474B with NO byte written while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN for VERDICT R2478 FAIL failing=matrix at exit 2; then src/sandbox/suite_matrix.py regenerated docs/sandbox-suite-matrix.md from THIS round own green evidence through --evidence plus --stamp-from and printed 'PASS generated 54474 bytes, registry suites=566 criteria=4372 evidence=qa/reconcile-all-R2478-leg2.log green=566/566' with --check reading byte-identical at 54474B / 566 / 4372; the write leg then read all four sections PASS - matrix byte-identical, fingerprint CLEAN, profile byte-identical, census DRIFT-CLEAN - for VERDICT R2478 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this round at green=566/566 because it names this round own battery rather than a borrowed older leg.",
    "2026-11-05 R2478 debt register closed through its own writer: reconcile-battery-R2477 closed through debt_close at its predicted 123363B -> 123367B (line=203, open 3->2, done 181->182, readback=ok) after a dry run that named exactly those deltas. NO successor battery was registered because this window changed no product src byte - the repair moved three qa evidence files and added one repair script, a launcher and a seeder, none of them a module - and the registry is unmoved at 566 suites / 4372 criteria. The two rows now open are the carried internal audit row product-face-R2456 (state/queue/tech.md:522 prefix AC-PFKC1) and the new runner-suite-timeout-cap, so the NEXT window may ship a BUSINESS face and should name the supersession of the audit row per the CEO standing order OB-20261105-003656-879.",
    "2026-11-05 R2478 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was rebuilt, and no P-47 business surface was touched; what it bought is a proved registry (566 suites, 4372 criteria) on the exact tree R2477 committed, so the one-command launcher shipped there is now PROVED rather than merely shipped; (b) the first leg was RED and the window says so plainly instead of reporting only the green leg - the red leg is a real defect in R2477 own evidence hygiene plus a cap casualty, not a flake; (c) the repair is dialect-only and proves payload identity, so no evidence byte was silently lost and no census baseline was widened; (d) the timeout is NOT fixed this window and is not claimed to be - it is measured, named, and pre-registered for the next product window; (e) the retry leg ran on a much less loaded machine (1224.2s versus 1603.6s) which is exactly why reportclaims finished, and that dependence on load is the defect being registered rather than hidden; (f) Docker is absent on this host, so a containerised bring-up of the sandbox faces stays unproved and is not claimed; (g) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (h) tasks.md was not touched, it is the P-47 canonical board; (i) no fold was due: src/os/state.json measured 32647B at open against the 78500B waterline.",
    "R2478 tokens: local=~12k api=0 api_reason=verification window - one full reconcile battery RED at 564/566 naming two real defects, one birth-site dialect repair proven payload-identical and then census DRIFT-CLEAN plus the red suite 8/8 alone, one suite timed alone at 198s to separate load from defect, one full retry battery GREEN at 566/566 and 4372 criteria on the repaired committed tree, four follow-up sections in the designed order for VERDICT PASS, one battery row closed and one timeout row opened through their shipped writers, one tech seed row with six criteria pinned before code, and the state/export/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-05 R2478 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2478
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
          and back["tick"] == 2478
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())