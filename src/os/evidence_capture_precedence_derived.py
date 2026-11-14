"""Evidence capture derived precedence (R2723).

MEASURED at R2720 that the compound refusal report own shape ORDER was a
hardcoded constant tuple while the first code was asked from the shipped chain
at CALL time, so the two could drift apart silently: with that tuple patched to
tail-first the same payload still published first code E_EBOM_BOM while the
shape list started with tail, i.e. the report could name a defect first that
the shipped chain would never name first.

This face DERIVES the precedence at CALL time instead of copying it: for each
of the fifteen shape pairs it builds a payload carrying exactly those two
shapes, verifies that isolation against the shipped counters, asks the shipped
chain which code it publishes first on that payload, and reads the winner off
the answer. The fifteen answers give a dominance relation, and the order is the
unique topological reading of it - a relation that is not total, a seed that no
longer isolates its two shapes and an answer that names a third shape are all
REFUSED rather than guessed. A patched shipped refusal law therefore MOVES the
derived order by construction.

Every published answer - the first code, each measured counter and each shape
list - is byte for byte what the shipped trio published, so this face changes
provenance rather than policy.

Criteria AC-ECORD1..AC-ECORD6 were pinned in state/queue/tech.md:694 at R2720
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

import evidence_capture_tail_guard as ETG
import evidence_utf8_capture as EUC

LABEL = "os-evidence-capture-precedence-derived"

E_ARGS = EUC.E_ARGS
E_EXISTS = EUC.E_EXISTS
E_SEED = "E_EPD_SEED"
E_ANSWER = "E_EPD_ANSWER"
E_ORDER = "E_EPD_ORDER"

BOM = b"\xef\xbb\xbf"

# The six shapes the shipped chain can name. This tuple is the CANDIDATE SET,
# never the answer: the answer is read out of the chain by the probes below.
ITEMS = ("bom", "nul", "utf8", "crlf", "lone_cr", "tail")

CODES = {
    "bom": "E_EBOM_BOM",
    "nul": "E_EBOM_NUL",
    "utf8": EUC.E_NOT_UTF8,
    "crlf": EUC.E_CRLF,
    "lone_cr": EUC.E_LONE_CR,
    "tail": "E_ETAIL_TAIL",
}

BY_CODE = dict((code, name) for name, code in CODES.items())

# One fixture per shape pair, each carrying EXACTLY those two shapes. They are
# re-checked against the shipped counters at CALL time, so a shipped change to
# shape detection is refused here rather than silently mis-derived.
_SEED_FIXTURES = {
    ("bom", "nul"): BOM + b"a\x00b\n",
    ("bom", "utf8"): BOM + b"\xff\n",
    ("bom", "crlf"): BOM + b"a\r\nb\n",
    ("bom", "lone_cr"): BOM + b"a\rb\n",
    ("bom", "tail"): BOM + b"abc",
    ("nul", "utf8"): b"\xff\x00\n",
    ("nul", "crlf"): b"a\x00\r\n",
    ("nul", "lone_cr"): b"a\x00\rb\n",
    ("nul", "tail"): b"a\x00b",
    ("utf8", "crlf"): b"\xff\r\n",
    ("utf8", "lone_cr"): b"\xff\rb\n",
    ("utf8", "tail"): b"\xff",
    ("crlf", "lone_cr"): b"a\r\nb\rc\n",
    ("crlf", "tail"): b"a\r\nb",
    ("lone_cr", "tail"): b"a\rb",
}

# Keyed by the canonical (name-sorted) pair so the probe list carries no bias.
SEEDS = dict((tuple(sorted(pair)), seed)
             for pair, seed in _SEED_FIXTURES.items())

USAGE = ("usage: evidence_capture_precedence_derived.py --source PATH "
         "[--target PATH] [--root PATH] [--json] [--check] [--order]\n")


class Refused(EUC.CaptureRefused):
    """A refusal that also carries the derived shape list."""

    def __init__(self, code, detail="", counters=None, shapes=None):
        EUC.CaptureRefused.__init__(self, code, detail, counters)
        self.shapes = list(shapes or [])


class DerivationRefused(Exception):
    """The chain could not be read into a single order; refused, not guessed."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def earned_shapes(raw):
    """The shapes a payload earns, read from the shipped counters only."""
    raw = EUC.as_bytes(raw)
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
    return earned


