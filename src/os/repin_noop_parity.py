"""repin_noop_parity - do the shipped re-pin CLI and the NOOP wire agree?

Criteria AC-RNP1..AC-RNP6 were pinned inside the R2372 seed row of
state/queue/tech.md BEFORE this file existed.

Why this exists: `residue_triage_repin.plan` composes a fresh declaration and
writes it, and R2372 added the NOOP reading in ONE module
(`residue_triage_repin_idempotent.decide`) without teaching the tool operators
actually run. R2363 measured the seam at its own live write: a second plan
composed bytes IDENTICAL to the file on disk and still read PLANNED, so
`--execute` rewrote the same bytes and reported PINNED, and a caller could not
tell which law had run.

This file owns the comparison and nothing else:

  * `is_noop(path, text)` is the ONE law: the composed document's bytes equal
    the bytes on disk. `residue_triage_repin.plan` imports it, so the shipped
    CLI and the wire answer one question through one comparison - no second
    composition, no second writer, and the shipped module keeps its own single
    atomic replace;
  * `check` runs BOTH faces over ONE declaration, dry by default so neither
    face can move the file between the two readings, and reports AGREES or
    names the FIRST field that differs in the pinned key order;
  * refusals are compared by code AND detail, because the two faces must keep
    answering refusals and exit codes byte-identically.

Read-only: it writes nothing, reads no clock, imports no network, and it is
pure ASCII stdlib. The two faces are imported INSIDE the functions that ask
them, so this module imports cleanly while `residue_triage_repin` imports it.
"""

import json
import os
import sys

PARITY_PREFIX = "E_RNP"

# AC-RNP4: the report carries these keys in this order and nothing else, and
# a NOOP reading travels inside them rather than adding a key.
REPORT_KEYS = (
    "verdict",
    "shipped",
    "wire",
    "shipped_code",
    "wire_code",
    "first_diff",
    "round",
    "until",
)

VERDICTS = ("AGREES", "DISAGREES")

REFUSED = "REFUSED"


class ParityError(Exception):
    """Raised only when the parity cannot be measured at all."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def is_noop(path, text):
    """The ONE comparison law: does the composed document equal the file?

    The law now owns the EOL dialect and lives in ONE place
    (`repin_noop_eol_dialect.is_noop`), imported AT CALL time (R2388) so a
    patched normaliser moves the shipped CLI and the wire together. A
    declaration that could not be read is not a NOOP - the caller then walks
    the shipped writer and its own refusals decide.
    """
    import repin_noop_eol_dialect as RNED
    return RNED.is_noop(path, text)


def _faces():
    """The two faces, resolved at CALL time so a patched law moves this read.

    Imported here rather than at module level because `residue_triage_repin`
    imports this module for the comparison; the wire imports the shipped
    module in turn. Asking inside the call keeps that chain one-way.
    """
    import residue_triage_repin as RTR
    import residue_triage_repin_idempotent as RI
    return RTR, RI


def _failures(RTR):
    return (RTR.RepinError, RTR.RT.ResidueTriageError)


def _side(call, RTR):
    """One face's answer, reduced to (verdict, code, detail, report)."""
    try:
        report = call()
    except _failures(RTR) as exc:
        return {"verdict": REFUSED, "code": exc.code,
                "detail": exc.detail or "", "report": None}
    except Exception as exc:  # noqa: BLE001 - a broken face is not agreement
        return {"verdict": REFUSED,
                "code": PARITY_PREFIX + "_BROKEN",
                "detail": "%s (%s)" % (type(exc).__name__, exc),
                "report": None}
    if not isinstance(report, dict):
        return {"verdict": REFUSED,
                "code": PARITY_PREFIX + "_BROKEN",
                "detail": "face returned %r" % (type(report).__name__,),
                "report": None}
    return {"verdict": report.get("verdict"), "code": None, "detail": "",
            "report": report}


def check(root, round_text, until_text, reason, allow_drop=False):
    """Run both faces over ONE declaration and say whether they agree.

    Both calls are DRY: nothing is written, so the second face reads exactly
    the file the first face read and the two answers belong to one instant.
    """
    if not os.path.isdir(root):
        raise ParityError(PARITY_PREFIX + "_ROOT",
                          "no such root: %s" % root)
    RTR, RI = _faces()
    args = (root, round_text, until_text, reason, allow_drop, False)
    shipped = _side(lambda: RTR.plan(*args), RTR)
    wire = _side(lambda: RI.decide(*args), RTR)

    first_diff = None
    if shipped["code"] is not None or wire["code"] is not None:
        # a refusal is compared by its code and then by its detail
        if shipped["code"] != wire["code"]:
            first_diff = "code"
        elif shipped["detail"] != wire["detail"]:
            first_diff = "detail"
    elif shipped["verdict"] != wire["verdict"]:
        first_diff = "verdict"
    else:
        for key in RTR.PLAN_KEYS:
            if shipped["report"].get(key) != wire["report"].get(key):
                first_diff = key
                break

    return {
        "verdict": "AGREES" if first_diff is None else "DISAGREES",
        "shipped": shipped["verdict"],
        "wire": wire["verdict"],
        "shipped_code": shipped["code"],
        "wire_code": wire["code"],
        "first_diff": first_diff,
        "round": round_text,
        "until": until_text,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("REPIN NOOP PARITY verdict=%s round=%s until=%s shipped=%s "
            "wire=%s first_diff=%s"
            % (report["verdict"], report["round"], report["until"],
               report["shipped_code"] or report["shipped"],
               report["wire_code"] or report["wire"],
               report["first_diff"] or "(none)"))


def render(report):
    """The one line, then both answers side by side."""
    out = [one_line(report)]
    out.append("  SHIPPED %s%s"
               % (report["shipped"],
                  "" if not report["shipped_code"]
                  else " " + report["shipped_code"]))
    out.append("  WIRE %s%s"
               % (report["wire"],
                  "" if not report["wire_code"]
                  else " " + report["wire_code"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (AC-RNP4)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: repin_noop_parity.py --check --round R<n> --until R<n> "
         "--reason TEXT [--drop-unmatched] [--root PATH] [--json]\n"
         "  exit 0 = the shipped re-pin CLI and the NOOP wire agree\n"
         "  exit 2 = they disagree (the first differing field is named)\n"
         "  exit 3 = the root is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check_flag = False
    as_json = False
    allow_drop = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    round_text = None
    until_text = None
    reason = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check_flag = True
        elif arg == "--json":
            as_json = True
        elif arg == "--drop-unmatched":
            allow_drop = True
        elif arg in ("--root", "--round", "--until", "--reason"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RNP_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return 5
            if arg == "--root":
                root = argv[index]
            elif arg == "--round":
                round_text = argv[index]
            elif arg == "--until":
                until_text = argv[index]
            else:
                reason = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_RNP_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check_flag:
        sys.stdout.write("E_RNP_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None or until_text is None or reason is None:
        sys.stdout.write("E_RNP_BAD_ARGS: --round, --until and --reason are "
                         "required\n")
        sys.stdout.write(USAGE)
        return 5
    try:
        report = check(root, round_text, until_text, reason, allow_drop)
    except ParityError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return 0 if report["verdict"] == "AGREES" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))