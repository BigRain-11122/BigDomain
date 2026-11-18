"""Refuse a NEW raw bind site in the sandbox tree.

R2942 moved the birth gate into the nine shipped starters, so every face that
is started through one of them is judged before its socket exists - and R2942
also disclosed what that leaves open: a script that builds a server class
ITSELF never reaches the gate, and nothing in the tree bounded that.  This
module is that bound.  It is a static read over the sandbox sources, no
processes, no sockets, no writes.

Five kinds of site are recognised, and each has one rule:

``http-server``
    a call that constructs an HTTP/TCP server (``ThreadingHTTPServer``,
    ``HTTPServer``, ``ThreadingTCPServer``, ``TCPServer``,
    ``ThreadingUnixStreamServer``, ``UnixStreamServer``; bare name or
    attribute) must sit INSIDE a ``*.checked_server(...)`` call - the shipped
    starters pass a ``lambda`` factory, so the constructor is a descendant of
    that call.  Otherwise ``E_BIND_UNGUARDED_FACE``.

``server-subclass``
    a ``class X(ThreadingHTTPServer)`` definition is not a bind by itself, but
    the module that defines one must also call ``checked_server(`` - the two
    shipped subclasses (``PanelServer``, ``FaceServer``) are only ever built
    through the gate.  Otherwise ``E_BIND_UNGUARDED_FACE``.

``ws-serve``
    a ``serve(...)`` call in a module that imports websockets binds when its
    ``async with`` is entered, so it is judged exactly where the asyncio site
    is judged: it must sit inside a ``*.checked_server(...)`` call, or an
    ordinary statement-level ``birth_gate.guard(...)`` must stand in the SAME
    body (function or module) on a line strictly BEFORE the site line.
    Otherwise ``E_BIND_UNGUARDED_FACE``.

    R2946 tightened this the way R2945 tightened the asyncio kind, because the
    rule until then was ``birth_gate.guard(`` appearing ANYWHERE in the module
    text - so a guard written AFTER ``serve(...)``, a guard in another
    function, and a guard under ``if False:`` all passed.  The two kinds now
    share one judgement rather than one strict rule and one text match.  The
    price is stated, not hidden: a guard inside a real branch is refused too,
    because a static read cannot prove the branch runs.

``asyncio-server``
    an ``asyncio.start_server(...)`` / ``<loop>.create_server(...)`` /
    (after ``from asyncio import start_server``) bare ``start_server(...)``
    call - and, since R2969, the unix-domain half of the same family:
    ``asyncio.start_unix_server(...)`` / ``<loop>.create_unix_server(...)`` /
    (after ``from asyncio import start_unix_server``) bare
    ``start_unix_server(...)`` - must have a ``birth_gate.guard(...)`` call in
    the SAME function body,
    because an asyncio server binds when the coroutine is awaited - the
    ``checked_server`` shim calls its factory synchronously and therefore
    cannot wrap a coroutine factory, which is why this rule is attached to
    ``guard`` rather than to the gate's server shim.  Otherwise
    ``E_BIND_UNGUARDED_FACE``.

    R2945 tightened WHICH guard call counts, because a guard only gates what
    runs after it: the guard must be a STATEMENT of the same body (a direct
    ``guard(...)`` expression or assignment, not one nested in an ``if`` / ``try``
    / ``while`` / ``with``) and its line must come strictly BEFORE the site
    line.  A guard after the await is too late, and a guard inside ``if
    False:`` never runs.  The price of this rule is stated rather than hidden:
    a guard inside a real branch (``if ready: guard()``) is refused too,
    because a static read cannot prove the branch runs.

``socket-bind``
    a ``.bind(...)`` call is a probe or a listening socket and the two cannot
    be told apart from syntax, so every such site must be listed, by path and
    enclosing function, in ``bind_sites.json``.  An unlisted site is
    ``E_BIND_SITE_UNAPPROVED`` - a new one is refused by name until a person
    writes down what it is.

Not scanned, by name: ``test_*.py`` (suite scaffolding binds ephemeral ports
on purpose), ``vendor`` directories and ``pycrdt-poc`` (third-party code is
not this repo's face), and bind forms this module does not recognise
(``socketserver`` factories named something else, ``serve_forever`` reached
through an alias of an alias) - a hole that is named rather than implied
closed.

Stdlib only (ast/json/os/sys), no shell, no network, no writes.
"""

import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE_NAME = "bind_sites.json"

SERVER_NAMES = frozenset((
    "ThreadingHTTPServer",
    "HTTPServer",
    "ThreadingTCPServer",
    "TCPServer",
    "ThreadingUnixStreamServer",
    "UnixStreamServer",
))

