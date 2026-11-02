"""bare_evidence_pile_refusal (R2386; criteria AC-BEPR1..AC-BEPR6 were pinned

inside the R2380 seed row of state/queue/tech.md BEFORE this code existed).

followup_guard_evidence_scope (R2380) made the guarded pile follow the evidence
path, but a BARE filename has no directory part: os.path.dirname answers '' and
the derivation silently returned its default 'qa'. Measured at R2380:
evidence_dir('x.log') == 'qa' for a file that may live anywhere, so the guard
could once more speak about a pile the file does not belong to - the exact
defect R2380 closed for paths that carry a directory.

This module owns ONE question: which pile does an evidence NAME belong to?

  - pile_for(evidence, root)  the pile the file is MEASURED to live in.
  - a bare name is resolved by STAT-ing it under the root: the root itself
    (answered as '.') or a one-level subdirectory that contains the file.
  - a bare name that lives in two piles refuses as AMBIGUOUS rather than
    picking one; a bare name that lives nowhere refuses with its own code
    instead of speaking about a pile it cannot prove.
  - a name WITH a directory part answers exactly what
    followup_guard_evidence_scope answers (asked at call time), so that live
    reading is byte-identical.

The CLI asks the same question and then reads the derived pile through
followup_section_foreign_wire (imported at call time): a bare filename that
lives in a FOREIGN-SECTION pile refuses NAMING that pile, which is only
possible because the answer was measured. Exit codes and the pinned
GUARD_KEYS are the wire's: 0 clean, 2 refusal, 3 unreadable, 5 bad flags.

It writes nothing, reads no clock, opens no network connection. Pure stdlib,
pure-ASCII source, and it carries no default pile of its own.
"""

import json
import os
import sys

E_BEPR_BAD_ARGS = "E_BEPR_BAD_ARGS"
E_BEPR_BAD_EVIDENCE = "E_BEPR_BAD_EVIDENCE"
E_BEPR_NOT_FOUND = "E_BEPR_NOT_FOUND"
E_BEPR_AMBIGUOUS = "E_BEPR_AMBIGUOUS"

ROOT_PILE = "."

USAGE = ("usage: bare_evidence_pile_refusal.py --check EVIDENCE "
         "[--root PATH] [--json]\n"
         "  EVIDENCE is the log name the matrix section would read; a bare\n"
         "  filename is resolved under --root (default .), never defaulted\n"
         "  exit 0 = the pile reads VOCABULARY-CLEAN\n"
         "  exit 2 = refusal (E_BEPR_NOT_FOUND / E_BEPR_AMBIGUOUS / the\n"
         "           wire's foreign-section code), naming the pile\n"
         "  exit 3 = the derived pile cannot be read at all\n"
         "  exit 5 = bad flags\n")


class BareEvidencePileRefusalError(Exception):
    """A pile that must not be guessed, carrying its own token."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def is_bare(evidence):
    """True when the name carries no directory part.

    The seam the matrix section asks before it decides which law applies, so
    the wire never re-derives the 'no directory part' test itself.
    """
    return bool(isinstance(evidence, str) and evidence
                and not os.path.dirname(evidence))


def resolve_bare(evidence, root):
    """AC-BEPR1: the pile a bare filename actually lives in, by STAT-ing it.

    The root itself counts (answered as '.'), then every one-level
    subdirectory. Two containing piles are refused instead of chosen, because
    a guard that picks one of two is back to guessing.
    """
    found = []
    direct = os.path.join(root, evidence)
    if os.path.isfile(direct):
        found.append(ROOT_PILE)
    try:
        names = sorted(os.listdir(root))
    except OSError:
        names = []
    for name in names:
        folder = os.path.join(root, name)
        if os.path.isdir(folder) and os.path.isfile(
                os.path.join(folder, evidence)):
            if name not in found:
                found.append(name)
    if not found:
        raise BareEvidencePileRefusalError(
            E_BEPR_NOT_FOUND,
            "evidence %r is not under root %r" % (evidence, root))
    if len(found) > 1:
        raise BareEvidencePileRefusalError(
            E_BEPR_AMBIGUOUS,
            "evidence %r lives in piles %s"
            % (evidence, ",".join(found)))
    return found[0]


def pile_for(evidence, root):
    """AC-BEPR1/AC-BEPR2: the measured pile, never a default.

    A name with a directory part is not this module's question - it is handed
    to followup_guard_evidence_scope at call time, so that reading is exactly
    the R2380 one. A bare name is measured by resolve_bare, asked as a module
    attribute so a patched resolver moves which pile is read.
    """
    if not isinstance(evidence, str) or not evidence:
        raise BareEvidencePileRefusalError(
            E_BEPR_BAD_EVIDENCE, "evidence names no file")
    if os.path.dirname(evidence):
        import followup_guard_evidence_scope as FGES
        return FGES.evidence_dir(evidence)
    return resolve_bare(evidence, root)


def reading(evidence, root="."):
    """The wire's own report over the MEASURED pile, plus this module's codes.

    A refused derivation is reported with the wire's GUARD_KEYS shape and the
    empty pile, so a caller never reads a pile it could not prove.
    """
    import followup_section_foreign_wire as FSFW
    empty = {"vocabulary": [], "foreign": [], "missing": []}
    try:
        pile = pile_for(evidence, root)
    except BareEvidencePileRefusalError as exc:
        return {"dir": "", "verdict": "REFUSED", "rounds": 0,
                "rounds_foreign": [], "foreign": [], "census": empty,
                "code": exc.code, "detail": exc.detail}
    report = FSFW.guard(root, pile)
    report["detail"] = "pile=%s" % pile
    return report


def exit_code(report):
    """0 clean, 2 refusal, 3 unreadable - in that precedence."""
    if report["verdict"] == "REFUSED":
        return 2
    if report["code"]:
        return 3
    if report["verdict"] == "FOREIGN-SECTION":
        return 2
    return 0


def render(report):
    out = ["BARE EVIDENCE PILE dir=%s verdict=%s rounds=%d foreign_rounds=%d"
           % (report["dir"], report["verdict"], report["rounds"],
              len(report["rounds_foreign"]))]
    out.append("  foreign=%s" % (",".join(report["foreign"]) or "none"))
    census = report["census"]
    out.append("  census foreign=%s missing=%s"
               % (",".join(census.get("foreign") or []) or "none",
                  ",".join(census.get("missing") or []) or "none"))
    if report["code"]:
        out.append("  code=%s %s" % (report["code"], report.get("detail") or ""))
    return "\n".join(line.rstrip() for line in out)


def to_json(report):
    """AC-BEPR5: the pinned GUARD_KEYS order, ASCII, one trailing LF."""
    import followup_section_foreign_wire as FSFW
    ordered = {}
    for key in FSFW.GUARD_KEYS:
        if key == "census":
            census = {}
            for name in ("vocabulary", "foreign", "missing"):
                census[name] = report["census"].get(name) or []
            ordered["census"] = census
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    operation = False
    as_json = False
    root = "."
    evidence = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_BEPR_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif evidence is None and not arg.startswith("-"):
            evidence = arg
        else:
            sys.stdout.write("E_BEPR_BAD_ARGS: unexpected %r\n" % arg)
            return 5
        index += 1
    if not operation or not evidence:
        sys.stdout.write(USAGE)
        return 5
    if not os.path.isdir(root):
        sys.stdout.write("E_BEPR_BAD_ARGS: root %r is not a directory\n" % root)
        return 5
    report = reading(evidence, root)
    code = exit_code(report)
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))