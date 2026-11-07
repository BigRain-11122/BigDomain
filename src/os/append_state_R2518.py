"""append_state_R2518 - record the R2518 battery window in src/os/state.json.

Pure bookkeeping writer: bumps tick, appends the round line, the honest
disclosures line and the token line. Written as a script so the JSON stays
valid and the exact bytes appended are reviewable (the state file is data,
not a hand-edited document).
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-07 R2518 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2517, pre-registered 588 suites / 4504 criteria), "
    "because the R2168 mixed-tree rule puts an owed battery ahead of any "
    "further product byte after R2517 moved the registry by one row. "
    "Five-silence scan clean at HEAD f00dbd48 (git status empty, no "
    "index.lock, zero @BigDomain ledger rows, decisions diff new=0 over the "
    "stored 90-token baseline, group orders tail unchanged at 2026-11-06 "
    "23:46, benchmarks 2026-11-03 inside the gate); debt_gate read "
    "CLAIM-FIRST item=reconcile-battery-R2517 first=yes. The target was "
    "re-measured BEFORE the run by importing reconcile_all.SUITES: 588 "
    "suites / 4504 criteria, byte for byte the registered note. RESULT: "
    "qa/reconcile-all-R2518.log (900373B, utf-8, bom=False, crlf=0, lone_cr=0) "
    "closes with \"RUNNER PASS (588/588 suites green, reconcile controls 7/7, "
    "1146.5s)\", zero FAIL rows, and an independent recount of the 588 PASS "
    "rows summing to exactly 4504 criteria, tmp reclaim 932/932 worlds "
    "326.59 MiB. The battery ran detached (pid in logs/battery-R2518.pid, "
    "removed after the readback) and was never restarted. FOLLOW-UP: "
    "docs/sandbox-suite-matrix.md regenerated stamp-aligned from THIS round "
    "own evidence (--evidence qa/reconcile-all-R2518.log, --stamp-from the "
    "previous doc) to 56541B at 588 suites / 4504 criteria with --check "
    "byte-identical, and its green line now honestly reads 588/588. DEBT: "
    "reconcile-battery-R2517 closed through debt_close (line 241, open 6->5, "
    "done 218->219, 151161B -> 151164B, readback ok); NO successor battery "
    "owed because no registry row and no product byte moved this window; "
    "product-face-R2518 appended first=yes through debt_append (151164B -> "
    "151620B, readback ok) naming the tech head state/queue/tech.md:555 "
    "prefix AC-PDI1 so the next window owes a product face."
)
HONEST = (
    "2026-11-07 R2518 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this "
    "window; the window bought proof that the R2517 tree is green as "
    "committed, which is what the register owed; (b) the battery ran on the "
    "first leg with no retry and no cleanup needed, so the 588/588 claim is "
    "one run rather than a best-of; (c) the matrix stamp line was carried "
    "from the previous document by --stamp-from rather than re-timed, so the "
    "content is this round while the stamp is provenance-only, and the check "
    "compares content only; (d) the group decisions file was READ at 189 rows "
    "/ 89 tokens against a stored baseline of 90 tokens so the scanner reads "
    "new=0 and no decision arrived, and the stored last_decision_rows field "
    "still reads 116 - reported rather than silently rewritten; (e) Docker is "
    "absent on this host so no containerised bring-up of the sandbox faces is "
    "claimed; (f) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (g) "
    "tasks.md was not touched, it is the P-47 canonical board; (h) the S4U "
    "lane reconcile (loop-s4u-reconcile) still needs an ELEVATED shell and "
    "was not attempted - BigDomain-OSLoop re-read this window as Running with "
    "Principal.LogonType=Interactive, which the 2026-09-29 machine law "
    "forbids for lane tasks; (i) the queue head moved from the backlog "
    "carried note (AC-RMSC1) to state/queue/tech.md:555 AC-PDI1 because the "
    "register is the authority and queue_head reported claimable=10, so the "
    "seeded row is what the next window ships."
)
TOKENS = (
    "R2518 tokens: local=~10k api=0 api_reason=verification window - "
    "five-silence scan, one pre-run registry recount by import, one full "
    "588-suite battery in a single leg, one stamp-aligned matrix regeneration "
    "checked byte-identical, one debt row closed and one appended through "
    "their shipped writers, and the state/export/backlog/heartbeat closeout; "
    "zero cloud calls and zero external API touches"
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