"""export_R2465 - refresh docs/status-export.json for the R2465 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2465 verification window: the full reconcile battery ran twice on "
           "the committed tree and both legs are red for two different, named, "
           "repaired causes - a residue round the register never declared "
           "(R2452, now declared and re-proved green) and a load-sensitive "
           "transport race in the checkout-demo suite (now retried at the "
           "birth site and proved green twice standalone). No product byte was "
           "rebuilt and nothing a CEO can open changed this window")

base.LATEST = ("state/residue_triage.json (282 declarations, R2452 appended "
               "through residue_triage_append and re-proved by AC-RTR6) + "
               "src/sandbox/lobby/test_checkout_demo.py (transport retry in the "
               "http helper, criteria untouched) + qa/reconcile-all-R2465.log "
               "(both legs, red, kept verbatim) + repair commit 9f0e5a57")

base.NEXT = ("2026-11-05/06 the green battery this window owes runs FIRST on "
             "the committed tree at the unchanged pre-registered 560 suites / "
             "4336 criteria, closing reconcile-battery-R2465; then the real "
             "msgSecCheck and the real 19.9 debit the moment the mini-program "
             "appid/secret and the merchant id land, ETA inside 48h")

base.RESULT = (
    "2026-11-05 R2465 VERIFICATION window, and it reports red evidence as red. "
    "Leg 1 read 559/560 suites green with one failing suite (os-residue-triage "
    "AC-RTR6, untriaged=1); the live-vs-declared set difference named exactly "
    "R2452, whose residue row is DELIVERED with hits=1 closed=1, so the gap was "
    "a missing declaration. It was appended through the shipped writer (dry run "
    "first, 281->282 entries, readback TRIAGED) and the suite re-ran SUITE PASS "
    "6/6. Leg 2 then failed a DIFFERENT single suite: os-lobby-checkout-demo "
    "died on its first request with WinError 10053, while standalone it reads "
    "6/6 twice with the unchanged digest 46654133EC75D89438D1B6C4547C79CE, so "
    "the suite http helper now retries transport failures only and prints every "
    "retry, with no status, byte or count assertion relaxed. Honest limits: "
    "reconcile-battery-R2465 stays OPEN because no green full battery exists "
    "yet; zero product points; the matrix was not regenerated from a red leg; "
    "Docker is absent and the real debit plus the real msgSecCheck still wait on "
    "CEO physical items."
)

base.OUTS = (
    "state/residue_triage.json + "
    "src/sandbox/lobby/test_checkout_demo.py + "
    "qa/reconcile-all-R2465.log + "
    "src/os/closeout_R2465.py + src/os/export_R2465.py + "
    "src/os/backlog.md + docs/status-export.json + src/os/state.json + "
    "heartbeat.txt"
)

if __name__ == "__main__":
    sys.exit(base.main())