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

R2604 extended the same face again with AC-EDMC1..AC-EDMC6 (pinned in
state/queue/tech.md:636 at R2602 BEFORE any code, from four limits MEASURED
there): a SEPARATOR row whose width disagrees with its own header is refused
by HEADER-SHAPE naming BOTH widths instead of falling through to a content
word, a document that carries no matrix table at all refuses with its own
word naming the missing table instead of reading ROWS-MISMATCH rows=0, the
candidate walk is bounded by a DECLARED ceiling and says so, and a caller
that passes an explicit --evidence together with a --qa-dir is told which
source answered and which one was ignored.

R2606 extended the same face again with AC-EDMD1..AC-EDMD6 (pinned in
state/queue/tech.md:638 at R2604 BEFORE any code, from four limits MEASURED
there): a SEPARATOR row drawn with any single repeated punctuation character
("=", "~", "*", ...) is read as the separator and a width disagreement is
refused by HEADER-SHAPE naming BOTH widths instead of falling through to a
content word; a header carrying NO separator row at all refuses with its own
word naming the missing separator; a ceiling below one candidate refuses by
name so a starved walk cannot look like an honest empty pile; and a document
whose matrix title appears more than once refuses by name with the count
instead of reading the first table and ignoring the rest.

R2608 extended the same face again with AC-EDME1..AC-EDME6 (pinned in
state/queue/tech.md:640 at R2606 BEFORE any code), and its own suite printed
the successor limit in plain words: "the row counter is NOT fence-aware".

R2621 extends the same face with AC-EDMG1..AC-EDMG6 (pinned in
state/queue/tech.md:650 at R2616 BEFORE any code, re-measured here before any
byte): the row law is TABLE-AWARE as well as fence-aware, so a data-shaped row
in a SECOND table (fenced or not) is not a matrix row; the fence law names its
own malformations instead of toggling blind - an opening mark that is never
closed is refused naming the LINE it was opened on, and a closing mark SHORTER
than the mark that opened the block is a nested dialect refused naming BOTH
marker widths.

