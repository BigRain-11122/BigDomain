"""export_R2462 - refresh docs/status-export.json for the R2462 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2462 business window: the sandbox now has ONE door. Run `python "
           "src/sandbox/lobby/server.py --city-http-port 8092 --web-port 8094 "
           "--hub-port 8095` and open http://127.0.0.1:8095/hub/ - one page "
           "lists the lobby chat, the silicon city and the 19.9 mock checkout, "
           "and it fills each link from the ports the server really bound")

base.LATEST = ("src/sandbox/lobby/hub.html (5393B self-contained entry page, "
               "zero external references, AI generated label + non-advice note "
               "+ mock/no-real-charge statement + read-only statement) + "
               "src/sandbox/lobby/hub_page.py (GET /hub/, GET /hub, GET "
               "/hub/api/faces publishing the REAL bound ports; read-only "
               "HTTP) + --hub-port/--checkout-port on src/sandbox/lobby/"
               "server.py + src/sandbox/lobby/test_hub_page.py SUITE PASS 6/6 "
               "twice with an identical digest (qa/sandbox-hub-R2462.log)")

base.NEXT = ("2026-11-05/07 the battery the R2462 src edits owe runs FIRST next "
             "window on the committed tree at the pre-registered 559 suites / "
             "4330 criteria (reconcile-battery-R2463); then the real "
             "msgSecCheck and the real 19.9 debit the moment the mini-program "
             "appid/secret and the merchant id land, and a room picker over the "
             "shipped lobby rooms, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2462 BUSINESS window on the entry face the R2461 export "
    "already named as the next milestone, under the CEO standing order "
    "OB-20261105-003656-879 (real output only): the sandbox had four openable "
    "faces and no door. Shipped hub.html plus hub_page.py plus --hub-port and "
    "--checkout-port on server.py, so one URL lists the three faces and every "
    "link is filled from the ports the server really bound rather than a "
    "hardcoded guess. Six criteria were pre-registered in the backlog BEFORE "
    "the code and read off a REAL server on OS-assigned ports, twice with an "
    "identical digest, with three adjacent suites green and the checkout "
    "digest unchanged; the registry moved exactly one row to 559 suites / 4330 "
    "criteria and the matrix was regenerated stamp-aligned with a "
    "byte-identical check. Honest limits: the checkout URL is a published port "
    "with a note naming the process to start, not a liveness claim; Docker is "
    "absent so the compose bring-up stays unproved; the real debit and the real "
    "msgSecCheck still wait on CEO physical items; the battery this window "
    "owes is registered as reconcile-battery-R2463."
)

base.OUTS = (
    "src/sandbox/lobby/hub.html + src/sandbox/lobby/hub_page.py + "
    "src/sandbox/lobby/test_hub_page.py + src/sandbox/lobby/server.py "
    "(--hub-port, --checkout-port) + qa/sandbox-hub-R2462.log + "
    "src/sandbox/reconcile_all.py (one registry row) + "
    "docs/sandbox-suite-matrix.md + state/debt.md + src/os/backlog.md + "
    "src/os/closeout_R2462.py + src/os/fold_R2462.py + "
    "src/os/export_R2462.py + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())