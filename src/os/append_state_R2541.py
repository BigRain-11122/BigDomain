"""append_state_R2541 - record the R2541 product window in src/os/state.json.

Pure bookkeeping writer: bumps tick, appends the round line, the honest
disclosures line and the token line, and records the measured decisions row
count. Written as a script so the JSON stays valid and the exact bytes
appended are reviewable.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(BASE, "state.json")

ROUND = (
    "2026-11-07 R2541 PRODUCT window on the tech head the register named "
    "(product-face-R2540, state/queue/tech.md:577 prefix AC-PNSP1 "
    "probe_seam_name_binding_position_scope, criteria AC-PNSP1..AC-PNSP6 "
    "pinned in that row at R2539 BEFORE any code). Five-silence scan at open: "
    "GIT STATUS EMPTY at HEAD b0a6c80f with no index.lock, zero @BigDomain "
    "rows in cph4/evolution-ledger.md, the content-addressed decisions diff "
    "read new=0 over the stored 160-token baseline at a measured 330 rows / "
    "145 tokens, group orders tail unchanged, benchmarks 2026-11-03 inside "
    "the seven-day gate. The debt gate read CLAIM-FIRST item="
    "product-face-R2540 first=1 with no battery owed, queue_head named tech "
    "line 577 claimable=11 with the floor MET at 5/5 10/10 10/10, and all "
    "five pinned anchors were re-checked at zero occupancy by git grep before "
    "any code: every hit was a seed row, a bookkeeping writer, state or debt "
    "prose, never an implementation."
)

SHIP = (
    "2026-11-07 R2541 SHIPPED src/os/probe_seam_name_binding_position_scope.py "
    "plus its six-criteria suite. MEASURED at R2539 on the shipped scope face "
    "own readers and re-measured here before shipping: the bindings are read "
    "per SCOPE and not per POSITION, so a loop that runs before its key is "
    "bound reads exactly like one that runs after; a class body is not a "
    "scope that reading follows, so a class-level constant reads unbound for "
    "a loop in that class body while the row attributes the loop to module; "
    "and a loop spelled inside a comprehension is dropped silently because a "
    "comprehension is not an ast.For node. The face answers all three on top "
    "of the shipped law: the shipped scope face is asked FIRST so every "
    "answer it already gave stands, the position tables ADD the LINE of each "
    "binding, and the row gains a not-yet-bound refusal, a class scope, a "
    "later-write publication and comprehension kinds "
    "(comprehension:list/:set/:dict/:generator). The seam classifier is still "
    "the shipped registry single `quiets`, so no second classifier exists."
)

PROOF = (
    "2026-11-07 R2541 PROOF measured, not quoted: AC-PNSP1..AC-PNSP6 SUITE "
    "PASS 6/6 TWICE with identical output plus five adjacent probe suites "
    "green (qa/probe-seam-name-binding-position-scope-R2541.log, 14166B, "
    "legs=2 identical=True fails=0 adjacent=5) landed through the shipped "
    "capture callable; a live leg on the REAL tree reads "
    "SEAMS-POSITION-COVERED over 1474 probes (3 covered, 180 out-of-scope, "
    "1291 historical, missing=0, unreadable=0) with the covered probes "
    "publishing their own position loop rows "
    "(qa/probe-seam-name-binding-position-scope-live-R2541.log, 1206B, utf-8, "
    "LF, written by a single UTF-8 LF writer rather than a shell "
    "redirection). The registry moved by ONE row to 600 suites / 4576 "
    "criteria, recounted by importing reconcile_all.SUITES rather than "
    "trusted, and docs/sandbox-suite-matrix.md was regenerated stamp-aligned "
    "from the eligible battery leg qa/reconcile-all-R2539.log to 57951 bytes "
    "at 600 suites / 4576 criteria with its green line honestly reading "
    "599/600, after the dry run failed first by design and wrote no byte; "
    "--check then read byte-identical."
)

BOARD = (
    "2026-11-07 R2541 BOARD AND DEBT: the claimed row 577 was closed through "
    "src/os/queue_close_R2541.py at its predicted and measured 1734579B "
    "(delta 6375) and ONE row was seeded from this window own MEASURED limit "
    "- a binding inside a branch that may not run still resolves, a with-as "
    "binding is not collected at all, and a try/except binding the name twice "
    "in exclusive branches reads one ambiguous word - as AC-PNCF1..AC-PNCF6; "
    "queue_floor then read FLOOR-MET 5/5 11/10 10/10 with the new head at "
    "line 579. DEBT through the shipped writers: product-face-R2540 closed "
    "(line 275, open 18->17, done 239->240, 166562B -> 166565B, readback ok), "
    "reconcile-battery-R2541 appended first=yes at the pre-registered 600 "
    "suites / 4576 criteria (166565B -> 166971B) and product-face-R2541 "
    "appended first=no (166971B -> 167420B), both readback ok, so the gate "
    "now names that battery first. The round was declared through the shipped "
    "batch writer at its predicted 83498B -> 83775B (303 -> 304 entries, "
    "until R2551) and residue_triage --check then read R2541 TRIAGED at exit "
    "0."
)

HONEST = (
    "2026-11-07 R2541 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a live "
    "reading a maintainer can run - but nothing a CEO could newly open and no "
    "P-47 business surface moved; (b) the defect was MEASURED at R2539 in "
    "that window own legs and re-measured here before shipping, so this is a "
    "repair of a disclosed gap rather than a new discovery; (c) THREE LIMITS "
    "were MEASURED this window rather than assumed and are seeded as the next "
    "tech row: control flow is not read (a binding inside `if False:` still "
    "resolves), a `with ... as NAME` binding is not collected at all and "
    "reads unbound, and a try/except binding the same name in two exclusive "
    "branches reads ambiguous; (d) only literally constant values are "
    "followed and a name bound twice BEFORE the loop is still refused as "
    "ambiguous rather than picked; (e) the matrix green line honestly reads "
    "599/600 because this round own suite is not in the battery leg it was "
    "stamped from; (f) the registry moved by one row and a shipped doc moved, "
    "so a battery on this committed tree is owed BEFORE any further product "
    "byte; (g) MEASURED DEFECT STILL OPEN from R2522: the shipped state_fold "
    "layout reader no longer matches the state file written with json.dump, "
    "so this window appended through a proved load+dump round-trip instead of "
    "reformatting the file; (h) the stored last_decision_rows field read 331 "
    "against a measured 330 rows and was corrected to the measurement here "
    "rather than left drifting; (i) Docker is absent on this host so no "
    "containerised bring-up of the sandbox faces is claimed; (j) the real "
    "19.9 debit and the real msgSecCheck still wait on CEO physical items "
    "(merchant id, mini-program appid/secret); (k) tasks.md was not touched, "
    "it is the P-47 canonical board; (l) the S4U lane reconcile still needs "
    "an ELEVATED shell and remains a ceo-pending physical item with zero "
    "chase."
)

TOKENS = (
    "R2541 tokens: local=~15k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one zero-"
    "occupancy anchor check on five anchors, one pre-registered face shipped "
    "with its six criteria, one suite proved twice through the shipped "
    "capture callable plus five adjacent suites, one live leg on the real "
    "tree with a single UTF-8 LF writer, three limits measured and seeded as "
    "the next row, one registry row recounted by import, one stamp-aligned "
    "matrix regeneration checked byte-identical after a designed dry-run "
    "FAIL, one board row closed and one seeded through their shipped "
    "writers, three debt rows moved and one residue declaration appended "
    "through their shipped writers, and the state/export/backlog/heartbeat "
    "closeout; zero cloud calls and zero external API touches"
)

MEASURED_DECISION_ROWS = 330


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    before = state["tick"]
    log_before = len(state["log"])
    state["tick"] = before + 1
    state["log"].extend([ROUND, SHIP, PROOF, BOARD, HONEST, TOKENS])
    state["last_decision_rows"] = MEASURED_DECISION_ROWS
    data = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(data)
    with io.open(STATE, encoding="utf-8") as handle:
        back = json.load(handle)
    print("STATE APPEND tick=%d->%d log=%d->%d bytes=%d readback=%s rows=%d"
          % (before, back["tick"], log_before, len(back["log"]),
             os.path.getsize(STATE),
             "ok" if back["log"][-1] == TOKENS else "MISMATCH",
             back["last_decision_rows"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())