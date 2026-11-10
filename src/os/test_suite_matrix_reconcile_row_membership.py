"""AC-EDMI1..AC-EDMI6 suite for the TABLE-MEMBERSHIP law of the suite-matrix
reconciliation face (R2630).

Criteria were pinned in state/queue/tech.md:653 at R2624 BEFORE this code
existed, from a limit measured there and re-measured at the start of this
window with src/os/limits_matrix_reconcile_row_membership_R2630.py:
  (a) a malformed row whose FIRST CELL is not numeric still ENDED the table,
      so doc_rows collapsed from 643 to 0 (delta -643) - the gap
  (b) a GENUINE second-table header already ended the first table (delta 0)
  (c) the footer/total row already read as a non-row (delta 0)
  (d) a malformed row as the LAST row already read -1

The shipped law is decided by the SEPARATOR row a header carries rather than
by a digit in the first cell.

Every fixture is a private temporary copy; docs/ is never touched. Proofs run
through the shipped faces; the shipped check face is patched ONLY to count
that it was asked.

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
LABEL = "os-suite-matrix-reconcile-row-membership"
MODULE = os.path.join(BASE, "suite_matrix_reconcile.py")
SELFTEST = os.path.abspath(__file__)
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"%s",' % LABEL
WIRED_SUITE = '"test_suite_matrix_reconcile_row_membership.py"),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"
FOOTER = "|  | total |  | 4834 | green / FAIL 0 |  |"


def check(ok, label):
    # The criterion marker sits at COLUMN 0 because the shipped evidence
    # capture digests lines that start with PASS/FAIL.
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
    raise AssertionError("E_EDMI_SUITE_NO_TABLE")


def row_indexes(text):
    return [index for index, line in enumerate(text.splitlines())
            if SMR.ROW_RE.match(line)]


def doctor_first_cell_nonnumeric(text):
    """The measured gap: the FIRST data row carries 'n/a' in its first cell."""
    lines = text.splitlines()
    index = row_indexes(text)[0]
    parts = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
    parts[0] = "n/a"
    lines[index] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def doctor_last_cell_nonnumeric(text):
    lines = text.splitlines()
    index = row_indexes(text)[-1]
    parts = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
    parts[0] = "n/a"
    lines[index] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def doctor_wrong_cells(text, cells):
    lines = text.splitlines()
    index = row_indexes(text)[0]
    parts = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
    if cells < len(parts):
        parts = parts[:cells]
    else:
        parts = parts + ["x"] * (cells - len(parts))
    lines[index] = "| " + " | ".join(parts) + " |"
    return "\n".join(lines) + "\n"


def doctor_two_adjacent(text):
    lines = text.splitlines()
    for index in row_indexes(text)[:2]:
        parts = [cell.strip()
                 for cell in lines[index].strip().strip("|").split("|")]
        lines[index] = "| " + " | ".join(parts[:4]) + " |"
    return "\n".join(lines) + "\n"


def doctor_second_header(text):
    """A GENUINE second table: a header row followed by a separator row."""
    lines = text.splitlines()
    block = ["| # | Suite | Path | Criteria | State | Secs |",
             "|---|---|---|---|---|---|", ROW]
    at = row_indexes(text)[-1] + 1
    return "\n".join(lines[:at] + block + lines[at:]) + "\n"


def doctor_footer_after_last(text):
    lines = text.splitlines()
    at = row_indexes(text)[-1] + 1
    return "\n".join(lines[:at] + [FOOTER] + lines[at:]) + "\n"


def doctor_separator_inside(text):
    lines = text.splitlines()
    rows = row_indexes(text)
    mid = rows[0] + max(1, (rows[-1] - rows[0]) // 2)
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
    lines[row_indexes(text)[0] - 1] = "|---|---|"
    return "\n".join(lines) + "\n"


def doctor_no_separator(text):
    lines = text.splitlines()
    del lines[row_indexes(text)[0] - 1]
    return "\n".join(lines) + "\n"


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
    workdir = tempfile.mkdtemp(prefix="edmi-")
    try:
        # AC-EDMI1: a malformed row whose FIRST CELL is not numeric is ONE
        # non-row, so the count falls by one rather than collapsing to zero.
        nonnumeric = copy(workdir, "nonnumeric.md",
                          doctor_first_cell_nonnumeric)
        nonnumeric_rows = SMR.doc_rows(read(nonnumeric))
        nonnumeric_rep = SMR.report(nonnumeric, green)
        results.append(check(
            real == registry_rows
            and nonnumeric_rows == real - 1
            and nonnumeric_rep["verdict"] == SMR.WORD_ROWS
            and nonnumeric_rep["doc_rows"] == real - 1
            and nonnumeric_rep["registry_rows"] == registry_rows,
            "AC-EDMI1 nonnumeric-first-cell rows=%d real=%d delta=%+d"
            " verdict=%s doc_rows=%d"
            % (nonnumeric_rows, real, nonnumeric_rows - real,
               nonnumeric_rep["verdict"], nonnumeric_rep["doc_rows"])))

        # AC-EDMI2: a GENUINE header of a SECOND table still ENDS the first
        # table, and the AC-EDMG1 fixture reads exactly as it does today.
        second = copy(workdir, "second-header.md", doctor_second_header)
        ac_edmg1 = copy(workdir, "second-table.md", doctor_second_table_row)
        second_rows = SMR.doc_rows(read(second))
        ac_edmg1_rows = SMR.doc_rows(read(ac_edmg1))
        ac_edmg1_rep = SMR.report(ac_edmg1, green)
        results.append(check(
            second_rows == real and ac_edmg1_rows == real
            and SMR.matrix_title_count(read(ac_edmg1), patterns) == 1
            and ac_edmg1_rep["verdict"] == SMR.WORD_STALE,
            "AC-EDMI2 genuine-header rows=%d ac-edmg1-rows=%d real=%d"
            " titles=%d verdict=%s"
            % (second_rows, ac_edmg1_rows, real,
               SMR.matrix_title_count(read(ac_edmg1), patterns),
               ac_edmg1_rep["verdict"])))

        # AC-EDMI3: the footer/total row after the last data row is still not
        # counted and does not change the count.
        footer = copy(workdir, "footer.md", doctor_footer_after_last)
        footer_rows = SMR.doc_rows(read(footer))
        footer_rep = SMR.report(footer, green)
        results.append(check(
            footer_rows == real
            and footer_rep["verdict"] == SMR.WORD_STALE
            and footer_rep["doc_rows"] == registry_rows,
            "AC-EDMI3 footer-after-last rows=%d real=%d delta=%+d verdict=%s"
            % (footer_rows, real, footer_rows - real, footer_rep["verdict"])))

        # AC-EDMI4: the shipped check face is still asked EXACTLY ONCE per
        # reading, and a content difference keeps its content word.
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
            "AC-EDMI4 asked live=%s diff=%s verdict=%s/%s"
            % (calls_live.get("asked"), calls_diff.get("asked"),
               live2["verdict"], diff2["verdict"])))

        # AC-EDMI5: every R2624 answer survives beside the new ones, proved on
        # the same fixtures, plus both counts and the named evidence source.
        four = copy(workdir, "four.md", lambda t: doctor_wrong_cells(t, 4))
        two = copy(workdir, "two.md", doctor_two_adjacent)
        last = copy(workdir, "last.md", doctor_last_cell_nonnumeric)
        sep = copy(workdir, "separator.md", doctor_separator_inside)
        quoted = copy(workdir, "quoted.md", doctor_quoted)
        unseen = copy(workdir, "unseen.md", doctor_unclosed)
        nested = copy(workdir, "nested.md", doctor_nested)
        same = copy(workdir, "same.md", doctor_same_header_no_separator)
        other = copy(workdir, "other.md", doctor_other_header)
        narrow = copy(workdir, "narrow.md", doctor_narrow_separator)
        nosep = copy(workdir, "nosep.md", doctor_no_separator)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        walk_rep = SMR.report(DOC, None, pass_dir)
        four_rows = SMR.doc_rows(read(four))
        two_rows = SMR.doc_rows(read(two))
        last_rows = SMR.doc_rows(read(last))
        sep_rows = SMR.doc_rows(read(sep))
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
        no_doc = SMR.report(os.path.join(workdir, "absent.md"), green)
        results.append(check(
            four_rows == real - 1 and two_rows == real - 2
            and last_rows == real - 1
            and sep_rows == real and quoted_rows == real
            and unseen_rep["verdict"] == SMR.WORD_FENCE
            and unseen_rep.get("line") == open_line
            and unseen_rep.get("open_marker") == 3
            and nested_rep["verdict"] == SMR.WORD_NEST
            and nested_rep.get("open_marker") == 4
            and nested_rep.get("inner_marker") == 3
            and same_titles == 1 and other_titles == 2
            and other_rep["verdict"] == SMR.WORD_TITLE
            and other_rep.get("titles") == 2
            and narrow_rep["verdict"] == SMR.WORD_HEADER
            and narrow_rep.get("separator_cells") == 2
            and narrow_rep.get("header_cells") == 6
            and nosep_rep["verdict"] == SMR.WORD_SEP
            and starved["verdict"] == SMR.WORD_CEILING
            and no_doc["verdict"] == SMR.WORD_NONE
            and live["verdict"] == SMR.WORD_CURRENT
            and live.get("doc_rows") == registry_rows
            and live.get("registry_rows") == registry_rows
            and live.get("registry_criteria") == registry_criteria
            and live.get("evidence_source") == "explicit"
            and walk_rep.get("evidence_source") == "walk",
            "AC-EDMI5 four=%d two=%d last=%d sep=%d quoted=%d"
            " fence=%s/%s nest=%s/%s/%s titles=%d/%d other=%s/%s"
            " narrow=%s nosep=%s starved=%s nodoc=%s counts=%d/%d src=%s/%s"
            % (four_rows, two_rows, last_rows, sep_rows, quoted_rows,
               unseen_rep["verdict"], unseen_rep.get("line"),
               nested_rep["verdict"], nested_rep.get("open_marker"),
               nested_rep.get("inner_marker"), same_titles, other_titles,
               other_rep["verdict"], other_rep.get("titles"),
               narrow_rep["verdict"], nosep_rep["verdict"],
               starved["verdict"], no_doc["verdict"],
               live.get("doc_rows"), live.get("registry_rows"),
               live.get("evidence_source"), walk_rep.get("evidence_source"))))

        # AC-EDMI6: hygiene and its own registration.
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
        wired = [row for row in RA.SUITES if row[0] == LABEL]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDMI6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
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
