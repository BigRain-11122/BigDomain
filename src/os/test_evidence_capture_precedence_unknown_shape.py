"""AC-EPDU1..AC-EPDU6 suite for the unknown-shape refusal face (R2725).

Criteria were pinned in state/queue/tech.md:695 at R2723 BEFORE this code
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

import evidence_capture_precedence_derived as EPD  # noqa
import evidence_capture_precedence_unknown_shape as WSU  # noqa
import evidence_capture_tail_guard as ETG  # noqa
import evidence_utf8_capture as EUC  # noqa
import evidence_utf8_capture_bom_guard as EBG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_capture_precedence_unknown_shape.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-capture-precedence-unknown-shape",'
WIRED_SUITE = '"test_evidence_capture_precedence_unknown_shape.py"'
PREV_LABEL = '"os-evidence-capture-precedence-derived",'

SCRATCH = os.path.join(SRC, "..", "tmp", "epdu-R2725-%d" % os.getpid())

BOM = b"\xef\xbb\xbf"
UTF16_LE_BOM = b"\xff\xfe"
CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK

# A payload earning NONE of the six known shapes, which a patched shipped law
# nonetheless refuses: clean by every shipped counter, BOM marker mid-file.
SOLE = b"head" + BOM + b"mid\n"
# A payload earning nul, utf8 and tail at once, byte-order-marked UTF-16LE.
MIX = UTF16_LE_BOM + b"a\x00b"

# The four compound fixtures R2720 measured, byte for byte.
R2720_FIXTURES = (b"a\x00b", BOM + b"abc", BOM + b"a\x00b", b"a\r\n\x00\n")

# The single-defect fixtures the shipped faces pin.
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
    """Drop the per-leg pid from a path so two legs read the same line."""
    return text.replace(SCRATCH, "<scratch>")


def refuse(target, data):
    try:
        WSU.capture(target, data)
    except WSU.Refused as err:
        return err
    return None


def real_evidence():
    for name in ("write-sensitive-R2724.log", "reconcile-all-R2723.log",
                 "reconcile-all-R2721.log"):
        path = os.path.join(SRC, "..", "qa", name)
        if os.path.isfile(path):
            return path
    return None


def patched_code_law(code):
    """A patched BOM-guard law answering `code` for a byte-order-marked payload."""
    original = EBG.refusal_of

    def patched(data):
        raw = EUC.as_bytes(data)
        counts = EUC.measure(raw)
        reading = EBG.eol_reading(raw)
        if raw.startswith(UTF16_LE_BOM) or BOM in raw[len(BOM):]:
            return {"code": code, "counters": counts, "eol": reading}
        if reading["bom"]:
            return {"code": EBG.E_BOM, "counters": counts, "eol": reading}
        if counts["nul"]:
            return {"code": EBG.E_NUL, "counters": counts, "eol": reading}
        base = EUC.refusal_of(raw)
        if base is not None:
            return {"code": base["code"], "counters": base["counters"],
                    "eol": reading}
        return None

    return original, patched


def patched_order_law():
    """A patched BOM-guard law that checks NUL before BOM, moving the order."""
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


def ac_epdu1():
    """AC-EPDU1: an unknown first code is REFUSED naming it, never omitted."""
    ok = True
    original, patched = patched_code_law("E_EBOM_UTF16")
    EBG.refusal_of = patched
    try:
        report = WSU.report_of(MIX)
        theirs = EPD.report_of(MIX)
        ok = check(report is not None,
                   "AC-EPDU1 an unknown first code is never an ACCEPT (%r)"
                   % (report,)) and ok
        ok = check(report is not None and report["code"] == "E_EBOM_UTF16",
                   "AC-EPDU1 the refusal names the unknown code (%r)"
                   % (None if report is None else report["code"],)) and ok
        ok = check(report is not None
                   and "E_EBOM_UTF16" in report["shape_codes"],
                   "AC-EPDU1 no published list omits the unknown code (%r)"
                   % (None if report is None else report["shape_codes"],)) and ok
        ok = check(report is not None
                   and report["shapes"][0] == "E_EBOM_UTF16",
                   "AC-EPDU1 the unknown code stands FIRST in the list (%r)"
                   % (None if report is None else report["shapes"],)) and ok
        ok = check(theirs is not None
                   and "E_EBOM_UTF16" not in theirs["shape_codes"],
                   "AC-EPDU1 the R2723 face still omits it (%r)"
                   % (None if theirs is None else theirs["shape_codes"],)) and ok
        ok = check(theirs is not None
                   and EPD.CODES[theirs["shapes"][0]] != theirs["code"],
                   "AC-EPDU1 the R2723 first shape still disagrees (%r vs %r)"
                   % (None if theirs is None else EPD.CODES[theirs["shapes"][0]],
                      None if theirs is None else theirs["code"])) and ok
        absent = os.path.join(SCRATCH, "unknown.txt")
        err = refuse(absent, MIX)
        ok = check(err is not None and err.code == "E_EBOM_UTF16",
                   "AC-EPDU1 capture refuses with that code (%r)"
                   % (None if err is None else err.code,)) and ok
        ok = check(not os.path.exists(absent),
                   "AC-EPDU1 the refused target is absent") and ok
        ok = check(err is not None and "E_EBOM_UTF16" in WSU.refusal_line(err),
                   "AC-EPDU1 the refusal line names the code (%r)"
                   % (None if err is None
                      else sanitise(WSU.refusal_line(err)),)) and ok
    finally:
        EBG.refusal_of = original
    return ok


def ac_epdu2():
    """AC-EPDU2: a payload earning ONLY the unknown shape is refused too."""
    ok = True
    plain = WSU.report_of(SOLE)
    ok = check(plain is None and ETG.refusal_of(SOLE) is None,
               "AC-EPDU2 the shipped tree accepts the sole fixture (%r)"
               % (plain,)) and ok
    original, patched = patched_code_law("E_EBOM_UTF16")
    EBG.refusal_of = patched
    try:
        chain = ETG.refusal_of(SOLE)
        theirs = EPD.report_of(SOLE)
        mine = WSU.report_of(SOLE)
        ok = check(chain is not None and chain["code"] == "E_EBOM_UTF16",
                   "AC-EPDU2 the patched chain refuses it (%r)"
                   % (None if chain is None else chain["code"],)) and ok
        ok = check(theirs is None,
                   "AC-EPDU2 the R2723 face reads ACCEPT on it (%r)"
                   % (theirs,)) and ok
        ok = check(mine is not None and mine["code"] == "E_EBOM_UTF16",
                   "AC-EPDU2 this face refuses it naming the code (%r)"
                   % (None if mine is None else mine["code"],)) and ok
        ok = check(mine is not None and mine["shapes"] == ["E_EBOM_UTF16"],
                   "AC-EPDU2 the sole shape is named alone (%r)"
                   % (None if mine is None else mine["shapes"],)) and ok
        absent = os.path.join(SCRATCH, "sole.txt")
        err = refuse(absent, SOLE)
        ok = check(err is not None and err.code == "E_EBOM_UTF16"
                   and not os.path.exists(absent),
                   "AC-EPDU2 capture refuses and lands nothing (%r)"
                   % (None if err is None else err.code,)) and ok
        ok = check(mine is not None
                   and WSU.report_line(mine) == EPD.report_line(mine),
                   "AC-EPDU2 the sole report line uses the shipped format") and ok
    finally:
        EBG.refusal_of = original
    return ok


def ac_epdu3():
    """AC-EPDU3: every answer the six known shapes publish stays byte for byte."""
    ok = True
    fixtures = (R2720_FIXTURES + SHIPPED_FIXTURES
                + tuple(EPD.SEEDS.values()))
    for raw in fixtures:
        mine = WSU.report_of(raw)
        theirs = EPD.report_of(raw)
        ok = check(mine == theirs,
                   "AC-EPDU3 %r publishes the R2723 answer (%r)"
                   % (raw[:12], None if theirs is None else theirs["shapes"])
                   ) and ok
        if mine is not None and theirs is not None:
            ok = check(WSU.report_line(mine) == EPD.report_line(theirs),
                       "AC-EPDU3 %r report line is byte-identical"
                       % (raw[:12],)) and ok
    ok = check(WSU.order_line() == EPD.order_line(),
               "AC-EPDU3 the order line is byte-identical (%r)"
               % (WSU.order_line(),)) and ok
    ok = check(WSU.known_codes() == frozenset(EPD.CODES.values()),
               "AC-EPDU3 the known code set is the shipped six (%d)"
               % (len(WSU.known_codes()),)) and ok
    return ok


def ac_epdu4():
    """AC-EPDU4: accepts unchanged, refusal leaves no byte behind."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    landed = WSU.capture(path, GOOD)
    ok = check(landed["verdict"] == "LANDED" and landed["shapes"] == [],
               "AC-EPDU4 a clean payload lands with shapes=none") and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-EPDU4 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    empty = os.path.join(SCRATCH, "empty.txt")
    report = WSU.capture(empty, b"")
    ok = check(report["bytes"] == 0 and read_bytes(empty) == b"",
               "AC-EPDU4 the zero-byte payload still lands empty") and ok
    real = real_evidence()
    if real is None:
        ok = check(False, "AC-EPDU4 a real evidence fixture is missing") and ok
    else:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        ok = check(WSU.report_of(raw) is None,
                   "AC-EPDU4 the real evidence reads ACCEPT (%s, %d bytes)"
                   % (os.path.basename(real), len(raw))) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-EPDU4 the live read changed no real byte (%s)"
                   % (before,)) and ok
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, BOM + b"a\x00b")
    ok = check(not os.path.exists(absent),
               "AC-EPDU4 a known-shape refusal leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == WSU.E_EXISTS,
               "AC-EPDU4 an existing target is refused as %s (got %r)"
               % (WSU.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-EPDU4 the existing target is byte-identical (%s)"
               % (before,)) and ok
    return ok


def ac_epdu5():
    """AC-EPDU5: order and unknown answer are both read at CALL time."""
    ok = True
    plain_order = EPD.order()
    ok = check(WSU.order_line() == EPD.order_line(),
               "AC-EPDU5 the face reads the order from the chain at call time"
               ) and ok
    original, patched = patched_order_law()
    EBG.refusal_of = patched
    try:
        moved = EPD.order()
        ok = check(moved != plain_order and WSU.order_line() == EPD.order_line(),
                   "AC-EPDU5 a reordered shipped law MOVES this face order "
                   "(%r -> %r)" % (plain_order, moved)) and ok
        ok = check(moved.index("nul") < moved.index("bom"),
                   "AC-EPDU5 the patched law puts nul before bom (%r)"
                   % (moved,)) and ok
    finally:
        EBG.refusal_of = original
    ok = check(EPD.order() == plain_order,
               "AC-EPDU5 restoring the shipped law restores the order") and ok
    original, patched = patched_code_law("E_EBOM_UTF16")
    EBG.refusal_of = patched
    try:
        first = WSU.report_of(SOLE)
    finally:
        EBG.refusal_of = original
    original, patched = patched_code_law("E_EBOM_UTF32")
    EBG.refusal_of = patched
    try:
        second = WSU.report_of(SOLE)
    finally:
        EBG.refusal_of = original
    ok = check(first is not None and second is not None
               and first["code"] == "E_EBOM_UTF16"
               and second["code"] == "E_EBOM_UTF32",
               "AC-EPDU5 a different patched code MOVES the unknown answer "
               "(%r -> %r)" % (None if first is None else first["code"],
                               None if second is None else second["code"])) and ok
    ok = not hasattr(WSU, "ORDER") and not hasattr(WSU, "UNKNOWN")
    ok = check(ok, "AC-EPDU5 no cached order or unknown-code attribute exists") and ok
    return ok


def ac_epdu6():
    """AC-EPDU6: hygiene - ASCII, stdlib only, own label and own suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-EPDU6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-EPDU6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    imports = [line for line in text.splitlines()
               if line.startswith("import ") or line.startswith("from ")]
    allowed = ("argparse", "json", "os", "sys",
               "evidence_capture_precedence_derived",
               "evidence_capture_tail_guard", "evidence_utf8_capture")
    bad = [line for line in imports
           if line.split()[1].split(".")[0] not in allowed]
    ok = check(not bad, "AC-EPDU6 every import is stdlib or a shipped face "
               "(%s)" % (bad,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-EPDU6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-EPDU6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(PREV_LABEL) == 1,
               "AC-EPDU6 the shipped derived row is untouched (%d)"
               % (registry.count(PREV_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-EPDU6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-EPDU6 six criteria are declared") and ok
    ok = check(WSU.LABEL == "os-evidence-capture-precedence-unknown-shape",
               "AC-EPDU6 the face carries its own reconcile label (%r)"
               % (WSU.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_epdu1, ac_epdu2, ac_epdu3, ac_epdu4, ac_epdu5, ac_epdu6]
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