SKIP_DIRS = frozenset(("vendor", "node_modules", "__pycache__", "pycrdt-poc",
                       ".git", ".venv", "venv"))

# The asyncio server family this module judges (R2969 added the unix half).
ASYNCIO_CREATE_NAMES = frozenset(("create_server", "create_unix_server"))
ASYNCIO_SERVE_NAMES = frozenset(("start_server", "start_unix_server"))

GUARD_CALL = "checked_server"

UNGUARDED = "E_BIND_UNGUARDED_FACE"
UNAPPROVED = "E_BIND_SITE_UNAPPROVED"

KINDS = ("http-server", "server-subclass", "ws-serve", "asyncio-server",
         "socket-bind")


def is_test_file(name):
    return name.startswith("test_") and name.endswith(".py")


def _callee(node):
    """The bare name / attribute name a Call goes through, else None."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_guarded_call(node):
    return isinstance(node, ast.Call) and _callee(node) == GUARD_CALL


def _asyncio_imported(tree):
    """Bare asyncio server names that came in BY NAME.

    R2969 widened this from the single ``start_server`` fact to the set of
    server constructors this module judges, because the unix-domain pair is the
    same bind shape under a different suffix - and the bare names are still
    recognised from the module's own import facts rather than the name, because
    this repo has its own synchronous ``start_server(host, port, ...)`` helpers
    in ledger and checkout (and could grow a ``start_unix_server`` helper).
    """
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if (node.module or "").split(".")[0] != "asyncio":
            continue
        for alias in node.names:
            if alias.name in ASYNCIO_SERVE_NAMES:
                names.add(alias.name)
    return names


def _asyncio_site(call, bare_imported):
    """The asyncio server shape a Call opens, else None.

    Four attribute shapes and the bare ones the import facts license. The
    unix-domain constructors bind a unix socket exactly where the TCP ones bind
    a TCP socket, so they share this judgement instead of a kind of their own
    (R2969); the attribute form stays receiver-blind for ``create_*``, matching
    ``create_server`` as it shipped.
    """
    func = call.func
    if isinstance(func, ast.Attribute):
        if func.attr in ASYNCIO_CREATE_NAMES:
            return func.attr
        if func.attr in ASYNCIO_SERVE_NAMES and isinstance(func.value, ast.Name):
            if func.value.id == "asyncio":
                return "asyncio." + func.attr
        return None
    if isinstance(func, ast.Name) and func.id in bare_imported:
        return "%s(from asyncio)" % func.id
    return None


def _is_guard_call(node):
    """True when ``node`` is a Call through a ``guard`` name (bare or attribute)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr == "guard"
    return isinstance(func, ast.Name) and func.id == "guard"


def _level_guard_lines(body):
    """Lines where ``guard(...)`` is a STATEMENT of ``body`` itself.

    Only a statement-level call counts. A guard nested inside a branch is not a
    gate this scanner can prove, and a guard that merely shares the function is
    exactly the shape R2945 closed: written after the await it runs after the
    socket exists, written under ``if False:`` it never runs.
    """
    lines = []
    for stmt in body:
        value = getattr(stmt, "value", None)
        if _is_guard_call(value):
            lines.append(stmt.lineno)
    return lines


def _class_bases(classdef):
    """Every server class name appearing in a ClassDef's bases."""
    found = []
    for base in classdef.bases:
        if isinstance(base, ast.Name) and base.id in SERVER_NAMES:
            found.append(base.id)
        elif isinstance(base, ast.Attribute) and base.attr in SERVER_NAMES:
            found.append(base.attr)
    return found


def scan_source(path, text):
    """Every bind-shaped site in one module, with its rule verdict."""
    rel = path.replace(os.sep, "/")
    rows = []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        rows.append({"path": rel, "line": exc.lineno or 0, "function": "<module>",
                     "kind": "unparseable", "code": "E_BIND_UNPARSEABLE",
                     "detail": str(exc)})
        return rows
    has_checked = GUARD_CALL in text
    imports_websockets = "websockets" in text
    bare_start = _asyncio_imported(tree)
    stack = [(tree, [], None)]
    while stack:
        node, ancestors, func_node = stack.pop()
        function = func_node.name if func_node is not None else "<module>"
        for child in ast.iter_child_nodes(node):
            name = function
            next_func = func_node
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = child.name
                next_func = child
            here = ancestors + [node]
            if isinstance(child, ast.Call):
                callee = _callee(child)
                if callee in SERVER_NAMES:
                    guarded = any(_is_guarded_call(a) for a in here)
                    rows.append({
                        "path": rel, "line": child.lineno,
                        "function": name, "kind": "http-server",
                        "code": None if guarded else UNGUARDED,
                        "detail": callee,
                    })
                elif callee == "serve" and imports_websockets:
                    container = func_node if func_node is not None else tree
                    guarded = (
                        any(_is_guarded_call(a) for a in here) or
                        any(line < child.lineno
                            for line in _level_guard_lines(container.body)))
                    rows.append({
                        "path": rel, "line": child.lineno,
                        "function": name, "kind": "ws-serve",
                        "code": None if guarded else UNGUARDED,
                        "detail": callee,
                    })
                else:
                    shape = _asyncio_site(child, bare_start)
                    if shape:
                        container = func_node if func_node is not None else tree
                        guarded = (
                            any(_is_guarded_call(a) for a in here) or
                            any(line < child.lineno
                                for line in _level_guard_lines(container.body)))
                        rows.append({
                            "path": rel, "line": child.lineno,
                            "function": name, "kind": "asyncio-server",
                            "code": None if guarded else UNGUARDED,
                            "detail": shape,
                        })
                    elif callee == "bind":
                        rows.append({
                            "path": rel, "line": child.lineno,
                            "function": name, "kind": "socket-bind",
                            "code": None,  # the baseline decides
                            "detail": callee,
                        })
            elif isinstance(child, ast.ClassDef):
                bases = _class_bases(child)
                if bases:
                    rows.append({
                        "path": rel, "line": child.lineno,
                        "function": name, "kind": "server-subclass",
                        "code": None if has_checked else UNGUARDED,
                        "detail": ",".join(bases),
                    })
            stack.append((child, here, next_func))
    return rows


def iter_modules(root):
    """Every scannable .py under ``root``, repo-relative to it."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith(".py") or is_test_file(name):
                continue
            full = os.path.join(dirpath, name)
            yield os.path.relpath(full, root), full


def scan(root=None, baseline=None):
    """Scan ``root`` and judge it against the socket-bind baseline."""
    root = root or HERE
    rows = []
    scanned = 0
    for rel, full in iter_modules(root):
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            rows.extend(scan_source(rel, handle.read()))
        scanned += 1
    approved = load_baseline(baseline or os.path.join(root, BASELINE_NAME))
    keys = set((entry.get("path"), entry.get("function"))
               for entry in approved.get("sites", ()))
    for row in rows:
        if row["kind"] == "socket-bind" and row["code"] is None:
            if (row["path"], row["function"]) not in keys:
                row["code"] = UNAPPROVED
    found = set((r["path"], r["function"]) for r in rows
                if r["kind"] == "socket-bind")
    stale = sorted(k for k in keys if k not in found)
    refused = [r for r in rows if r["code"]]
    by_kind = {}
    for row in rows:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
    return {
        "root": root,
        "modules": scanned,
        "sites": len(rows),
        "by_kind": by_kind,
        "refused": refused,
        "stale": stale,
        "ok": not refused,
    }


def load_baseline(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return {"sites": []}
    if not isinstance(payload, dict):
        return {"sites": []}
    return payload


def render(verdict, stream=None):
    out = stream or sys.stdout
    for row in verdict["refused"]:
        out.write("[refuse] %s %s:%d %s kind=%s detail=%s\n"
                  % (row["code"], row["path"], row["line"], row["function"],
                     row["kind"], row.get("detail", "")))
    kinds = ",".join("%s=%d" % (k, verdict["by_kind"][k])
                     for k in KINDS if k in verdict["by_kind"])
    out.write("BIND-SCAN %s modules=%d sites=%d refused=%d stale=%d %s\n"
              % ("PASS" if verdict["ok"] else "REFUSED", verdict["modules"],
                 verdict["sites"], len(verdict["refused"]),
                 len(verdict["stale"]), kinds))
    out.flush()


def main(argv):
    root = HERE
    baseline = None
    list_all = False
    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        if arg == "--root" and idx + 1 < len(argv):
            root = argv[idx + 1]
            idx += 2
        elif arg == "--baseline" and idx + 1 < len(argv):
            baseline = argv[idx + 1]
            idx += 2
        elif arg == "--list":
            list_all = True
            idx += 1
        else:
            sys.stderr.write("E_BIND_SCAN_BAD_ARG %s\n" % arg)
            return 2
    verdict = scan(root=root, baseline=baseline)
    if list_all:
        for row in scan_rows(root):
            print("[site] %s %s:%d %s" % (row["kind"], row["path"],
                                          row["line"], row["function"]))
    render(verdict)
    return 0 if verdict["ok"] else 2


def scan_rows(root=None):
    root = root or HERE
    rows = []
    for rel, full in iter_modules(root):
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            rows.extend(scan_source(rel, handle.read()))
    return rows


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
