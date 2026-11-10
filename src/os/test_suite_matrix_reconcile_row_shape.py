"""AC-EDMH1..AC-EDMH6 suite for the row-shape law of the suite-matrix
reconciliation face (R2624).

Criteria were pinned in state/queue/tech.md:652 at R2621 BEFORE this code
existed, from a limit MEASURED there and re-measured at the start of this
window with src/os/limits_matrix_reconcile_row_shape_R2624.py:
  (a) ONE malformed data row inside the matrix table collapsed doc_rows to 0
      (measured 642 -> 0 for a four-cell row and 642 -> 0 for a seven-cell row)
  (b) a GENUINE second-table header still ended the first table (delta 0)
  (c) a separator row inside the table already neither restarted nor ended it
      (delta 0) - named as already correct rather than claimed as a gap

Every fixture is a private temporary copy; docs/ is never touched. Proofs run
through the shipped faces (suite_matrix.main --check, suite_matrix.parse_
evidence, suite_matrix.load_patterns, reconcile_all.SUITES); the shipped main
is patched ONLY to count that it was asked.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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
WIRED_LABEL = '"os-suite-matrix-reconcile-row-shape",'
WIRED_SUITE = '"test_suite_matrix_reconcile_row_shape.py"),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"


def check(ok, label):
    # The criterion marker sits at COLUMN 0 because the shipped evidence
    # capture digests the lines that start with PASS/FAIL; an indented marker
    # digests to the empty string and would make two arbitrary legs look
    # identical (measured at R2624 on this suite own first capture).
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def copy(workdir, name, doctor):
    path = os.path.join(workdir, name)
    write(path, doctor(read(DOC)))
    return path


def leg(kind):
    paths = [os.path.join(QA_DIR, n) for n in os.listdir(QA_DIR)
             if n.endswith(".log")]
    paths.sort(key=lambda p: (-os.path.getmtime(p), os.path.basename(p)))
    for path in paths:
        try:
            _, run = SM.parse_evidence(path)
        except (OSError, UnicodeDecodeError):
            continue
        if kind == "PASS" and run and run["verdict"] == "PASS":
            return path
        if kind == "FAIL" and not (run and run["verdict"] == "PASS"):
            return path
    return None


def title_of():
    return SM.load_patterns()["labels"]["matrix_title"]


def table_header(text):
    title = title_of().strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != title:
            continue
        for follow in lines[index + 1:]:
            if follow.startswith("|"):
                return follow
            if follow.strip():
                break
    raise AssertionError("E_EDMH_SUITE_NO_TABLE")


def first_row_index(text):
    for index, line in enumerate(text.splitlines()):
        if SMR.ROW_RE.match(line):
            return index
    raise AssertionError("E_EDMH_SUITE_NO_ROW")


def doctor_wrong_cells(text, cells):
    """Replace the FIRST matrix data row with a data-shaped row carrying a
    different cell count."""
    lines = text.splitlines()
    index = first_row_index(text)
    parts = [cell.strip()
             for cell in lines[index].strip().strip("|").split("|")]
    if cells < len(parts):
        parts = parts[:cells]
    else:
        parts = parts + ["x"] * (cells - len(parts))
    lines[index] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def doctor_second_header(text):
    """A GENUINE second table: a header row followed by a separator row."""
    lines = text.splitlines()
    last = None
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            last = index
    block = ["| # | Suite | Path | Criteria | State | Secs |",
             "|---|---|---|---|---|---|", ROW]
    return "\n".join(lines[:last + 1] + block + lines[last + 1:]) + "\n"


def doctor_separator_inside(text):
    lines = text.splitlines()
    first = first_row_index(text)
    last = None
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            last = index
    mid = first + max(1, (last - first) // 2)
    return "\n".join(lines[:mid] + ["|---|---|---|---|---|---|"]
                     + lines[mid:]) + "\n"


def doctor_quoted(text):
    return (text + "\n" + SMR.FENCE_MARK + "\n" + ROW + "\n"
            + SMR.FENCE_MARK + "\n")


def doctor_unclosed(text):
    return text + "\n" + SMR.FENCE_MARK + "\n" + ROW + "\n"


def doctor_nested(text):
    return (text + "\n````\n" + ROW + "\n```\n" + ROW + "\n````\n")


def doctor_second_table_row(text):
    return (text + "\n" + title_of() + "\n\n" + table_header(text) + "\n"
            "|---|---|---|---|---|---|\n" + ROW + "\n")


def doctor_same_header_no_separator(text):
    return text + "\n" + title_of() + "\n\n" + table_header(text) + "\n" \
        + ROW + "\n"


def doctor_other_header(text):
    return (text + "\n" + title_of() + "\n\n"
            "| a | b | c | d | e | f |\n|---|---|---|---|---|---|\n" + ROW
            + "\n")


def doctor_narrow_separator(text):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            lines[index - 1] = "|---|---|"
            return "\n".join(lines) + "\n"
    raise AssertionError("E_EDMH_SUITE_NO_ROW")


def doctor_no_separator(text):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            del lines[index - 1]
            return "\n".join(lines) + "\n"
    raise AssertionError("E_EDMH_SUITE_NO_ROW")


def doctor_dropped_row(text):
    match = SMR.ROW_RE.search(text)
    if match is None:
        raise AssertionError("E_EDMH_SUITE_NO_ROW")
    return text[:match.start()] + text[match.end():]


@contextlib.contextmanager
def patched_check(calls):
    original = SM.main

    def counting(argv):
        calls["asked"] = calls.get("asked", 0) + 1
        return original(argv)

    SM.main = counting
    try:
        yield calls
    finally:
        SM.main = original


def verify():
    green = leg("PASS")
    patterns = SM.load_patterns()
    real = SMR.doc_rows(read(DOC))
    registry_rows, registry_criteria = SMR.registry_counts()
    live = SMR.report(DOC, green)
    results = []
    workdir = tempfile.mkdtemp(prefix="edmh-")
    try:
        # AC-EDMH1: a data-shaped row with the WRONG CELL COUNT is skipped as
        # ONE non-row, and every well-formed row after it is still counted, so
        # the count falls by one rather than to zero.
        four = copy(workdir, "four.md", lambda t: doctor_wrong_cells(t, 4))
        seven = copy(workdir, "seven.md", lambda t: doctor_wrong_cells(t, 7))
        four_rows = SMR.doc_rows(read(four))
        seven_rows = SMR.doc_rows(read(seven))
        four_rep = SMR.report(four, green)
        seven_rep = SMR.report(seven, green)
        results.append(check(
            real == registry_rows
            and four_rows == real - 1 and seven_rows == real - 1
            and four_rep["verdict"] == SMR.WORD_ROWS
            and four_rep["doc_rows"] == real - 1
            and four_rep["registry_rows"] == registry_rows
            and seven_rep["verdict"] == SMR.WORD_ROWS
            and seven_rep["doc_rows"] == real - 1,
            "AC-EDMH1 four=%d seven=%d real=%d registry=%d verdict=%s/%s"
            % (four_rows, seven_rows, real, registry_rows,
               four_rep["verdict"], seven_rep["verdict"])))

        # AC-EDMH2: a GENUINE header of a SECOND table still ENDS the first
        # table, so the AC-EDMG1 law is unchanged and proved on its fixture.
        second = copy(workdir, "second-header.md", doctor_second_header)
        ac_edmg1 = copy(workdir, "second-table.md", doctor_second_table_row)
        second_rows = SMR.doc_rows(read(second))
        ac_edmg1_rows = SMR.doc_rows(read(ac_edmg1))
        ac_edmg1_rep = SMR.report(ac_edmg1, green)
        results.append(check(
            second_rows == real and ac_edmg1_rows == real
            and SMR.matrix_title_count(read(ac_edmg1), patterns) == 1
            and ac_edmg1_rep["verdict"] == SMR.WORD_STALE,
            "AC-EDMH2 genuine-header rows=%d ac-edmg1-rows=%d real=%d"
            " titles=%d verdict=%s"
            % (second_rows, ac_edmg1_rows, real,
               SMR.matrix_title_count(read(ac_edmg1), patterns),
               ac_edmg1_rep["verdict"])))

        # AC-EDMH3: a separator row reappearing INSIDE the table does not
        # restart or end it.
        sep = copy(workdir, "separator.md", doctor_separator_inside)
        sep_rows = SMR.doc_rows(read(sep))
        sep_rep = SMR.report(sep, green)
        results.append(check(
            sep_rows == real and sep_rep["verdict"] == SMR.WORD_STALE,
            "AC-EDMH3 separator-inside rows=%d real=%d verdict=%s"
            % (sep_rows, real, sep_rep["verdict"])))

        # AC-EDMH4: the shipped check face is asked EXACTLY ONCE per reading,
        # so a content difference keeps its content word.
        calls_live = {}
        with patched_check(calls_live):
            live2 = SMR.report(DOC, green)
        calls_diff = {}
        with patched_check(calls_diff):
            diff2 = SMR.report(ac_edmg1, green)
        results.append(check(
            calls_live.get("asked") == 1 and calls_diff.get("asked") == 1
            and live2["verdict"] == SMR.WORD_CURRENT
            and diff2["verdict"] == SMR.WORD_STALE,
            "AC-EDMH4 asked live=%s diff=%s verdict=%s/%s"
            % (calls_live.get("asked"), calls_diff.get("asked"),
               live2["verdict"], diff2["verdict"])))

        # AC-EDMH5: every R2621 answer survives beside the new ones, proved on
        # the same fixtures, plus both counts and the named evidence source.
        quoted = copy(workdir, "quoted.md", doctor_quoted)
        unseen = copy(workdir, "unseen.md", doctor_unclosed)
        nested = copy(workdir, "nested.md", doctor_nested)
        same = copy(workdir, "same.md", doctor_same_header_no_separator)
        other = copy(workdir, "other.md", doctor_other_header)
        narrow = copy(workdir, "narrow.md", doctor_narrow_separator)
        nosep = copy(workdir, "nosep.md", doctor_no_separator)
        dropped = copy(workdir, "dropped.md", doctor_dropped_row)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        walk_rep = SMR.report(DOC, None, pass_dir)
        quoted_rows = SMR.doc_rows(read(quoted))
        unseen_text = read(unseen)
        open_line = unseen_text.splitlines().index("```") + 1
        unseen_rep = SMR.report(unseen, green)
        nested_rep = SMR.report(nested, green)
        same_titles = SMR.matrix_title_count(read(same), patterns)
        other_titles = SMR.matrix_title_count(read(other), patterns)
        other_rep = SMR.report(other, green)
        narrow_rep = SMR.report(narrow, green)
        nosep_rep = SMR.report(nosep, green)
        starved = SMR.report(DOC, None, None, 0)
        drop_rep = SMR.report(dropped, green)
        results.append(check(
            quoted_rows == real
            and unseen_rep["verdict"] == SMR.WORD_FENCE
            and unseen_rep.get("line") == open_line
            and unseen_rep.get("open_marker") == 3
            and nested_rep["verdict"] == SMR.WORD_NEST
            and nested_rep.get("open_marker") == 4
            and nested_rep.get("inner_marker") == 3
            and same_titles == 1
            and other_titles == 2
            and other_rep["verdict"] == SMR.WORD_TITLE
            and other_rep.get("titles") == 2
            and narrow_rep["verdict"] == SMR.WORD_HEADER
            and narrow_rep.get("separator_cells") == 2
            and narrow_rep.get("header_cells") == 6
            and nosep_rep["verdict"] == SMR.WORD_SEP
            and starved["verdict"] == SMR.WORD_CEILING
            and drop_rep["verdict"] == SMR.WORD_ROWS
            and drop_rep["doc_rows"] == registry_rows - 1
            and live["verdict"] == SMR.WORD_CURRENT
            and live.get("evidence_source") == "explicit"
            and walk_rep.get("evidence_source") == "walk",
            "AC-EDMH5 quoted=%d/%d fence=%s/%s nest=%s/%s/%s titles=%d/%d"
            " other=%s narrow=%s nosep=%s starved=%s drop=%d src=%s/%s"
            % (quoted_rows, real, unseen_rep["verdict"],
               unseen_rep.get("line"), nested_rep["verdict"],
               nested_rep.get("open_marker"), nested_rep.get("inner_marker"),
               same_titles, other_titles, other_rep["verdict"],
               narrow_rep["verdict"], nosep_rep["verdict"],
               starved["verdict"], drop_rep["doc_rows"],
               live.get("evidence_source"), walk_rep.get("evidence_source"))))

        # AC-EDMH6: hygiene and its own registration.
        with open(MODULE, "rb") as handle:
            module_ascii = all(byte < 128 for byte in handle.read())
        with open(SELFTEST, "rb") as handle:
            suite_ascii = all(byte < 128 for byte in handle.read())
        imports = set()
        for line in read(MODULE).splitlines():
            line = line.strip()
            if line.startswith("import "):
                imports.add(line[7:].split(".")[0].split(" ")[0])
            elif line.startswith("from "):
                imports.add(line[5:].split(".")[0].split(" ")[0])
        runner = read(RUNNER)
        wired = [row for row in RA.SUITES
                 if row[0] == "os-suite-matrix-reconcile-row-shape"]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDMH6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
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
