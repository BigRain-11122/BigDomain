"""AC-ECMP1..AC-ECMP6 suite for the compound refusal report (R2720).

Criteria were pinned in state/queue/tech.md:693 at R2718 BEFORE this code
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

import evidence_capture_compound_refusal as ECR  # noqa
import evidence_capture_tail_guard as ETG  # noqa
import evidence_utf8_capture as EUC  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_capture_compound_refusal.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-capture-compound-refusal",'
WIRED_SUITE = '"test_evidence_capture_compound_refusal.py"'
TAIL_LABEL = '"os-evidence-capture-tail-guard",'

SCRATCH = os.path.join(SRC, "..", "tmp", "ecmp-R2720-%d" % os.getpid())

BOM = b"\xef\xbb\xbf"
CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK
NUL_TAIL = b"a\x00b"
BOM_TAIL = BOM + b"abc"
BOM_NUL_TAIL = BOM + b"a\x00b"
CRLF_NUL = b"a\r\n\x00\n"
CRLF_FIXTURE = b"alpha\r\nbeta\r\n"
LONE_CR_FIXTURE = b"alpha\rbeta"
BAD_UTF8 = b"ok\xffbad"
TAIL_FIXTURE = b"alpha\nunterminated"
NUL_FIXTURE = b"a\x00b\x00\n"
SENTINEL = b"keep me\n"

REAL_EVIDENCE = os.path.join(SRC, "..", "qa", "write-sensitive-R2719.log")
FALLBACK_EVIDENCE = os.path.join(SRC, "..", "qa",
                                 "reconcile-all-R2719.log")


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
    return text.replace(SCRATCH, "<scratch>")


def refuse(target, data):
    try:
        ECR.capture(target, data)
    except ECR.Refused as err:
        return err
    return None


def real_evidence():
    for path in (REAL_EVIDENCE, FALLBACK_EVIDENCE):
        if os.path.isfile(path):
            return path
    return None


def ac_ecmp1():
    """AC-ECMP1: every earned shape is reported with its own counter."""
    ok = True
    cases = ((NUL_TAIL, ["nul", "tail"], "nul+tail"),
             (BOM_TAIL, ["bom", "tail"], "bom+tail"),
             (BOM_NUL_TAIL, ["bom", "nul", "tail"], "bom+nul+tail"),
             (CRLF_NUL, ["nul", "crlf"], "crlf+nul"))
    for raw, want, name in cases:
        report = ECR.report_of(raw)
        ok = check(report is not None and report["shapes"] == want,
                   "AC-ECMP1 %s reports EVERY shape %s (got %r)"
                   % (name, want, None if report is None
                      else report["shapes"])) and ok
        ok = check(report is not None
                   and len(report["shape_codes"]) == len(want),
                   "AC-ECMP1 %s names one code per shape" % (name,)) and ok
        line = "" if report is None else ECR.report_line(report)
        ok = check(report is not None
                   and ("shapes=" + ",".join(want)) in line,
                   "AC-ECMP1 %s prints its shapes on one ASCII line (%r)"
                   % (name, sanitise(line))) and ok
    path = os.path.join(SCRATCH, "nul-tail.txt")
    err = refuse(path, NUL_TAIL)
    ok = check(err is not None and err.shapes == ["nul", "tail"],
               "AC-ECMP1 capture() refuses with both shapes (%r)"
               % (None if err is None else err.shapes,)) and ok
    ok = check(not os.path.exists(path),
               "AC-ECMP1 the compound refusal wrote NO file") and ok
    ok = check(err is not None and "shapes=nul,tail" in ECR.refusal_line(err),
               "AC-ECMP1 the refusal line names both shapes") and ok
    return ok


def ac_ecmp2():
    """AC-ECMP2: every single-defect answer stays byte for byte shipped."""
    ok = True
    cases = ((CRLF_FIXTURE, "E_EUC_CRLF", "crlf", 2),
             (LONE_CR_FIXTURE, "E_EUC_LONE_CR", "lone_cr", 1),
             (BAD_UTF8, "E_EUC_NOT_UTF8", "bad_offset", 2),
             (BOM_TAIL, "E_EBOM_BOM", "bytes", 6),
             (NUL_FIXTURE, "E_EBOM_NUL", "nul", 2),
             (TAIL_FIXTURE, "E_ETAIL_TAIL", "bytes", 18))
    for raw, code, key, want in cases:
        shipped = ETG.refusal_of(raw)
        report = ECR.report_of(raw)
        ok = check(shipped is not None and report is not None
                   and report["code"] == shipped["code"] == code,
                   "AC-ECMP2 first code stays %s exactly as shipped (got %r/%r)"
                   % (code, None if report is None else report["code"],
                      None if shipped is None else shipped["code"])) and ok
        ok = check(report is not None
                   and report["counters"].get(key) == want,
                   "AC-ECMP2 the %s counter still reads %d (got %r)"
                   % (key, want, None if report is None
                      else report["counters"].get(key))) and ok
    ok = check(ECR.report_of(GOOD) is None
               and ETG.refusal_of(GOOD) is None,
               "AC-ECMP2 a clean payload is accepted by both readings") and ok
    ok = check(ECR.first_code(GOOD) is None,
               "AC-ECMP2 the shipped first code is asked at CALL time") and ok
    return ok


def ac_ecmp3():
    """AC-ECMP3: clean payload and real evidence ACCEPT, digests unchanged."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    landed = ECR.capture(path, GOOD)
    ok = check(landed["verdict"] == "LANDED" and landed["shapes"] == [],
               "AC-ECMP3 a clean payload lands with shapes=none") and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-ECMP3 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    real = real_evidence()
    if real is not None:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        ok = check(ECR.report_of(raw) is None,
                   "AC-ECMP3 the real evidence reads ACCEPT (%s, %d bytes)"
                   % (os.path.basename(real), len(raw))) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-ECMP3 the live read changed no real byte (%s)"
                   % (before,)) and ok
    else:
        ok = check(False, "AC-ECMP3 a real evidence fixture is missing") and ok
    empty = os.path.join(SCRATCH, "empty.txt")
    report = ECR.capture(empty, b"")
    ok = check(report["verdict"] == "LANDED" and report["bytes"] == 0,
               "AC-ECMP3 the zero-byte payload still lands empty") and ok
    return ok


