"""AC-EDWX1..AC-EDWX6 suite for the composed/landed BOM PRECEDENCE SECOND WAVE.

Criteria were pinned in state/queue/tech.md:661 at R2643 BEFORE this code
existed, from five shapes that window MEASURED with
src/os/limits_export_composed_landed_next_R2643.py and this window re-measured
before any byte was written (qa/limits-export-composed-landed-bom-precedence-next-R2643.log):

    a_truncated_mixed  TRANSPORT-MIXED     bom=0 (truncation fact lost)
    b_utf16_empty      UTF16-BOM-LANDING   bom=2 disk=2 (marker read as landing)
    c_bom_only         BOM-LANDING         delta=0 (empty payload read clean)
    d_utf16_no_bom     COMPOSED-MISMATCH   delta=12 (no marker names encoding)
    e_legit_ef_start   PASS                (already correct, named)

What this proves: a truncated prefix over a MIXED body names BOTH facts in ONE
word (X1); a UTF-16 marker with no body names that it carries nothing (X2); a
BOM-only landing names its empty payload instead of reading clean (X3); a
payload whose encoding no marker names still reads the compare word with BOTH
counts rather than a guessed encoding (X4); every AC-EDWW and AC-EDWV answer
survives on the same fixtures (X5); and the module stays pure ASCII, stdlib
only, no clock, no network, registered exactly once with its own suite (X6).

Fixtures live in private temporary directories. Stdlib only, ASCII source.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import export_composed_landed_face as CLF  # noqa: E402
import export_R2431 as EX  # noqa: E402
import reconcile_all as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_composed_landed_face.py")
WIRED = os.path.join(BASE,
                     "test_export_composed_landed_bom_precedence_second_wave.py")
PARENT_SUITE = os.path.join(BASE,
                            "test_export_composed_landed_bom_precedence.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-second-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

TEXT = '{\n "a": 1\n}\n'
CRLF = TEXT.replace("\n", "\r\n")
BOM = b"\xef\xbb\xbf"


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def fingerprint(path):
    rows = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if os.path.isfile(full):
            with open(full, "rb") as handle:
                raw = handle.read()
            rows.append((name, len(raw), hashlib.sha256(raw).hexdigest()))
    return rows


def write_bytes(path, data):
    with open(path, "wb") as handle:
        handle.write(data)


def verify():
    results = []
    workdir = tempfile.mkdtemp(prefix="edwx2646-suite-")
    try:
        trunc_mixed = os.path.join(workdir, "trunc_mixed.json")
        utf16_only = os.path.join(workdir, "utf16_only.json")
        utf16_be_only = os.path.join(workdir, "utf16_be_only.json")
        bom_only = os.path.join(workdir, "bom_only.json")
        utf16_no_bom = os.path.join(workdir, "utf16_no_bom.json")
        legit = os.path.join(workdir, "legit_ef.json")

        write_bytes(trunc_mixed, b"\xef\xbb" + b'{\r\n "a": 1\n}\r\n')
        write_bytes(utf16_only, b"\xff\xfe")
        write_bytes(utf16_be_only, b"\xfe\xff")
        write_bytes(bom_only, BOM)
        write_bytes(utf16_no_bom, TEXT.encode("utf-16-le"))
        write_bytes(legit, "\uf000".encode("utf-8") + b'{"x":2}\n')

        # --- AC-EDWX1: truncation and transport named in ONE word.
        rep_tm = CLF.account(trunc_mixed, TEXT)
        line_tm = CLF.render(rep_tm)
        results.append(check(
            rep_tm["word"] == CLF.WORD_BOM_TRUNCATED_MIXED
            and rep_tm["word"] != CLF.WORD_TRANSPORT_MIXED
            and rep_tm["word"] != CLF.WORD_BOM_TRUNCATED
            and rep_tm["word"] != CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep_tm["transport"] == CLF.TRANSPORT_MIXED
            and rep_tm["bom"] == 2
            and rep_tm["bom_kind"] == "utf8-truncated"
            and rep_tm["composed"] == len(TEXT.encode("utf-8"))
            and rep_tm["disk"] == 16
            and rep_tm["delta"] == 4
            and "TRUNCATED" in line_tm and "MIXED" in line_tm,
            "AC-EDWX1 trunc_mixed word=%s transport=%s bom=%d disco=%s"
            " disk=%d delta=%s line=%s"
            % (rep_tm["word"], rep_tm["transport"], rep_tm["bom"],
               rep_tm["composed"], rep_tm["disk"], rep_tm["delta"], line_tm)))

        # --- AC-EDWX2: a UTF-16 marker with NOTHING behind it is named.
        rep_u = CLF.account(utf16_only, "")
        rep_ub = CLF.account(utf16_be_only, "")
        line_u = CLF.render(rep_u)
        results.append(check(
            rep_u["word"] == CLF.WORD_UTF16_BOM_MARKER_ONLY
            and rep_ub["word"] == CLF.WORD_UTF16_BOM_MARKER_ONLY
            and rep_u["word"] != CLF.WORD_UTF16_BOM
            and rep_u["word"] != CLF.WORD_EMPTY_LANDING
            and rep_u["bom"] == 2 and rep_ub["bom"] == 2
            and rep_u["bom_kind"] == "utf16-empty"
            and rep_u["composed"] is None and rep_u["delta"] is None
            and rep_u["disk"] == 2
            and "MARKER-ONLY" in line_u,
            "AC-EDWX2 utf16_only le=%s/%s be=%s bom=%d disk=%d line=%s"
            % (rep_u["word"], rep_u["bom_kind"], rep_ub["word"],
               rep_u["bom"], rep_u["disk"], line_u)))

        # --- AC-EDWX3: a BOM-only landing names its EMPTY payload.
        rep_bo = CLF.account(bom_only, "")
        line_bo = CLF.render(rep_bo)
        results.append(check(
            rep_bo["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep_bo["word"] != CLF.WORD_BOM_LANDING
            and rep_bo["word"] != CLF.WORD_EMPTY_LANDING
            and rep_bo["bom"] == 3
            and rep_bo["bom_kind"] == "utf8-empty"
            and rep_bo["composed"] is None
            and rep_bo["delta"] is None
            and rep_bo["disk"] == 3
            and "EMPTY-PAYLOAD" in line_bo,
            "AC-EDWX3 bom_only word=%s bom=%d kind=%s disk=%d line=%s"
            % (rep_bo["word"], rep_bo["bom"], rep_bo["bom_kind"],
               rep_bo["disk"], line_bo)))

        # --- AC-EDWX4: an unnamed encoding reads the compare word with BOTH
        # counts, never a guessed encoding.
        rep_u16 = CLF.account(utf16_no_bom, TEXT)
        line_u16 = CLF.render(rep_u16)
        results.append(check(
            rep_u16["word"] == CLF.WORD_COMPOSED_MISMATCH
            and rep_u16["bom"] == 0
            and rep_u16.get("bom_kind") is None
            and rep_u16["composed"] == len(TEXT.encode("utf-8"))
            and rep_u16["disk"] == 24
            and rep_u16["delta"] == 12
            and "composed=12" in line_u16 and "disk=24" in line_u16
            and "encoding" not in line_u16.lower(),
            "AC-EDWX4 utf16_no_bom word=%s composed=%s disk=%d delta=%s"
            " bom=%d line=%s"
            % (rep_u16["word"], rep_u16["composed"], rep_u16["disk"],
               rep_u16["delta"], rep_u16["bom"], line_u16)))

        # --- AC-EDWX5: every AC-EDWW / AC-EDWV / AC-EDWT answer survives.
        results.append(legacy_answers(workdir))

        # --- AC-EDWX6: ascii, stdlib only, no clock, registered exactly once.
        results.append(hygiene())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


def legacy_answers(workdir):
    """AC-EDWX5: the parent words are re-read on their own fixtures."""
    fixtures = {
        "bom_gap": BOM + TEXT.encode("utf-8") + b"extra\n",
        "bom_mixed": BOM + b'{\r\n "a": 1\n}\r\n',
        "bom_clean": BOM + TEXT.encode("utf-8"),
        "utf16le": b"\xff\xfe" + TEXT.encode("utf-16-le"),
        "short2": b"\xef\xbb" + TEXT.encode("utf-8"),
        "short1": b"\xef" + TEXT.encode("utf-8"),
        "mixed": b'{\r\n "a": 1\n}\r\n',
        "empty": b"",
        "lf": TEXT.encode("utf-8"),
        "crlf": CRLF.encode("utf-8"),
        "gap": TEXT.encode("utf-8") + b"extra\n",
        "one": b'{"a":1}',
    }
    paths = {}
    for name, raw in fixtures.items():
        path = os.path.join(workdir, "legacy_%s.json" % name)
        write_bytes(path, raw)
        paths[name] = path
    legit = os.path.join(workdir, "legacy_legit.json")
    write_bytes(legit, "\uf000".encode("utf-8") + b'{"x":2}\n')
    before = fingerprint(workdir)
    rep = {}
    for name in ("bom_gap", "bom_mixed", "bom_clean", "utf16le", "short2",
                 "short1", "mixed", "empty", "lf", "crlf", "gap", "one"):
        rep[name] = CLF.account(paths[name], TEXT)
    rep["short1"] = CLF.account(paths["short1"], TEXT)
    rep["one"] = CLF.account(paths["one"], '{"a":1}')
    rep["crlf_caller"] = CLF.account(paths["crlf"], CRLF)
    rep["legit"] = CLF.account(legit, "\uf000" + '{"x":2}\n')
    after = fingerprint(workdir)
    at = {"k": 1}
    words_export = (
        EX.classify({"k": 2}, at, at, True, 10, 10) == EX.DOC_DOCTORED
        and EX.classify(at, at, at, False, 10, 10) == EX.CHECK_MISMATCH
        and EX.classify(at, at, {"k": 3}, True, 10, 10)
        == EX.DRIFT_UNDER_WRITE
        and EX.classify(at, at, at, True, 10, 11) == EX.SIZE_MISMATCH
        and EX.classify(at, at, at, True, 10, 10) == EX.VERDICT_PASS)
    return check(
        rep["bom_gap"]["word"] == CLF.WORD_BOM_BODY_MISMATCH
        and rep["bom_gap"]["delta"] == 6
        and rep["bom_mixed"]["word"] == CLF.WORD_BOM_TRANSPORT_MIXED
        and rep["bom_clean"]["word"] == CLF.WORD_BOM_LANDING
        and rep["bom_clean"]["delta"] == 0
        and rep["utf16le"]["word"] == CLF.WORD_UTF16_BOM
        and rep["utf16le"]["bom_kind"] == "utf16"
        and rep["short2"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short2"]["bom"] == 2 and rep["short2"]["delta"] == 2
        and rep["short1"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short1"]["bom"] == 1 and rep["short1"]["delta"] == 1
        and rep["mixed"]["word"] == CLF.WORD_TRANSPORT_MIXED
        and rep["mixed"]["composed"] is None
        and rep["empty"]["word"] == CLF.WORD_EMPTY_LANDING
        and rep["empty"]["disk"] == 0
        and rep["lf"]["word"] == CLF.WORD_PASS
        and rep["crlf"]["word"] == CLF.WORD_PASS
        and rep["crlf"]["transport"] == CLF.TRANSPORT_CRLF
        and rep["crlf"]["composed"] == rep["crlf"]["disk"]
        and rep["crlf_caller"]["word"] == CLF.WORD_PASS
        and rep["gap"]["word"] == CLF.WORD_COMPOSED_MISMATCH
        and rep["gap"]["delta"] == 6
        and rep["one"]["word"] == CLF.WORD_PASS
        and rep["legit"]["word"] == CLF.WORD_PASS
        and rep["legit"]["bom"] == 0
        and words_export and before == after,
        "AC-EDWX5 parent answers bom_gap=%s/%d bom_mixed=%s bom=%s"
        " utf16=%s/#%d trunc2=%s/#%d trunc1=%s/#%d mixed=%s empty=%s lf=%s"
        " crlf=%s caller=%s gap=%s/%d one=%s legit=%s export=%s untouched=%s"
        % (rep["bom_gap"]["word"], rep["bom_gap"]["delta"],
           rep["bom_mixed"]["word"], rep["bom_clean"]["word"],
           rep["utf16le"]["word"], rep["utf16le"]["bom"],
           rep["short2"]["word"], rep["short2"]["bom"],
           rep["short1"]["word"], rep["short1"]["bom"],
           rep["mixed"]["word"], rep["empty"]["word"], rep["lf"]["word"],
           rep["crlf"]["word"], rep["crlf_caller"]["word"],
           rep["gap"]["word"], rep["gap"]["delta"], rep["one"]["word"],
           rep["legit"]["word"], words_export, before == after))


def hygiene():
    """AC-EDWX6: pure ASCII, stdlib only, no clock, registered once."""
    with io.open(MODULE, encoding="utf-8") as handle:
        module_text = handle.read()
    with io.open(WIRED, encoding="utf-8") as handle:
        suite_text = handle.read()
    module_ascii = all(ord(ch) < 128 for ch in module_text)
    suite_ascii = all(ord(ch) < 128 for ch in suite_text)
    imports = set()
    for line in module_text.split("\n"):
        line = line.strip()
        if line.startswith("import "):
            imports.add(line[7:].split(".")[0].split(" ")[0])
        elif line.startswith("from "):
            imports.add(line[5:].split(".")[0].split(" ")[0])
    with open(RUNNER, encoding="utf-8") as handle:
        runner = handle.read()
    wired = [row for row in RA.SUITES if row[0] == LABEL]
    parent = [row for row in RA.SUITES if row[0] == PARENT_LABEL]
    return check(
        module_ascii and suite_ascii
        and not (imports & set(NET)) and "time" not in imports
        and ('"%s",' % LABEL) in runner
        and '"test_export_composed_landed_bom_precedence_second_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDWX6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
