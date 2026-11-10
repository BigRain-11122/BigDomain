"""AC-EDMD1..AC-EDMD6 suite for the suite-matrix reconciliation SHAPE face
(R2606).

Criteria were pinned in state/queue/tech.md:638 at R2604 BEFORE this code
existed, from four limits MEASURED there with
src/os/limits_suite_matrix_reconcile_shape_next_R2604.py.

What this proves: a separator drawn with "=" (or any single repeated
punctuation character) is a separator, a header with NO separator row names
the missing separator instead of falling through to a content word, a ceiling
below one candidate refuses by name, and a document carrying the matrix title
more than once refuses by name with the count. Every R2604 answer survives on
the same fixtures.

All doctoring happens in private temporary directories, never in docs/ or qa/.
Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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
WIRED_LABEL = '"os-suite-matrix-reconcile-shape",'
WIRED_SUITE = '"test_suite_matrix_reconcile_shape.py"),'
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


def temp_copy(directory, name="probe-matrix.md", doctor=None):
    target = os.path.join(directory, name)
    shutil.copyfile(DOC, target)
    if doctor is not None:
        with open(target, encoding="utf-8") as handle:
            text = handle.read()
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(doctor(text))
    return target


def title_of():
    return SM.load_patterns()["labels"]["matrix_title"]


def _table_lines(lines):
    """(header_index, separator_index, data_start) of the FIRST matrix table,
    located by position under the shipped title - never by shape guess."""
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
            return header, j, j + 1
        return None
    return None


def doctor_separator(cells, char="-"):
    """Rewrite the matrix separator row to `cells` columns drawn with `char`."""
    def apply(text):
        lines = text.splitlines(True)
        where = _table_lines(lines)
        if not where:
            raise AssertionError("E_EDMD_SUITE_NO_TABLE")
        header, sep, _ = where
        lines[sep] = "|" + char * 3 + ("|" + char * 3) * (cells - 1) + "|\n"
        return "".join(lines)
    return apply


def doctor_header(cells):
    def apply(text):
        lines = text.splitlines(True)
        where = _table_lines(lines)
        if not where:
            raise AssertionError("E_EDMD_SUITE_NO_TABLE")
        header, _, _ = where
        name = "c%d" % cells
        lines[header] = "|" + "|".join([name] * cells) + "|\n"
        return "".join(lines)
    return apply


def doctor_drop_separator(text):
    lines = text.splitlines(True)
    where = _table_lines(lines)
    if not where:
        raise AssertionError("E_EDMD_SUITE_NO_TABLE")
    _, sep, _ = where
    del lines[sep]
    return "".join(lines)


def doctor_drop_table(text):
    lines = text.splitlines(True)
    where = _table_lines(lines)
    if not where:
        raise AssertionError("E_EDMD_SUITE_NO_TABLE")
    header, _, start = where
    title = title_of().strip()
    keep = [line for line in lines
            if line.strip() != title and not line.startswith("|")]
    return "".join(keep)


def doctor_title_twice(text):
    title = title_of().strip()
    lines = text.splitlines(True)
    extra = [line for line in ("\n", title + "\n", "\n",
                               "| a | b | c | d | e | f |\n",
                               "|---|---|---|---|---|---|\n",
                               "| 1 | x | y | 6 | green | 0.1 |\n")]
    return "".join(lines + extra)


def doctor_recorded_evidence(other):
    def apply(text):
        labels = SM.load_patterns()["labels"]
        prefix = "- %s: " % labels["command"]
        out = []
        for line in text.splitlines(True):
            if line.startswith(prefix):
                line = re.sub(r"--evidence \S+", "--evidence " + other, line)
            out.append(line)
        return "".join(out)
    return apply


def one_word_cli(args):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = SMR.main(["suite_matrix_reconcile.py"] + args)
    lines = [line for line in buffer.getvalue().splitlines() if line.strip()]
    return code, (lines[0].split()[0] if lines else ""), buffer.getvalue()


def verify():
    green, greendata = leg("PASS")
    red, reddata = leg("FAIL")
    results = []
    workdir = tempfile.mkdtemp(prefix="edmd-")
    try:
        patterns = SM.load_patterns()

        # AC-EDMD1: a "=" separator is a separator, and a width disagreement
        # against its header refuses by HEADER-SHAPE naming BOTH widths.
        eq_narrow = temp_copy(workdir, "eq-narrow.md",
                              doctor_separator(2, "="))
        narrow = SMR.report(eq_narrow, green)
        eq_wide = temp_copy(workdir, "eq-wide.md",
                            doctor_separator(6, "="))
        wide_shape = SMR.matrix_shape(read(eq_wide), patterns)
        wide = SMR.report(eq_wide, green)
        results.append(check(
            narrow["verdict"] == SMR.WORD_HEADER and narrow["exit"] == 3
            and narrow.get("header_cells") == 6
            and narrow.get("separator_cells") == 2
            and "6" in narrow.get("reason", "")
            and "2" in narrow.get("reason", "")
            and wide_shape == (6, 6)
            and wide["verdict"] not in (SMR.WORD_HEADER, SMR.WORD_SEP),
            "AC-EDMD1 eq-separator 2/6 -> %s cells=%s/%s, eq-separator 6/6"
            " shape=%s verdict=%s"
            % (narrow["verdict"], narrow.get("header_cells"),
               narrow.get("separator_cells"), wide_shape, wide["verdict"]) ))

        # AC-EDMD2: a header carrying NO separator row refuses with its own
        # word naming the missing separator, not a content word.
        no_sep = temp_copy(workdir, "no-sep.md", doctor_drop_separator)
        rep = SMR.report(no_sep, green)
        wrote = SMR.write(no_sep, green)
        before_free = read(no_sep)
        code, word, printed = one_word_cli(["--check", "--doc", no_sep,
                                           "--evidence", green])
        results.append(check(
            rep["verdict"] == SMR.WORD_SEP and rep["exit"] == 3
            and rep.get("code") == SMR.CODE_SEP
            and SMR.WORD_SEP != SMR.WORD_STALE
            and wrote["verdict"] == SMR.WORD_SEP
            and wrote["written"] is False
            and read(no_sep) == before_free
            and word == SMR.WORD_SEP and code == 3
            and "header-cells=6" in printed,
            "AC-EDMD2 no-separator -> %s (code=%s, exit=%d) nothing written,"
            " CLI word=%s rc=%d" % (rep["verdict"], rep.get("code"),
                                    rep["exit"], word, code)))

        # AC-EDMD3: a ceiling below one candidate is refused by name, on the
        # read path and on the compose path, and creates nothing.
        probe = temp_copy(workdir, "ceiling.md")
        before = read(probe)
        rep = SMR.report(probe, None, None, 0)
        wrote = SMR.write(probe, None, None, None, 0)
        code, word, printed = one_word_cli(["--check", "--doc", probe,
                                            "--ceiling", "0"])
        results.append(check(
            rep["verdict"] == SMR.WORD_CEILING and rep["exit"] == 3
            and rep.get("ceiling") == 0
            and rep.get("code") == SMR.CODE_CEILING
            and wrote["verdict"] == SMR.WORD_CEILING
            and wrote["written"] is False
            and read(probe) == before
            and word == SMR.WORD_CEILING and code == 3
            and "ceiling=0" in printed,
            "AC-EDMD3 ceiling 0 -> %s (exit=%d) nothing written, CLI=%s rc=%d"
            % (rep["verdict"], rep["exit"], word, code)))

        # AC-EDMD4: a document carrying the matrix title more than once
        # refuses by name WITH the count, instead of reading the first table.
        twice = temp_copy(workdir, "title-twice.md", doctor_title_twice)
        rep = SMR.report(twice, green)
        wrote = SMR.write(twice, green)
        before = read(twice)
        count = SMR.matrix_title_count(before, patterns)
        code, word, printed = one_word_cli(["--check", "--doc", twice,
                                            "--evidence", green])
        results.append(check(
            count == 2
            and rep["verdict"] == SMR.WORD_TITLE and rep["exit"] == 3
            and rep.get("titles") == 2
            and rep.get("code") == SMR.CODE_TITLE
            and wrote["verdict"] == SMR.WORD_TITLE
            and wrote["written"] is False
            and read(twice) == before
            and word == SMR.WORD_TITLE and code == 3
            and "titles=2" in printed,
            "AC-EDMD4 title lines=%d -> %s titles=%s (exit=%d), nothing"
            " written, CLI=%s rc=%d"
            % (count, rep["verdict"], rep.get("titles"), rep["exit"], word,
               code)))

        # AC-EDMD5: every R2604 answer survives on the same fixtures - both
        # HEADER-SHAPE widths, TABLE-MISSING, the bounded walk, the named
        # evidence source, the R2602 words, both counts, one verdict word on
        # the CLI and the exit codes.
        five = temp_copy(workdir, "header-5.md", doctor_header(5))
        r5 = SMR.report(five, green)
        dash2 = temp_copy(workdir, "dash-2.md", doctor_separator(2, "-"))
        rd = SMR.report(dash2, green)
        gone = temp_copy(workdir, "no-table.md", doctor_drop_table)
        rt = SMR.report(gone, green)
        missing = SMR.report(os.path.join(workdir, "absent.md"), green)
        starved_dir = os.path.join(workdir, "qa-no-pass")
        os.makedirs(starved_dir, exist_ok=True)
        for name in ("leg-one.log", "leg-two.log"):
            with open(os.path.join(starved_dir, name), "w",
                      encoding="utf-8", newline="\n") as handle:
                handle.write("RUNNER FAIL (1 failed assertions)\n")
        rw = SMR.report(DOC, None, starved_dir, 1)
        pass_dir = os.path.join(workdir, "qa-pass")
        os.makedirs(pass_dir, exist_ok=True)
        shutil.copyfile(green, os.path.join(pass_dir, "leg.log"))
        rp = SMR.report(DOC, None, pass_dir)
        rred = SMR.report(DOC, red)
        recorded = doctor_recorded_evidence("qa/edmd-other-leg.log")
        evid = temp_copy(workdir, "evid-face.md", recorded)
        re_ = SMR.report(evid, green)
        drop = temp_copy(workdir, "rows.md", lambda t: t.replace(
            "| 1 | lobby | lobby/test_client.py | 79 | green | 45.2 |\n", ""))
        rr = SMR.report(drop, green)
        live = SMR.report(DOC, green)
        results.append(check(
            r5["verdict"] == SMR.WORD_HEADER and r5.get("cells") == 5
            and r5.get("expected_cells") == 6
            and rd["verdict"] == SMR.WORD_HEADER
            and rd.get("header_cells") == 6
            and rd.get("separator_cells") == 2
            and rt["verdict"] == SMR.WORD_TABLE
            and missing["verdict"] == SMR.WORD_NONE
            and rw["verdict"] == SMR.WORD_RED
            and rw.get("walk", {}).get("bounded") is True
            and rw.get("walk", {}).get("decoded") == 1
            and rp.get("evidence_source") == "walk"
            and rred["verdict"] == SMR.WORD_RED
            and rred.get("evidence_source") == "explicit"
            and re_["verdict"] == SMR.WORD_EVID
            and re_.get("recorded_evidence") == "qa/edmd-other-leg.log"
            and rr["verdict"] == SMR.WORD_ROWS
            and rr["doc_rows"] < rr["registry_rows"]
            and live["verdict"] == (SMR.WORD_CURRENT
                                    if live.get("doc_rows") ==
                                    live.get("registry_rows")
                                    else SMR.WORD_ROWS),
            "AC-EDMD5 header5=%s(dash2=%s/%s) table=%s nodoc=%s"
            " walk=%s(bounded=%s,decoded=%s) src=%s/%s evid=%s(%s)"
            " rows=%s(%d<%d) live=%s"
            % (r5["verdict"], rd.get("header_cells"),
               rd.get("separator_cells"), rt["verdict"], missing["verdict"],
               rw["verdict"], rw.get("walk", {}).get("bounded"),
               rw.get("walk", {}).get("decoded"), rp.get("evidence_source"),
               rred.get("evidence_source"), re_["verdict"],
               re_.get("recorded_evidence"), rr["verdict"], rr["doc_rows"],
               rr["registry_rows"], live["verdict"])))

        # AC-EDMD6: hygiene and its own registration.
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
                 if row[0] == "os-suite-matrix-reconcile-shape"]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDMD6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
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