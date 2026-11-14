"""Evidence capture compound refusal report (R2720).

MEASURED this window on the shipped trio (evidence_utf8_capture, its BOM and
NUL guard, and its tail guard): a payload can carry TWO or more shapes at once
and only the FIRST code is reported -

  NUL plus an unterminated tail        -> E_EBOM_NUL only
  BOM prefix plus an unterminated tail -> E_EBOM_BOM only
  BOM plus NUL plus an unterminated tail -> E_EBOM_BOM only
  CRLF plus NUL                        -> E_EBOM_NUL only

so an operator fixes one defect, retries, and is told about the next one only
then. This face reports EVERY shape a payload earns, each with its own measured
counter, in the shipped precedence order (BOM, NUL, utf8, CRLF, lone CR, tail),
BESIDE - never instead of - the shipped first code, which is asked from the
shipped chain at CALL time so the two can never disagree about which defect an
operator sees first.

Criteria AC-ECMP1..AC-ECMP6 were pinned in state/queue/tech.md:693 at R2718
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

import evidence_capture_tail_guard as ETG
import evidence_utf8_capture as EUC

LABEL = "os-evidence-capture-compound-refusal"

E_ARGS = EUC.E_ARGS
E_EXISTS = EUC.E_EXISTS

BOM = b"\xef\xbb\xbf"

# The published precedence of the shipped chain, measured rather than assumed:
# the BOM guard answers BOM then NUL BEFORE the capture face answers utf8,
# CRLF and lone CR, and the tail guard answers last.
ORDER = ("bom", "nul", "utf8", "crlf", "lone_cr", "tail")

CODES = {
    "bom": "E_EBOM_BOM",
    "nul": "E_EBOM_NUL",
    "utf8": EUC.E_NOT_UTF8,
    "crlf": EUC.E_CRLF,
    "lone_cr": EUC.E_LONE_CR,
    "tail": "E_ETAIL_TAIL",
}

USAGE = ("usage: evidence_capture_compound_refusal.py --source PATH "
         "[--target PATH] [--root PATH] [--json] [--check]\n")


class Refused(EUC.CaptureRefused):
    """A refusal that also carries EVERY shape the payload earned."""

    def __init__(self, code, detail="", counters=None, shapes=None):
        EUC.CaptureRefused.__init__(self, code, detail, counters)
        self.shapes = list(shapes or [])


def shapes_of(data):
    """Every shape the payload earns, in the shipped precedence order."""
    raw = EUC.as_bytes(data)
    counts = EUC.measure(raw)
    earned = set()
    if raw.startswith(BOM):
        earned.add("bom")
    if counts["nul"]:
        earned.add("nul")
    if not counts["utf8"]:
        earned.add("utf8")
    if counts["crlf"]:
        earned.add("crlf")
    if counts["lone_cr"]:
        earned.add("lone_cr")
    if raw and not raw.endswith(b"\n"):
        earned.add("tail")
    return [name for name in ORDER if name in earned]


def first_code(data):
    """The code the shipped chain publishes first, asked at CALL time."""
    raw = EUC.as_bytes(data)
    answer = ETG.refusal_of(raw)
    if answer is None:
        return None
    return answer["code"]


def report_of(data):
    """None when the bytes may land, otherwise the whole compound report."""
    raw = EUC.as_bytes(data)
    shapes = shapes_of(raw)
    if not shapes:
        return None
    counts = EUC.measure(raw)
    return {"code": first_code(raw), "shapes": shapes,
            "shape_codes": [CODES[name] for name in shapes],
            "counters": counts}


def refusal_of(data):
    """The compound report, or None - the same shape the shipped faces return."""
    return report_of(data)


def capture(target, data, root=None):
    """Refuse with the compound report, otherwise land exactly as the trio does."""
    raw = EUC.as_bytes(data)
    path = EUC.resolve(root, target)
    counts = EUC.measure(raw)
    if os.path.exists(path):
        raise Refused(E_EXISTS, path, counts, shapes_of(raw))
    report = report_of(raw)
    if report is not None:
        raise Refused(report["code"], path, counts, report["shapes"])
    landed = ETG.capture(path, raw, root=root)
    landed["shapes"] = []
    return landed


def report_line(report):
    """One ASCII line naming the first code, every shape and its counters."""
    counters = report["counters"]
    line = ("REFUSED code=%s shapes=%s codes=%s bytes=%d crlf=%d lone_cr=%d"
            " nul=%d"
            % (report["code"], ",".join(report["shapes"]),
               ",".join(report["shape_codes"]), counters["bytes"],
               counters["crlf"], counters["lone_cr"], counters["nul"]))
    if counters.get("bad_offset") is not None:
        line += " offset=%d" % counters["bad_offset"]
    return line


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
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
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
    if args.check or not args.target:
        report = report_of(raw)
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
