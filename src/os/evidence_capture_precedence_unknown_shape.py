"""Evidence capture unknown-shape refusal (R2725).

The R2723 derivation covers exactly the SIX shapes the shipped chain names
today, and an earned shape whose code is NOT in that table is invisible to the
detector while the first code still names it. MEASURED this window on the
shipped face before this module existed, with one shipped refusal law patched
to answer E_EBOM_UTF16 for a byte-order-marked payload:

  a payload earning nul, utf8 and tail reads
      report_of -> code E_EBOM_UTF16 beside shapes nul,utf8,tail and
      shape_codes E_EBOM_NUL,E_EUC_NOT_UTF8,E_ETAIL_TAIL
      so the published list OMITS the defect the chain named first, and
      CODES[shapes[0]] reads E_EBOM_NUL against that code;

  a payload earning ONLY the unknown shape reads
      report_of -> None, i.e. ACCEPT
      while chain_code reads E_EBOM_UTF16, so bytes the shipped chain refuses
      would be LANDED by the derived face.

This face REFUSES any first code outside the six known shapes, naming that
code and the measured counters, and it names it FIRST in the shape list so no
published list can omit it. Every answer the six known shapes produce is
handed to the R2723 face unchanged, so those bytes and those report lines stay
byte for byte what it published. Both the derived order and the first code are
read from the shipped chain at CALL time, so patching a shipped face moves
each of them.

Criteria AC-EPDU1..AC-EPDU6 were pinned in state/queue/tech.md:695 at R2723
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

import evidence_capture_precedence_derived as EPD
import evidence_capture_tail_guard as ETG
import evidence_utf8_capture as EUC

LABEL = "os-evidence-capture-precedence-unknown-shape"

E_ARGS = EUC.E_ARGS
E_EXISTS = EUC.E_EXISTS

USAGE = ("usage: evidence_capture_precedence_unknown_shape.py --source PATH "
         "[--target PATH] [--root PATH] [--json] [--check] [--order]\n")


class Refused(EUC.CaptureRefused):
    """A refusal that also carries the published shape list."""

    def __init__(self, code, detail="", counters=None, shapes=None):
        EUC.CaptureRefused.__init__(self, code, detail, counters)
        self.shapes = list(shapes or [])


def known_codes():
    """The codes the six known shapes own, read off the shipped table."""
    return frozenset(EPD.CODES.values())


def chain_code(data):
    """The first code the shipped chain publishes, asked at CALL time."""
    return EPD.chain_code(data)


def unknown_code(data):
    """The first code when it is outside the six known shapes, else None."""
    code = chain_code(EUC.as_bytes(data))
    if code is None:
        return None
    if code in known_codes():
        return None
    return code


def _unnamed_report(raw, code):
    """The chain named a code the shape table cannot place: name it alone."""
    return {"code": code, "shapes": [code], "shape_codes": [code],
            "counters": EUC.measure(raw)}


def _unknown_report(raw, code):
    """Name the unknown code FIRST, then the known shapes it also earned."""
    earned = EPD.earned_shapes(raw)
    shape_names = [name for name in EPD.order() if name in earned]
    return {"code": code,
            "shapes": [code] + shape_names,
            "shape_codes": [code] + [EPD.CODES[name] for name in shape_names],
            "counters": EUC.measure(raw)}


def report_of(data):
    """None when the bytes may land, otherwise a report naming every shape."""
    raw = EUC.as_bytes(data)
    code = chain_code(raw)
    if code is None:
        return None
    if code in known_codes():
        base = EPD.report_of(raw)
        if base is not None:
            return base
        return _unnamed_report(raw, code)
    return _unknown_report(raw, code)


def refusal_of(data):
    """The report, or None - the same shape the shipped faces return."""
    return report_of(data)


def capture(target, data, root=None):
    """Refuse an unknown code, otherwise land exactly as the R2723 face does."""
    raw = EUC.as_bytes(data)
    path = EUC.resolve(root, target)
    counts = EUC.measure(raw)
    if os.path.exists(path):
        raise Refused(E_EXISTS, path, counts, [])
    report = report_of(raw)
    if report is not None:
        raise Refused(report["code"], path, counts, report["shapes"])
    landed = EPD.capture(path, raw, root=root)
    landed["shapes"] = []
    return landed


def report_line(report):
    """One ASCII line in the shipped format, byte for byte for known codes."""
    return EPD.report_line(report)


def order_line(derived=None):
    """One ASCII line naming the derived order, still derived at this call."""
    return EPD.order_line(derived)


def refusal_line(err):
    """One ASCII line for a refusal raised by capture()."""
    line = "REFUSED code=%s target=%s shapes=%s" % (
        err.code, err.detail, ",".join(err.shapes) or "none")
    for key, name in (("bytes", "bytes"), ("crlf", "crlf"),
                      ("lone_cr", "lone_cr"), ("nul", "nul"),
                      ("bad_offset", "offset")):
        value = err.counters.get(key)
        if value is not None:
            line += " %s=%s" % (name, value)
    return line


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--order", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
        return 0
    if args.order:
        try:
            print(order_line())
        except EPD.DerivationRefused as err:
            print("REFUSED code=%s detail=%s" % (err.code, err.detail))
            return 2
        return 0
    if not args.source:
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
        report = report_of(raw)
    except EPD.DerivationRefused as err:
        print("REFUSED code=%s detail=%s" % (err.code, err.detail))
        return 2
    if args.check or not args.target:
        if report is None:
            print("ACCEPT bytes=%d shapes=none" % (len(raw),))
            return 0
        print(report_line(report))
        return 2
    try:
        landed = capture(args.target, raw, root=args.root)
    except Refused as err:
        print(refusal_line(err))
        return 2
    if args.json:
        print(json.dumps(landed, sort_keys=True))
    else:
        print("capture target=%s bytes=%d sha256=%s shapes=none verdict=%s"
              % (landed["target"], landed["bytes"], landed["sha256"],
                 landed["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
