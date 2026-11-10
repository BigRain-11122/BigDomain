"""AC-EDME1..AC-EDME6 suite for the suite-matrix reconciliation FENCE face
(R2608).

Criteria were pinned in state/queue/tech.md:640 at R2606 BEFORE this code
existed, from four limits MEASURED there with
src/os/limits_suite_matrix_reconcile_shape_next_R2606.py and re-measured at
the start of R2608.

What this proves: a separator drawn with MIXED punctuation is a separator and
a width disagreement against its header refuses by HEADER-SHAPE naming BOTH
widths; a matrix title inside a fenced code block is quoted text and not a
table title; a title that introduces no table (a bare repeat differing only
by trailing whitespace) is not counted twice; a walk that reached its
DECLARED ceiling before a PASS leg was found reads CEILING-STARVED naming the
ceiling while a pile whose every candidate was decoded reads RED-LEG; every
R2606 answer survives on the same fixtures.

All doctoring happens in private temporary directories, never in docs/ or
qa/. Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
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

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "suite_matrix_reconcile.py")
SELFTEST = os.path.abspath(__file__)
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-suite-matrix-reconcile-fence",'
WIRED_SUITE = '"test_suite_matrix_reconcile_fence.py"),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")


def check(ok, label):
    # The criterion marker must start the line: the shipped capture digests
    # lines that BEGIN with "PASS "/"FAIL ", so an indented marker would land
    # an empty digest (a trap this repo has already paid for).
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def leg(kind):
    """Newest qa/*.log whose RUNNER answer is `kind` (measured, not canned)."""
    paths = [os.path.join(QA_DIR, n) for n in os.listdir(QA_DIR)
             if n.endswith(".log")]
    paths.sort(key=lambda p: (-os.path.getmtime(p), os.path.basename(p)))
    for path in paths:
        try:
            _, run = SM.parse_evidence(path)
        except (OSError, UnicodeDecodeError):
            continue
        if kind == "PASS":
            if run and run["verdict"] == "PASS":
                return path, run
        elif run is None or run["verdict"] != "PASS":
            return path, run or {"verdict": "no RUNNER line"}
    return None, None


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def title_of():
    return SM.load_patterns()["labels"]["matrix_title"]


def _table_lines(lines):
    """(header_index, separator_index) of the FIRST matrix table, located by
    position under the shipped title - never by a shape guess."""
    title = title_of().strip()
    for index, line in enumerate(lines):
        if line.strip() != title:
            continue
        header = None
        for j in range(index + 1, len(lines)):
            if not lines[j].startswith("|"):
                if lines[j].strip():
                    return None
                continue
            if header is None:
                header = j
                continue
            return header, j
        return None
    return None


def temp_copy(directory, name, doctor=None):
    target = os.path.join(directory, name)
    shutil.copyfile(DOC, target)
    if doctor is not None:
        text = read(target)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(doctor(text))
    return target


def doctor_sep(cells, pattern="-="):
    """Rewrite the separator row with `cells` columns drawn from `pattern`."""
    def apply(text):
        lines = text.splitlines(True)
        where = _table_lines(lines)
        if not where:
            raise AssertionError("E_EDME_SUITE_NO_TABLE")
        _, sep = where
        drawn = ""
        while len(drawn) < 3 * cells:
            drawn += pattern
        drawn = drawn[:3 * cells]
        row = "|"
        for index in range(cells):
            row += drawn[index * 3:(index + 1) * 3] + "|"
        lines[sep] = row + "\n"
        return "".join(lines)
    return apply


def doctor_fenced_title(text):
    """Append the shipped title inside a fenced code block, with a table."""
    return (text + "\n```\n" + title_of().strip() + "\n"
            "| a | b | c | d | e | f |\n|---|---|---|---|---|---|\n"
            "| 1 | x | y | 6 | green | 0.1 |\n```\n")


def doctor_bare_title_trailing(text):
    """Append the title alone, differing only by trailing whitespace."""
    return text + "\n" + title_of().strip() + "   \n"


def one_word_cli(args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SMR.main(["suite_matrix_reconcile.py"] + args)
    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    return code, (lines[0].split()[0] if lines else ""), buffer.getvalue()


def verify():
    green, greendata = leg("PASS")
    red, reddata = leg("FAIL")
    patterns = SM.load_patterns()
    results = []
    workdir = tempfile.mkdtemp(prefix="edme-")
    try:
        # AC-EDME1: a separator drawn with MIXED punctuation is a separator,
        # and a width disagreement refuses by HEADER-SHAPE naming BOTH widths.
        narrow = temp_copy(workdir, "mixed-narrow.md", doctor_sep(2))
        wide_doc = temp_copy(workdir, "mixed-wide.md", doctor_sep(6))
        narrow_rep = SMR.report(narrow, green)
        wide_shape = SMR.matrix_shape(read(wide_doc), patterns)
        wide_rep = SMR.report(wide_doc, green)
        sea_shape = SMR.matrix_shape(read(narrow), patterns)
        results.append(check(
            sea_shape == (6, 2)
            and narrow_rep["verdict"] == SMR.WORD_HEADER
            and narrow_rep["exit"] == 3
            and narrow_rep.get("header_cells") == 6
            and narrow_rep.get("separator_cells") == 2
            and "6" in narrow_rep.get("reason", "")
            and "2" in narrow_rep.get("reason", "")
            and wide_shape == (6, 6)
            and wide_rep["verdict"] not in (SMR.WORD_HEADER, SMR.WORD_SEP),
            "AC-EDME1 mixed-separator narrow-shape=%s -> %s cells=%s/%s,"
            " wide-shape=%s verdict=%s"
            % (sea_shape, narrow_rep["verdict"],
               narrow_rep.get("header_cells"),
               narrow_rep.get("separator_cells"), wide_shape,
               wide_rep["verdict"])))

        # AC-EDME2: a title inside a fenced block does not count as a table
        # title, so one real table plus one quoted title reads that table.
        fenced = temp_copy(workdir, "fenced.md", doctor_fenced_title)
        fenced_text = read(fenced)
        count = SMR.matrix_title_count(fenced_text, patterns)
        rep = SMR.report(fenced, green)
        code, word, printed = one_word_cli(["--check", "--doc", fenced,
                                            "--evidence", green])
        results.append(check(
            count == 1
            and rep["verdict"] not in (SMR.WORD_TITLE, SMR.WORD_TABLE)
            and word == rep["verdict"]
            and code == rep["exit"],
            "AC-EDME2 fenced-title count=%d -> %s rows=%s/%s CLI=%s rc=%d"
            " (the row counter is NOT fence-aware: a quoted data row still"
            " counts, which is the seeded successor limit)"
            % (count, rep["verdict"], rep.get("doc_rows"),
               rep.get("registry_rows"), word, code)))

        # AC-EDME3: a bare title differing only by trailing whitespace is the
        # SAME title and introduces no table, so it is not counted twice.
        trailing = temp_copy(workdir, "trailing.md",
                             doctor_bare_title_trailing)
        trailing_text = read(trailing)
        count = SMR.matrix_title_count(trailing_text, patterns)
        rep = SMR.report(trailing, green)
        results.append(check(
            count == 1
            and rep["verdict"] not in (SMR.WORD_TITLE, SMR.WORD_TABLE)
            and rep.get("doc_rows") == rep.get("registry_rows"),
            "AC-EDME3 trailing-bare-title count=%d -> %s rows=%s/%s"
            % (count, rep["verdict"], rep.get("doc_rows"),
               rep.get("registry_rows"))))

        # AC-EDME4: a walk whose ceiling was reached before a PASS leg reads
        # CEILING-STARVED naming the ceiling; a pile whose every candidate was
        # decoded reads RED-LEG.
        starved_dir = os.path.join(workdir, "qa-starved")
        os.makedirs(starved_dir, exist_ok=True)
        for name in ("one.log", "two.log", "three.log"):
            with open(os.path.join(starved_dir, name), "w",
                      encoding="utf-8", newline="\n") as handle:
                handle.write("RUNNER FAIL (1 failed assertions)\n")
        starved = SMR.report(DOC, None, starved_dir, 1)
        drained = SMR.report(DOC, None, starved_dir, 10)
        code, word, printed = one_word_cli(["--check", "--doc", DOC,
                                            "--qa-dir", starved_dir,
                                            "--ceiling", "1"])
        results.append(check(
            starved["verdict"] == SMR.WORD_CEILING
            and starved["exit"] == 3
            and starved.get("ceiling") == 1
            and starved.get("walk", {}).get("bounded") is True
            and "1" in starved.get("reason", "")
            and drained["verdict"] == SMR.WORD_RED
            and drained["walk"].get("decoded") == 3
            and not drained["walk"].get("bounded")
            and word == SMR.WORD_CEILING and "ceiling=1" in printed,
            "AC-EDME4 starved=%s(ceiling=%s bounded=%s) drained=%s"
            "(decoded=%s) CLI=%s rc=%d"
            % (starved["verdict"], starved.get("ceiling"),
               starved.get("walk", {}).get("bounded"), drained["verdict"],
               drained.get("walk", {}).get("decoded"), word, code)))

        # AC-EDME5: every R2606 answer survives on the same fixtures - the
        # four shape words, both counts, the bounded walk block, the named
        # evidence source, the R2602 words, one CLI word and the exit codes.
        dash2 = temp_copy(workdir, "dash2.md", doctor_sep(2, "-"))
        rd = SMR.report(dash2, green)
        missing = SMR.report(os.path.join(workdir, "absent.md"), green)
        no_sep = temp_copy(workdir, "nosep.md")
        sep_lines = read(no_sep).splitlines(True)
        sep_where = _table_lines(sep_lines)
        del sep_lines[sep_where[1]]
        with open(no_sep, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(sep_lines))
        rs = SMR.report(no_sep, green)
        five = temp_copy(workdir, "h5.md")
        hlines = read(five).splitlines(True)
        hwhere = _table_lines(hlines)
        hh, _ = hwhere
        hlines[hh] = "|" + "|".join(["c5"] * 5) + "|\n"
        with open(five, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(hlines))
        r5 = SMR.report(five, green)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        rp = SMR.report(DOC, None, pass_dir)
        rred = SMR.report(DOC, red)
        drop_doc = temp_copy(workdir, "rows.md", lambda t: t)
        text_rows = read(drop_doc)
        match = SMR.ROW_RE.search(text_rows)
        if match is None:
            raise AssertionError("E_EDME_SUITE_NO_ROW")
        with open(drop_doc, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text_rows[:match.start()] + text_rows[match.end():])
        rr = SMR.report(drop_doc, green)
        live = SMR.report(DOC, green)
        results.append(check(
            rs["verdict"] == SMR.WORD_SEP and rs["exit"] == 3
            and rd["verdict"] == SMR.WORD_HEADER
            and rd.get("header_cells") == 6
            and rd.get("separator_cells") == 2
            and missing["verdict"] == SMR.WORD_NONE
            and r5["verdict"] == SMR.WORD_HEADER and r5.get("cells") == 5
            and r5.get("expected_cells") == 6
            and rp.get("evidence_source") == "walk"
            and rred["verdict"] == SMR.WORD_RED
            and rred.get("evidence_source") == "explicit"
            and rr["verdict"] == SMR.WORD_ROWS
            and rr["doc_rows"] < rr["registry_rows"]
            and live["verdict"] == (SMR.WORD_CURRENT
                                    if live.get("doc_rows") ==
                                    live.get("registry_rows")
                                    else SMR.WORD_ROWS),
            "AC-EDME5 sep=%s dash2=%s/%s nodoc=%s header5=%s/%s src=%s/%s"
            " rows=%s(%d<%d) live=%s"
            % (rs["verdict"], rd.get("header_cells"),
               rd.get("separator_cells"), missing["verdict"], r5.get("cells"),
               r5.get("expected_cells"), rp.get("evidence_source"),
               rred.get("evidence_source"), rr["verdict"], rr["doc_rows"],
               rr["registry_rows"], live["verdict"])))

        # AC-EDME6: hygiene and its own registration.
        with open(MODULE, "rb") as handle:
            module_ascii = all(byte < 128 for byte in handle.read())
        with open(SELFTEST, "rb") as handle:
            suite_ascii = all(byte < 128 for byte in handle.read())
        with open(MODULE, encoding="utf-8") as handle:
            source = handle.read()
        imports = set()
        for line in source.splitlines():
            line = line.strip()
            if line.startswith("import "):
                imports.add(line[7:].split(".")[0].split(" ")[0])
            elif line.startswith("from "):
                imports.add(line[5:].split(".")[0].split(" ")[0])
        with open(RUNNER, encoding="utf-8") as handle:
            runner = handle.read()
        wired = [row for row in RA.SUITES
                 if row[0] == "os-suite-matrix-reconcile-fence"]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDME6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
            " cells=%s"
            % (module_ascii, suite_ascii, "time" in imports,
               sorted(imports & set(NET)), bool(wired),
               wired[0][2] if wired else "-")))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())