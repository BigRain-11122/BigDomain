"""export_R2463 - refresh docs/status-export.json for the R2463 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2463 verification window: the battery the R2462 src edits owed ran "
           "on the committed tree - 559/559 suites green, controls 7/7, 4330 "
           "criteria exactly as pre-registered, 990.3s - so the entry page "
           "shipped at R2462 is now PROVED, not merely shipped. Same bring-up: "
           "python src/sandbox/lobby/server.py --city-http-port 8092 "
           "--web-port 8094 --hub-port 8095 then open "
           "http://127.0.0.1:8095/hub/")

base.LATEST = ("src/sandbox/lobby/hub.html (5393B self-contained entry page "
               "shipped R2462) plus LATE evidence qa/reconcile-all-R2463.log "
               "(858063B, one utf-8 LF single writer, crlf=0 bom=False) "
               "reading RUNNER PASS 559/559 suites, controls 7/7, criteria "
               "total=4330, TMP RECLAIM 932/932 removed")

base.NEXT = ("2026-11-05/06 a BUSINESS face superseding the carried internal "
             "audit row product-face-R2456 (carried 8 windows, stale) under the "
             "CEO standing order for real output - target: the shipped lobby "
             "gains a room picker and a readable event ledger so a visitor sees "
             "more than one room, ETA inside 48h; then the real msgSecCheck and "
             "the real 19.9 debit the moment the mini-program appid/secret and "
             "the merchant id land")

base.RESULT = (
    "2026-11-05 R2463 VERIFICATION window (zero product points, stated rather "
    "than dressed up): the R2168 mixed-tree rule owed the battery after R2462 "
    "changed product src bytes and moved the registry. RUNNER PASS 559/559 "
    "suites green, controls 7/7, 4330 criteria exactly as pre-registered, "
    "990.3s, TMP RECLAIM 932/932. The designed matrix FAIL-then-regenerate "
    "order held: FAIL at 53959B vs 53952B with no byte written, then a "
    "stamp-aligned regeneration from this round own green evidence and a "
    "byte-identical --check, then LEG 2 four sections PASS for VERDICT R2463 "
    "PASS. Evidence is a single utf-8 LF writer (crlf=0 bom=False). Honest "
    "limits: nothing a CEO can open was rebuilt this window, no P-47 business "
    "surface was touched, Docker is absent so the compose bring-up stays "
    "unproved, and the real debit plus the real msgSecCheck still wait on CEO "
    "physical items."
)

base.OUTS = (
    "qa/reconcile-all-R2463.log + docs/sandbox-suite-matrix.md + "
    "state/debt.md + src/os/backlog.md + src/os/closeout_R2463.py + "
    "src/os/export_R2463.py + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())