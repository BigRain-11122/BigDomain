"""AC-EDWW1..AC-EDWW6 suite for the composed/landed BOM PRECEDENCE (R2643).

Criteria were pinned in state/queue/tech.md:660 at R2638 BEFORE this code
existed, from four shapes that window MEASURED with
src/os/limits_export_composed_landed_next_R2638.py and this window re-measured
before any byte was written:

    a_bom_body_gap  BOM-LANDING       transport=lf    bom=3 delta=6
    b_bom_mixed     BOM-LANDING       transport=mixed bom=3 delta=2
    c_utf16_bom     COMPOSED-MISMATCH transport=lf    bom=0 delta=14
    d_short_bom     COMPOSED-MISMATCH transport=lf    bom=0 delta=2
    e_empty_both    EMPTY-LANDING     (already correct, named at R2638)

What this proves: a BOM landing whose BODY disagrees earns a word that names
BOTH facts (WW1); a BOM landing carrying MIXED separators names both facts in
ONE word rather than letting the BOM hide the transport (WW2); a UTF-16 BOM in
either byte order is named as a UTF-16 BOM instead of a fourteen byte content
delta (WW3); a TRUNCATED BOM prefix is named as truncated instead of a two byte
content delta, and a legitimate 0xef-leading payload is NOT accused (WW4);
every AC-EDWV and AC-EDWT answer survives on the same fixtures, including the
clean BOM landing that must stay BOM-LANDING (WW5); and the module stays pure
ASCII, stdlib only, no clock, no network, registered exactly once at six
criteria with its own suite wired into the runner (WW6).

Fixtures live in private temporary directories. Stdlib only, ASCII source,
zero network, no clock.
"""

import hashlib
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

