"""suite_matrix_reconcile - let the matrix document carry CURRENT registry
truth while its evidence line names a RUNNER PASS leg.

MEASURED at R2598 and re-measured at R2600 (this window open): the six
readability suites compare docs/sandbox-suite-matrix.md against a fresh
render and went RED because the document still rendered 631 rows while
src/sandbox/reconcile_all.SUITES read 634 by import. The only shipped way to
move the document is src/sandbox/suite_matrix.py --evidence <leg>, and that
face refuses a document stamped from a leg that is not RUNNER PASS (a red leg
records an evidence path that --check cannot resolve back, so the document
reads stale for a second, structural reason).

This face is the ONE reconciliation: it asks the shipped faces at CALL time
and says what is actually wrong, in one word.

  newest_pass_leg(qa_dir)      the newest qa/*.log whose RUNNER line reads
                             PASS, found by walking newest-first and asking
                             the shipped suite_matrix.parse_evidence (linear
                             walk; a linear scan answers None honestly when
                             no such leg exists).
  doc_rows(text)              matrix table data rows of a composed document.
  report(doc=..., evidence=...)  asks suite_matrix.main --check (the shipped
                             check face) and compares its row counts with
                             reconcile_all.SUITES. One verdict word:
                               DOC-CURRENT     the shipped check face is green
                               ROWS-MISMATCH   the document row count differs
                                               from the registry, BOTH counts
                                               named (the word this face adds)
                               STALE-CONTENT   rows agree, content drifted
                               RED-LEG         the named leg is not RUNNER PASS
                                               - refused, nothing written
                               NO-DOC          the document is missing
  write(doc=..., evidence=...)   composes the document from the CURRENT
                             registry through suite_matrix.render (the shipped
                             composition), keeps the document own stamp and
                             recorded --stamp-from provenance so only content
                             moves, writes it atomically with a read-back, and
                             proves it through the shipped check face before
                             it reports WRITTEN. A red leg or a post-write
                             check failure restores the previous bytes.

Nothing here re-implements a law: the check verdict, the row counts of the
composed document, the leg's own suite count and the render are all asked of
the shipped modules. Patching those seams moves this report, which is how
AC-EDM4 is proved.

LIMIT, stated rather than buried: the shipped check face is asked by CALLING
suite_matrix.main with --check and capturing its stdout, because that face
prints rather than returning a verdict. That costs one render per reading and
it is why this module must never be asked to decide what the shipped face
already decides.

Criteria AC-EDM1..AC-EDM6 were pinned in state/queue/tech.md:633 as the R2599
seed row BEFORE this code existed. R2602 extended the same face in place with
AC-EDMB1..AC-EDMB6 (pinned the same way at R2601): an explicit PASS leg that
differs from the leg the document records reads EVIDENCE-FACE naming BOTH, the
candidate walk reports what it decoded, a MISSING document can be composed
from a --stamp-from source, and a matrix table that is not six cells refuses
by header shape instead of reading zero rows.

Pure ASCII, stdlib only, no clock, no network. Default mode is read-only.

CLI: [--doc PATH] [--evidence PATH] [--stamp-from PATH] [--check | --write]
     [--json]
  exit 0 = DOC-CURRENT (or WRITTEN)
  exit 2 = document missing, ROWS-MISMATCH, EVIDENCE-FACE or STALE-CONTENT
  exit 3 = RED-LEG / HEADER-SHAPE / REWRITE-REFUSED / bad flags
  exit 4 = the shipped check face refused for readability (its own reasons)
"""

import argparse
import contextlib
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)

import reconcile_all as RA  # noqa: E402  the suite registry
import suite_matrix as SM  # noqa: E402  the shipped composition + check face
import matrix_stamp_provenance_line as MSPL  # noqa: E402

DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")

