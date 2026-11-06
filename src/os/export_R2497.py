"""export_R2497 - refresh docs/status-export.json for the R2497 product window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies
this round's CEO lines and its outs row.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2497 product window: the round export driver now asks the shipped "
           "queue face for its section and proves the block with the freshness "
           "gate before any replace, so a refreshed CEO document can no longer "
           "carry a stale queue block or need a hand-landed fix")

base.LATEST = ("qa/export-driver-queue-face-R2497.log (2657B, utf-8 LF, crlf=0, "
               "legs=2 identical=True, adjacent=5 fails=0) at 2026-11-06, plus "
               "src/os/export_driver_queue_face.py and "
               "src/os/test_export_driver_queue_face.py")

base.NEXT = ("2026-11-07 a TECH face on the tech head state/queue/tech.md "
             "prefix AC-ECQF1 (export_consistency_queue_face) - the 21-check "
             "consistency face cannot see a stale queue block and must read "
             "DRIFT instead of PASS - with AC-CEPM1, AC-PLR1 and AC-EUC1 "
             "claimable behind it. Every P-47 item beyond the shipped sandbox "
             "faces still waits on CEO physical items (merchant id, "
             "mini-program appid/secret)")

base.NEXT_DUE = "2026-11-07T23:00:00+08:00"

base.RESULT = (
    "2026-11-06 R2497 PRODUCT window on the tech head the register named "
    "(product-face-R2496, state/queue/tech.md:531 prefix AC-EDQF1 "
    "export_driver_queue_face, criteria AC-EDQF1..AC-EDQF6 pinned in that row "
    "at R2453 BEFORE any code). CLAIM: export_R2431.main re-derived the "
    "CEO-visible queue block itself out of queue_floor --check --json while the "
    "published section the house reads is queue_floor_export_face.face - the "
    "DISCOUNTED reading with delivered_total - so two derivations of one "
    "document existed, and MEASURED TWICE (R2452, R2453) both windows refreshed "
    "the export and then read queue_floor_export_face --check STALE "
    "(claimable=5,10,10) and had to land the block by hand. SHIPPED "
    "src/os/export_driver_queue_face.py plus its six-criteria suite: the "
    "section is QFE.face asked as an attribute at CALL time (patching that "
    "reading moves the section), the gross reading path was DELETED from the "
    "driver rather than left unused, the section is refreshed IN PLACE so every "
    "already-published key keeps its value and position, and publish() stages "
    "the composed bytes beside the export and proves them through "
    "queue_export_freshness_gate.check BEFORE any replace - so a queue that "
    "moved between the reading and the write refuses with the gate own verdict "
    "word (STALE) and leaves the document byte-identical with no residue, while "
    "the gate verdict and byte count reach the driver output instead of a "
    "silent write. PROOF: AC-EDQF1..AC-EDQF6 SUITE PASS 6/6 TWICE with identical "
    "verdicts plus five adjacent suites green "
    "(qa/export-driver-queue-face-R2497.log, 2657B, utf-8, bom=False, crlf=0, "
    "lone_cr=0). MEASURED on the real tree: the driver run reads queue=CURRENT "
    "with queue_drifted=(none), the queue face itself re-reads CURRENT and the "
    "gate reports no drift. REGISTRY: one runner row "
    "os-export-driver-queue-face(6), so 576 suites / 4432 criteria becomes 577 "
    "/ 4438 (recounted by importing reconcile_all.SUITES, not quoted). DEBT: "
    "the row was closed through a per-round stamp writer (predicted 1635465B -> "
    "1638291B, measured exactly, readback ok) and ONE real measured gap was "
    "seeded as AC-ECQF1: a copy of the real export whose queue block was "
    "doctored (verdict FLOOR-DEBT, tech claimable 0) still reads pass=21 fail=0 "
    "on check_export_consistency while the gate reads STALE, so the face every "
    "window trusts cannot see a stale queue block at all. No successor battery "
    "is owed by this closeout alone, but this window moved a shipped module "
    "(export_R2431.py) and the registry, so the next window owes the battery at "
    "the measured 577 / 4438. Honest: two product points for a real driver fix; "
    "no CEO-visible business surface changed, and the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items (merchant id, "
    "mini-program appid/secret); Docker absent on this host; tasks.md untouched."
)

base.OUTS = (
    "qa/export-driver-queue-face-R2497.log + src/os/export_driver_queue_face.py "
    "+ src/os/test_export_driver_queue_face.py + src/os/export_R2431.py + "
    "src/os/stamp_queue_R2497.py + src/sandbox/reconcile_all.py + "
    "state/queue/tech.md + src/os/state.json + docs/status-export.json + "
    "src/os/backlog.md + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())