"""export_R2492 - refresh docs/status-export.json for the R2492 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2492 tech face: a declared package the read tree does not carry is "
           "now refused ONCE by name - E_RMPP_NO_PACKAGE naming the declaration "
           "and the corpus it searched - instead of being published as N broken "
           "imports")

base.LATEST = ("src/os/relative_package_presence_refusal.py + "
               "src/os/test_relative_package_presence_refusal.py (six "
               "pre-registered criteria, SUITE PASS 6/6 twice identical at "
               "qa/relative-package-presence-refusal-R2492.log, plus the live leg "
               "qa/relative-package-presence-refusal-live-R2492.log which reads "
               "NO-PACKAGE with zero rows for an absent declaration and still "
               "names a real missing import under a carried package) at "
               "2026-11-06 R2492")

base.NEXT = ("2026-11-07 the owed battery on the registry this window moved to "
             "575 suites / 4426 criteria, then a product face on the tech head "
             "state/queue/tech.md:528 prefix AC-MSFL1 (matrix_stamp_from_liveness, "
             "criteria pinned at R2442 before any code). Every P-47 item beyond "
             "the shipped sandbox faces still waits on CEO physical items "
             "(merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2492 TECH window on the carried product leader the register "
    "named after R2491 discharged its battery (product-face-R2491, tech head "
    "state/queue/tech.md:527 prefix AC-RMPP1, criteria AC-RMPP1..AC-RMPP6 pinned "
    "in that row at R2440 BEFORE any code). Claim: neither the corpus-scope face "
    "nor the existence face asked whether the DECLARED package is itself carried "
    "by the read tree, so --package nosuchpkg joined every relative import onto a "
    "package that does not exist and a declaration typo was published as N broken "
    "imports. Shipped src/os/relative_package_presence_refusal.py: the declared "
    "package now gets a presence decision on the parent's own root-wide corpus "
    "(ABSENT / MARKER / PRESENT with a carrier count); an ABSENT declaration "
    "refuses ONCE as E_RMPP_NO_PACKAGE naming the declaration and the corpus it "
    "searched with zero per-import rows; a carried declaration keeps the parent "
    "reading byte for byte (all 22 REPORT_KEYS compared equal); a package carried "
    "only by __init__.py reads MARKER rather than ABSENT; and the corpus is the "
    "R2440 walk asked once, the parent reading being handed that same measurement "
    "behind a root equality guard and restored in a finally block. Proof: "
    "AC-RMPP1..AC-RMPP6 SUITE PASS 6/6 TWICE identical plus three adjacent "
    "suites green (qa/relative-package-presence-refusal-R2492.log, legs=2 "
    "identical=True, fails=0). LIVE on one real tree: declared=nosuchpkg rc=2 "
    "verdict=NO-PACKAGE presence=ABSENT missing_rows=0, and declared=mypkg rc=2 "
    "verdict=MISSING-MODULE presence=PRESENT missing_modules=mypkg.nosuchmodule, "
    "so the refusal does not hide a real typo (qa/"
    "relative-package-presence-refusal-live-R2492.log, utf-8 LF). Registry "
    "574/4420 -> 575/4426 by exactly one row; matrix restamped stamp-aligned to "
    "55158B at 575/4426 with a byte-identical --check whose green line honestly "
    "reads 574/575; product-face-R2491 closed and product-face-R2492 opened "
    "first=yes through their shipped writers, so the next window owes the battery "
    "before any further product byte. Honest: an INTERNAL face, not a "
    "CEO-clickable one; my own first live leg was wrong twice and is disclosed; "
    "the one-walk substitution is a per-call module attribute restored in a "
    "finally block, a real limit for concurrent in-process callers; the real 19.9 "
    "debit and the real msgSecCheck still wait on CEO physical items; Docker is "
    "absent so no containerised bring-up is claimed; tasks.md was not touched."
)

base.OUTS = (
    "src/os/relative_package_presence_refusal.py + "
    "src/os/test_relative_package_presence_refusal.py + "
    "src/sandbox/reconcile_all.py + "
    "qa/relative-package-presence-refusal-R2492.log + "
    "qa/relative-package-presence-refusal-live-R2492.log + "
    "docs/sandbox-suite-matrix.md + state/queue/tech.md + state/debt.md + "
    "src/os/capture_R2492.py + src/os/live_R2492.py + src/os/wire_R2492.py + "
    "src/os/closeout_R2492.py + src/os/export_R2492.py + src/os/state.json + "
    "docs/status-export.json + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())