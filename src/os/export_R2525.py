"""export_R2525 - refresh docs/status-export.json for the R2525 window.

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
    "2026-11-07 R2525 PRODUCT window on the tech head the queue named "
    "(state/queue/tech.md:561 prefix AC-PLAC1, criteria AC-PLAC1..AC-PLAC6 "
    "pinned at R2523 BEFORE any code; debt gate OPEN-NONE, queue_head "
    "claimable=11, all five anchors re-checked at zero occupancy). SHIPPED "
    "src/os/probe_seam_annotated_constant_scope.py plus its suite: the shipped "
    "constant tables are EXTENDED rather than replaced - an annotated "
    "assignment whose annotation is a plain name, a walrus binding and a "
    "for-loop target of one str literal are read in the module body and in "
    "function bodies with the same ambiguity rule - and the shipped resolution "
    "law is asked FIRST with those tables, so only when it answers None is ONE "
    "more attribute hop taken on a module-level constant tree with the binding "
    "label carried on the row. An annotation that is not a plain name is "
    "refused; a call, a concatenation, a comprehension and an arithmetic "
    "expression are never evaluated and are named unresolved. PROOF: "
    "AC-PLAC1..AC-PLAC6 SUITE PASS 6/6 TWICE with an identical digest plus "
    "three adjacent probe faces green (qa/probe-seam-annotated-constant-scope-"
    "R2525.log, 8335B, legs=2 identical=True fails=0 adjacent=3) with LF only "
    "and a byte read-back; a live leg on the REAL tree reads "
    "SEAMS-ANNOTATED-COVERED over 1410 probes (3 covered, 172 out-of-scope, "
    "1235 historical, missing=0) with the real probes showing their annotated "
    "local bindings, one annotated fixture reads MISSING-SEAM missing=PLRC "
    "dynamic=importlib.import_module:plac_live_helper@NAME, a missing root is "
    "refused E_PLAC_NO_ROOT, and the module and render digests are unchanged "
    "(qa/probe-seam-annotated-constant-scope-live-R2525.log, 1267B). REGISTRY "
    "591/4522 -> 592/4528 by one row recounted by importing "
    "reconcile_all.SUITES; docs/sandbox-suite-matrix.md regenerated "
    "stamp-aligned from the eligible battery leg qa/reconcile-all-R2524-"
    "retry.log to 57026B with --check byte-identical and green honestly "
    "591/592. BIRTH SITE: the R2514 residue block had expired at until R2524, "
    "so the shipped idempotent repin re-read every live round it carries and "
    "re-pinned them through R2535 (300 -> 301 entries, 83156B -> 83255B, "
    "readback PINNED), which also declared R2525 DELIVERED, after which the "
    "batch appender correctly REFUSED a duplicate and residue_triage --check "
    "reads R2525 TRIAGED live=DELIVERED at exit 0. BOARD: row 561 closed with "
    "its DISCHARGED note (predicted and measured 1698899B) and ONE row seeded "
    "from this window own measured limit naming AC-PCAS1..AC-PCAS6, floor "
    "FLOOR-MET 5/5 10/10 10/10, head now line 563. DEBT: "
    "reconcile-battery-R2525 appended first=yes at 592 suites / 4528 criteria "
    "(156539B -> 156981B) and product-face-R2525 first=no (156981B -> "
    "157320B), both readback ok. HONEST: two product points on a runnable "
    "reading, nothing a CEO opens is new and no P-47 business surface moved; "
    "the defect was measured at R2523 and re-measured here, so this is a "
    "repair of a disclosed gap; the limits are measured rather than assumed; "
    "the walk shape is a third copy because parameterising a shipped face "
    "would owe a same-window battery while tables, resolution law, shape "
    "detector and seam classifier all stay the shipped ones; the state_fold "
    "layout defect from R2524 is still open and the append used a proved "
    "load+dump round-trip instead; Docker is absent; the real 19.9 debit and "
    "the real msgSecCheck still wait on CEO physical items; tasks.md was not "
    "touched.")

base.OUTS = (
    "qa/probe-seam-annotated-constant-scope-R2525.log + "
    "qa/probe-seam-annotated-constant-scope-live-R2525.log + "
    "src/os/probe_seam_annotated_constant_scope.py + "
    "src/os/test_probe_seam_annotated_constant_scope.py + "
    "src/sandbox/reconcile_all.py + docs/sandbox-suite-matrix.md + "
    "state/residue_triage.json + state/queue/tech.md + state/debt.md + "
    "src/os/queue_close_R2525.py + src/os/closeout_R2525.py + "
    "src/os/export_R2525.py + src/os/state.json + docs/status-export.json + "
    "src/os/backlog.md + heartbeat.txt")

if __name__ == "__main__":
    print(base.main())