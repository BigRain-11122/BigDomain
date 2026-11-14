"""AC-ETAIL1..AC-ETAIL6 suite for the evidence tail guard (R2718).

Criteria were pinned in state/queue/tech.md:692 at R2716 BEFORE this code
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

import evidence_capture_tail_guard as ETG  # noqa
import evidence_utf8_capture_bom_guard as EBG  # noqa
import evidence_utf8_capture as EUC  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_capture_tail_guard.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-capture-tail-guard",'
WIRED_SUITE = '"test_evidence_capture_tail_guard.py"'
BASE_LABEL = '"os-evidence-utf8-capture",'
BOM_LABEL = '"os-evidence-utf8-capture-bom-guard",'

SCRATCH = os.path.join(SRC, "..", "tmp", "etail-R2718-%d" % os.getpid())

CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK
TAIL_FIXTURE = b"alpha\nunterminated"
BOM_FIXTURE = b"\xef\xbb\xbf" + b"alpha\n"
NUL_FIXTURE = b"a\x00b\x00\n"
CRLF_FIXTURE = b"alpha\r\nbeta\r\n"
LONE_CR_FIXTURE = b"alpha\rbeta"
BAD_UTF8 = b"ok\xffbad"
SENTINEL = b"keep me\n"

REAL_EVIDENCE = os.path.join(SRC, "..", "qa", "write-sensitive-R2717.log")
FALLBACK_EVIDENCE = os.path.join(SRC, "..", "qa",
                                 "reconcile-all-R2717.log")


def check(ok, label):
    print("%s %s" % ("PASS" if ok else "FAIL", label))
    return ok


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def write_bytes(path, raw):
    with open(path, "wb") as handle:
        handle.write(raw)


def sanitise(text):
    """The scratch path carries this run's pid; keep criterion lines stable."""
    return text.replace(SCRATCH, "<scratch>")


def refuse(target, data):
    """Return the refusal, or None when the capture was (wrongly) landed."""
    try:
        ETG.capture(target, data)
    except ETG.Refused as err:
        return err
    return None


def real_evidence():
    for path in (REAL_EVIDENCE, FALLBACK_EVIDENCE):
        if os.path.isfile(path):
            return path
    return None


def ac_etail1():
    """AC-ETAIL1: an unterminated tail is refused naming the form and counts."""
    ok = True
    path = os.path.join(SCRATCH, "tail.txt")
    err = refuse(path, TAIL_FIXTURE)
    ok = check(err is not None and err.code == ETG.E_TAIL,
               "AC-ETAIL1 an unterminated tail is refused as %s (got %r)"
               % (ETG.E_TAIL, None if err is None else err.code)) and ok
    ok = check(not os.path.exists(path),
               "AC-ETAIL1 the refused tail capture wrote NO file") and ok
    ok = check(err is not None and err.counters.get("bytes")
               == len(TAIL_FIXTURE),
               "AC-ETAIL1 the measured byte count is printed (%r)"
               % (None if err is None else err.counters.get("bytes"),)) and ok
    line = "" if err is None else ETG.refusal_line(err)
    ok = check("bytes=18" in line and "tail_last=0x64" in line,
               "AC-ETAIL1 the refusal line names the count and last byte (%r)"
               % (sanitise(line),)) and ok
    landed = 0
    for reader, name in ((EUC, "euc-tail.txt"), (EBG, "ebg-tail.txt")):
        try:
            reader.capture(os.path.join(SCRATCH, name), TAIL_FIXTURE)
            landed += 1
        except Exception:
            pass
    ok = check(landed == 2,
               "AC-ETAIL1 BOTH shipped readers still LAND the same bytes (%d/2)"
               % (landed,)) and ok
    ok = check(ETG.E_TAIL != EBG.E_BOM and ETG.E_TAIL != EBG.E_NUL,
               "AC-ETAIL1 the tail code is distinct from both BOM and NUL"
               ) and ok
    return ok


