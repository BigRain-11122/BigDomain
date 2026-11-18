"""Refuse a NEW raw bind site in the sandbox tree.

R2942 moved the birth gate into the nine shipped starters, so every face that
is started through one of them is judged before its socket exists - and R2942
also disclosed what that leaves open: a script that builds a server class
ITSELF never reaches the gate, and nothing in the tree bounded that.  This
module is that bound.  It is a static read over the sandbox sources, no
processes, no sockets, no writes.

Six kinds of site are recognised, and each has one rule:

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

``socketserver-server``

    a construction that reaches ``socketserver`` - the module imported (bare or

    under an alias) and then ``<alias>.<name ending in Server>(...)``, a name

    brought in from it that ends in ``Server`` and then called bare, or a

    module-local ALIAS CHAIN that starts at one of those

    (``Base = socketserver.UDPServer`` then ``Maker = Base`` then

    ``Maker(...)``) - must sit inside a ``*.checked_server(...)`` call, the same

    rule the ``http-server`` kind carries.  ``socketserver`` servers bind inside

    ``__init__`` (``server_bind``), so the gate's server shim can wrap them

    exactly as it wraps an ``http.server`` class.  A

    ``class X(socketserver.<...>Server)`` is a ``server-subclass`` like any

    other, because a subclass is not a bind by itself.  This kind stays apart

    (a UDP or unix server is not an HTTP server), and this module reports what

    it sees.


    R2970 added this kind, and R2971 widened WHICH names reach it: a server
    class that a module of THIS repo re-exports at module level is carried out
    with it.  ``helper`` binding ``UDPServer`` (by from-import, by
    ``Y = socketserver.UDPServer``, or by a module-level alias chain) is
    followed, and a site reaching it as ``import helper as h`` then
    ``h.UDPServer(...)`` or ``from helper import UDPServer`` then
    ``UDPServer(...)`` is judged by the same gate rule.  The chains are resolved
    to a fixpoint across modules, so a re-export of a re-export resolves and a
    cycle contributes nothing.  An ambiguous module name (two files with the
    same stem, or a stem that is not a module) is DROPPED rather than guessed,
    and a name bound twice keeps every shape it was ever bound to - a static
    read refuses what it cannot bound.  What it still does NOT recognise is
    named below.


    R2972 widened the module IDENTITY those exports are keyed by: the map now
    carries each file under its stem AND under its dotted path, so
    ``from pkg.helper import UDPServer`` and ``import pkg.helper as ph`` then
    ``ph.UDPServer(...)`` resolve exactly as the bare forms above do.  The
    dotted path is the only identity that stays unique when two directories
    carry the same stem - measured on this tree, 2 of 90 stems collide
    (``reconcile`` in three directories, ``store`` in two) while 0 of 93
    dotted paths do - so this NARROWS a hole that was open before it and
    widens no rule: a bare ``from helper import ...`` whose stem collides is
    still dropped, and only the dotted form answers.


``socket-bind``

    a ``.bind(...)`` call is a probe or a listening socket and the two cannot be told apart from syntax, so every such site must be listed, by path and
    enclosing function, in ``bind_sites.json``.  An unlisted site is
    ``E_BIND_SITE_UNAPPROVED`` - a new one is refused by name until a person
    writes down what it is.

Not scanned, by name: ``test_*.py`` (suite scaffolding binds ephemeral ports
on purpose), ``vendor`` directories and ``pycrdt-poc`` (third-party code is
not this repo's face), and bind forms this module does not recognise - a hole
that is named rather than implied closed.  Since R2970 the ``socketserver``
family above IS judged when its shape is statically visible; since R2971 that
includes a class another module of this repo re-exports, and since R2972 a
dotted module path (``pkg.helper``) names the same exports the bare stem does.
What remains out of range, in the same breath, MEASURED this window on the
live tree (93 modules, every one parseable): a class built with ``type(...)``
or a factory such as ``functools.partial`` (0 calls touch
``Server``/``socket``), a class imported under a name that does not end in
``Server`` (0 such from-imports exist; a mixin or handler alone binds
nothing), a constructor reached through a module OUTSIDE this repo (its
exports cannot be read without importing it, and this module never imports
what it judges), a name assembled at run time, a bare ``import a.b`` (no
``as``) whose ``a.b.Name(...)`` triple-attribute chain would reach an export
(all 15 dotted imports and 19 dotted from-imports in this tree name stdlib or
third-party modules, and none of the 3280 triple-attribute calls touches the
export face), and ``serve_forever`` reached through an object this read cannot
trace back to a construction.  A ``serve_forever`` call is not itself a bind
site: ``socketserver`` binds in ``__init__``, so the construction is where the
judgement belongs.

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
         "socketserver-server", "socket-bind")

# R2970: the socketserver family, recognised from import facts rather than from
# a growing list of class names, because the module's own namespace is what the
# import statement names. A server class in that namespace always ends in
# "Server" (TCPServer, UDPServer, UnixStreamServer, ForkingTCPServer, ...).
SOCKETSERVER_MODULE = "socketserver"
SOCKETSERVER_SUFFIX = "Server"
SOCKETSERVER_KIND = "socketserver-server"


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


def _socketserver_module_names(tree):
    """Names bound to the ``socketserver`` module itself."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == SOCKETSERVER_MODULE:
                    names.add(alias.asname or alias.name)
    return names


