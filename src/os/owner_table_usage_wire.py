"""owner_table_usage_wire (R2399; criteria pinned inside the R2390 tech seed row
of state/queue/tech.md:460 BEFORE this code).

Why this exists: R2390 shipped owner_table_parity, which reads every
module-level UPPER_CASE constant that carries flag-shaped literals as a
declared own-flag table. That law is right about a tool whose table really is
an argument table and WRONG about a tool whose DATA happens to look like one.
Measured at HEAD before this window:

    evidence_R2372.py  ARGS  = ["--round", "R2372", "--until", "R2390", ...]
    r2140_fold.py      ARGS  = [sys.executable, TOOL, "fold", "--round", ...]
    retry_naming.py    LEGACY_RERUN_SUFFIXES = ("-run2", "-2")

all three read PARITY-DISAGREES with their data listed as missing_in_parser,
while runner_arg_guard.py reads a REAL drift (its help table omits --help and
the whole --guard family) and battery_followup.py reads AGREES. A reader that
cries wolf on invocation data is a reader an operator stops believing.

This module is the missing notion: a constant is a TABLE only when a help or
usage path in the same file reads it. The usage path is measured from the
source, never whitelisted:

  1. a module-level function whose own name carries "usage" or "help", or
  2. a function that emits a usage text (a call whose string argument starts
     with or carries "usage:"), because several shipped tools print their
     usage from main() instead of a helper;
  3. inside such a path, a constant counts when it is named directly or
     through ONE hop (a local alias bound to the module constant), and when
     the path hands the MODULE itself to a renderer (sys.modules[__name__])
     every declared table of that module counts, because that renderer is
     deriving the help block from exactly those tables.

Everything else - the table derivation, the parser side, the verdict words,
the JSON keys and every printed line - is owner_table_parity's, asked at CALL
time, so this module adds a notion and never a second wheel. owner_table_parity
is untouched: it still answers the question it was built for (does the help
table match the parser) and this reader answers which constants ARE that
table.

Measured limits, stated rather than hidden: the usage path is found by name and
by emitted usage text, so a tool that renders a help block from a constant
inside a function named neither way reads NO-TABLE even though it may own a
real table - a false NEGATIVE is the honest failure direction for a reader
whose whole job is to stop false positives. A usage path that reaches a
constant through a call chain longer than one local alias is also not counted,
for the same reason.

CLI:

    python owner_table_usage_wire.py <tool.py> [--json]
    python owner_table_usage_wire.py --help

Exit codes: 0 PARITY-AGREES, 2 PARITY-DISAGREES or NO-TABLE, 3 tool path
missing or unreadable, 5 bad this-tool flags.

Stdlib only, ASCII source, zero network, no clock, read-only.
"""

import ast
import io
import json
import os
import sys

LABEL = "OWNER TABLE USAGE WIRE"

USAGE_NAME_WORDS = ("usage", "help")
USAGE_TEXT_MARKERS = ("usage:", "usage :")

E_OTUW_UNREADABLE = "E_OTUW_UNREADABLE"
E_OTUW_NO_TABLE = "E_OTUW_NO_TABLE"
E_OTUW_BAD_FLAG = "E_OTUW_BAD_FLAG"

EXIT_AGREES = 0
EXIT_REFUSED = 2
EXIT_UNREADABLE = 3
EXIT_BAD_FLAG = 5


def _law():
    """The shipped owner-table law, imported at CALL time.

    One owner of the table derivation, the parser side, the verdict words and
    the JSON keys: patching it moves this reader too (AC-OTUW4).
    """
    import owner_table_parity
    return owner_table_parity


