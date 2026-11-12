"""AC-EDXB1..AC-EDXB6 suite for the composed/landed BOM PRECEDENCE SIXTH WAVE.

Criteria were pinned in state/queue/tech.md:665 at R2657 BEFORE this code
existed, from four shapes measured there with
src/os/limits_export_composed_landed_next_R2657.py and re-measured by this
window before any byte was written
(qa/limits-export-composed-landed-sixth-wave-before-R2659.log):

    a_utf16_cut_even       UTF16-BOM-LANDING  composed=None disk=24
                                              (a lost UTF-16 character named
                                               by no word and no delta)
    b_utf16_other_body     UTF16-BOM-LANDING  composed=None disk=4
                                              (right answer, silent refusal)
    c_utf16_empty_text     UTF16-BOM-BODY-GAP composed=2 delta=24 (named)
    d_double_even_two      BOM-DOUBLE-MARKER  body=2 body_short=False (named)

What this proves: a UTF-16 body that is the text encoding minus a whole number
of code units is named as a CUT with the units it lost, never as a whole
landing (X1); that name carries the whole landing it would have been, so a
delta is published rather than None (X2); a body that is neither the text nor a
head of it keeps the historical whole-landing word, reports no delta, and names
the refusal out loud (X3); the two answers measured here survive on their own
fixtures (X4); every AC-EDXA, AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW and AC-EDWV
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
    BASE, "test_export_composed_landed_bom_precedence_sixth_wave.py")
PARENT_SUITE = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_fifth_wave.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-sixth-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence-fifth-wave"
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
    workdir = tempfile.mkdtemp(prefix="edxb2659-suite-")
    try:
        paths = {}
        le_full = TEXT.encode("utf-16-le")
        be_full = TEXT.encode("utf-16-be")
        fixtures = {
            # this wave own shapes
            "le_cut1": U16LE + le_full[:-2],
            "be_cut2": U16BE + be_full[:-4],
            "other_body": U16LE + b"\x00\x00",
            "double_even_two": BOM + U16LE + b"\x00\x00",
            "empty_text": U16LE + le_full,
            # parent fixtures, unchanged, so their answers are re-read here
            "le_agree": U16LE + le_full,
            "le_disagree": U16LE + (TEXT + "X\n").encode("utf-16-le"),
            "be_agree": U16BE + be_full,
            "double_odd": BOM + U16LE + b"\x00",
            "double_even": BOM + U16LE + b"\x00\x00",
            "even_two": U16LE + b"\x00\x00",
            "be_short": U16BE + b"\x00",
            "lf": TEXT.encode("utf-8"),
            "empty": b"",
            "bom_gap": BOM + TEXT.encode("utf-8") + b"extra\n",
            "bom_mixed": BOM + b'{\r\n "a": 1\n}\r\n',
            "bom_clean": BOM + TEXT.encode("utf-8"),
            "utf16le": U16LE + le_full,
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

        # --- AC-EDXB1: a UTF-16 body that is the text encoding minus a whole
        # number of code units is a CUT, never a whole landing. The body has
        # an EVEN length in both worlds, which is exactly why the even-length
        # law could not see it.
        rep_c1 = CLF.account(paths["le_cut1"], TEXT)
        line_c1 = CLF.render(rep_c1)
        rep_c2 = CLF.account(paths["be_cut2"], TEXT)
        results.append(check(
            rep_c1["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_c1["word"] != CLF.WORD_UTF16_BOM
            and rep_c1["cut_units"] == 1
            and rep_c1["body"] == len(le_full) - 2 == 22
            and rep_c2["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_c2["cut_units"] == 2
            and rep_c2["body"] == len(be_full) - 4
            and "UTF16-BOM-CUT" in line_c1
            and "cut_units=1" in line_c1
            and "kind=utf16-cut" in line_c1,
            "AC-EDXB1 le_cut=%s/%s body=%s be_cut=%s/%s line=%s"
            % (rep_c1["word"], rep_c1["cut_units"], rep_c1["body"],
               rep_c2["word"], rep_c2["cut_units"], line_c1)))

        # --- AC-EDXB2: the cut carries the whole landing it would have been,
        # so a delta is published rather than None.
        results.append(check(
            rep_c1["composed"] == 2 + len(le_full) == 26
            and rep_c1["disk"] == 2 + len(le_full) - 2 == 24
            and rep_c1["delta"] == rep_c1["disk"] - rep_c1["composed"] == -2
            and rep_c1["delta"] is not None
            and rep_c2["composed"] == 26 and rep_c2["delta"] == -4
            and ("composed=%d" % rep_c1["composed"]) in line_c1
            and ("delta=%d" % rep_c1["delta"]) in line_c1,
            "AC-EDXB2 composed=%s disk=%s delta=%s be_delta=%s line=%s"
            % (rep_c1["composed"], rep_c1["disk"], rep_c1["delta"],
               rep_c2["delta"], line_c1)))

        # --- AC-EDXB3: a body that is neither the text nor a head of it keeps
        # the historical word, reports no delta, and NAMES the refusal.
        rep_ob = CLF.account(paths["other_body"], TEXT)
        line_ob = CLF.render(rep_ob)
        results.append(check(
            rep_ob["word"] == CLF.WORD_UTF16_BOM
            and rep_ob["composed"] is None and rep_ob["delta"] is None
            and rep_ob["disk"] == 4
            and rep_ob.get("judged") is False
            and rep_ob.get("refusal") == CLF.REFUSAL_NOT_TEXT_NOR_HEAD
            and "refusal=NOT-TEXT-NOR-HEAD" in line_ob,
            "AC-EDXB3 word=%s composed=%s delta=%s judged=%s refusal=%s"
            " line=%s"
            % (rep_ob["word"], rep_ob["composed"], rep_ob["delta"],
               rep_ob.get("judged"), rep_ob.get("refusal"), line_ob)))

        # --- AC-EDXB4: the two answers measured at R2657 survive.
        rep_et = CLF.account(paths["empty_text"], "")
        rep_de2 = CLF.account(paths["double_even_two"], TEXT)
        line_de2 = CLF.render(rep_de2)
        results.append(check(
            rep_et["word"] == CLF.WORD_UTF16_BOM_BODY_GAP
            and rep_et["composed"] == 2 and rep_et["disk"] == 26
            and rep_et["delta"] == 24
            and rep_de2["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_de2["body"] == 2 and rep_de2["body_short"] is False
            and "body_short" not in line_de2,
            "AC-EDXB4 empty_text=%s/%s/%s double_even_two=%s/%s"
            % (rep_et["word"], rep_et["composed"], rep_et["delta"],
               rep_de2["word"], rep_de2["body"])))

        # --- AC-EDXB5: every parent answer survives on its own fixture.
        rep = dict((name, CLF.account(paths[name], TEXT))
                   for name in fixtures)
        legit = CLF.account(paths["legit_ef_mixed"], TEXT)
        results.append(check(
            rep["le_agree"]["word"] == CLF.WORD_UTF16_BOM
            and rep["le_agree"]["composed"] == 26
            and rep["le_disagree"]["word"] == CLF.WORD_UTF16_BOM_BODY_GAP
            and rep["le_disagree"]["delta"] == 4
            and rep["be_agree"]["word"] == CLF.WORD_UTF16_BOM
            and rep["be_agree"]["delta"] == 0
            and rep["double_odd"]["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep["double_odd"]["body"] == 1
            and rep["double_odd"]["body_short"] is True
            and rep["even_two"]["word"] == CLF.WORD_UTF16_BOM
            and rep["even_two"]["composed"] is None
            and rep["be_short"]["word"] == CLF.WORD_UTF16_BOM_SHORT_BODY
            and rep["be_short"]["delta"] == -23
            and rep["bom_gap"]["word"] == CLF.WORD_BOM_BODY_MISMATCH
            and rep["bom_gap"]["delta"] == 6
            and rep["bom_mixed"]["word"] == CLF.WORD_BOM_TRANSPORT_MIXED
            and rep["bom_clean"]["word"] == CLF.WORD_BOM_LANDING
            and rep["bom_clean"]["delta"] == 0
            and rep["utf16le"]["word"] == CLF.WORD_UTF16_BOM
            and rep["utf16le"]["bom_kind"] == "utf16"
            and rep["utf16_empty"]["word"] == CLF.WORD_UTF16_BOM_MARKER_ONLY
            and rep["short2"]["word"] == CLF.WORD_BOM_TRUNCATED
            and rep["short2"]["delta"] == 2
            and rep["short1"]["word"] == CLF.WORD_BOM_TRUNCATED
            and rep["short1"]["delta"] == 1
            and rep["short_mixed"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED
            and rep["trunc_gap"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED_GAP
            and rep["bom_only"]["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep["empty"]["word"] == CLF.WORD_EMPTY_LANDING
            and rep["lf"]["word"] == CLF.WORD_PASS
            and rep["crlf"]["word"] == CLF.WORD_PASS
            and rep["mixed"]["word"] == CLF.WORD_TRANSPORT_MIXED
            and rep["mixed"]["bom"] == 0
            and legit["word"] == CLF.WORD_TRANSPORT_MIXED
            and legit["bom"] == 0
            and rep["one"]["word"] == CLF.WORD_COMPOSED_MISMATCH
            and fingerprint(workdir) == before,
            "AC-EDXB5 utf16=%s/%s gap=%s/%s marker_only=%s short2=%s/%d"
            " short1=%s/%d trunc_mixed=%s trunc_gap=%s bom_only=%s"
            " empty=%s lf=%s crlf=%s mixed=%s/%d legit=%s/%d one=%s"
            " untouched=%s"
            % (rep["le_agree"]["word"], rep["le_agree"]["composed"],
               rep["le_disagree"]["word"], rep["le_disagree"]["delta"],
               rep["utf16_empty"]["word"], rep["short2"]["word"],
               rep["short2"]["delta"], rep["short1"]["word"],
               rep["short1"]["delta"], rep["short_mixed"]["word"],
               rep["trunc_gap"]["word"], rep["bom_only"]["word"],
               rep["empty"]["word"], rep["lf"]["word"], rep["crlf"]["word"],
               rep["mixed"]["word"], rep["mixed"]["bom"], legit["word"],
               legit["bom"], rep["one"]["word"],
               fingerprint(workdir) == before)))

        results.append(hygiene())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUMMARY %s %d/%d" % ("PASS" if all(results) else "FAIL",
                                sum(results), EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


def hygiene():
    """AC-EDXB6: pure ASCII, stdlib only, no clock, registered once."""
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
        and '"test_export_composed_landed_bom_precedence_sixth_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDXB6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