R2616 extends the same face with AC-EDMF1..AC-EDMF6 (pinned in
state/queue/tech.md:646 at R2608 BEFORE any code, from four limits MEASURED
there and re-measured here before any byte): the row law is FENCE-AWARE, so a
data-shaped row inside a ``` block is quoted text and not a matrix row and a
document whose only row difference is quoted reads the check face own word
instead of ROWS-MISMATCH; a table is identified by its header text and width,
so the same table repeated WITHOUT its separator row is the SAME table rather
than a second title; a table with DIFFERENT header text is still a second
table and still refuses by TITLE-REPEATED with the count; the shipped check
face is still asked on every reading so a content difference keeps its
content word; and every R2608 answer survives beside the new ones.

R2624 extends the same face with AC-EDMH1..AC-EDMH6 (pinned in
state/queue/tech.md:652 at R2621 BEFORE any code, and re-measured here with
src/os/limits_matrix_reconcile_row_shape_R2624.py before any byte): a
data-shaped row with the WRONG CELL COUNT is ONE non-row, so one bad row
undercounts by one instead of collapsing the count to zero - MEASURED at
R2624 as 642 -> 0 for both a four-cell and a seven-cell row, where the honest
answer is 641. A genuine header of a SECOND table still ends the first table
(the AC-EDMG1 law, re-proved on the same fixture), a separator row reappearing
inside the table still neither restarts nor ends it, and the shipped check
face is still asked exactly once per reading.

Pure ASCII, stdlib only, no clock, no network. Default mode is read-only.

CLI: [--doc PATH] [--evidence PATH] [--stamp-from PATH] [--qa-dir PATH]
     [--ceiling N] [--check | --write] [--json]
  exit 0 = DOC-CURRENT (or WRITTEN)
  exit 2 = document missing, ROWS-MISMATCH, EVIDENCE-FACE, STALE-CONTENT or
           TABLE-MISSING
  exit 3 = RED-LEG / HEADER-SHAPE / SEPARATOR-MISSING / TITLE-REPEATED /
           CEILING-STARVED / REWRITE-REFUSED / bad flags
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
# AC-EDMC2: a document that carries NO matrix table is not a row mismatch
# against a table it never had; it gets its own word and names what is absent.
WORD_TABLE = "TABLE-MISSING"
CODE_TABLE = "E_EDMC_TABLE"
# AC-EDMD2: a header that carries NO separator row is its own answer. Failing
# through to a content word told the operator nothing about the shape.
WORD_SEP = "SEPARATOR-MISSING"
CODE_SEP = "E_EDMD_SEPARATOR"
# AC-EDMD3: a ceiling smaller than one candidate cannot read anything, so it
# is refused by name rather than returning an empty answer that looks honest.
WORD_CEILING = "CEILING-STARVED"
CODE_CEILING = "E_EDMD_CEILING"
# AC-EDMD4: a document carrying the matrix title more than once was read as
# its FIRST table with the rest silently dropped.
WORD_TITLE = "TITLE-REPEATED"
CODE_TITLE = "E_EDMD_TITLE"
# AC-EDMC3: the candidate walk is bounded by a DECLARED ceiling so a qa pile
# with no PASS leg cannot be decoded end to end. The bound is reported.
WALK_CEILING = 64

# AC-EDMG2/AC-EDMG3: the fence law used to toggle on any line starting with
# three backticks, so a mark never closed quoted the rest of the document and
# a LONGER mark carrying a shorter one toggled twice. Both are refused by name.
WORD_FENCE = "FENCE-UNCLOSED"
WORD_NEST = "FENCE-NESTED"
CODE_FENCE = "E_EDMG_FENCE"
CODE_NEST = "E_EDMG_NEST"

# Matrix table data rows carry SIX cells (index, suite, path, criteria, state,
# secs). The billable-faces table below it also starts with a number, so a
# bare "^| <n> |" would count it too and inflate the row count by design.
ROW_RE = re.compile(r"(?m)^\| \d+ \|(?:[^|\n]*\|){5}$")
# AC-EDMH1: a row that OPENS like a data row (a pipe, digits, a pipe) but
# carries the wrong cell count is ONE malformed row, not the end of the table.
# Measured at R2624: one such row collapsed the whole count to 0 (delta -642)
# because it fell through to the second-table branch.
DATA_HEAD_RE = re.compile(r"^\|\s*\d+\s*\|")
SEPARATOR_CHARS = set("-: ")
# AC-EDMF1: a fenced code block quotes example text. A quoted data-shaped row
# is not a matrix row, so the row law has to know where the fence is.
FENCE_MARK = "```"
# AC-EDMG2/AC-EDMG3: an OPENING mark may carry an info string; a CLOSING mark
# may not. A closing mark shorter than its opening mark is not a close.
FENCE_OPEN_RE = re.compile(r"^[ \t]*(`{3,})([^`]*)$")
FENCE_CLOSE_RE = re.compile(r"^[ \t]*(`{3,})[ \t]*$")


def rel(path):
    return os.path.relpath(path, REPO).replace(os.sep, "/")


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def fence_scan(text):
    """(mask, problem): which lines are INSIDE a fenced block, and the first
    malformation the block law meets.

    AC-EDMG2: a block opened and never closed quotes every remaining line and
    is never named, so the document silently loses rows. It is refused here
    naming the line the block was opened on.
    AC-EDMG3: a block opened with FOUR backticks and carrying a THREE-backtick
    line toggled twice - the quoted row was counted and the row after the block
    was swallowed. A closing candidate shorter than its opening mark is content
    inside the block, and the dialect is refused here naming both widths."""
    lines = text.splitlines()
    mask = [False] * len(lines)
    open_len = 0
    open_line = 0
    problem = None
    for index, line in enumerate(lines):
        if open_len:
            mask[index] = True
            close = FENCE_CLOSE_RE.match(line)
            if close:
                width = len(close.group(1))
                if width >= open_len:
                    open_len = 0
                    open_line = 0
                elif problem is None:
                    problem = {"code": CODE_NEST, "line": index + 1,
                               "open_line": open_line,
                               "open_marker": open_len, "inner_marker": width}
            continue
        opening = FENCE_OPEN_RE.match(line)
        if opening:
            mask[index] = True
            open_len = len(opening.group(1))
            open_line = index + 1
    if open_len and problem is None:
        problem = {"code": CODE_FENCE, "line": open_line,
                   "open_marker": open_len}
    return mask, problem