def _functions(tree):
    """Every function defined anywhere in the module."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(node)
    return found


def _emits_usage_text(node):
    """True when this function emits a usage text through any call."""
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        for argument in list(sub.args) + [kw.value for kw in sub.keywords]:
            if isinstance(argument, ast.Constant) and \
                    isinstance(argument.value, str):
                lowered = argument.value.lower()
                if any(marker in lowered for marker in USAGE_TEXT_MARKERS):
                    return True
    return False


def usage_paths(tree):
    """The functions of this module that describe its own argument surface.

    Measured from the source: the name carries usage/help, or the body emits a
    usage text. Nothing is whitelisted and no tool name is hard-coded
    (AC-OTUW3).
    """
    paths = []
    for node in _functions(tree):
        name = node.name.lower()
        if any(word in name for word in USAGE_NAME_WORDS):
            paths.append(node)
        elif _emits_usage_text(node):
            paths.append(node)
    return paths


def hands_whole_module(node):
    """True when this path hands the MODULE itself to a renderer.

    battery_followup.help_text() returns HW.usage_text(module=sys.modules[
    __name__]): the help block is derived from that module's own tables, so
    every declared table of the module is read by the usage path - one hop,
    measured at the call rather than assumed from a name.
    """
    for sub in ast.walk(node):
        if isinstance(sub, ast.Subscript):
            value = sub.value
            if isinstance(value, ast.Attribute) and value.attr == "modules":
                index = sub.slice
                if isinstance(index, ast.Name) and index.id == "__name__":
                    return True
            if isinstance(value, ast.Attribute) and value.attr == "modules":
                index = sub.slice
                if isinstance(index, ast.Constant) and \
                        index.value == "__name__":
                    return True
    return False


def named_constants(node, constants):
    """Module constants this function names, directly or through one alias."""
    named = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in constants:
            named.add(sub.id)
        elif isinstance(sub, ast.Attribute) and sub.attr in constants:
            named.add(sub.attr)
        elif isinstance(sub, ast.Assign):
            if isinstance(sub.value, ast.Name) and sub.value.id in constants:
                for target in sub.targets:
                    if isinstance(target, ast.Name):
                        named.add(sub.value.id)
    return named


def used_table_names(tree, constants):
    """The declared-table names a usage path actually reads.

    A path that hands the module to a renderer makes every declared table
    usable, because the renderer's whole job is to derive the help block from
    them; otherwise only the names the path itself carries count.
    """
    names = set()
    whole = False
    for node in usage_paths(tree):
        if hands_whole_module(node):
            whole = True
        names |= named_constants(node, constants)
    if whole:
        return set(constants)
    return names


def declared_usage_table(tree, constants=None, usage_names=None):
    """The flags carried by the declared tables a usage path reads.

    The flag literals and the table shape are the shipped law's (the constants
    map comes from owner_table_parity.module_constants, so a patched
    derivation moves this table too); only WHICH constants join is this
    reader's answer.
    """
    law = _law()
    if constants is None:
        constants = law.module_constants(tree)
    if usage_names is None:
        usage_names = used_table_names(tree, constants)
    flags = []
    for name in constants:
        if name not in usage_names:
            continue
        for literal in constants[name]:
            if literal not in flags:
                flags.append(literal)
    return flags


def read_tool(path):
    """The tool's source text, or None when it cannot be read."""
    try:
        with io.open(path, encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError):
        return None


def audit(path):
    """Read one tool and return its usage-wired parity reading."""
    law = _law()
    source = read_tool(path)
    if source is None:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    constants = law.module_constants(tree)
    table = declared_usage_table(tree, constants)
    if not table:
        return {"tool": os.path.basename(path), "table": [], "parser": [],
                "prefix": [], "missing_in_table": [],
                "missing_in_parser": [], "verdict": law.VERDICT_NO_TABLE}
    exact, prefix = law.accepted_tokens(tree, constants)
    return law.classify(os.path.basename(path), table, exact, prefix)


def render(payload, as_json):
    """One stable line, or byte-stable JSON over the shipped key set."""
    law = _law()
    if as_json:
        body = dict((key, payload[key]) for key in law.JSON_KEYS)
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    if payload["verdict"] == law.VERDICT_NO_TABLE:
        return "%s %s verdict=%s %s" % (
            LABEL, payload["tool"], law.VERDICT_NO_TABLE, E_OTUW_NO_TABLE)
    if payload["verdict"] == law.VERDICT_AGREES:
        return "%s %s verdict=%s table=%d parser=%d" % (
            LABEL, payload["tool"], law.VERDICT_AGREES,
            len(payload["table"]), len(payload["parser"]))
    return "%s %s verdict=%s missing_in_table=[%s] missing_in_parser=[%s]" % (
        LABEL, payload["tool"], law.VERDICT_DISAGREES,
        ",".join(payload["missing_in_table"]),
        ",".join(payload["missing_in_parser"]))


USAGE = ("usage: owner_table_usage_wire.py <tool.py> [--json]\n"
         "       owner_table_usage_wire.py --help\n")


def main(argv):
    args = list(argv[1:])
    as_json = False
    target = ""
    for token in args:
        if token == "--help":
            print(USAGE, end="", flush=True)
            return EXIT_AGREES
        if token == "--json":
            as_json = True
            continue
        if token.startswith("-"):
            print("%s %s %s" % (LABEL, E_OTUW_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        if target:
            print("%s %s %s" % (LABEL, E_OTUW_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        target = token
    if not target:
        print("%s %s <tool.py>" % (LABEL, E_OTUW_BAD_FLAG), flush=True)
        return EXIT_BAD_FLAG
    if not os.path.isfile(target):
        print("%s %s %s" % (LABEL, E_OTUW_UNREADABLE, target), flush=True)
        return EXIT_UNREADABLE
    payload = audit(target)
    if payload is None:
        print("%s %s %s" % (LABEL, E_OTUW_UNREADABLE, target), flush=True)
        return EXIT_UNREADABLE
    print(render(payload, as_json), flush=True)
    if payload["verdict"] == _law().VERDICT_AGREES:
        return EXIT_AGREES
    return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv))