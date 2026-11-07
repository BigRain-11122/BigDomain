"""R2520 state append: the verification window on the battery R2519 owed."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2520 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2519, pre-registered 589 suites / 4510 criteria). "
    "Five-silence scan clean at HEAD 37c5f448 (git status empty, no "
    "index.lock, zero @BigDomain rows in cph4/evolution-ledger.md, "
    "content-addressed decisions diff new=0 over the stored 90-token baseline "
    "at a measured 190 rows, group orders tail unchanged at 2026-11-06 23:46 "
    "so last_order stands, benchmarks 2026-11-03 inside the seven-day gate); "
    "debt_gate read CLAIM-FIRST item=reconcile-battery-R2519 opened=R2519 "
    "carried=unknown open=6 first=1. The target was re-measured BEFORE the "
    "run by importing reconcile_all.SUITES (the module lives in src/sandbox "
    "and the first probe of src/os was a wrong path, disclosed): 589 suites "
    "and 4510 criteria, byte for byte the registered note.",

    "2026-11-07 R2520 LEG 1 RED AND THE RED LEG KEPT "
    "(qa/reconcile-all-R2520.log, 904869B): 585/589 suites green with FOUR "
    "failed assertions, os-matrix-stamp-compare AC-MSC4 plus AC-ADTR3, "
    "AC-EVNM3 and AC-STPT3, each reading --check at rc=2 where the suite "
    "expects rc=0. READ THE CAUSE, DID NOT GUESS IT: the shipped "
    "docs/sandbox-suite-matrix.md was regenerated at R2519 against "
    "qa/probe-seam-dynamic-import-scope-R2519.log, a PRODUCT suite log, "
    "instead of an eligible battery leg - the shipped tool said so itself "
    "(evidence-face: doc-recorded=qa/probe-seam-dynamic-import-scope-R2519.log "
    "check-resolved=qa/reconcile-all-R2518.log) and the rendered table carried "
    "no-evidence in every per-suite evidence cell, which R2519 own log already "
    "reported as a green line reading 0/589. REPAIR AT THE BIRTH SITE: the doc "
    "was regenerated stamp-aligned through suite_matrix.py from the eligible "
    "battery leg qa/reconcile-all-R2518.log (56656B, 589 suites, 4510 "
    "criteria, green honestly 588/589), --check then read byte-identical at "
    "rc=0 and all four red suites re-read SUITE PASS 6/6 alone. The repair "
    "plus the red leg were committed ALONE as c9732e67 so the retry ran on a "
    "committed tree with an empty git status.",

    "2026-11-07 R2520 RETRY GREEN ON THE COMMITTED REPAIR TREE, measured not "
    "quoted: qa/reconcile-all-R2520-retry.log is 904220B, utf-8, bom=False, "
    "crlf=0, lone_cr=0, closing RUNNER PASS (589/589 suites green, reconcile "
    "controls 7/7, 1192.3s), zero FAIL suite rows, and an independent recount "
    "over the 589 PASS rows summing to EXACTLY 4510 criteria - the "
    "pre-registered total matched by measurement. Launched detached and "
    "unfiltered through src/os/battery_stream.py (pid in "
    "logs/battery-R2520-retry.pid) so the filtering-pipe trap was not "
    "re-paid. FOUR FOLLOW-UP SECTIONS in the designed order: the dry run read "
    "SECTION matrix FAIL on-disk=56656B against regenerated=56676B with NO "
    "byte written while fingerprint read CLEAN domains=5, profile "
    "byte-identical and census DRIFT-CLEAN; docs/sandbox-suite-matrix.md was "
    "then regenerated stamp-aligned from THIS round own green evidence "
    "through src/sandbox/suite_matrix.py --stamp-from (56676 bytes, 589 "
    "suites / 4510 criteria, green=589/589 self-describing), --check read "
    "byte-identical, and the re-run read all four PASS for VERDICT retry PASS "
    "failing=none (APPENDED 1950B eol_ok=True).",

    "2026-11-07 R2520 DEBT AND BOARD: reconcile-battery-R2519 closed through "
    "the shipped debtor at its predicted 151915B -> 151918B (line=244, open "
    "6->5, done 220->221, readback ok) and product-face-R2520 was appended "
    "first=yes through the shipped appender at its predicted 151918B -> "
    "152424B (readback ok) naming the next window a PRODUCT face on tech head "
    "state/queue/tech.md:557 prefix AC-PCB1 probe_seam_constant_binding_scope, "
    "whose AC-PCB1..AC-PCB6 were pinned in that row at R2519 BEFORE any code. "
    "NO successor battery is owed because this window moved no product src "
    "byte and the registry is unmoved at 589 suites / 4510 criteria, which is "
    "exactly what the green leg measured; the count was re-read by import "
    "rather than trusted, and queue_head read claimable=10 at line 557 with "
    "the floor MET.",

    "2026-11-07 R2520 honest disclosures: (a) ZERO product points on the "
    "Executive Protocol scale - nothing a CEO could open was built this "
    "window and none is claimed; the deliverable is a green 589/4510 battery "
    "plus a CEO-visible matrix document whose evidence column is real again. "
    "(b) the red cause was BORN in the previous window: R2519 regenerated the "
    "shipped doc from a product suite log, so every evidence cell read "
    "no-evidence and its own green line read 0/589; that window disclosed the "
    "0/589 line but not the cause, and this window names it. (c) my first "
    "registry re-measure probed src/os/reconcile_all.py and failed with "
    "ModuleNotFoundError before the right path src/sandbox/reconcile_all.py "
    "was measured - reported rather than hidden. (d) the repair changed a "
    "shipped document only (plus the red leg as evidence); no src product byte "
    "and no registry row moved, so no successor battery is owed. (e) the "
    "window overshot its 25-minute budget on two full 589-suite batteries "
    "(1192.3s for the green leg alone) and says so. (f) the decisions baseline "
    "stored last_decision_rows now records the measured 190 rows; no new "
    "token arrived this round. (g) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed. (h) the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret). (i) tasks.md was not touched, "
    "it is the P-47 canonical board. (j) the S4U lane reconcile "
    "(loop-s4u-reconcile) still needs an ELEVATED shell and was not "
    "attempted; BigDomain-OSLoop still reads InteractiveToken.",

    "R2520 tokens: local=~11k api=0 api_reason=verification window - "
    "five-silence scan, one registry target re-measured by import, one full "
    "589-suite battery kept red, one cause read from the shipped tool own "
    "evidence-face line rather than guessed, one birth-site doc repair "
    "committed alone with its red leg, one full 589-suite retry green at the "
    "pre-registered 4510 criteria, four follow-up sections plus one "
    "stamp-aligned matrix regeneration checked byte-identical, one debt row "
    "closed and one opened through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2520
    state["last_decision_rows"] = 190
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
          and back["tick"] == 2520
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())