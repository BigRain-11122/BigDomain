"""AC-EDMB1..AC-EDMB6 suite for the matrix reconciliation evidence face (R2602).

Criteria were pinned in state/queue/tech.md:634 at R2601 BEFORE this code
existed, from three limits MEASURED in that window: an explicit RUNNER PASS
leg that differs from the leg the document records read STALE-CONTENT (a
content word for an evidence-face difference), the newest_pass_leg walk
decoded every file with no bound and no count, and a document that does not
exist read NO-DOC under --write as well as --check.

Every proof runs through the shipped faces (suite_matrix.main --check,
suite_matrix.parse_evidence, suite_matrix.doc_evidence_face,
reconcile_all.SUITES). The shipped seams are patched ONLY to prove the
CALL-time ask. Every doctoring happens in a private temporary directory,
never in docs/.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

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
WIRED_LABEL = '"os-suite-matrix-reconcile-evidence-face",'
WIRED_SUITE = "test_suite_matrix_reconcile_evidence_face.py"
LABEL = "os-suite-matrix-reconcile-evidence-face"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")
PASS_LEG = "RUNNER PASS (2/2 suites green, reconcile controls 7/7, 1.0s)"
RED_LEG = "RUNNER FAIL (5 failed assertions)\n"


def check(ok, label):
    print("  %s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def recorded_leg():
    """The leg the real document records, resolved to a path. Returns
    (path, run) or (None, None) when the document names no PASS leg."""
    recorded = SM.doc_evidence_face(read(DOC), SM.load_patterns())
    if recorded is None:
        return None, None
    path = os.path.join(REPO, recorded)
    if not os.path.exists(path):
        return None, None
    _, run = SM.parse_evidence(path)
    if run is None or run["verdict"] != "PASS":
        return None, None
    return path, run


def other_pass_leg(workdir):
    """A RUNNER PASS leg that is NOT the leg the document records, built as a
    fixture and read through the SHIPPED parser, so the case is deterministic
    and costs one small file instead of decoding the whole evidence pile."""
    path = os.path.join(workdir, "probe-pass-leg.log")
    write_text(path, PASS_LEG + "\n")
    _, run = SM.parse_evidence(path)
    return path, run, "fixture"


def temp_copy(directory, name, doctor=None):
    target = os.path.join(directory, name)
    shutil.copyfile(DOC, target)
    if doctor is not None:
        write_text(target, doctor(read(target)))
    return target


def drop_one_row(text):
    lines = text.splitlines(True)
    for index, line in enumerate(lines):
        if SMR.ROW_RE.match(line):
            del lines[index]
            break
    return "".join(lines)


def drift_text(text):
    return text + "\n- drifted line: this document no longer equals its render\n"


def reshape_header(text):
    """Give the matrix table a FIVE-cell header so the row counter would read
    zero rows - the shape AC-EDMB4 says must be refused by name."""
    patterns = SM.load_patterns()
    title = patterns["labels"]["matrix_title"]
    lines = text.splitlines(True)
    inside = False
    for index, line in enumerate(lines):
        if line.strip() == title.strip():
            inside = True
            continue
        if inside and line.startswith("|"):
            cells = line.rstrip("\n").split("|")
            # ['', ' c1 ', ' c2 ', ..., '']
            del cells[2]
            lines[index] = "|".join(cells) + "\n"
            return "".join(lines)
    return text


def cli(args):
    buffer = io.StringIO()
    stdout = sys.stdout
    sys.stdout = buffer
    try:
        code = SMR.main(["suite_matrix_reconcile.py"] + args)
    finally:
        sys.stdout = stdout
    return code, buffer.getvalue()


def verify():
    recorded_path, recorded_run = recorded_leg()
    results = []
    workdir = tempfile.mkdtemp(prefix="edmb-")
    try:
        if recorded_path is None:
            results.append(check(False, "AC-EDMB0 precondition: the live"
                                        " document records no PASS leg"))
            print("SUITE FAIL %d/%d" % (sum(results),
                                       EXPECTED_CRITERIA))
            return 1
        other_path, other_run, other_kind = other_pass_leg(workdir)

        # AC-EDMB1: an explicit RUNNER PASS leg that DIFFERS from the leg the
        # document records reads its OWN word naming BOTH legs, never a
        # content word - and the ask is derived from the shipped
        # doc_evidence_face at CALL time (patching it moves the answer).
        doctor = temp_copy(workdir, "probe-matrix.md")
        code, out = cli(["--check", "--doc", doctor,
                         "--evidence", other_path])
        rep = SMR.report(doctor, other_path)
        real_face = SM.doc_evidence_face
        try:
            SM.doc_evidence_face = lambda text, patterns: SMR.rel(other_path)
            patched = SMR.report(doctor, other_path)
        finally:
            SM.doc_evidence_face = real_face
        results.append(check(
            other_run is not None and other_run["verdict"] == "PASS"
            and os.path.abspath(other_path) != os.path.abspath(recorded_path)
            and rep["verdict"] == SMR.WORD_EVID and rep["exit"] == 2
            and code == 2 and out.split()[0] == SMR.WORD_EVID
            and rep["recorded_evidence"] != rep["evidence"]
            and "recorded-evidence=%s" % rep["recorded_evidence"] in out
            and "named-evidence=%s" % rep["evidence"] in out
            and patched["verdict"] != SMR.WORD_EVID,
            "AC-EDMB1 evidence-face=%s (%s leg) both legs named, patched"
            " doc_evidence_face -> %s"
            % (rep["verdict"], other_kind, patched["verdict"])))

        # AC-EDMB2: the candidate walk reports what it decoded, stops at the
        # first PASS leg, and its cost is printed rather than hidden.
        probe_qa = os.path.join(workdir, "probe-qa")
        os.makedirs(probe_qa)
        names = ["zz-newest.log", "yy-pass.log", "xx-oldest.log"]
        bodies = ["STATUS unknown\n", PASS_LEG + "\n", PASS_LEG + "\n"]
        for name, body in zip(names, bodies):
            write_text(os.path.join(probe_qa, name), body)
            # pin the age order the walk sorts by (mtime newest first)
        for offset, name in enumerate(names):
            os.utime(os.path.join(probe_qa, name),
                     (1000 - offset, 1000 - offset))
        walk_path, walk_run, walk = SMR.newest_pass_leg_scanned(probe_qa)
        walked = SMR.report(DOC, None, probe_qa)
        printed = "evidence-walk considered=%d decoded=%d" % (
            walk["considered"], walk["decoded"])
        _, out2 = cli(["--check", "--doc", DOC, "--qa-dir", probe_qa])
        results.append(check(
            walk_path is not None and walk_run is not None
            and os.path.basename(walk_path) == "yy-pass.log"
            and walk["considered"] == 3 and walk["decoded"] == 2
            and walked.get("walk") == {"considered": 3, "decoded": 2}
            and printed in out2,
            "AC-EDMB2 walk stopped at %s considered=%d decoded=%d printed=%s"
            % (os.path.basename(walk_path) if walk_path else "-",
               walk["considered"], walk["decoded"], printed in out2)))

        # AC-EDMB3: a MISSING document is composed from a --stamp-from source;
        # with no source it still reads NO-DOC and writes nothing. ONE
        # criterion carries both halves.
        target = os.path.join(workdir, "composed-matrix.md")
        composed = SMR.write(target, recorded_path, None, DOC)
        text = read(target)
        rows, criteria = SMR.registry_counts()
        source_stamp = SM.doc_stamp(read(DOC), SM.load_patterns())
        missing = os.path.join(workdir, "never-written.md")
        bare = SMR.write(missing, recorded_path)
        code3, out3 = cli(["--write", "--doc", missing,
                           "--evidence", recorded_path])
        composed_ok = (composed["verdict"] == SMR.WORD_WRITTEN
                       and composed["exit"] == 0
                       and composed["written"] is True
                       and os.path.exists(target)
                       and SMR.doc_rows(text) == rows
                       and source_stamp is not None and source_stamp in text
                       and "--stamp-from docs/sandbox-suite-matrix.md" in text)
        bare_ok = (bare["verdict"] == SMR.WORD_NONE and bare["exit"] == 2
                   and bare["written"] is False
                   and not os.path.exists(missing) and code3 == 2
                   and out3.split()[0] == SMR.WORD_NONE)
        results.append(check(
            composed_ok and bare_ok,
            "AC-EDMB3 composed=%s (%d rows/%d criteria, stamp %s carried),"
            " no --stamp-from=%s exit=%d wrote nothing=%s"
            % (composed["verdict"], composed.get("doc_rows", 0), criteria,
               source_stamp, bare["verdict"], code3,
               not os.path.exists(missing))))

        # AC-EDMB4: a matrix table that is not six cells refuses by HEADER
        # SHAPE naming the counts, instead of reading zero rows.
        reshaped = temp_copy(workdir, "probe-header.md", reshape_header)
        shape = SMR.matrix_header_cells(read(reshaped), SM.load_patterns())
        rep4 = SMR.report(reshaped, recorded_path)
        code4, out4 = cli(["--check", "--doc", reshaped,
                           "--evidence", recorded_path])
        wrote4 = SMR.write(reshaped, recorded_path)
        results.append(check(
            shape == 5 and rep4["verdict"] == SMR.WORD_HEADER
            and rep4["exit"] == 3 and rep4["cells"] == 5
            and rep4["expected_cells"] == SMR.MATRIX_CELLS
            and SMR.CODE_HEADER in out4 and "cells=5" in out4
            and code4 == 3 and wrote4["verdict"] == SMR.WORD_HEADER
            and wrote4["written"] is False,
            "AC-EDMB4 header cells=%d -> %s %s exit=%d, write refused"
            % (shape, rep4["verdict"], rep4["code"], code4)))

        # AC-EDMB5: every R2601 answer survives beside the new ones - the five
        # words, both counts, one verdict word on the CLI and the exit codes -
        # proved on the SAME fixtures.
        rows_case = temp_copy(workdir, "probe-rows.md", drop_one_row)
        rep_rows = SMR.report(rows_case, recorded_path)
        code_r, out_r = cli(["--check", "--doc", rows_case,
                             "--evidence", recorded_path])
        stale_case = temp_copy(workdir, "probe-stale.md", drift_text)
        rep_stale = SMR.report(stale_case, recorded_path)
        code_s, out_s = cli(["--check", "--doc", stale_case,
                             "--evidence", recorded_path])
        red_path = os.path.join(workdir, "probe-red-leg.log")
        write_text(red_path, RED_LEG)
        rep_red = SMR.report(DOC, red_path)
        code_red, out_red = cli(["--check", "--doc", DOC,
                                 "--evidence", red_path])
        absent = os.path.join(workdir, "absent.md")
        rep_none = SMR.report(absent, recorded_path)
        code_none, out_none = cli(["--check", "--doc", absent,
                                   "--evidence", recorded_path])
        rep_cur = SMR.report(DOC, recorded_path)
        code_cur, out_cur = cli(["--check", "--doc", DOC,
                                 "--evidence", recorded_path])
        firsts = [o.split()[0] for o in (out_r, out_s, out_red, out_none,
                                        out_cur) if o.strip()]
        results.append(check(
            rep_rows["verdict"] == SMR.WORD_ROWS and code_r == 2
            and rep_rows["doc_rows"] < rep_rows["registry_rows"]
            and ("doc-rows=%d" % rep_rows["doc_rows"]) in out_r
            and ("registry-rows=%d" % rep_rows["registry_rows"]) in out_r
            and rep_stale["verdict"] == SMR.WORD_STALE and code_s == 2
            and rep_red["verdict"] == SMR.WORD_RED and code_red == 3
            and rep_red["written"] is False
            and rep_none["verdict"] == SMR.WORD_NONE and code_none == 2
            and rep_cur["verdict"] == SMR.WORD_CURRENT and code_cur == 0
            and firsts == [rep_rows["verdict"], rep_stale["verdict"],
                           rep_red["verdict"], rep_none["verdict"],
                           rep_cur["verdict"]]
            and all(len(o.strip().splitlines()[0].split()) == 2
                    for o in (out_r, out_s, out_red, out_none, out_cur)),
            "AC-EDMB5 five words kept: %s -> [%s]"
            % (",".join(firsts), ",".join(
                str(c) for c in (code_r, code_s, code_red, code_none,
                                 code_cur)))))

        # AC-EDMB6: hygiene and registration.
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
        rows = [row for row in RA.SUITES if row[0] == LABEL]
        registered = (len(rows) == 1 and rows[0][2] == EXPECTED_CRITERIA
                      and WIRED_SUITE in rows[0][1].replace("\\", "/"))
        results.append(check(
            ascii_only and selftest_ascii and not (imports & set(NET))
            and "time" not in imports
            and WIRED_LABEL in runner and registered,
            "AC-EDMB6 hygiene ascii=%s clock=%s network=%s registered=%s (%d"
            " rows, %d criteria)"
            % (ascii_only and selftest_ascii, "time" in imports,
               sorted(imports & set(NET)), registered, len(rows),
               rows[0][2] if rows else 0)))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())