def chain_code(raw):
    """The code the shipped chain publishes first, asked at CALL time."""
    answer = ETG.refusal_of(raw)
    if answer is None:
        return None
    return answer["code"]


def pairs():
    """The fifteen unordered shape pairs, in a name order with no bias."""
    names = sorted(ITEMS)
    out = []
    for left in range(len(names)):
        for right in range(left + 1, len(names)):
            out.append((names[left], names[right]))
    return out


def dominance():
    """Every shape pair answer, read into 'who wins' form."""
    beats = dict((name, set()) for name in ITEMS)
    for pair in pairs():
        seed = SEEDS[pair]
        earned = earned_shapes(seed)
        if earned != set(pair):
            raise DerivationRefused(
                E_SEED, "pair=%s,%s other=%s" %
                (pair[0], pair[1], ",".join(sorted(earned - set(pair))) or "none"))
        winner = BY_CODE.get(chain_code(seed))
        if winner is None:
            raise DerivationRefused(E_ANSWER, "pair=%s,%s code=none"
                                    % (pair[0], pair[1]))
        if winner not in pair:
            raise DerivationRefused(E_ANSWER, "pair=%s,%s code=%s names=%s"
                                    % (pair[0], pair[1],
                                       chain_code(seed), winner))
        loser = pair[1] if winner == pair[0] else pair[0]
        beats[winner].add(loser)
    return beats


def order():
    """The precedence DERIVED from the chain at this call, not a constant."""
    beats = dominance()
    remaining = list(ITEMS)
    out = []
    while remaining:
        top = [name for name in remaining
               if not any(name in beats[other]
                          for other in remaining if other != name)]
        if len(top) != 1:
            raise DerivationRefused(
                E_ORDER, "step=%d candidates=%s" % (len(out), ",".join(top)))
        out.append(top[0])
        remaining.remove(top[0])
    return tuple(out)


def shapes_of(data):
    """Every shape the payload earns, in the precedence derived at this call."""
    earned = earned_shapes(data)
    return [name for name in order() if name in earned]


def report_of(data):
    """None when the bytes may land, otherwise the same report the trio gives."""
    raw = EUC.as_bytes(data)
    shapes = shapes_of(raw)
    if not shapes:
        return None
    counts = EUC.measure(raw)
    return {"code": chain_code(raw), "shapes": shapes,
            "shape_codes": [CODES[name] for name in shapes],
            "counters": counts}


def refusal_of(data):
    """The derived report, or None - the same shape the shipped faces return."""
    return report_of(data)


def capture(target, data, root=None):
    """Refuse with the derived report, otherwise land exactly as the trio does."""
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
    """One ASCII line in the shipped format, naming the derived shape order."""
    counters = report["counters"]
    line = ("REFUSED code=%s shapes=%s codes=%s bytes=%d crlf=%d lone_cr=%d"
            " nul=%d"
            % (report["code"], ",".join(report["shapes"]),
               ",".join(report["shape_codes"]), counters["bytes"],
               counters["crlf"], counters["lone_cr"], counters["nul"]))
    if counters.get("bad_offset") is not None:
        line += " offset=%d" % counters["bad_offset"]
    return line


def order_line(derived=None):
    """One ASCII line naming the derived order and the probes that produced it."""
    names = order() if derived is None else derived
    return ("ORDER derived=%s probes=%d items=%d"
            % (",".join(names), len(pairs()), len(ITEMS)))


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
        except DerivationRefused as err:
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
    except DerivationRefused as err:
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
