"""export_R2459 - refresh docs/status-export.json for the R2459 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2459 business window: the 19.9 entrance checkout that until today "
           "only existed as a terminal proof is now a page a person can click "
           "through - open http://127.0.0.1:8093/checkout/, place the mock 19.9 "
           "order, pay it, watch the month card activate, then try a sentence "
           "and see the entrance gate refuse an unpaid actor before the content "
           "gate is ever asked")

base.LATEST = ("src/sandbox/lobby/checkout.html (8051B self-contained page, "
               "zero external references, MOCK non-chargeable + AI generated "
               "label + non-advice note on screen) + "
               "src/sandbox/lobby/checkout_demo.py (GET /checkout/, GET "
               "/checkout/api/state, POST order/pay/send over the shipped "
               "pay_mock and msgsec_stub) + "
               "src/sandbox/lobby/test_checkout_demo.py SUITE PASS 6/6 twice "
               "with an identical digest (qa/checkout-demo-R2459.log, "
               "46654133EC75D89438D1B6C4547C79CE) + a live CLI process proving "
               "page bytes=8051 and a real live order at 1990 cents "
               "mock=chargeable=false")

base.NEXT = ("2026-11-05/06 the battery the R2459 src edits owe runs FIRST next "
             "window on the committed tree at the pre-registered 557 suites / "
             "4318 criteria (reconcile-battery-R2460), then the browser surface "
             "gets its next business step: the same checkout page driven by the "
             "real msgSecCheck contract the moment the mini-program appid/secret "
             "lands, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2459 BUSINESS window, SUPERSEDING the carried internal audit "
    "face product-face-R2456 (still open and claimable in the tech queue at "
    "state/queue/tech.md:522 prefix AC-PFKC1) under the CEO standing order "
    "OB-20261105-003656-879: real output only, no new mechanism, rule or "
    "document. The lobby already shipped pay_mock.py and msgsec_stub.py but "
    "nothing a human could operate, so this window shipped the operator: "
    "checkout_demo.py serves GET /checkout (and /checkout/) byte-identical from "
    "checkout.html plus four same-origin routes - state, order, pay, send - "
    "with the entrance gate ordered BEFORE the content gate, so an unpaid actor "
    "is refused E_ENTRANCE_REQUIRED at 403 with the gate call counter provably "
    "unmoved. Six pre-registered criteria read off a real server on port 0, "
    "twice with an identical digest: page 8051B identical to disk with zero "
    "external references and all three standing notices; order pinned to 1990 "
    "cents mock/chargeable=false with a blank actor refused at 400 creating no "
    "order; pay replayed returns the SAME receipt_no with replay=true and the "
    "month card reads active; risky/review/plain read 422/422/200 from the "
    "shipped stub with trace_id and ai_generated=false; an unknown order reads "
    "404 with orders, receipts and entitlements byte-identical and unlisted "
    "paths 404 while non-GET reads 405; the module is pure ASCII stdlib with "
    "zero clock and the registry moved exactly one row. Two REAL birth defects "
    "of my own were caught by RUNNING and repaired at their birth site without "
    "widening a criterion: demo.state asked a module-level contract() as if it "
    "were a PayMock method (fixed by importing it), and AC-CKD6 caught an "
    "'import time' inside main() - the MODULE changed to a threading.Event "
    "wait rather than the criterion being loosened. Live proof: a real CLI "
    "process on port 8093 served the page at 8051B and accepted a real order at "
    "1990 cents, mock=true chargeable=false, then was terminated. Debt: "
    "reconcile-battery-R2460 appended first=no at 119468B -> 119792B "
    "(readback ok) because product src changed and the registry moved 556->557 "
    "suites / 4312->4318 criteria; the gate still reads first=product-face-R2456 "
    "(carried=4, stale). Honest limits: Docker is absent on this host so the "
    "containerised bring-up stays unproved; the real 19.9 debit and the real "
    "msgSecCheck both wait on CEO physical items (merchant id, mini-program "
    "appid/secret) and the page says so on screen; the first live probe hung "
    "on a buffered pipe and its survivor was cleared before any commit."
)

base.OUTS = (
    "src/sandbox/lobby/checkout_demo.py + src/sandbox/lobby/checkout.html + "
    "src/sandbox/lobby/test_checkout_demo.py + qa/checkout-demo-R2459.log + "
    "src/sandbox/reconcile_all.py (one registry row) + state/debt.md + "
    "src/os/backlog.md + src/os/export_R2459.py + docs/status-export.json + "
    "src/os/state.json + heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())