def ac_etail2():
    """AC-ETAIL2: an LF-terminated payload lands byte for byte as the pair does."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    report = ETG.capture(path, GOOD)
    ok = check(report["verdict"] == "LANDED" and report["tail_ok"] is True,
               "AC-ETAIL2 a clean payload reports LANDED with tail_ok=True"
               ) and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-ETAIL2 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    ok = check(report["sha256"] == EUC.digest(GOOD),
               "AC-ETAIL2 the digest equals the shipped law answer (%s)"
               % (report["sha256"],)) and ok
    single = os.path.join(SCRATCH, "single-lf.txt")
    ETG.capture(single, b"\n")
    ok = check(read_bytes(single) == b"\n",
               "AC-ETAIL2 a single-LF payload lands as its one byte") and ok
    two = os.path.join(SCRATCH, "two-line.txt")
    ETG.capture(two, b"alpha\nbeta\n")
    ok = check(read_bytes(two) == b"alpha\nbeta\n",
               "AC-ETAIL2 a two-line payload lands byte for byte") and ok
    ok = check(ETG.refusal_of(GOOD) is None,
               "AC-ETAIL2 the direct reading agrees no refusal is owed") and ok
    return ok


def ac_etail3():
    """AC-ETAIL3: every pinned reading rides unchanged; real evidence ACCEPTs
    on all three readers."""
    ok = True
    cases = ((CRLF_FIXTURE, EUC.E_CRLF, "crlf", 2, "crlf-keep.txt"),
             (LONE_CR_FIXTURE, EUC.E_LONE_CR, "lone_cr", 1, "lone-keep.txt"),
             (BAD_UTF8, EUC.E_NOT_UTF8, "bad_offset", 2, "bad-keep.txt"),
             (BOM_FIXTURE, EBG.E_BOM, "bytes", 9, "bom-keep.txt"),
             (NUL_FIXTURE, EBG.E_NUL, "nul", 2, "nul-keep.txt"))
    for fixture, code, key, want, name in cases:
        path = os.path.join(SCRATCH, name)
        err = refuse(path, fixture)
        ok = check(err is not None and err.code == code,
                   "AC-ETAIL3 %r still refuses as %s (got %r)"
                   % (key, code, None if err is None else err.code)) and ok
        ok = check(err is not None and err.counters.get(key) == want,
                   "AC-ETAIL3 its %s count still reads %d (got %r)"
                   % (key, want, None if err is None
                      else err.counters.get(key))) and ok
        ok = check(not os.path.exists(path),
                   "AC-ETAIL3 the refused %r wrote NO file" % (key,)) and ok
    real = real_evidence()
    if real is not None:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        readers = (("this face", ETG.refusal_of(raw)),
                   ("the BOM guard", EBG.refusal_of(raw)),
                   ("the shipped capture", EUC.refusal_of(raw)))
        for name, answer in readers:
            ok = check(answer is None,
                       "AC-ETAIL3 the real evidence reads ACCEPT on %s"
                       % (name,)) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-ETAIL3 the live read changed no real byte (%s)"
                   % (before,)) and ok
    else:
        ok = check(False, "AC-ETAIL3 a real evidence fixture is missing") and ok
    return ok


def ac_etail4():
    """AC-ETAIL4: a refusal leaves the target absent; existing target intact."""
    ok = True
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, TAIL_FIXTURE)
    ok = check(not os.path.exists(absent),
               "AC-ETAIL4 a refused tail leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == ETG.E_EXISTS,
               "AC-ETAIL4 an existing target is refused as %s (got %r)"
               % (ETG.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-ETAIL4 the existing target is byte-identical (%s)"
               % (before,)) and ok
    err = refuse(existing, TAIL_FIXTURE)
    ok = check(err is not None and err.code == ETG.E_EXISTS,
               "AC-ETAIL4 existence is asked BEFORE the tail shape") and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-ETAIL4 the second refusal left it byte-identical") and ok
    return ok


def ac_etail5():
    """AC-ETAIL5: a ZERO-byte payload is ACCEPTED and landed as an empty file."""
    ok = True
    path = os.path.join(SCRATCH, "empty.txt")
    report = ETG.capture(path, b"")
    ok = check(report["verdict"] == "LANDED" and report["bytes"] == 0,
               "AC-ETAIL5 the zero-byte payload reports LANDED bytes=0"
               ) and ok
    ok = check(os.path.isfile(path) and read_bytes(path) == b"",
               "AC-ETAIL5 the target exists on disk and is empty") and ok
    ok = check(ETG.refusal_of(b"") is None,
               "AC-ETAIL5 the direct reading accepts the empty payload") and ok
    ok = check(report["tail_ok"] is True,
               "AC-ETAIL5 the empty landing carries tail_ok=True") and ok
    ok = check(ETG.E_TAIL != ETG.E_EXISTS,
               "AC-ETAIL5 the tail code never doubles as the existence code"
               ) and ok
    return ok


def ac_etail6():
    """AC-ETAIL6: hygiene - ASCII, stdlib only, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-ETAIL6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-ETAIL6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "json", "os", "sys", "evidence_utf8_capture",
               "evidence_utf8_capture_bom_guard")
    ok = check(all(line.split()[1].split(".")[0] in allowed
                   for line in imports),
               "AC-ETAIL6 every import is stdlib or a shipped face (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-ETAIL6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-ETAIL6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(BASE_LABEL) == 1
               and registry.count(BOM_LABEL) == 1,
               "AC-ETAIL6 both shipped base rows are untouched (%d/%d)"
               % (registry.count(BASE_LABEL), registry.count(BOM_LABEL))) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-ETAIL6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-ETAIL6 six criteria are declared") and ok
    ok = check(ETG.LABEL == "os-evidence-capture-tail-guard",
               "AC-ETAIL6 the face carries its own reconcile label (%r)"
               % (ETG.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_etail1, ac_etail2, ac_etail3, ac_etail4, ac_etail5,
              ac_etail6]
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
