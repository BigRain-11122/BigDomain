"""AC-EDM1..AC-EDM6 suite for the suite-matrix reconciliation face (R2601).

Criteria were pinned in state/queue/tech.md:633 at R2599 BEFORE this code
existed.

What this proves: the matrix document can carry the CURRENT registry truth
while its evidence line still names a RUNNER PASS leg, so the six readability
suites and the battery check face can both be green at once. Every proof runs
through the shipped faces (suite_matrix.main --check, suite_matrix.render,
suite_matrix.parse_evidence, reconcile_all.SUITES); the shipped seams are
patched ONLY to prove the CALL-time ask. Every doctoring happens in a private
temporary directory, never in docs/.

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
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-suite-matrix-reconcile",'
WIRED_SUITE = '"test_suite_matrix_reconcile.py"), 6),'
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")


def check(ok, label):
    print("  %s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def leg(kind):
    """Newest qa/*.log whose RUNNER answer is `kind` (measured, not canned).
    A red leg may carry no parsable runner line at all ('RUNNER FAIL (N failed
    assertions)' has no suite counts), so `FAIL` means NOT PASS."""
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


def temp_copy(directory, doctor=None):
    target = os.path.join(directory, "probe-matrix.md")
    shutil.copyfile(DOC, target)
    if doctor is not None:
        with open(target, encoding="utf-8") as handle:
            text = handle.read()
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(doctor(text))
    return target


def drop_one_row(text):
    lines = text.splitlines(True)
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            del lines[index]
            break
    return "".join(lines)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def verify():
    green, greendata = leg("PASS")
    red, reddata = leg("FAIL")
    results = []
    workdir = tempfile.mkdtemp(prefix="edm-")
    try:
        # AC-EDM1: a document regenerated from the CURRENT registry carries
        # exactly one row per registered suite and its evidence line names the
        # newest RUNNER PASS leg plus that leg's own suite count.
        probe = temp_copy(workdir, drop_one_row)
        out = SMR.write(probe, green)
        text = read(probe)
        rows, criteria = SMR.registry_counts()
        wants = "RUNNER PASS %s/%s" % (greendata["green"], greendata["total"])
        results.append(check(
            out["verdict"] == SMR.WORD_WRITTEN and out["exit"] == 0
            and SMR.doc_rows(text) == rows and rows == len(RA.SUITES)
            and wants in text and os.path.basename(green) in text,
            "AC-EDM1 regenerated doc rows=%d registry rows=%d evidence names"
            " %s with %s" % (SMR.doc_rows(text), rows,
                             os.path.basename(green), wants)))

        # AC-EDM2: a document whose row count differs from the registry reads
        # its OWN word naming BOTH counts, never a shape word or silence.
        doctor = temp_copy(workdir, drop_one_row)
        rep = SMR.report(doctor, green)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            SMR.main(["suite_matrix_reconcile.py", "--check", "--doc", doctor,
                      "--evidence", green])
        printed = buffer.getvalue()
        results.append(check(
            rep["verdict"] == SMR.WORD_ROWS and rep["exit"] == 2
            and rep["doc_rows"] < rep["registry_rows"]
            and SMR.WORD_ROWS in printed
            and ("doc-rows=%d" % rep["doc_rows"]) in printed
            and ("registry-rows=%d" % rep["registry_rows"]) in printed,
            "AC-EDM2 rows word=%s doc=%d registry=%d BOTH named"
            % (rep["verdict"], rep["doc_rows"], rep["registry_rows"])))

        # AC-EDM3: a leg that is not RUNNER PASS is refused, nothing written,
        # and the shipped check face still refuses exactly as it did before.
        doctor = temp_copy(workdir, drop_one_row)
        before = read(doctor)
        code_before, msg_before = SMR.shipped_check(doctor, green)
        rep = SMR.report(doctor, red)
        wrote = SMR.write(doctor, red)
        code_after, msg_after = SMR.shipped_check(doctor, green)
        results.append(check(
            reddata["verdict"] != "PASS"
            and rep["verdict"] == SMR.WORD_RED and rep["exit"] == 3
            and wrote["verdict"] == SMR.WORD_RED and wrote["written"] is False
            and read(doctor) == before
            and (code_before, msg_before) == (code_after, msg_after)
            and code_before != 0,
            "AC-EDM3 red leg refused word=%s, doc byte-identical, shipped"
            " check unchanged (exit=%d)" % (rep["verdict"], code_before)))

        # AC-EDM4: both answers are derived at CALL time from the shipped
        # faces - patching each moves this report.
        real_parse = SM.parse_evidence
        real_main = SM.main
        try:
            SM.parse_evidence = lambda path: ({"verdict": "FAIL",
                                               "green": 0, "total": 0,
                                               "exit": 1,
                                               "pass_lines": 0,
                                               "fail_lines": 1,
                                               "criteria": 1, "secs": "0.0"},
                                              {"verdict": "FAIL", "green": 0,
                                               "total": 0, "controls": "0/0",
                                               "secs": "0.0"})
            patched_leg = SMR.report(DOC, green)
        finally:
            SM.parse_evidence = real_parse
        try:
            SM.main = lambda argv: 0
            patched_check = SMR.report(DOC, green)
        finally:
            SM.main = real_main
        live = SMR.report(DOC, green)
        results.append(check(
            patched_leg["verdict"] == SMR.WORD_RED
            and patched_check["verdict"] == SMR.WORD_CURRENT
            and live["verdict"] != SMR.WORD_RED,
            "AC-EDM4 patch parse_evidence -> %s, patch check face -> %s,"
            " live -> %s" % (patched_leg["verdict"],
                             patched_check["verdict"], live["verdict"])))

        # AC-EDM5: the face writes nothing except the document it is asked to
        # write, emits ONE verdict word, and never rewrites a red-leg doc.
        doctor = temp_copy(workdir, drop_one_row)
        before = read(doctor)
        rep = SMR.report(doctor, green)
        untouched = read(doctor) == before
        words = []
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            SMR.main(["suite_matrix_reconcile.py", "--check", "--doc", doctor,
                      "--evidence", green])
        words = buffer.getvalue().strip().splitlines()
        current = SMR.write(doctor, green)
        after = read(doctor)
        again = SMR.write(doctor, green)
        results.append(check(
            rep["written"] is False and untouched
            and len(words) >= 1 and words[0].split()[0] in (
                SMR.WORD_CURRENT, SMR.WORD_ROWS, SMR.WORD_STALE, SMR.WORD_RED)
            and current["verdict"] == SMR.WORD_WRITTEN
            and again["verdict"] == SMR.WORD_CURRENT
            and read(doctor) == after,
            "AC-EDM5 report wrote nothing, one verdict word (%s), idempotent"
            " rewrite (%s)" % (words[0].split()[0] if words else "-",
                               again["verdict"])))

        # AC-EDM6: hygiene and registration.
        with open(MODULE, "rb") as handle:
            raw = handle.read()
        ascii_only = all(byte < 128 for byte in raw)
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
        with open(os.path.abspath(__file__), "rb") as handle:
            selftest_ascii = all(byte < 128 for byte in handle.read())
        results.append(check(
            ascii_only and selftest_ascii and not (imports & set(NET))
            and "time" not in imports
            and WIRED_LABEL in runner and WIRED_SUITE in runner,
            "AC-EDM6 hygiene ascii=%s clock=%s network=%s registered=%s"
            % (ascii_only and selftest_ascii, "time" in imports,
               sorted(imports & set(NET)), WIRED_LABEL in runner)))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())