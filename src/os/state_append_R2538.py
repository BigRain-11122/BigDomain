"""R2538 state append: tick 2538, the verification window log lines, baselines.

The shipped state_fold layout reader still does not match the dumped file
(disclosed since R2522), so this appends through a proved load+dump round-trip
instead of reformatting the file.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2538 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2537, pre-registered 598 suites / 4564 criteria as "
    "the R2537 window registered when it moved the registry by one row). "
    "Five-silence scan at open: git status EMPTY at HEAD bc7cc37d with no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, the "
    "content-addressed decisions scan reading new=0 (237 rows, 148 tokens) "
    "against the stored baseline, the group orders tail carrying only a "
    "2026-11-07 18:01 fleet auto-dispatch row judged knowledge-only, "
    "benchmarks 2026-11-03 inside the seven-day gate; debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2537 first=1, so the R2168 "
    "mixed-tree rule put the battery ahead of any product byte.",

    "2026-11-07 R2538 LEG 1 WAS RED AND IS KEPT (qa/reconcile-all-R2538.log, "
    "939714B): RUNNER FAIL (2 failed assertions) at 597/598 suites in "
    "1280.5s with the criteria total exactly the pre-registered 4564, the "
    "only red suite being reconcile-daily-census at cd7-live-real-tree "
    "exit=2 drift. The cause was READ, not guessed: the shipped writer "
    "census --check named exactly one file - qa/reconcile-all-R2538.stdout.log "
    "class=ps-utf16 - which was THIS window own transport artifact, a "
    "PowerShell redirection of the battery stdout into the evidence "
    "directory; the file was deleted, the census re-read DRIFT-CLEAN "
    "flags=0 files=2681, and the red leg was committed ALONE as e11fa6fd "

    "before the retry.",

    "2026-11-07 R2538 RETRY GREEN on the repaired tree: "
    "qa/reconcile-all-R2538-retry.log reads RUNNER PASS (598/598 suites "
    "green, reconcile controls 7/7, 1260.7s, BATTERY rc=0). The four "
    "follow-up sections ran in the designed order: matrix FAILED first by "
    "design on a stale doc (on-disk 57696B vs regenerated 57715B, no byte "
    "written) and the doc was regenerated stamp-aligned from this round own "
    "green evidence through suite_matrix.py --stamp-from (57715B at 598 "
    "suites / 4564 criteria, green=598/598 self-describing), with --check "
    "then byte-identical; the second pass read four PASS - matrix "
    "byte-identical 57715B, fingerprint CLEAN domains=5, profile "
    "byte-identical, census DRIFT-CLEAN - for VERDICT R2538 PASS "
    "failing=none. DEBT: reconcile-battery-R2537 closed through debt_close "
    "(line 270, open 17->16, done 236->237, 164872B -> 164875B, readback ok) "
    "and product-face-R2538 appended first=yes naming tech head AC-PNSB1 "
    "(164875B -> 165045B, readback ok), so the gate now names the product "
    "face.",

    "2026-11-07 R2538 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - this is a verification window and nothing a "
    "CEO could newly open was built, and no P-47 business surface moved; (b) "
    "the red was born in this window own transport, not in product code: a "
    "PowerShell redirection of battery stdout into qa/ lands UTF-16 and the "
    "census flags it, which is the fifth recorded instance of this same "
    "trap - the durable repair is to always pass --evidence to "
    "battery_stream.py and never redirect its stdout into the evidence "
    "directory; (c) TWO full batteries ran (1280.5s red + 1260.7s green), so "
    "this window ran far past the 25-minute budget, and the first launch was "
    "additionally killed once by the shell tool own five-minute silence "
    "limit because its stdout was redirected away from the caller; (d) "
    "MEASURED DEFECT STILL OPEN from R2522: the shipped state_fold layout "
    "reader no longer matches the state file written with json.dump, so this "
    "window appended through a proved load+dump round-trip rather than "
    "reformatting the file; (e) Docker is absent on this host so no "
    "containerised bring-up is claimed; (f) the real 19.9 debit and the real "
    "msgSecCheck still wait on CEO physical items (merchant id, mini-program "
    "appid/secret); (g) tasks.md was not touched, it is the P-47 canonical "
    "board; (h) the S4U lane reconcile still needs an ELEVATED shell and "
    "remains a ceo-pending physical item with zero chase.",

    "R2538 tokens: local=~18k api=0 api_reason=verification window - "
    "five-silence scan, one content-addressed decisions scan reading new=0, "
    "two full reconcile batteries (one red, one green) streamed through the "
    "single-writer runner, one census read naming the red cause at its birth "
    "site, one stamp-aligned matrix regeneration from this round own green "
    "evidence checked byte-identical, four follow-up sections through their "
    "shipped runner, two debt rows moved through their shipped writers, and "
    "the state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2538
    state["last_order"] = "2026-11-07 18:01"
    state["log"].extend(LINES)
    state["last_dec_tokens"] = list(state.get("last_dec_tokens") or [])
    state["last_decision_rows"] = 237
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2538
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d tokens=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(back["last_dec_tokens"]), os.path.getsize(PATH),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())