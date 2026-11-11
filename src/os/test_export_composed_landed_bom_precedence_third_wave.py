"""AC-EDWY1..AC-EDWY6 suite for the composed/landed BOM PRECEDENCE THIRD WAVE.

Criteria were pinned in state/queue/tech.md:662 at R2646 BEFORE this code
existed, from six shapes that window MEASURED with
src/os/limits_export_composed_landed_next_R2646.py and this window re-measured
before any byte was written (qa/limits-export-composed-landed-third-wave-before-R2649.log):

    a_trunc_mixed_extra  TRANSPORT-MIXED       bom=0 (cut fact dropped)
    b_bom_only_vs_text   BOM-EMPTY-PAYLOAD     composed=None (compare lost)
    c_trunc_empty_body   BOM-TRUNCATED         delta=2 (nothing behind prefix)
    d_bom_then_utf16     BOM-BODY-MISMATCH     delta=-10 (two markers, one gap)
    e_legit_ef_mixed     TRANSPORT-MIXED       (already correct, named)
    f_utf16_one_byte     UTF16-BOM-LANDING     (named, not claimed)
    g_clean_lf           PASS                  (already correct, named)

What this proves: a cut over a MIXED body whose HEAD is the composed text
names BOTH the cut and the transport in ONE word (Y1); a BOM-only landing
against non-empty text carries the composed count it was measured against
(Y2); a prefix with nothing behind it is named as a cut with no body rather
than a plain truncation (Y3); two markers on one landing are named as both
markers instead of one body gap (Y4); every AC-EDWX, AC-EDWW and AC-EDWV
answer survives on the same fixtures, including the legitimate 0xef-leading
payload that must NOT be accused of being a cut marker (Y5); and the module
stays pure ASCII, stdlib only, no clock, no network, registered exactly once
with its own suite (Y6).

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
                     "test_export_composed_landed_bom_precedence_third_wave.py")
PARENT_SUITE = os.path.join(
    BASE, "test_export_composed_landed_bom_precedence_second_wave.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence-third-wave"
PARENT_LABEL = "os-export-composed-landed-bom-precedence-second-wave"
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


def verify():
    results = []
    workdir = tempfile.mkdtemp(prefix="edwy2649-suite-")
    try:
        trunc_gap = os.path.join(workdir, "trunc_gap.json")
        bom_only = os.path.join(workdir, "bom_only.json")
        cut_only = os.path.join(workdir, "cut_only.json")
        double = os.path.join(workdir, "double.json")

        write_bytes(trunc_gap, b"\xef\xbb" + MIXED_TAIL)
        write_bytes(bom_only, BOM)
        write_bytes(cut_only, b"\xef\xbb")
        write_bytes(double, BOM + b"\xff\xfe")

        # --- AC-EDWY1: the cut and the transport in ONE word, with the gap.
        rep_tg = CLF.account(trunc_gap, TEXT)
        line_tg = CLF.render(rep_tg)
        results.append(check(
            rep_tg["word"] == CLF.WORD_BOM_TRUNCATED_MIXED_GAP
            and rep_tg["word"] != CLF.WORD_TRANSPORT_MIXED
            and rep_tg["word"] != CLF.WORD_BOM_TRUNCATED_MIXED
            and rep_tg["word"] != CLF.WORD_COMPOSED_MISMATCH
            and rep_tg["transport"] == CLF.TRANSPORT_MIXED
            and rep_tg["bom"] == 2
            and rep_tg["bom_kind"] == "utf8-truncated-gap"
            and rep_tg["composed"] == len(TEXT.encode("utf-8"))
            and rep_tg["disk"] == 18
            and rep_tg["delta"] == 6
            and "TRUNCATED" in line_tg and "MIXED" in line_tg
            and "GAP" in line_tg,
            "AC-EDWY1 trunc_gap word=%s transport=%s bom=%d kind=%s"
            " composed=%s disk=%d delta=%s line=%s"
            % (rep_tg["word"], rep_tg["transport"], rep_tg["bom"],
               rep_tg["bom_kind"], rep_tg["composed"], rep_tg["disk"],
               rep_tg["delta"], line_tg)))

        # --- AC-EDWY2: an empty payload carries the count it was measured
        # against, and the EMPTY-text control keeps composed=None.
        rep_bo = CLF.account(bom_only, TEXT)
        line_bo = CLF.render(rep_bo)
        rep_bo_empty = CLF.account(bom_only, "")
        results.append(check(
            rep_bo["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep_bo["word"] != CLF.WORD_BOM_LANDING
            and rep_bo["bom"] == 3
            and rep_bo["bom_kind"] == "utf8-empty"
            and rep_bo["composed"] == len(TEXT.encode("utf-8"))
            and rep_bo["disk"] == 3
            and rep_bo["delta"] == -9
            and "composed=12" in line_bo and "EMPTY-PAYLOAD" in line_bo
            and rep_bo_empty["word"] == CLF.WORD_BOM_EMPTY_PAYLOAD
            and rep_bo_empty["composed"] is None
            and rep_bo_empty["delta"] is None,
            "AC-EDWY2 bom_only word=%s composed=%s disk=%d delta=%s"
            " empty_text=%s/%s line=%s"
            % (rep_bo["word"], rep_bo["composed"], rep_bo["disk"],
               rep_bo["delta"], rep_bo_empty["composed"],
               rep_bo_empty["delta"], line_bo)))

        # --- AC-EDWY3: a prefix with NOTHING behind it names the cut alone.
        rep_co = CLF.account(cut_only, "")
        line_co = CLF.render(rep_co)
        results.append(check(
            rep_co["word"] == CLF.WORD_BOM_CUT_NO_BODY
            and rep_co["word"] != CLF.WORD_BOM_TRUNCATED
            and rep_co["word"] != CLF.WORD_EMPTY_LANDING
            and rep_co["bom"] == 2
            and rep_co["bom_kind"] == "utf8-cut-only"
            and rep_co["composed"] is None
            and rep_co["delta"] is None
            and rep_co["disk"] == 2
            and "CUT-NO-BODY" in line_co,
            "AC-EDWY3 cut_only word=%s bom=%d kind=%s composed=%s delta=%s"
            " disk=%d line=%s"
            % (rep_co["word"], rep_co["bom"], rep_co["bom_kind"],
               rep_co["composed"], rep_co["delta"], rep_co["disk"],
               line_co)))

        # --- AC-EDWY4: two markers on one landing are named as both.
        rep_dm = CLF.account(double, TEXT)
        line_dm = CLF.render(rep_dm)
        results.append(check(
            rep_dm["word"] == CLF.WORD_BOM_DOUBLE_MARKER
            and rep_dm["word"] != CLF.WORD_BOM_BODY_MISMATCH
            and rep_dm["word"] != CLF.WORD_BOM_LANDING
            and rep_dm["bom"] == 5
            and rep_dm["bom_kind"] == "utf8+utf16"
            and rep_dm["disk"] == 5
            and "DOUBLE-MARKER" in line_dm
            and "utf8+utf16" in line_dm,
            "AC-EDWY4 double_marker word=%s bom=%d kind=%s disk=%d line=%s"
            % (rep_dm["word"], rep_dm["bom"], rep_dm["bom_kind"],
               rep_dm["disk"], line_dm)))

        # --- AC-EDWY5: every AC-EDWX / AC-EDWW / AC-EDWV answer survives.
        results.append(legacy_answers(workdir))

        # --- AC-EDWY6: ascii, stdlib only, no clock, registered exactly once.
        results.append(hygiene())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


def legacy_answers(workdir):
    """AC-EDWY5: the parent words are re-read on their own fixtures."""
    fixtures = {
        "bom_gap": BOM + TEXT.encode("utf-8") + b"extra\n",
        "bom_mixed": BOM + b'{\r\n "a": 1\n}\r\n',
        "bom_clean": BOM + TEXT.encode("utf-8"),
        "utf16le": b"\xff\xfe" + TEXT.encode("utf-16-le"),
        "utf16_empty": b"\xff\xfe",
        "short2": b"\xef\xbb" + TEXT.encode("utf-8"),
        "short1": b"\xef" + TEXT.encode("utf-8"),
        "short_mixed": b"\xef\xbb" + b'{\r\n "a": 1\n}\r\n',
        "mixed": b'{\r\n "a": 1\n}\r\n',
        "empty": b"",
        "lf": TEXT.encode("utf-8"),
        "crlf": CRLF.encode("utf-8"),
        "gap": TEXT.encode("utf-8") + b"extra\n",
        "one": b'{"a":1}',
        "utf16_one": b"\xff\xfe\x00",
    }
    paths = {}
    for name, raw in fixtures.items():
        path = os.path.join(workdir, "legacy_%s.json" % name)
        write_bytes(path, raw)
        paths[name] = path
    legit = os.path.join(workdir, "legacy_legit_mixed.json")
    write_bytes(legit, "\uf000".encode("utf-8") + b'{\r\n 1\n}\r\n')
    before = fingerprint(workdir)
    rep = {}
    for name in fixtures:
        rep[name] = CLF.account(paths[name], TEXT)
    rep["bom_clean"] = CLF.account(paths["bom_clean"], TEXT)
    rep["one"] = CLF.account(paths["one"], '{"a":1}')
    rep["crlf_caller"] = CLF.account(paths["crlf"], CRLF)
    rep["legit"] = CLF.account(
        legit, "\uf000" + '{\r\n 1\n}\r\n')
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
        # AC-EDWZ1 (pinned at R2649 in state/queue/tech.md:663 BEFORE the
        # R2653 code) changes exactly this shape: a UTF-16 body is an even
        # number of bytes, so the one byte remnant can no longer be called a
        # whole landing. The assertion stays an EXACT word equality - the new
        # word is the shipped answer, not a loosened subset - and the rest of
        # this legacy reading is untouched.
        and rep["utf16_one"]["word"] == CLF.WORD_UTF16_BOM_SHORT_BODY
        and rep["short2"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short2"]["bom"] == 2 and rep["short2"]["delta"] == 2
        and rep["short1"]["word"] == CLF.WORD_BOM_TRUNCATED
        and rep["short1"]["bom"] == 1 and rep["short1"]["delta"] == 1
        and rep["short_mixed"]["word"] == CLF.WORD_BOM_TRUNCATED_MIXED
        and rep["short_mixed"]["bom"] == 2
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
        "AC-EDWY5 parent answers bom_gap=%s/%d bom_mixed=%s bom=%s"
        " utf16=%s/%s/#%d trunc2=%s/#%d trunc1=%s/#%d trunc_mixed=%s"
        " mixed=%s empty=%s lf=%s crlf=%s caller=%s gap=%s/%d one=%s"
        " legit=%s export=%s untouched=%s"
        % (rep["bom_gap"]["word"], rep["bom_gap"]["delta"],
           rep["bom_mixed"]["word"], rep["bom_clean"]["word"],
           rep["utf16le"]["word"], rep["utf16_empty"]["word"],
           rep["utf16le"]["bom"], rep["short2"]["word"], rep["short2"]["bom"],
           rep["short1"]["word"], rep["short1"]["bom"],
           rep["short_mixed"]["word"], rep["mixed"]["word"],
           rep["empty"]["word"], rep["lf"]["word"], rep["crlf"]["word"],
           rep["crlf_caller"]["word"], rep["gap"]["word"],
           rep["gap"]["delta"], rep["one"]["word"], rep["legit"]["word"],
           words_export, before == after))


def hygiene():
    """AC-EDWY6: pure ASCII, stdlib only, no clock, registered once."""
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
        and '"test_export_composed_landed_bom_precedence_third_wave.py"),'
        in runner
        and os.path.isfile(PARENT_SUITE)
        and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
        and len(parent) == 1 and parent[0][2] == 6,
        "AC-EDWY6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
        " cells=%s parent_cells=%s"
        % (module_ascii, suite_ascii, "time" in imports,
           sorted(imports & set(NET)), bool(wired),
           wired[0][2] if wired else "-",
           parent[0][2] if parent else "-"))


if __name__ == "__main__":
    sys.exit(verify())
