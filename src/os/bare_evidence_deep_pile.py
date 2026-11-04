"""bare_evidence_deep_pile (R2432; criteria AC-BEDP1..AC-BEDP6 were pinned in

the R2404 seed row of state/queue/tech.md BEFORE this code existed).

bare_evidence_pile_refusal (R2386) made a bare evidence name MEASURED instead
of defaulted, but the measurement walks the root and its ONE-LEVEL
subdirectories only. Measured at R2404 and again at R2432 before any code: a
name whose only copy lives at qa/rounds/<name> reads
file-exists=yes verdict=REFUSED code=E_BEPR_NOT_FOUND on both shipped faces
(bare_evidence_pile_refusal --check and matrix_evidence_pile_consistency
--check), so a filed-away log is reported ABSENT while it sits on disk.

This module owns ONE question: how deep does the pile measurement look, and
what does it say when the answer is "not within the depth I searched"?

  - MAX_DEPTH is the DECLARED search depth (2 = root plus two levels, so
    qa/rounds/<name> is inside it). search_depth() answers it AT CALL TIME,
    so a patched MAX_DEPTH moves every face that asks this module.
  - resolve(evidence, root) walks that depth and answers the pile, refusing
    AMBIGUOUS when two piles inside the searched depth carry the name.
  - A name that is not found is reported honestly: when the tree actually
    continues below the searched depth the refusal is E_BEDP_BEYOND_DEPTH and
    its detail names the depth that was searched; only when absence is PROVED
    (nothing continues below the limit) is the shipped E_BEPR_NOT_FOUND kept,
    so the R2386 face's code namespace stays exactly what it was.
  - reading() publishes the pinned keys, and the CLI exits 0/2/3/5 with a
    byte-stable --json.

It writes nothing, reads no clock, opens no network connection. Pure stdlib,
pure-ASCII source, and it carries no whitelist of directory names.
"""

import json
import os
import sys

MAX_DEPTH = 2

ROOT_PILE = "."

E_BEPR_NOT_FOUND = "E_BEPR_NOT_FOUND"
E_BEPR_AMBIGUOUS = "E_BEPR_AMBIGUOUS"
E_BEDP_BEYOND_DEPTH = "E_BEDP_BEYOND_DEPTH"
E_BEDP_BAD_EVIDENCE = "E_BEDP_BAD_EVIDENCE"
E_BEDP_BAD_ROOT = "E_BEDP_BAD_ROOT"

READING_KEYS = ("evidence", "root", "depth", "pile", "verdict", "code",
                "detail")

USAGE = ("usage: bare_evidence_deep_pile.py --check EVIDENCE "
         "[--root PATH] [--depth N] [--json]\n"
         "  EVIDENCE is a bare log name; the measurement looks MAX_DEPTH\n"
         "  levels under --root (default 2, default root .)\n"
         "  exit 0 = RESOLVED, the pile is named\n"
         "  exit 2 = refusal (E_BEDP_BEYOND_DEPTH / E_BEPR_AMBIGUOUS /\n"
         "           E_BEPR_NOT_FOUND when absence is proved)\n"
         "  exit 3 = the root cannot be read at all\n"
         "  exit 5 = bad flags\n")