def doc_rows(text, patterns=None):
    """Matrix table data rows of a composed document, FENCE-AWARE (R2616) and
    TABLE-AWARE (R2621).

    AC-EDMF1: a quoted data row inside a ``` block is not a matrix row.
    AC-EDMG1: R2616 measured a data-shaped row in a SECOND table (fenced or
    not) still counted, so a document whose only difference was a second table
    read ROWS-MISMATCH. Only rows of the FIRST table introduced by the shipped
    matrix title are matrix rows."""
    patterns = patterns or SM.load_patterns()
    title = patterns["labels"]["matrix_title"].strip()
    lines = text.splitlines()
    mask, _problem = fence_scan(text)
    start = None
    for index, line in enumerate(lines):
        if mask[index] or line.strip() != title:
            continue
        follow = index + 1
        while (follow < len(lines) and not mask[follow]
               and not lines[follow].strip()):
            follow += 1
        if follow < len(lines) and not mask[follow] \
                and lines[follow].startswith("|"):
            start = follow
            break
    if start is None:
        return 0
    count = 0
    index = start + 1
    if (index < len(lines) and not mask[index]
            and lines[index].startswith("|")
            and is_separator_row(lines[index])):
        index += 1
    while index < len(lines):
        line = lines[index]
        if mask[index]:
            index += 1
            continue
        if not line.strip():
            # A blank line inside a table is a doctoring artefact (deleting a
            # row leaves one behind), not the end of the matrix table.
            index += 1
            continue
        if not line.startswith("|"):
            break
        if ROW_RE.match(line):
            count += 1
        elif is_separator_row(line):
            # AC-EDMH3: a separator row reappearing inside the table neither
            # restarts nor ends it.
            pass
        elif DATA_HEAD_RE.match(line):
            # AC-EDMH1: a data-shaped row whose CELL COUNT is wrong is skipped
            # as one non-row and every well-formed row after it is still
            # counted, so the count falls by one instead of to zero.
            pass
        else:
            # A row that is neither data nor separator is the header of
            # ANOTHER table: the first table ends here (AC-EDMG1, unchanged by
            # AC-EDMH2).
            break
        index += 1
    return count


def registry_counts():
    return len(RA.SUITES), sum(c for _, _, c in RA.SUITES)


def newest_pass_leg_scanned(qa_dir=None, ceiling=None):
    """Newest qa/*.log whose RUNNER line reads PASS, asked of the shipped
    parse_evidence. Returns (path, run, walk) where walk names the cost that
    was paid: how many candidate files were listed and how many were actually
    decoded before the answer was found (AC-EDMB2 - the walk stops at the
    first PASS leg, so its cost is bounded and now visible).

    AC-EDMC3: `ceiling` bounds how many candidates may be decoded at all. A
    pile with no PASS leg stops at the ceiling, reports bounded=True and
    returns None rather than decoding every file it can list."""
    qa_dir = qa_dir or QA_DIR
    ceiling = WALK_CEILING if ceiling is None else int(ceiling)
    if not os.path.isdir(qa_dir):
        return None, None, {"considered": 0, "decoded": 0}
    paths = [os.path.join(qa_dir, name) for name in os.listdir(qa_dir)
             if name.endswith(".log")]
    paths.sort(key=lambda p: (-os.path.getmtime(p), os.path.basename(p)))
    decoded = 0
    for path in paths:
        if decoded >= ceiling:
            # AC-EDMC3: the bound ENGAGED, so it is named on the walk. When it
            # does not engage the walk keeps the exact R2602 shape
            # {"considered", "decoded"} and nothing else.
            return None, None, {"considered": len(paths), "decoded": decoded,
                                "ceiling": ceiling, "bounded": True}
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


def is_separator_row(cells_text):
    """True when a table row is a SEPARATOR: every non-space character is
    punctuation (AC-EDMD1 accepted ONE repeated punctuation character; R2608
    AC-EDME1 widens it to ANY mix of punctuation, so a row drawn "-=-=" is a
    separator too instead of being called absent). A content row always
    carries a letter or a digit, so nothing readable is swallowed."""
    stripped = cells_text.replace("|", "").strip()
    if not stripped:
        return False
    chars = set(stripped) - set(" ")
    if not chars:
        return False
    if chars <= SEPARATOR_CHARS:
        return True
    if len(chars) == 1:
        only = next(iter(chars))
        return not only.isalnum()
    return all(not ch.isalnum() for ch in chars)


