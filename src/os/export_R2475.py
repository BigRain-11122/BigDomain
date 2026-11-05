"""export_R2475 - refresh docs/status-export.json for the R2475 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2475 BUSINESS window: the sandbox entry page now reaches FIVE faces "
           "instead of four - the UGC console shipped at R2473 entered the hub "
           "payload, its card and a request-time live marker, and the operator "
           "flag --ugc-port - so one URL really reaches the newest console")

base.LATEST = ("qa/hub-ugc-R2475.log (SUITE PASS 6/6 twice, identical verdict "
               "digest b13a5112f83d66d7, 1018B, one utf-8 LF writer) + "
               "qa/hub-ugc-live-R2475.log (a REAL ugc_page.py on port 54398 "
               "published by the hub as http://127.0.0.1:54398/ugc/ with "
               "live_ugc=True and the shipped 8816B page answering 200) + "
               "src/sandbox/lobby/hub.html + docs/sandbox-suite-matrix.md "
               "(54396B, 565 suites / 4366 criteria, --check byte-identical)")

base.NEXT = ("2026-11-05/06 the next window owes the battery on this committed "
             "tree FIRST (reconcile-battery-R2475, pre-registered 565 suites / "
             "4366 criteria) because the R2168 mixed-tree rule puts it ahead of "
             "any further product byte; after green the product face is the "
             "next thing a person cannot yet do - the hub can say a face is "
             "alive but cannot start one; the real msgSecCheck and the real "
             "19.9 debit land the moment the mini-program appid/secret and the "
             "merchant id arrive, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2475 BUSINESS window on the CEO standing order "
    "OB-20261105-003656-879 (real output only); it SUPERSEDES the carried "
    "internal audit row product-face-R2456 by name, which stays open and "
    "claimable at state/queue/tech.md:522 prefix AC-PFKC1. Five-silence scan at "
    "open was clean at HEAD 800120a4 with an empty git status and no "
    "index.lock, zero unreplied @BigDomain ledger rows, the content-addressed "
    "decisions diff new=0 against its 136-token baseline, the group orders tail "
    "unchanged at 2026-11-05 00:36, benchmarks refreshed 2026-11-03 inside the "
    "seven-day gate, and the tech head read AC-PFKC1 with claimable=11 so no "
    "idle declaration was available. SHIPPED the fifth face into the one door: "
    "hub_page gains UGC_CMD/UGC_NOTE plus ugc_port (default 8098) in "
    "build_faces and in face_ports, hub.html gains the UGC card id=link-ugc "
    "with its data-face=ugc live marker (five markers, zero external "
    "references), server.py advertises --ugc-port and passes ugc_port through, "
    "and test_hub_ugc.py wires AC-HUG1..AC-HUG6 into the registry as "
    "lobby-hub-ugc(6). PROOF: criteria pinned in src/os/backlog.md BEFORE the "
    "code, SUITE PASS 6/6 twice with identical verdict bodies (digest "
    "b13a5112f83d66d7) in qa/hub-ugc-R2475.log, and a LIVE leg against a real "
    "UGC console in qa/hub-ugc-live-R2475.log. ONE real defect found and "
    "repaired at its birth site: test_hub_ledger_live.py asserted face_ports as "
    "an exact dict where its own AC-HLL1 is an additive contract, so the "
    "neighbour refused the new key; the assertion now reads the five keys it "
    "owns as a subset with the criterion text unchanged and no other assertion "
    "loosened. Registry 565 suites / 4366 criteria; matrix restamped "
    "stamp-aligned to 54396B with --check byte-identical, its green line "
    "honestly 564/565 because this window ran no battery. Debt: "
    "reconcile-battery-R2475 appended first=no at its predicted 122769B -> "
    "123176B (readback ok) with the pre-registered 565/4366 target. Honest "
    "gaps: no battery ran; every P-47 item beyond the shipped sandbox faces "
    "remains blocked on CEO physical items (merchant id, mini-program "
    "appid/secret); Docker is absent on this host; the hub still cannot start a "
    "face, it can only report whether one is listening."
)

base.OUTS = (
    "src/sandbox/lobby/hub_page.py + src/sandbox/lobby/hub.html + "
    "src/sandbox/lobby/server.py + src/sandbox/lobby/test_hub_ugc.py + "
    "src/sandbox/lobby/test_hub_ledger_live.py + src/sandbox/reconcile_all.py + "
    "qa/hub-ugc-R2475.log + qa/hub-ugc-live-R2475.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/export_R2475.py + "
    "src/os/state.json + src/os/backlog.md + docs/status-export.json"
)

if __name__ == "__main__":
    print(base.main())