"""matrix_evidence_pile_consistency (R2396; criteria AC-MEPC1..AC-MEPC6 were

pinned inside the R2386 seed row of state/queue/tech.md BEFORE this code).

bare_evidence_pile_refusal (R2386) made the matrix section guard the pile a
bare evidence name MEASURABLY lives in, but the section still handed the
ORIGINAL string to the matrix tool: battery_followup.matrix_core runs
`suite_matrix.py --evidence <evidence>` with cwd=root, so a bare name resolves
against the root while the guard spoke about the pile the file was measured in.
One reading named `qa`, the other read `<root>/<name>` - a guard protecting a
pile the rendered doc was not built from.

This module owns ONE answer: the exact argument the tool must receive, derived
from THAT SAME measured pile.

  - pile_for(evidence, root, directory)  the pile the guard reads: an explicit
    directory wins (the caller's assertion), otherwise a bare name is measured
    by bare_evidence_pile_refusal.pile_for and a name with a directory part is
    derived exactly as followup_guard_evidence_scope derives it.
  - tool_argument(evidence, root, directory)  a bare name becomes
    `<pile>/<basename>`; a name that carries a directory is handed through
    UNCHANGED, byte for byte (AC-MEPC2), so the R2380 reading is untouched.
  - align(...)  the pair, with a refusal entry instead of an exception, so the
    matrix section can refuse BEFORE any doc byte exists (AC-MEPC4).
  - placement(...)  the pair plus `same_file`: both strings resolved under the
    root the tool actually runs in, so the guard and the tool provably read the
    SAME file (AC-MEPC3).

Two authorities stay where they are: the pile measurement is
bare_evidence_pile_refusal's and the matrix rendering is battery_followup's -
this file only makes the two halves name one file.

It writes nothing, reads no clock, opens no network connection. Pure stdlib,
pure-ASCII source.
"""

import json
import os
import sys

E_MEPC_BAD_ARGS = "E_MEPC_BAD_ARGS"
E_MEPC_BAD_EVIDENCE = "E_MEPC_BAD_EVIDENCE"
E_MEPC_UNPLACEABLE = "E_MEPC_UNPLACEABLE"

SECTION_NAME = "matrix"

PLACED = "PLACED"
REFUSED = "REFUSED"

REPORT_KEYS = ("evidence", "pile", "argument", "same_file", "verdict",
               "code", "detail")
JSON_KEYS = REPORT_KEYS + ("guard",)

USAGE = ("usage: matrix_evidence_pile_consistency.py --check EVIDENCE "
         "[--root PATH] [--directory DIR] [--json]\n"
         "  EVIDENCE is the name the matrix section would hand its tool\n"
         "  exit 0 = PLACED, one pile and one argument naming the same file\n"
         "  exit 2 = refusal (E_MEPC_UNPLACEABLE / E_MEPC_BAD_EVIDENCE)\n"
         "  exit 3 = the pile cannot be read at all (the guard's own code)\n"
         "  exit 5 = bad flags\n")


