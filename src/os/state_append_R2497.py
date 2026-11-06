"""state_append_R2497 - append this product window's log items and bump the tick."""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"

SUMMARY = (
    "2026-11-06 R2497 PRODUCT window on the tech head the register named "
    "(product-face-R2496, state/queue/tech.md:531 prefix AC-EDQF1 "
    "export_driver_queue_face, criteria AC-EDQF1..AC-EDQF6 pinned in that row at "
    "R2453 BEFORE any code). Five-silence scan at open was clean at HEAD "
    "62713a50 equal to origin/main (git status empty, no index.lock, zero "
    "@BigDomain ledger rows, decisions diff new=1 being the known prose artifact "
    "D-20261105-0, benchmarks 2026-11-03 inside the seven-day gate) except the "
    "group orders tail, which had moved to 2026-11-06 23:46 and is judged below. "
    "The debt gate read CLAIM-FIRST item=product-face-R2496 first=1 because "
    "R2496 discharged its battery and changed no registry module, so the product "
    "byte came first. CLAIM: export_R2431.main re-derived the CEO-visible queue "
    "block itself out of `queue_floor --check --json` while the published "
    "section the house reads is queue_floor_export_face.face - the DISCOUNTED "
    "reading with delivered_total - so one document had two derivations and "
    "MEASURED TWICE (R2452, R2453) a freshly refreshed export read STALE "
    "(claimable=5,10,10) and had to be fixed by hand."
)

SHIPPED = (
    "2026-11-06 R2497 SHIPPED src/os/export_driver_queue_face.py plus "
    "src/os/test_export_driver_queue_face.py, and the gross reading path was "
    "DELETED from src/os/export_R2431.py rather than left unused. The section "
    "the driver publishes IS queue_floor_export_face.face asked as an attribute "
    "at CALL time (the suite patches that reading and watches the section move); "
    "refresh() updates the section IN PLACE so every already-published key of "
    "the document keeps its value and its position (rows refreshed by queue name, "
    "never reordered); publish() stages the composed bytes in the target own "
    "dialect through the shipped audit, asks queue_export_freshness_gate.check "
    "on the staged file BEFORE any replace, refuses with the gate own verdict "
    "word and leaves the document byte-identical with no residue when the queue "
    "moved between the reading and the write, and returns the gate verdict plus "
    "the byte count so the driver prints them (queue=<verdict> queue_bytes=<n> "
    "queue_drifted=<names>) instead of writing silently."
)

PROOF = (
    "2026-11-06 R2497 PROOF measured, not quoted: AC-EDQF1..AC-EDQF6 SUITE PASS "
    "6/6 TWICE with identical verdicts plus five adjacent suites green "
    "(qa/export-driver-queue-face-R2497.log, 2657B, utf-8, bom=False, crlf=0, "
    "lone_cr=0, legs=2 identical=True adjacent=5 fails=0); the adjacent set was "
    "the queue export face, the freshness gate, the gate wire, the writer "
    "dialect wire and the publish path guard, because this window changed the "
    "export driver and the registry. MEASURED on the real tree through the "
    "driver itself: queue=CURRENT, queue_drifted=(none), the queue face re-reads "
    "CURRENT at exit 0 and the gate reports no drift. REGISTRY: one runner row "
    "os-export-driver-queue-face(6), so 576 suites / 4432 criteria becomes 577 / "
    "4438, recounted by importing reconcile_all.SUITES rather than quoted."
)

QUEUE = (
    "2026-11-06 R2497 BOARD: the claimed row state/queue/tech.md:531 was closed "
    "through a per-round stamp writer with its discharge note (dry run first, "
    "then one atomic replace, predicted 1635465B -> 1638291B and measured "
    "exactly, readback ok) and ONE real measured gap was seeded beneath it: a "
    "copy of the real export whose queue block was doctored (verdict FLOOR-DEBT, "
    "tech claimable set to 0) still reads pass=21 fail=0 on "
    "check_export_consistency while queue_export_freshness_gate on the same "
    "document reads STALE with drifted=section:shortfall_total, "
    "section:delivered_total,queue:tech - so the face every window trusts cannot "
    "see a stale queue block at all. That became the next head as "
    "AC-ECQF1..AC-ECQF6 (export_consistency_queue_face), pre-registered in the "
    "new row BEFORE any code. The floor re-read FLOOR-MET main=5/5 tech=10/10 "
    "explore=10/10 because one row closed and one was seeded."
)

HONEST = (
    "2026-11-06 R2497 honest disclosures: (a) this is an INTERNAL driver face - "
    "it is worth two product points on the Executive Protocol scale because a "
    "real shipped write path changed behaviour, but no CEO-visible business "
    "surface was built and nothing a CEO would open is new; (b) the seed defect "
    "was bought twice by earlier windows of mine, so it is named as mine rather "
    "than blamed on the tool; (c) the doctored-document measurement behind the "
    "new row is a fixture measurement, not a live catch, and it is described as "
    "such; (d) Docker is absent on this host so no containerised bring-up is "
    "claimed; (e) the real 19.9 debit and the real msgSecCheck still wait on CEO "
    "physical items (merchant id, mini-program appid/secret); (f) tasks.md was "
    "not touched, it is the P-47 canonical board; (g) state.json measured about "
    "31KB at open, far under the 78500B waterline, so no fold was due and none "
    "ran."
)

DECISION = (
    "2026-11-06 R2497 group scan: the content-addressed decisions diff read new=1 "
    "over the 78-token baseline and that single token is D-20261105-0, the known "
    "prose artifact out of a '0x7' count on decisions.md rather than a dispatch; "
    "it is recorded in the baseline so it cannot re-read as a phantom. "
    "cph4/evolution-ledger.md carried no @BigDomain row. The group orders tail "
    "moved to 2026-11-06 23:46 OB-20261106-2346-345 (CEO: go align with the "
    "fleet and the master and start everything automatically) and the row names "
    "bm-c surgical convergence, SELF-IMPROVE receipts, a fleet-wide broadcast, "
    "lifting bm-a's 11:46 yield state and a bm-m heartbeat stall - a fleet lane "
    "ruling with NO BigDomain execution face, so it was ACKNOWLEDGED with no "
    "action and last_order advanced to 2026-11-06 23:46."
)

LEDGER = (
    "R2497 tokens: local=~22k api=0 api_reason=product window - one "
    "pre-registered face shipped with its six criteria, one gross derivation "
    "deleted at its birth site, one suite proved twice with five adjacent suites "
    "green, one registry row and 577/4438 recounted by import, one queue row "
    "closed and one measured gap seeded through a per-round stamp writer, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero external "
    "API touches"
)

SELF_HEAL = (
    "2026-11-06 R2497 self-heal check: BigDomain-OSLoop exists and reads Ready, "
    "but its Principal.LogonType still reads Interactive, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 needs "
    "an elevated shell while this session is unelevated, so the definition was "
    "left untouched again (carried as the stale row loop-s4u-reconcile)."
)


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == SELF_HEAL:
        print("already appended")
        return
    state["log"].extend([SUMMARY, SHIPPED, PROOF, QUEUE, HONEST, DECISION,
                         LEDGER, SELF_HEAL])
    state["tick"] = 2497
    state["last_order"] = "2026-11-06 23:46"
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
    if len(back["log"]) != len(state["log"]) or back["tick"] != 2497:
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d tick=%s tokens=%d bytes=%d" % (
        len(back["log"]), back["tick"], len(back["last_dec_tokens"]),
        os.path.getsize(PATH)))


if __name__ == "__main__":
    main()