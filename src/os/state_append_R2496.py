"""R2496 closeout state append (one-off): the owed battery, red then green.

The register owed reconcile-battery-R2496 because R2495 repaired a shipped
module after the last battery ran. This append records the red first leg, the
two birth-site repairs and the green retry, plus the group-order scan.
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
    "2026-11-06 R2496 VERIFICATION window on the battery the register owed "
    "(reconcile-battery-R2496, pre-registered 576 suites / 4432 criteria "
    "because R2495 repaired the shipped export base export_R2431.py at its "
    "birth site). Five-silence scan at open was clean at HEAD 156c4d2b equal to "
    "origin/main (git status empty, no index.lock, zero @BigDomain ledger rows, "
    "content-addressed decisions diff new=0 over a 77-token baseline) EXCEPT the "
    "group orders tail, which had moved: six CEO rows at 20:2x, 20:5x, 21:3x, "
    "21:4x, 22:0x and 22:5x (tooling audit, tool test board, disk cleanup plus "
    "fleet broadcast, DOC-DELIVERY-LAW bus, deletion mandate, "
    "LOCAL-COMPUTE-ALLOCATION) were read in full and every one is a fleet or HQ "
    "ruling with NO BigDomain execution face, so all six were ACKNOWLEDGED with "
    "no action taken and last_order advanced to 2026-11-06 22:5x. debt_gate read "
    "OPEN-NONE open=2 first=0 and the R2168 mixed-tree rule ranked the owed "
    "battery ahead of any product byte, so it was claimed first."
)

RED = (
    "2026-11-06 R2496 the FIRST leg came back RED (574/576, three failed "
    "assertions across two matrix suites) and the red leg was KEPT rather than "
    "re-run - qa/reconcile-all-R2496.log, committed as 55aa22b1 - and both "
    "causes reproduced ALONE at the runner cwd, so they are real birth-site "
    "defects rather than load noise: (a) os-matrix-stamp-from-liveness AC-MSFL5 "
    "'two renders are byte-identical' compared two PLAIN renders, and a plain "
    "render stamps the wall clock at MINUTE resolution, so two renders that "
    "straddled a minute under battery load differed on exactly that line - a "
    "determinism proof measuring the clock; (b) os-matrix-stamp-compare AC-MSC4 "
    "measured check=2 live=PASS agrees=False because the shipped doc recorded "
    "qa/reconcile-all-R2493-retry.log while suite_matrix --check resolved "
    "qa/reconcile-all-R2495-retry.log: R2495 adopted a pre-existing green log "
    "and never regenerated the document from it, so the newest eligible "
    "evidence face could not agree with the recorded one. BOTH repaired at the "
    "birth site and committed ALONE as f48b67c6: the two renders now borrow the "
    "doc own stamp through the shipped --stamp-from law so no clock is asked "
    "and the comparison stays byte for byte, and the document was regenerated "
    "stamp-aligned from the newest eligible green evidence (55309B, --check "
    "byte-identical). After the repair both suites read SUITE PASS 6/6 and the "
    "liveness suite read two identical legs."
)

RETRY = (
    "2026-11-06 R2496 RETRY GREEN ON THE COMMITTED REPAIR TREE, MEASURED NOT "
    "QUOTED: qa/reconcile-all-R2496-retry.log is 871017B with bom=False crlf=0 "
    "lone_cr=0, its closing line reads 'RUNNER PASS (576/576 suites green, "
    "reconcile controls 7/7, 1080.4s)' with zero FAIL suite rows, an independent "
    "recount over the 576 PASS rows sums to exactly 4432 criteria - byte for "
    "byte the pre-registered target - and tmp reclaim read 932/932 worlds at "
    "326.59 MiB. The four follow-up sections ran in the designed order: the dry "
    "run read SECTION matrix FAIL (on-disk 55309B vs regenerated 55308B, no byte "
    "written) with fingerprint CLEAN domains=5, profile byte-identical and "
    "census DRIFT-CLEAN; suite_matrix.py regenerated the document from THIS "
    "round own evidence through --evidence plus --stamp-from (green=576/576), "
    "--check read byte-identical at 55308B / 576 / 4432, and the re-run read "
    "four PASS for VERDICT R2496 PASS (APPENDED 1950B eol_ok=True)."
)

DEBT = (
    "2026-11-06 R2496 debt settled through the shipped writers: "
    "reconcile-battery-R2496 closed at line 218 (open 2->1, done 197->198, "
    "131578B -> 131582B, readback ok) and product-face-R2496 was appended "
    "first=yes through debt_append (131582B -> 132144B, readback ok) naming the "
    "next product face state/queue/tech.md:531 prefix AC-EDQF1 "
    "export_driver_queue_face with the three gaps behind it (AC-CEPM1, AC-PLR1, "
    "AC-EUC1) still claimable. No successor battery is registered: this window "
    "changed one suite file and one document, not a registry module, so the "
    "registry stands unmoved at 576 suites / 4432 criteria."
)

HONEST = (
    "2026-11-06 R2496 honest disclosures: (a) this is an INTERNAL verification "
    "face - zero points on the Executive Protocol scale and nothing a CEO could "
    "open was built; (b) both red causes were shipped by earlier windows of "
    "mine and are named as mine rather than blamed on the runner - the "
    "clock-dependent determinism proof was written at R2494 and the "
    "un-regenerated document was left by the R2495 closeout, which adopted a "
    "green log without restamping the doc; (c) the first follow-up invocation "
    "was refused E_BFU_BAD_ARGS because I passed --round R2496 instead of an "
    "integer, and the shipped refusal was obeyed rather than the tool loosened; "
    "(d) this window ran far past its 25-minute budget (two full batteries plus "
    "the repairs) and that is disclosed rather than dressed up; (e) Docker is "
    "absent on this host so no containerised bring-up is claimed; (f) the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (g) tasks.md was not touched, it "
    "is the P-47 canonical board."
)

DECISION = (
    "2026-11-06 R2496 group transfer scan: decisions.md carried NO new token "
    "past the R2495 baseline (content-addressed diff new=0 over the 77-token "
    "set, 158 measured lines), and cph4/evolution-ledger.md carried no "
    "@BigDomain row at all. The group orders tail DID move and was read in full "
    "- OB rows at 2026-11-06 20:2x (token-optimisation toolbox bench), 20:5x "
    "(tooling inventory plus GitHub sourcing), 21:3x (17-item tool test board), "
    "21:4x (4.8GB dead-cache deletion plus a fleet broadcast id "
    "OB-20261106-2140-QA-TOOLKIT), 22:0x (DOC-DELIVERY-LAW v1 plus a real "
    "document bus over the NATS KV bucket FLEET_DOCS) and 22:5x (two delegated "
    "decisions: reversible deletion rights for the retention seat, and the "
    "four-tier LOCAL-COMPUTE-ALLOCATION routing law) - every one is a fleet, HQ "
    "or sibling-company ruling with no BigDomain execution face, so all six "
    "were ACKNOWLEDGED with no action and last_order was advanced to "
    "2026-11-06 22:5x."
)

LEDGER = (
    "R2496 tokens: local=~34k api=0 api_reason=verification window - one "
    "pre-registered battery re-measured by import before the run, one red leg "
    "kept as evidence with both causes reproduced alone, two birth-site repairs "
    "committed alone, one green retry at 576/576 with exactly 4432 criteria "
    "recounted independently, four follow-up sections PASS after the designed "
    "matrix FAIL, one debt row closed and the successor opened through their "
    "shipped writers, and the state/export/backlog/heartbeat closeout; zero "
    "cloud calls and zero external API touches"
)


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LEDGER:
        print("already appended")
        return
    state["log"].extend([SUMMARY, RED, RETRY, DEBT, HONEST, DECISION, LEDGER])
    state["tick"] = 2496
    state["last_order"] = "2026-11-06 22:5x"
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
    if len(back["log"]) != len(state["log"]) or back["tick"] != 2496:
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d tick=%s tokens=%d bytes=%d" % (
        len(back["log"]), back["tick"], len(back["last_dec_tokens"]),
        os.path.getsize(PATH)))


if __name__ == "__main__":
    main()