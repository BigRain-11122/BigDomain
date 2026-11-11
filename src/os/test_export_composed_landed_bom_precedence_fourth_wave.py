"""AC-EDWZ1..AC-EDWZ6 suite for the composed/landed BOM PRECEDENCE FOURTH WAVE.

Criteria were pinned in state/queue/tech.md:663 at R2649 BEFORE this code
existed, from four shapes that window MEASURED with
src/os/limits_export_composed_landed_next_R2649.py and this window re-measured
before any byte was written
(qa/limits-export-composed-landed-fourth-wave-before-R2653.log):

    a_utf16_one_byte        UTF16-BOM-LANDING     composed=None disk=3
    b_utf16_one_byte_text   UTF16-BOM-LANDING     composed=None disk=3
    c_double_marker_body    BOM-DOUBLE-MARKER     composed=None delta=None
                                                  disk=8 (body invisible)
    d_cut_only_vs_text      BOM-CUT-NO-BODY       composed=12 delta=-10
                                                  (already correct, named)
    e_cut1_vs_text          BOM-CUT-NO-BODY       composed=12 delta=-11
                                                  (already correct, named)
    f_clean_lf              PASS                  (already correct, named)

What this proves: a UTF-16 body is an even number of bytes, so an ODD remnant
is NOT named as a whole landing (Z1); the same remnant against a non-empty text
carries the count it was measured against - the whole landing it would have
been, marker included, in its own byte order (Z2); two markers carrying a body
describe that body by its own fields instead of leaving it invisible (Z3); a
prefix-only landing against non-empty text keeps its composed count and its
negative delta (Z4); every AC-EDWY, AC-EDWX, AC-EDWW and AC-EDWV answer
survives on its own fixture, including the legitimate 0xef-leading MIXED
payload that stays TRANSPORT-MIXED with bom=0 and the clean LF PASS (Z5); and
the module stays pure ASCII, stdlib only, no clock, no network, registered
exactly once with its own suite (Z6).

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
WIRED = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_fourth_wave.py")
PARENT_SUITE = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_third_wave.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-fourth-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence-third-wave"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

TEXT = '{\n "a": 1\n}\n'
CRLF = TEXT.replace("\n", "\r\n")
BOM = b"\xef\xbb\xbf"
MIXED_TAIL = b'{\r\n "a": 1\n}\r\nX\n'


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


def whole_landing_size(text, codec, mark):
    """The size the WHOLE landing would have: marker plus its own encoding."""
    return len(mark) + len(text.replace("\r\n", "\n").encode(codec))


def verify():
    results = []
    workdir = tempfile.mkdtemp(prefix="edwz2653-suite-")
    try:
        short = os.path.join(workdir, "utf16_short.json")
        double_body = os.path.join(workdir, "double_body.json")
        double_bare = os.path.join(workdir, "double_bare.json")
        cut_only = os.path.join(workdir, "cut_only.json")
        cut_one = os.path.join(workdir, "cut_one.json")

        write_bytes(short, b"\xff\xfe\x00")
        write_bytes(double_body, BOM + b"\xff\xfe" + b"abc")
        write_bytes(double_bare, BOM + b"\xff\xfe")
        write_bytes(cut_only, b"\xef\xbb")
        write_bytes(cut_one, b"\xef")

        # --- AC-EDWZ1: an ODD remnant is not a whole UTF-16 landing.
        rep_s = CLF.account(short, "")
        line_s = CLF.render(rep_s)
        results.append(check(
            rep_s["word"] == CLF.WORD_UTF16_BOM_SHORT_BODY
            and rep_s["word"] != CLF.WORD_UTF16_BOM
            and rep_s["word"] != CLF.WORD_UTF16_BOM_MARKER_ONLY
            and rep_s["word"] != CLF.WORD_COMPOSED_MISMATCH
            and rep_s["bom"] == 2
            and rep_s["bom_kind"] == "utf16-short"
            and rep_s["body"] == 1
            and rep_s["disk"] == 3
            and "SHORT-BODY" in line_s and "kind=utf16-short" in line_s,
            "AC-EDWZ1 utf16_short word=%s bom=%d kind=%s body=%s disk=%d"
            " line=%s"
            % (rep_s["word"], rep_s["bom"], rep_s["bom_kind"],
               rep_s.get("body"), rep_s["disk"], line_s)))

        # --- AC-EDWZ2: against non-empty text the remnant carries the count.
        rep_st = CLF.account(short, TEXT)
        line_st = CLF.render(rep_st)
        expected = whole_landing_size(TEXT, "utf-16-le", b"\xff\xfe")
        results.append(check(
            rep_st["word"] == CLF.WORD_UTF16_BOM_SHORT_BODY
            and rep_st["composed"] == expected
            and rep_st["composed"] is not None
            and rep_st["disk"] == 3
            and rep_st["delta"] == 3 - expected
            and "composed=%d" % expected in line_st
            and "delta=%d" % (3 - expected) in line_st,
            "AC-EDWZ2 utf16_short_vs_text word=%s composed=%s expected=%d"
            " disk=%d delta=%s line=%s"
            % (rep_st["word"], rep_st["composed"], expected,
               rep_st["disk"], rep_st["delta"], line_st)))

        # --- AC-EDWZ3: two markers with a body describe that body.
        rep_db = CLF.account(double_body, TEXT)
        line_db = CLF.render(rep_db)
        rep_d0 = CLF.account(double_bare, TEXT)
        line_d0 = CLF.render(rep_d0)
        results.append(check(
            rep_db["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_db["bom"] == 5
            and rep_db["bom_kind"] == "utf8+utf16"
            and rep_db["body"] == 3
            and rep_db["body_transport"] == CLF.TRANSPORT_LF
            and rep_db["disk"] == 8
            and "double_body=3" not in line_db
            and "body=3" in line_db and "body_transport=lf" in line_db
            and "utf8+utf16" in line_db
            and rep_d0["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_d0["body"] == 0
            and rep_d0["body_transport"] == CLF.TRANSPORT_LF
            and "body=0" in line_d0,
            "AC-EDWZ3 double_marker body=%s transport=%s disk=%d"
            " bare_body=%s line=%s bare_line=%s"
            % (rep_db.get("body"), rep_db.get("body_transport"),
               rep_db["disk"], rep_d0.get("body"), line_db, line_d0)))

        # --- AC-EDWZ4: a prefix-only landing keeps its count and delta.
        rep_c2 = CLF.account(cut_only, TEXT)
        rep_c1 = CLF.account(cut_one, TEXT)
        line_c2 = CLF.render(rep_c2)
        results.append(check(
            rep_c2["word"] == CLF.WORD_BOM_CUT_NO_BODY
            and rep_c2["composed"] == len(TEXT.encode("utf-8"))
            and rep_c2["delta"] == 2 - len(TEXT.encode("utf-8"))
            and rep_c2["disk"] == 2
            and "composed=12" in line_c2 and "delta=-10" in line_c2
            and rep_c1["word"] == CLF.WORD_BOM_CUT_NO_BODY
            and rep_c1["composed"] == len(TEXT.encode("utf-8"))
            and rep_c1["delta"] == 1 - len(TEXT.encode("utf-8")),
            "AC-EDWZ4 cut_only composed=%s delta=%s disk=%d cut1_delta=%s"
            " line=%s"
            % (rep_c2["composed"], rep_c2["delta"], rep_c2["disk"],
               rep_c1["delta"], line_c2)))

        # --- AC-EDWZ5: every parent answer survives on its own fixture.
        results.append(legacy_answers(workdir))

        # --- AC-EDWZ6: ascii, stdlib only, no clock, registered exactly once.
        results.append(hygiene())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


def legacy_answers(workdir):
    """AC-EDWZ5: the AC-EDWY / AC-EDWX / AC-EDWW / AC-EDWV answers stand."""
    fixtures = {
        "bom_gap": BOM + TEXT.encode("utf-8") + b"extra\n",
        "bom_mixed": BOM + b'{\r\n "a": 1\n}\r\n',
        "bom_clean": BOM + TEXT.encode("utf-8"),
        "utf16le": b"\xff\xfe" + TEXT.encode("utf-16-le"),
        "utf16_empty": b"\xff\xfe",
        "short2": b"\xef\xbb" + TEXT.encode("utf-8"),
        "short1": b"\xef" + TEXT.encode("utf-8"),
        "short_mixed": b"\xef\xbb" + b'{\r\n "a": 1\n}\r\n',
        "trunc_gap": b"\xef\xbb" + MIXED_TAIL,
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
    legit = os.path.join(workdir, "legacy_legit_mixed.json")
    write_bytes(legit, "\uf000".encode("utf-8") + b'{\r\n 1\n}\r\n')
    bom_only = os.path.join(workdir, "legacy_bom_only.json")
    write_bytes(bom_only, BOM)
    before = fingerprint(workdir)
    rep = {}
    for name in fixtures:
        rep[name] = CLF.account(paths[name], TEXT)
    rep["bom_clean"] = CLF.account(paths["bom_clean"], TEXT)
    rep["one"] = CLF.account(paths["one"], '{"a":1}')
    rep["crlf_caller"] = CLF.account(paths["crlf"], CRLF)
    rep["legit"] = CLF.account(legit, "\uf000" + '{\r\n 1\n}\r\n')
    rep["bom_only"] = CLF.account(bom_only, TEXT)
    rep["bom_only_empty"] = CLF.account(bom_only, "")
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
        and rep["utf16_empty"]["word"] == CLF.WORD_UTF16_BOM_MARKER_ONLY
        and rep["short2"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short2"]["bom"] == 2 and rep["short2"]["delta"] == 2
        and rep["short1"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short1"]["bom"] == 1 and rep["short1"]["delta"] == 1
        and rep["short_mixed"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED
        and rep["short_mixed"]["bom"] == 2
        and rep["trunc_gap"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED_GAP
        and rep["trunc_gap"]["delta"] == 6
        and rep["bom_only"]["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
        and rep["bom_only"]["composed"] == len(TEXT.encode("utf-8"))
        and rep["bom_only"]["delta"] == -9
        and rep["bom_only_empty"]["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
        and rep["bom_only_empty"]["composed"] is None
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
        and rep["legit"]["word"] == CLF.WORD_TRANSPORT_MIXED
        and rep["legit"]["bom"] == 0
        and rep["legit"].get("bom_kind") is None
        and words_export and before == after,
        "AC-EDWZ5 parent answers bom_gap=%s/%d bom_mixed=%s bom=%s"
        " utf16=%s/%s marker_only=%s trunc2=%s/#%d trunc1=%s/#%d"
        " trunc_mixed=%s trunc_gap=%s/%d bom_only=%s/%s empty_text=%s"
        " mixed=%s empty=%s lf=%s crlf=%s caller=%s gap=%s/%d one=%s"
        " legit=%s export=%s untouched=%s"
        % (rep["bom_gap"]["word"], rep["bom_gap"]["delta"],
           rep["bom_mixed"]["word"], rep["bom_clean"]["word"],
           rep["utf16le"]["word"], rep["utf16le"]["bom"],
           rep["utf16_empty"]["word"], rep["short2"]["word"],
           rep["short2"]["bom"], rep["short1"]["word"], rep["short1"]["bom"],
           rep["short_mixed"]["word"], rep["trunc_gap"]["word"],
           rep["trunc_gap"]["delta"], rep["bom_only"]["word"],
           rep["bom_only"]["composed"], rep["bom_only_empty"]["composed"],
           rep["mixed"]["word"], rep["empty"]["word"], rep["lf"]["word"],
           rep["crlf"]["word"], rep["crlf_caller"]["word"],
           rep["gap"]["word"], rep["gap"]["delta"], rep["one"]["word"],
           rep["legit"]["word"], words_export, before == after))


def hygiene():
    """AC-EDWZ6: pure ASCII, stdlib only, no clock, registered once."""
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
        and '"test_export_composed_landed_bom_precedence_fourth_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDWZ6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
