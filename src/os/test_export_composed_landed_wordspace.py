"""AC-EDWV1..AC-EDWV6 suite for the composed/landed WORD SPACE (R2638).

Criteria were pinned in state/queue/tech.md:659 at R2637 BEFORE this code
existed, from three shapes that window MEASURED riding on COMPOSED-MISMATCH:
a MIXED landing with composed=None, an EMPTY landing reported as delta -12, and
a BOM landing indistinguishable from a genuine three byte content gap.

What this proves: a MIXED landing earns its own word and still carries the
bytes it read (WV1); an EMPTY landing earns its own word distinct from
COMPOSED-MISMATCH (WV2); a BOM landing is named as a BOM landing with the BOM
counted separately rather than as a content delta (WV3); all five shapes each
keep exactly ONE word and nothing is written (WV4); every AC-EDWT answer
survives on the same fixtures, including the CRLF caller PASS, the gap word
and the five pre-existing export verdict words (WV5); and the module stays
pure ASCII, stdlib only, no clock, no network, registered exactly once at six
criteria with its own suite wired into the runner (WV6).

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
WIRED = os.path.join(BASE, "test_export_composed_landed_face.py")
SELFTEST = os.path.abspath(__file__)
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-wordspace"
OLD_LABEL = "os-export-composed-landed-face"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

LF = '{\n "a": 1\n}\n'
CRLF = LF.replace("\n", "\r\n")


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
    workdir = tempfile.mkdtemp(prefix="edwv2638-suite-")
    try:
        mixed = os.path.join(workdir, "mixed.json")
        empty = os.path.join(workdir, "empty.json")
        bom = os.path.join(workdir, "bom.json")
        lf = os.path.join(workdir, "lf.json")
        crlf = os.path.join(workdir, "crlf.json")
        gap = os.path.join(workdir, "gap.json")
        one = os.path.join(workdir, "one.json")
        write_bytes(mixed, b'{\r\n "a": 1\n}\r\n')
        write_bytes(empty, b"")
        write_bytes(bom, b"\xef\xbb\xbf" + LF.encode("utf-8"))
        write_bytes(lf, LF.encode("utf-8"))
        write_bytes(crlf, CRLF.encode("utf-8"))
        write_bytes(gap, LF.encode("utf-8") + b"extra\n")
        write_bytes(one, b'{"a":1}')

        # --- AC-EDWV1: MIXED earns its own word and still carries its bytes.
        rep_mixed = CLF.account(mixed, LF)
        line_mixed = CLF.render(rep_mixed)
        results.append(check(
            rep_mixed["word"] == CLF.WORD_TRANSPORT_MIXED
            and rep_mixed["transport"] == CLF.TRANSPORT_MIXED
            and rep_mixed["disk"] == 14
            and rep_mixed["composed"] is None
            and str(rep_mixed["disk"]) in line_mixed,
            "AC-EDWV1 mixed word=%s transport=%s disk=%d line=%s"
            % (rep_mixed["word"], rep_mixed["transport"],
               rep_mixed["disk"], line_mixed)))

        # --- AC-EDWV2: EMPTY earns its own word, distinct from the gap word.
        rep_empty = CLF.account(empty, LF)
        results.append(check(
            rep_empty["word"] == CLF.WORD_EMPTY_LANDING
            and rep_empty["word"] != CLF.WORD_COMPOSED_MISMATCH
            and rep_empty["disk"] == 0
            and rep_empty["composed"] is None,
            "AC-EDWV2 empty word=%s disk=%d distinct=%s"
            % (rep_empty["word"], rep_empty["disk"],
               rep_empty["word"] != CLF.WORD_COMPOSED_MISMATCH)))

        # --- AC-EDWV3: a BOM landing is a BOM landing, BOM counted separately.
        rep_bom = CLF.account(bom, LF)
        line_bom = CLF.render(rep_bom)
        results.append(check(
            rep_bom["word"] == CLF.WORD_BOM_LANDING
            and rep_bom["bom"] == 3
            and rep_bom["composed"] == len(LF.encode("utf-8"))
            and rep_bom["delta"] == 0
            and rep_bom["disk"] == len(LF.encode("utf-8")) + 3
            and "bom=3" in line_bom,
            "AC-EDWV3 bom word=%s bom=%d composed=%d body_delta=%d disk=%d"
            % (rep_bom["word"], rep_bom["bom"], rep_bom["composed"],
               rep_bom["delta"], rep_bom["disk"])))

        # --- AC-EDWV4: five shapes, one word each, nothing written.
        before = fingerprint(workdir)
        words = [
            CLF.account(mixed, LF)["word"],
            CLF.account(empty, LF)["word"],
            CLF.account(bom, LF)["word"],
            CLF.account(crlf, LF)["word"],
            CLF.account(one, '{"a":1}')["word"],
        ]
        after = fingerprint(workdir)
        results.append(check(
            len(words) == 5
            and words[0] == CLF.WORD_TRANSPORT_MIXED
            and words[1] == CLF.WORD_EMPTY_LANDING
            and words[2] == CLF.WORD_BOM_LANDING
            and words[3] == CLF.WORD_PASS
            and words[4] == CLF.WORD_PASS
            and before == after,
            "AC-EDWV4 words=%s untouched=%s" % (words, before == after)))

        # --- AC-EDWV5: every AC-EDWT answer survives beside the new words.
        rep_lf = CLF.account(lf, LF)
        rep_crlf = CLF.account(crlf, LF)
        rep_crlf_caller = CLF.account(crlf, CRLF)
        rep_gap = CLF.account(gap, LF)
        at = {"k": 1}
        words_export = (
            EX.classify({"k": 2}, at, at, True, 10, 10) == EX.DOC_DOCTORED
            and EX.classify(at, at, at, False, 10, 10) == EX.CHECK_MISMATCH
            and EX.classify(at, at, {"k": 3}, True, 10, 10)
            == EX.DRIFT_UNDER_WRITE
            and EX.classify(at, at, at, True, 10, 11) == EX.SIZE_MISMATCH
            and EX.classify(at, at, at, True, 10, 10) == EX.VERDICT_PASS)
        results.append(check(
            rep_lf["word"] == CLF.WORD_PASS
            and rep_lf["transport"] == CLF.TRANSPORT_LF
            and rep_crlf["word"] == CLF.WORD_PASS
            and rep_crlf_caller["word"] == CLF.WORD_PASS
            and rep_crlf_caller["composed"] == rep_crlf_caller["disk"]
            and rep_gap["word"] == CLF.WORD_COMPOSED_MISMATCH
            and rep_gap["delta"] == 6
            and words_export,
            "AC-EDWV5 lf=%s crlf=%s caller=%s gap=%s/%d export_words=%s"
            % (rep_lf["word"], rep_crlf["word"], rep_crlf_caller["word"],
               rep_gap["word"], rep_gap["delta"], words_export)))

        # --- AC-EDWV6: ascii, stdlib only, no clock, registered once.
        with io.open(MODULE, encoding="utf-8") as handle:
            module_text = handle.read()
        with io.open(SELFTEST, encoding="utf-8") as handle:
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
        old = [row for row in RA.SUITES if row[0] == OLD_LABEL]
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and ('"%s",' % LABEL) in runner
            and '"test_export_composed_landed_wordspace.py"),' in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA
            and len(old) == 1 and old[0][2] == 6,
            "AC-EDWV6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
            " cells=%s old_cells=%s"
            % (module_ascii, suite_ascii, "time" in imports,
               sorted(imports & set(NET)), bool(wired),
               wired[0][2] if wired else "-",
               old[0][2] if old else "-")))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())
