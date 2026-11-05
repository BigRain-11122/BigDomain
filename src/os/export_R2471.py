"""export_R2471 - refresh docs/status-export.json for the R2471 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2471 BUSINESS window: the one entry page now lists the P-47-2 token "
           "ledger console as a fourth face and tells the truth about every "
           "face - each card reads online/not-started from a TCP probe made "
           "during that request, so a dead link can no longer look alive")

base.LATEST = ("src/sandbox/lobby/hub.html (four face cards + live markers) + "
               "src/sandbox/lobby/hub_page.py (ledger face and face_ports, "
               "GET /hub/api/faces?probe=1 live map) + "
               "src/sandbox/lobby/test_hub_ledger_live.py (SUITE PASS 6/6 twice, "
               "identical verdict lines) + qa/hub-ledger-live-R2471.log (five "
               "faces 200, live all true, zero survivors)")

base.NEXT = ("2026-11-05/06 the next window runs the owed battery on this tree "
             "(reconcile-battery-R2471, pre-registered at 563 suites / 4354 "
             "criteria) and folds src/os/state.json, which now sits at 78449B "
             "against the 78500B waterline (margin 51B); the real msgSecCheck "
             "and the real 19.9 debit land the moment the mini-program "
             "appid/secret and the merchant id arrive, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2471 BUSINESS window on the CEO standing order "
    "OB-20261105-003656-879, superseding the carried internal audit row "
    "product-face-R2456 by name (it stays open and claimable). Five-silence "
    "scan at open was clean at HEAD 34c752af equal to origin/main with no "
    "index.lock, zero unreplied @BigDomain ledger rows, content-addressed "
    "decisions diff new=0, group orders tail unchanged at 2026-11-05 00:36, "
    "benchmarks refreshed 2026-11-03 inside the seven-day gate. Shipped the "
    "hub ledger face and a measured live map: build_faces keeps all fourteen "
    "old keys value-identical and adds ledger/ledger_note/ledger_cmd/face_ports "
    "(default 8097), /hub/api/faces?probe=1 answers a live map built by TCP "
    "connect at request time, hub.html gains the fourth card plus one live "
    "marker per face and still carries zero external references, and server.py "
    "advertises --ledger-port (default named in the help text) and passes it "
    "through. Evidence: src/sandbox/lobby/test_hub_ledger_live.py SUITE PASS "
    "6/6 TWICE with byte-identical verdict lines (qa/hub-ledger-R2471-a.log and "
    "-b.log), with the live map proved by opening and closing a real listener "
    "and two adjacent suites re-run green inside AC-HLL6. Live: "
    "qa/hub-ledger-live-R2471.log starts the whole stack and reads five faces "
    "at 200 with live all true, then zero survivors and a dead hub after stop. "
    "Matrix regenerated stamp-aligned to 54266B at 563 suites / 4354 criteria "
    "with --check byte-identical and green honestly 562/563; "
    "reconcile-battery-R2471 opened first=no at 121823B -> 122265B (readback "
    "ok), so the mixed-tree rule owes the battery first next window. Honest: "
    "the ledger console is still a separate process and one URL does not start "
    "four servers; Docker is absent; the real msgSecCheck and the real 19.9 "
    "debit still wait on CEO physical items; one printed substring check in the "
    "live driver proves nothing and is disclosed rather than cited; state.json "
    "sits 51B under the waterline so the next window must fold."
)

base.OUTS = (
    "src/sandbox/lobby/hub_page.py + src/sandbox/lobby/hub.html + "
    "src/sandbox/lobby/server.py + src/sandbox/lobby/test_hub_ledger_live.py + "
    "src/sandbox/reconcile_all.py + qa/hub-ledger-R2471-a.log + "
    "qa/hub-ledger-R2471-b.log + qa/hub-ledger-live-R2471.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/state_append_R2471.py "
    "+ src/os/export_R2471.py + src/os/state.json + src/os/backlog.md + "
    "heartbeat.txt + docs/status-export.json"
)

if __name__ == "__main__":
    print(base.main() if hasattr(base, "main") else "export_R2431 has no main()")