def title_tables(text, patterns):
    """Every matrix TABLE introduced by the shipped title OUTSIDE fenced code
    blocks, as (header_cells, separator_cells, signature).

    AC-EDME2: a title inside a fence is quoted sample text, not a table.
    AC-EDME3: a title line that introduces no table at all (a bare repeat,
    trailing whitespace or not) is not a table title. Two titles that
    introduce the SAME table read as one, and two that introduce DIFFERENT
    tables read as two - that is what makes AC-EDMD4's repeated real table a
    repeat while a quoted or bare repeat is not."""
    title = patterns["labels"]["matrix_title"].strip()
    lines = text.splitlines()
    found = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or line.strip() != title:
            continue
        header = None
        header_text = None
        separator = None
        for follow in lines[index + 1:]:
            stripped = follow.strip()
            if stripped.startswith("```"):
                break
            if not follow.startswith("|"):
                if stripped:
                    break
                continue
            if header is None:
                header = follow.count("|") - 1
                header_text = "|".join(cell.strip() for cell in
                                       follow.strip().strip("|").split("|"))
                continue
            if is_separator_row(follow):
                separator = follow.count("|") - 1
            break
        if header is None:
            continue
        # AC-EDMF2: a table is identified by its HEADER TEXT and its width.
        # R2608 put the separator width in the signature, so the same table
        # repeated WITHOUT its separator row counted as a second table and
        # read TITLE-REPEATED. The separator is a row of a table, not part of
        # its identity.
        found.append((header, separator, (header_text, header)))
    return found


def matrix_title_count(text, patterns):
    """How many DISTINCT matrix tables the shipped title introduces outside
    fenced blocks (AC-EDMD4 count, refined by AC-EDME2/AC-EDME3)."""
    signatures = set(sig for _, _, sig in title_tables(text, patterns))
    return len(signatures)


def matrix_shape(text, patterns):
    """(header_cells, separator_cells) of the FIRST matrix table outside
    fenced blocks, each None when that row is absent. Read by POSITION under
    the shipped matrix title, never by a row shape guess, so a table that
    changed its column layout is named rather than silently counted as zero
    rows (AC-EDMB4) and a SEPARATOR that disagrees with its own header is a
    shape answer instead of a content word (AC-EDMC1, widened by AC-EDMD1 and
    again by AC-EDME1)."""
    found = title_tables(text, patterns)
    if not found:
        return None, None
    header, separator, _ = found[0]
    return header, separator


def matrix_header_cells(text, patterns):
    """Header cells only - the shape R2602 published, kept byte for byte."""
    return matrix_shape(text, patterns)[0]


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


def _walk_miss(doc_path, source, walk):
    """AC-EDME4: a walk whose DECLARED ceiling was reached before a PASS leg
    was found is starved and says so with the ceiling named; a pile whose
    every candidate was decoded is an honest miss and reads RED-LEG. Before
    this, both states shared one verdict word and only the walk block told
    them apart."""
    walk = walk or {"considered": 0, "decoded": 0}
    if walk.get("bounded"):
        return {"verdict": WORD_CEILING, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_CEILING,
                "ceiling": walk.get("ceiling"), "evidence_source": source,
                "walk": walk,
                "reason": "the walk reached its ceiling of %s before a PASS"
                          " leg was found" % walk.get("ceiling")}
    return {"verdict": WORD_RED, "doc": rel(doc_path), "exit": 3,
            "written": False, "reason": "no runner leg",
            "evidence_source": source, "walk": walk,
            "bound_reached": False}


