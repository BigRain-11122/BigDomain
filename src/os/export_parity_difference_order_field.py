"""Export parity difference order field (R2742).

The refusal R2501 ships names its field through
export_closeout_gate_parity.first_difference, and MEASURED this window on the
shipped law before this module existed that law answers the SHAPE WORD
``bytes`` when the ONLY difference between the two documents is key ORDER:

    left  {"x": 1, "y": 2}
    right {"y": 2, "x": 1}      -> first_difference -> "bytes"
    left  {"x": 1, "y": 2}
    right {"x": 1, "y": 3}      -> first_difference -> "y"

So an operator refused for a reordered document is told nothing, and the
R2501 refusal inherits that blind spot. This face does not replace that law:
it asks the shipped law at CALL time and publishes its answer unchanged in
``differs``, then names an order-only difference by the FIRST KEY THAT MOVED
in ``order_field`` - beside the shipped answer, never instead of it, so a
real value difference keeps exactly the field the shipped law names.

The reading is read-only (nothing is written, no clock is read), stdlib only,
ASCII source, zero network. Criteria AC-DFOB1..AC-DFOB6 were pinned in
state/queue/tech.md:703 at R2501 BEFORE this code existed.

CLI: export_parity_difference_order_field.py --left PATH --right PATH
                                                [--json]
  exit 0 = compared (the report says what the difference is)
  exit 2 = a source is missing, unreadable or not utf-8 text
  exit 5 = the flags are bad
"""

import argparse
import json
import sys

import export_closeout_gate_parity as PCP

LABEL = "os-export-parity-difference-order-field"

E_INPUT = "E_DFOB_INPUT"
E_NO_SOURCE = "E_DFOB_NO_SOURCE"

USAGE = ("usage: export_parity_difference_order_field.py --left PATH "
         "--right PATH [--json]\n")


class Refused(Exception):
    """A refusal that always carries its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s %s" % (code, detail))
        self.code = code
        self.detail = detail


def as_text(value):
    """Text from text or utf-8 bytes, or a named refusal."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            raise Refused(E_INPUT, "not utf-8 text")
    if not isinstance(value, str):
        raise Refused(E_INPUT, "not text")
    return value


def shipped_answer(left_text, right_text):
    """The shipped difference law, asked on its module at CALL time."""
    return PCP.first_difference(left_text, right_text)


def parsed(text):
    """True and the document when the text parses, False and None otherwise."""
    try:
        return True, json.loads(text)
    except ValueError:
        return False, None


def moved_key(left, right, prefix=""):
    """The first key that moved between two order-different documents."""
    if isinstance(left, dict) and isinstance(right, dict):
        left_keys = list(left.keys())
        right_keys = list(right.keys())
        if left_keys != right_keys:
            position = {}
            for index, key in enumerate(right_keys):
                position[key] = index
            for index, key in enumerate(left_keys):
                if position.get(key) != index:
                    return ("%s.%s" % (prefix, key)) if prefix else str(key)
        for key in left_keys:
            if key not in right:
                continue
            name = ("%s.%s" % (prefix, key)) if prefix else str(key)
            found = moved_key(left[key], right[key], name)
            if found:
                return found
        return ""
    if isinstance(left, list) and isinstance(right, list):
        name = prefix or "list"
        for index in range(min(len(left), len(right))):
            found = moved_key(left[index], right[index],
                              "%s[%d]" % (name, index))
            if found:
                return found
        return ""
    return ""


def order_field(left_text, right_text):
    """The first key that moved, or "" when no key moved at all.

    A value difference answers "" here: this field names an ORDER-ONLY
    difference and never competes with the field the shipped law names.
    """
    left_text = as_text(left_text)
    right_text = as_text(right_text)
    ok_left, left = parsed(left_text)
    ok_right, right = parsed(right_text)
    if not (ok_left and ok_right):
        return ""
    if left != right:
        return ""
    return moved_key(left, right)


def report_of(left_text, right_text):
    """One reading: the shipped answer unchanged beside the order field."""
    left_text = as_text(left_text)
    right_text = as_text(right_text)
    differs = shipped_answer(left_text, right_text)
    moved = order_field(left_text, right_text)
    ok_left, left = parsed(left_text)
    ok_right, right = parsed(right_text)
    if not differs and not moved:
        verdict = "IDENTICAL"
    elif moved:
        verdict = "ORDER-ONLY"
    elif not (ok_left and ok_right):
        verdict = "UNPARSEABLE"
    elif left == right:
        verdict = "FORMAT"
    else:
        verdict = "VALUE"
    return {"label": LABEL,
            "verdict": verdict,
            "differs": differs,
            "order_field": moved,
            "order_only": bool(moved),
            "left_bytes": len(left_text.encode("utf-8")),
            "right_bytes": len(right_text.encode("utf-8"))}


def report_line(report):
    """One ASCII line, the shipped answer kept in its own position."""
    return ("%s verdict=%s differs=%s order_field=%s order_only=%s "
            "left_bytes=%d right_bytes=%d"
            % (report["label"], report["verdict"],
               report["differs"] or "(none)",
               report["order_field"] or "(none)",
               "yes" if report["order_only"] else "no",
               report["left_bytes"], report["right_bytes"]))


def refusal_line(err):
    """One ASCII line for a refusal raised by this face."""
    return "REFUSED code=%s detail=%s" % (err.code, err.detail)


def read_text(path):
    """Read one source as text, or refuse with its own code."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        raise Refused(E_NO_SOURCE, str(path).replace("\\", "/"))
    return as_text(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--left")
    parser.add_argument("--right")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
        return 0
    if not args.left or not args.right:
        sys.stderr.write(USAGE)
        return 5
    try:
        report = report_of(read_text(args.left), read_text(args.right))
    except Refused as err:
        print(refusal_line(err))
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(report_line(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
