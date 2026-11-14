"""AC-EPTYP1..AC-EPTYP6 suite for the shape-typing face (R2730).

Criteria were pinned in state/queue/tech.md:697 at R2725 BEFORE this code
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
import evidence_capture_precedence_shape_typing as STP  # noqa
import evidence_capture_precedence_unknown_shape as WSU  # noqa
import evidence_capture_tail_guard as ETG  # noqa
import evidence_utf8_capture as EUC  # noqa
import evidence_utf8_capture_bom_guard as EBG  # noqa

EXPECTED_CRITERIA = 6
MODULE_NAME = "evidence_capture_precedence_shape_typing.py"
MODULE = os.path.join(BASE, MODULE_NAME)
SUITE = os.path.join(BASE, "test_" + MODULE_NAME)
REGISTRY = os.path.join(SANDBOX, "reconcile_all.py")
WIRED_LABEL = '"os-evidence-capture-precedence-shape-typing",'
WIRED_SUITE = '"test_evidence_capture_precedence_shape_typing.py"'
PREV_LABEL = '"os-evidence-capture-precedence-unknown-shape",'

SCRATCH = os.path.join(SRC, "..", "tmp", "epty-R2730-%d" % os.getpid())

BOM = b"\xef\xbb\xbf"
UTF16_LE_BOM = b"\xff\xfe"
CJK = u"\u8bc1\u636e\n".encode("utf-8")
GOOD = b"section one\nline two\n" + CJK

# A payload earning NONE of the six known shapes, which a patched law refuses.
SOLE = b"head" + BOM + b"mid\n"
# A payload earning nul, utf8 and tail at once, byte-order-marked UTF-16LE.
MIX = UTF16_LE_BOM + b"a\x00b"

R2720_FIXTURES = (b"a\x00b", BOM + b"abc", BOM + b"a\x00b", b"a\r\n\x00\n")

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
        STP.capture(target, data)
    except STP.Refused as err:
        return err
    return None


def real_evidence():
    for name in ("reconcile-all-R2725.log", "write-sensitive-R2729.log",
                 "reconcile-all-R2723.log"):
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


def falsifiable_fixtures():
    """Every payload this suite can put in front of the face, both laws."""
    return (R2720_FIXTURES + SHIPPED_FIXTURES + tuple(EPD.SEEDS.values())
            + (MIX, SOLE, b"", GOOD, SENTINEL))


def sweep(label, patched):
    """Ask the face every falsifiable fixture under one law, one line each."""
    ok = True
    original = EBG.refusal_of
    EBG.refusal_of = patched
    try:
        table = STP.name_table()
        for raw in falsifiable_fixtures():
            report = STP.report_of(raw)
            if report is None:
                ok = check(True, "AC-EPTYP1 %s %r reads ACCEPT"
                           % (label, raw[:10])) and ok
                continue
            names = report["shapes"]
            ok = check(all(name in table for name in names),
                       "AC-EPTYP1 %s %r shapes are name-table keys (%r)"
                       % (label, raw[:10], names)) and ok
            ok = check(report["shape_codes"]
                       == [table[name] for name in names],
                       "AC-EPTYP1 %s %r shape_codes align 1:1 with names"
                       % (label, raw[:10])) and ok
            if names:
                try:
                    first = table[names[0]]
                except KeyError as err:
                    first = "KeyError(%s)" % (err,)
                ok = check(isinstance(first, str),
                           "AC-EPTYP1 %s %r CODES[shapes[0]] never raises (%r)"
                           % (label, raw[:10], first)) and ok
            else:
                ok = check(report.get("unknown_code") == report["code"],
                           "AC-EPTYP1 %s %r an empty list names the code in "
                           "its own field (%r)"
                           % (label, raw[:10],
                              report.get("unknown_code"))) and ok
    finally:
        EBG.refusal_of = original
    return ok


def ac_eptyp1():
    """AC-EPTYP1: every shape entry is a name, and CODES[shapes[0]] never raises."""
    original, patched = patched_code_law("E_EBOM_UTF16")
    ok = sweep("patched", patched)
    ok = sweep("shipped", original) and ok
    return ok


def ac_eptyp2():
    """AC-EPTYP2: the unknown code is refused, named and never a shape entry."""
    ok = True
    original, patched = patched_code_law("E_EBOM_UTF16")
    EBG.refusal_of = patched
    try:
        caught = False
        try:
            EPD.CODES[WSU.report_of(MIX)["shapes"][0]]
        except KeyError:
            caught = True
        ok = check(caught,
                   "AC-EPTYP2 the R2725 list still breaks a names-only consumer"
                   ) and ok
        report = STP.report_of(MIX)
        ok = check(report is not None and report["code"] == "E_EBOM_UTF16",
                   "AC-EPTYP2 the code is still refused and still named (%r)"
                   % (None if report is None else report["code"],)) and ok
        ok = check(report is not None
                   and report.get("unknown_code") == "E_EBOM_UTF16",
                   "AC-EPTYP2 the unknown code sits in its own field (%r)"
                   % (None if report is None else report.get("unknown_code"),)
                   ) and ok
        ok = check(report is not None
                   and "E_EBOM_UTF16" not in report["shapes"],
                   "AC-EPTYP2 no code token enters the shape list (%r)"
                   % (None if report is None else report["shapes"],)) and ok
        ok = check(report is not None
                   and report["shapes"] == ["nul", "utf8", "tail"],
                   "AC-EPTYP2 the earned names ride unchanged (%r)"
                   % (None if report is None else report["shapes"],)) and ok
        sole = STP.report_of(SOLE)
        ok = check(sole is not None and sole["code"] == "E_EBOM_UTF16",
                   "AC-EPTYP2 a sole unknown shape is refused, not accepted (%r)"
                   % (None if sole is None else sole["code"],)) and ok
        ok = check(sole is not None and sole["shapes"] == []
                   and sole.get("unknown_code") == "E_EBOM_UTF16",
                   "AC-EPTYP2 the sole shape is named in its own field only "
                   "(%r / %r)"
                   % (None if sole is None else sole["shapes"],
                      None if sole is None else sole.get("unknown_code"))) and ok
        absent = os.path.join(SCRATCH, "unknown.txt")
        err = refuse(absent, MIX)
        ok = check(err is not None and err.code == "E_EBOM_UTF16"
                   and err.unknown_code == "E_EBOM_UTF16",
                   "AC-EPTYP2 capture refuses and carries the field (%r)"
                   % (None if err is None else err.unknown_code,)) and ok
        ok = check(not os.path.exists(absent),
                   "AC-EPTYP2 the refused target is absent") and ok
        ok = check(err is not None
                   and "unknown=E_EBOM_UTF16" in STP.refusal_line(err),
                   "AC-EPTYP2 the refusal line names the code (%r)"
                   % (None if err is None
                      else sanitise(STP.refusal_line(err)),)) and ok
        ok = check(report is not None
                   and STP.report_line(report).endswith(
                       "unknown=E_EBOM_UTF16"),
                   "AC-EPTYP2 the report line names the code (%r)"
                   % (None if report is None
                      else sanitise(STP.report_line(report)),)) and ok
    finally:
        EBG.refusal_of = original
    return ok


def ac_eptyp3():
    """AC-EPTYP3: every answer the six known shapes publish stays byte for byte."""
    ok = True
    fixtures = (R2720_FIXTURES + SHIPPED_FIXTURES
                + tuple(EPD.SEEDS.values()) + (GOOD, b"", SENTINEL))
    for raw in fixtures:
        mine = STP.report_of(raw)
        theirs = WSU.report_of(raw)
        ok = check(mine == theirs,
                   "AC-EPTYP3 %r publishes the R2725 answer (%r)"
                   % (raw[:10], None if theirs is None else theirs["shapes"])
                   ) and ok
        if mine is not None and theirs is not None:
            ok = check(STP.report_line(mine) == WSU.report_line(theirs),
                       "AC-EPTYP3 %r report line is byte-identical"
                       % (raw[:10],)) and ok
    ok = check(STP.order_line() == EPD.order_line(),
               "AC-EPTYP3 the order line is byte-identical (%r)"
               % (STP.order_line(),)) and ok
    ok = check(STP.known_codes() == frozenset(EPD.CODES.values()),
               "AC-EPTYP3 the known code set is the shipped six (%d)"
               % (len(STP.known_codes()),)) and ok
    return ok


def ac_eptyp4():
    """AC-EPTYP4: accepts unchanged, refusal leaves no byte behind."""
    ok = True
    path = os.path.join(SCRATCH, "clean.txt")
    landed = STP.capture(path, GOOD)
    ok = check(landed["verdict"] == "LANDED" and landed["shapes"] == [],
               "AC-EPTYP4 a clean payload lands with shapes=none") and ok
    ok = check(read_bytes(path) == GOOD,
               "AC-EPTYP4 every byte landed unchanged (%d bytes)"
               % (len(GOOD),)) and ok
    empty = os.path.join(SCRATCH, "empty.txt")
    reading = STP.capture(empty, b"")
    ok = check(reading["bytes"] == 0 and read_bytes(empty) == b"",
               "AC-EPTYP4 the zero-byte payload still lands empty") and ok
    real = real_evidence()
    if real is None:
        ok = check(False, "AC-EPTYP4 a real evidence fixture is missing") and ok
    else:
        raw = read_bytes(real)
        before = EUC.digest(raw)
        ok = check(STP.report_of(raw) is None,
                   "AC-EPTYP4 the real evidence reads ACCEPT (%s, %d bytes)"
                   % (os.path.basename(real), len(raw))) and ok
        ok = check(EUC.digest(read_bytes(real)) == before,
                   "AC-EPTYP4 the live read changed no real byte (%s)"
                   % (before,)) and ok
    absent = os.path.join(SCRATCH, "absent.txt")
    refuse(absent, BOM + b"a\x00b")
    ok = check(not os.path.exists(absent),
               "AC-EPTYP4 a known-shape refusal leaves the target absent") and ok
    existing = os.path.join(SCRATCH, "existing.txt")
    write_bytes(existing, SENTINEL)
    before = EUC.digest(read_bytes(existing))
    err = refuse(existing, GOOD)
    ok = check(err is not None and err.code == STP.E_EXISTS,
               "AC-EPTYP4 an existing target is refused as %s (got %r)"
               % (STP.E_EXISTS, None if err is None else err.code)) and ok
    ok = check(EUC.digest(read_bytes(existing)) == before,
               "AC-EPTYP4 the existing target is byte-identical (%s)"
               % (before,)) and ok
    return ok


def ac_eptyp5():
    """AC-EPTYP5: order and the unplaced-code field are read at CALL time."""
    ok = True
    plain_order = EPD.order()
    ok = check(STP.order_line() == EPD.order_line(),
               "AC-EPTYP5 the face reads the order from the chain at call time"
               ) and ok
    original, patched = patched_order_law()
    EBG.refusal_of = patched
    try:
        moved = EPD.order()
        ok = check(moved != plain_order and STP.order_line() == EPD.order_line(),
                   "AC-EPTYP5 a reordered shipped law MOVES this face order "
                   "(%r -> %r)" % (plain_order, moved)) and ok
        ok = check(moved.index("nul") < moved.index("bom"),
                   "AC-EPTYP5 the patched law puts nul before bom (%r)"
                   % (moved,)) and ok
    finally:
        EBG.refusal_of = original
    ok = check(EPD.order() == plain_order,
               "AC-EPTYP5 restoring the shipped law restores the order") and ok
    fields = []
    for code in ("E_EBOM_UTF16", "E_EBOM_UTF32"):
        original, patched = patched_code_law(code)
        EBG.refusal_of = patched
        try:
            fields.append(STP.unplaced_code(SOLE))
        finally:
            EBG.refusal_of = original
    ok = check(fields == ["E_EBOM_UTF16", "E_EBOM_UTF32"],
               "AC-EPTYP5 a different patched code MOVES the field (%r)"
               % (fields,)) and ok
    ok = not hasattr(STP, "ORDER") and not hasattr(STP, "UNKNOWN")
    ok = check(ok, "AC-EPTYP5 no cached order or unknown-code attribute exists"
               ) and ok
    ok = check(STP.name_table() == EPD.CODES,
               "AC-EPTYP5 the name table is read from the chain at call time"
               ) and ok
    return ok


def import_names(text):
    """The module names a source text imports, read line by line."""
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import "):
            out.append(stripped.split()[1])
        elif stripped.startswith("from ") and " import " in stripped:
            out.append(stripped.split()[1])
    return out


def ac_eptyp6():
    """AC-EPTYP6: hygiene - ASCII, stdlib only, own label and own suite."""
    raw = read_bytes(MODULE)
    ok = check(not any(byte >= 128 for byte in raw),
               "AC-EPTYP6 the module source is pure ASCII (%d bytes)"
               % (len(raw),))
    text = raw.decode("ascii")
    banned = [name for name in ("import time", "import datetime",
                                "import socket", "import urllib",
                                "import http", "shell=True")
              if name in text]
    ok = check(not banned, "AC-EPTYP6 no clock, no network, no shell (%s)"
               % (banned,)) and ok
    allowed = ("argparse", "json", "os", "sys",
               "evidence_capture_precedence_derived",
               "evidence_capture_precedence_unknown_shape",
               "evidence_capture_tail_guard", "evidence_utf8_capture")
    bad = [name for name in import_names(text)
           if name.split(".")[0] not in allowed]
    ok = check(not bad and import_names(text),
               "AC-EPTYP6 every import is stdlib or a shipped face (%s)"
               % (bad,)) and ok
    registry = read_bytes(REGISTRY).decode("utf-8")
    ok = check(registry.count(WIRED_LABEL) == 1,
               "AC-EPTYP6 the registry carries exactly one label row (%d)"
               % (registry.count(WIRED_LABEL),)) and ok
    ok = check(registry.count(WIRED_SUITE) == 1,
               "AC-EPTYP6 the registry carries exactly one suite row (%d)"
               % (registry.count(WIRED_SUITE),)) and ok
    ok = check(registry.count(PREV_LABEL) == 1,
               "AC-EPTYP6 the shipped unknown-shape row is untouched (%d)"
               % (registry.count(PREV_LABEL),)) and ok
    ok = check(os.path.isfile(SUITE),
               "AC-EPTYP6 this suite exists on disk") and ok
    ok = check(EXPECTED_CRITERIA == 6,
               "AC-EPTYP6 six criteria are declared") and ok
    ok = check(STP.LABEL == "os-evidence-capture-precedence-shape-typing",
               "AC-EPTYP6 the face carries its own reconcile label (%r)"
               % (STP.LABEL,)) and ok
    return ok


def main():
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    checks = [ac_eptyp1, ac_eptyp2, ac_eptyp3, ac_eptyp4, ac_eptyp5, ac_eptyp6]
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
