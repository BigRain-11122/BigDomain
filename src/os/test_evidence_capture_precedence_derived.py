"""AC-ECORD1..AC-ECORD6 suite for the derived precedence face (R2723).

Criteria were pinned in state/queue/tech.md:694 at R2720 BEFORE this code
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
import evidence_capture_precedence_derived as EPD  # noqa
import evidence_capture_tail_guard as ETG  # noqa
import evidence_utf8_capture as EUC  # noqa
import evidence_utf8_capture_bom_guard as EBG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_capture_precedence_derived.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-capture-precedence-derived",'
WIRED_SUITE = '"test_evidence_capture_precedence_derived.py"'
COMPOUND_LABEL = '"os-evidence-capture-compound-refusal",'

SCRATCH = os.path.join(SRC, "..", "tmp", "ecord-R2723-%d" % os.getpid())

BOM = b"\xef\xbb\xbf"
CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK

# The four compound fixtures R2720 measured, byte for byte.
R2720_FIXTURES = (b"a\x00b", BOM + b"abc", BOM + b"a\x00b", b"a\r\n\x00\n")

# The single-defect fixtures the three shipped faces pin.
SHIPPED_FIXTURES = (b"alpha\r\nbeta\r\n", b"alpha\rbeta", b"ok\xffbad",
                    b"a\x00b\x00\n",
                    b"alpha\nunterminated")

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


def sanitise(text):
    return text.replace(SCRATCH, "<scratch>")


def refuse(target, data):
    try:
        EPD.capture(target, data)
    except EPD.Refused as err:
        return err
    return None


def real_evidence():
    for name in ("write-sensitive-R2722.log", "write-sensitive-R2719.log",
                 "reconcile-all-R2721.log"):
        path = os.path.join(SRC, "..", "qa", name)
        if os.path.isfile(path):
            return path
    return None


def patched_shipped_law():
    """Return a patched BOM-guard refusal law that checks NUL before BOM."""
    original = EBG.refusal_of

    def patched(data):
        raw = EUC.as_bytes(data)
        counts = EUC.measure(raw)
        reading = EBG.eol_reading(raw)
        if counts["nul"]:
            return {"code": EBG.E_NUL, "counters": counts, "eol": reading}
        if reading["bom"]:
            return {"code": EBG.E_BOM, "counters": counts, "eol": reading}
        base = EUC.refusal_of(raw)
        if base is not None:
            return {"code": base["code"], "counters": base["counters"],
                    "eol": reading}
        return None

    return original, patched


def ac_ecord1():
    """AC-ECORD1: the order is derived at CALL time; a patch MOVES it."""
    ok = True
    plain = EPD.order()
    ok = check(plain == EPD.order(),
               "AC-ECORD1 the same chain derives the same order twice (%r)"
               % (plain,)) and ok
    original, patched = patched_shipped_law()
    EBG.refusal_of = patched
    try:
        moved = EPD.order()
    finally:
        EBG.refusal_of = original
    ok = check(moved != plain,
               "AC-ECORD1 a patched shipped law MOVES the derived order "
               "(%r -> %r)" % (plain, moved)) and ok
    ok = check(moved.index("nul") < moved.index("bom"),
               "AC-ECORD1 the patched law puts nul before bom (%r)"
               % (moved,)) and ok
    ok = check(EPD.order() == plain,
               "AC-ECORD1 restoring the shipped law restores the order") and ok
    ok = not hasattr(EPD, "ORDER")
    ok = check(ok, "AC-ECORD1 no constant ORDER attribute exists on the face"
               ) and ok
    return ok


def ac_ecord2():
    """AC-ECORD2: the derived order agrees with the shipped first code."""
    ok = True
    derived = EPD.order()
    for raw in R2720_FIXTURES + SHIPPED_FIXTURES:
        report = EPD.report_of(raw)
        shipped = ETG.refusal_of(raw)
        ok = check(report is not None and shipped is not None
                   and report["shapes"][0] is not None
                   and EPD.CODES[report["shapes"][0]] == shipped["code"],
                   "AC-ECORD2 %r first named shape maps to the shipped code "
                   "%r (%r)" % (raw[:12], None if shipped is None
                                else shipped["code"],
                                None if report is None else report["shapes"])
                   ) and ok
    for pair, seed in EPD.SEEDS.items():
        shipped = ETG.refusal_of(seed)
        report = EPD.report_of(seed)
        ok = check(report is not None and shipped is not None
                   and report["shapes"] == [name for name in derived
                                            if name in set(pair)],
                   "AC-ECORD2 seed %s,%s reads in derived order (%r)"
                   % (pair[0], pair[1],
                      None if report is None else report["shapes"])) and ok
    ok = check(EPD.report_of(GOOD) is None,
               "AC-ECORD2 a clean payload names no shape") and ok
    return ok


def ac_ecord3():
    """AC-ECORD3: every published answer stays byte for byte what R2720 said."""
    ok = True
    fixtures = R2720_FIXTURES + SHIPPED_FIXTURES + tuple(EPD.SEEDS.values())
    for raw in fixtures:
        mine = EPD.report_of(raw)
        theirs = ECR.report_of(raw)
        ok = check(mine == theirs,
                   "AC-ECORD3 %r publishes the R2720 answer (%r)"
                   % (raw[:12], None if theirs is None else theirs["shapes"])
                   ) and ok
        if mine is not None and theirs is not None:
            ok = check(EPD.report_line(mine) == ECR.report_line(theirs),
                       "AC-ECORD3 %r report line is byte-identical"
                       % (raw[:12],)) and ok
    return ok


def ac_ecord4():
    """AC-ECORD4: accepts unchanged, refusal leaves no byte behind."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    landed = EPD.capture(path, GOOD)
    ok = check(landed["verdict"] == "LANDED" and landed["shapes"] == [],
               "AC-ECORD4 a clean payload lands with shapes=none") and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-ECORD4 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    empty = os.path.join(SCRATCH, "empty.txt")
    report = EPD.capture(empty, b"")
    ok = check(report["bytes"] == 0 and read_bytes(empty) == b"",
               "AC-ECORD4 the zero-byte payload still lands empty") and ok
    real = real_evidence()
    if real is None:
        ok = check(False, "AC-ECORD4 a real evidence fixture is missing") and ok
    else:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        ok = check(EPD.report_of(raw) is None,
                   "AC-ECORD4 the real evidence reads ACCEPT (%s, %d bytes)"
                   % (os.path.basename(real), len(raw))) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-ECORD4 the live read changed no real byte (%s)"
                   % (before,)) and ok
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, BOM + b"a\x00b")
    ok = check(not os.path.exists(absent),
               "AC-ECORD4 a refusal leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == EPD.E_EXISTS,
               "AC-ECORD4 an existing target is refused as %s (got %r)"
               % (EPD.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-ECORD4 the existing target is byte-identical (%s)"
               % (before,)) and ok
    return ok


def ac_ecord5():
    """AC-ECORD5: the reading writes nothing, reads no clock, stays ASCII."""
    ok = True
    before = sorted(os.listdir(SCRATCH))
    lines = [EPD.report_line(EPD.report_of(raw)) for raw in R2720_FIXTURES]
    lines.append(EPD.order_line())
    after = sorted(os.listdir(SCRATCH))
    ok = check(before == after,
               "AC-ECORD5 the readings created no file (%d -> %d)"
               % (len(before), len(after))) and ok
    ok = check(all(all(ord(ch) < 128 for ch in line) for line in lines),
               "AC-ECORD5 every report line is pure ASCII") and ok
    text = read_bytes(MODULE).decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "time.time(", "time.monotonic(",
                                "datetime.now(", "utcnow(")
              if name in text]
    ok = check(not banned,
               "AC-ECORD5 the face reads no clock (%s)" % (banned,)) and ok
    writes = [name for name in ('open(', '"w"', "'w'", 'open(path, "wb")')
              if name in text and name.startswith(('"w"', "'w'"))]
    ok = check(not writes,
               "AC-ECORD5 the face opens no target for text writing (%s)"
               % (writes,)) and ok
    ok = check("ORDER derived=" in EPD.order_line(),
               "AC-ECORD5 the order line names the derivation (%r)"
               % (EPD.order_line(),)) and ok
    return ok


def ac_ecord6():
    """AC-ECORD6: hygiene - ASCII, stdlib only, own label and own suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-ECORD6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-ECORD6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "json", "os", "sys", "evidence_capture_tail_guard",
               "evidence_utf8_capture")
    bad = [line for line in imports
           if line.split()[1].split(".")[0] not in allowed]
    ok = check(not bad, "AC-ECORD6 every import is stdlib or a shipped face "
               "(%s)" % (bad,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-ECORD6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-ECORD6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(COMPOUND_LABEL) == 1,
               "AC-ECORD6 the shipped compound row is untouched (%d)"
               % (registry.count(COMPOUND_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-ECORD6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-ECORD6 six criteria are declared") and ok
    ok = check(EPD.LABEL == "os-evidence-capture-precedence-derived",
               "AC-ECORD6 the face carries its own reconcile label (%r)"
               % (EPD.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_ecord1, ac_ecord2, ac_ecord3, ac_ecord4, ac_ecord5,
              ac_ecord6]
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