class BareEvidenceDeepPileError(Exception):
    """A pile that must not be guessed, carrying its own token."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def search_depth():
    """AC-BEDP2: the declared depth, asked at CALL time."""
    return MAX_DEPTH


def _levels(root, depth):
    """Every directory at each level 0..depth, as root-relative paths."""
    level = [""]
    yield level
    for _ in range(depth):
        nxt = []
        for rel in level:
            base = os.path.join(root, rel) if rel else root
            try:
                names = sorted(os.listdir(base))
            except OSError:
                names = []
            for name in names:
                folder = os.path.join(base, name)
                if os.path.isdir(folder) and not os.path.islink(folder):
                    nxt.append(os.path.join(rel, name) if rel else name)
        level = nxt
        yield level


def piles_for(evidence, root, depth=None):
    """AC-BEDP1/AC-BEDP4: every pile inside the searched depth carrying it."""
    limit = search_depth() if depth is None else depth
    found = []
    for current, level in enumerate(_levels(root, limit)):
        if current > limit:
            break
        for rel in level:
            if os.path.isfile(os.path.join(root, rel, evidence)):
                found.append(rel or ROOT_PILE)
    return found


def continues_below(root, depth=None):
    """True when the tree really continues past the searched depth.

    A directory at exactly the limit that carries at least one subdirectory
    means a file could live one level further down, so absence is NOT proved.
    A root that cannot be listed is treated the same way: ignorance is never
    reported as absence.
    """
    limit = search_depth() if depth is None else depth
    last = None
    for current, level in enumerate(_levels(root, limit)):
        last = level
        if current >= limit:
            break
    for rel in last or []:
        base = os.path.join(root, rel) if rel else root
        try:
            names = os.listdir(base)
        except OSError:
            return True
        for name in names:
            if os.path.isdir(os.path.join(base, name)):
                return True
    return False


def resolve(evidence, root, depth=None):
    """AC-BEDP1/AC-BEDP3/AC-BEDP4: the pile, or a refusal that names why."""
    if not isinstance(evidence, str) or not evidence:
        raise BareEvidenceDeepPileError(
            E_BEDP_BAD_EVIDENCE, "evidence names no file")
    limit = search_depth() if depth is None else depth
    found = piles_for(evidence, root, limit)
    if len(found) > 1:
        raise BareEvidenceDeepPileError(
            E_BEPR_AMBIGUOUS,
            "evidence %r lives in piles %s within depth %d"
            % (evidence, ",".join(found), limit))
    if found:
        return found[0]
    if continues_below(root, limit):
        raise BareEvidenceDeepPileError(
            E_BEDP_BEYOND_DEPTH,
            "evidence %r is not within the searched depth %d of root %r, "
            "which continues below that depth" % (evidence, limit, root))
    raise BareEvidenceDeepPileError(
        E_BEPR_NOT_FOUND,
        "evidence %r is not under root %r and the tree does not continue "
        "below depth %d, so its absence is proved"
        % (evidence, root, limit))


def reading(evidence, root=".", depth=None):
    """AC-BEDP5: the pinned keys, never raising for a refusal."""
    limit = search_depth() if depth is None else depth
    try:
        pile = resolve(evidence, root, limit)
    except BareEvidenceDeepPileError as exc:
        return {"evidence": evidence, "root": root, "depth": limit,
                "pile": "", "verdict": "REFUSED", "code": exc.code,
                "detail": exc.detail}
    return {"evidence": evidence, "root": root, "depth": limit,
            "pile": pile, "verdict": "RESOLVED", "code": "",
            "detail": "pile=%s" % pile}


def exit_code(report):
    """0 resolved, 2 refusal, 3 an unreadable root - in that precedence."""
    if report["code"] == E_BEDP_BAD_ROOT:
        return 3
    if report["verdict"] == "REFUSED":
        return 2
    return 0


def render(report):
    out = ["BARE EVIDENCE DEEP PILE evidence=%s root=%s depth=%d"
           % (report["evidence"], report["root"], report["depth"])]
    out.append("  pile=%s verdict=%s"
               % (report["pile"] or "-", report["verdict"]))
    if report["code"]:
        out.append("  code=%s %s" % (report["code"], report["detail"]))
    return "\n".join(line.rstrip() for line in out)


def to_json(report):
    ordered = {}
    for key in READING_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    operation = False
    as_json = False
    root = "."
    depth = None
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
                sys.stdout.write("E_BEDP_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg == "--depth":
            index += 1
            if index >= len(argv) or not argv[index].isdigit():
                sys.stdout.write("E_BEDP_BAD_ARGS: --depth needs an integer\n")
                return 5
            depth = int(argv[index])
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif evidence is None and not arg.startswith("-"):
            evidence = arg
        else:
            sys.stdout.write("E_BEDP_BAD_ARGS: unexpected %r\n" % arg)
            return 5
        index += 1
    if not operation or not evidence:
        sys.stdout.write(USAGE)
        return 5
    if not os.path.isdir(root) or not os.access(root, os.R_OK):
        report = {"evidence": evidence, "root": root,
                  "depth": search_depth() if depth is None else depth,
                  "pile": "", "verdict": "REFUSED", "code": E_BEDP_BAD_ROOT,
                  "detail": "root %r cannot be read" % root}
        if as_json:
            sys.stdout.write(to_json(report))
        else:
            sys.stdout.write(render(report) + "\n")
        return 3
    report = reading(evidence, root, depth)
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))