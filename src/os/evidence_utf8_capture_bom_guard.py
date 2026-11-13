"""Evidence UTF-8 capture BOM and NUL guard (R2715).

The shipped capture guard src/os/evidence_utf8_capture.py refuses CRLF, lone
CR and non-utf-8 bytes at CALL time, but it accepts two shapes that the
verdict face already treats as bad. MEASURED this window on that shipped tree
before this module existed:

  a payload beginning with a UTF-8 BOM LANDS
      capture -> LANDED bytes=9
      battery_followup.eol_state(file) -> (0, 0, True, 9), i.e. bom=True and
      therefore eol_ok=False on the very file the capture just accepted, so
      the two faces disagree about the same bytes;

  a payload carrying NUL LANDS
      capture -> LANDED nul=1, measured and published but never enforced.

This face asks the SHIPPED eol_state law at CALL time on the same bytes, so
the two faces cannot disagree, and it refuses BOM and NUL with its own codes
and measured counters before any landing. Every payload R2714 lands is handed
to that shipped face unchanged, so its bytes and its answers stay byte for
byte what it published.

Criteria AC-EBOM1..AC-EBOM6 were pinned in state/queue/tech.md:691 at R2714
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys
import tempfile

import battery_followup as BF
import evidence_utf8_capture as EUC

LABEL = "os-evidence-utf8-capture-bom-guard"

E_ARGS = EUC.E_ARGS
E_BOM = "E_EBOM_BOM"
E_NUL = "E_EBOM_NUL"
E_EXISTS = EUC.E_EXISTS

BOM = b"\xef\xbb\xbf"

USAGE = ("usage: evidence_utf8_capture_bom_guard.py --target PATH "
         "--source PATH [--root PATH] [--json]\n")


class Refused(EUC.CaptureRefused):
    """A refused capture that also carries the shipped eol reading."""

    def __init__(self, code, detail="", counters=None, eol=None):
        EUC.CaptureRefused.__init__(self, code, detail, counters)
        self.eol = dict(eol or {})


def eol_reading(data):
    """Ask the SHIPPED eol_state law on exactly these bytes, at call time."""
    raw = EUC.as_bytes(data)
    handle, path = tempfile.mkstemp(suffix=".ebom-probe")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(raw)
        crlf, bare, bom, size = BF.eol_state(path)
    finally:
        try:
            os.unlink(path)
        except (IOError, OSError):
            pass
    return {"crlf": crlf, "bare_cr": bare, "bom": bom, "bytes": size,
            "eol_ok": crlf == 0 and bare == 0 and not bom}


def refusal_of(data):
    """None when the bytes may land; otherwise its own code and counters."""
    raw = EUC.as_bytes(data)
    counts = EUC.measure(raw)
    reading = eol_reading(raw)
    if reading["bom"]:
        return {"code": E_BOM, "counters": counts, "eol": reading}
    if counts["nul"]:
        return {"code": E_NUL, "counters": counts, "eol": reading}
    base = EUC.refusal_of(raw)
    if base is not None:
        return {"code": base["code"], "counters": base["counters"],
                "eol": reading}
    return None


def capture(target, data, root=None):
    """Refuse BOM and NUL, otherwise land exactly as the shipped face does."""
    raw = EUC.as_bytes(data)
    path = EUC.resolve(root, target)
    counts = EUC.measure(raw)
    reading = eol_reading(raw)
    if os.path.exists(path):
        raise Refused(E_EXISTS, path, counts, reading)
    refusal = refusal_of(raw)
    if refusal is not None:
        raise Refused(refusal["code"], path, refusal["counters"],
                      refusal["eol"])
    report = EUC.capture(path, raw, root=root)
    report["bom"] = False
    report["eol_ok"] = True
    return report


def refusal_line(err):
    """One ASCII line naming the code, the target and every measured count."""
    line = "REFUSED code=%s target=%s" % (err.code, err.detail)
    for key, name in (("bytes", "bytes"), ("crlf", "crlf"),
                      ("lone_cr", "lone_cr"), ("nul", "nul"),
                      ("bad_offset", "offset")):
        value = err.counters.get(key)
        if value is not None:
            line += " %s=%s" % (name, value)
    if err.eol:
        line += " bom=%s eol_ok=%s" % (err.eol.get("bom"),
                                       err.eol.get("eol_ok"))
    return line


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target")
    parser.add_argument("--source")
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
        return 0
    if not args.target or not args.source:
        sys.stderr.write(USAGE)
        return 5
    source = EUC.resolve(args.root, args.source)
    try:
        with open(source, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        print("REFUSED code=%s source=%s" % (EUC.E_NO_SOURCE, source))
        return 3
    try:
        report = capture(args.target, raw, root=args.root)
    except Refused as err:
        print(refusal_line(err))
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print("capture target=%s bytes=%d sha256=%s crlf=%d lone_cr=%d"
              " nul=%d bom=%s verdict=%s"
              % (report["target"], report["bytes"], report["sha256"],
                 report["crlf"], report["lone_cr"], report["nul"],
                 report["bom"], report["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
