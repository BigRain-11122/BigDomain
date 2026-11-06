"""R2495 closeout state append (one-off): the owed battery, recorded honestly.

The round was interrupted after its repairs were committed (3f4adbbd) and its
green retry battery finished at 10:29 without ever being recorded or committed.
This append finishes that same round rather than opening a new one.
"""

import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"

if SRC not in sys.path:
    sys.path.insert(0, SRC)

SUMMARY = (
    "2026-11-06 R2495 VERIFICATION window, resumed: this round was interrupted "
    "after its repairs landed (commit 3f4adbbd kept the RED first battery leg as "
    "evidence) and its green retry finished at 10:29 with nothing recorded, so "
    "this window finished the SAME round instead of opening a new one. CLAIM: "
    "the register owed reconcile-battery-R2495 at the pre-registered 576 suites "
    "/ 4432 criteria (R2168 mixed-tree rule puts the battery ahead of any "
    "further product byte). RESULT: qa/reconcile-all-R2495-retry.log is GREEN - "
    "closing line \"RUNNER PASS (576/576 suites green, reconcile controls 7/7, "
    "1125.6s)\", zero FAIL rows, an independent recount over the 576 suite rows "
    "summing to exactly 4432 criteria, utf-8 / bom=False / crlf=0 / lone_cr=0, "
    "871018B, and 932/932 tmp worlds reclaimed at 326.59 MiB. The first leg's "
    "RED run stays committed as evidence rather than deleted. DEBT: "
    "reconcile-battery-R2495 closed through its own writer (line 217, open 2->1, "
    "done 196->197, 131100B -> 131104B, readback ok); NO successor battery is "
    "owed because this window changed only qa/, state/ and docs/ - no registry "
    "module and no suite, so the registry stands unmoved at 576 suites / 4432 "
    "criteria and the next window owes a BUSINESS face, not another battery. "
    "HONEST: zero product points this window; the twelve-hour gap between the "
    "green retry (10:29) and this closeout (22:35) is disclosed, not dressed "
    "up; Docker is absent so no containerised bring-up is claimed; the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items; "
    "tasks.md untouched; the one remaining open debt row is loop-s4u-reconcile "
    "(first=no, needs an elevated shell) so the gate reads OPEN-NONE and this "
    "window did not invent a first=yes row to silence it."
)

DECISION = (
    "2026-11-06 R2495 group transfer scan: decisions.md carried eight tokens "
    "past the R2494 baseline - D-20261106-05 (lane liveness vs commit receipts, "
    "bm-b/bm-c/bm-m/bm-d statuses), D-20261106-06 (24h zero-dispatch rule), "
    "D-20261106-07 (audit-sentinel PROBE A invalid-transfer reclassification), "
    "D-20261106-08 (BigLife SILENT-BY-DESIGN), D-20261106-09 (HQ schedule "
    "hardening batch, resume +6h), D-20261106-10 (@HQ dispatch chief owes two P1 "
    "rows by 18:00), D-20261106-11 (bm-a 690/296 branch divergence), "
    "D-20261106-12 (disk retention top-20 by 18:00) - every one is a fleet, HQ "
    "or sibling-company lane ruling with NO BigDomain execution face, so all "
    "eight were ACKNOWLEDGED with no action taken; last_dec_tokens advanced from "
    "69 to the full 77-token set read from decisions.md this window, and "
    "last_decision_rows was re-measured at 158 lines (the prior 221 did not "
    "match the file, so the token set is carried as the authority, not the "
    "count). No new @BigDomain row was found in cph4/evolution-ledger.md and "
    "orders.md carried no newer timestamp than 2026-11-05 20:22."
)

LEDGER = (
    "R2495 tokens: local=~26k api=0 api_reason=verification closeout only - one "
    "owed battery already on disk (read, recounted and committed rather than "
    "re-run), one decision-token diff, one debt close through the shipped "
    "writer, one export re-derivation and one commit; zero cloud calls and zero "
    "external API touches, with no product byte shipped and none claimed"
)


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LEDGER:
        print("already appended")
        return
    state["log"].extend([SUMMARY, DECISION, LEDGER])
    state["tick"] = 2495
    raw = io.open(DEC, "r", encoding="utf-8").read()
    tokens = sorted(set(re.findall(r"[DC]-\d{8}-\d{2}", raw)))
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = len(raw.splitlines())
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if len(back["log"]) != len(state["log"]) or back["tick"] != 2495:
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d tick=%s tokens=%d bytes=%d" % (
        len(back["log"]), back["tick"], len(back["last_dec_tokens"]),
        os.path.getsize(PATH)))


if __name__ == "__main__":
    main()