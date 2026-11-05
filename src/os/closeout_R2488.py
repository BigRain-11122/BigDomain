"""R2488 closeout: append this window's log items and move the tick. One
atomic replace in the state canon, proved by a read-back. No decision token
moved this window (new=0 against the stored baseline), so the baseline list is
carried unchanged and says so.
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
    "2026-11-06 R2488 VERIFICATION window on the two batteries the register owed (reconcile-battery-R2486 and reconcile-battery-R2487, both pre-registered at 571 suites / 4402 criteria), because the R2168 mixed-tree rule puts an owed battery ahead of any further product byte and R2487 had itself disclosed breaking that ordering. Five-silence scan at open: git status empty with no .git/index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the content-addressed decisions diff reading new=0 against the stored 142-token baseline over 304 lines (newest token D-20261105-23), the group orders tail unchanged at 2026-11-05 20:22 equal to the stored last_order, and benchmarks refreshed 2026-11-03 inside the seven-day gate; debt_gate --check --round R2488 read open=4 with the two battery rows first, so this window claimed them rather than a product face.",
    "2026-11-06 R2488 BATTERY GREEN ON THE COMMITTED TREE, MEASURED NOT QUOTED: qa/reconcile-all-R2488.log closes with 'RUNNER PASS (571/571 suites green, reconcile controls 7/7, 1947.4s)' with zero '^FAIL suite' rows, and an independent recount over the 571 per-suite PASS lines sums criteria to exactly 4402 - byte for byte the total pre-registered at R2486, so prediction and measurement agree and no delta had to be explained. The tmp reclaim line reads candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. The run was launched as a detached process with its pid in logs/battery-R2488.pid, because the runner tees through a block-buffered stdout and the shell watchdog cancels a five-minute silence (the R2485 lesson applied rather than re-paid).",
    "2026-11-06 R2488 the four follow-up sections reproduced the designed FAIL-then-regenerate shape: the dry run read SECTION matrix FAIL matrix mismatch on-disk=54827B regenerated=54834B with no byte written, while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN, for VERDICT R2488 FAIL failing=matrix. src/sandbox/suite_matrix.py then regenerated docs/sandbox-suite-matrix.md from THIS round's own evidence through --evidence plus --stamp-from ('PASS generated ... 54834 bytes ... registry suites=571 criteria=4402 evidence=qa/reconcile-all-R2488.log green=571/571'), --check read byte-identical at 54834B / 571 / 4402, and the write leg read all four sections PASS for VERDICT R2488 PASS failing=none (APPENDED 1950B eol_ok=True). The matrix is self-describing this round because its green line names this round's own battery.",
    "2026-11-06 R2488 DEBT closed three rows through their own writer and named why each one was eligible: reconcile-battery-R2486 at line 209 (open 4->3, done 187->188, 126816B -> 126820B, readback ok) and reconcile-battery-R2487 at line 210 (open 3->2, done 188->189, 126820B -> 126824B, readback ok) both discharged by the single green battery above, since R2487's product bytes were on the committed tree that the battery walked; and the carried pointer product-face-R2456 at line 192 (open 2->1, done 189->190, 126824B -> 126827B, readback ok) was closed because its own note names state/queue/tech.md:522 prefix AC-PFKC1 and that row reads [x] [done 2026-11-06 R2486] with a DISCHARGED line beneath it - the pointer named work that had already shipped, and leaving it open would have made the next window rebuild row_key_carrier_scope.",
    "2026-11-06 R2488 honest disclosures: (a) this is a ZERO product-point verification window - nothing a CEO could open was built, and what it bought is that two product windows' worth of proof (the R2486 audit face and the R2487 member page) is now true on a committed tree rather than merely committed; (b) MY OWN MISTAKE IS DISCLOSED RATHER THAN HIDDEN: while looking for the follow-up driver I invoked src/os/closeout_R2480.py with --help, which that one-off script does not parse, so it appended seven stale R2480 log items and moved the tick to 2488; the change was never committed, git checkout restored src/os/state.json to HEAD byte for byte, and this append is the only state write of the round - the lesson is that one-off closeout scripts are not CLI faces and must not be probed; (c) the debt pointer I closed is bookkeeping, not a product claim, and the queue head it pointed at was consumed at R2486, so no work is being suppressed by closing it; (d) Docker is absent on this host, so a containerised bring-up of the six sandbox faces stays unproved and is not claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (f) tasks.md was not touched, it is the P-47 canonical board; (g) no fold was due: src/os/state.json measured 39013B at open against the 78500B waterline with 43 log items.",
    "R2488 tokens: local=~9k api=0 api_reason=verification window - one green detached battery at 571/571 suites and exactly 4402 criteria with an independent recount, one designed matrix FAIL followed by a stamp-aligned regeneration and a byte-identical --check, four follow-up sections PASS for VERDICT R2488 PASS, two owed battery rows plus one stale product pointer closed through the shipped writer, one disclosed and reverted mistaken invocation of a one-off closeout script, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2488 self-heal check: BigDomain-OSLoop exists and reads Ready, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2488
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
          and back["tick"] == 2488
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())