"""owner_table_parity (R2390; criteria pinned inside the R2383 tech seed row of
state/queue/tech.md:445 BEFORE this code).

Why this exists: R2383 gave a tool's OWN argument block one renderer
(own_usage_block_renderer), so the SHAPE is no longer copied. The TABLE that
shape is rendered from is still hand-written beside the parser that actually
accepts the tokens. Measured at HEAD before this window:

    runner_arg_guard.GUARD_FLAGS = ("--json",)
    runner_arg_guard.main()      accepts "--json", "--guard-help" and "--"
                                 as literals inside its own loop

so a flag added to the loop silently never appears in the help block, and no
reader compares the two sides.

This module is that reader. It reads ONE tool file, derives the declared
own-flag table from the module-level UPPER_CASE constants that carry flag
literals (a tuple, a dict of flag -> dest, or a help-only tuple - the SHAPE is
measured, not prescribed) and the accepted tokens from the parser source
itself (literal comparisons, membership tests - including membership of a
module constant, resolved one hop - and startswith prefixes over a
token-name), and names every flag present on one side and missing from the
other. It never rewrites the tool and never whitelists a tool - the verdict is
a property of the code it is pointed at.

Measured limits, stated rather than hidden (both found by running it on the
real tree this window): a flag must be ONE token, so a prose constant such as
a markdown backlog row is not read as a table; and a tool whose DATA happens
to carry flag-shaped literals (several historical round scripts) is read as a
one-sided table because this reader has no notion of the constant being used
by a help path - that gap is seeded as the successor row rather than claimed
as a clean tree.

CLI:

    python owner_table_parity.py <tool.py> [--json]
    python owner_table_parity.py --help

Exit codes: 0 PARITY-AGREES, 2 PARITY-DISAGREES or NO-TABLE, 3 tool path
missing or unreadable, 5 bad this-tool flags.

Stdlib only, ASCII source, zero network, no clock, read-only: this module
opens the tool for reading and creates nothing.

CRITERIA LABEL NOTE (measurement, not preference): the R2383 seed row pinned
the labels AC-OTP1..AC-OTP6 / E_OTP, but AC-OTP1..AC-OTP6 and E_OTP_* are
already owned by src/os/orphan_promote.py at HEAD, so this window pins the
free labels AC-OTPP1..AC-OTPP6 / E_OTPP_* for the SAME six substantive
criteria - named here rather than silently sharing a prefix.
"""

import ast
import io
import json
import os
import sys

LABEL = "OWNER TABLE PARITY"
TABLE_NAME_RE = None  # set in _is_table_name; kept as a module constant slot

VERDICT_AGREES = "PARITY-AGREES"
VERDICT_DISAGREES = "PARITY-DISAGREES"
VERDICT_NO_TABLE = "NO-TABLE"

E_OTPP_UNREADABLE = "E_OTPP_UNREADABLE"
E_OTPP_NO_TABLE = "E_OTPP_NO_TABLE"
E_OTPP_BAD_FLAG = "E_OTPP_BAD_FLAG"

EXIT_AGREES = 0
EXIT_REFUSED = 2
EXIT_UNREADABLE = 3
EXIT_BAD_FLAG = 5

JSON_KEYS = ("tool", "table", "parser", "prefix",
             "missing_in_table", "missing_in_parser", "verdict")


def _is_table_name(name):
    """A declared own-flag table: an UPPER_CASE module constant.

    The SHAPE is not prescribed (tuple, dict of flag -> dest, help-only
    tuple); what makes it a table is that it carries flag literals, which is
    measured from its value rather than guessed from its name.
    """
    return isinstance(name, str) and name.isupper()


def module_constants(tree):
    """Map every module-level UPPER_CASE constant to the flags it carries."""
    constants = {}
    for node in tree.body:
        targets = ()
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = (node.target,)
            value = node.value
        literals = _flag_literals(value)
        for target in targets:
            if isinstance(target, ast.Name) and _is_table_name(target.id):
                constants[target.id] = literals
    return constants