def _socketserver_class_names(tree):
    """Names imported BY NAME from ``socketserver`` that name a server class.

    Only names ending in ``Server`` qualify.  ``from socketserver import
    BaseRequestHandler`` is a handler and ``ThreadingMixIn`` is a mixin; a
    mixin alone binds nothing, so neither is a construction shape.
    """
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if (node.module or "").split(".")[0] != SOCKETSERVER_MODULE:
            continue
        for alias in node.names:
            if alias.name.endswith(SOCKETSERVER_SUFFIX):
                names.add(alias.asname or alias.name)
    return names


def _module_level_nodes(body):
    """Every module-level statement, descending into blocks but never into a def.

    A binding inside a function body is not a re-export - nobody can import it -
    so reading one as an export would invent a surface that does not exist.
    ``if`` / ``try`` / ``with`` bodies DO count, because that is where a person
    puts a guarded import.
    """
    stack = list(body)
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                stack.append(child)


def _module_carried_classes(tree):
    """What one module carries out at module level.

    Three facts, all static: ``direct`` names bound straight to a
    ``socketserver`` class (a from-import or an attribute assignment), ``links``
    names bound to another module-local name (followed, so an alias of an alias
    resolves), and ``borrowed`` names taken from another module by name (which
    only resolve if that module itself exports one).
    """
    ss_modules = _socketserver_module_names(tree)
    direct = {}
    links = {}
    borrowed = {}
    nodes = sorted(_module_level_nodes(tree.body),
                   key=lambda item: getattr(item, "lineno", 0))
    for node in nodes:
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not module:
                continue
            if module == SOCKETSERVER_MODULE:
                for alias in node.names:
                    local = alias.asname or alias.name
                    if alias.name.endswith(SOCKETSERVER_SUFFIX):
                        direct[local] = "%s.%s" % (SOCKETSERVER_MODULE,
                                                   alias.name)
                continue
            # Since R2972 a DOTTED module path is carried verbatim, so the
            # borrowing module names the same target the dotted import names
            # and the resolve lands on the dotted entry of the carried map.
            for alias in node.names:
                local = alias.asname or alias.name
                borrowed[local] = (module, alias.name)
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if node.value is None:
                continue
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node.target, ast.Name):
                targets = [node.target.id]
            else:
                targets = []
            if not targets:
                continue
            value = node.value
            detail = None
            if (isinstance(value, ast.Attribute)
                    and isinstance(value.value, ast.Name)
                    and value.value.id in ss_modules
                    and value.attr.endswith(SOCKETSERVER_SUFFIX)):
                detail = "%s.%s" % (value.value.id, value.attr)
            for target in targets:
                if detail:
                    direct[target] = detail
                elif isinstance(value, ast.Name):
                    links[target] = value.id
    return (direct, links, borrowed)


def _resolve_carried(module, name, carried, seen=None):
    """The chain from ``module.name`` to a ``socketserver`` class, else None."""
    seen = set() if seen is None else seen
    if (module, name) in seen or len(seen) > 8:
        return None
    seen.add((module, name))
    entry = carried.get(module)
    if entry is None:
        return None
    direct, links, borrowed = entry
    if name in direct:
        return direct[name]
    if name in links:
        inner = _resolve_carried(module, links[name], carried, seen)
        if inner:
            return "%s->%s" % (links[name], inner)
        return None
    if name in borrowed:
        other, remote = borrowed[name]
        inner = _resolve_carried(other, remote, carried, seen)
        if inner:
            return "%s.%s->%s" % (other, remote, inner)
    return None