def ac_ecmp4():
    """AC-ECMP4: ASCII, deterministic order, refusal leaves target intact."""
    ok = True
    text = ECR.report_line(ECR.report_of(BOM_NUL_TAIL))
    ok = check(all(ord(ch) < 128 for ch in text),
               "AC-ECMP4 the report line is pure ASCII (%r)"
               % (sanitise(text),)) and ok
    orders = [tuple(ECR.shapes_of(raw)) for raw in
              (BOM_NUL_TAIL, BOM_NUL_TAIL, NUL_TAIL, CRLF_NUL)]
    ok = check(orders[0] == orders[1],
               "AC-ECMP4 the same payload reads the same shapes twice (%r)"
               % (orders[0],)) and ok
    ok = check(list(orders[0]) == [n for n in ECR.ORDER if n in orders[0]],
               "AC-ECMP4 the order follows the published precedence (%r)"
               % (list(orders[0]),)) and ok
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, BOM_NUL_TAIL)
    ok = check(not os.path.exists(absent),
               "AC-ECMP4 a compound refusal leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == ECR.E_EXISTS,
               "AC-ECMP4 an existing target is refused as %s (got %r)"
               % (ECR.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-ECMP4 the existing target is byte-identical (%s)"
               % (before,)) and ok
    return ok


def ac_ecmp5():
    """AC-ECMP5: the zero-byte ACCEPT decision from AC-ETAIL5 rides unchanged."""
    ok = True
    ok = check(ECR.report_of(b"") is None,
               "AC-ECMP5 the empty payload earns no shape") and ok
    ok = check(ECR.shapes_of(b"") == [],
               "AC-ECMP5 the shape list for empty bytes is empty") and ok
    path = os.path.join(SCRATCH, "empty5.txt")
    report = ECR.capture(path, b"")
    ok = check(os.path.isfile(path) and read_bytes(path) == b"",
               "AC-ECMP5 the empty file really exists and is empty") and ok
    ok = check(report["bytes"] == 0 and report["verdict"] == "LANDED",
               "AC-ECMP5 the landing report names bytes=0 LANDED") and ok
    ok = check(ETG.refusal_of(b"") is None,
               "AC-ECMP5 the shipped tail guard agrees about the same bytes"
               ) and ok
    return ok


def ac_ecmp6():
    """AC-ECMP6: hygiene - ASCII, stdlib only, registered, with its suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-ECMP6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-ECMP6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "json", "os", "sys", "evidence_capture_tail_guard",
               "evidence_utf8_capture")
    ok = check(all(line.split()[1].split(".")[0] in allowed
                   for line in imports),
               "AC-ECMP6 every import is stdlib or a shipped face (%s)"
               % (imports,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-ECMP6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-ECMP6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(TAIL_LABEL) == 1,
               "AC-ECMP6 the shipped tail-guard row is untouched (%d)"
               % (registry.count(TAIL_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-ECMP6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-ECMP6 six criteria are declared") and ok
    ok = check(ECR.LABEL == "os-evidence-capture-compound-refusal",
               "AC-ECMP6 the face carries its own reconcile label (%r)"
               % (ECR.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_ecmp1, ac_ecmp2, ac_ecmp3, ac_ecmp4, ac_ecmp5, ac_ecmp6]
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
