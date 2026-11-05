"""export_R2478 - refresh docs/status-export.json for the R2478 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2478 VERIFICATION window: the full reconcile battery ran on the "
           "committed tree and came back RED at 564/566 - one evidence-dialect "
           "drift and one 300s cap casualty - so the dialect defect was "
           "repaired at its birth site with a payload-identical proof "
           "(census now DRIFT-CLEAN, the red suite 8/8 alone) and the retry "
           "battery came back GREEN at 566/566 suites and exactly the 4372 "
           "pre-registered criteria; the cap casualty is measured, named and "
           "pre-registered, not silently waved through")

base.LATEST = ("qa/reconcile-all-R2478-leg2.log (RUNNER PASS 566/566 suites, "
               "controls 7/7, 4372 criteria exactly as pre-registered, "
               "1224.2s) + qa/reconcile-all-R2478.log (the red leg, kept) + "
               "src/os/repair_R2478.py (dialect repair, payload_equal=True on "
               "all three captures, atomic replace, byte read-back) + "
               "docs/sandbox-suite-matrix.md (54474B, self-describing "
               "green=566/566, --check byte-identical) + state/debt.md "
               "(reconcile-battery-R2477 closed, runner-suite-timeout-cap "
               "opened)")

base.NEXT = ("2026-11-06 the next window owes a BUSINESS face (CEO standing "
             "order OB-20261105-003656-879) and should name the supersession "
             "of the carried audit row product-face-R2456; the two named "
             "candidates are letting the hub page START a face from the "
             "browser (half of the R2475 candidate still undone) and the "
             "pre-registered AC-RSC1..AC-RSC6 timeout-cap work, which must "
             "land with its criteria because the deployed headroom fixture "
             "pins the 300s cap as a reading")

base.RESULT = (
    "2026-11-05 R2478 VERIFICATION window on the battery R2477 owed "
    "(reconcile-battery-R2477, pre-registered at 566 suites / 4372 criteria), "
    "because the R2168 mixed-tree rule puts the battery ahead of any further "
    "product byte. Five-silence scan at open was clean at HEAD 23179787 with "
    "an empty git status and no index.lock, zero @BigDomain ledger rows, the "
    "content-addressed decisions diff reading new=0 against the 142-token "
    "baseline, the group orders tail unchanged at 2026-11-05 20:22, "
    "benchmarks refreshed 2026-11-03 inside the seven-day gate. LEG 1 WAS RED "
    "at 564/566 in 1603.6s and both reds were real. (a) reconcile-daily-census "
    "named drift(exit=2) because the R2477 window wrote three of its own "
    "evidence captures outside the one UTF-8 LF single-writer law - "
    "start-all-live-R2477.log as ps-utf16 and both suite legs as utf-8-sig "
    "with CRLF. Repair landed at the birth site: each file decoded, the line "
    "set proved identical through run_identity.normalize (payload_equal=True "
    "on all three), rewritten UTF-8 LF with an atomic os.replace and a byte "
    "read-back (922B -> 447B, 103B -> 93B twice, crlf=0 bom=False), committed "
    "ALONE as b4e1ac93 before any retry, after which the census reads "
    "flags=0 DRIFT-CLEAN and the suite reads 8/8 alone. (b) "
    "ledger-apimarket-reportclaims exit=124 was the flat 300s per-suite cap, "
    "not an assertion: the same suite passes 8/8 alone in 198s, and the "
    "shipped headroom reader already reads three ledger suites in the band "
    "(232.2s / 268.1s / 300.1s against 300s), so this is the third casualty of "
    "the same cap. It is NOT fixed here, and saying why is the point: the "
    "deployed os-runner-suite-timeout-headroom fixture pins the 300s default "
    "as a reading, so a bare cap raise would make that instrument lie - "
    "instead a debt row runner-suite-timeout-cap was appended through its "
    "writer (123367B -> 124306B, readback ok) and a tech seed row was landed "
    "with AC-RSC1..AC-RSC6 pinned before any code. LEG 2 WAS GREEN on the "
    "repaired committed tree b4e1ac93: RUNNER PASS 566/566 suites, controls "
    "7/7, and the closing line reads exactly 4372 criteria, the pre-registered "
    "total, in 1224.2s, with TMP RECLAIM 932/932 and both legs kept as "
    "evidence. The four follow-up sections ran in the designed order: a "
    "designed matrix FAIL at 54461B against 54474B with no byte written, a "
    "stamp-aligned regeneration from this round own green evidence reading "
    "green=566/566, a byte-identical --check, then VERDICT R2478 PASS with "
    "fingerprint CLEAN, profile byte-identical and census DRIFT-CLEAN. Debt: "
    "reconcile-battery-R2477 closed through debt_close at its predicted "
    "123363B -> 123367B (line=203, open 3->2, done 181->182, readback ok) and "
    "no successor battery was registered because no product src byte moved. "
    "Honest: this is a ZERO product-point window - nothing a CEO could open "
    "was rebuilt; what it bought is a proved registry on the exact tree R2477 "
    "committed, a repair that is proven payload-identical rather than trusted, "
    "and a timeout defect that is named instead of excused by machine load; "
    "Docker is absent so a containerised bring-up stays unproved; the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items; "
    "tasks.md was not touched."
)

base.OUTS = (
    "qa/reconcile-all-R2478.log + qa/reconcile-all-R2478-leg2.log + "
    "src/os/repair_R2478.py + src/os/launch_battery_R2478.py + "
    "src/os/seed_queue_R2478.py + qa/start-all-R2477-leg1.log + "
    "qa/start-all-R2477-leg2.log + qa/start-all-live-R2477.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + state/queue/tech.md + "
    "src/os/state.json + src/os/state_append_R2478.py + "
    "src/os/export_R2478.py + docs/status-export.json + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())