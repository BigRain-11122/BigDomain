"""export_R2466 - refresh docs/status-export.json for the R2466 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2466 verification window: the battery the R2464 edits owed finally "
           "ran green - 560/560 suites, 4336 criteria exactly as pre-registered "
           "- after two real birth-site repairs, a stale export re-derived "
           "through its shipped drivers and a runner that now survives a suite "
           "hitting the 300s cap instead of aborting the whole run")

base.LATEST = ("qa/reconcile-all-R2466-retry2.log (RUNNER PASS 560/560, "
               "controls 7/7, 1143.3s, one utf-8 LF single writer) + "
               "docs/sandbox-suite-matrix.md (regenerated stamp-aligned, "
               "byte-identical check) + repair commits dc3a6f05 and f7728805")

base.NEXT = ("2026-11-05/06 the next window resumes the PRODUCT face at tech "
             "head state/queue/tech.md:522 AC-PFKC1 (product-face-R2456), and "
             "the real msgSecCheck plus the real 19.9 debit the moment the "
             "mini-program appid/secret and the merchant id land, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2466 VERIFICATION window on the battery R2464 owed and R2465 "
    "could not discharge. Leg 1 was RED with self_drive stored=90 against 91 "
    "live lines because R2465 appended its self-heal line after its last export "
    "refresh (the R2433/R2441 closeout-ordering shape); the export was "
    "re-derived through export_R2465 then queue_export_gate_wire --execute "
    "(consistency 21/21 PASS) and both red suites read 6/6. Leg 2 ABORTED on "
    "subprocess.TimeoutExpired at the 300s per-suite cap on "
    "ledger-apimarket-refundregister, whose own measured leg is 268.1s, so "
    "run_cmd now records one failed suite with a TIMEOUT marker at exit 124 "
    "instead of killing the battery. Leg 3 on the committed repair tree read "
    "RUNNER PASS 560/560 with criteria total 4336 exactly as pre-registered, "
    "four follow-up sections PASS after the designed matrix FAIL and its "
    "stamp-aligned regeneration, reconcile-battery-R2465 closed through "
    "debt_close (open 3->2, done 175->176), the fold that R2465 deferred run at "
    "a true round-block boundary (87861B -> 60618B, FOLD-CLEAR) and its one "
    "fold-created residue round R2454 declared through the shipped writer "
    "(282->283 entries, TRIAGED). Honest: zero product points, nothing a CEO "
    "can open was rebuilt, and the real debit plus the real msgSecCheck still "
    "wait on CEO physical items."
)

base.OUTS = (
    "docs/sandbox-suite-matrix.md + qa/reconcile-all-R2466-retry2.log + "
    "src/sandbox/reconcile_all.py + state/residue_triage.json + "
    "src/os/closeout_R2466.py + src/os/export_R2466.py + "
    "src/os/backlog.md + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())