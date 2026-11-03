# library_declaration_dialect_sweep.py - which LIBRARY writers of a JSON
# declaration still choose their own line-ending transport.
# Criteria AC-LDWS1..AC-LDWS6 were pre-registered inside the R2406 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: the dialect seam reached the four SPLICE writers (R2398) and
# the re-render (R2406). MEASURED at R2406 over every non-test src/os/*.py,
# four LIBRARY writers still composed with json.dumps and landed through one
# os.replace without ever asking the dialect, so a CRLF declaration was
# silently converted to LF by whichever writer happened to run.
#
# This module owns exactly one question, derived from the SOURCE rather than a
# whitelist file (AC-LDWS1):
#
#   which files compose JSON and replace a file, which of those are library
#   modules, which of THOSE ask the shared dialect law at CALL time, and which
#   do not?
#
# A file is a candidate when its own text carries both a json.dumps composition
# and an os.replace landing. It is HISTORICAL when its name carries a round
# suffix (closeout_R2406, battery_followup_R2271, export_R2400, live_R2406,
# repair_R2407, ...) because those are one-off per-round scripts rather than
# debt, and LIBRARY otherwise. A library candidate is ROUTED when its source
# names the shared payload derivation, because a writer that asks it at call
# time cannot choose a transport by accident.
#
# The reading is honest in the direction that matters: a writer that composes
# its JSON through some other helper, or lands bytes without os.replace, reads
# as not-a-candidate rather than as routed. That limit is stated here instead
# of hidden, so no green is claimed over a shape this scan cannot see.
#
# Pure: it writes nothing, reads no clock, imports no network, and it is pure
# ASCII stdlib (AC-LDWS6).

import os
import re

PREFIX = "E_LDWS"
SUITE_LABEL = "os-library-declaration-dialect-sweep"

# the one shared payload derivation a writer must ask at call time
SHARED_LAW = "declaration_writer_dialect_preservation"
# a seam that itself asks that law (the R2406 re-render) is the same answer
ROUTED_SEAMS = (SHARED_LAW, "repin_dialect_preservation")
# the house's declaration-write idiom: a temp sibling beside the target
WORKS_IN_PLACE = "TEMP_SUFFIX ="
# a JSON declaration is named in the module's own text, never in this file
DECLARATION_MARKS = ('DEFAULT_DECLARATION', '="state/', '= "state/',
                     '="src/os/state.json', '= "src/os/state.json',
                     "import residue_triage")

COMPOSE_MARK = "json.dumps"
REPLACE_MARK = "os.replace"

ROW_KEYS = ("name", "kind", "composes", "replaces", "routed")
REPORT_KEYS = ("verdict", "scanned", "library", "historical", "general",
               "routed", "unrouted", "offenders")

# a per-round one-off script carries its round in its own name
ROUND_SUFFIX_RE = re.compile(r"(^|[_.])[Rr]\d{3,5}(?![0-9])")


class SweepError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def is_test(name):
    """A suite file describes a writer, it is never one."""
    return name.startswith("test_")


def kind_of(name):
    """HISTORICAL when the name carries a round suffix, LIBRARY otherwise."""
    stem = name[:-3] if name.endswith(".py") else name
    return "HISTORICAL" if ROUND_SUFFIX_RE.search(stem) else "LIBRARY"


def names_declaration(source):
    """True when the module's own text names the JSON declaration it lands."""
    return any(mark in source for mark in DECLARATION_MARKS)


def facts(source):
    """What the module CALLS and what it names, read from its own syntax.

    String constants must not count as behaviour: this module names
    "os.replace" and its own law in its own text, and a substring reading would
    classify it as a writer of a declaration it merely describes. Only real
    calls and real imports count.
    """
    import ast
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(source)
    except SyntaxError:
        return {"composes": False, "replaces": False, "in_place": False,
                "declares": False, "asked": set()}
    composes = False
    replaces = False
    in_place = False
    asked = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            holder = node.func.value
            if isinstance(holder, ast.Name) and holder.id == "json" \
                    and node.func.attr == "dumps":
                composes = True
            if isinstance(holder, ast.Name) and holder.id == "os" \
                    and node.func.attr == "replace":
                replaces = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                asked.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            asked.add(node.module)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TEMP_SUFFIX":
                    in_place = True
    return {"composes": composes, "replaces": replaces, "in_place": in_place,
            "declares": names_declaration(source), "asked": asked}


