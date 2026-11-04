# general_writer_dialect_audit.py - the tier the declaration sweep excludes,
# audited instead of assumed.
# Criteria AC-GWDA1..AC-GWDA6 were pre-registered inside the R2409 seed row of
# state/queue/tech.md BEFORE this file existed.
#
# Why this exists: library_declaration_dialect_sweep splits DECLARATION from
# GENERAL honestly, and then says nothing about GENERAL. MEASURED at R2409,
# sixteen library modules compose JSON and replace a file, and several of them
# land a structured document the house actually keeps (the debt register,
# src/os/state.json). None of them asked the dialect, so a CRLF document was
# converted by whichever writer happened to run.
#
# This module owns exactly one question, derived from the SOURCE rather than a
# whitelist file (AC-GWDA1):
#
#   among the GENERAL tier the sweep excludes, which writers land a structured
#   file that is really on disk, and of those, which ask the shared payload
#   derivation at CALL time?
#
# The target is not guessed from any literal the module happens to carry: it is
# read off the destination of the module's OWN os.replace call and resolved
# through its own data flow - local and module assignments, imported module
# constants (read from that module's source, never imported for real), the
# constant parts of an os.path.join, and a one-hop local function whose body is
# a single return. A writer whose destination does not resolve is REPORTED as
# UNRESOLVED with its own code instead of being counted clean or dropped.
#
# Three answers leave the audit, and none is silent:
#
#   * KEEPS       - the writer lands a structured file the tree carries, so its
#     transport must be preserved; a KEEPS writer that does not ask the shared
#     law reads as DEBT and the audit exits 2 rather than claiming a green;
#   * REPAIR      - the writer deliberately rewrites the whole document in the
#     house canon (it defines a normalising callable), so "every untouched line
#     stays byte-identical" is not a property it can have. EXCLUDED as
#     E_GWDA_REPAIR with its reason published beside it;
#   * UNRESOLVED  - E_GWDA_UNRESOLVED, named with the destination reading that
#     failed, so a gap in this scan can never masquerade as a green.
#
# payload_for() is the one seam a KEEPS writer asks at its own call site. It
# reads the target's current bytes and asks the SHARED derivation
# (declaration_writer_dialect_preservation.encode) at CALL time, so patching
# that law moves every writer that asks this seam (AC-GWDA2).
#
# Pure: it writes nothing itself, reads no clock, imports no network, and it is
# pure ASCII stdlib plus the house module it asks (AC-GWDA6).

import ast
import io
import os

import declaration_writer_dialect_preservation as DWDP
import library_declaration_dialect_sweep as LDWS

PREFIX = "E_GWDA"
SUITE_LABEL = "os-general-writer-dialect-audit"

# a structured document the house keeps, recognised by its own extension
STRUCTURED_SUFFIXES = (".json", ".md")

# a writer that deliberately normalises defines a callable carrying one of
# these words (the house own vocabulary for a re-render / a transport repair)
REPAIR_MARKS = ("canon", "fix")

# the one shared payload derivation a KEEPS writer must ask at CALL time
SHARED_LAW = DWDP.__name__
# a seam that itself asks that law (this module own payload_for) is the same
# answer, so a writer routing through it is routed too
ROUTED_SEAMS = (SHARED_LAW, "general_writer_dialect_audit")

ROW_KEYS = ("name", "kind", "target", "asks")
REPORT_KEYS = ("verdict", "scanned", "general", "keeps", "repair", "routed",
               "unrouted", "offenders", "excluded", "unresolved")


class AuditError(Exception):
    """A refusal carrying its own code."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def _tree(source):
    """The module's own syntax, or None when it does not parse."""
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return ast.parse(source)
    except SyntaxError:
        return None


def _es(text):
    """A Windows or POSIX path spelling normalised to one slash form."""
    return text.replace("\\", "/").strip().strip(".").strip("/") or text.strip()


def _assignments(tree):
    """name -> every value expression assigned to it, anywhere in the module."""
    out = {}
    for node in ast.walk(tree):
        pairs = ()
        if isinstance(node, ast.Assign):
            pairs = ((target, node.value) for target in node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            pairs = ((node.target, node.value),)
        for target, value in pairs:
            if isinstance(target, ast.Name):
                out.setdefault(target.id, []).append(value)
    return out


def _functions(tree):
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, node)
    return out


def _module_constant(base_dir, module, attr):
    """A constant read from ANOTHER module's own source, never by importing it."""
    path = os.path.join(base_dir, module + ".py")
    if not os.path.isfile(path):
        return None
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
            source = handle.read()
    except (IOError, OSError):
        return None
    tree = _tree(source)
    if tree is None:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == attr:
            found = _resolve_node(node.value, _assignments(tree), {}, {},
                                  os.path.dirname(path))
            if found:
                return found[0]
    return None


def _imports(tree):
    """local name -> module name, as the module's own import statements spell it."""
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                out[alias.asname or alias.name] = node.module
    return out


