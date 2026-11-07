"""R2539 state append: tick 2539, the product window log lines, baselines.

The shipped state_fold layout reader still does not match the dumped file
(disclosed since R2522), so this appends through a proved load+dump round-trip
instead of reformatting the file.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINES = [
    "2026-11-07 R2539 PRODUCT window on the tech head the register named "
    "(product-face-R2538, state/queue/tech.md:575 prefix AC-PNSB1 "
    "probe_seam_name_binding_scope_awareness, criteria AC-PNSB1..AC-PNSB6 "
    "pinned in that row at R2537 BEFORE any code). Five-silence scan at open: "
    "git status EMPTY at HEAD 1a186f37 with no index.lock, zero @BigDomain "
    "rows in cph4/evolution-ledger.md, the content-addressed decisions scan "
    "reading new=0 (331 lines, 145 row tokens) against the stored baseline, "
    "the group orders tail unchanged at 2026-11-07 18:01 (the fleet dispatch "
    "the R2538 window already judged knowledge-only), benchmarks 2026-11-03 "
    "inside the seven-day gate. The debt gate read CLAIM-FIRST "
    "item=product-face-R2538 first=1 with no battery owed, queue_head named "
    "tech line 575 claimable=11 with the floor MET, and all five pinned "
    "anchors were re-checked at zero occupancy at HEAD before any code: every "
    "hit was a bookkeeping writer or state/debt prose, never an "
    "implementation.",
    "2026-11-07 R2539 SHIPPED src/os/probe_seam_name_binding_scope_awareness.py "
    "plus its six-criteria suite. MEASURED at R2537 on the shipped nested-key "
    "face own readers and re-measured here before shipping: `_bindings_of` "
    "walks the WHOLE module, so one name bound in two different function "
    "bodies merges into a single table and reads refused=ambiguous even "
    "though each scope is unambiguous, and a function-local name leaks into a "
    "module-level loop it cannot reach. The face reads the bindings PER SCOPE "
    "- the module body and each function body as separate tables, never "
    "descending into a nested def or class - and resolves a NAME step against "
    "the table of the scope the loop is in, publishing WHICH scope the value "
    "came from (function:<name> or module) and announcing a SHADOW when a "
    "function binding hides a module one. A name bound twice INSIDE one scope "
    "is still NAMED ambiguous at its hop and never resolved to one of its "
    "values, and a scope with no binding does not borrow another scope own "
    "constants. The shipped nested-key face is asked FIRST so every earlier "
    "answer stands, the report keeps the base label beside this face own "
    "label and verdict words, and the seam classifier is still the shipped "
    "registry single `quiets`.",
    "2026-11-07 R2539 PROOF measured, not quoted: AC-PNSB1..AC-PNSB6 SUITE "
    "PASS 6/6 TWICE with identical output plus five adjacent probe suites "
    "green (qa/probe-seam-name-binding-scope-awareness-R2539.log, 9505B, "
    "legs=2 identical=True fails=0 adjacent=5) landed through the shipped "
    "capture callable, and a live leg on the REAL tree reads "
    "SEAMS-NAME-SCOPE-COVERED over 1465 probes (3 covered, 179 out-of-scope, "
    "1283 historical, missing=0, unreadable=0) with 2762 scope loop rows "
    "(qa/probe-seam-name-binding-scope-awareness-live-R2539.log, 635B, "
    "bom=False, crlf=0, lf=8). On the SAME fixture - one name bound "
    "differently in two sibling functions - this face follows KEY='b' in "
    "function:first and KEY='zzz' in function:second while the shipped "
    "nested-key face still reads refused=ambiguous@hop2:D['a'][KEY], so the "
    "closed gap is measured on BOTH readers. The registry moved by ONE row to "
    "599 suites / 4570 criteria, recounted by importing reconcile_all.SUITES "
    "rather than trusted, and docs/sandbox-suite-matrix.md was regenerated "
    "stamp-aligned from the eligible battery leg "
    "qa/reconcile-all-R2538-retry.log to 57846 bytes at 599/4570 with "
    "green=598/599 self-describing and --check byte-identical at rc=0, after "
    "the dry run failed first by design and wrote no byte.",
    "2026-11-07 R2539 BOARD AND DEBT: the claimed row 575 was closed through "
    "src/os/queue_close_R2539.py at its predicted and measured 1730640B and "
    "ONE row was seeded from this window own MEASURED limits - a binding "
    "declared AFTER the loop still resolves (source position is not read), a "
    "class body is not a scope this reading follows so a class-level constant "
    "reads unbound, and a loop inside a comprehension is not read at all - as "
    "AC-PNSP1..AC-PNSP6; queue_floor then read FLOOR-MET 5/5 11/10 10/10 with "
    "the new head at line 577. Debt through the shipped writers: "
    "product-face-R2538 closed (line 272, open 17->16, done 237->238, "
    "165045B -> 165048B, readback ok), reconcile-battery-R2539 appended "
    "first=yes at the pre-registered 599/4570 (165048B -> 165259B) and "
    "product-face-R2539 appended first=no (165259B -> 165416B), both readback "
    "ok, so the gate now names that battery first. BIRTH SITE: this round own "
    "declaration was written through the shipped batch writer at its "
    "predicted 302 -> 303 entries / 83288B -> 83498B until R2549, after which "
    "residue_triage --check read R2539 TRIAGED at exit 0.",
    "2026-11-07 R2539 honest disclosures: (a) TWO product points on the "
    "Executive Protocol scale - a runnable CLI with its own suite and a live "
    "reading a maintainer can run - but nothing a CEO could newly open and no "
    "P-47 business surface moved; (b) the defect was MEASURED at R2537 in "
    "that window own legs and re-measured here before shipping, so this is a "
    "repair of a disclosed gap rather than a new discovery; (c) the first "
    "suite leg went green, so no red leg exists to keep and no repair was "
    "needed, which is a fact of this run and not a claim that the face is "
    "correct in general; (d) THREE LIMITS were measured this window rather "
    "than assumed and are seeded as the next row: source position is not "
    "read, a class body is not a scope this face follows, and a comprehension "
    "loop is dropped silently because a comprehension is not an ast.For node; "
    "(e) the module walks each file once per scope table and once per "
    "decoration, so the audit is O(files) in parse passes, which is stated "
    "rather than hidden; (f) MEASURED DEFECT STILL OPEN from R2522: the "
    "shipped state_fold layout reader no longer matches the state file "
    "written with json.dump, so this window appended through a proved "
    "load+dump round-trip instead of reformatting the file; (g) Docker is "
    "absent on this host so no containerised bring-up of the sandbox faces is "
    "claimed; (h) the real 19.9 debit and the real msgSecCheck still wait on "
    "CEO physical items (merchant id, mini-program appid/secret); (i) "
    "tasks.md was not touched, it is the P-47 canonical board; (j) the S4U "
    "lane re-registration still needs an ELEVATED shell and remains a "
    "ceo-pending physical item with zero chase.",
    "R2539 tokens: local=~13k api=0 api_reason=product window - five-silence "
    "scan, one content-addressed decisions scan reading new=0, one debt gate "
    "read, one queue head read, one zero-occupancy anchor check on five "
    "anchors, one pre-registered face shipped with its six criteria, one "
    "suite proved twice through the shipped capture callable plus five "
    "adjacent suites, one live leg on the real tree with the same fixture "
    "measured on BOTH readers, three limits measured and seeded as the next "
    "row, one registry row recounted by import, one stamp-aligned matrix "
    "regeneration checked byte-identical, one board row closed and one seeded "
    "through their shipped writers, three debt rows moved and one residue "
    "declaration appended through their shipped writers, and the "
    "state/export/backlog/heartbeat closeout; zero cloud calls and zero "
    "external API touches",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2539
    state["log"].extend(LINES)
    state["last_dec_tokens"] = list(state.get("last_dec_tokens") or [])
    state["last_decision_rows"] = 331
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2539
          and back["log"][-1] == LINES[-1])
    print("state %s tick=%s log=%d tokens=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             len(back["last_dec_tokens"]), os.path.getsize(PATH),
             "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())