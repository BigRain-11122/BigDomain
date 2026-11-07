"""export_R2515 - refresh docs/status-export.json for the R2515 product window.

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
    "2026-11-07 R2515 PRODUCT window on the tech head the register named "
    "(product-face-R2514, state/queue/tech.md:552 prefix AC-PSF1 "
    "probe_seam_forwarding_scope, criteria AC-PSF1..AC-PSF6 pinned there at "
    "R2513 BEFORE any code). Five-silence scan clean at HEAD f80b75a9 (git "
    "status empty, no index.lock, zero @BigDomain ledger rows, decisions diff "
    "new=0 over the stored 90-token baseline at 189 rows, group orders tail "
    "unchanged at 2026-11-06 23:46, benchmarks 2026-11-03 inside the gate). "
    "R2513 had MEASURED that a probe quieting the guard seams through a "
    "shared helper names no seam itself, so the registry read it OUT-OF-SCOPE "
    "while the helper read COVERED and the forwarding shape stayed invisible. "
    "SHIPPED src/os/probe_seam_forwarding_scope.py plus its suite: the hop is "
    "DERIVED at CALL time from the probe own module-level imports and each "
    "helper own syntax tree (no helper list, no seam name spelled in the "
    "module), so editing ONLY a helper moves the same probe MISSING-SEAM -> "
    "COVERED with no code change, a bare string that merely names a helper is "
    "not an import, and a differently named helper is followed. A forwarding "
    "probe reads COVERED with its helpers named; a helper that omits a seam "
    "makes the probe MISSING-SEAM naming seam and file with the probe never "
    "run; a module importing helpers that quiet nothing stays OUT-OF-SCOPE; "
    "an unparseable source or helper reads UNREADABLE; a round-token file "
    "reads HISTORICAL. ONE HOOP WAS NOT ENOUGH, measured before shipping: a "
    "one-hop reading INVENTS a MISSING-SEAM when a middle helper names part "
    "of the set and re-exports the rest, so the shipped reading follows local "
    "imports transitively (same root, cycle-guarded, depth 8) - a strict "
    "superset of the registered face, disclosed. PROOF: AC-PSF1..AC-PSF6 "
    "SUITE PASS 6/6 TWICE identical plus four adjacent readability suites "
    "green (qa/probe-seam-forwarding-scope-R2515.log, 6183B, legs=2 "
    "identical=True fails=0 adjacent=4) and a live leg on the REAL tree "
    "reading SEAMS-FORWARDED over 3 covered probes with the render and doc "
    "digests unchanged, a forwarding fixture COVERED helpers=quiet_helper "
    "quieted=5, a stale fixture MISSING-SEAM missing=STPT and a MEASURED lazy "
    "gap (an import inside a function body reads OUT-OF-SCOPE quieted=0, "
    "qa/probe-seam-forwarding-scope-live-R2515.log 1132B class=tee). "
    "REGISTRY 586/4492 -> 587/4498 by exactly one row "
    "os-probe-seam-forwarding-scope(6) recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md regenerated "
    "stamp-aligned from qa/reconcile-all-R2514-retry.log to 56475B at 587 "
    "suites / 4498 criteria with --check byte-identical and green honestly "
    "586/587. BOARD: row 552 closed through a per-round writer (predicted and "
    "measured 1674931B, readback ok), one row seeded from this window own "
    "measured limit as AC-PSL1..AC-PSL6, floor FLOOR-MET 5/5 10/10 10/10, head "
    "now line 553. DEBT: product-face-R2514 closed (148756B -> 148759B), "
    "reconcile-battery-R2515 appended first=yes at 587/4498 (148759B -> "
    "149123B), product-face-R2515 appended first=no (149123B -> 149635B); "
    "the gate now names the battery first. HONEST: one product point on a "
    "runnable reading and nothing a CEO could open newly built; the same-root "
    "and module-level limits are named and seeded; raw queue_row / "
    "queue_done_stamp checkers read VIOLATION / UNSTAMPED on OLD rows that "
    "pre-date this window and were not touched; Docker absent; tasks.md "
    "untouched; the S4U lane reconcile still needs an ELEVATED shell."
)

base.OUTS = (
    "qa/probe-seam-forwarding-scope-R2515.log + "
    "qa/probe-seam-forwarding-scope-live-R2515.log + "
    "src/os/probe_seam_forwarding_scope.py + "
    "src/os/test_probe_seam_forwarding_scope.py + "
    "docs/sandbox-suite-matrix.md + "
    "state/queue/tech.md + state/debt.md + src/os/state.json + "
    "docs/status-export.json + src/os/backlog.md + heartbeat.txt"
)

if __name__ == "__main__":
    print(base.main())