"""R2491 closeout: append this window's log items and move the tick.

One atomic replace in the state canon, proved by a read-back. No new group
decision token was dispatched this window (the five-silence scan read new=0),
so the stored baseline is carried unchanged.
"""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINES = [
    "2026-11-06 R2491 TECH window on the carried product leader the register named after R2490 discharged its battery (product-face-R2490, tech head state/queue/tech.md:525 prefix AC-RMSC1, criteria AC-RMSC1..AC-RMSC6 pinned in that row at R2440 BEFORE any code). Claim: the R2440 existence face measures its module corpus by walking the ROOT it is handed, so a join whose module is importable but lives outside that root - an installed package, or a publisher read from a subdirectory while the package sits at the tree top - read MISSING-MODULE exactly like a broken import, i.e. a scope limit and a typo were indistinguishable. Five-silence scan at open was clean at HEAD 874aba06 (git status empty, no index.lock, zero @BigDomain ledger rows, decisions diff new=0, group orders tail unchanged, benchmarks 2026-11-03 inside the gate) and debt_gate named this row CLAIM-FIRST, so the window shipped it rather than running another battery.",
    "2026-11-06 R2491 SHIPPED src/os/relative_module_corpus_scope.py: every MISSING-MODULE row now carries scope_root (the root AS GIVEN) and scope_corpus (the merged corpus size) both in the object and on screen; caller-declared --extra names are merged ON TOP of the measured tree and never replace it; the corpus is ONE root-wide walk per check; and the join plus the WIRE/FOREIGN word stay publish_relative_package_identity's own, asked at CALL time, so an extra makes a module PRESENT and cannot invent a wire. Every key the R2440 face published keeps its name and meaning, so this reading is a strict extension of that contract.",
    "2026-11-06 R2491 PROOF: AC-RMSC1..AC-RMSC6 read SUITE PASS 6/6 TWICE with identical verdicts through the shipped capture callable plus three adjacent suites green (qa/relative-module-corpus-scope-R2491.log, 1413B, legs=2 identical=True, adjacent=3 fails=0). MEASURED on the real tree: root=src/os package=src.os verdict=WIRE corpus=1402 scanned=1400 publishers=11 wire=11 relative=0 missing=0. The seed's own defect is reproduced live end to end in qa/relative-module-corpus-scope-live-R2491.log (1666B, utf-8 LF, crlf=0): a scripts/ root reads MISSING-MODULE at exit 2 with its scope printed, the same root plus --extra mypkg.wire reads WIRE at exit 0, and the whole-tree root reads WIRE too - so the scope limit is printed as a scope limit rather than read as a typo.",
    "2026-11-06 R2491 my own first test drafts were wrong twice and were corrected against measurement, never by loosening a criterion: the AC-RMSC3 draft expected the extras to turn FOREIGN into WIRE (they only make a module PRESENT - the word stays the parent's, which is exactly AC-RMSC4's split), and the AC-RMSC4 dependency probe banned the R2440 face's NAME while the module legitimately names it in prose, so it now bans the import instead. Both are disclosed because a suite that was wrong first and fixed later is weaker evidence than one written right, and the criteria text in the queue row was never touched.",
    "2026-11-06 R2491 registry, matrix and debt: the registry moved 573 -> 574 suites and 4414 -> 4420 criteria by exactly one row os-relative-module-corpus-scope(6) and tech row 525 was closed with a DISCHARGED line, so the queue floor still reads FLOOR-MET 5/5 10/10 10/10 and the next head is state/queue/tech.md:527 prefix AC-RMPP1. docs/sandbox-suite-matrix.md was restamped stamp-aligned from the last eligible battery evidence qa/reconcile-all-R2490.log to 55073B at 574/4420 with --check byte-identical, its green line honestly reading 573/574; qa_writer_census --check read flags=0 verdict DRIFT-CLEAN. reconcile-battery-R2491 was appended first=no through the shipped debt_append at 127795B -> 128177B with readback ok at the pre-registered 574/4420.",
    "2026-11-06 R2491 the battery ran FIRST on the committed product tree (fb9bff6c) and came back RED - 571/574 with four failed assertions in os-residue-triage AC-RTR6, os-status-export-writer-dialect-wire AC-SEWD4 and os-queue-floor-export-face AC-QFE3 - and both causes were real birth-site defects rather than load noise, so the red leg was kept and not counted as green: (a) the residue declaration had expired at until=R2482 while the log kept growing, so 283 of 284 live rounds read EXPIRED; (b) the product commit moved the queue (closing row 525 took tech claimable 11 -> 10) without refreshing the export, so the queue face read STALE. Both were repaired at the birth site - the declaration re-pinned through the shipped writer from ONE live reading (283 -> 284 entries at MEASURED statuses, until=R2511, 78996B -> 79303B) and the export re-derived through the shipped driver then landed through the queue gate wire (197593B -> 197842B, gate CURRENT) - and the repair was committed ALONE as 50a7d360 before the retry.",
    "2026-11-06 R2491 RETRY GREEN ON THE COMMITTED REPAIR TREE, MEASURED NOT QUOTED: qa/reconcile-all-R2491-retry.log is 868331B utf-8 with bom=False, crlf=0 and lone_cr=0; its closing line reads 'RUNNER PASS (574/574 suites green, reconcile controls 7/7, 1395.3s)' with zero FAIL suite rows; an independent recount over the 574 per-suite PASS rows sums criteria to exactly 4420 - byte for byte the total pre-registered at R2491 - and the tmp reclaim line reads candidates=932 removed=932 busy=0 failed=0 reclaimed=326.59 MiB. The four follow-up sections then ran in the designed order: the dry run read SECTION matrix FAIL matrix mismatch on-disk=55073B regenerated=55097B with no byte written while fingerprint PASS CLEAN domains=5, profile PASS byte-identical and census PASS DRIFT-CLEAN; suite_matrix.py regenerated the document from THIS round's own green evidence through --evidence plus --stamp-from ('green=574/574'), --check read byte-identical at 55097B / 574 / 4420, and the write leg read four PASS for VERDICT R2491 PASS failing=none (APPENDED 1950B eol_ok=True). So the matrix is self-describing again rather than naming a borrowed leg.",
    "2026-11-06 R2491 debt settled through the shipped writers: reconcile-battery-R2491 closed at line 213 (open 3->2, done 191->192, 128177B -> 128181B, readback ok); the stale pointer product-face-R2490 was closed at line 212 (open 2->1, done 192->193, 128181B -> 128184B, readback ok) because its own note names tech.md:525 and that row now reads done R2491 with a DISCHARGED line, so leaving it open would have had the next window rebuild this face; and product-face-R2491 was appended first=yes at 128184B -> 128723B with readback ok, naming state/queue/tech.md:527 prefix AC-RMPP1. No successor battery is registered: this window's post-battery writes are the matrix doc, the register, the closeout scripts and the state/export/backlog/heartbeat closeout, none of which is a registry module or suite, and the registry is unmoved at 574 suites / 4420 criteria.",
    "2026-11-06 R2491 honest disclosures: (a) this is an INTERNAL tech face, one point of product on the ambitious reading and zero on the Executive Protocol scale - nothing a CEO could open was built, and what it buys is that an absence in a relative-import reading now says where it looked instead of accusing a typo; (b) the battery cost two full runs because this window's own product commit moved the queue without refreshing the export - the defect is mine and it is named rather than blamed on the runner; (c) Docker is absent on this host, so a containerised bring-up of the seven sandbox faces stays unproved and is not claimed; (d) the real 19.9 debit and the real msgSecCheck still wait on CEO physical items (merchant id, mini-program appid/secret); (e) tasks.md was not touched, it is the P-47 canonical board; (f) no fold was due: src/os/state.json measured 60206B at open against the 78500B waterline with 69 log items.",
    "R2491 tokens: local=~22k api=0 api_reason=tech-face window - one pre-registered face reading every absence's search scope with caller-declared extras merged on top, one six-criteria suite proved twice identical plus three adjacent suites green, one live leg that reproduces the seed defect on a real tree and clears it two ways, one red battery leg naming two real birth-site defects, two repairs committed alone (residue re-pin from one live reading; export re-derived and landed through the gate), one green retry at 574/574 with exactly 4420 criteria recounted independently, one stamp-aligned matrix regeneration with a byte-identical --check, four follow-up sections PASS, one battery row and one stale pointer closed plus the successor opened through their shipped writers, and the state/export/backlog/heartbeat closeout; zero cloud calls and zero external API touches",
    "2026-11-06 R2491 self-heal check: BigDomain-OSLoop exists but its Principal.LogonType still reads InteractiveToken, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["tick"] = 2491
    state["last_order"] = "2026-11-05 20:22"
    state["last_decision_rows"] = 221
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = (len(back["log"]) == len(state["log"])
          and back["tick"] == 2491
          and back["last_order"] == "2026-11-05 20:22")
    print("APPEND tick=%d log_items=%d tokens=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), len(back["last_dec_tokens"]),
             os.path.getsize(PATH), "ok" if ok else "MISMATCH"))


if __name__ == "__main__":
    main()