WORD_CURRENT = "DOC-CURRENT"
WORD_ROWS = "ROWS-MISMATCH"
WORD_STALE = "STALE-CONTENT"
WORD_RED = "RED-LEG"
WORD_NONE = "NO-DOC"
WORD_WRITTEN = "WRITTEN"
WORD_REFUSED = "REWRITE-REFUSED"
# AC-EDMB1: a PASS leg that differs from the leg the document records is an
# EVIDENCE-FACE difference, not a content difference. The shipped check face
# already prints that comparison; this face gives it one word and one exit
# code instead of leaving it inside the content word.
WORD_EVID = "EVIDENCE-FACE"
# AC-EDMB4: a matrix table that does not carry the six cells this face counts
# refuses by header shape instead of reading zero rows and reporting a row
# mismatch against a table it never understood.
WORD_HEADER = "HEADER-SHAPE"
CODE_HEADER = "E_EDMB_HEADER"
MATRIX_CELLS = 6

# Matrix table data rows carry SIX cells (index, suite, path, criteria, state,
# secs). The billable-faces table below it also starts with a number, so a
# bare "^| <n> |" would count it too and inflate the row count by design.
ROW_RE = re.compile(r"(?m)^\| \d+ \|(?:[^|\n]*\|){5}$")


def rel(path):
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def doc_rows(text):
    return len(ROW_RE.findall(text))


def registry_counts():
    return len(RA.SUITES), sum(c for _, _, c in RA.SUITES)


def newest_pass_leg_scanned(qa_dir=None):
    """Newest qa/*.log whose RUNNER line reads PASS, asked of the shipped
    parse_evidence. Returns (path, run, walk) where walk names the cost that
    was paid: how many candidate files were listed and how many were actually
    decoded before the answer was found (AC-EDMB2 - the walk stops at the
    first PASS leg, so its cost is bounded and now visible)."""
    qa_dir = qa_dir or QA_DIR
    if not os.path.isdir(qa_dir):
        return None, None, {"considered": 0, "decoded": 0}
    paths = [os.path.join(qa_dir, name) for name in os.listdir(qa_dir)
             if name.endswith(".log")]
    paths.sort(key=lambda p: (-os.path.getmtime(p), os.path.basename(p)))
    decoded = 0
    for path in paths:
        try:
            _, run = SM.parse_evidence(path)
        except (OSError, UnicodeDecodeError):
            continue
        decoded += 1
        if run and run["verdict"] == "PASS":
            return path, run, {"considered": len(paths), "decoded": decoded}
    return None, None, {"considered": len(paths), "decoded": decoded}


def newest_pass_leg(qa_dir=None):
    """(path, run) only - the shape R2601 published, kept byte for byte."""
    path, run, _walk = newest_pass_leg_scanned(qa_dir)
    return path, run


def matrix_header_cells(text, patterns):
    """Cells of the matrix table header line, or None when that table is
    absent. Read by POSITION under the shipped matrix title, never by a row
    shape guess, so a table that changed its column layout is named rather
    than silently counted as zero rows (AC-EDMB4)."""
    title = patterns["labels"]["matrix_title"]
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == title.strip():
            for follow in lines[index + 1:]:
                if follow.startswith("|"):
                    return follow.count("|") - 1
                if follow.strip():
                    return None
            return None
    return None


