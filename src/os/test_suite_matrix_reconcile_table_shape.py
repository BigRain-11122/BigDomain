"""AC-EDMC1..AC-EDMC6 suite for the matrix reconciliation table-shape face.

Criteria were pinned in state/queue/tech.md:636 at R2602 BEFORE this code
existed, from four limits MEASURED there and re-measured at HEAD before any
byte was written: a separator row of four cells under a six-cell header read
header_cells=6 and fell through to a CONTENT word, a document carrying no
matrix table at all read ROWS-MISMATCH rows=0, an explicit --evidence plus a
--qa-dir answered without naming which source answered, and a qa directory
with no PASS leg decoded every candidate it could list (measured 40/40).

AC-EDMC1 a separator row whose width disagrees with the header refuses by
         HEADER-SHAPE naming BOTH widths instead of reading a content word.
AC-EDMC2 a document with no matrix table refuses with its own word naming the
         missing table instead of reading ROWS-MISMATCH.
AC-EDMC3 the candidate walk is bounded by a declared ceiling, stops there and
         says so, so a pile with no PASS leg cannot be decoded end to end.
AC-EDMC4 an explicit --evidence together with --qa-dir reports which source
         it used and never ignores one in silence.
AC-EDMC5 every R2602 answer survives beside the new ones (all seven verdict
         words reachable on fixtures, both counts, one word on the CLI, the
         exit codes).
AC-EDMC6 pure ASCII, stdlib only, no clock, no network, its own reconcile
         label and its own suite.

Every proof runs through the shipped faces (suite_matrix.main --check,
suite_matrix.parse_evidence, suite_matrix.doc_evidence_face,
reconcile_all.SUITES). Every doctoring happens in a private temporary
directory, never in docs/.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import ast
import io
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import suite_matrix_reconcile as SMR  # noqa: E402
import suite_matrix as SM  # noqa: E402
import reconcile_all as RA  # noqa: E402

MODULE = os.path.join(BASE, "suite_matrix_reconcile.py")
SUITE = os.path.join(BASE, "test_suite_matrix_reconcile_table_shape.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
LABEL = "os-suite-matrix-reconcile-table-shape"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
R2602_WORDS = ("DOC-CURRENT", "ROWS-MISMATCH", "STALE-CONTENT", "RED-LEG",
               "NO-DOC", "EVIDENCE-FACE", "HEADER-SHAPE")


def check(ok, label):
    print("  %s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def pass_legs():
    """Every qa/*.log whose RUNNER line reads PASS, newest first."""
    found = []
    for name in os.listdir(QA_DIR):
        if not name.endswith(".log"):
            continue
        path = os.path.join(QA_DIR, name)
        try:
            _, run = SM.parse_evidence(path)
        except (OSError, UnicodeDecodeError):
            continue
        if run and run["verdict"] == "PASS":
            found.append((os.path.getmtime(path), path))
    found.sort(key=lambda pair: -pair[0])
    return [path for _, path in found]


def matrix_title():
    return SM.load_patterns()["labels"]["matrix_title"]


def doc_without_table(text):
    title = matrix_title().strip()
    kept = []
    inside = False
    for line in text.splitlines(True):
        if line.strip() == title:
            inside = True
            continue
        if inside and line.startswith("|"):
            continue
        kept.append(line)
    return "".join(kept)


def doc_with_separator(text, width):
    """The real document with its matrix SEPARATOR rewritten to `width` cells
    and the header left untouched."""
    title = matrix_title().strip()
    lines = text.splitlines(True)
    inside = False
    for index, line in enumerate(lines):
        if line.strip() == title:
            inside = True
            continue
        if inside and line.startswith("|---"):
            lines[index] = "|" + "|".join(["---"] * width) + "|\n"
            return "".join(lines)
    return None


def doc_with_one_row_removed(text):
    match = SMR.ROW_RE.search(text)
    if match is None:
        return None
    return text[:match.start()] + text[match.end():]


def cli_first_word(argv):
    buffer = io.StringIO()
    stdout = sys.stdout
    sys.stdout = buffer
    try:
        code = SMR.main(["suite_matrix_reconcile.py"] + argv)
    finally:
        sys.stdout = stdout
    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    return code, (lines[0].split()[0] if lines else None), \
        buffer.getvalue()


def criterion_edmc1(work, text, leg):
    """AC-EDMC1: a separator/header width disagreement is a SHAPE answer."""
    cases = []
    for width in (4, 8):
        doctored = doc_with_separator(text, width)
        if doctored is None:
            return check(False, "the real document carries a matrix"
                                " separator row to doctor")
        doc = os.path.join(work, "sep%d.md" % width)
        write_text(doc, doctored)
        shape = SMR.matrix_shape(read(doc), SM.load_patterns())
        result = SMR.report(doc, leg)
        cases.append((width, shape, result))
    ok = True
    for width, shape, result in cases:
        ok &= check(shape == (6, width),
                    "separator width %d reads shape=(6, %d) got %r"
                    % (width, width, shape))
        ok &= check(result["verdict"] == SMR.WORD_HEADER,
                    "separator width %d verdict HEADER-SHAPE got %s"
                    % (width, result["verdict"]))
        ok &= check(result["header_cells"] == 6
                    and result["separator_cells"] == width,
                    "separator width %d names BOTH widths (%r)"
                    % (width, (result.get("header_cells"),
                               result.get("separator_cells"))))
        ok &= check(result["exit"] == 3,
                    "separator width %d exits 3 got %d"
                    % (width, result["exit"]))
    return ok


def criterion_edmc2(work, text, leg):
    """AC-EDMC2: no matrix table is its own word, and write() can restore it."""
    doc = os.path.join(work, "no-table.md")
    write_text(doc, doc_without_table(text))
    shape = SMR.matrix_shape(read(doc), SM.load_patterns())
    result = SMR.report(doc, leg)
    ok = check(shape == (None, None), "no table reads shape=(None, None)"
               " got %r" % (shape,))
    ok &= check(result["verdict"] == SMR.WORD_TABLE,
                "no table verdict TABLE-MISSING got %s" % result["verdict"])
    ok &= check(result["verdict"] != SMR.WORD_ROWS,
                "no table does NOT read ROWS-MISMATCH")
    ok &= check(result.get("table_title") == matrix_title(),
                "no table names the missing table (%r)"
                % (result.get("table_title"),))
    ok &= check(result["exit"] == 2, "no table exits 2 got %d" % result["exit"])
    written = SMR.write(doc, leg)
    ok &= check(written["verdict"] == SMR.WORD_WRITTEN
                and written["written"] is True,
                "write() restores a table-less document (%s)"
                % written["verdict"])
    ok &= check(SMR.matrix_shape(read(doc), SM.load_patterns())[0] == 6,
                "restored document carries a six-cell header")
    return ok


def criterion_edmc3(work, text, leg):
    """AC-EDMC3: the walk is bounded by a declared ceiling and says so."""
    dump = os.path.join(work, "qa-dump")
    os.makedirs(dump)
    for index in range(40):
        write_text(os.path.join(dump, "x%02d.log" % index), "STATUS unknown\n")
    ceiling = 8
    path, run, walk = SMR.newest_pass_leg_scanned(dump, ceiling)
    ok = check(path is None and run is None,
               "no-PASS pile returns no leg under a ceiling")
    ok &= check(walk["decoded"] == ceiling and walk["bounded"] is True,
                "walk stops AT the ceiling decoded=%d bounded=%s"
                % (walk["decoded"], walk["bounded"]))
    ok &= check(walk["considered"] == 40,
                "walk still reports what it listed (%d)" % walk["considered"])
    ok &= check(walk["ceiling"] == ceiling,
                "walk declares its ceiling (%r)" % walk["ceiling"])
    doc = os.path.join(work, "bounded.md")
    write_text(doc, text)
    result = SMR.report(doc, None, dump, ceiling)
    ok &= check(result["verdict"] == SMR.WORD_RED
                and result.get("bound_reached") is True,
                "report says BOUND-REACHED on a capped pile (%s)"
                % result["verdict"])
    ok &= check(isinstance(SMR.WALK_CEILING, int) and SMR.WALK_CEILING > 0,
                "a declared default ceiling exists (%r)" % SMR.WALK_CEILING)
    return ok


def criterion_edmc4(work, text, leg):
    """AC-EDMC4: both evidence sources are named, never silently merged."""
    doc = os.path.join(work, "both.md")
    write_text(doc, text)
    both = SMR.report(doc, leg, QA_DIR)
    ok = check(both.get("evidence_source") == "explicit",
               "explicit leg wins and is named (%r)"
               % (both.get("evidence_source"),))
    ok &= check(both.get("qa_dir_given") is True
                and both.get("qa_dir_used") is False,
                "the unused qa-dir is named rather than ignored (%r/%r)"
                % (both.get("qa_dir_given"), both.get("qa_dir_used")))
    walked = SMR.report(doc, None, QA_DIR)
    ok &= check(walked.get("evidence_source") == "walk",
                "a walk-only reading names itself walk (%r)"
                % (walked.get("evidence_source"),))
    code, word, out = cli_first_word(["--doc", doc, "--qa-dir", QA_DIR])
    ok &= check("evidence-source=walk" in out,
                "the CLI prints the source it used")
    code2, word2, out2 = cli_first_word(["--doc", doc, "--evidence", leg,
                                         "--qa-dir", QA_DIR])
    ok &= check("qa-dir given, not used" in out2,
                "the CLI names the qa-dir it did not use")
    return ok


def criterion_edmc5(work, text, leg):
    """AC-EDMC5: the seven R2602 answers survive beside the new ones."""
    ok = True
    consts = {"DOC-CURRENT": SMR.WORD_CURRENT,
              "ROWS-MISMATCH": SMR.WORD_ROWS,
              "STALE-CONTENT": SMR.WORD_STALE,
              "RED-LEG": SMR.WORD_RED,
              "NO-DOC": SMR.WORD_NONE,
              "EVIDENCE-FACE": SMR.WORD_EVID,
              "HEADER-SHAPE": SMR.WORD_HEADER}
    for word, value in consts.items():
        ok &= check(value == word,
                    "word %s still in the shipped vocabulary (got %r)"
                    % (word, value))
    ok &= check(SMR.WORD_TABLE == "TABLE-MISSING"
                and SMR.WORD_TABLE not in consts,
                "the new word is additive, not a rename")
    # reachable answers and their exit codes, each on its own fixture
    patterns = SM.load_patterns()
    recorded = SM.doc_evidence_face(text, patterns)
    recorded_path = (os.path.join(REPO, recorded) if recorded else leg)
    current = SMR.report(DOC, recorded_path)
    ok &= check(current["verdict"] == SMR.WORD_CURRENT
                and current["exit"] == 0,
                "DOC-CURRENT still reachable with exit 0 (%s)"
                % current["verdict"])
    missing = SMR.report(os.path.join(work, "absent.md"), leg)
    ok &= check(missing["verdict"] == SMR.WORD_NONE and missing["exit"] == 2,
                "NO-DOC still exits 2 (%s)" % missing["verdict"])
    rows_doc = os.path.join(work, "rows.md")
    write_text(rows_doc, doc_with_one_row_removed(text))
    rows = SMR.report(rows_doc, leg)
    ok &= check(rows["verdict"] == SMR.WORD_ROWS and rows["exit"] == 2,
                "ROWS-MISMATCH still exits 2 (%s)" % rows["verdict"])
    ok &= check(rows.get("doc_rows") == rows.get("registry_rows", 0) - 1,
                "ROWS-MISMATCH still names BOTH counts (%r/%r)"
                % (rows.get("doc_rows"), rows.get("registry_rows")))
    stale_doc = os.path.join(work, "stale.md")
    write_text(stale_doc, text + "\nextra trailing prose line\n")
    stale = SMR.report(stale_doc, leg)
    ok &= check(stale["verdict"] == SMR.WORD_STALE and stale["exit"] == 2,
                "STALE-CONTENT still exits 2 (%s)" % stale["verdict"])
    others = [p for p in pass_legs() if SMR.rel(p) != recorded]
    if others:
        evid = SMR.report(DOC, others[0])
        ok &= check(evid["verdict"] == SMR.WORD_EVID
                    and evid["exit"] == 2,
                    "EVIDENCE-FACE still exits 2 (%s)" % evid["verdict"])
    red_path = os.path.join(work, "red.log")
    write_text(red_path, "RUNNER FAIL (5 failed assertions)\n")
    red = SMR.report(DOC, red_path)
    ok &= check(red["verdict"] == SMR.WORD_RED and red["exit"] == 3,
                "RED-LEG still exits 3 (%s)" % red["verdict"])
    for argv, expected in (
            (["--doc", rows_doc, "--evidence", leg], "ROWS-MISMATCH"),
            (["--doc", os.path.join(work, "absent.md"),
              "--evidence", leg], "NO-DOC")):
        code, word, out = cli_first_word(argv)
        ok &= check(word == expected,
                    "CLI prints ONE verdict word for %s (got %r)"
                    % (expected, word))
    return ok


def criterion_edmc6(work, text, leg):
    """AC-EDMC6: ASCII, stdlib only, no clock, own label, own suite."""
    source = read(MODULE)
    suite = read(SUITE)
    ok = check(all(ord(ch) < 128 for ch in source),
               "module is pure ASCII")
    ok &= check(all(ord(ch) < 128 for ch in suite), "suite is pure ASCII")
    # Imports are read from the SYNTAX TREE, not a line regex: a docstring
    # line that merely begins with a word like "from" is not an import.
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    ok &= check(not [name for name in imports if name in NET],
                "module imports no clock/network face (%r)"
                % (sorted(imports),))
    allowed = {"argparse", "contextlib", "io", "json", "os", "re", "sys",
               "reconcile_all", "suite_matrix", "matrix_stamp_provenance_line"}
    ok &= check(imports <= allowed,
                "module imports stdlib and shipped faces only (%r)"
                % (sorted(imports - allowed),))
    labels = {row[0] for row in RA.SUITES}
    ok &= check(LABEL in labels,
                "its own reconcile label is registered (%r)" % (LABEL,))
    ok &= check("os-suite-matrix-reconcile" in labels,
                "the base reconcile label is still registered")
    wired = [row for row in RA.SUITES if row[0] == LABEL]
    ok &= check(len(wired) == 1 and wired[0][2] == 6,
                "its own label carries six criteria (%r)" % (wired,))
    ok &= check(wired and os.path.basename(wired[0][1]) ==
                os.path.basename(SUITE),
                "the label points at THIS suite")
    ok &= check("suite_matrix_reconcile" in os.path.basename(MODULE),
                "the module keeps its own reconcile identity")
    return ok


def main():
    text = read(DOC)
    legs = pass_legs()
    if not legs:
        print("FAIL no RUNNER PASS leg under qa/")
        return 1
    leg = legs[0]
    work = tempfile.mkdtemp(prefix="edmc-")
    ok = True
    try:
        print("[AC-EDMC1] separator width is a shape answer")
        ok &= criterion_edmc1(work, text, leg)
        print("[AC-EDMC2] a missing matrix table is its own word")
        ok &= criterion_edmc2(work, text, leg)
        print("[AC-EDMC3] the candidate walk is bounded and says so")
        ok &= criterion_edmc3(work, text, leg)
        print("[AC-EDMC4] both evidence sources are named")
        ok &= criterion_edmc4(work, text, leg)
        print("[AC-EDMC5] the R2602 answers survive")
        ok &= criterion_edmc5(work, text, leg)
        print("[AC-EDMC6] ASCII, stdlib, no clock, own label")
        ok &= criterion_edmc6(work, text, leg)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("SUITE %s 6/6" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())