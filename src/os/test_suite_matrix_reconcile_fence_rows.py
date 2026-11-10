"""AC-EDMF1..AC-EDMF6 suite for the suite-matrix reconciliation FENCE-ROW
face (R2616).

Criteria were pinned in state/queue/tech.md:646 at R2608 BEFORE this code
existed, from four limits MEASURED there with
src/os/limits_matrix_reconcile_fence_next_R2608.py and RE-MEASURED at the
start of R2616 with src/os/limits_matrix_reconcile_fence_rows_next_R2616.py
before a single product byte was written.

What this proves: a data-shaped row inside a ``` fenced block is quoted text
and NOT a matrix row, so a document whose only row difference is quoted stops
reading ROWS-MISMATCH; a table repeated WITHOUT its separator row under the
SAME header text is the SAME table instead of a second title; a table with
DIFFERENT header text is still a second table and still refuses with the
count; the shipped check face is still asked on every reading, so a CONTENT
difference keeps its content word; and every R2608 answer survives on the
same fixtures.

Disclosed measurement technique: AC-EDMF1 owns DOC-CURRENT case patches the
SHIPPED check face green for that one reading, because the criterion is about
the ROW LAW and not about the shipped face (AC-EDMF4 covers the content word,
and it is asserted with the check face UNPATCHED). The same fixture is then
measured with the check face untouched to show the row verdict is gone.

All doctoring happens in private temporary directories, never in docs/ or
qa/. Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import contextlib
import io
import os
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
WIRED_LABEL = '"os-suite-matrix-reconcile-fence-rows",'
WIRED_SUITE = '"test_suite_matrix_reconcile_fence_rows.py"),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
ROW_SHAPE = "| 9999 | quoted-example | src/os/quoted.py | 6 | PASS | 0.1 |"


def check(ok, label):
    # The criterion marker must START the line: the shipped capture digests
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


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def title_of():
    return SM.load_patterns()["labels"]["matrix_title"].strip()


def table_rows(text):
    """(header_line, separator_line) of the FIRST matrix table, located by
    POSITION under the shipped title - never by a shape guess."""
    title = title_of()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != title:
            continue
        header = None
        for follow in lines[index + 1:]:
            if not follow.startswith("|"):
                if follow.strip():
                    return None
                continue
            if header is None:
                header = follow
                continue
            return header, follow
        return None
    return None


def temp_copy(directory, name, doctor=None):
    target = os.path.join(directory, name)
    shutil.copyfile(DOC, target)
    if doctor is not None:
        write(target, doctor(read(target)))
    return target


def doctor_quoted_row(text):
    """Append one fenced block carrying ONE data-shaped row."""
    return text + "\n" + SMR.FENCE_MARK + "\n" + ROW_SHAPE + "\n" + \
        SMR.FENCE_MARK + "\n"


def doctor_same_header_no_separator(text):
    """Repeat the SAME table with its separator row LEFT OUT."""
    rows = table_rows(text)
    if rows is None:
        raise AssertionError("E_EDMF_SUITE_NO_TABLE")
    header = rows[0]
    return text + "\n" + title_of() + "\n\n" + header + "\n" + ROW_SHAPE + "\n"


def doctor_other_header(text):
    """Append a second table with DIFFERENT header text."""
    return (text + "\n" + title_of() + "\n\n"
            "| a | b | c | d | e | f |\n|---|---|---|---|---|---|\n"
            + ROW_SHAPE + "\n")


def doctor_content_change(text):
    """Change a CONTENT byte inside the first data row, keeping its shape."""
    match = SMR.ROW_RE.search(text)
    if match is None:
        raise AssertionError("E_EDMF_SUITE_NO_ROW")
    row = match.group(0)
    cells = row.split("|")
    if len(cells) < 4 or not cells[2].strip():
        raise AssertionError("E_EDMF_SUITE_NO_CONTENT")
    cells[2] = " " + cells[2].strip() + "x "
    swapped = "|".join(cells)
    if swapped == row:
        raise AssertionError("E_EDMF_SUITE_NO_CONTENT")
    return text[:match.start()] + swapped + text[match.end():]


@contextlib.contextmanager
def patched_check(green=True):
    """Swap the SHIPPED check face for a constant verdict, restore in a
    finally. Used ONLY where the criterion is about the row law."""
    original = SM.main
    calls = {"n": 0}

    def stub(argv):
        calls["n"] += 1
        return 0 if green else 2

    SM.main = stub
    try:
        yield calls
    finally:
        SM.main = original


@contextlib.contextmanager
def counting_check():
    """Ask the SHIPPED check face for real and count how many times it was
    asked, so 'still asked on every reading' is measured not asserted."""
    original = SM.main
    calls = {"n": 0, "code": None}

    def counting(argv):
        code = original(argv)
        calls["n"] += 1
        calls["code"] = code
        return code

    SM.main = counting
    try:
        yield calls
    finally:
        SM.main = original


def one_word_cli(args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SMR.main(["suite_matrix_reconcile.py"] + args)
    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    return code, (lines[0].split()[0] if lines else ""), buffer.getvalue()


def verify():
    green, _greendata = leg("PASS")
    red, _reddata = leg("FAIL")
    patterns = SM.load_patterns()
    results = []
    workdir = tempfile.mkdtemp(prefix="edmf-")
    try:
        # AC-EDMF1: a data row inside a fence is NOT a matrix row, so a
        # document whose only row difference is quoted no longer reads
        # ROWS-MISMATCH. The row law is measured on its own (check patched
        # green) AND on the untouched shipped face.
        quoted = temp_copy(workdir, "quoted.md", doctor_quoted_row)
        quoted_text = read(quoted)
        real_rows = SMR.doc_rows(read(DOC))
        quoted_rows = SMR.doc_rows(quoted_text)
        registry_rows, _rc = SMR.registry_counts()
        with patched_check(True):
            patched = SMR.report(quoted, green)
        untouched = SMR.report(quoted, green)
        live = SMR.report(DOC, green)
        results.append(check(
            quoted_rows == real_rows
            and ROW_SHAPE in quoted_text
            and patched["verdict"] == SMR.WORD_CURRENT
            and patched["exit"] == 0
            and untouched["verdict"] != SMR.WORD_ROWS,
            "AC-EDMF1 quoted rows=%d real=%d (quoted row present, not"
            " counted) law=%s untouched=%s live=%s registry=%d"
            % (quoted_rows, real_rows, patched["verdict"],
               untouched["verdict"], live["verdict"], registry_rows)))

        # AC-EDMF2: the SAME header text without a separator row is the SAME
        # table, so it does not read TITLE-REPEATED the way R2608 did.
        no_sep = temp_copy(workdir, "nosep-repeat.md",
                           doctor_same_header_no_separator)
        count = SMR.matrix_title_count(read(no_sep), patterns)
        rep = SMR.report(no_sep, green)
        one = SMR.matrix_title_count(read(DOC), patterns)
        results.append(check(
            count == 1 and one == 1
            and rep["verdict"] != SMR.WORD_TITLE,
            "AC-EDMF2 same-header-no-separator titles=%d (live=%d)"
            " -> %s exit=%d"
            % (count, one, rep["verdict"], rep["exit"])))

        # AC-EDMF3: DIFFERENT header text is still a second table and still
        # refuses by name with the count.
        other = temp_copy(workdir, "other-header.md", doctor_other_header)
        count = SMR.matrix_title_count(read(other), patterns)
        rep = SMR.report(other, green)
        code, word, printed = one_word_cli(["--check", "--doc", other,
                                            "--evidence", green])
        results.append(check(
            count == 2
            and rep["verdict"] == SMR.WORD_TITLE and rep["exit"] == 3
            and rep.get("titles") == 2 and rep.get("code") == SMR.CODE_TITLE
            and word == SMR.WORD_TITLE and code == 3
            and "titles=2" in printed,
            "AC-EDMF3 other-header titles=%d -> %s titles=%s exit=%d"
            " CLI=%s rc=%d"
            % (count, rep["verdict"], rep.get("titles"), rep["exit"],
               word, code)))

        # AC-EDMF4: the shipped check face is STILL ASKED on every reading,
        # so a document that differs in CONTENT rather than shape keeps its
        # content word instead of being called current.
        content = temp_copy(workdir, "content.md", doctor_content_change)
        with counting_check() as calls:
            rep = SMR.report(content, green)
        with counting_check() as live_calls:
            live_rep = SMR.report(DOC, green)
        results.append(check(
            calls["n"] == 1 and calls["code"] != 0
            and rep["verdict"] == SMR.WORD_STALE
            and live_calls["n"] == 1 and live_calls["code"] == 0
            and live_rep["verdict"] == SMR.WORD_CURRENT,
            "AC-EDMF4 check-asked=%d code=%s content=%s | live asked=%d"
            " code=%s verdict=%s"
            % (calls["n"], calls["code"], rep["verdict"], live_calls["n"],
               live_calls["code"], live_rep["verdict"])))

        # AC-EDMF5: every R2608 answer survives on the same fixtures.
        twice = temp_copy(workdir, "r2608-twice.md", doctor_other_header)
        fenced_title = temp_copy(workdir, "r2608-fenced.md",
                                 lambda t: t + "\n```\n" + title_of() + "\n"
                                 "| a | b | c | d | e | f |\n"
                                 "|---|---|---|---|---|---|\n"
                                 + ROW_SHAPE + "\n```\n")
        bare = temp_copy(workdir, "r2608-bare.md",
                         lambda t: t + "\n" + title_of() + "   \n")
        missing = SMR.report(os.path.join(workdir, "absent.md"), green)
        narrow = temp_copy(workdir, "r2608-narrow.md")
        lines = read(narrow).splitlines(True)
        where = None
        for index, line in enumerate(lines):
            if line.startswith("|") and SMR.is_separator_row(line) and \
                    line.count("|") - 1 == SMR.MATRIX_CELLS:
                where = index
                break
        if where is None:
            raise AssertionError("E_EDMF_SUITE_NO_SEPARATOR")
        lines[where] = "|" + "---|" * 2 + "\n"
        write(narrow, "".join(lines))
        narrow_rep = SMR.report(narrow, green)
        starved_dir = os.path.join(workdir, "qa-starved")
        os.makedirs(starved_dir, exist_ok=True)
        for name in ("one.log", "two.log"):
            write(os.path.join(starved_dir, name),
                  "RUNNER FAIL (1 failed assertions)\n")
        starved = SMR.report(DOC, None, starved_dir, 1)
        drained = SMR.report(DOC, None, starved_dir, 10)
        red_rep = SMR.report(DOC, red)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        walk_rep = SMR.report(DOC, None, pass_dir)
        dropped = temp_copy(workdir, "r2608-rows.md")
        text_rows = read(dropped)
        match = SMR.ROW_RE.search(text_rows)
        if match is None:
            raise AssertionError("E_EDMF_SUITE_NO_ROW")
        write(dropped, text_rows[:match.start()] + text_rows[match.end():])
        rows_rep = SMR.report(dropped, green)
        results.append(check(
            SMR.matrix_title_count(read(twice), patterns) == 2
            and SMR.matrix_title_count(read(fenced_title), patterns) == 1
            and SMR.matrix_title_count(read(bare), patterns) == 1
            and missing["verdict"] == SMR.WORD_NONE
            and narrow_rep["verdict"] == SMR.WORD_HEADER
            and narrow_rep.get("separator_cells") == 2
            and narrow_rep.get("header_cells") == 6
            and starved["verdict"] == SMR.WORD_CEILING
            and starved.get("walk", {}).get("bounded") is True
            and drained["verdict"] == SMR.WORD_RED
            and not drained["walk"].get("bounded")
            and red_rep["verdict"] == SMR.WORD_RED
            and red_rep.get("evidence_source") == "explicit"
            and walk_rep.get("evidence_source") == "walk"
            and rows_rep["verdict"] == SMR.WORD_ROWS
            and rows_rep["doc_rows"] == rows_rep["registry_rows"] - 1,
            "AC-EDMF5 twice=%d fenced=%d bare=%d nodoc=%s narrow=%s/%s"
            " starved=%s drained=%s red=%s src=%s/%s rows=%s(%d/%d)"
            % (SMR.matrix_title_count(read(twice), patterns),
               SMR.matrix_title_count(read(fenced_title), patterns),
               SMR.matrix_title_count(read(bare), patterns),
               missing["verdict"], narrow_rep["verdict"],
               narrow_rep.get("separator_cells"), starved["verdict"],
               drained["verdict"], red_rep["verdict"],
               walk_rep.get("evidence_source"), red_rep.get("evidence_source"),
               rows_rep["verdict"], rows_rep["doc_rows"],
               rows_rep["registry_rows"])))

        # AC-EDMF6: hygiene and its own registration.
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
                 if row[0] == "os-suite-matrix-reconcile-fence-rows"]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDMF6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
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
