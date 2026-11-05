"""export_R2467 - refresh docs/status-export.json for the R2467 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2467 business window: the content gate finally becomes something a "
           "person can use - open the console, type a sentence, read the verdict "
           "the shipped msgSecCheck stub really returned (SERVE / REVIEW / "
           "REFUSE) together with its trace id and the endpoint contract the "
           "real WeChat gate must satisfy")

base.LATEST = ("src/sandbox/lobby/gate.html + src/sandbox/lobby/gate_page.py "
               "(openable console over the shipped stub) + "
               "qa/content-gate-console-R2467.log (SUITE PASS 6/6 twice, "
               "identical digest) + qa/content-gate-console-live-R2467.log "
               "(real process, bound port in the banner)")

base.NEXT = ("2026-11-05/06 the next window runs the battery R2467 owes at the "
             "pre-registered 561 suites / 4342 criteria, and the real "
             "msgSecCheck plus the real 19.9 debit the moment the mini-program "
             "appid/secret and the merchant id land, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2467 BUSINESS window on the CEO standing order "
    "OB-20261105-003656-879, taken over the carried audit row "
    "product-face-R2456 (carried, never dropped). The five-silence scan found a "
    "dirty tree and that was the first finding: R2466 had finished its work but "
    "never committed it, so the closeout was measured consistent (21/21, tick "
    "2466) and committed as 96f24160 before anything else. Product: the content "
    "gate is now a console - GET /gate and /gate/ serve the page from disk, "
    "GET /gate/api/contract publishes the endpoint the real WeChat msgSecCheck "
    "v2 must satisfy, and POST /gate/api/check runs the SHIPPED stub over the "
    "submitted text and returns its own response plus one derived "
    "http_decision taken from the stub own is_risky / needs_review, so the "
    "mapping has one owner and no second wordlist exists. AC-GC1..AC-GC6 were "
    "pre-registered before the code and read SUITE PASS 6/6 twice with an "
    "identical digest off a real server, plus one live bring-up whose banner "
    "publishes the bound gate port. Registry 561 suites / 4342 criteria, "
    "matrix regenerated stamp-aligned to 54146B with --check byte-identical, "
    "reconcile-battery-R2467 owed next. Honest: Docker is absent, and the real "
    "msgSecCheck plus the real 19.9 debit still wait on CEO physical items."
)

base.OUTS = (
    "src/sandbox/lobby/gate.html + src/sandbox/lobby/gate_page.py + "
    "src/sandbox/lobby/test_gate_console.py + src/sandbox/lobby/server.py + "
    "src/sandbox/lobby/hub_page.py + src/sandbox/reconcile_all.py + "
    "qa/content-gate-console-R2467.log + "
    "qa/content-gate-console-live-R2467.log + "
    "docs/sandbox-suite-matrix.md + state/debt.md + "
    "src/os/closeout_R2467.py + src/os/export_R2467.py + "
    "src/os/live_R2467.py + src/os/backlog.md + "
    "docs/status-export.json + src/os/state.json + heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())