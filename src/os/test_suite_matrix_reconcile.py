"""AC-EDM1..AC-EDM7 suite for the suite-matrix reconciliation face (R2601).

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

EXPECTED_CRITERIA = 15
MODULE = os.path.join(BASE, "suite_matrix_reconcile.py")
DOC = os.path.join(REPO, "docs", "sandbox-suite-matrix.md")
QA_DIR = os.path.join(REPO, "qa")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-suite-matrix-reconcile",'
WIRED_SUITE = '"test_suite_matrix_reconcile.py"), 15),'
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


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def mini_doc(rows):
    """A private matrix document: the shipped title, header, separator, rows.

    AC-EDML: every fixture is built in memory from the shipped label face, so
    no fixture carries a hand-copied title and no file is written."""
    title = SM.load_patterns()["labels"]["matrix_title"].strip()
    lines = [title,
             "| # | suite | path | criteria | state | secs |",
             "|---|---|---|---|---|---|"] + list(rows)
    return "\n".join(lines) + "\n"


NUM_HEAD = "| 1 | Suite | Path | Criteria | State | Secs |"
WORD_HEAD = "| # | Suite | Path | Criteria | State | Secs |"
SEP_OWN = "| --- | --- | --- | --- | --- | --- |"
SEP_NARROW = "|---|---|---|---|---|"
ROW_A = "| 1 | suite-a | a.py | 6 | green | 0.4 |"
ROW_B = "| 2 | suite-b | b.py | 7 | green | 0.5 |"
ROW_DASH = "| 3 | suite-c | c.py | 12 | no-evidence | - |"


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

        # AC-EDM7 (R3150): the live document is recognised by PATH IDENTITY,
        # so a case-variant spelling of it takes the same scratch cross-check
        # instead of being judged as some other document. p after normalising
        # the scratch copy's own temp name, the variant and the plain spelling
        # answer the SAME text - before this arm existed the variant was
        # handed to the shipped face on the LIVE path, a different question
        # with a different answer; q neither answer is an ownership token,
        # i.e. both were judged rather than refused; r a path that does not
        # exist is not a live document - no scratch copy, no ownership token,
        # a non-zero answer.
        plain_code, plain_out = SMR.shipped_check(DOC, green)
        variant_code, variant_out = SMR.shipped_check(DOC.upper(), green)
        missing_path = os.path.join(workdir, "no-such-matrix.md")
        missing_code, missing_out = SMR.shipped_check(missing_path, green)

        def face(text):
            lines = text.splitlines()
            if lines and len(lines[0].split()) > 2:
                parts = lines[0].split()
                parts[2] = "<doc>"
                lines[0] = " ".join(parts)
            return "\n".join(lines)

        judged_words = ("doc-current", "rows-mismatch", "red-leg", "stale",
                        "evidence-face")
        word = next((w for w in judged_words if w in plain_out.lower()), "-")
        results.append(check(
            plain_code == variant_code and face(plain_out) == face(variant_out)
            and word != "-" and "E_SMX" not in plain_out + variant_out
            and missing_code != 0 and "E_SMX" not in missing_out,
            "AC-EDM7 case variant answers %s (%d, %s) exactly as the plain"
            " path; missing path exits %d without an ownership token"
            % ("same text" if face(plain_out) == face(variant_out)
               else "different text", variant_code, word, missing_code)))

        # AC-EDMK1: the LIVE leg is the leg the DOCUMENT records; the newest
        # PASS in the pile is only a fallback. The three fallbacks are proved
        # on their own document text, and the negative control keeps AC-EDMB1
        # alive: a newest PASS that DIFFERS from the record still reads
        # EVIDENCE-FACE, so this narrows WHICH leg is held, never the law.
        text_live = read(DOC)
        recorded = SM.doc_evidence_face(text_live, SM.load_patterns())
        recorded_path = (os.path.join(REPO, recorded) if recorded else None)
        live_path, live_run, live_source = SMR.live_pass_leg()
        newest_path, _newest_run = SMR.newest_pass_leg()
        others = [p for p in [os.path.join(QA_DIR, n)
                              for n in os.listdir(QA_DIR) if n.endswith(".log")]
                  if recorded_path and os.path.abspath(p) != os.path.abspath(
                      recorded_path)]
        control = None
        for candidate in others:
            try:
                _raw, cand_run = SM.parse_evidence(candidate)
            except (OSError, UnicodeDecodeError):
                continue
            if cand_run and cand_run["verdict"] == "PASS":
                control = SMR.report(DOC, candidate)
                break
        fallbacks = []
        if recorded:
            absent_doc = os.path.join(workdir, "absent-leg.md")
            write_text(absent_doc, text_live.replace(
                recorded, "qa/no-such-leg-R3172.log"))
            red_doc = os.path.join(workdir, "red-leg.md")
            red_name = os.path.basename(red[0]) if isinstance(red, tuple) else red
            write_text(red_doc, text_live.replace(
                recorded, "qa/" + red_name))
            none_doc = os.path.join(workdir, "no-leg.md")
            write_text(none_doc, text_live.replace(recorded, "none"))
            saved = SMR.DOC
            try:
                for path in (absent_doc, red_doc, none_doc):
                    SMR.DOC = path
                    fallbacks.append(SMR.live_pass_leg())
            finally:
                SMR.DOC = saved
        helpers = []
        for name in ("fence", "fence_rows", "fence_table", "row_membership",
                     "row_shape", "second_table_separator", "shape",
                     "table_shape"):
            with open(os.path.join(BASE, "test_suite_matrix_reconcile_%s.py"
                                  % name), encoding="utf-8") as handle:
                helpers.append("SMR.live_pass_leg" in handle.read())
        results.append(check(
            recorded_path is not None
            and live_source == "recorded"
            and live_path is not None
            and os.path.abspath(live_path) == os.path.abspath(recorded_path)
            and live_run["verdict"] == "PASS"
            and (control is None or (control["verdict"] == SMR.WORD_EVID
                                     and control["exit"] == 2))
            and len(fallbacks) == 3
            and all(one[2] == "newest" for one in fallbacks)
            and all((one[0] is None) == (newest_path is None)
                    for one in fallbacks)
            and (newest_path is None or all(
                os.path.abspath(one[0]) == os.path.abspath(newest_path)
                for one in fallbacks))
            and all(helpers),
            "AC-EDMK1 live source=%s same-as-recorded=%s control=%s"
            " fallbacks=%s helpers=%d/8"
            % (live_source,
               live_path is not None
               and os.path.abspath(live_path) == os.path.abspath(recorded_path),
               control["verdict"] if control else "no-other-leg",
               [one[2] for one in fallbacks], sum(helpers))))

        # AC-EDML1: a numbered second-table header is NOT a data row and ENDS
        # the first table. Measured at HEAD before the law, the same three
        # fixtures read delta +2 (no separator), +2 (narrow separator) and +1
        # (trailing header) because ROW_RE was asked before the header law.
        no_sep = SMR.doc_rows_scan(mini_doc([ROW_A, NUM_HEAD, ROW_B]))
        narrow = SMR.doc_rows_scan(mini_doc(
            [ROW_A, NUM_HEAD, SEP_NARROW, ROW_B]))
        trailing = SMR.doc_rows_scan(mini_doc([ROW_A, NUM_HEAD]))
        results.append(check(
            no_sep[0] == 1 and no_sep[1] == (6, None, SMR.WORD_NUMHEAD)
            and narrow[0] == 1 and narrow[1] == (6, 5, SMR.WORD_NUMHEAD)
            and trailing[0] == 1
            and trailing[1] == (6, None, SMR.WORD_NUMHEAD),
            "AC-EDML1 numbered header ends the table: no-sep=%r narrow=%r"
            " trailing=%r" % (no_sep, narrow, trailing)))

        # AC-EDML2: a numbered header carrying a separator of its OWN width
        # still opens another table in silence - the AC-EDMI2 answer byte for
        # byte, proved beside a header whose first cell is a word.
        own = SMR.doc_rows_scan(mini_doc([ROW_A, NUM_HEAD, SEP_OWN, ROW_B]))
        word_own = SMR.doc_rows_scan(mini_doc(
            [ROW_A, WORD_HEAD, SEP_OWN, ROW_B]))
        results.append(check(
            own == (1, None) and word_own == (1, None),
            "AC-EDML2 own-width separator stays silent: numbered=%r word=%r"
            % (own, word_own)))

        # AC-EDML3: every well-formed data row is counted exactly once - the
        # shipped dash row included - and the AC-EDMJ/AC-EDMH1 answers survive
        # byte for byte (their problem tuples are still TWO elements).
        counted = SMR.doc_rows_scan(mini_doc([ROW_A, ROW_DASH, ROW_B]))
        malformed = SMR.doc_rows_scan(mini_doc(["| 9 | broken | b.py |",
                                                ROW_B]))
        stray_narrow = SMR.doc_rows_scan(mini_doc(
            [ROW_A, WORD_HEAD, SEP_NARROW, ROW_B]))
        stray_none = SMR.doc_rows_scan(mini_doc([ROW_A, WORD_HEAD, ROW_B]))
        results.append(check(
            counted[0] == 3 and counted[1] is None
            and SMR.is_data_row(ROW_A) and SMR.is_data_row(ROW_DASH)
            and not SMR.is_data_row(NUM_HEAD)
            and not SMR.is_data_row(ROW_DASH.replace("-", "n/a"))
            and malformed[0] == 1 and malformed[1] is None
            and stray_narrow[1] == (6, 5) and stray_none[1] == (6, None)
            and stray_narrow[0] == 1 and stray_none[0] == 1,
            "AC-EDML3 rows survive: counted=%r dash=%s malformed=%r"
            " stray=%r/%r" % (counted, SMR.is_data_row(ROW_DASH), malformed,
                              stray_narrow, stray_none)))

        # AC-EDML4: the LIVE document loses nothing to the value law, and the
        # shipped check still reads current on it.
        live_text = read(DOC)
        live_shaped = [line for line in live_text.splitlines()
                       if SMR.ROW_RE.match(line)]
        live_rep = SMR.report()
        results.append(check(
            all(SMR.is_data_row(line) for line in live_shaped)
            and SMR.doc_rows(live_text) == len(live_shaped)
            == SMR.registry_counts()[0]
            and live_rep["verdict"] == SMR.WORD_CURRENT
            and live_rep["exit"] == 0,
            "AC-EDML4 live doc rows=%d shaped=%d registry=%d verdict=%s"
            % (SMR.doc_rows(live_text), len(live_shaped),
               SMR.registry_counts()[0], live_rep["verdict"])))

        # AC-EDML5: the value law is asked at CALL time and the SHAPE law is
        # untouched - a numbered header still matches ROW_RE while the value
        # law refuses it, and patching the value law moves the count.
        saved_pred = SMR.is_data_row
        try:
            SMR.is_data_row = lambda line: bool(SMR.ROW_RE.match(line))
            patched = SMR.doc_rows_scan(mini_doc([ROW_A, NUM_HEAD, ROW_B]))
        finally:
            SMR.is_data_row = saved_pred
        results.append(check(
            bool(SMR.ROW_RE.match(NUM_HEAD)) and not saved_pred(NUM_HEAD)
            and patched[0] == 3 and patched[1] is None
            and SMR.doc_rows_scan(mini_doc([ROW_A, NUM_HEAD, ROW_B]))[0] == 1,
            "AC-EDML5 shape-vs-value split: shape=%s value=%s patched=%d"
            % (bool(SMR.ROW_RE.match(NUM_HEAD)), saved_pred(NUM_HEAD),
               patched[0])))

        # AC-EDML6: hygiene - both laws and the dash decision live in the
        # module, the registry carries this suite's criteria count, and the
        # module stays ASCII and clock/network free.
        with open(MODULE, "rb") as handle:
            law_raw = handle.read()
        with open(MODULE, encoding="utf-8") as handle:
            law_src = handle.read()
        registry_row = [row for row in RA.SUITES
                        if str(row[1]).replace("\\", "/").endswith(
                            "os/test_suite_matrix_reconcile.py")]
        results.append(check(
            all(byte < 128 for byte in law_raw)
            and law_src.count("def is_data_row(") == 1
            and law_src.count("def numbered_header(") == 1
            and "SECS_DASH" in law_src
            and len(registry_row) == 1
            and registry_row[0][2] == EXPECTED_CRITERIA,
            "AC-EDML6 hygiene ascii=%s laws=%d registry=%r"
            % (all(byte < 128 for byte in law_raw),
               law_src.count("def is_data_row(")
               + law_src.count("def numbered_header("),
               registry_row[0][2] if len(registry_row) == 1 else None)))

        # AC-EDM7 (R3324): a registry carrying a DUPLICATE label is refused at
        # CALL time with the runner's own word. Measured at R3323 and re-used
        # here as the fixture: the shipped render answers TWO-ROWS for a
        # duplicated registry while the doc row count still agrees with
        # SUITES, so a hand-edited registry plus a stale PASS leg could publish
        # a duplicated row and still read DOC-CURRENT.
        live_text7 = read(DOC)
        row7 = [line for line in live_text7.splitlines()
                if line.startswith("| ") and
                "| os-suite-matrix-reconcile |" in line]
        dup_doc7 = os.path.join(workdir, "dup-registry.md")
        body7 = []
        for line in live_text7.splitlines():
            body7.append(line)
            if row7 and line == row7[0]:
                body7.append(line)
        write_text(dup_doc7, "\n".join(body7) + "\n")
        saved_rows7 = RA.SUITES
        dup_dups7 = None
        try:
            RA.SUITES = list(saved_rows7) + [
                row for row in saved_rows7
                if row[0] == "os-suite-matrix-reconcile"]
            dup_dups7 = RA.registry_dups(RA.SUITES)
            refused7 = SMR.report(dup_doc7)
            before7 = open(dup_doc7, "rb").read()
            wrote7 = SMR.write(dup_doc7)
            after7 = open(dup_doc7, "rb").read()
            saved_gate7 = SMR.registry_dups_answer
            try:
                SMR.registry_dups_answer = lambda *a, **k: None
                control7 = SMR.report(dup_doc7)
            finally:
                SMR.registry_dups_answer = saved_gate7
        finally:
            RA.SUITES = saved_rows7
        live_dups7 = RA.registry_dups(RA.SUITES)
        results.append(check(
            len(row7) == 1 and live_dups7 == []
            and RA.registry_dups(RA.SUITES + [
                row for row in RA.SUITES
                if row[0] == "os-suite-matrix-reconcile"]) == dup_dups7
            and dup_dups7 == ["os-suite-matrix-reconcile"]
            and refused7["verdict"] == SMR.WORD_DUP
            and refused7["code"] == SMR.CODE_DUP and refused7["exit"] == 3
            and refused7["written"] is False
            and wrote7["verdict"] == SMR.WORD_DUP and before7 == after7
            and control7["verdict"] != SMR.WORD_DUP,
            "AC-EDM7 duplicate registry refused: live_dups=%r dup=%r"
            " report=%s write=%s control=%s doc_bytes_moved=%s"
            % (live_dups7, dup_dups7, refused7["verdict"], wrote7["verdict"],
               control7["verdict"], before7 != after7)))

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