def report(doc_path=None, evidence_path=None, qa_dir=None, ceiling=None):
    doc_path = doc_path or DOC
    if not os.path.exists(doc_path):
        return {"verdict": WORD_NONE, "doc": rel(doc_path),
                "exit": 2, "written": False}
    current = read_text(doc_path)
    patterns = SM.load_patterns()
    # AC-EDMG2/AC-EDMG3: a malformed fence is a SHAPE answer that names itself,
    # and it comes before any row count, because a blind toggle either swallows
    # the rest of the document or counts a quoted row.
    _mask, fence_problem = fence_scan(current)
    if fence_problem is not None:
        nested = fence_problem["code"] == CODE_NEST
        answer = {"doc": rel(doc_path), "exit": 3, "written": False,
                  "code": fence_problem["code"],
                  "line": fence_problem["line"],
                  "open_marker": fence_problem["open_marker"]}
        if nested:
            answer["inner_marker"] = fence_problem["inner_marker"]
            answer["open_line"] = fence_problem["open_line"]
            answer["reason"] = ("a %d-backtick fence at line %d carries a"
                                " %d-backtick closing mark"
                                % (fence_problem["open_marker"],
                                   fence_problem["open_line"],
                                   fence_problem["inner_marker"]))
            answer.update({"verdict": WORD_NEST, "titles": None})
        else:
            answer["reason"] = ("the fence opened on line %d is never closed"
                                % fence_problem["line"])
            answer["verdict"] = WORD_FENCE
        return answer
    rows, criteria = registry_counts()
    # AC-EDMD4: a document carrying the matrix title more than once was read
    # as its FIRST table with every other table dropped in silence.
    titles = matrix_title_count(current, patterns)
    if titles > 1:
        return {"verdict": WORD_TITLE, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_TITLE, "titles": titles,
                "table_title": patterns["labels"]["matrix_title"],
                "reason": "the matrix title appears %d times" % titles}
    header, separator = matrix_shape(current, patterns)
    # AC-EDMC2: no matrix table is its own answer, naming what is absent.
    if header is None:
        return {"verdict": WORD_TABLE, "doc": rel(doc_path), "exit": 2,
                "written": False, "code": CODE_TABLE,
                "table_title": patterns["labels"]["matrix_title"],
                "reason": "the matrix table is absent from this document"}
    # AC-EDMD2: a header with no separator row is a shape answer naming the
    # missing separator, not a content word.
    if separator is None:
        return {"verdict": WORD_SEP, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_SEP,
                "header_cells": header, "cells": header,
                "expected_cells": MATRIX_CELLS,
                "reason": "the matrix header carries no separator row"}
    # AC-EDMC1: a separator whose width disagrees with its own header is a
    # SHAPE answer naming BOTH widths, not a content drift.
    if separator is not None and separator != header:
        return {"verdict": WORD_HEADER, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_HEADER,
                "header_cells": header, "separator_cells": separator,
                "cells": header, "expected_cells": MATRIX_CELLS,
                "reason": "matrix separator carries %d cells under a %d-cell"
                          " header" % (separator, header)}
    if header != MATRIX_CELLS:
        return {"verdict": WORD_HEADER, "doc": rel(doc_path), "exit": 3,
                "written": False, "code": CODE_HEADER, "cells": header,
                "header_cells": header, "expected_cells": MATRIX_CELLS,
                "reason": "matrix table carries %d cells, expected %d"
                          % (header, MATRIX_CELLS)}
    have_rows = doc_rows(current)
    walk = None
    # AC-EDMC4: the caller is always told WHICH source answered, and a source
    # it handed over but that was not used is named rather than ignored.
    if evidence_path is None:
        # AC-EDMD3: a ceiling that cannot read even one candidate is refused
        # by name, so a starved walk never looks like an honest empty pile.
        if ceiling is not None and int(ceiling) < 1:
            return {"verdict": WORD_CEILING, "doc": rel(doc_path), "exit": 3,
                    "written": False, "code": CODE_CEILING,
                    "ceiling": int(ceiling), "evidence_source": "walk",
                    "reason": "a ceiling of %d cannot read one candidate"
                              % int(ceiling)}
        source = "walk"
        evidence_path, _, walk = newest_pass_leg_scanned(qa_dir, ceiling)
        if evidence_path is None:
            return _walk_miss(doc_path, source, walk)
    else:
        source = "explicit"
        evidence_path = (evidence_path if os.path.isabs(evidence_path)
                         else os.path.join(REPO, evidence_path))
    status, run = SM.parse_evidence(evidence_path)
    if run is None or run["verdict"] != "PASS":
        return {"verdict": WORD_RED, "doc": rel(doc_path),
                "evidence": rel(evidence_path), "exit": 3,
                "written": False, "walk": walk, "evidence_source": source,
                "reason": (run or {}).get("verdict", "no RUNNER line")}
    code, message = shipped_check(doc_path, evidence_path)
    result = {"doc": rel(doc_path), "evidence": rel(evidence_path),
              "doc_rows": have_rows, "registry_rows": rows,
              "registry_criteria": criteria,
              "leg_green": run["green"], "leg_total": run["total"],
              "shipped_check": code, "written": False,
              "evidence_source": source}
    if qa_dir is not None:
        result["qa_dir_given"] = True
        result["qa_dir_used"] = source != "explicit"
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


