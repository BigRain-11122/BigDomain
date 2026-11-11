"""AC-EDWT1..AC-EDWT6 suite for the composed/landed export face (R2637).

Criteria were pinned in state/queue/tech.md:658 at R2596 BEFORE this code
existed, and the gap they close was MEASURED at R2637 with
src/os/limits_export_composed_landed_R2637.py: a CRLF landing is three bytes
longer than the composed LF text for a three line document, and the shipped
classify() answered PASS with that gap invisible.

What this proves: a composed/landed gap earns its own word naming BOTH counts
(EDWT1); a legal CRLF landing still reads PASS because the composed length is
normalised into the landing's own transport (EDWT2); the transport is read off
the landed bytes rather than off the composed text (EDWT3); the account reads
the file ONCE and writes nothing, so a transport that flips under the caller
still yields exactly one word (EDWT4); every pre-existing verdict word and the
six-argument call shape survive byte for byte (EDWT5); and the module is pure
ASCII, stdlib only, no clock, no network, registered exactly once at six
criteria with its own suite wired into the runner (EDWT6).

All fixtures live in private temporary directories; nothing under docs/ or qa/
is touched. Stdlib only, ASCII source, zero network, no clock.
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
SELFTEST = os.path.abspath(__file__)
RUNNER = os.path.join(SANDBOX, "reconcile_all.py")
LABEL = "os-export-composed-landed-face"
NET = ("urllib", "requests", "socket", "http", "ftplib", "xmlrpc",
       "smtplib", "asyncio", "time")

TEXT = '{\n "a": 1\n}\n'


def check(ok, label):
    # The marker must START the line: the shipped capture digests lines that
    # begin with "PASS "/"FAIL ", so an indented marker would land an empty
    # digest.
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def fingerprint(path):
    """(name, size, sha256) for every entry in a directory, sorted by name."""
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
    workdir = tempfile.mkdtemp(prefix="edwt2637-suite-")
    try:
        # --- AC-EDWT1: a composed/landed gap gets its own word and BOTH counts.
        gap = os.path.join(workdir, "gap.json")
        write_bytes(gap, b'{\n "a": 1\n}\nextra\n')   # 6 bytes longer than TEXT
        rep_gap = CLF.account(gap, TEXT)
        line_gap = CLF.render(rep_gap)
        results.append(check(
            rep_gap["word"] == CLF.WORD_COMPOSED_MISMATCH
            and rep_gap["composed"] == len(TEXT.encode("utf-8"))
            and rep_gap["disk"] == len(TEXT.encode("utf-8")) + 6
            and rep_gap["delta"] == 6
            and str(rep_gap["composed"]) in line_gap
            and str(rep_gap["disk"]) in line_gap
            and CLF.WORD_COMPOSED_MISMATCH != "SIZE-MISMATCH",
            "AC-EDWT1 gap word=%s composed=%d disk=%d delta=%d line=%s"
            % (rep_gap["word"], rep_gap["composed"], rep_gap["disk"],
               rep_gap["delta"], line_gap)))

        # --- AC-EDWT2: a legal CRLF landing reports its OWN length as PASS.
        crlf = os.path.join(workdir, "crlf.json")
        write_bytes(crlf, TEXT.replace("\n", "\r\n").encode("utf-8"))
        rep_crlf = CLF.account(crlf, TEXT)
        # R2637 birth-site repair: a caller that ALREADY hands CRLF must not be
        # charged for the CR twice (measured 18 composed against 15 landed
        # before the fold), so the same landing is asked with CRLF composed
        # text as well and must still read PASS.
        rep_crlf_caller = CLF.account(crlf, TEXT.replace("\n", "\r\n"))
        results.append(check(
            rep_crlf["word"] == CLF.WORD_PASS
            and rep_crlf["transport"] == CLF.TRANSPORT_CRLF
            and rep_crlf["composed"] == rep_crlf["disk"]
            and rep_crlf["delta"] == 0
            and rep_crlf_caller["word"] == CLF.WORD_PASS
            and rep_crlf_caller["composed"] == rep_crlf_caller["disk"]
            and CLF.composed_bytes(TEXT, CLF.TRANSPORT_CRLF)
            > len(TEXT.encode("utf-8")),
            "AC-EDWT2 crlf word=%s transport=%s composed=%d disk=%d"
            " caller_crlf=%s/%d"
            % (rep_crlf["word"], rep_crlf["transport"],
               rep_crlf["composed"], rep_crlf["disk"],
               rep_crlf_caller["word"], rep_crlf_caller["composed"])))

        # --- AC-EDWT3: the transport comes off the LANDED bytes, not the text.
        lf = os.path.join(workdir, "lf.json")
        write_bytes(lf, TEXT.encode("utf-8"))
        rep_lf = CLF.account(lf, TEXT)
        same_text_two_transports = (
            CLF.account(lf, TEXT)["transport"] == CLF.TRANSPORT_LF
            and CLF.account(crlf, TEXT)["transport"] == CLF.TRANSPORT_CRLF)
        mixed = os.path.join(workdir, "mixed.json")
        write_bytes(mixed, b'{\r\n "a": 1\n}\r\n')
        rep_mixed = CLF.account(mixed, TEXT)
        results.append(check(
            rep_lf["transport"] == CLF.TRANSPORT_LF
            and same_text_two_transports
            and rep_mixed["transport"] == CLF.TRANSPORT_MIXED
            and rep_mixed["word"] == CLF.WORD_COMPOSED_MISMATCH
            and rep_mixed["composed"] is None,
            "AC-EDWT3 lf=%s crlf=%s mixed=%s mixed_word=%s"
            % (rep_lf["transport"], rep_crlf["transport"],
               rep_mixed["transport"], rep_mixed["word"])))

        # --- AC-EDWT4: ONE read, one word, nothing written.
        one = os.path.join(workdir, "one.json")
        write_bytes(one, TEXT.encode("utf-8"))
        before = fingerprint(workdir)
        opened = {"n": 0}
        real_io = CLF.io

        class CountingIO(object):
            @staticmethod
            def open(*args, **kwargs):
                opened["n"] += 1
                return real_io.open(*args, **kwargs)

        CLF.io = CountingIO
        try:
            rep_one = CLF.account(one, TEXT)
        finally:
            CLF.io = real_io
        after = fingerprint(workdir)
        results.append(check(
            opened["n"] == 1 and rep_one["word"] == CLF.WORD_PASS
            and before == after,
            "AC-EDWT4 reads=%d word=%s untouched=%s"
            % (opened["n"], rep_one["word"], before == after)))

        # --- AC-EDWT5: every pre-existing word and the six-arg call survive.
        at = {"k": 1}
        words = {
            "doctor": EX.classify({"k": 2}, at, at, True, 10, 10),
            "check": EX.classify(at, at, at, False, 10, 10),
            "drift": EX.classify(at, at, {"k": 3}, True, 10, 10),
            "size": EX.classify(at, at, at, True, 10, 11),
            "pass": EX.classify(at, at, at, True, 10, 10),
        }
        by_call = EX.classify(at, at, at, True, 10, 10,
                              composed_text=TEXT, path=gap)
        results.append(check(
            words["doctor"] == EX.DOC_DOCTORED
            and words["check"] == EX.CHECK_MISMATCH
            and words["drift"] == EX.DRIFT_UNDER_WRITE
            and words["size"] == EX.SIZE_MISMATCH
            and words["pass"] == EX.VERDICT_PASS
            and by_call == CLF.WORD_COMPOSED_MISMATCH,
            "AC-EDWT5 doctor=%s check=%s drift=%s size=%s pass=%s by_call=%s"
            % (words["doctor"], words["check"], words["drift"],
               words["size"], words["pass"], by_call)))

        # --- AC-EDWT6: ascii, stdlib only, no clock, registered once.
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
        results.append(check(
            module_ascii and suite_ascii
            and not (imports & set(NET)) and "time" not in imports
            and ('"%s",' % LABEL) in runner
            and '"test_export_composed_landed_face.py"),' in runner
            and len(wired) == 1 and wired[0][2] == EXPECTED_CRITERIA,
            "AC-EDWT6 hygiene ascii=%s/%s clock=%s network=%s registered=%s"
            " cells=%s"
            % (module_ascii, suite_ascii, "time" in imports,
               sorted(imports & set(NET)), bool(wired),
               wired[0][2] if wired else "-")))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("SUITE %s %d/%d"
          % ("PASS" if all(results) else "FAIL", sum(results),
             EXPECTED_CRITERIA))
    return 0 if all(results) and len(results) == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(verify())