import export_composed_landed_face as CLF  # noqa: E402
import export_R2431 as EX  # noqa: E402
import reconcile_all as RA  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "export_composed_landed_face.py")
WIRED = os.path.join(BASE, "test_export_composed_landed_bom_precedence.py")
PARENT_SUITE = os.path.join(BASE, "test_export_composed_landed_wordspace.py")
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-bom-precedence"
PARENT_LABEL = "os-export-composed-landed-wordspace"
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
    workdir = tempfile.mkdtemp(prefix="edww2643-suite-")
    try:
        bom_gap = os.path.join(workdir, "bom_gap.json")
        bom_mixed = os.path.join(workdir, "bom_mixed.json")
        bom_clean = os.path.join(workdir, "bom_clean.json")
        utf16le = os.path.join(workdir, "utf16le.json")
        utf16be = os.path.join(workdir, "utf16be.json")
        short2 = os.path.join(workdir, "short2.json")
        short1 = os.path.join(workdir, "short1.json")
        legit = os.path.join(workdir, "legit_ef.json")
        mixed = os.path.join(workdir, "mixed.json")
        empty = os.path.join(workdir, "empty.json")
        lf = os.path.join(workdir, "lf.json")
        crlf = os.path.join(workdir, "crlf.json")
        gap = os.path.join(workdir, "gap.json")
        one = os.path.join(workdir, "one.json")

        write_bytes(bom_gap, BOM + TEXT.encode("utf-8") + b"extra\n")
        write_bytes(bom_mixed, BOM + b'{\r\n "a": 1\n}\r\n')
        write_bytes(bom_clean, BOM + TEXT.encode("utf-8"))
        write_bytes(utf16le, b"\xff\xfe" + TEXT.encode("utf-16-le"))
        write_bytes(utf16be, b"\xfe\xff" + TEXT.encode("utf-16-be"))
        write_bytes(short2, b"\xef\xbb" + TEXT.encode("utf-8"))
        write_bytes(short1, b"\xef" + TEXT.encode("utf-8"))
        # A legitimate payload whose first byte is 0xef but whose rest is NOT
        # the composed text: it must not be accused of being a truncated BOM.
        write_bytes(legit, "\uf000".encode("utf-8") + b'{"x":2}\n')
        write_bytes(mixed, b'{\r\n "a": 1\n}\r\n')
        write_bytes(empty, b"")
        write_bytes(lf, TEXT.encode("utf-8"))
        write_bytes(crlf, CRLF.encode("utf-8"))
        write_bytes(gap, TEXT.encode("utf-8") + b"extra\n")
        write_bytes(one, b'{"a":1}')

        # --- AC-EDWW1: a BOM landing whose BODY disagrees names BOTH facts.
        rep_gap = CLF.account(bom_gap, TEXT)
        line_gap = CLF.render(rep_gap)
        results.append(check(
            rep_gap["word"] == CLF.WORD_BOM_BODY_MISMATCH
            and rep_gap["word"] != CLF.WORD_BOM_LANDING
            and rep_gap["bom"] == 3
            and rep_gap["delta"] == 6
            and rep_gap["disk"] == len(BOM) + len(TEXT.encode("utf-8")) + 6
            and "BOM" in line_gap and "delta=6" in line_gap
            and "bom=3" in line_gap,
            "AC-EDWW1 bom_gap word=%s bom=%d delta=%d disk=%d line=%s"
            % (rep_gap["word"], rep_gap["bom"], rep_gap["delta"],
               rep_gap["disk"], line_gap)))

        # --- AC-EDWW2: BOM plus MIXED names BOTH facts in ONE word.
        rep_bm = CLF.account(bom_mixed, TEXT)
        line_bm = CLF.render(rep_bm)
        results.append(check(
            rep_bm["word"] == CLF.WORD_BOM_TRANSPORT_MIXED
            and rep_bm["word"] != CLF.WORD_BOM_LANDING
            and rep_bm["word"] != CLF.WORD_TRANSPORT_MIXED
            and rep_bm["transport"] == CLF.TRANSPORT_MIXED
            and rep_bm["bom"] == 3
            and rep_bm["disk"] == 17
            and "BOM" in line_bm and "MIXED" in line_bm,
            "AC-EDWW2 bom_mixed word=%s transport=%s bom=%d disk=%d line=%s"
            % (rep_bm["word"], rep_bm["transport"], rep_bm["bom"],
               rep_bm["disk"], line_bm)))

        # --- AC-EDWW3: a UTF-16 BOM is named as one, in BOTH byte orders.
        rep_le = CLF.account(utf16le, TEXT)
        rep_be = CLF.account(utf16be, TEXT)
        line_le = CLF.render(rep_le)
        results.append(check(
            rep_le["word"] == CLF.WORD_UTF16_BOM
            and rep_be["word"] == CLF.WORD_UTF16_BOM
            and rep_le["word"] != CLF.WORD_COMPOSED_MISMATCH
            and rep_le["bom"] == 2 and rep_be["bom"] == 2
            and rep_le.get("bom_kind") == "utf16"
            and rep_le["delta"] is None
            and rep_le["disk"] == 26
            and "UTF16" in line_le and "kind=utf16" in line_le,
            "AC-EDWW3 utf16 le=%s/%s be=%s/%s disk=%d line=%s"
            % (rep_le["word"], rep_le.get("bom_kind"), rep_be["word"],
               rep_be.get("bom_kind"), rep_le["disk"], line_le)))

        # --- AC-EDWW4: truncated prefix named; a legit 0xef payload is not.
        rep_s2 = CLF.account(short2, TEXT)
        rep_s1 = CLF.account(short1, TEXT)
        rep_legit = CLF.account(legit, "\uf000" + '{"x":2}\n')
        line_s2 = CLF.render(rep_s2)
        results.append(check(
            rep_s2["word"] == CLF.WORD_BOM_TRUNCATED
            and rep_s1["word"] == CLF.WORD_BOM_TRUNCATED
            and rep_s2["word"] != CLF.WORD_COMPOSED_MISMATCH
            and rep_s2["bom"] == 2 and rep_s2["delta"] == 2
            and rep_s1["bom"] == 1 and rep_s1["delta"] == 1
            and rep_s2.get("bom_kind") == "utf8-truncated"
            and "BOM-TRUNCATED" in line_s2
            and rep_legit["word"] == CLF.WORD_PASS
            and rep_legit["bom"] == 0,
            "AC-EDWW4 short2=%s/%d/%d short1=%s/%d legit=%s/%d"
            % (rep_s2["word"], rep_s2["bom"], rep_s2["delta"],
               rep_s1["word"], rep_s1["bom"], rep_legit["word"],
               rep_legit["bom"])))

        # --- AC-EDWW5: every AC-EDWV / AC-EDWT answer survives.
        before = fingerprint(workdir)
        rep_mixed = CLF.account(mixed, TEXT)
        rep_empty = CLF.account(empty, TEXT)
        rep_bom = CLF.account(bom_clean, TEXT)
        rep_crlf = CLF.account(crlf, TEXT)
        rep_caller = CLF.account(crlf, CRLF)
        rep_lf = CLF.account(lf, TEXT)
        rep_body_gap = CLF.account(gap, TEXT)
        rep_one = CLF.account(one, '{"a":1}')
        after = fingerprint(workdir)
        at = {"k": 1}
        words_export = (
            EX.classify({"k": 2}, at, at, True, 10, 10) == EX.DOC_DOCTORED
            and EX.classify(at, at, at, False, 10, 10) == EX.CHECK_MISMATCH
            and EX.classify(at, at, {"k": 3}, True, 10, 10)
            == EX.DRIFT_UNDER_WRITE
            and EX.classify(at, at, at, True, 10, 11) == EX.SIZE_MISMATCH
            and EX.classify(at, at, at, True, 10, 10) == EX.VERDICT_PASS)
        results.append(check(
            rep_mixed["word"] == CLF.WORD_TRANSPORT_MIXED
            and rep_mixed["transport"] == CLF.TRANSPORT_MIXED
            and rep_mixed["composed"] is None
            and rep_empty["word"] == CLF.WORD_EMPTY_LANDING
            and rep_empty["disk"] == 0 and rep_empty["composed"] is None
            and rep_bom["word"] == CLF.WORD_BOM_LANDING
            and rep_bom["bom"] == 3 and rep_bom["delta"] == 0
            and rep_bom["composed"] == len(TEXT.encode("utf-8"))
            and rep_crlf["word"] == CLF.WORD_PASS
            and rep_crlf["transport"] == CLF.TRANSPORT_CRLF
            and rep_crlf["composed"] == rep_crlf["disk"]
            and rep_caller["word"] == CLF.WORD_PASS
            and rep_lf["word"] == CLF.WORD_PASS
            and rep_body_gap["word"] == CLF.WORD_COMPOSED_MISMATCH
            and rep_body_gap["delta"] == 6
            and rep_one["word"] == CLF.WORD_PASS
            and words_export and before == after,
            "AC-EDWW5 mixed=%s empty=%s bom=%s/%d crlf=%s caller=%s lf=%s"
            " gap=%s/%d one=%s export=%s untouched=%s"
            % (rep_mixed["word"], rep_empty["word"], rep_bom["word"],
               rep_bom["delta"], rep_crlf["word"], rep_caller["word"],
               rep_lf["word"], rep_body_gap["word"], rep_body_gap["delta"],
               rep_one["word"], words_export, before == after)))

        # --- AC-EDWW6: ascii, stdlib only, no clock, registered exactly once.
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
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and ('"%s",' % LABEL) in runner
            and '"test_export_composed_landed_bom_precedence.py"),' in runner
            and os.path.isfile(PARENT_SUITE)
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
            and len(parent) == 1 and parent[0][2] == 6,
            "AC-EDWW6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
            " cells=%s parent_cells=%s"
            % (module_ascii, suite_ascii, "time" in imports,
               sorted(imports & set(NET)), bool(wired),
               wired[0][2] if wired else "-",
               parent[0][2] if parent else "-")))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())
