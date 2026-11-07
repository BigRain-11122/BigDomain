"""export_R2527 - refresh docs/status-export.json for the R2527 window.

The derivation, the queue face and the proved write live in the shipped
export_R2431 / export_driver_queue_face modules; this driver only supplies this
round's result row and its outs row. The three CEO lines are derived at call
time from state, from what actually landed under qa/ for this tick, and from
the open first=yes debt row - never typed as constants that can go stale.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as base  # noqa: E402

base.RESULT = (
    "2026-11-07 R2527 PRODUCT window on the tech head the queue named "
    "(state/queue/tech.md:563 prefix AC-PCAS1, criteria AC-PCAS1..AC-PCAS6 "
    "pinned at R2525 BEFORE any code; debt gate OPEN-NONE, queue_head "
    "claimable=11, all five anchors re-checked at zero occupancy after a "
    "defective first probe was found and re-run). SHIPPED "
    "src/os/probe_seam_constant_alias_scope.py plus its suite: an alias of an "
    "existing constant resolves to the SAME value to a FIXPOINT (plain, "
    "annotated and walrus bindings, in the module body and in function bodies) "
    "with the chain it took published on the row; a name bound twice with "
    "different values is DROPPED as ambiguous; the shapes that are genuinely "
    "not constants (with-as, multi-value for target, call, format, arithmetic "
    "and comprehension) are NAMED per name and printed even on OUT-OF-SCOPE "
    "rows; and a dict chain either resolves with its FULL label or is REFUSED "
    "naming the hop that broke (not-a-dict / no-key), never silently None. "
    "The shipped tables and resolution law are EXTENDED at call time and the "
    "seam classifier is still the shipped registry single `quiets`. "
    "BIRTH-SITE REPAIR: the shipped annotated face own chain label appended "
    "the hops in reverse for chains deeper than one (measured "
    "pkg.DEEP.A.B.NAMES -> pkg.DEEP.NAMES.B.A) and was repaired to the order "
    "followed, with one-hop labels byte-identical and that suite still 6/6. "
    "PROOF: AC-PCAS1..AC-PCAS6 SUITE PASS 6/6 TWICE with an identical digest "
    "plus three adjacent probe faces green (qa/probe-seam-constant-alias-"
    "scope-R2527.log, 7503B, legs=2 identical=True fails=0 adjacent=3) with a "
    "read-back; a live leg on the REAL tree reads SEAMS-ALIAS-COVERED over "
    "1418 probes (3 covered, 173 out-of-scope, 1242 historical, missing=0) "
    "with the module and render digests unchanged, and the SAME fixture reads "
    "COVERED quieted=5 dynamic=importlib.import_module:pcas_live_helper@"
    "ALIAS<-BASE_NAME here while the shipped annotated face still reads "
    "OUT-OF-SCOPE quieted=0 on it, with a broken chain refused by name "
    "(qa/probe-seam-constant-alias-scope-live-R2527.log, 564B, crlf=0). "
    "REGISTRY 592/4528 -> 593/4534 by one row recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md regenerated "
    "stamp-aligned from the eligible battery leg qa/reconcile-all-R2526.log to "
    "57113B with --check byte-identical and green honestly 592/593. BOARD: row "
    "563 closed with its DISCHARGED note (predicted and measured 1703036B) and "
    "ONE row seeded from this window own measured limit naming "
    "AC-PCAE1..AC-PCAE6 (a for-loop over a NAMED constant, a subscript alias "
    "and a container element all read empty and unnamed), floor FLOOR-MET "
    "5/5 11/10 10/10, head now line 565. DEBT: reconcile-battery-R2527 "
    "appended first=yes at 593 suites / 4534 criteria (159187B -> 159491B) and "
    "product-face-R2527 first=no (159491B -> 159687B), both readback ok; the "
    "birth site was declared through the shipped batch writer at its predicted "
    "301->302 entries / 83255B -> 83490B, after which residue_triage --check "
    "reads TRIAGED with untriaged=0. HONEST: two product points on a runnable "
    "reading, nothing a CEO opens is new and no P-47 business surface moved; "
    "the defect was measured at R2525 and re-measured here, so this is a "
    "repair of a disclosed gap; a real pre-existing label defect in a shipped "
    "module was repaired at its birth site; my first anchor probe was itself "
    "defective and was re-run; the limits are measured and seeded; the walk "
    "shape is a fourth copy because parameterising a shipped face would owe a "
    "same-window battery while tables, resolution law, shape detector and seam "
    "classifier all stay the shipped ones; the state_fold layout defect from "
    "R2522 is still open and the append used a proved load+dump round-trip "
    "instead; Docker is absent; the real 19.9 debit and the real msgSecCheck "
    "still wait on CEO physical items; tasks.md was not touched.")

base.OUTS = (
    "qa/probe-seam-constant-alias-scope-R2527.log + "
    "qa/probe-seam-constant-alias-scope-live-R2527.log + "
    "src/os/probe_seam_constant_alias_scope.py + "
    "src/os/test_probe_seam_constant_alias_scope.py + "
    "src/os/probe_seam_annotated_constant_scope.py + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/residue_triage.json + state/queue/tech.md + state/debt.md + "
    "src/os/queue_close_R2527.py + src/os/live_R2527.py + "
    "src/os/closeout_R2527.py + src/os/export_R2527.py + src/os/state.json + "
    "docs/status-export.json + src/os/backlog.md + heartbeat.txt")

if __name__ == "__main__":
    print(base.main())