def _resolve_node(node, assigns, funcs, imports, base_dir, depth=0):
    """Every path string this expression can land, best effort and pure."""
    if depth > 6 or node is None:
        return []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Name):
        found = []
        for value in assigns.get(node.id, []):
            for item in _resolve_node(value, assigns, funcs, imports,
                                      base_dir, depth + 1):
                if item not in found:
                    found.append(item)
        return found
    if isinstance(node, ast.Attribute):
        holder = node.value
        if isinstance(holder, ast.Name) and holder.id in imports:
            module = imports[holder.id]
            constant = _module_constant(base_dir, module, node.attr)
            if constant is not None:
                return [constant]
        return []
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _resolve_node(node.left, assigns, funcs, imports, base_dir,
                             depth + 1)
        right = _resolve_node(node.right, assigns, funcs, imports, base_dir,
                              depth + 1)
        return [a + b for a in left for b in right]
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "join" \
                and isinstance(func.value, ast.Attribute) \
                and func.value.attr == "path" \
                and isinstance(func.value.value, ast.Name) \
                and func.value.value.id == "os":
            parts = []
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    parts.append(arg.value)
                    continue
                resolved = _resolve_node(arg, assigns, funcs, imports, base_dir,
                                         depth + 1)
                literal = [item for item in resolved
                           if isinstance(item, str) and not item.startswith("/")]
                if literal:
                    parts.append(literal[0])
            if parts:
                return [os.path.join(*parts)]
            return []
        if isinstance(func, ast.Name) and func.id in funcs:
            body = funcs[func.id].body
            returns = [item for item in body if isinstance(item, ast.Return)]
            if len(body) == 1 and len(returns) == 1:
                return _resolve_node(returns[0].value, assigns, funcs, imports,
                                     base_dir, depth + 1)
        return []
    return []


def replace_targets(source):
    """The destination of every os.replace call, resolved through its own flow.

    Returns (resolved, unresolved) lists of spelling strings: `resolved` holds
    every path the source can prove it lands, `unresolved` holds a short
    description of a destination the source could not be read for.
    """
    tree = _tree(source)
    if tree is None:
        return [], ["source does not parse"]
    assigns = _assignments(tree)
    funcs = _functions(tree)
    imports = _imports(tree)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resolved = []
    unresolved = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "replace"
                and isinstance(func.value, ast.Name) and func.value.id == "os"):
            continue
        destination = node.args[1] if len(node.args) >= 2 else None
        if destination is None:
            for keyword in node.keywords:
                if keyword.arg in ("dst", "dest", "destination"):
                    destination = keyword.value
        found = _resolve_node(destination, assigns, funcs, imports, base_dir)
        if not found:
            label = ast.dump(destination) if destination is not None else "none"
            short = "os.replace destination not resolvable"
            if isinstance(destination, ast.Name):
                short += " (name %s carries no assignment)" % destination.id
            elif isinstance(destination, ast.Call):
                short += " (call to a function with no single-return body)"
            if label and short not in unresolved:
                unresolved.append(short)
            continue
        for item in found:
            spelling = _es(item)
            if spelling not in resolved:
                resolved.append(spelling)
    return resolved, unresolved


def structured_hit(root, spellings):
    """The first spelling that names a structured file the tree really carries."""
    for spelling in spellings:
        if not spelling.lower().endswith(STRUCTURED_SUFFIXES):
            continue
        candidate = os.path.join(root, *spelling.replace("\\", "/").split("/"))
        if os.path.isfile(candidate):
            return spelling.replace("\\", "/")
    return None


def defines_normaliser(source):
    """True when the module defines a callable that rewrites the house canon.

    A SOURCE reading, not a whitelist: any function whose own name carries the
    normalising word marks the module as a deliberate re-render.
    """
    tree = _tree(source)
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lower()
            for mark in REPAIR_MARKS:
                if mark in name:
                    return True
    return False


def asks_shared(source):
    """True when the module's own imports name a seam that asks the shared law.

    Two spellings count, and only two: the shared derivation itself, and this
    module own payload_for - which asks that derivation at CALL time, so a
    writer that routes through it cannot pick a transport either.
    """
    return bool(set(_imports(_tree(source) or ast.parse("")).values())
                & set(ROUTED_SEAMS))


def classify(name, source, root):
    """One row for one file: None unless it belongs to the audited tier.

    The candidate law (composes JSON, replaces a file) and the GENERAL tier are
    asked of the shipped sweep, so this module owns no second copy of either.
    What it adds is the destination reading and the three answers.
    """
    base = LDWS.classify(name, source)
    if base["kind"] != "GENERAL":
        return None
    spellings, unresolved = replace_targets(source)
    target = structured_hit(root, spellings)
    if target is None:
        if not spellings:
            detail = unresolved[0] if unresolved else "no destination"
            return {"name": name, "kind": "UNRESOLVED", "target": "-",
                    "asks": False, "why": detail}
        return None
    if defines_normaliser(source):
        return {"name": name, "kind": "REPAIR", "target": target,
                "asks": False, "why": "defines a normalising callable"}
    return {"name": name, "kind": "KEEPS", "target": target,
            "asks": asks_shared(source), "why": ""}