def _is_own_flag(value):
    """A literal that names a FLAG, not the dash separator or prose.

    "-" alone and "--" are transport (a bare dash test, the argv separator),
    never entries in a help table, so they are read as separators rather than
    reported as one-sided flags. A markdown/prose constant ("- [ ] ...") is
    not a flag table either: a flag is ONE token, so any literal carrying
    whitespace is prose and is skipped - measured at R2390, where one-off
    closeout scripts embed markdown backlog rows as module constants.
    """
    if not isinstance(value, str) or not value.startswith("-"):
        return False
    if value in ("-", "--"):
        return False
    if any(character.isspace() for character in value):
        return False
    return len(value) <= 40


def _flag_literals(node):
    """String literals naming a flag from a tuple/list/set/dict/constant node."""
    found = []
    if isinstance(node, ast.Constant) and _is_own_flag(node.value):
        found.append(node.value)
        return found
    if isinstance(node, ast.Dict):
        for key in node.keys:
            found.extend(_flag_literals(key))
        return found
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        for element in node.elts:
            found.extend(_flag_literals(element))
    return found


def declared_table(tree):
    """Every module-level UPPER_CASE constant that carries flag literals.

    A tool may keep its flags in a tuple (GUARD_FLAGS), a dict of flag -> dest
    (TAKES / FLAGS) or a help-only tuple (HELP_FLAGS); all three are the same
    declaration and are unioned in source order. A constant that carries no
    flag literal contributes nothing, so prose tables never join the set.

    Dict keys are read (R2390 measured: battery_followup keeps FLAGS and TAKES
    as flag -> dest dicts, which a tuple-only reader read as absent).
    """
    flags = []
    for node in tree.body:
        targets = ()
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = (node.target,)
            value = node.value
        for target in targets:
            if isinstance(target, ast.Name) and _is_table_name(target.id):
                for literal in _flag_literals(value):
                    if literal not in flags:
                        flags.append(literal)
    return flags


def _token_side(node):
    """True when this node reads a token-like name (token/arg/argv/flag)."""
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return False
    return any(word in name for word in ("token", "arg", "flag", "opt"))


def local_aliases(tree, constants):
    """Local names bound straight to a module constant (``flags = FLAGS``).

    Measured at R2390 on battery_followup: the parser binds its tables to
    local names before testing membership, so a one-hop reader saw the flags
    declared but never accepted.
    """
    aliases = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        value = node.value
        if (isinstance(target, ast.Name) and isinstance(value, ast.Name)
                and value.id in constants):
            aliases[target.id] = list(constants[value.id])
    return aliases


def _resolved(node, constants, aliases=None):
    """Flags carried by a literal node, or by a name bound to such a table."""
    if isinstance(node, ast.Name):
        if aliases and node.id in aliases:
            return list(aliases[node.id])
        if node.id in constants:
            return list(constants[node.id])
    return _flag_literals(node)


def accepted_tokens(tree, constants=None, aliases=None):
    """Exact literals and startswith prefixes the parser source accepts.

    A comparison against a MODULE CONSTANT (``arg in HELP_FLAGS``) or against a
    LOCAL ALIAS of one (``flags = FLAGS; arg in flags``) is resolved through
    the same tables the declaration side reads, so a tool that keeps its flags
    in one table and tests membership of it is read as accepting exactly those
    flags (measured at R2390 on battery_followup).
    """
    if constants is None:
        constants = module_constants(tree)
    if aliases is None:
        aliases = local_aliases(tree, constants)
    exact = []
    prefix = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, right in zip(node.ops, node.comparators):
                left = node.left
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    pair = None
                    if _token_side(left):
                        pair = right
                    elif _token_side(right):
                        pair = left
                    if pair is None:
                        continue
                    for literal in _resolved(pair, constants, aliases):
                        if literal not in exact:
                            exact.append(literal)
                elif isinstance(op, ast.In):
                    if _token_side(left):
                        for literal in _resolved(right, constants, aliases):
                            if literal not in exact:
                                exact.append(literal)
            # a comparison whose OTHER side is not a token name contributes
            # nothing - the reading keys on the parser's own variable names.
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "startswith":
                if _token_side(func.value) and node.args:
                    for literal in _resolved(node.args[0], constants,
                                             aliases):
                        if literal not in prefix:
                            prefix.append(literal)
    return exact, prefix