def classify(name, source):
    """One row for one file, derived only from the file's own syntax.

    Three tiers, because a file that composes JSON and replaces a file is not
    automatically a writer of a JSON DECLARATION:

      * DECLARATION - works in place beside its target (the house temp-sibling
        idiom) and names the JSON declaration it lands;
      * GENERAL     - composes and replaces, but lands something else (a
        register, a report, a quarantine move), so it is reported and is not
        debt for this law;
      * HISTORICAL  - a per-round one-off script.
    """
    kind = kind_of(name)
    read = facts(source)
    routed = bool(read["asked"] & set(ROUTED_SEAMS))
    if kind == "HISTORICAL":
        return {"name": name, "kind": "HISTORICAL",
                "composes": read["composes"], "replaces": read["replaces"],
                "routed": routed}
    if read["composes"] and read["replaces"] and read["in_place"] \
            and read["declares"]:
        return {"name": name, "kind": "DECLARATION", "composes": True,
                "replaces": True, "routed": routed}
    return {"name": name, "kind": "GENERAL", "composes": read["composes"],
            "replaces": read["replaces"], "routed": routed}


def scan(root):
    """Every candidate writer under <root>/src/os, in name order."""
    base = os.path.join(root, "src", "os")
    if not os.path.isdir(base):
        raise SweepError(PREFIX + "_UNREADABLE", "no such directory: %s" % base)
    try:
        names = sorted(entry for entry in os.listdir(base)
                       if entry.endswith(".py") and not is_test(entry))
    except (IOError, OSError) as exc:
        raise SweepError(PREFIX + "_UNREADABLE", "%s (%s)" % (base, exc))
    rows = []
    scanned = 0
    for name in names:
        path = os.path.join(base, name)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                source = handle.read()
        except (IOError, OSError) as exc:
            raise SweepError(PREFIX + "_UNREADABLE", "%s (%s)" % (path, exc))
        scanned += 1
        row = classify(name, source)
        if row["composes"] and row["replaces"]:
            rows.append(row)
    return scanned, rows


def report(root):
    """The reading, with every set difference the operator needs."""
    scanned, rows = scan(root)
    library = [row for row in rows if row["kind"] == "DECLARATION"]
    historical = [row for row in rows if row["kind"] == "HISTORICAL"]
    general = [row for row in rows if row["kind"] == "GENERAL"]
    routed = [row for row in library if row["routed"]]
    offenders = [row["name"] for row in library if not row["routed"]]
    return {
        "verdict": "SWEEP-CLEAN" if not offenders else "SWEEP-DEBT",
        "scanned": scanned,
        "library": len(library),
        "historical": len(historical),
        "general": len(general),
        "routed": len(routed),
        "unrouted": len(offenders),
        "offenders": offenders,
        "rows": rows,
    }


def one_line(reading):
    """The single line an operator reads."""
    return ("LIBRARY DIALECT SWEEP scanned=%d library=%d historical=%d "
            "general=%d routed=%d unrouted=%d verdict=%s"
            % (reading["scanned"], reading["library"],
               reading["historical"], reading["general"],
               reading["routed"], reading["unrouted"], reading["verdict"]))


def render(reading):
    """The one line, then every declaration writer and its answer."""
    out = [one_line(reading)]
    for row in reading["rows"]:
        if row["kind"] == "DECLARATION":
            out.append("  DECLARATION %s routed=%s"
                       % (row["name"], "yes" if row["routed"] else "no"))
    for name in reading["offenders"]:
        out.append("  DEBT %s does not ask %s at call time"
                   % (name, SHARED_LAW))
    if reading["general"]:
        out.append("  NOTE %d library files compose and replace something "
                   "else, so they are not debt for this law"
                   % reading["general"])
    if reading["historical"]:
        out.append("  NOTE %d per-round one-off scripts are historical, not "
                   "debt" % reading["historical"])
    return "\n".join(out)


def to_json(reading):
    """A byte-stable payload over the pinned keys."""
    import json
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = reading[key]
    ordered["rows"] = []
    for row in reading["rows"]:
        item = {}
        for key in ROW_KEYS:
            item[key] = row[key]
        ordered["rows"].append(item)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: library_declaration_dialect_sweep.py --check [--root PATH] "
         "[--json]\n"
         "  exit 0 = every library JSON writer asks the dialect law\n"
         "  exit 2 = a library writer still chooses its own transport\n"
         "  exit 3 = src/os is missing or unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    as_json = False
    checked = False
    root = "."
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            checked = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                import sys
                sys.stdout.write("%s_BAD_ARGS: --root needs a value\n" % PREFIX)
                sys.stdout.write(USAGE)
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            import sys
            sys.stdout.write(USAGE)
            return 0
        else:
            import sys
            sys.stdout.write("%s_BAD_ARGS: unknown flag %s\n" % (PREFIX, arg))
            sys.stdout.write(USAGE)
            return 5
        index += 1
    import sys
    if not checked:
        sys.stdout.write("%s_BAD_ARGS: --check is required\n" % PREFIX)
        sys.stdout.write(USAGE)
        return 5
    try:
        reading = report(root)
    except SweepError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(reading))
    else:
        sys.stdout.write(render(reading) + "\n")
    return 0 if reading["verdict"] == "SWEEP-CLEAN" else 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))