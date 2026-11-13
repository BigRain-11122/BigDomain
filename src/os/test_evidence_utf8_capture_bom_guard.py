"""AC-EBOM1..AC-EBOM6 suite for the BOM and NUL capture guard (R2715).

Criteria were pinned in state/queue/tech.md:691 at R2714 BEFORE this code
existed. Every fixture is built in memory and landed under a scratch dir that
this suite removes before it exits; no shipped source file is written.
Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_utf8_capture_bom_guard as EBG  # noqa
import evidence_utf8_capture as EUC  # noqa
import battery_followup as BF  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_utf8_capture_bom_guard.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-utf8-capture-bom-guard",'
WIRED_SUITE = '"test_evidence_utf8_capture_bom_guard.py"'
BASE_LABEL = '"os-evidence-utf8-capture",'

SCRATCH = os.path.join(SRC, "..", "tmp", "ebom-R2716-%d" % os.getpid())

CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK
BOM_FIXTURE = b"\xef\xbb\xbf" + b"alpha\n"
NUL_FIXTURE = b"a\x00b\x00\n"
CRLF_FIXTURE = b"alpha\r\nbeta\r\n"
LONE_CR_FIXTURE = b"alpha\rbeta"
BAD_UTF8 = b"ok\xffbad"
SENTINEL = b"keep me\n"

REAL_EVIDENCE = os.path.join(SRC, "..", "qa", "write-sensitive-R2715.log")
FALLBACK_EVIDENCE = os.path.join(SRC, "..", "qa",
                                 "evidence-utf8-capture-R2714.log")


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_bytes(path, raw):
    with open(path, "wb") as handle:
        handle.write(raw)


def shown(text):
    """ASCII-only rendering, so a GBK console can never break the capture."""
    return text.encode("unicode_escape").decode("ascii")


def sanitise(text):
    """The scratch path carries this run's pid; keep criterion lines stable."""
    return text.replace(SCRATCH, "<scratch>")


def refuse(target, data):
    """Return the refusal, or None when the capture was (wrongly) landed."""
    try:
        EBG.capture(target, data)
    except EBG.Refused as err:
        return err
    return None


def real_evidence():
    for path in (REAL_EVIDENCE, FALLBACK_EVIDENCE):
        if os.path.isfile(path):
            return path
    return None


def ac_ebom1():
    """AC-EBOM1: a BOM prefix is refused and the shipped eol law is asked."""
    ok = True
    path = os.path.join(SCRATCH, "bom.txt")
    err = refuse(path, BOM_FIXTURE)
    ok = check(err is not None and err.code == EBG.E_BOM,
               "AC-EBOM1 a BOM payload is refused as %s (got %r)"
               % (EBG.E_BOM, None if err is None else err.code)) and ok
    ok = check(not os.path.exists(path),
               "AC-EBOM1 the refused BOM capture wrote NO file") and ok
    reading = EBG.eol_reading(BOM_FIXTURE)
    ok = check(reading["bom"] is True and reading["eol_ok"] is False,
               "AC-EBOM1 the shipped eol law reads bom=%s eol_ok=%s on the"
               " SAME bytes" % (reading["bom"], reading["eol_ok"])) and ok
    ok = check(err is not None and err.eol.get("bom") is True,
               "AC-EBOM1 the refusal carries that same eol reading") and ok
    line = "" if err is None else EBG.refusal_line(err)
    ok = check("bom=True" in line and "eol_ok=False" in line,
               "AC-EBOM1 the refusal line prints bom=True eol_ok=False (%r)"
               % (sanitise(line),)) and ok
    shipped = None
    try:
        EUC.capture(os.path.join(SCRATCH, "bom-shipped.txt"), BOM_FIXTURE)
    except EUC.CaptureRefused:
        shipped = "REFUSED"
    ok = check(shipped is None,
               "AC-EBOM1 the shipped capture still LANDS the same BOM bytes"
               " (so this face is a new law, not a duplicate)") and ok
    saved = BF.eol_state

    def fake(raw):
        return (0, 0, True, len(raw))

    BF.eol_state = fake
    try:
        moved = refuse(os.path.join(SCRATCH, "patched-bom.txt"), GOOD)
    finally:
        BF.eol_state = saved
    ok = check(moved is not None and moved.code == EBG.E_BOM,
               "AC-EBOM1 a patched eol law moves the verdict on CLEAN bytes,"
               " so the law is asked at CALL time") and ok
    ok = check(not os.path.exists(os.path.join(SCRATCH,
                                               "patched-bom.txt")),
               "AC-EBOM1 the patched refusal wrote nothing") and ok
    return ok


