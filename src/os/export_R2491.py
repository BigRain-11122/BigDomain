"""export_R2491 - refresh docs/status-export.json for the R2491 window.

The derivation, atomic write and read-back self-check live in the shipped
export_R2431 module; this driver only supplies this round's CEO lines and its
outs row, so no second derivation exists.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.DO = ("R2491 tech face: an absence in the relative-import reading now says "
           "WHERE it looked - every MISSING-MODULE row carries the root as given "
           "and the corpus size it was judged against, and an operator may "
           "declare extra module names that merge on top of the measured tree")

base.LATEST = ("src/os/relative_module_corpus_scope.py + "
               "src/os/test_relative_module_corpus_scope.py (six pre-registered "
               "criteria, SUITE PASS 6/6 twice identical at "
               "qa/relative-module-corpus-scope-R2491.log 1413B, plus the live leg "
               "qa/relative-module-corpus-scope-live-R2491.log 1666B which "
               "reproduces the seed defect on a real tree and clears it two ways) "
               "at 2026-11-06 R2491")

base.NEXT = ("2026-11-07 a PRODUCT face on the tech head the register now names: "
             "state/queue/tech.md:527 prefix AC-RMPP1 "
             "(relative_package_presence_refusal, criteria pinned at R2440 before "
             "any code) - a declared package the tree does not carry must refuse "
             "once instead of printing N broken imports. Every P-47 item beyond "
             "the shipped sandbox faces still waits on CEO physical items "
             "(merchant id, mini-program appid/secret)")

base.RESULT = (
    "2026-11-06 R2491 TECH window on the carried product leader the register "
    "named after R2490 discharged its battery (product-face-R2490, tech head "
    "state/queue/tech.md:525 prefix AC-RMSC1, criteria AC-RMSC1..AC-RMSC6 "
    "pinned in that row at R2440 BEFORE any code). Claim: the R2440 existence "
    "face measures its module corpus by walking the ROOT it is handed, so a "
    "join whose module is importable but lives outside that root - an installed "
    "package, or a publisher read from a subdirectory while the package sits at "
    "the tree top - read MISSING-MODULE exactly like a broken import, i.e. a "
    "scope limit and a typo were indistinguishable. Shipped "
    "src/os/relative_module_corpus_scope.py: every MISSING-MODULE row now "
    "carries scope_root (the root as given) and scope_corpus (the merged corpus "
    "size) both in the object and on screen; caller-declared --extra names are "
    "merged ON TOP of the measured tree and never replace it; the corpus is ONE "
    "root-wide walk per check (proved by a call counter reading 1 and by the "
    "module not importing the R2440 face at all); and the join plus the "
    "WIRE/FOREIGN word stay publish_relative_package_identity's own, asked at "
    "CALL time, so an extra makes a module PRESENT and cannot invent a wire. "
    "Proof: AC-RMSC1..AC-RMSC6 SUITE PASS 6/6 TWICE with identical verdicts and "
    "three adjacent suites green (qa/relative-module-corpus-scope-R2491.log, "
    "1413B, legs=2 identical=True, fails=0). LIVE: the real tree reads "
    "verdict=WIRE corpus=1402 scanned=1400 publishers=11 wire=11 missing=0, and "
    "the seed's own defect is reproduced end to end - a scripts/ root reads "
    "MISSING-MODULE with its scope printed, --extra clears it, and the "
    "whole-tree root clears it too "
    "(qa/relative-module-corpus-scope-live-R2491.log, 1666B utf-8 LF). Registry "
    "573/4414 -> 574/4420 by exactly one row; matrix restamped stamp-aligned to "
    "55073B at 574/4420 with a byte-identical --check whose green line honestly "
    "reads 573/574; census DRIFT-CLEAN flags=0; tech row 525 closed and the next "
    "head is AC-RMPP1; reconcile-battery-R2491 appended first=no at the "
    "pre-registered 574/4420. The battery then ran RED on the committed product "
    "tree with four failed assertions in three suites, all traceable to two "
    "birth-site defects this window created or inherited: the residue "
    "declaration had expired at until=R2482 (283 of 284 live rounds read "
    "EXPIRED) and the product commit moved the queue without refreshing the "
    "export, so the queue face read STALE. Both were repaired at the birth site "
    "- the declaration re-pinned through the shipped writer from one live "
    "reading (283 -> 284 entries, MEASURED statuses, until=R2511) and the export "
    "re-derived then landed through the queue gate. Honest: an INTERNAL face, "
    "not a CEO-clickable one; the real 19.9 debit and the real msgSecCheck still "
    "wait on CEO physical items; Docker is absent so no containerised bring-up "
    "is claimed; tasks.md was not touched."
)

base.OUTS = (
    "src/os/relative_module_corpus_scope.py + "
    "src/os/test_relative_module_corpus_scope.py + "
    "src/sandbox/reconcile_all.py + qa/relative-module-corpus-scope-R2491.log + "
    "qa/relative-module-corpus-scope-live-R2491.log + "
    "docs/sandbox-suite-matrix.md + state/queue/tech.md + state/debt.md + "
    "state/residue_triage.json + src/os/evidence_R2491.py + "
    "src/os/wire_R2491.py + src/os/close_tech_R2491.py + src/os/export_R2491.py + "
    "src/os/state.json + docs/status-export.json + heartbeat.txt + "
    "src/os/backlog.md"
)

if __name__ == "__main__":
    print(base.main())