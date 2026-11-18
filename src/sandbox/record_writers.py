"""Which shipped paths write the launcher record, and does each carry the stamp.

WHY THIS EXISTS (R2978). R2974 taught judge() to compare the creation stamp of
the process CURRENTLY holding a pid with the stamp the record carries, so a
number the system recycled can no longer resurrect a dead launcher. That
guarantee rests on the field being WRITTEN: today only start_all's two calls
(claim and write_serving) publish the record, and a future writer that omits the
field produces a record judge() treats as an OLD record (trust=record-pid), on
which the recycled-pid refusal silently does not apply. Nothing in the tree
pinned that: the fact lived in a docstring only, so the loss would be silent.

This module is that pin, and it is a STATIC READ: it starts no process, binds
no socket, opens no record and writes nothing. It answers one question - for
every call site in the tree that can write the record, do the literal keys the
site hands over include the stamp? - and it publishes, rather than hides, the
sites it exempts.

WHAT IS A WRITE SITE. A call to claim() or write_serving() reached through
`import launcher_registry` (bare or aliased) or a `from launcher_registry
import claim, write_serving`. The record is argument 1 of both, spelled
RECORD_PARAM below; the suite reads the LEAF's own signature and refuses if
this module and the leaf ever disagree, so an inserted parameter cannot make
the reader look at the wrong argument in silence.

HOW THE KEYS ARE READ. The record expression is traced inside its own function
scope, statement by statement: a dict literal contributes its constant string
keys, dict(<expr>) contributes the keys of what it was handed, a name is
resolved to its most recent preceding assignment, name[key] = value adds a key,
and name.pop(key) / del name[key] remove one. Anything else - a call that
returns a record, a comprehension, a name bound by a shape this walk does not
fold - reads UNPROVEN, which is a refusal and not a pass.

WHAT THIS MODULE IS NOT. It is not a security boundary and it does not make the
record trustworthy: it judges the shipped WRITERS, and it cannot see a record
assembled at run time by a helper it does not trace, a writer reached through a
module object passed as a parameter, or a site inside an unreadable module. The
first two read UNPROVEN (refused); the third is published as unreadable and is
only tolerated for test fixtures, which is stated in the report rather than
assumed.

Boundary, named: imports of the leaf under another spelling (a package path, a
relative import, a re-export through a helper module) are not followed, and a
file that fails to parse contributes nothing. Both directions are visible in
the report instead of being skipped in silence.

Pure stdlib (ast, os), pure ASCII source, zero network, zero subprocess.
"""

import ast
import os

LEAF_MODULE = "launcher_registry"
ENTRIES = ("claim", "write_serving")
RECORD_PARAM = "record"
# Argument position of the record for each entry, measured against the leaf's
# own signature by the suite rather than trusted here.
RECORD_INDEX = {"claim": 1, "write_serving": 1}
STAMP_FIELD = "pid_started"
JUDGE_MODULE = "record_writers.py"
FIXTURE_PREFIX = "test_"
WHY_FIXTURE = "fixture"
WHY_JUDGE = "judge"
STATUS_CARRIES = "carries"
STATUS_MISSING = "missing"
STATUS_UNPROVEN = "unproven"


def py_files(root):
    """Every python file under root, sorted, no bytecode caches."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name != "__pycache__")
        for name in sorted(filenames):
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def import_faces(tree):
    """Module-object names and directly imported entry names in one tree."""
    modules, direct = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == LEAF_MODULE:
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == LEAF_MODULE:
                for alias in node.names:
                    if alias.name in ENTRIES:
                        direct.add(alias.asname or alias.name)
    return modules, direct


def dict_keys(expr, env, depth=0):
    """The literal string keys expr contributes, or None when not static."""
    if depth > 6:
        return None
    if isinstance(expr, ast.Dict):
        keys = set()
        for key in expr.keys:
            if key is None:
                return None
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                return None
            keys.add(key.value)
        return keys
    if isinstance(expr, ast.Call):
        func = expr.func
        if isinstance(func, ast.Name) and func.id == "dict":
            keys = set()
            for arg in expr.args:
                part = dict_keys(arg, env, depth + 1)
                if part is None:
                    return None
                keys |= part
            for keyword in expr.keywords:
                if keyword.arg is None:
                    part = dict_keys(keyword.value, env, depth + 1)
                    if part is None:
                        return None
                    keys |= part
                else:
                    keys.add(keyword.arg)
            return keys
        return None
    if isinstance(expr, ast.Name):
        found = env.get(expr.id)
        return None if found is None else set(found)
    return None


def _own_nodes(node):
    """node and its expression descendants, stopping at a nested statement.

    A statement's body is walked by _scan_scope in source order, so descending
    into it here would judge the same call twice - once with the bindings that
    exist before the block and once with the bindings inside it.
    """
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Lambda, ast.stmt)):
            continue
        for sub in _own_nodes(child):
            yield sub


def _bind(stmt, env):
    """Fold one statement's bindings into env; unknown shapes poison the name."""
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
        if isinstance(target, ast.Name):
            env[target.id] = dict_keys(stmt.value, env)
        elif (isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)):
            key = target.slice
            base = env.get(target.value.id)
            if (isinstance(key, ast.Constant) and isinstance(key.value, str)
                    and base is not None):
                env[target.value.id] = set(base) | {key.value}
            else:
                env[target.value.id] = None
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        env[stmt.target.id] = (dict_keys(stmt.value, env)
                               if stmt.value is not None else None)
    elif isinstance(stmt, ast.Delete):
        for target in stmt.targets:
            if (isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and isinstance(target.slice, ast.Constant)
                    and isinstance(target.slice.value, str)):
                base = env.get(target.value.id)
                if base is not None:
                    env[target.value.id] = set(base) - {target.slice.value}
            elif isinstance(target, ast.Name):
                env[target.id] = None
    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
        func = call.func
        if (isinstance(func, ast.Attribute) and func.attr == "pop"
                and isinstance(func.value, ast.Name) and call.args):
            key = call.args[0]
            base = env.get(func.value.id)
            if (isinstance(key, ast.Constant) and isinstance(key.value, str)
                    and base is not None):
                env[func.value.id] = set(base) - {key.value}
            else:
                env[func.value.id] = None
    elif isinstance(stmt, (ast.For, ast.AsyncFor, ast.With, ast.AsyncWith,
                           ast.AugAssign, ast.Global, ast.Nonlocal)):
        for target in _target_names(stmt):
            env[target] = None