def _module_names(rel):
    """Module identities one file answers to: its stem, and its dotted path.

    A stem is what a bare ``import helper`` names.  The dotted path is what
    ``from pkg.helper import ...`` names, and it is the only identity that
    stays unique when two directories carry the same stem - on this tree 2 of
    90 stems collide (``reconcile``, ``store``) while 0 of 93 dotted paths do,
    so the second identity narrows a hole instead of opening one.  A package's
    ``__init__.py`` answers to the package name, and a file at the root has no
    dotted form of its own.
    """
    parts = rel.replace(os.sep, "/").split("/")
    base = parts[-1]
    dirs = [part for part in parts[:-1] if part]
    if base == "__init__.py":
        stem = dirs[-1] if dirs else ""
        dotted = ".".join(dirs)
    else:
        stem = os.path.splitext(base)[0]
        dotted = ".".join(dirs + [stem]) if dirs else stem
    names = []
    if stem:
        names.append(stem)
    if dotted and dotted not in names:
        names.append(dotted)
    return names


def repo_reexports(root=None):
    """Module identity -> {exported name: chain to the socketserver class}.

    A module RE-EXPORTS a server class when a module-level statement binds a
    name to one.  The chains are followed across repo modules to a fixpoint, so
    ``helper2`` re-exporting what ``helper1`` re-exports resolves, and a cycle
    contributes nothing because the path set cuts it.

    Every file is registered under BOTH identities ``_module_names`` returns,
    and the two share one namespace: a name is DROPPED rather than guessed when
    two files claim it (the R2971 rule), so a colliding stem stays dropped
    while the dotted path of each file still answers - the direction that
    narrows.  A file whose source will not parse is dropped the same way.
    """
    root = root or HERE
    trees = {}
    owners = {}
    facts = {}
    ambiguous = set()
    for rel, full in iter_modules(root):
        names = _module_names(rel)
        if not names:
            continue
        try:
            with open(full, "r", encoding="utf-8-sig", errors="replace") as handle:
                tree = ast.parse(handle.read())
        except SyntaxError:
            for name in names:
                ambiguous.add(name)
                trees.pop(name, None)
                owners.pop(name, None)
            continue
        for name in names:
            holder = owners.get(name)
            if name in ambiguous or (holder is not None and holder != rel):
                ambiguous.add(name)
                trees.pop(name, None)
                owners.pop(name, None)
                continue
            owners[name] = rel
            trees[name] = tree
        if rel not in facts:
            facts[rel] = _module_carried_classes(tree)
    carried = dict((name, facts[owners[name]]) for name in trees)
    exports = {}
    for name in sorted(carried):
        direct, links, borrowed = carried[name]
        found = {}
        for local in sorted(set(direct) | set(links) | set(borrowed)):
            chain = _resolve_carried(name, local, carried)
            if chain:
                found[local] = chain
        if found:
            exports[name] = found
    return exports


def _repo_reexport_context(tree, exports):
    """(module aliases, from-import names, exports) this module holds on the repo.

    Only modules that actually export a server class are tracked, so a normal
    ``import ledger`` costs nothing and cannot be mistaken for a constructor.
    Since R2972 the tracked identities include dotted paths: ``import
    pkg.helper as ph`` binds ``ph`` to ``pkg.helper`` and a dotted from-import
    borrows from it.  A bare dotted import with NO ``as`` binds the PACKAGE,
    not this module, so it is deliberately not bound here - the three-part
    attribute chain it makes reachable is named out of range in the module
    docstring rather than guessed at.
    """
    aliases = {}
    borrowed = {}
    if not exports:
        return (aliases, borrowed, {})
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if "." in name:
                    if alias.asname and name in exports:
                        aliases[alias.asname] = name
                    continue
                if name in exports:
                    aliases[alias.asname or name] = name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module not in exports:
                continue
            for alias in node.names:
                if alias.name in exports[module]:
                    borrowed[alias.asname or alias.name] = (module, alias.name)
    return (aliases, borrowed, exports)


def _server_class_shape(node, module_names, class_names, aliases, repo=None):
    """(kind, detail) when ``node`` evaluates to a server CLASS, else None."""
    if isinstance(node, ast.Name):
        if node.id in aliases:
            kind, detail = sorted(aliases[node.id])[0]
            return (kind, "%s->%s" % (node.id, detail))
        if node.id in SERVER_NAMES:
            return ("http-server", node.id)
        if node.id in class_names:
            return (SOCKETSERVER_KIND, "%s(from socketserver)" % node.id)
        if repo is not None:
            hit = repo[1].get(node.id)
            if hit is not None:
                module, remote = hit
                return (SOCKETSERVER_KIND,
                        "%s(from %s)->%s" % (node.id, module,
                                             repo[2][module][remote]))
        return None
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id in module_names:
            if node.attr.endswith(SOCKETSERVER_SUFFIX):
                return (SOCKETSERVER_KIND,
                        "%s.%s" % (node.value.id, node.attr))
            return None
        if repo is not None and isinstance(node.value, ast.Name):
            target = repo[0].get(node.value.id)
            if target is not None and node.attr in repo[2].get(target, {}):
                return (SOCKETSERVER_KIND,
                        "%s.%s->%s" % (node.value.id, node.attr,
                                       repo[2][target][node.attr]))
        if node.attr in SERVER_NAMES:
            return ("http-server", node.attr)
    return None


def _server_aliases(tree, module_names, class_names, repo=None):
    """Module-local names bound to a server class, followed to a fixpoint.

    One assignment is what a person writes; an alias OF an alias is the same
    fact one step further out, and both are static - the value is either a bare
    server-class name, an attribute of the socketserver module, or (since
    R2971) a name another repo module re-exports.  A name assigned twice keeps
    BOTH shapes, because a static read cannot prove which assignment runs, and
    this module's standing rule is to refuse a shape it cannot bound rather
    than guess the live one.
    """
    assigns = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target] if isinstance(node.target, ast.Name) else []
            value = node.value
        else:
            continue
        if targets:
            assigns.append((node.lineno, targets, value))
    assigns.sort(key=lambda item: item[0])
    aliases = {}
    changed = True
    while changed:
        changed = False
        for _, targets, value in assigns:
            shape = _server_class_shape(value, module_names, class_names,
                                        aliases, repo)
            if shape is None:
                continue
            for target in targets:
                before = aliases.get(target.id, frozenset())
                after = before | frozenset((shape,))
                if after != before:
                    aliases[target.id] = after
                    changed = True
    return aliases


def _socketserver_site(call, module_names, class_names, aliases, repo=None):
    """(kind, detail) when ``call`` constructs a server this read can trace."""
    return _server_class_shape(call.func, module_names, class_names, aliases,
                               repo)


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


def _class_bases(classdef, module_names, class_names, aliases, repo=None):
    """Every server class appearing in a ClassDef's bases."""
    found = []
    for base in classdef.bases:
        if isinstance(base, ast.Name):
            if (base.id in SERVER_NAMES or base.id in class_names
                    or base.id in aliases):
                found.append(base.id)
            elif repo is not None and base.id in repo[1]:
                module, remote = repo[1][base.id]
                found.append("%s(from %s)->%s"
                             % (base.id, module, repo[2][module][remote]))
        elif isinstance(base, ast.Attribute):
            if base.attr in SERVER_NAMES:
                found.append(base.attr)
            elif (isinstance(base.value, ast.Name)
                  and base.value.id in module_names
                  and base.attr.endswith(SOCKETSERVER_SUFFIX)):
                found.append("%s.%s" % (base.value.id, base.attr))
            elif repo is not None and isinstance(base.value, ast.Name):
                target = repo[0].get(base.value.id)
                if target is not None and base.attr in repo[2].get(target, {}):
                    found.append("%s.%s" % (base.value.id, base.attr))
    return found


def scan_source(path, text, repo=None):
    """Every bind-shaped site in one module, with its rule verdict.

    ``repo`` is the map ``repo_reexports`` returns for the tree being scanned;
    without it this read is exactly the R2970 one, so a caller that hands a bare
    file to the judge gets the bare file's judgement.
    """
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
    ss_modules = _socketserver_module_names(tree)
    ss_classes = _socketserver_class_names(tree)
    ss_repo = _repo_reexport_context(tree, repo) if repo else None
    ss_aliases = _server_aliases(tree, ss_modules, ss_classes, ss_repo)
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
                    else:
                        traced = _socketserver_site(child, ss_modules,
                                                    ss_classes, ss_aliases,
                                                    ss_repo)
                        if traced:
                            traced_kind, traced_detail = traced
                            guarded = any(_is_guarded_call(a) for a in here)
                            rows.append({
                                "path": rel, "line": child.lineno,
                                "function": name, "kind": traced_kind,
                                "code": None if guarded else UNGUARDED,
                                "detail": traced_detail,
                            })
                        elif callee == "bind":
                            rows.append({
                                "path": rel, "line": child.lineno,
                                "function": name, "kind": "socket-bind",
                                "code": None,  # the baseline decides
                                "detail": callee,
                            })
            elif isinstance(child, ast.ClassDef):
                bases = _class_bases(child, ss_modules, ss_classes,
                                     ss_aliases, ss_repo)
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
    exports = repo_reexports(root)
    rows = []
    scanned = 0
    for rel, full in iter_modules(root):
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            rows.extend(scan_source(rel, handle.read(), exports))
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
    exports = repo_reexports(root)
    rows = []
    for rel, full in iter_modules(root):
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            rows.extend(scan_source(rel, handle.read(), exports))
    return rows


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
