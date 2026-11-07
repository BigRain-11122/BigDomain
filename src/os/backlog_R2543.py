"""R2543 backlog bookkeeping: one carried row for R2544 and one done row."""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
BACKLOG = os.path.join(REPO, "src", "os", "backlog.md")

CARRIED = (
    "- [ ] [carried 2026-11-08 R2543] R2544 first item: a VERIFICATION window "
    "on the battery the register owes - reconcile-battery-R2543 at the "
    "pre-registered 601 suites / 4582 criteria, because R2543 moved the "
    "registry by one row (os-probe-seam-name-binding-control-flow-scope) and a "
    "shipped document (the R2168 mixed-tree rule). Re-measure the target by "
    "importing reconcile_all.SUITES before the launch rather than trusting the "
    "register, run the full battery on a CLEAN committed tree with git status "
    "empty before the run, launch it detached and unfiltered through "
    "src/os/battery_stream.py with an explicit --evidence path and NEVER a "
    "shell redirection of its stdout into qa/ (the ps-utf16 trap has cost this "
    "repository several whole legs), keep the red leg if it goes red and commit "
    "a birth-site repair ALONE before any retry, then run the four follow-up "
    "sections through src/os/battery_followup.py (its matrix section FAILS "
    "first on a stale doc by design and must NOT rewrite it; regenerate with "
    "src/sandbox/suite_matrix.py --evidence <leg> --stamp-from "
    "docs/sandbox-suite-matrix.md after). On green go back to the product face "
    "the queue head names - re-read it with python src/os/queue_head.py --head "
    "tech, which this window left at state/queue/tech.md:581 prefix AC-PNCG1 "
    "probe_seam_name_binding_control_flow_guard_scope (criteria AC-PNCG1.."
    "AC-PNCG6 pinned in that row THIS window before any code): two arms binding "
    "the SAME literal refuse as guarded although both agree, two separate if "
    "statements binding one name to two values read as one guard word, and a "
    "nested binding publishes only the innermost guard while the outer guard on "
    "the same path is dropped. NOTE measured many times: a commit that moves "
    "the queue must also re-derive docs/status-export.json and land its queue "
    "block through queue_export_gate_wire --execute. Also open and misc: the "
    "state file stands well past the waterline so state_fold --check reads "
    "FOLD-DUE and the fold could NOT run because the shipped layout reader "
    "still refuses a json.dump layout (open since R2522) - carry that as an "
    "owed fold; queue_row --check still names four PRE-EXISTING rows without a "
    "criteria prefix (tech.md:524, :537, :586 and explore.md:295) which this "
    "window declined to mass-edit; and BigDomain-OSLoop still reads "
    "InteractiveToken, which the 2026-09-29 machine law forbids for every lane "
    "task (carried as the ceo-pending physical item loop-s4u-reconcile, needs "
    "an ELEVATED shell).\n")

DONE = (
    "- [x] [done 2026-11-08 R2543] R2543 PRODUCT window on the tech head the "
    "register named (product-face-R2542, state/queue/tech.md:579 prefix "
    "AC-PNCF1 probe_seam_name_binding_control_flow_scope, criteria "
    "AC-PNCF1..AC-PNCF6 pinned in that row at R2541 BEFORE any code). "
    "Five-silence scan at open: git status EMPTY at HEAD 3ae0d426 with no "
    "index.lock, zero @BigDomain rows in the group ledger, the content-"
    "addressed decisions diff read SIX new tokens (D-20261108-01..06) over the "
    "stored 176-token baseline at 344 rows, the group orders tail moved to "
    "2026-11-08 00:04 (a lane-batch dispatch to @bm-m and the BigCompute lanes, "
    "knowledge only), benchmarks 2026-11-03 inside the gate; debt gate read "
    "CLAIM-FIRST product-face-R2542 with no battery owed and queue_head named "
    "line 579 claimable=11 with the floor MET. SHIPPED "
    "src/os/probe_seam_name_binding_control_flow_scope.py plus its six-criteria "
    "suite: a NAME step resolves ONLY when its binding is PROVED to run before "
    "the loop - a binding behind a branch is NAMED guarded:if:<line> and never "
    "resolved while an unconditional binding still wins, a with-as binding is "
    "NAMED with-as instead of reading unbound, two EXCLUSIVE arms of one if "
    "publish BOTH arms by name instead of one ambiguity word, and a binding "
    "inside a loop body, a try arm or a handler is NAMED with its own guard. "
    "The shipped position face is asked FIRST and every row carries the shipped "
    "answer beside this face own, so the closed gap is measured on BOTH "
    "readers. PROOF: SUITE PASS 6/6 TWICE with identical output plus five "
    "adjacent probe suites green (qa/probe-seam-name-binding-control-flow-"
    "scope-R2543.log, 11053B, legs=2 identical=True fails=0 adjacent=5) and a "
    "live leg on the REAL tree reading SEAMS-CONTROL-FLOW-COVERED over 1481 "
    "probes (3 covered, 181 out-of-scope, 1297 historical, missing=0) with 9 "
    "own loop rows, written by one UTF-8 LF writer. REGISTRY 600/4576 -> "
    "601/4582 by exactly one row recounted by import; matrix regenerated "
    "stamp-aligned from qa/reconcile-all-R2542-leg3.log to 58105B at 601/4582 "
    "with green honestly 600/601 and --check byte-identical. BOARD: row 579 "
    "closed at its predicted and measured 1738378B, ONE row seeded from this "
    "window own measured limits as AC-PNCG1..AC-PNCG6, floor FLOOR-MET 5/5 "
    "11/10 10/10, head now line 581. DEBT: product-face-R2542 closed "
    "(168141B -> 168144B, line 278, open 19->18, done 241->242, readback ok), "
    "reconcile-battery-R2543 opened first=yes at 601/4582 (168144B -> 168425B) "
    "and product-face-R2543 opened first=no naming tech line 581 AC-PNCG1 "
    "(168425B -> 168693B), both readback ok; the round was declared through the "
    "shipped batch writer (304 -> 305 entries, 83775B -> 84151B, until R2553) "
    "and residue_triage --check then read R2543 TRIAGED. HONEST: two product "
    "points, nothing a CEO could newly open and no P-47 business surface moved; "
    "three limits measured and seeded; queue_row still names four PRE-EXISTING "
    "rows without a criteria prefix which this window declined to mass-edit; "
    "the state_fold layout reader is still broken since R2522 so the fold is "
    "carried rather than discharged; Docker absent; the real 19.9 debit and the "
    "real msgSecCheck still wait on CEO physical items; tasks.md untouched.\n")

text = io.open(BACKLOG, encoding="utf-8").read()
payload = CARRIED + DONE + text
io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(payload)
back = io.open(BACKLOG, encoding="utf-8").read().splitlines()
print("backlog rows=%d head=%s" % (len(back), back[0][:70]))