class UnplaceableEvidence(Exception):
    """A name that must not be handed to the tool, carrying its own token."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _bad_evidence(evidence):
    if not isinstance(evidence, str) or not evidence:
        raise UnplaceableEvidence(E_MEPC_BAD_EVIDENCE, "evidence names no file")


def is_bare(evidence):
    """Asked of the pile law, never re-derived here (one owner)."""
    import bare_evidence_pile_refusal as BEPR
    return BEPR.is_bare(evidence)


def pile_for(evidence, root, directory=None):
    """AC-MEPC1/AC-MEPC2: the pile the GUARD reads, from one measured reading.

    An explicit directory is the caller's assertion and wins. Otherwise a bare
    name is measured (a patched measured moves this reading, and with it the
    argument the tool receives) and a path that carries a directory keeps the
    R2380 derivation byte for byte.
    """
    _bad_evidence(evidence)
    if directory is not None:
        return directory
    import bare_evidence_pile_refusal as BEPR
    if BEPR.is_bare(evidence):
        try:
            return BEPR.pile_for(evidence, root)
        except BEPR.BareEvidencePileRefusalError as exc:
            raise UnplaceableEvidence(exc.code, exc.detail)
    import followup_guard_evidence_scope as FGES
    return FGES.evidence_dir(evidence)


def tool_argument(evidence, root, directory=None):
    """AC-MEPC1/AC-MEPC2: the exact string the matrix tool must receive."""
    _bad_evidence(evidence)
    if not is_bare(evidence):
        return evidence
    pile = pile_for(evidence, root, directory)
    return os.path.join(pile, os.path.basename(evidence))


def _resolve(root, path):
    """The absolute file a root-relative or absolute path names."""
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(root, path))


def same_file(root, evidence, pile, argument):
    """AC-MEPC3: both halves, resolved the way the tool resolves them.

    The tool runs with cwd=root, so its argument is root-relative; the guard
    joins its pile under the same root. Equality of the two absolute paths is
    the whole proof - a guard and a tool that name different files reads False.
    """
    guard_side = _resolve(root, os.path.join(pile,
                                             os.path.basename(evidence)))
    tool_side = _resolve(root, argument)
    return guard_side == tool_side


def placement(evidence, root, directory=None):
    """AC-MEPC3: the pair plus whether they name one file, never raising."""
    try:
        pile = pile_for(evidence, root, directory)
        argument = tool_argument(evidence, root, pile)
    except UnplaceableEvidence as exc:
        return {"evidence": evidence, "pile": "", "argument": "",
                "same_file": False, "verdict": REFUSED, "code": exc.code,
                "detail": exc.detail}
    return {"evidence": evidence, "pile": pile, "argument": argument,
            "same_file": same_file(root, evidence, pile, argument),
            "verdict": PLACED, "code": "", "detail": "pile=%s" % pile}


def refusal_entry(code, detail, evidence):
    """AC-MEPC4: a FAIL entry the matrix section returns before any tool call."""
    return {"section": SECTION_NAME, "verdict": "FAIL",
            "detail": "%s %s evidence=%s" % (code, detail, evidence)}


def align(evidence, root, directory=None):
    """AC-MEPC1/AC-MEPC4: (argument, refusal entry or None) for the section."""
    report = placement(evidence, root, directory)
    if report["verdict"] != PLACED:
        return evidence, refusal_entry(report["code"], report["detail"],
                                       evidence)
    return report["argument"], None


def exit_code(report, guard=None):
    """0 placed and readable, 2 refusal, 3 the pile cannot be read at all."""
    if report["verdict"] != PLACED:
        return 2
    if guard is not None and guard.get("code"):
        return 3
    return 0


def render(report, guard=None):
    out = ["MATRIX EVIDENCE PILE evidence=%s pile=%s verdict=%s"
           % (report["evidence"], report["pile"] or "-", report["verdict"])]
    out.append("  argument=%s same_file=%s"
               % (report["argument"] or "-",
                  "yes" if report["same_file"] else "no"))
    if report["code"]:
        out.append("  code=%s %s" % (report["code"], report["detail"]))
    if guard is not None:
        out.append("  guard=%s dir=%s rounds=%d foreign_rounds=%d"
                   % (guard.get("verdict") or "-", guard.get("dir") or "-",
                      guard.get("rounds") or 0,
                      len(guard.get("rounds_foreign") or [])))
        if guard.get("code"):
            out.append("  guard_code=%s" % guard["code"])
    return "\n".join(line.rstrip() for line in out)


def to_json(report, guard=None):
    """AC-MEPC5: a byte-stable payload over the pinned JSON_KEYS."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    ordered["guard"] = ("" if guard is None
                        else (guard.get("code") or guard.get("verdict") or ""))
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    operation = False
    as_json = False
    root = "."
    directory = None
    evidence = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--directory"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("%s: %s needs a value\n"
                                 % (E_MEPC_BAD_ARGS, arg))
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                directory = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif evidence is None and not arg.startswith("-"):
            evidence = arg
        else:
            sys.stdout.write("%s: unexpected %r\n" % (E_MEPC_BAD_ARGS, arg))
            return 5
        index += 1
    if not operation or not evidence:
        sys.stdout.write(USAGE)
        return 5
    if not os.path.isdir(root):
        sys.stdout.write("%s: root %r is not a directory\n"
                         % (E_MEPC_BAD_ARGS, root))
        return 5
    report = placement(evidence, root, directory)
    guard = None
    if report["verdict"] == PLACED:
        import followup_section_foreign_wire as FSFW
        guard = FSFW.guard(root, report["pile"])
    if as_json:
        sys.stdout.write(to_json(report, guard))
    else:
        sys.stdout.write(render(report, guard) + "\n")
    return exit_code(report, guard)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))