"""AC-EUC1..AC-EUC6 suite for the evidence UTF-8 capture guard (R2714).

Criteria were pinned in state/queue/tech.md:689 at R2494 BEFORE this code
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

import evidence_utf8_capture as EUC  # noqa
import evidence_capture as EC  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_utf8_capture.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-utf8-capture",'
WIRED_SUITE = '"test_evidence_utf8_capture.py"'

SCRATCH = os.path.join(SRC, "..", "tmp", "euc-R2714-%d" % os.getpid())

CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK
CRLF_FIXTURE = b"alpha\r\nbeta\r\n"
LONE_CR_FIXTURE = b"alpha\rbeta"
BAD_UTF8 = b"ok\xffbad"
SENTINEL = b"keep me\n"


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
        EUC.capture(target, data)
    except EUC.CaptureRefused as err:
        return err
    return None


def ac_euc1():
    """AC-EUC1: asked at CALL time, landed by one atomic write with read-back."""
    ok = True
    path = os.path.join(SCRATCH, "call-time.txt")
    report = EUC.capture(path, GOOD)
    ok = check(report["verdict"] == "LANDED",
               "AC-EUC1 a clean capture reports LANDED (%r)"
               % (report["verdict"],)) and ok
    ok = check(os.path.isfile(path), "AC-EUC1 the target exists on disk") and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-EUC1 the read-back equals the bytes handed in") and ok
    ok = check(report["sha256"] == EUC.digest(GOOD),
               "AC-EUC1 the report carries the input digest (%s)"
               % (report["sha256"],)) and ok
    leftovers = [name for name in os.listdir(SCRATCH)
                 if ".euc-tmp-" in name]
    ok = check(not leftovers,
               "AC-EUC1 no temp file survives the atomic write (%s)"
               % (leftovers,)) and ok
    saved = EUC.measure

    def fake(raw):
        counts = saved(raw)
        counts["crlf"] = 1
        return counts

    EUC.measure = fake
    try:
        moved = refuse(os.path.join(SCRATCH, "patched.txt"), b"clean\n")
    finally:
        EUC.measure = saved
    ok = check(moved is not None and moved.code == EUC.E_CRLF,
               "AC-EUC1 a patched measuring law moves the verdict, so the"
               " guard asks it at CALL time") and ok
    ok = check(not os.path.exists(os.path.join(SCRATCH, "patched.txt")),
               "AC-EUC1 the patched refusal wrote nothing") and ok
    missing = refuse(os.path.join(SCRATCH, "nope", "x.txt"), GOOD)
    ok = check(missing is not None and missing.code == EUC.E_BADDIR,
               "AC-EUC1 a missing directory refuses before any byte (%r)"
               % (None if missing is None else missing.code,)) and ok
    return ok


def ac_euc2():
    """AC-EUC2: utf-8 LF-only bytes land unchanged, proved byte for byte."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    report = EUC.capture(path, GOOD)
    ok = check(report["bytes"] == len(GOOD),
               "AC-EUC2 the landed byte count is the input count (%d)"
               % (report["bytes"],)) and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-EUC2 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    ok = check(report["crlf"] == 0 and report["lone_cr"] == 0
               and report["utf8"] is True,
               "AC-EUC2 the counters read clean (crlf=%d lone_cr=%d utf8=%s)"
               % (report["crlf"], report["lone_cr"], report["utf8"])) and ok
    ok = check(EUC.refusal_of(GOOD) is None,
               "AC-EUC2 the direct reading agrees no refusal is owed") and ok
    text_path = os.path.join(SCRATCH, "text.txt")
    text = u"line\n\u4e2d\u6587\n"
    report_text = EUC.capture(text_path, text)
    ok = check(read_bytes(text_path) == text.encode("utf-8"),
               "AC-EUC2 text input lands as its utf-8 encoding (%d bytes)"
               % (report_text["bytes"],)) and ok
    ok = check(CJK in read_bytes(path),
               "AC-EUC2 the non-ASCII fixture really is non-ASCII") and ok
    return ok


def ac_euc3():
    """AC-EUC3: CRLF and lone CR refused with their own code and counters."""
    ok = True
    cases = ((CRLF_FIXTURE, EUC.E_CRLF, "crlf", 2, "crlf.txt"),
             (LONE_CR_FIXTURE, EUC.E_LONE_CR, "lone_cr", 1, "lone.txt"))
    for fixture, code, key, want, name in cases:
        path = os.path.join(SCRATCH, name)
        err = refuse(path, fixture)
        ok = check(err is not None and err.code == code,
                   "AC-EUC3 %r is refused as %s (got %r)"
                   % (key, code, None if err is None else err.code)) and ok
        ok = check(err is not None and err.counters.get(key) == want,
                   "AC-EUC3 the %s count is measured as %d (got %r)"
                   % (key, want, None if err is None
                      else err.counters.get(key))) and ok
        line = "" if err is None else EUC.refusal_line(err)
        ok = check(("%s=%d" % (key, want)) in line,
                   "AC-EUC3 the refusal line prints %s=%d (%r)"
                   % (key, want, sanitise(line))) and ok
        ok = check(not os.path.exists(path),
                   "AC-EUC3 the refused %r wrote NO file" % (key,)) and ok
    ok = check(EUC.refusal_of(CRLF_FIXTURE)["code"] == EUC.E_CRLF
               and EUC.refusal_of(LONE_CR_FIXTURE)["code"] == EUC.E_LONE_CR,
               "AC-EUC3 the two newline laws are separate codes") and ok
    return ok


