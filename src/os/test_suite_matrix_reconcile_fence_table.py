"""AC-EDMG1..AC-EDMG6 suite for the table-aware row law and the named fence
law of the suite-matrix reconciliation face (R2621).

Criteria were pinned in state/queue/tech.md:650 at R2616 BEFORE this code
existed, from three limits MEASURED there and re-measured at the start of this
window with src/os/limits_matrix_reconcile_fence_table_R2621.py:
  (a) a data-shaped row in a SECOND unfenced table counted (delta 1)
  (b) a fence opened and never closed was never named (delta 0)
  (c) a four-backtick fence carrying a three-backtick line counted a quoted
      row (delta 1)

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
WIRED_LABEL = '"os-suite-matrix-reconcile-fence-table",'
WIRED_SUITE = '"test_suite_matrix_reconcile_fence_table.py"),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
ROW = "| 999 | probe-suite | os/probe.py | 6 | green | 1.0 |"


def check(ok, label):
    print("  %s %s" % ("PASS" if ok else "FAIL", label))
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
    raise AssertionError("E_EDMG_SUITE_NO_TABLE")


def doctor_second_table(text):
    return (text + "\n" + title_of() + "\n\n" + table_header(text) + "\n"
            "|---|---|---|---|---|---|\n" + ROW + "\n")


def doctor_unclosed(text):
    return text + "\n" + SMR.FENCE_MARK + "\n" + ROW + "\n"


def doctor_nested(text):
    return (text + "\n````\n" + ROW + "\n```\n" + ROW + "\n````\n")


def doctor_quoted(text):
    return (text + "\n" + SMR.FENCE_MARK + "\n" + ROW + "\n"
            + SMR.FENCE_MARK + "\n")


def doctor_same_header_no_separator(text):
    return text + "\n" + title_of() + "\n\n" + table_header(text) + "\n" \
        + ROW + "\n"


def doctor_other_header(text):
    return (text + "\n" + title_of() + "\n\n"
            "| a | b | c | d | e | f |\n|---|---|---|---|---|---|\n" + ROW
            + "\n")


def doctor_no_table(text):
    title = title_of().strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == title:
            return "\n".join(lines[:index]) + "\n"
    raise AssertionError("E_EDMG_SUITE_NO_TITLE")


def doctor_narrow_separator(text):
    title = title_of().strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == title:
            for follow in range(index + 1, len(lines)):
                if lines[follow].startswith("|"):
                    lines[follow + 1] = "|---|---|"
                    return "\n".join(lines) + "\n"
    raise AssertionError("E_EDMG_SUITE_NO_TABLE")


def doctor_no_separator(text):
    title = title_of().strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != title:
            continue
        for follow in range(index + 1, len(lines)):
            if lines[follow].startswith("|"):
                del lines[follow + 1]
                return "\n".join(lines) + "\n"
    raise AssertionError("E_EDMG_SUITE_NO_TABLE")


def doctor_dropped_row(text):
    match = SMR.ROW_RE.search(text)
    if match is None:
        raise AssertionError("E_EDMG_SUITE_NO_ROW")
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


def one_word_cli(args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SMR.main(["suite_matrix_reconcile.py"] + args)
    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    return code, (lines[0].split()[0] if lines else ""), buffer.getvalue()


def verify():
    green = leg("PASS")
    patterns = SM.load_patterns()
    real = SMR.doc_rows(read(DOC))
    registry_rows, registry_criteria = SMR.registry_counts()
    live = SMR.report(DOC, green)
    results = []
    workdir = tempfile.mkdtemp(prefix="edmg-")
    try:
        # AC-EDMG1: a data-shaped row in a SECOND table under the same title is
        # not a matrix row, so a document whose only row difference is there
        # stops reading ROWS-MISMATCH.
        second = copy(workdir, "second.md", doctor_second_table)
        second_text = read(second)
        second_rows = SMR.doc_rows(second_text)
        second_rep = SMR.report(second, green)
        results.append(check(
            real == registry_rows and second_rows == real
            and SMR.matrix_title_count(second_text, patterns) == 1
            and second_rep["verdict"] != SMR.WORD_ROWS
            and second_rep["verdict"] == SMR.WORD_STALE,
            "AC-EDMG1 second-table rows=%d real=%d registry=%d titles=%d"
            " verdict=%s"
            % (second_rows, real, registry_rows,
               SMR.matrix_title_count(second_text, patterns),
               second_rep["verdict"])))

        # AC-EDMG2: a fence opened and never closed is REFUSED by name with the
        # line it was opened on, instead of silently quoting the rest.
        unseen = copy(workdir, "unclosed.md", doctor_unclosed)
        unseen_text = read(unseen)
        open_line = unseen_text.splitlines().index("```") + 1
        unseen_rep = SMR.report(unseen, green)
        code_u, word_u, out_u = one_word_cli(
            ["--doc", unseen, "--evidence", green])
        results.append(check(
            unseen_rep["verdict"] == SMR.WORD_FENCE
            and unseen_rep["exit"] == 3
            and unseen_rep.get("code") == SMR.CODE_FENCE
            and unseen_rep.get("line") == open_line
            and unseen_rep.get("open_marker") == 3
            and code_u == 3 and word_u == SMR.WORD_FENCE
            and ("line=%d" % open_line) in out_u,
            "AC-EDMG2 unclosed verdict=%s code=%s line=%s open-line=%d"
            " cli=%s/%s"
            % (unseen_rep["verdict"], unseen_rep.get("code"),
               unseen_rep.get("line"), open_line, word_u, code_u)))

        # AC-EDMG3: a FOUR-backtick fence carrying a THREE-backtick line is a
        # nested dialect refused naming BOTH markers, and neither quoted row
        # is counted as a matrix row.
        nested = copy(workdir, "nested.md", doctor_nested)
        nested_rows = SMR.doc_rows(read(nested))
        nested_rep = SMR.report(nested, green)
        code_n, word_n, out_n = one_word_cli(
            ["--doc", nested, "--evidence", green])
        results.append(check(
            nested_rep["verdict"] == SMR.WORD_NEST
            and nested_rep["exit"] == 3
            and nested_rep.get("code") == SMR.CODE_NEST
            and nested_rep.get("open_marker") == 4
            and nested_rep.get("inner_marker") == 3
            and nested_rows == real
            and code_n == 3 and word_n == SMR.WORD_NEST
            and "open-marker=````" in out_n and "inner-marker=```" in out_n,
            "AC-EDMG3 nested verdict=%s markers=%s/%s rows=%d real=%d"
            " cli=%s/%s"
            % (nested_rep["verdict"], nested_rep.get("open_marker"),
               nested_rep.get("inner_marker"), nested_rows, real,
               word_n, code_n)))

        # AC-EDMG4: the shipped check face is asked EXACTLY ONCE per reading,
        # so a content difference keeps its content word.
        calls_live = {}
        with patched_check(calls_live):
            live2 = SMR.report(DOC, green)
        calls_diff = {}
        with patched_check(calls_diff):
            diff2 = SMR.report(second, green)
        results.append(check(
            calls_live.get("asked") == 1 and calls_diff.get("asked") == 1
            and live2["verdict"] == SMR.WORD_CURRENT
            and diff2["verdict"] == SMR.WORD_STALE,
            "AC-EDMG4 asked live=%s diff=%s verdict=%s/%s"
            % (calls_live.get("asked"), calls_diff.get("asked"),
               live2["verdict"], diff2["verdict"])))

        # AC-EDMG5: every R2616 answer survives beside the new ones, proved on
        # the same fixtures, plus both counts and the named evidence source.
        quoted = copy(workdir, "quoted.md", doctor_quoted)
        same = copy(workdir, "same.md", doctor_same_header_no_separator)
        other = copy(workdir, "other.md", doctor_other_header)
        none = copy(workdir, "none.md", doctor_no_table)
        narrow = copy(workdir, "narrow.md", doctor_narrow_separator)
        nosep = copy(workdir, "nosep.md", doctor_no_separator)
        dropped = copy(workdir, "dropped.md", doctor_dropped_row)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        walk_rep = SMR.report(DOC, None, pass_dir)
        quoted_rows = SMR.doc_rows(read(quoted))
        same_titles = SMR.matrix_title_count(read(same), patterns)
        other_titles = SMR.matrix_title_count(read(other), patterns)
        other_rep = SMR.report(other, green)
        none_rep = SMR.report(none, green)
        narrow_rep = SMR.report(narrow, green)
        nosep_rep = SMR.report(nosep, green)
        starved = SMR.report(DOC, None, None, 0)
        drop_rep = SMR.report(dropped, green)
        results.append(check(
            quoted_rows == real
            and same_titles == 1
            and other_titles == 2
            and other_rep["verdict"] == SMR.WORD_TITLE
            and other_rep.get("titles") == 2
            and other_rep["exit"] == 3
            and none_rep["verdict"] == SMR.WORD_TABLE
            and none_rep["exit"] == 2
            and narrow_rep["verdict"] == SMR.WORD_HEADER
            and narrow_rep.get("separator_cells") == 2
            and narrow_rep.get("header_cells") == 6
            and nosep_rep["verdict"] == SMR.WORD_SEP
            and nosep_rep["exit"] == 3
            and starved["verdict"] == SMR.WORD_CEILING
            and starved["exit"] == 3
            and drop_rep["verdict"] == SMR.WORD_ROWS
            and drop_rep["doc_rows"] == registry_rows - 1
            and drop_rep["registry_rows"] == registry_rows
            and live["verdict"] == SMR.WORD_CURRENT
            and live.get("evidence_source") == "explicit"
            and walk_rep.get("evidence_source") == "walk",
            "AC-EDMG5 quoted=%d/%d same-titles=%d other=%s(%s) none=%s"
            " narrow=%s/%s nosep=%s starved=%s rows=%s(%d/%d) src=%s/%s"
            % (quoted_rows, real, same_titles, other_rep["verdict"],
               other_rep.get("titles"), none_rep["verdict"],
               narrow_rep["verdict"], narrow_rep.get("separator_cells"),
               nosep_rep["verdict"], starved["verdict"],
               drop_rep["verdict"], drop_rep["doc_rows"],
               drop_rep["registry_rows"], live.get("evidence_source"),
               walk_rep.get("evidence_source"))))

        # AC-EDMG6: hygiene and its own registration.
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
                 if row[0] == "os-suite-matrix-reconcile-fence-table"]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDMG6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
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
