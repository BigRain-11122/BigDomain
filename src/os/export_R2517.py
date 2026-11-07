"""export_R2517 - refresh docs/status-export.json for the R2517 product window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies
this round's result row and its outs row.

RUN ORDER (shipped law): execute this AFTER the state append, then land the
queue block through src/os/queue_export_gate_wire.py --execute if it reports
STALE.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-07 R2517 PRODUCT window on the tech head the register named "
    "(product-face-R2516, state/queue/tech.md:553 prefix AC-PSL1 "
    "probe_seam_lazy_scope, criteria AC-PSL1..AC-PSL6 pinned there at R2515 "
    "BEFORE any code). Five-silence scan clean at HEAD 3c3a4e5f (git status "
    "empty, no index.lock, zero @BigDomain ledger rows, decisions diff new=0 "
    "over the stored 90-token baseline, group orders tail unchanged at "
    "2026-11-06 23:46, benchmarks 2026-11-03 inside the gate). R2515 had "
    "MEASURED that a probe importing its quieting helper INSIDE a function "
    "body reads OUT-OF-SCOPE with zero quieted seams because only "
    "module-level imports were followed, so a lazy forwarding probe stayed "
    "invisible. SHIPPED src/os/probe_seam_lazy_scope.py plus its suite: import "
    "resolution is DERIVED at CALL time from the probe own syntax tree at ANY "
    "nesting level on the same cycle-guarded same-root walk (no helper list, "
    "no seam name spelled in the module), so a lazy forwarding probe reads "
    "COVERED with its helpers and its lazy imports named on the row while the "
    "same fixture reads OUT-OF-SCOPE under the module-level face. A lazy "
    "helper that omits a seam makes the probe MISSING-SEAM naming seam and "
    "file with the probe never run; a module whose lazy imports quiet nothing "
    "stays OUT-OF-SCOPE; a lazily chained helper cannot invent a missing seam; "
    "a lazy cycle terminates; an unparseable source reads UNREADABLE; a "
    "round-token file reads HISTORICAL. PROOF: AC-PSL1..AC-PSL6 SUITE PASS 6/6 "
    "TWICE identical plus two adjacent probe faces green "
    "(qa/probe-seam-lazy-scope-R2517.log 6504B legs=2 identical=True fails=0 "
    "adjacent=2) and a live leg on the REAL tree reading SEAMS-LAZY-COVERED "
    "over 3 covered probes, 168 out-of-scope modules and 1208 historical "
    "one-shot scripts with a lazy fixture COVERED quieted=5 beside the same "
    "fixture OUT-OF-SCOPE quieted=0 and a stale fixture MISSING-SEAM missing "
    "STPT while render and artifact digests were unchanged "
    "(qa/probe-seam-lazy-scope-live-R2517.log 625B class=tee). REGISTRY "
    "587/4498 -> 588/4504 by exactly one row os-probe-seam-lazy-scope(6) "
    "recounted by importing reconcile_all.SUITES; docs/sandbox-suite-matrix.md "
    "regenerated stamp-aligned from qa/reconcile-all-R2516.log to 56544B at "
    "588 suites / 4504 criteria with --check byte-identical and green "
    "honestly 587/588. BOARD: row 553 closed through a per-round writer "
    "(predicted and measured 1679440B, readback ok), one row seeded from this "
    "window own measured limit as AC-PDI1..AC-PDI6, floor FLOOR-MET 5/5 "
    "10/10 10/10, head now line 555. DEBT: product-face-R2516 closed "
    "(150420B -> 150423B), reconcile-battery-R2517 appended first=yes at "
    "588/4504 (150423B -> 150786B), product-face-R2517 appended first=no "
    "(150786B -> 151161B) after one equals-sign refusal obeyed and rewritten; "
    "the gate now names the battery first. HONEST: one product point on a "
    "runnable reading and nothing a CEO could open newly built; the run-time "
    "import limit is named and seeded rather than hidden; the decisions file "
    "read 116 rows against a stored 189 with its token set unchanged at 90 so "
    "no new decision arrived; raw queue_row / queue_done_stamp checkers read "
    "VIOLATION / UNSTAMPED on OLD rows that pre-date this window and were not "
    "touched; Docker absent; tasks.md untouched; the S4U lane reconcile still "
    "needs an ELEVATED shell."
)

base.OUTS = (
    "qa/probe-seam-lazy-scope-R2517.log + "
    "qa/probe-seam-lazy-scope-live-R2517.log + "
    "src/os/probe_seam_lazy_scope.py + "
    "src/os/test_probe_seam_lazy_scope.py + "
    "docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/debt.md + src/os/state.json + "
    "docs/status-export.json + src/os/backlog.md + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())