def ac_ebom2():
    """AC-EBOM2: NUL is refused with its own code and its measured count."""
    ok = True
    path = os.path.join(SCRATCH, "nul.txt")
    err = refuse(path, NUL_FIXTURE)
    ok = check(err is not None and err.code == EBG.E_NUL,
               "AC-EBOM2 a NUL payload is refused as %s (got %r)"
               % (EBG.E_NUL, None if err is None else err.code)) and ok
    ok = check(err is not None and err.counters.get("nul") == 2,
               "AC-EBOM2 the NUL count is measured as 2 (got %r)"
               % (None if err is None else err.counters.get("nul"),)) and ok
    line = "" if err is None else EBG.refusal_line(err)
    ok = check("nul=2" in line,
               "AC-EBOM2 the refusal line prints nul=2 (%r)"
               % (sanitise(line),)) and ok
    ok = check(not os.path.exists(path),
               "AC-EBOM2 the refused NUL capture wrote NO file") and ok
    ok = check(EBG.E_NUL != EBG.E_BOM,
               "AC-EBOM2 the NUL code is distinct from the BOM code") and ok
    shipped_nul = None
    try:
        report = EUC.capture(os.path.join(SCRATCH, "nul-shipped.txt"),
                             NUL_FIXTURE)
        shipped_nul = report["nul"]
    except EUC.CaptureRefused:
        shipped_nul = "REFUSED"
    ok = check(shipped_nul == 2,
               "AC-EBOM2 the shipped capture LANDS it with nul=%r measured"
               " and never enforced" % (shipped_nul,)) and ok
    return ok


