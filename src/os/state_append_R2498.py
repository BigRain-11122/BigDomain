"""state_append_R2498 - append this window's log items and bump the tick."""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"

SUMMARY = (
    "2026-11-07 R2498 PRODUCT window on the tech head the register named "
    "(product-face-R2496, state/queue/tech.md:533 prefix AC-ECQF1 "
    "export_consistency_queue_face, criteria AC-ECQF1..AC-ECQF6 pinned in that "
    "row at R2497 BEFORE any code). Five-silence scan at open: git status empty, "
    "no @BigDomain ledger row, benchmarks 2026-11-03 inside the seven-day gate, "
    "tech head claimable and the debt gate read CLAIM-FIRST item=product-face-"
    "R2496 first=1 (no battery owed). The group decisions diff read six new "
    "tokens (D-20261107-01..06), all HQ-level rulings about the 11-06 executor "
    "pause, the fleet roster and the feedback-surface sweep, with no BigDomain "
    "execution face; they were acknowledged with no action and the baseline was "
    "advanced to them. CLAIM: check_export_consistency is the twenty-one-check "
    "face every window trusts and it never opens the export queue block, so a "
    "document edited after the driver published it still reads pass=21 fail=0."
)

SHIPPED = (
    "2026-11-07 R2498 SHIPPED src/os/export_consistency_queue_face.py plus "
    "src/os/test_export_consistency_queue_face.py and one registry row "
    "os-export-consistency-queue-face(6). read() asks check_export_consistency."
    "check at CALL time for the twenty-one base checks and "
    "queue_export_freshness_gate.check at CALL time for the queue verdict, then "
    "publishes the gate verdict BESIDE the base lines instead of inside them: a "
    "stale or missing block reads DRIFT naming every drifted section field and "
    "queue, a CURRENT block reads AGREE at today exit code with exactly one "
    "additional line, and the CLI emits LF-only bytes through the stdout buffer "
    "so evidence files cannot inherit CRLF from text-mode translation."
)

PROOF = (
    "2026-11-07 R2498 PROOF measured, not quoted: AC-ECQF1..AC-ECQF6 SUITE PASS "
    "6/6 TWICE with identical criterion lines plus three adjacent suites green "
    "(qa/export-consistency-queue-face-R2498.log, captured through the shipped "
    "evidence ritual which refuses a red or drifting leg). The suite proves the "
    "call-time asks by patching both shipped readings and watching the composed "
    "result move, proves the base twenty-one lines are byte-identical with their "
    "order and count preserved, and proves a doctored document reads DRIFT with "
    "queue:tech plus section names while the base twenty-one stay green. A LIVE "
    "catch was measured on the real tree at open: the shipped export carried a "
    "stale queue block (drifted=section:verdict,section:shortfall_total,"
    "section:delivered_total,queue:tech) while the twenty-one checks read 21/21 "
    "PASS, which is the exact blind spot this face names. REGISTRY 577/4438 -> "
    "578/4444, recounted by importing reconcile_all.SUITES rather than quoted."
)

QUEUE = (
    "2026-11-07 R2498 BOARD: the claimed row state/queue/tech.md:533 was closed "
    "with its DISCHARGED note through one in-place rewrite with readback, and "
    "the four carried seed rows beneath it (AC-CEPM1, AC-RSC1, AC-PLR1, AC-EUC1) "
    "stay claimable, so the floor re-read FLOOR-MET. No new seed row was added "
    "this window: the live catch above is already the row that was shipped, and "
    "inventing a sixth face to fill a quota would be the fourth form of idling."
)

HONEST = (
    "2026-11-07 R2498 honest disclosures: (a) this is an INTERNAL verification "
    "face; a real shipped reading changed behaviour, but nothing a CEO opens is "
    "new; (b) the live catch was found at open, before the face existed, so it "
    "is evidence for the seed and not a claim that the new face produced it; "
    "(c) Docker is absent on this host so no containerised bring-up is claimed; "
    "(d) the real 19.9 debit and the real msgSecCheck still wait on CEO physical "
    "items (merchant id, mini-program appid/secret); (e) tasks.md was not "
    "touched, it is the P-47 canonical board; (f) state.json measured 37989B at "
    "open, far under the 78500B waterline, so no fold was due."
)

DECISION = (
    "2026-11-07 R2498 group scan: the content-addressed decisions diff read six "
    "new tokens over the baseline (D-20261107-01 executor pause and clock-anchor "
    "correction, D-02 production-backlog stock law, D-03 machine roster build, "
    "D-04 cherry-pick whitelist order, D-05 feedback-surface sweep, D-06 no "
    "external research this round). Each is an HQ ruling whose subject is the "
    "fleet, the roster or the research policy; none names BigDomain or assigns "
    "an execution face, so all six are ACKNOWLEDGED with no action and the "
    "baseline advanced to them. cph4/evolution-ledger.md carried zero "
    "@BigDomain rows. The group orders tail moved to 2026-11-07 00:59 and is "
    "read at closeout."
)

LEDGER = (
    "R2498 tokens: local=~26k api=0 api_reason=product window - one "
    "pre-registered face shipped with its six criteria, one suite proved twice "
    "with three adjacent suites green under the shipped evidence ritual, one "
    "registry row recounted by import, one live blind spot measured on the real "
    "tree, one queue row closed, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches"
)

SELF_HEAL = (
    "2026-11-07 R2498 self-heal check: the BigDomain-OSLoop definition still "
    "reads Interactive LogonType, which the 2026-09-29 machine law forbids for "
    "every lane task, and src/os/register_loop_task.ps1 needs an elevated shell "
    "while this session is unelevated, so it was left untouched again and is "
    "carried as loop-s4u-reconcile."
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
    state["tick"] = 2498
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
    if len(back["log"]) != len(state["log"]) or back["tick"] != 2498:
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d tick=%s tokens=%d bytes=%d" % (
        len(back["log"]), back["tick"], len(back["last_dec_tokens"]),
        os.path.getsize(PATH)))


if __name__ == "__main__":
    main()