def ac_euc4():
    """AC-EUC4: non-utf-8 refused by a different code naming the offset."""
    ok = True
    path = os.path.join(SCRATCH, "badutf8.txt")
    err = refuse(path, BAD_UTF8)
    ok = check(err is not None and err.code == EUC.E_NOT_UTF8,
               "AC-EUC4 non-utf-8 bytes are refused as %s (got %r)"
               % (EUC.E_NOT_UTF8, None if err is None else err.code)) and ok
    ok = check(err is not None and err.counters.get("bad_offset") == 2,
               "AC-EUC4 the first offending offset is named (got %r)"
               % (None if err is None else err.counters.get("bad_offset"),)
               ) and ok
    ok = check(EUC.E_NOT_UTF8 != EUC.E_CRLF
               and EUC.E_NOT_UTF8 != EUC.E_LONE_CR,
               "AC-EUC4 the decode code is distinct from both newline codes"
               ) and ok
    line = "" if err is None else EUC.refusal_line(err)
    ok = check("offset=2" in line,
               "AC-EUC4 the refusal line prints offset=2 (%r)"
               % (sanitise(line),)) and ok
    ok = check(not os.path.exists(path),
               "AC-EUC4 the refused capture wrote NO file") and ok
    ok = check(EUC.measure(BAD_UTF8)["utf8"] is False,
               "AC-EUC4 the raw measurement agrees the bytes do not decode"
               ) and ok
    return ok


def ac_euc5():
    """AC-EUC5: never rewrites; live leg measuring the same fixture on BOTH."""
    ok = True
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, CRLF_FIXTURE)
    ok = check(not os.path.exists(absent),
               "AC-EUC5 a refused capture leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == EUC.E_EXISTS,
               "AC-EUC5 an existing target is refused as %s (got %r)"
               % (EUC.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-EUC5 the existing target is byte-identical after the"
               " refusal (%s)" % (before,)) and ok
    shipped_text = EC._flat(CRLF_FIXTURE.decode("utf-8"))
    shipped_raw = shipped_text.encode("utf-8")
    ok = check(shipped_raw != CRLF_FIXTURE and b"\r" not in shipped_raw,
               "AC-EUC5 the SHIPPED normaliser REWRITES the same bytes"
               " (%d -> %d)" % (len(CRLF_FIXTURE), len(shipped_raw))) and ok
    ok = check(EUC.refusal_of(CRLF_FIXTURE) is not None,
               "AC-EUC5 this guard REFUSES them instead of rewriting") and ok
    shipped_bad = BAD_UTF8.decode("utf-8", "replace")
    ok = check(u"\ufffd" in shipped_bad,
               "AC-EUC5 the shipped decode replaces the bad byte and loses"
               " the offset (%r)" % (shown(shipped_bad),)) and ok
    ok = check(EUC.measure(BAD_UTF8)["bad_offset"] == 2,
               "AC-EUC5 this guard names the offset the shipped decode loses"
               ) and ok
    real = os.path.join(SRC, "..", "qa", "write-sensitive-R2713.log")
    if os.path.isfile(real):
        raw = read_bytes(real)
        digest_before = EUC.digest(raw)
        ok = check(EUC.refusal_of(raw) is None,
                   "AC-EUC5 the real committed evidence passes this guard"
                   " (%d bytes)" % (len(raw),)) and ok
        normalised = EC._flat(raw.decode("utf-8", "replace")).encode("utf-8")
        ok = check(normalised == raw,
                   "AC-EUC5 the same real bytes read identically on BOTH"
                   " readers") and ok
        ok = check(EUC.digest(read_bytes(real)) == digest_before,
                   "AC-EUC5 the live leg wrote nothing to the real file"
                   " (%s)" % (digest_before,)) and ok
    else:
        ok = check(False, "AC-EUC5 the real evidence fixture is missing") and ok
    return ok


def ac_euc6():
    """AC-EUC6: hygiene - ASCII, stdlib only, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-EUC6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-EUC6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "hashlib", "json", "os", "sys")
    ok = check(all(line.split()[1].split(".")[0] in allowed
                   for line in imports),
               "AC-EUC6 every import is stdlib (%s)" % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-EUC6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-EUC6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-EUC6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-EUC6 six criteria are declared") and ok
    ok = check(EUC.LABEL == "os-evidence-utf8-capture",
               "AC-EUC6 the face carries its own reconcile label (%r)"
               % (EUC.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_euc1, ac_euc2, ac_euc3, ac_euc4, ac_euc5, ac_euc6]
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
