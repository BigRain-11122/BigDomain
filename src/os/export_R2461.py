"""export_R2461 - refresh docs/status-export.json for the R2461 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2461 verification window: the sandbox faces shipped over the last "
           "two windows are now PROVED rather than merely shipped. Bring-up is "
           "unchanged - `python src/sandbox/lobby/server.py --city-http-port "
           "8092 --web-port 8094` - then open http://127.0.0.1:8094/lobby/ "
           "for the chat, http://127.0.0.1:8092/city/ for the city, and the "
           "checkout page served by checkout_demo.py for the 19.9 mock")

base.LATEST = ("docs/sandbox-suite-matrix.md regenerated from this round own "
               "battery evidence (53887B, 558 suites / 4324 criteria, "
               "--check byte-identical) + qa/reconcile-all-R2461.log (861329B, "
               "one utf-8 LF single writer, RUNNER PASS 558/558 suites, "
               "reconcile controls 7/7, 1002.1s, TMP RECLAIM 932/932) + both "
               "outstanding battery debt rows closed through their shipped CLI")

base.NEXT = ("2026-11-05/07 the next window takes the gate leader "
             "product-face-R2456 or a P-47 business face under the CEO standing "
             "order; then a sandbox hub page linking the city, lobby and "
             "checkout faces from one URL, and the real msgSecCheck plus the "
             "real 19.9 debit the moment the mini-program appid/secret and the "
             "merchant id land, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2461 VERIFICATION window on the debt two product windows "
    "left behind: the R2459 checkout face and the R2460 lobby page both "
    "changed product src bytes and neither side had been verified by the whole "
    "registry, so the R2168 mixed-tree rule owed the battery first. It ran on "
    "the committed tree 2a9fed3f with an empty git status and read RUNNER PASS "
    "558/558 suites green plus reconcile controls 7/7 in 1002.1s at criteria "
    "total 4324 EXACTLY as pre-registered, with birth-site TMP RECLAIM 932/932 "
    "and evidence written by one utf-8 LF single writer. The four follow-up "
    "sections produced the designed order - matrix FAIL at 53731B against "
    "53887B without rewriting anything, then a stamp-aligned regeneration from "
    "this round own green evidence, --check byte-identical, and all four "
    "sections PASS for VERDICT R2461 PASS. The regeneration also un-stales the "
    "suite matrix that R2460 had to disclose as stale, and its own green line "
    "now reads 558/558 because it names this round battery. Both battery debt "
    "rows were closed through their shipped writer (open 4->2, done 172->174, "
    "readback ok); no successor battery is owed because no product src byte "
    "changed and the registry is unmoved. The closeout crossed the state "
    "waterline, so the R2450 block was folded at a true round-block boundary "
    "(12 lines, 232 tokens, predicted=actual 73836B) and the fold-created "
    "residue round R2450 was spliced through the shipped batch channel at its "
    "MEASURED DELIVERED status (281/281 TRIAGED), with the badge exemption "
    "reading NO-DRIFT over 383 entries. Honest limits: zero product points - "
    "nothing a CEO could open was rebuilt this window, the value is that the "
    "shipped sandbox faces are now proved; Docker is still absent so the "
    "compose bring-up stays unproved; the real debit and the real msgSecCheck "
    "still wait on CEO physical items (merchant id, mini-program "
    "appid/secret)."
)

base.OUTS = (
    "qa/reconcile-all-R2461.log + docs/sandbox-suite-matrix.md + "
    "state/debt.md + state/residue_triage.json + src/os/backlog.md + "
    "src/os/closeout_R2461.py + src/os/fold_R2461.py + "
    "src/os/export_R2461.py + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())