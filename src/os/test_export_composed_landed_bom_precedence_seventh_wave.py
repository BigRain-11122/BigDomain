"""AC-EDXC1..AC-EDXC6 suite for the composed/landed BOM PRECEDENCE SEVENTH WAVE.

Criteria were pinned in state/queue/tech.md:666 at R2661 BEFORE this code
existed, from four shapes measured there with
src/os/limits_export_composed_landed_next_R2661.py and re-measured by this
window before any byte was written
(qa/limits-export-composed-landed-seventh-wave-before-R2671.log):

    a_surrogate_half   UTF16-BOM-CUT         composed=12 disk=10 cut_units=1
                                             (a lost unit named as if it were
                                              always a whole character)
    b_crlf_cut         UTF16-BOM-LANDING     composed=10 disk=10 delta=0
                                             (a wrong payload of the right
                                              size called a clean landing)
    c_cut_behind_two   BOM-DOUBLE-MARKER     composed=None disk=13 body=8
                                             (the cut behind two markers was
                                              never named)
    d_be_three_units   UTF16-BOM-CUT         composed=16 disk=10 cut_units=3
                                             (re-measured, unchanged)

What this proves: a UTF-16 body of the right LENGTH with the wrong CONTENT is
named apart from an agreeing landing and never as a clean whole landing (X1);
that name carries the counts it was measured against and says out loud that
the bytes differ, because delta=0 alone would read clean (X2); the code units
a cut lost are named apart from the whole characters it lost, so a lone
surrogate half is not counted as a whole character (X3); the four answers
measured here survive on their own fixtures, including the cut behind two
markers (X4); every AC-EDXB, AC-EDXA, AC-EDWZ, AC-EDWY, AC-EDWX, AC-EDWW and
AC-EDWV answer survives on its own fixture, including the legitimate
0xef-leading MIXED payload that stays TRANSPORT-MIXED with bom=0 and the clean
LF PASS (X5); and the module stays pure ASCII, stdlib only, no clock, no
network, registered exactly once with its own suite (X6).

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
    BASE, "test_export_composed_landed_bom_precedence_seventh_wave.py")
PARENT_SUITE = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_sixth_wave.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-seventh-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence-sixth-wave"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

TEXT = '{\n "a": 1\n}\n'
CRLF = TEXT.replace("\n", "\r\n")
BOM = b"\xef\xbb\xbf"
U16LE = b"\xff\xfe"
U16BE = b"\xfe\xff"
# A text whose second character is a surrogate PAIR in UTF-16, so cutting the
# last two bytes of a longer text leaves a LONE SURROGATE HALF behind.
EMOJI = 'a\U0001F600b\n'
PAIR_ONLY = 'a\U0001F600'
# The exact shape the seed row measured: a CRLF text landed as UTF-16 and cut
# by one code unit, so the body has the SAME length as the folded text and a
# DIFFERENT content.
PLAIN_TEXT = "a\r\nb\n"


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
    workdir = tempfile.mkdtemp(prefix="edxc2671-suite-")
    try:
        paths = {}
        le_full = TEXT.encode("utf-16-le")
        be_full = TEXT.encode("utf-16-be")
        emoji_le = EMOJI.encode("utf-16-le")
        pair_le = PAIR_ONLY.encode("utf-16-le")
        fixtures = {
            # this wave own shapes
            "same_len_wrong": U16LE + PLAIN_TEXT.encode("utf-16-le")[:-2],
            "surrogate_half": U16LE + emoji_le[:-2],
            "lone_half_cut": U16LE + pair_le[:-2],
            "cut_behind_two": BOM + U16LE + emoji_le[:-2],
            "be_three_units": U16BE + "abcdef\n".encode("utf-16-be")[:-6],
            # parent fixtures, unchanged, so their answers are re-read here
            "le_agree": U16LE + le_full,
            "le_disagree": U16LE + (TEXT + "X\n").encode("utf-16-le"),
            "be_agree": U16BE + be_full,
            "le_cut1": U16LE + le_full[:-2],
            "other_body": U16LE + b"\x00\x00",
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

        # --- AC-EDXC1: a UTF-16 body of the same LENGTH and a different
        # CONTENT is named apart from an agreeing landing. The old equal-length
        # branch compared lengths only, so this shape read agrees=True.
        rep_sl = CLF.account(paths["same_len_wrong"], PLAIN_TEXT)
        rep_ok = CLF.account(paths["le_agree"], TEXT)
        results.append(check(
            rep_sl["word"] == CLF.WORD_UTF16_BOM_BODY_MISMATCH
            and rep_sl["word"] != CLF.WORD_UTF16_BOM
            and rep_sl["agrees"] is False
            and rep_sl["body_differs"] is True
            and rep_ok["word"] == CLF.WORD_UTF16_BOM
            and rep_ok["agrees"] is True,
            "AC-EDXC1 same_len=%s agrees=%s ok=%s agrees=%s"
            % (rep_sl["word"], rep_sl["agrees"], rep_ok["word"],
               rep_ok["agrees"])))

        # --- AC-EDXC2: that name carries the counts it was measured against
        # AND says the bytes differ, because delta=0 would otherwise read clean.
        line_sl = CLF.render(rep_sl)
        folded_plain = len(PLAIN_TEXT.replace("\r\n", "\n")
                           .encode("utf-16-le"))
        results.append(check(
            rep_sl["composed"] == 2 + folded_plain == 10
            and rep_sl["disk"] == 2 + len(PLAIN_TEXT.encode("utf-16-le")) - 2
            == 10
            and rep_sl["delta"] == rep_sl["disk"] - rep_sl["composed"] == 0
            and rep_sl["body"] == len(PLAIN_TEXT.encode("utf-16-le")) - 2 == 8
            and ("composed=%d" % rep_sl["composed"]) in line_sl
            and ("disk=%d" % rep_sl["disk"]) in line_sl
            and "body_differs=1" in line_sl
            and "kind=utf16-body-mismatch" in line_sl,
            "AC-EDXC2 composed=%s disk=%s delta=%s body=%s line=%s"
            % (rep_sl["composed"], rep_sl["disk"], rep_sl["delta"],
               rep_sl["body"], line_sl)))

        # --- AC-EDXC3: the units a cut lost are named apart from the whole
        # characters it lost. A text cut mid-pair keeps its units count and
        # stops claiming a character for half of one.
        rep_sh = CLF.account(paths["surrogate_half"], EMOJI)
        rep_lh = CLF.account(paths["lone_half_cut"], PAIR_ONLY)
        line_lh = CLF.render(rep_lh)
        results.append(check(
            rep_sh["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_sh["cut_units"] == 1
            and rep_sh["cut_chars"] == 1
            and rep_sh["surrogate_half"] is False
            and rep_lh["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_lh["cut_units"] == 1
            and rep_lh["cut_chars"] == 0
            and rep_lh["surrogate_half"] is True
            and "cut_chars=0" in line_lh
            and "surrogate_half=1" in line_lh,
            "AC-EDXC3 whole_unit=%s/%s/%s half=%s/%s/%s line=%s"
            % (rep_sh["cut_units"], rep_sh["cut_chars"],
               rep_sh["surrogate_half"], rep_lh["cut_units"],
               rep_lh["cut_chars"], rep_lh["surrogate_half"], line_lh)))

        # --- AC-EDXC4: the four answers measured at R2661 survive on their
        # own fixtures, and the cut behind two markers is now NAMED while the
        # word a parent pinned stays.
        rep_cb = CLF.account(paths["cut_behind_two"], EMOJI)
        rep_be = CLF.account(paths["be_three_units"], "abcdef\n")
        line_cb = CLF.render(rep_cb)
        results.append(check(
            rep_sh["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_sh["composed"] == 12 and rep_sh["disk"] == 10
            and rep_sl["word"] == CLF.WORD_UTF16_BOM_BODY_MISMATCH
            and rep_sl["composed"] == 10 and rep_sl["disk"] == 10            and rep_cb["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_cb["disk"] == 13 and rep_cb["body"] == 8
            and rep_cb["cut_units"] == 1 and rep_cb["cut_chars"] == 1
            and rep_cb["surrogate_half"] is False
            and "cut_units=1" in line_cb
            and rep_be["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep_be["cut_units"] == 3 and rep_be["composed"] == 16
            and rep_be["disk"] == 10 and rep_be["delta"] == -6,
            "AC-EDXC4 half=%s/%s same_len=%s/%s behind=%s/%s/%s be=%s/%s"
            " line=%s"
            % (rep_sh["word"], rep_sh["cut_units"], rep_sl["word"],
               rep_sl["disk"], rep_cb["word"], rep_cb["body"],
               rep_cb["cut_units"], rep_be["cut_units"], rep_be["delta"],
               line_cb)))

        # --- AC-EDXC5: every parent answer survives on its own fixture.
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
            and rep["le_cut1"]["word"] == CLF.WORD_UTF16_BOM_CUT
            and rep["le_cut1"]["cut_units"] == 1
            and rep["other_body"]["word"] == CLF.WORD_UTF16_BOM
            and rep["other_body"].get("refusal") == CLF.REFUSAL_NOT_TEXT_NOR_HEAD
            and rep["double_odd"]["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep["double_odd"]["body"] == 1
            and rep["double_odd"]["body_short"] is True
            and rep["double_even"]["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep["double_even"]["body"] == 2
            and rep["double_even"]["body_short"] is False
            and "cut_units" not in rep["double_even"]
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
            "AC-EDXC5 utf16=%s/%s gap=%s/%s cut=%s/%s other=%s double=%s/%s"
            " even_two=%s be_short=%s/%d bom_gap=%s/%d bom_clean=%s"
            " marker_only=%s short2=%s/%d short1=%s/%d trunc_mixed=%s"
            " trunc_gap=%s bom_only=%s empty=%s lf=%s crlf=%s mixed=%s/%d"
            " legit=%s/%d one=%s untouched=%s"
            % (rep["le_agree"]["word"], rep["le_agree"]["composed"],
               rep["le_disagree"]["word"], rep["le_disagree"]["delta"],
               rep["le_cut1"]["word"], rep["le_cut1"]["cut_units"],
               rep["other_body"]["word"], rep["double_even"]["body"],
               rep["double_even"]["body_short"], rep["even_two"]["word"],
               rep["be_short"]["word"], rep["be_short"]["delta"],
               rep["bom_gap"]["word"], rep["bom_gap"]["delta"],
               rep["bom_clean"]["word"], rep["utf16_empty"]["word"],
               rep["short2"]["word"], rep["short2"]["delta"],
               rep["short1"]["word"], rep["short1"]["delta"],
               rep["short_mixed"]["word"], rep["trunc_gap"]["word"],
               rep["bom_only"]["word"], rep["empty"]["word"],
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
    """AC-EDXC6: pure ASCII, stdlib only, no clock, registered once."""
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
        and '"test_export_composed_landed_bom_precedence_seventh_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDXC6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