def shipped_check(doc_path, evidence_path):
    """Ask the SHIPPED check face. Returns (exit_code, its own output)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SM.main(["suite_matrix.py", "--check", "--out", doc_path,
                        "--evidence", evidence_path])
    return code, buffer.getvalue()


def compose(doc_path, evidence_path, source_text=None):
    """Compose the document from the CURRENT registry, keeping its stamp and
    recorded provenance so only content moves. Returns (text, status, run).

    `source_text` is the text the stamp and the recorded borrow are read from;
    it defaults to the document being written and is the ONLY way a MISSING
    document can be composed (AC-EDMB3), because a document that does not
    exist cannot lend its own stamp."""
    patterns = SM.load_patterns()
    current = read_text(doc_path) if source_text is None else source_text
    stamp = SM.doc_stamp(current, patterns)
    if stamp is None:
        raise ValueError("E_EDM_STAMP")
    status, run = SM.parse_evidence(evidence_path)
    text = SM.render(patterns, evidence_path, status, run, stamp,
                     stamp_from=MSPL.recorded_source(current,
                                                     patterns["labels"]))
    return text, status, run


def report(doc_path=None, evidence_path=None, qa_dir=None):
    doc_path = doc_path or DOC
    if not os.path.exists(doc_path):
        return {"verdict": WORD_NONE, "doc": rel(doc_path),
                "exit": 2, "written": False}
    current = read_text(doc_path)
    patterns = SM.load_patterns()
    rows, criteria = registry_counts()
    cells = matrix_header_cells(current, patterns)
    if cells is not None and cells != MATRIX_CELLS:
        return {"verdict": WORD_HEADER, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_HEADER, "cells": cells,
                "expected_cells": MATRIX_CELLS,
                "reason": "matrix table carries %d cells, expected %d"
                          % (cells, MATRIX_CELLS)}
    have_rows = doc_rows(current)
    walk = None
    if evidence_path is None:
        evidence_path, _, walk = newest_pass_leg_scanned(qa_dir)
        if evidence_path is None:
            return {"verdict": WORD_RED, "doc": rel(doc_path),
                    "exit": 3, "written": False, "reason": "no runner leg",
                    "walk": walk}
    else:
        evidence_path = (evidence_path if os.path.isabs(evidence_path)
                         else os.path.join(REPO, evidence_path))
    status, run = SM.parse_evidence(evidence_path)
    if run is None or run["verdict"] != "PASS":
        return {"verdict": WORD_RED, "doc": rel(doc_path),
                "evidence": rel(evidence_path), "exit": 3,
                "written": False, "walk": walk,
                "reason": (run or {}).get("verdict", "no RUNNER line")}
    code, message = shipped_check(doc_path, evidence_path)
    result = {"doc": rel(doc_path), "evidence": rel(evidence_path),
              "doc_rows": have_rows, "registry_rows": rows,
              "registry_criteria": criteria,
              "leg_green": run["green"], "leg_total": run["total"],
              "shipped_check": code, "written": False}
    if walk is not None:
        result["walk"] = walk
    if code == 0:
        result.update({"verdict": WORD_CURRENT, "exit": 0})
        return result
    if code == 4:
        result.update({"verdict": "READABILITY-REFUSED", "exit": 4,
                       "reason": message.strip().splitlines()[0]})
        return result
    if have_rows != rows:
        result.update({"verdict": WORD_ROWS, "exit": 2})
        return result
    # AC-EDMB1: rows agree, the leg is PASS, so a remaining difference is the
    # document naming a DIFFERENT leg. Asked of the shipped doc_evidence_face
    # at CALL time, and both legs are named so the operator can see them.
    recorded = SM.doc_evidence_face(current, patterns)
    if recorded is not None and recorded != rel(evidence_path):
        result.update({"verdict": WORD_EVID, "exit": 2,
                       "recorded_evidence": recorded})
        return result
    result.update({"verdict": WORD_STALE, "exit": 2})
    return result


def write(doc_path=None, evidence_path=None, qa_dir=None, stamp_from=None):
    doc_path = doc_path or DOC
    if not os.path.exists(doc_path) and stamp_from is not None:
        return _compose_missing(doc_path, evidence_path, qa_dir, stamp_from)
    result = report(doc_path, evidence_path, qa_dir)
    if result["verdict"] in (WORD_CURRENT, WORD_NONE):
        return result
    if result["verdict"] in (WORD_RED, "READABILITY-REFUSED", WORD_HEADER):
        return result
    leg = os.path.join(REPO, result["evidence"])
    previous = read_text(doc_path)
    text, _, _ = compose(doc_path, leg)
    with open(doc_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    readback = read_text(doc_path)
    code, _ = shipped_check(doc_path, leg)
    if readback != text or code != 0:
        with open(doc_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(previous)
        result.update({"verdict": WORD_REFUSED, "exit": 3,
                       "written": False, "shipped_check": code})
        return result
    result.update({"verdict": WORD_WRITTEN, "exit": 0, "written": True,
                   "doc_rows": doc_rows(text), "bytes": len(
                       text.encode("utf-8")), "shipped_check": code})
    return result


def _compose_missing(doc_path, evidence_path, qa_dir, stamp_from):
    """AC-EDMB3: compose a document that does not exist from a --stamp-from
    source. The source lends the stamp and the recorded borrow ONLY; the rows
    and the evidence line come from the CURRENT registry and the named leg.
    A red leg, a missing source or a failed read-back leaves NO file behind,
    which is the pre-state of a document that never existed."""
    stamp_from = (stamp_from if os.path.isabs(stamp_from)
                  else os.path.join(REPO, stamp_from))
    walk = None
    if evidence_path is None:
        evidence_path, _, walk = newest_pass_leg_scanned(qa_dir)
        if evidence_path is None:
            return {"verdict": WORD_RED, "doc": rel(doc_path), "exit": 3,
                    "written": False, "reason": "no runner leg",
                    "walk": walk}
    else:
        evidence_path = (evidence_path if os.path.isabs(evidence_path)
                         else os.path.join(REPO, evidence_path))
    status, run = SM.parse_evidence(evidence_path)
    if run is None or run["verdict"] != "PASS":
        return {"verdict": WORD_RED, "doc": rel(doc_path),
                "evidence": rel(evidence_path), "exit": 3,
                "written": False, "walk": walk,
                "reason": (run or {}).get("verdict", "no RUNNER line")}
    if not os.path.exists(stamp_from):
        return {"verdict": "STAMP-MISSING", "doc": rel(doc_path), "exit": 3,
                "written": False, "stamp_from": rel(stamp_from)}
    try:
        text, _, _ = compose(doc_path, evidence_path,
                             source_text=read_text(stamp_from))
    except ValueError:
        return {"verdict": WORD_REFUSED, "doc": rel(doc_path), "exit": 3,
                "written": False, "stamp_from": rel(stamp_from)}
    with open(doc_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    readback = read_text(doc_path)
    code, _ = shipped_check(doc_path, evidence_path)
    if readback != text or code != 0:
        os.remove(doc_path)
        return {"verdict": WORD_REFUSED, "doc": rel(doc_path), "exit": 3,
                "written": False, "shipped_check": code}
    return {"verdict": WORD_WRITTEN, "doc": rel(doc_path), "exit": 0,
            "written": True, "composed_from": rel(stamp_from),
            "evidence": rel(evidence_path), "doc_rows": doc_rows(text),
            "bytes": len(text.encode("utf-8")), "shipped_check": code,
            "walk": walk}


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--doc", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--qa-dir", default=None)
    parser.add_argument("--stamp-from", default=None)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.write and args.check:
        print("FAIL flags: E_EDM_BAD_FLAGS --write and --check are exclusive")
        return 3
    if args.write:
        result = write(args.doc, args.evidence, args.qa_dir,
                       args.stamp_from)
    else:
        result = report(args.doc, args.evidence, args.qa_dir)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("%s %s" % (result["verdict"], result["doc"]))
        if result["verdict"] in (WORD_ROWS, WORD_STALE):
            print("  doc-rows=%d registry-rows=%d (%d criteria)"
                  " evidence=%s leg=%s/%s shipped-check=%d"
                  % (result["doc_rows"], result["registry_rows"],
                     result["registry_criteria"], result["evidence"],
                     result["leg_green"], result["leg_total"],
                     result["shipped_check"]))
        elif result["verdict"] == WORD_EVID:
            print("  recorded-evidence=%s named-evidence=%s"
                  " registry-rows=%d (%d criteria)"
                  % (result["recorded_evidence"], result["evidence"],
                     result["registry_rows"], result["registry_criteria"]))
        elif result["verdict"] == WORD_HEADER:
            print("  %s %s cells=%d expected=%d"
                  % (result["code"], result["reason"], result["cells"],
                     result["expected_cells"]))
        elif result["verdict"] == WORD_RED:
            print("  evidence=%s reason=%s"
                  % (result.get("evidence"), result.get("reason")))
        elif result["verdict"] == WORD_WRITTEN:
            print("  %d bytes, %d rows, evidence=%s"
                  % (result["bytes"], result["doc_rows"],
                     result["evidence"]))
        if result.get("walk"):
            print("  evidence-walk considered=%d decoded=%d"
                  % (result["walk"]["considered"], result["walk"]["decoded"]))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv))