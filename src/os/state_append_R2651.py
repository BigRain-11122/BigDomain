"""state_append_R2651 - the R2651 verification window narrative and tokens.

Every number below was measured off the tree in this window: the battery
evidence re-measured on bytes, the criteria recounted independently from the
PASS rows, the matrix byte counts on both sides of the regeneration, and the
debt register byte counts.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
NEW_DEC = ()

LINES = [
    "2026-11-12 R2651 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2649, pre-registered 650 suites / 4876"
    " criteria at R2649 because that window moved one product src file and one"
    " registry row). Five readings at open: git status EMPTY at HEAD c6d79c12"
    " with no index.lock; ZERO unreplied @BigDomain rows in"
    " cph4/evolution-ledger.md (atbd_lines=0 unreplied_groups=0); the"
    " content-addressed scan read 339 rows and tokens=195 with new=0; the"
    " group orders tail still carries the 2026-11-12 01:5x CEO-PROXY R40 row"
    " already recorded as last_order and judged knowledge-only for this"
    " company; benchmarks_refreshed 2026-11-10 sitting two days inside the"
    " seven-day gate. debt_gate read CLAIM-FIRST"
    " item=reconcile-battery-R2649 opened=R2649 carried=unknown open=45"
    " first=1, so the R2168 mixed-tree rule put the battery ahead of the queue"
    " head at tech line 663 prefix AC-EDWZ1.",
    "R2651 TARGET RE-MEASURED BY IMPORT BEFORE THE RUN: 650 suites and 4876"
    " criteria, byte for byte the pre-registered number, so the prediction"
    " matched the measurement and nothing had to be named or swept.",
    "R2651 BATTERY GREEN measured not quoted: qa/reconcile-all-R2649.log is"
    " 1099093B as delivered and 1101044B after the follow-up block, utf-8 with"
    " bom=False, crlf=0, lone_cr=0 and nul=0, 8632 lines, closing"
    " 'RUNNER PASS (650/650 suites green, reconcile controls 7/7, 4193.2s)'"
    " with BATTERY rc=0, ZERO FAIL suite rows, 650 PASS suite rows carrying 650"
    " UNIQUE names, and an independent recount over their criteria fields"
    " summing to EXACTLY 4876; TMP RECLAIM candidates=697 removed=697 busy=0"
    " failed=0 reclaimed=241.16 MiB. The leg was launched detached through"
    " src/os/battery_stream.py from a one-off launcher that was DELETED before"
    " the commit, with its stream and its pid in SEPARATE files under logs/, so"
    " no shell redirection dialect could reach qa/.",
    "R2651 FOUR FOLLOW-UP SECTIONS in the designed order: the dry run read"
    " matrix FAIL first BY DESIGN at on-disk 66616B against regenerated 66600B"
    " with NO byte written while fingerprint read CLEAN domains=5, profile read"
    " byte-identical and census read DRIFT-CLEAN; docs/sandbox-suite-matrix.md"
    " was then regenerated stamp-aligned from THIS round own green evidence"
    " through src/sandbox/suite_matrix.py --evidence plus --stamp-from to"
    " 66600B at 650 suites / 4876 criteria with its green line honestly"
    " reading 650/650 self-describing and --check byte-identical at rc=0; the"
    " write leg then read all four sections PASS for VERDICT R2649 PASS"
    " failing=none (APPENDED 1951B eol_ok=True).",
    "R2651 DEBT through the shipped writers: reconcile-battery-R2649 closed at"
    " its predicted and measured 209269B -> 209272B (line 384, open 45->44,"
    " done 322->323, readback ok); the gate then read OPEN-NONE with first=0"
    " and said this window owes one row, so product-face-R2651 was appended"
    " first=yes at the predicted 209272B -> 209830B naming the next window a"
    " PRODUCT face on the queue head state/queue/tech.md:663 prefix AC-EDWZ1"
    " whose AC-EDWZ1..AC-EDWZ6 were pinned in that row at R2649 BEFORE any"
    " code. NO successor battery is owed: this window moved no product src"
    " byte and no registry row, and the registry was re-measured by import at"
    " 650 / 4876.",
    "R2651 honest disclosures: (a) ZERO product points on the Executive"
    " Protocol scale - nothing a CEO could newly open was built and no P-47"
    " business surface moved, so every P-47 item still waits on CEO physical"
    " pieces (merchant id, mini-program appid/secret); (b) the window ran far"
    " past its 25-minute budget because the leg measured 4193.2s against a"
    " 25-minute window, and that overshoot is stated rather than dressed up;"
    " (c) the leg was adopted from its own detached process and re-measured on"
    " bytes, never quoted from its closing line alone; (d) src/os/scan_five_"
    " still.py still crashes at its final [ORD-TOP] print on the GBK console,"
    " so every scan was run under PYTHONIOENCODING=utf-8 - WORKED AROUND, NOT"
    " REPAIRED; (e) Docker is absent on this host so no containerised bring-up"
    " of the sandbox faces is claimed; (f) tasks.md was not touched, it is the"
    " P-47 canonical board; (g) BigDomain-OSLoop still reads InteractiveToken"
    " and needs an ELEVATED shell for its S4U re-registration (carried"
    " ceo-pending physical item loop-s4u-reconcile).",
    "R2651 tokens: local=~14k api=0 api_reason=verification window - one"
    " five-silence scan with the content-addressed decisions scan, the group"
    " orders tail and the ledger face read, one debt gate read, one target"
    " re-measure by import, one detached battery leg adopted and measured on"
    " bytes with an independent criteria recount, one designed matrix FAIL then"
    " one stamp-aligned regeneration checked byte-identical, one verdict append,"
    " one debt row closed and one successor appended through their shipped"
    " writers, and the state/export closeout; zero cloud calls and zero"
    " external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    tokens = list(state.get("last_dec_tokens") or [])
    for token in NEW_DEC:
        if token not in tokens:
            tokens.append(token)
    state["last_dec_tokens"] = tokens
    state["last_decision_rows"] = 339
    state["last_order"] = "2026-11-12 01:5x"
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"])
    print("APPEND tick=%d lines=%d tokens=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), len(reread["last_dec_tokens"]), before,
             len(check), "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