def ac_ebom3():
    """AC-EBOM3: every payload R2714 lands stays byte for byte, and clean
    committed evidence still reads ACCEPT."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    report = EBG.capture(path, GOOD)
    ok = check(report["verdict"] == "LANDED",
               "AC-EBOM3 a clean payload still reports LANDED (%r)"
               % (report["verdict"],)) and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-EBOM3 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    ok = check(report["bytes"] == len(GOOD) and report["sha256"]
               == EUC.digest(GOOD),
               "AC-EBOM3 the byte count and digest match the shipped law"
               " (%d, %s)" % (report["bytes"], report["sha256"])) and ok
    ok = check(report["bom"] is False and report["eol_ok"] is True,
               "AC-EBOM3 the landed report names bom=False eol_ok=True"
               ) and ok
    text_path = os.path.join(SCRATCH, "text.txt")
    text = u"line\n\u4e2d\u6587\n"
    EBG.capture(text_path, text)
    ok = check(read_bytes(text_path) == text.encode("utf-8"),
               "AC-EBOM3 text input still lands as its utf-8 encoding"
               ) and ok
    real = real_evidence()
    if real is not None:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        ok = check(EBG.refusal_of(raw) is None,
                   "AC-EBOM3 the real committed evidence reads ACCEPT (%s,"
                   " %d bytes)" % (os.path.basename(real), len(raw))) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-EBOM3 the live read wrote nothing (%s)" % (before,)
                   ) and ok
    else:
        ok = check(False, "AC-EBOM3 a real evidence fixture is missing") and ok
    return ok


def ac_ebom4():
    """AC-EBOM4: every reading R2714 pinned rides unchanged, plus one bounded
    live leg measuring the SAME fixture on BOTH readers."""
    ok = True
    cases = ((CRLF_FIXTURE, EUC.E_CRLF, "crlf", 2, "crlf-keep.txt"),
             (LONE_CR_FIXTURE, EUC.E_LONE_CR, "lone_cr", 1, "lone-keep.txt"),
             (BAD_UTF8, EUC.E_NOT_UTF8, "bad_offset", 2, "bad-keep.txt"))
    for fixture, code, key, want, name in cases:
        path = os.path.join(SCRATCH, name)
        err = refuse(path, fixture)
        ok = check(err is not None and err.code == code,
                   "AC-EBOM4 the R2714 reading %r still refuses as %s (got"
                   " %r)" % (key, code, None if err is None else err.code)
                   ) and ok
        ok = check(err is not None and err.counters.get(key) == want,
                   "AC-EBOM4 its %s count still reads %d (got %r)"
                   % (key, want, None if err is None
                      else err.counters.get(key))) and ok
        ok = check(not os.path.exists(path),
                   "AC-EBOM4 the refused %r still wrote NO file" % (key,)
                   ) and ok
    ok = check(EBG.E_BOM != EUC.E_CRLF and EBG.E_NUL != EUC.E_NOT_UTF8,
               "AC-EBOM4 the two new codes never shadow a shipped code") and ok
    both = (CRLF_FIXTURE, LONE_CR_FIXTURE, BAD_UTF8)
    for fixture in both:
        here = EBG.refusal_of(fixture)
        there = EUC.refusal_of(fixture)
        ok = check(here is not None and there is not None
                   and here["code"] == there["code"],
                   "AC-EBOM4 the fixture of %d bytes reads the SAME code %s on"
                   " BOTH readers" % (len(fixture),
                                      None if there is None else there["code"])
                   ) and ok
    ok = check(EBG.refusal_of(GOOD) is None and EUC.refusal_of(GOOD) is None,
               "AC-EBOM4 the clean payload is accepted on BOTH readers") and ok
    real = real_evidence()
    if real is not None:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        here = EBG.refusal_of(raw)
        there = EUC.refusal_of(raw)
        ok = check(here is None and there is None,
                   "AC-EBOM4 the real evidence file reads ACCEPT on BOTH"
                   " readers (%d bytes)" % (len(raw),)) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-EBOM4 the bounded live leg changed no real byte (%s)"
                   % (before,)) and ok
    else:
        ok = check(False, "AC-EBOM4 a real evidence fixture is missing") and ok
    return ok


def ac_ebom5():
    """AC-EBOM5: a refusal leaves the target absent; an existing target is
    byte-identical afterwards."""
    ok = True
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, BOM_FIXTURE)
    ok = check(not os.path.exists(absent),
               "AC-EBOM5 a refused BOM capture leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == EBG.E_EXISTS,
               "AC-EBOM5 an existing target is refused as %s (got %r)"
               % (EBG.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-EBOM5 the existing target is byte-identical (%s)"
               % (before,)) and ok
    err = refuse(existing, BOM_FIXTURE)
    ok = check(err is not None and err.code == EBG.E_EXISTS,
               "AC-EBOM5 the existence law is asked before the BOM shape"
               ) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-EBOM5 the second refusal left it byte-identical too"
               ) and ok
    return ok


def ac_ebom6():
    """AC-EBOM6: hygiene - ASCII, stdlib only, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-EBOM6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-EBOM6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "json", "os", "sys", "tempfile",
               "battery_followup", "evidence_utf8_capture")
    ok = check(all(line.split()[1].split(".")[0] in allowed
                   for line in imports),
               "AC-EBOM6 every import is stdlib or a shipped face (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-EBOM6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-EBOM6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(BASE_LABEL) == 1,
               "AC-EBOM6 the shipped base label row is untouched (%d)"
               % (registry.count(BASE_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-EBOM6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-EBOM6 six criteria are declared") and ok
    ok = check(EBG.LABEL == "os-evidence-utf8-capture-bom-guard",
               "AC-EBOM6 the face carries its own reconcile label (%r)"
               % (EBG.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_ebom1, ac_ebom2, ac_ebom3, ac_ebom4, ac_ebom5, ac_ebom6]
    try:
        results = [func() for func in checks]
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
    passed = sum(1 for item in results if item)
    print("SUITE %s %d/%d" % ("PASS" if passed == len(results) else "FAIL",
                              passed, len(results)))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    sys.exit(main())
