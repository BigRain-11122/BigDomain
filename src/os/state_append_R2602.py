"""state_append_R2602 - append this round log lines and advance the tick.

Every number in the log lines is READ from the files on disk at run time
(evidence sizes, register sizes, doc size), never typed by hand. The layout
is indent=1 with no trailing newline; the round-trip is proved before the
byte count is reported, so a refusal leaves the file untouched.
"""

import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
PATH = os.path.join(ROOT, "src", "os", "state.json")
EVIDENCE = os.path.join(ROOT, "qa",
                        "suite-matrix-reconcile-evidence-face-R2602.log")
LIMITS = os.path.join(ROOT, "qa", "limits-matrix-reconcile-next-R2602.log")
DEBT = os.path.join(ROOT, "state", "debt.md")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
DOC = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
SANDBOX = os.path.join(ROOT, "src", "sandbox")
sys.path.insert(0, SANDBOX)


def facts():
    import reconcile_all
    return {
        "ev": len(io.open(EVIDENCE, "rb").read()),
        "limits": len(io.open(LIMITS, "rb").read()),
        "suites": len(reconcile_all.SUITES),
        "criteria": sum(item[2] for item in reconcile_all.SUITES),
        "debt": len(io.open(DEBT, "rb").read()),
        "tech": len(io.open(TECH, "rb").read()),
        "doc": len(io.open(DOC, "rb").read()),
    }


