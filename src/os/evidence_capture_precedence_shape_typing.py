"""Evidence capture shape typing (R2730).

The R2725 unknown-shape refusal closes the boundary where a first code outside
the six known shapes is invisible, but MEASURED this window on the shipped face
before this module existed it publishes that code as an entry of the SHAPE
LIST, where every other entry is a shape NAME. With one shipped refusal law
patched to answer E_EBOM_UTF16 for a byte-order-marked payload:

  a payload earning nul, utf8 and tail reads
      report_of -> code E_EBOM_UTF16 beside
      shapes ['E_EBOM_UTF16', 'nul', 'utf8', 'tail'] and
      shape_codes ['E_EBOM_UTF16', 'E_EBOM_NUL', 'E_EUC_NOT_UTF8',
                   'E_ETAIL_TAIL']
      so EPD.CODES[shapes[0]] raises KeyError 'E_EBOM_UTF16' and any consumer
      that maps shapes through the name table breaks on exactly the payload
      that face exists to refuse;

  a payload earning ONLY that shape reads
      report_of -> code E_EBOM_UTF16 beside shapes ['E_EBOM_UTF16']
      and CODES[shapes[0]] raises the same KeyError.

This face keeps every published list NAMES-ONLY and carries the code that no
shape name can place in its OWN field, so a names-only consumer cannot break,
while the code is still refused and still named - never dropped and never
reported as an ACCEPT. Every answer the six known shapes publish is returned
unchanged, so those bytes and those report lines stay byte for byte what R2725
published. The name table, the derived order and the first code are all read
from the shipped chain at CALL time, so patching a shipped face moves each.

Criteria AC-EPTYP1..AC-EPTYP6 were pinned in state/queue/tech.md:697 at R2725
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

import evidence_capture_precedence_derived as EPD
import evidence_capture_precedence_unknown_shape as WSU
import evidence_capture_tail_guard as ETG
import evidence_utf8_capture as EUC

LABEL = "os-evidence-capture-precedence-shape-typing"

E_ARGS = EUC.E_ARGS
E_EXISTS = EUC.E_EXISTS

USAGE = ("usage: evidence_capture_precedence_shape_typing.py --source PATH "
         "[--target PATH] [--root PATH] [--json] [--check] [--order]\n")


class Refused(WSU.Refused):
    """A refusal whose shape list is names-only and which names its code."""

    def __init__(self, code, detail="", counters=None, shapes=None,
                 unknown_code=None):
        WSU.Refused.__init__(self, code, detail, counters, shapes)
        self.unknown_code = unknown_code


def name_table():
    """The shape-name to code table the shipped chain publishes, at call time."""
    return dict(EPD.CODES)


def known_codes():
    """The codes the six known shapes own, read at call time."""
    return frozenset(name_table().values())


def chain_code(data):
    """The first code the shipped chain publishes, asked at CALL time."""
    return EPD.chain_code(EUC.as_bytes(data))


def earned_names(data):
    """Every shape NAME the payload earns, in the order derived at call time.

    Names-only by construction: an entry is published only when the shipped
    name table can place it, so this list can never carry a code token.
    """
    table = name_table()
    earned = EPD.earned_shapes(EUC.as_bytes(data))
    return [name for name in EPD.order() if name in table and name in earned]


def placed_code(report):
    """The first code a report actually places inside its own list, or None."""
    if report is None:
        return None
    codes = report.get("shape_codes") or []
    if codes and codes[0] == report.get("code"):
        return codes[0]
    return None


def report_of(data):
    """None when the bytes may land, otherwise a names-only typed report."""
    raw = EUC.as_bytes(data)
    code = EPD.chain_code(raw)
    if code is None:
        return None
    base = EPD.report_of(raw)
    if placed_code(base) is not None:
        # The six known shapes answer exactly as they answered before.
        return base
    table = name_table()
    names = earned_names(raw)
    return {"code": code,
            "shapes": names,
            "shape_codes": [table[name] for name in names],
            "counters": EUC.measure(raw),
            "unknown_code": code}


def refusal_of(data):
    """The typed report, or None - the same shape the shipped faces return."""
    return report_of(data)


def unplaced_code(data):
    """The first code no shape name can place, or None when it is placed."""
    report = report_of(data)
    if report is None:
        return None
    return report.get("unknown_code")


def capture(target, data, root=None):
    """Refuse with the typed report, otherwise land as the shipped trio does."""
    raw = EUC.as_bytes(data)
    path = EUC.resolve(root, target)
    counts = EUC.measure(raw)
    if os.path.exists(path):
        raise Refused(E_EXISTS, path, counts, [])
    report = report_of(raw)
    if report is not None:
        raise Refused(report["code"], path, counts, report["shapes"],
                      report.get("unknown_code"))
    landed = EPD.capture(path, raw, root=root)
    landed["shapes"] = []
    return landed


def report_line(report):
    """One ASCII line in the shipped format, plus the unplaced code by name."""
    line = EPD.report_line(report)
    unknown = report.get("unknown_code")
    if unknown:
        line += " unknown=%s" % unknown
    return line


def order_line(derived=None):
    """One ASCII line naming the derived order, still derived at this call."""
    return EPD.order_line(derived)


def refusal_line(err):
    """One ASCII line for a refusal raised by capture()."""
    line = WSU.refusal_line(err)
    unknown = getattr(err, "unknown_code", None)
    if unknown:
        line += " unknown=%s" % unknown
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
