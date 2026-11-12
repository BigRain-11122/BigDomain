"""AC-EDXA1..AC-EDXA6 suite for the composed/landed BOM PRECEDENCE FIFTH WAVE.

Criteria were pinned in state/queue/tech.md:664 at R2653 BEFORE this code
existed, from three shapes measured there with
src/os/limits_export_composed_landed_next_R2653.py and re-measured by this
window before any byte was written
(qa/limits-export-composed-landed-fifth-wave-before-R2657.log):

    a_utf16_whole_agree     UTF16-BOM-LANDING   composed=None disk=26
    b_utf16_whole_disagree  UTF16-BOM-LANDING   composed=None disk=30
                                                (the SAME word, so agreement
                                                 was never decided)
    c_double_odd_body       BOM-DOUBLE-MARKER   body=1 (never named short)
    d_utf16be_short         UTF16-BOM-SHORT-BODY composed=26 delta=-23
                                                (already correct, named)
    e_utf16_even_two        UTF16-BOM-LANDING   (already correct, named)
    f_clean_lf              PASS                (already correct, named)

What this proves: a whole UTF-16 landing is compared with the composed text in
ITS OWN BYTE ORDER, so an agreeing one is named apart from a disagreeing one
(X1); that comparison publishes both counts, so a delta is carried instead of a
bare word (X2); an odd body behind two markers names BOTH that it sits behind
two markers AND that it is short, while the pinned double-marker word survives
(X3); the even two byte body and the UTF-16BE short remnant keep the answers
measured at R2653 (X4); every AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW and AC-EDWV
answer survives on its own fixture, including the legitimate 0xef-leading MIXED
payload that stays TRANSPORT-MIXED with bom=0 and the clean LF PASS (X5); and
the module stays pure ASCII, stdlib only, no clock, no network, registered
exactly once with its own suite (X6).

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
import reconcile_all as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_composed_landed_face.py")
WIRED = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_fifth_wave.py")
PARENT_SUITE = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_fourth_wave.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-fifth-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence-fourth-wave"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

TEXT = '{\n "a": 1\n}\n'
CRLF = TEXT.replace("\n", "\r\n")
BOM = b"\xef\xbb\xbf"
U16LE = b"\xff\xfe"
U16BE = b"\xfe\xff"


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
    workdir = tempfile.mkdtemp(prefix="edxa2657-suite-")
    try:
        paths = {}
        fixtures = {
            "le_agree": U16LE + TEXT.encode("utf-16-le"),
            "le_disagree": U16LE + (TEXT + "X\n").encode("utf-16-le"),
            "be_agree": U16BE + TEXT.encode("utf-16-be"),
            "double_odd": BOM + U16LE + b"\x00",
            "double_even": BOM + U16LE + b"\x00\x00",
            "even_two": U16LE + b"\x00\x00",
            "be_short": U16BE + b"\x00",
            "lf": TEXT.encode("utf-8"),
            "empty": b"",
            # parent fixtures, unchanged, so their answers are re-read here
            "bom_gap": BOM + TEXT.encode("utf-8") + b"extra\n",
            "bom_mixed": BOM + b'{\r\n "a": 1\n}\r\n',
            "bom_clean": BOM + TEXT.encode("utf-8"),
            "utf16le": U16LE + TEXT.encode("utf-16-le"),
            "utf16_empty": U16LE,
            "short2": b"\xef\xbb" + TEXT.encode("utf-8"),
            "short1": b"\xef" + TEXT.encode("utf-8"),
            "short_mixed": b"\xef\xbb" + b'{\r\n "a": 1\n}\r\n',
            "trunc_gap": b"\xef\xbb" + b'{\r\n "a": 1\n}\r\nX\n',
            "bom_only": BOM,
            "mixed": b'{\r\n "a": 1\n}\r\n',
            "one": b'{"a":1}',
            "legit_ef_mixed": b"\xef" + b'Z\r\n "a": 1\n}\r\n',
            "crlf": CRLF.encode("utf-8"),
        }
        for name, raw in fixtures.items():
            path = os.path.join(workdir, name + ".json")
            write_bytes(path, raw)
            paths[name] = path

        before = fingerprint(workdir)

        # --- AC-EDXA1: a whole UTF-16 landing is COMPARED in its own byte
        # order, and agreement is named apart from disagreement. The UTF-8
        # length of TEXT is 12, its UTF-16 length is 24, so composed=26 is the
        # marker plus the body in the marker own codec and nothing else.
        rep_ok = CLF.account(paths["le_agree"], TEXT)
        rep_bad = CLF.account(paths["le_disagree"], TEXT)
        rep_be = CLF.account(paths["be_agree"], TEXT)
        line_ok = CLF.render(rep_ok)
        line_bad = CLF.render(rep_bad)
        results.append(check(
            rep_ok["word"] == CLF.WORD_UTF16_BOM
            and rep_bad["word"] == CLF.WORD_UTF16_BOM_BODY_GAP
            and rep_ok["word"] != rep_bad["word"]
            and rep_ok["composed"] == 26 and rep_ok["disk"] == 26
            and rep_bad["composed"] == 26 and rep_bad["disk"] == 30
            and rep_be["word"] == CLF.WORD_UTF16_BOM
            and rep_be["composed"] == 26 and rep_be["delta"] == 0
            and rep_ok["composed"] != 2 + len(TEXT.encode("utf-8"))
            and "UTF16-BOM-BODY-GAP" in line_bad
            and "kind=utf16-gap" in line_bad,
            "AC-EDXA1 agree=%s/%s bad=%s/%s be=%s/%s"
            % (rep_ok["word"], rep_ok["composed"], rep_bad["word"],
               rep_bad["composed"], rep_be["word"], rep_be["composed"])))

        # --- AC-EDXA2: the comparison carries BOTH counts, so a delta is
        # published rather than a bare word.
        results.append(check(
            rep_ok["delta"] == 0
            and rep_bad["delta"] == rep_bad["disk"] - rep_bad["composed"] == 4
            and rep_bad["delta"] != 0
            and ("composed=%d" % rep_bad["composed"]) in line_bad
            and ("disk=%d" % rep_bad["disk"]) in line_bad
            and ("delta=%d" % rep_bad["delta"]) in line_bad
            and ("delta=%d" % rep_ok["delta"]) in line_ok,
            "AC-EDXA2 ok_delta=%s bad_delta=%s line=%s"
            % (rep_ok["delta"], rep_bad["delta"], line_bad)))

        # --- AC-EDXA3: an odd body behind two markers names BOTH facts. The
        # WORD stays the pinned one (AC-EDWZ3 own fixture must survive), so
        # the short fact rides on its own field and its own rendered token.
        rep_do = CLF.account(paths["double_odd"], TEXT)
        line_do = CLF.render(rep_do)
        rep_de = CLF.account(paths["double_even"], TEXT)
        line_de = CLF.render(rep_de)
        results.append(check(
            rep_do["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_do["bom"] == 5 and rep_do["bom_kind"] == "utf8+utf16"
            and rep_do["body"] == 1 and rep_do["body_short"] is True
            and "DOUBLE-MARKER" in line_do and "body=1" in line_do
            and "body_short=1" in line_do
            and rep_de["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_de["body"] == 2 and rep_de["body_short"] is False
            and "body_short" not in line_de,
            "AC-EDXA3 odd=%s/%s/%s even=%s/%s line=%s"
            % (rep_do["word"], rep_do["body"], rep_do["body_short"],
               rep_de["word"], rep_de["body"], line_do)))

        # --- AC-EDXA4: the even two byte body and the UTF-16BE short remnant
        # keep the answers measured at R2653.
        rep_e2 = CLF.account(paths["even_two"], TEXT)
        rep_bs = CLF.account(paths["be_short"], TEXT)
        results.append(check(
            rep_e2["word"] == CLF.WORD_UTF16_BOM
            and rep_e2["composed"] is None and rep_e2["delta"] is None
            and rep_e2["disk"] == 4
            and rep_bs["word"] == CLF.WORD_UTF16_BOM_SHORT_BODY
            and rep_bs["bom_kind"] == "utf16-short"
            and rep_bs["composed"] == 26 and rep_bs["delta"] == -23
            and rep_bs["body"] == 1,
            "AC-EDXA4 even_two=%s/%s be_short=%s/%s/%s"
            % (rep_e2["word"], rep_e2["composed"], rep_bs["word"],
               rep_bs["composed"], rep_bs["delta"])))

        # --- AC-EDXA5: every AC-EDWZ / AC-EDWY / AC-EDWX / AC-EDWW / AC-EDWV
        # answer survives on its own fixture.
        rep = dict((name, CLF.account(paths[name], TEXT))
                   for name in fixtures)
        legit = CLF.account(paths["legit_ef_mixed"], TEXT)
        results.append(check(
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
            and rep["trunc_gap"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED_GAP
            and rep["bom_only"]["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep["bom_only"]["composed"] == len(TEXT.encode("utf-8"))
            and rep["empty"]["word"] == CLF.WORD_EMPTY_LANDING
            and rep["lf"]["word"] == CLF.WORD_PASS
            and rep["crlf"]["word"] == CLF.WORD_PASS
            and rep["mixed"]["word"] == CLF.WORD_TRANSPORT_MIXED
            and rep["mixed"]["bom"] == 0
            and legit["word"] == CLF.WORD_TRANSPORT_MIXED
            and legit["bom"] == 0
            and rep["one"]["word"] == CLF.WORD_COMPOSED_MISMATCH
            and fingerprint(workdir) == before,
            "AC-EDXA5 bom_gap=%s/%s bom_mixed=%s bom_clean=%s utf16=%s/%s"
            " marker_only=%s trunc2=%s/%d trunc1=%s/%d trunc_mixed=%s"
            " trunc_gap=%s bom_only=%s/%s empty=%s lf=%s crlf=%s mixed=%s/%d"
            " legit=%s/%d one=%s untouched=%s"
            % (rep["bom_gap"]["word"], rep["bom_gap"]["delta"],
               rep["bom_mixed"]["word"], rep["bom_clean"]["word"],
               rep["utf16le"]["word"], rep["utf16le"]["bom_kind"],
               rep["utf16_empty"]["word"], rep["short2"]["word"],
               rep["short2"]["bom"], rep["short1"]["word"],
               rep["short1"]["bom"], rep["short_mixed"]["word"],
               rep["trunc_gap"]["word"], rep["bom_only"]["word"],
               rep["bom_only"]["composed"], rep["empty"]["word"],
               rep["lf"]["word"], rep["crlf"]["word"], rep["mixed"]["word"],
               rep["mixed"]["bom"], legit["word"], legit["bom"],
               rep["one"]["word"], fingerprint(workdir) == before)))

        results.append(hygiene())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUMMARY %s %d/%d" % ("PASS" if all(results) else "FAIL",
                                sum(results), EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


def hygiene():
    """AC-EDXA6: pure ASCII, stdlib only, no clock, registered once."""
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
        and '"test_export_composed_landed_bom_precedence_fifth_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDXA6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