def write(doc_path=None, evidence_path=None, qa_dir=None, stamp_from=None,
          ceiling=None):
    doc_path = doc_path or DOC
    if not os.path.exists(doc_path) and stamp_from is not None:
        return _compose_missing(doc_path, evidence_path, qa_dir, stamp_from,
                                ceiling)
    result = report(doc_path, evidence_path, qa_dir, ceiling)
    if result["verdict"] in (WORD_CURRENT, WORD_NONE, WORD_RED,
                             "READABILITY-REFUSED", WORD_HEADER, WORD_SEP,
                             WORD_TITLE, WORD_CEILING, WORD_FENCE, WORD_NEST):
        return result
    # A TABLE-MISSING answer (AC-EDMC2) carries no resolved evidence because
    # the shape was refused before the leg was looked at, so the leg is
    # resolved here rather than assumed to be in the result.
    if "evidence" in result:
        leg = os.path.join(REPO, result["evidence"])
    elif evidence_path is not None:
        leg = (evidence_path if os.path.isabs(evidence_path)
               else os.path.join(REPO, evidence_path))
    else:
        leg, run, walk = newest_pass_leg_scanned(qa_dir, ceiling)
        if leg is None:
            return _walk_miss(doc_path, "walk", walk)
        result["evidence"] = rel(leg)
        result["walk"] = walk
        result["evidence_source"] = "walk"
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


def _compose_missing(doc_path, evidence_path, qa_dir, stamp_from,
                     ceiling=None):
    """AC-EDMB3: compose a document that does not exist from a --stamp-from
    source. The source lends the stamp and the recorded borrow ONLY; the rows
    and the evidence line come from the CURRENT registry and the named leg.
    A red leg, a missing source or a failed read-back leaves NO file behind,
    which is the pre-state of a document that never existed."""
    stamp_from = (stamp_from if os.path.isabs(stamp_from)
                  else os.path.join(REPO, stamp_from))
    walk = None
    if evidence_path is None:
        # AC-EDMD3 on the compose path: same refusal, no file created.
        if ceiling is not None and int(ceiling) < 1:
            return {"verdict": WORD_CEILING, "doc": rel(doc_path), "exit": 3,
                    "written": False, "code": CODE_CEILING,
                    "ceiling": int(ceiling), "evidence_source": "walk",
                    "reason": "a ceiling of %d cannot read one candidate"
                              % int(ceiling)}
        evidence_path, _, walk = newest_pass_leg_scanned(qa_dir, ceiling)
        if evidence_path is None:
            return _walk_miss(doc_path, "walk", walk)
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
    parser.add_argument("--ceiling", type=int, default=None)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.write and args.check:
        print("FAIL flags: E_EDM_BAD_FLAGS --write and --check are exclusive")
        return 3
    if args.write:
        result = write(args.doc, args.evidence, args.qa_dir,
                       args.stamp_from, args.ceiling)
    else:
        result = report(args.doc, args.evidence, args.qa_dir, args.ceiling)
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
        elif result["verdict"] == WORD_TABLE:
            print("  %s %s table=%s"
                  % (result["code"], result["reason"], result["table_title"]))
        elif result["verdict"] == WORD_SEP:
            print("  %s %s header-cells=%d"
                  % (result["code"], result["reason"],
                     result["header_cells"]))
        elif result["verdict"] == WORD_TITLE:
            print("  %s %s titles=%d"
                  % (result["code"], result["reason"], result["titles"]))
        elif result["verdict"] == WORD_CEILING:
            print("  %s %s ceiling=%d"
                  % (result["code"], result["reason"], result["ceiling"]))
        elif result["verdict"] == WORD_FENCE:
            print("  %s %s line=%d marker=%s"
                  % (result["code"], result["reason"], result["line"],
                     "`" * result["open_marker"]))
        elif result["verdict"] == WORD_NEST:
            print("  %s %s open-line=%d open-marker=%s inner-marker=%s"
                  % (result["code"], result["reason"],
                     result["open_line"], "`" * result["open_marker"],
                     "`" * result["inner_marker"]))
        elif result["verdict"] == WORD_RED:
            print("  evidence=%s reason=%s%s"
                  % (result.get("evidence"), result.get("reason"),
                     " bound-reached" if result.get("bound_reached") else ""))
        elif result["verdict"] == WORD_WRITTEN:
            print("  %d bytes, %d rows, evidence=%s"
                  % (result["bytes"], result["doc_rows"],
                     result["evidence"]))
        if result.get("evidence_source"):
            print("  evidence-source=%s%s"
                  % (result["evidence_source"],
                     " (qa-dir given, not used)"
                     if result.get("qa_dir_given")
                     and result.get("qa_dir_used") is False else ""))
        if result.get("walk"):
            print("  evidence-walk considered=%d decoded=%d ceiling=%d%s"
                  % (result["walk"]["considered"], result["walk"]["decoded"],
                     result["walk"].get("ceiling", WALK_CEILING),
                     " BOUND-REACHED" if result["walk"].get("bounded")
                     else ""))
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main(sys.argv))