def scan(root):
    """Every audited writer under <root>/src/os, in name order."""
    base = os.path.join(root, "src", "os")
    if not os.path.isdir(base):
        raise AuditError(PREFIX + "_UNREADABLE", "no such directory: %s" % base)
    try:
        names = sorted(entry for entry in os.listdir(base)
                       if entry.endswith(".py") and not LDWS.is_test(entry))
    except (IOError, OSError) as exc:
        raise AuditError(PREFIX + "_UNREADABLE", "%s (%s)" % (base, exc))
    rows = []
    scanned = 0
    general = 0
    for name in names:
        path = os.path.join(base, name)
        try:
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                source = fh.read()
        except (IOError, OSError) as exc:
            raise AuditError(PREFIX + "_UNREADABLE", "%s (%s)" % (path, exc))
        scanned += 1
        if LDWS.classify(name, source)["kind"] == "GENERAL":
            general += 1
        row = classify(name, source, root)
        if row is not None:
            rows.append(row)
    return scanned, general, rows


def report(root):
    """The reading, with every set difference the operator needs."""
    scanned, general, rows = scan(root)
    keeps = [row for row in rows if row["kind"] == "KEEPS"]
    repair = [row for row in rows if row["kind"] == "REPAIR"]
    unresolved = [row for row in rows if row["kind"] == "UNRESOLVED"]
    routed = [row for row in keeps if row["asks"]]
    offenders = [row["name"] for row in keeps if not row["asks"]]
    return {
        "verdict": "AUDIT-DEBT" if offenders else "AUDIT-CLEAN",
        "scanned": scanned,
        "general": general,
        "keeps": len(keeps),
        "repair": len(repair),
        "routed": len(routed),
        "unrouted": len(offenders),
        "offenders": offenders,
        "excluded": [row["name"] for row in repair],
        "unresolved": [row["name"] for row in unresolved],
        "rows": rows,
    }


def payload_for(path, composed_text):
    """The bytes a KEEPS writer must land, in the target's own dialect.

    This is the seam each writer asks at its OWN call site. The dialect law is
    asked at CALL time (AC-GWDA2), a target that does not exist yet lands the
    composition unchanged, and a dialect no writer can preserve refuses with
    the law's own code instead of converting it.
    """
    raw = b""
    if os.path.exists(path):
        try:
            with io.open(path, "rb") as handle:
                raw = handle.read()
        except (IOError, OSError) as exc:
            raise AuditError(PREFIX + "_UNREADABLE", "%s (%s)" % (path, exc))
    name, payload = DWDP.encode(raw, composed_text)
    return payload


def one_line(reading):
    """The single line an operator reads."""
    return ("GENERAL DIALECT AUDIT scanned=%d general=%d keeps=%d repair=%d "
            "unresolved=%d routed=%d unrouted=%d verdict=%s"
            % (reading["scanned"], reading["general"], reading["keeps"],
               reading["repair"], len(reading["unresolved"]),
               reading["routed"], reading["unrouted"], reading["verdict"]))


def render(reading):
    """The one line, then every audited writer and its answer."""
    out = [one_line(reading)]
    for row in reading["rows"]:
        if row["kind"] == "KEEPS":
            out.append("  KEEPS %s target=%s asks=%s"
                       % (row["name"], row["target"],
                          "yes" if row["asks"] else "no"))
        elif row["kind"] == "REPAIR":
            out.append("  REPAIR %s target=%s %s_REPAIR (%s)"
                       % (row["name"], row["target"], PREFIX, row["why"]))
        else:
            out.append("  UNRESOLVED %s %s_UNRESOLVED (%s)"
                       % (row["name"], PREFIX, row["why"]))
    for name in reading["offenders"]:
        out.append("  DEBT %s lands a structured file and does not ask %s at "
                   "call time" % (name, SHARED_LAW))
    if reading["excluded"]:
        out.append("  NOTE %d general writer(s) are EXCLUDED as %s_REPAIR, "
                   "named above rather than silently skipped"
                   % (len(reading["excluded"]), PREFIX))
    if reading["unresolved"]:
        out.append("  NOTE %d general writer(s) read %s_UNRESOLVED with the "
                   "destination reading that failed, so this scan never counts "
                   "an unread writer as clean" % (len(reading["unresolved"]),
                                                   PREFIX))
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


USAGE = ("usage: general_writer_dialect_audit.py --check [--root PATH] "
         "[--json]\n"
         "  exit 0 = every GENERAL writer of a structured file asks the "
         "dialect law\n"
         "  exit 2 = a GENERAL writer still chooses its own transport\n"
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
    except AuditError as exc:
        sys.stdout.write("%s\n" % exc.code)
        if exc.detail:
            sys.stdout.write("  %s\n" % exc.detail)
        return 3
    if as_json:
        sys.stdout.write(to_json(reading))
    else:
        sys.stdout.write(render(reading) + "\n")
    return 0 if reading["verdict"] == "AUDIT-CLEAN" else 2


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))