def _covered_by_prefix(flag, prefixes):
    return any(flag.startswith(value) and flag != value for value in prefixes)


def classify(tool_name, table, exact, prefix):
    """Pin the verdict and the two one-sided lists."""
    missing_in_table = []
    for flag in exact:
        if flag in table:
            continue
        if _covered_by_prefix(flag, prefix):
            continue
        missing_in_table.append(flag)
    for value in prefix:
        if not any(flag.startswith(value) for flag in table):
            missing_in_table.append(value + "*")
    missing_in_parser = []
    for flag in table:
        if flag in exact:
            continue
        if _covered_by_prefix(flag, prefix):
            continue
        missing_in_parser.append(flag)
    missing_in_table.sort()
    missing_in_parser.sort()
    if not missing_in_table and not missing_in_parser:
        verdict = VERDICT_AGREES
    else:
        verdict = VERDICT_DISAGREES
    return {"tool": tool_name, "table": list(table), "parser": list(exact),
            "prefix": list(prefix), "missing_in_table": missing_in_table,
            "missing_in_parser": missing_in_parser, "verdict": verdict}


def read_tool(path):
    """The tool's source text, or the unreadable refusal."""
    try:
        with io.open(path, encoding="utf-8") as handle:
            return handle.read()
    except (IOError, OSError, UnicodeDecodeError):
        return None


def audit(path):
    """Read one tool and return its parity reading, or a NO-TABLE refusal."""
    source = read_tool(path)
    if source is None:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    table = declared_table(tree)
    if not table:
        payload = {"tool": os.path.basename(path), "table": [], "parser": [],
                   "prefix": [], "missing_in_table": [],
                   "missing_in_parser": [], "verdict": VERDICT_NO_TABLE}
        return payload
    exact, prefix = accepted_tokens(tree, module_constants(tree))
    return classify(os.path.basename(path), table, exact, prefix)


def render(payload, as_json):
    """One stable line, or byte-stable JSON over the pinned keys."""
    if as_json:
        body = dict((key, payload[key]) for key in JSON_KEYS)
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    if payload["verdict"] == VERDICT_NO_TABLE:
        return "%s %s verdict=%s %s" % (LABEL, payload["tool"],
                                        VERDICT_NO_TABLE, E_OTPP_NO_TABLE)
    if payload["verdict"] == VERDICT_AGREES:
        return "%s %s verdict=%s table=%d parser=%d" % (
            LABEL, payload["tool"], VERDICT_AGREES, len(payload["table"]),
            len(payload["parser"]))
    return "%s %s verdict=%s missing_in_table=[%s] missing_in_parser=[%s]" % (
        LABEL, payload["tool"], VERDICT_DISAGREES,
        ",".join(payload["missing_in_table"]),
        ",".join(payload["missing_in_parser"]))


USAGE = ("usage: owner_table_parity.py <tool.py> [--json]\n"
         "       owner_table_parity.py --help\n")


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
            print("%s %s %s" % (LABEL, E_OTPP_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        if target:
            print("%s %s %s" % (LABEL, E_OTPP_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        target = token
    if not target:
        print("%s %s <tool.py>" % (LABEL, E_OTPP_BAD_FLAG), flush=True)
        return EXIT_BAD_FLAG
    if not os.path.isfile(target):
        print("%s %s %s" % (LABEL, E_OTPP_UNREADABLE, target), flush=True)
        return EXIT_UNREADABLE
    payload = audit(target)
    if payload is None:
        print("%s %s %s" % (LABEL, E_OTPP_UNREADABLE, target), flush=True)
        return EXIT_UNREADABLE
    print(render(payload, as_json), flush=True)
    if payload["verdict"] == VERDICT_AGREES:
        return EXIT_AGREES
    return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv))