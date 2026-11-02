"""followup_bare_evidence_face (R2404; criteria AC-FBEF1..AC-FBEF6 were pinned

inside the R2396 seed row of state/queue/tech.md BEFORE this code existed).

matrix_evidence_pile_consistency (R2396) made the matrix SECTION hand its tool
the same file the guard measured, but the follow-up CLI never asked that law at
all: battery_followup.main answered

    evidence = os.path.join(root, opts["evidence"])

so `battery_followup.py --dry-run --evidence reconcile-all-R2394-retry.log`
printed MISSING EVIDENCE at exit 3 and never reached the section, while the same
bare name is PLACED in qa by the pile law. The defect was invisible from the
only face an operator walks.

This module owns ONE answer: the argument the four sections must receive.

  - placement(evidence, root)  the pile the pile law measured, the exact string
    the sections get, and whether that string names a file that exists.
  - a bare name that lives in exactly one pile resolves to `<pile>/<basename>`
    (AC-FBEF1), so the CLI face and the section face name one file.
  - a bare name that lives at the root keeps TODAY'S string unchanged, because
    that invocation already worked and its report must not move (AC-FBEF5).
  - a name that carries a directory is handed through byte for byte (AC-FBEF2).
  - a name the pile law cannot place is REFUSED with that law's own code and is
    never joined to a guessed pile (AC-FBEF3).

Three authorities stay where they are: the measured pile and the join belong to
matrix_evidence_pile_consistency, the pile measurement to
bare_evidence_pile_refusal, and the four sections to battery_followup. Both are
imported at CALL time, so a patched pile moves this reading too (AC-FBEF1).

It writes nothing, reads no clock, opens no network connection. Pure stdlib,
pure-ASCII source.
"""

import json
import os
import sys

E_FBEF_BAD_ARGS = "E_FBEF_BAD_ARGS"
E_FBEF_BAD_EVIDENCE = "E_FBEF_BAD_EVIDENCE"

RESOLVED = "RESOLVED"
REFUSED = "REFUSED"

REPORT_KEYS = ("evidence", "pile", "argument", "exists", "verdict", "code",
               "detail")
JSON_KEYS = REPORT_KEYS

USAGE = ("usage: followup_bare_evidence_face.py --check EVIDENCE "
         "[--root PATH] [--directory DIR] [--json]\n"
         "  EVIDENCE is the name the follow-up CLI was given\n"
         "  exit 0 = RESOLVED and the argument names a file that exists\n"
         "  exit 2 = the evidence argument is not a name at all\n"
         "  exit 3 = REFUSED by the pile law, or the resolved file is absent\n"
         "  exit 5 = bad flags\n")


def _law():
    """The pile/join law, asked at CALL time (AC-FBEF1, AC-FBEF6)."""
    import matrix_evidence_pile_consistency as MEPC
    return MEPC


def _root_pile():
    """The pile name the pile law gives the root itself, asked at CALL time."""
    import bare_evidence_pile_refusal as BEPR
    return BEPR.ROOT_PILE


def placement(evidence, root, directory=None):
    """AC-FBEF1/AC-FBEF2/AC-FBEF3: (pile, argument, exists, verdict, code)."""
    if not isinstance(evidence, str) or not evidence:
        return {"evidence": "", "pile": "", "argument": "", "exists": False,
                "verdict": REFUSED, "code": E_FBEF_BAD_EVIDENCE,
                "detail": "evidence names no file"}
    law = _law()
    report = law.placement(evidence, root, directory)
    if report["verdict"] != law.PLACED:
        return {"evidence": evidence, "pile": "", "argument": "",
                "exists": False, "verdict": REFUSED,
                "code": report["code"], "detail": report["detail"]}
    pile = report["pile"]
    # A file sitting at the root already worked: keep the operator's own string
    # so its report stays byte for byte (AC-FBEF5). Every other measured pile
    # moves the argument to `<pile>/<basename>` (AC-FBEF1).
    argument = evidence if pile == _root_pile() else report["argument"]
    if os.path.isabs(argument):
        target = os.path.normpath(argument)
    else:
        target = os.path.normpath(os.path.join(root, argument))
    return {"evidence": evidence, "pile": pile, "argument": argument,
            "exists": os.path.isfile(target), "verdict": RESOLVED,
            "code": "", "detail": "pile=%s" % pile}


def exit_code(report):
    """0 resolved and present, 2 malformed evidence, 3 refused or absent."""
    if report["verdict"] != RESOLVED:
        return 2 if report["code"] == E_FBEF_BAD_EVIDENCE else 3
    return 0 if report["exists"] else 3


def render(report):
    out = ["FOLLOWUP EVIDENCE evidence=%s pile=%s verdict=%s"
           % (report["evidence"], report["pile"] or "-", report["verdict"])]
    out.append("  argument=%s exists=%s"
               % (report["argument"] or "-",
                  "yes" if report["exists"] else "no"))
    if report["code"]:
        out.append("  code=%s %s" % (report["code"], report["detail"]))
    return "\n".join(line.rstrip() for line in out)


def to_json(report):
    """A byte-stable payload over the pinned JSON_KEYS."""
    ordered = {}
    for key in JSON_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def parse_args(argv):
    opts = {"evidence": None, "root": None, "directory": None, "json": False}
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg in ("--check",):
            index += 1
        elif arg == "--json":
            opts["json"] = True
            index += 1
        elif arg in ("--root", "--directory"):
            if index + 1 >= len(argv) or not argv[index + 1]:
                raise ValueError(E_FBEF_BAD_ARGS + " " + arg + " needs a value")
            opts[arg[2:]] = argv[index + 1]
            index += 2
        elif arg.startswith("-"):
            raise ValueError(E_FBEF_BAD_ARGS + " " + arg)
        elif opts["evidence"] is None:
            opts["evidence"] = arg
            index += 1
        else:
            raise ValueError(E_FBEF_BAD_ARGS + " " + arg)
    if opts["evidence"] is None:
        raise ValueError(E_FBEF_BAD_ARGS + " --check EVIDENCE is required")
    if opts["root"] is None:
        opts["root"] = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", ".."))
    if not os.path.isdir(opts["root"]):
        raise ValueError(E_FBEF_BAD_ARGS + " --root is not a directory")
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except ValueError as exc:
        print(str(exc))
        return 5
    report = placement(opts["evidence"], opts["root"], opts["directory"])
    print(render(report))
    if opts["json"]:
        print(to_json(report), end="")
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))