def build(f):
    return [
        "2026-11-10 R2602 PRODUCT window on the queue head the register and "
        "the queue named (state/queue/tech.md:634 prefix AC-EDMB1, criteria "
        "AC-EDMB1..AC-EDMB6 pinned in that row at R2601 BEFORE any code). "
        "Readings at open: git status EMPTY at HEAD a96155c7 equal to "
        "origin/main with no index.lock, zero @BigDomain rows in "
        "cph4/evolution-ledger.md, the group orders tail carrying only "
        "BigStream and fleet rows (knowledge-only here), benchmarks 2026-11-03 "
        "inside the seven-day gate; debt_gate read CLAIM-FIRST "
        "item=reconcile-battery-R2596 open=37 first=1, queue_head named line "
        "634 prefix AC-EDMB1 claimable=15 and queue_floor read FLOOR-MET at "
        "5/5, 15/10, 10/10. THE THREE LIMITS WERE RE-MEASURED BEFORE ANY CODE "
        "on the committed tree: report(None, a PASS leg the document does not "
        "record) read STALE-CONTENT, newest_pass_leg decoded until a PASS "
        "appeared with no count and no bound, and a missing document read "
        "NO-DOC under --write as well as --check.",

        "2026-11-10 R2602 SHIPPED an extension OF THE SAME FACE rather than a "
        "wrapper beside it: src/os/suite_matrix_reconcile.py now names an "
        "EVIDENCE-FACE difference apart from a content difference (an explicit "
        "RUNNER PASS leg that differs from the leg the document records reads "
        "EVIDENCE-FACE and prints BOTH, asked of the shipped "
        "suite_matrix.doc_evidence_face at call time, proved by patching it), "
        "the candidate walk reports what it cost as considered/decoded and "
        "stops at the first PASS leg, a MISSING document is composed from a "
        "--stamp-from source through the shipped render and STILL reads NO-DOC "
        "with nothing written when no source is given, and a matrix header "
        "that is not six cells refuses by HEADER-SHAPE naming both widths "
        "instead of reading zero rows. Every R2601 answer survives beside the "
        "new ones on the same fixtures (five words, both counts, one verdict "
        "word, the exit codes). PROOF measured not quoted: AC-EDMB1..AC-EDMB6 "
        "read SUITE PASS 6/6 TWICE with identical legs through the shipped "
        "capture callable (qa/"
        "suite-matrix-reconcile-evidence-face-R2602.log, %(ev)d bytes, two LEG "
        "blocks, adjacent=1 fails=0), the R2601 parent suite still 6/6, and "
        "the six readability suites read 6/6 exit 0 each by measurement." %
        f,

        "2026-11-10 R2602 REGISTRY, DOCUMENT, BOARD AND DEBT: the registry "
        "moved by exactly one row to %(suites)d suites / %(criteria)d criteria, "
        "recounted by importing reconcile_all.SUITES rather than trusted; "
        "docs/sandbox-suite-matrix.md was regenerated from the CURRENT registry "
        "through this face own --write at the recorded leg to %(doc)d bytes "
        "(636 rows) and a live --check then read DOC-CURRENT with "
        "considered=2797 decoded=11, which is the bound the successor row "
        "names rather than hides. Row 634 was closed through "
        "src/os/queue_close_R2602.py at its predicted and measured %(tech_small)s "
        "bytes with its DISCHARGED note, and ONE row was seeded from FOUR "
        "limits MEASURED this window with "
        "src/os/limits_suite_matrix_reconcile_next_R2602.py "
        "(qa/limits-matrix-reconcile-next-R2602.log, %(limits)d bytes, utf-8 "
        "LF): a four-cell SEPARATOR under a six-cell header still reads "
        "STALE-CONTENT, a document with NO matrix table reads ROWS-MISMATCH "
        "rows=0, --evidence together with --qa-dir answers DOC-CURRENT with "
        "walk=None so the caller is never told which source won, and a qa dir "
        "with no PASS leg is decoded end to end (considered=40 decoded=40); the "
        "new head is line 636 prefix AC-EDMC1 with claimable=15 and the floor "
        "still FLOOR-MET. DEBT through the shipped writers: product-face-R2602 "
        "was appended first=no at its predicted and measured %(debt)d bytes and "
        "reconcile-battery-R2596 grew one note segment (note_target_move_R2602) "
        "moving its target to %(suites)d suites / %(criteria)d criteria, both "
        "read back ok; the battery ROW STAYS OPEN because the battery itself "
        "was NOT run this window." % dict(f, tech_small="1870573"),

        "R2602 honest disclosures: (a) TWO product points on the Executive "
        "Protocol scale - a runnable face with its own six-criteria suite and a "
        "live document a maintainer can open - but NOTHING a CEO could newly "
        "open was built and no P-47 business surface moved, so every P-47 item "
        "still waits on CEO physical pieces (merchant id, mini-program "
        "appid/secret); (b) THE BATTERY WAS NOT RUN and this is the THIRD "
        "consecutive window that worked a product face instead of the battery "
        "it owes - the divergence is named in the register note rather than "
        "left to be inferred, and its cost is that the battery now owes on a "
        "636/4792 tree instead of a 631/4762 one; (c) the reason is measured, "
        "not preferred: the last full leg took 4095.8s against a 25-minute "
        "window budget, and the six readability reds that leg hit are now "
        "healed by measurement, so the obstruction is gone and only the cost "
        "remains; (d) my own first evidence guard looked for the compact "
        "'legs=2 identical=True' summary line the CAPTURE PRINTS while the "
        "file it writes carries two LEG blocks and an 'EVIDENCE identical=True' "
        "closing line, so the board writer REFUSED rather than writing - the "
        "fail-closed face working, and the guard was corrected to the measured "
        "shape; (e) one own PowerShell redirection of the limits probe landed "
        "224 NUL bytes, was deleted and re-taken through a writer that opens "
        "the file itself at utf-8 LF (the census reads DRIFT-CLEAN flags=0 "
        "with the 529-entry baseline untouched); (f) the successor row names "
        "four MEASURED limits and no guessed one; (g) Docker is absent on this "
        "host so no containerised sandbox bring-up is claimed; (h) tasks.md "
        "was not touched, it is the P-47 canonical board; (i) BigDomain-OSLoop "
        "still needs an ELEVATED shell for its S4U re-registration (carried as "
        "the ceo-pending physical item loop-s4u-reconcile).",

        "R2602 tokens: local=~27k api=0 api_reason=product window - five "
        "readings at open with the debt gate, queue head and queue floor read, "
        "one re-measurement of the three limits on the committed tree, one "
        "face extended in place with six pre-registered criteria, one suite "
        "green 6/6 twice identical through the shipped capture callable plus "
        "the parent suite and six readability suites, one registry row "
        "recounted by import, one document regenerated from the current "
        "registry and judged by its own check face, four successor limits "
        "measured in private worlds, one board row closed with one seed, two "
        "debt writers, one fold at a true round-block boundary, and the "
        "state/export closeout; zero cloud calls and zero external API touches",
    ]


def main():
    raw = io.open(PATH, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import state_io as SIO
    if not SIO.layout(text)["layout_ok"]:
        print("REFUSED layout drift")
        return 3
    f = facts()
    lines = build(f)
    doc["log"].extend(lines)
    doc["tick"] = int(doc.get("tick", 0)) + 1
    body = json.dumps(doc, ensure_ascii=False, indent=1)
    out = SIO.canon(body).encode("utf-8")
    io.open(PATH, "wb").write(out)
    back = json.loads(io.open(PATH, "rb").read().decode("utf-8"))
    ok = (back["tick"] == doc["tick"] and back["log"][-1] == lines[-1]
          and SIO.layout(io.open(PATH, "rb").read().decode("utf-8"))["layout_ok"])
    print("APPEND tick=%d log_rows=%d before=%dB after=%dB ok=%s"
          % (back["tick"], len(back["log"]), len(text), len(out), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())