def _target_names(stmt):
    names = []
    node = getattr(stmt, "target", None)
    if isinstance(node, ast.Name):
        names.append(node.id)
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        for item in stmt.items:
            if isinstance(item.optional_vars, ast.Name):
                names.append(item.optional_vars.id)
    return names


def _calls(site, modules, direct):
    """Is this Call a record write, and which entry is it?"""
    func = site.func
    if (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
            and func.value.id in modules and func.attr in ENTRIES):
        return func.attr
    if isinstance(func, ast.Name) and func.id in direct:
        return func.id
    return None


def _record_arg(site, entry):
    index = RECORD_INDEX[entry]
    arg = site.args[index] if len(site.args) > index else None
    for keyword in site.keywords:
        if keyword.arg == RECORD_PARAM:
            arg = keyword.value
    return arg


def _scan_scope(body, name, env, modules, direct, out, rel):
    for stmt in body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _scan_scope(stmt.body, stmt.name, {}, modules, direct, out, rel)
            continue
        if isinstance(stmt, ast.ClassDef):
            _scan_scope(stmt.body, stmt.name, {}, modules, direct, out, rel)
            continue
        _bind(stmt, env)
        for node in _own_nodes(stmt):
            if not isinstance(node, ast.Call):
                continue
            entry = _calls(node, modules, direct)
            if entry is None:
                continue
            arg = _record_arg(node, entry)
            keys = dict_keys(arg, env) if arg is not None else None
            if keys is None:
                status = STATUS_UNPROVEN
            elif STAMP_FIELD in keys:
                status = STATUS_CARRIES
            else:
                status = STATUS_MISSING
            out.append({"path": rel, "line": node.lineno, "function": name,
                        "entry": entry, "status": status,
                        "keys": sorted(keys) if keys is not None else None})
        for child in ("body", "orelse", "finalbody"):
            _scan_scope(getattr(stmt, child, None) or [], name, env, modules,
                        direct, out, rel)
        for handler in getattr(stmt, "handlers", None) or []:
            _scan_scope(handler.body, name, env, modules, direct, out, rel)
        for case in getattr(stmt, "cases", None) or []:
            _scan_scope(case.body, name, env, modules, direct, out, rel)


def writer_sites(root):
    """Every call site that can write the record, with its stamp verdict."""
    sites, unreadable, read = [], [], 0
    for path in py_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        read += 1
        try:
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (SyntaxError, UnicodeDecodeError, ValueError):
            unreadable.append(rel)
            continue
        modules, direct = import_faces(tree)
        if not modules and not direct:
            continue
        base = os.path.basename(rel)
        if base == JUDGE_MODULE:
            why = WHY_JUDGE
        elif base.startswith(FIXTURE_PREFIX):
            why = WHY_FIXTURE
        else:
            why = None
        found = []
        _scan_scope(tree.body, "<module>", {}, modules, direct, found, rel)
        for site in found:
            site["why"] = why
            sites.append(site)
    return {"sites": sites, "unreadable": unreadable, "modules_read": read}


def writer_coverage(root):
    """The verdict: does every shipped writer publish the stamp?"""
    scan = writer_sites(root)
    shipped = [site for site in scan["sites"] if site["why"] is None]
    exempt = [site for site in scan["sites"] if site["why"] is not None]
    missing = [site for site in shipped if site["status"] == STATUS_MISSING]
    unproven = [site for site in shipped if site["status"] == STATUS_UNPROVEN]
    unreadable_shipped = [rel for rel in scan["unreadable"]
                          if not os.path.basename(rel).startswith(FIXTURE_PREFIX)]
    return {"ok": bool(shipped) and not missing and not unproven
                  and not unreadable_shipped,
            "shipped": shipped, "exempt": exempt,
            "missing": missing, "unproven": unproven,
            "unreadable": scan["unreadable"],
            "unreadable_shipped": unreadable_shipped,
            "modules_read": scan["modules_read"],
            "field": STAMP_FIELD}


def record_parameters(leaf_path):
    """The leaf's own second-position parameter name per entry."""
    with open(leaf_path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=leaf_path)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ENTRIES:
                index = RECORD_INDEX[node.name]
                if len(node.args.args) > index:
                    found[node.name] = node.args.args[index].arg
    return found
