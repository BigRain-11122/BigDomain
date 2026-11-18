"""Suite for the static bind-site gate that bounds R2942's disclosed hole.

Criteria AC-BSC1..AC-BSC24 (27 checks). AC-BSC1..AC-BSC5 were pinned in
src/os/backlog.md
BEFORE this file, src/sandbox/bind_site_scan.py and src/sandbox/bind_sites.json
existed (in-window pre-registration, disclosed); AC-BSC6..AC-BSC7 came with the
asyncio kind (R2944), AC-BSC8..AC-BSC9 with its order/level rule (R2945),
AC-BSC10..AC-BSC12 with the same rule applied to ws-serve (R2946), AC-BSC13..
AC-BSC14 with the unix half of the asyncio family (R2969), AC-BSC15..
AC-BSC17 with the socketserver construction family plus the measured
declaration that serve_forever is not a bind site (R2970), AC-BSC18..
AC-BSC20 with a server class re-exported by another repo module plus the
measured declaration that the type()/partial class and the non-Server import
name stay out of range (R2971), and AC-BSC21..AC-BSC22 with the same exports
reached through a DOTTED module path plus the measured declaration that a bare
``import a.b`` leaves the ``a.b.Name(...)`` chain out of range (R2972), and
AC-BSC23..AC-BSC24 with that chain JUDGED once the module's own bare dotted
import licenses it, plus the measured declaration that the shape has no live
instance on this tree (R2973).

Nothing here is read off the scanner's own prose: every criterion builds a
private world on disk, runs the SHIPPED ``scan()`` over it, and requires a
named refusal - then removes the offending file (or declares it) and requires
the same world to pass, so each red is caused by the thing under test.

Usage: python test_bind_site_scan.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import ast
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAF = os.path.join(HERE, "bind_site_scan.py")
BASELINE = os.path.join(HERE, "bind_sites.json")
FRONTDOOR = os.path.join(HERE, "frontdoor.py")
LOBBY = os.path.join(HERE, "lobby", "server.py")
START_ALL = os.path.join(HERE, "start_all.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "bind-site-scan"
WORLD = os.path.join(REPO, "logs", "bind-scan-suite")
# The revision AC-BSC14 measures against. It is PINNED rather than "HEAD":
# once this round is committed HEAD carries the new scanner, so a HEAD-pinned
# red control would grade a tree against itself (the R2959 lesson).
PRE_R2969_REV = "73a00b5d64290948c1b2972208f7d5096a29ce4c"
# The revision AC-BSC16 measures the live tree against: the R2969 bytes, i.e.
# the scanner BEFORE the socketserver family existed.
PRE_R2970_REV = "c6bf93ea03476a43feb023dca735af3809448fb5"
# The revision AC-BSC19 measures the live tree against: the R2970 bytes, i.e.
# the scanner BEFORE a repo module's re-export was followed.
PRE_R2971_REV = "979b34e662c54ade292ea9826be285f0a9a52a27"
# The revision AC-BSC22 measures the live tree against: the R2971 bytes, i.e.
# the scanner BEFORE a dotted module path could name an export.
PRE_R2972_REV = "92d824d7c8e6fa1ec5cbcdaacac91c4388e2ffd8"
# The revision AC-BSC24 measures the live tree against: the R2972 bytes, i.e.
# the scanner BEFORE a bare `import a.b` licensed its three-part chain.
PRE_R2973_REV = "33182971c6a2854a2ffabb32b7ce061e62454632"

sys.path.insert(0, HERE)
import bind_site_scan  # noqa: E402

RESULTS = []

GATED = (
    "import birth_gate\n"
    "from http.server import ThreadingHTTPServer\n"
    "\n"
    "def start_face(host, port, handler):\n"
    "    return birth_gate.checked_server(\n"
    "        lambda: ThreadingHTTPServer((host, port), handler))\n"
)

RAW = (
    "from http.server import ThreadingHTTPServer\n"
    "\n"
    "def start_face(host, port, handler):\n"
    "    return ThreadingHTTPServer((host, port), handler)\n"
)

PROBE = (
    "import socket\n"
    "\n"
    "def free_port():\n"
    "    sock = socket.socket()\n"
    "    sock.bind((\"127.0.0.1\", 0))\n"
    "    port = sock.getsockname()[1]\n"
    "    sock.close()\n"
    "    return port\n"
)


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def fresh_world(name):
    path = os.path.join(WORLD, name)
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    return path


def write(root, rel, text):
    full = os.path.join(root, rel)
    parent = os.path.dirname(full)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(full, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return full


def codes(verdict):
    return [row["code"] for row in verdict["refused"]]


def serve_line(text):
    """Line of the first ``serve(...)`` call in ``text`` (0 when there is none).

    Written here rather than imported from the scanner so a criterion never
    grades the scanner with the scanner's own notion of where the site is.
    """
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name == "serve":
            return node.lineno
    return 0


def top_level_guard_lines(body):
    """Lines where a ``guard(...)`` call is a STATEMENT of ``body`` itself."""
    lines = []
    for stmt in body:
        value = getattr(stmt, "value", None)
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name == "guard":
            lines.append(stmt.lineno)
    return lines


def serve_forever_sites(root):
    """Every live ``serve_forever`` call, and whether its object came through
    a ``checked_server(...)`` construction inside the same module.

    Written here rather than imported from the scanner because AC-BSC17 grades
    a DECLARATION with a measurement: the answer "serve_forever is not a bind
    site" is only honest if the two live calls can be traced to the place where
    the socket really binds.
    """
    sites = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        with open(full, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        factories = set()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if any(isinstance(sub, ast.Call)
                   and isinstance(sub.func, ast.Attribute)
                   and sub.func.attr == "checked_server"
                   for sub in ast.walk(node)):
                factories.add(node.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute)
                    and func.attr == "serve_forever"):
                continue
            site = {"path": rel, "line": node.lineno, "resolved": False}
            if isinstance(func.value, ast.Name):
                want = func.value.id
                for owner in ast.walk(tree):
                    body = getattr(owner, "body", None)
                    if not isinstance(body, list):
                        continue
                    for stmt in body:
                        if not isinstance(stmt, ast.Assign):
                            continue
                        if not any(isinstance(t, ast.Name) and t.id == want
                                   for t in stmt.targets):
                            continue
                        value = stmt.value
                        if not isinstance(value, ast.Call):
                            continue
                        callee = value.func
                        if (isinstance(callee, ast.Attribute)
                                and callee.attr == "checked_server"):
                            site["resolved"] = True
                        elif (isinstance(callee, ast.Name)
                              and callee.id in factories):
                            site["resolved"] = True
            sites.append(site)
    return sites


def composed_class_sites(root):
    """Live ``type(...)`` / ``functools.partial(...)`` calls that touch a server.

    AC-BSC20 grades a DECLARATION the same way AC-BSC17 does: the answer "a
    class composed at run time stays out of range" is only honest if the number
    of places that would need it is measured on the tree that ships it.
    """
    found = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        with open(full, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        partial_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "functools":
                for alias in node.names:
                    if alias.name == "partial":
                        partial_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "functools":
                        partial_names.add(alias.asname or alias.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_type = isinstance(func, ast.Name) and func.id == "type"
            is_partial = ((isinstance(func, ast.Name)
                           and func.id in partial_names)
                          or (isinstance(func, ast.Attribute)
                              and func.attr == "partial"))
            if not (is_type or is_partial):
                continue
            dumped = ast.dump(node)
            if "Server" in dumped or "socket" in dumped:
                found.append({"path": rel, "line": node.lineno})
    return found


def socketserver_facts(root):
    """(modules importing socketserver, non-Server from-import names) live."""
    modules = set()
    non_server = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        with open(full, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "socketserver":
                        modules.add(rel)
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] != "socketserver":
                    continue
                for alias in node.names:
                    if not alias.name.endswith("Server"):
                        non_server.append((rel, node.lineno, alias.name))
    return (modules, non_server)


def dotted_import_facts(root):
    """The dotted-import face of a tree, measured rather than assumed.

    AC-BSC22 grades the declaration that a bare ``import a.b`` (no ``as``)
    leaves the ``a.b.Name(...)`` chain out of range, so this walk reports the
    facts that make the declaration checkable: which stems collide (a stem is
    what the export map loses first), whether the dotted path of every such
    file is unique (the identity that recovers it), and how many dotted
    imports name a module under the scanned root at all.
    """
    stems = {}
    dotted = {}
    files = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        parts = rel.split("/")
        base = parts[-1]
        dirs = [part for part in parts[:-1] if part]
        stem = dirs[-1] if base == "__init__.py" else os.path.splitext(base)[0]
        name = ".".join(dirs) if base == "__init__.py" else (
            ".".join(dirs + [stem]) if dirs else stem)
        files.append((rel, stem, name))
        if stem:
            stems.setdefault(stem, []).append(rel)
        if name:
            dotted.setdefault(name, []).append(rel)
    ambiguous_files = [rel for rels in stems.values() if len(rels) > 1
                       for rel in rels]
    recovered = [rel for rel, _, name in files
                 if len(dotted.get(name, ())) == 1]
    imports = []
    froms = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        with open(full, encoding="utf-8-sig", errors="replace") as handle:
            try:
                tree = ast.parse(handle.read())
            except SyntaxError:
                continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "." in alias.name:
                        imports.append((rel, node.lineno, alias.name,
                                        alias.name in dotted))
            elif (isinstance(node, ast.ImportFrom) and node.module
                  and "." in node.module):
                froms.append((rel, node.lineno, node.module,
                              node.module in dotted))
    return {
        "files": len(files),
        "ambiguous_stems": sorted(k for k, v in stems.items() if len(v) > 1),
        "ambiguous_dotted": sorted(k for k, v in dotted.items() if len(v) > 1),
        "ambiguous_files": ambiguous_files,
        "recovered": [rel for rel in ambiguous_files if rel in recovered],
        "imports": imports,
        "froms": froms,
    }


def triple_attr_facts(root):
    """The three-part attribute chain measured independently of the reader.

    AC-BSC24 grades the claim that R2973's new shape has no live instance, so
    this walk rebuilds the facts from the sources themselves - module
    identities from the file layout, import statements as written, and calls
    whose callee is a three-deep attribute chain - rather than asking the
    scanner what it thinks it saw.
    """
    identities = set()
    files = []
    for rel, full in bind_site_scan.iter_modules(root):
        rel = rel.replace(os.sep, "/")
        parts = rel.split("/")
        base = parts[-1]
        dirs = [part for part in parts[:-1] if part]
        stem = dirs[-1] if base == "__init__.py" else os.path.splitext(base)[0]
        name = ".".join(dirs) if base == "__init__.py" else (
            ".".join(dirs + [stem]) if dirs else stem)
        files.append((rel, full))
        for label in (stem, name):
            if label:
                identities.add(label)
    exports = bind_site_scan.repo_reexports(root)

    def spelling(node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        parts.append(node.id)
        return ".".join(reversed(parts))

    bare = 0
    aliased = 0
    landing_imports = []
    calls = 0
    landing_calls = []
    export_hits = []
    bases = []
    for rel, full in files:
        with open(full, encoding="utf-8-sig", errors="replace") as handle:
            try:
                tree = ast.parse(handle.read())
            except SyntaxError:
                continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "." not in alias.name:
                        continue
                    if alias.asname:
                        aliased += 1
                        continue
                    bare += 1
                    if alias.name in identities:
                        landing_imports.append((rel, node.lineno, alias.name))
            elif isinstance(node, ast.Call):
                func = node.func
                if not (isinstance(func, ast.Attribute)
                        and isinstance(func.value, ast.Attribute)):
                    continue
                calls += 1
                receiver = spelling(func.value)
                if receiver in identities:
                    landing_calls.append((rel, node.lineno, receiver,
                                          func.attr))
                    if func.attr in exports.get(receiver, {}):
                        export_hits.append((rel, node.lineno, receiver,
                                            func.attr))
            elif isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if not (isinstance(base, ast.Attribute)
                            and isinstance(base.value, ast.Attribute)):
                        continue
                    receiver = spelling(base.value)
                    if receiver in identities:
                        bases.append((rel, node.lineno, receiver, base.attr))
    return {
        "modules": len(files),
        "identities": len(identities),
        "bare_dotted_imports": bare,
        "aliased_dotted_imports": aliased,
        "landing_imports": landing_imports,
        "triple_calls": calls,
        "landing_calls": landing_calls,
        "export_hits": export_hits,
        "triple_bases": bases,
    }


def main():
    if os.path.isdir(WORLD):
        shutil.rmtree(WORLD)
    os.makedirs(WORLD)

    # ---- AC-BSC1: a NEW raw server construction is refused by name ------
    bad = []
    root = fresh_world("bsc1")
    write(root, "good.py", GATED)
    clean = bind_site_scan.scan(root=root)
    if not clean["ok"]:
        bad.append("gated-world-refused")
    write(root, "bad.py", RAW)
    dirty = bind_site_scan.scan(root=root)
    if dirty["ok"]:
        bad.append("raw-construction-passed")
    if bind_site_scan.UNGUARDED not in codes(dirty):
        bad.append("unnamed-refusal")
    named = [r for r in dirty["refused"] if r["path"].endswith("bad.py")]
    if not named:
        bad.append("file-not-named")
    else:
        row = named[0]
        if row["line"] != 4:
            bad.append("line-%s" % row["line"])
        if row["function"] != "start_face":
            bad.append("function-%s" % row["function"])
        if row["kind"] != "http-server":
            bad.append("kind-%s" % row["kind"])
    # red control: gate the same file the same way and the same world passes.
    write(root, "bad.py", GATED.replace("start_face", "start_other"))
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("healed-world-still-refused")
    report("AC-BSC1", bool(bad), ",".join(bad))

    # ---- AC-BSC2: an UNDECLARED socket bind is refused; declaring passes -
    bad = []
    root = fresh_world("bsc2")
    write(root, "probe.py", PROBE)
    lonely = bind_site_scan.scan(root=root)
    if lonely["ok"]:
        bad.append("undeclared-bind-passed")
    if bind_site_scan.UNAPPROVED not in codes(lonely):
        bad.append("unnamed-refusal")
    hit = [r for r in lonely["refused"] if r["kind"] == "socket-bind"]
    if not hit or hit[0]["function"] != "free_port":
        bad.append("function-not-named")
    write(root, "bind_sites.json",
          '{"sites": [{"path": "probe.py", "function": "free_port",'
          ' "kind": "probe", "reason": "suite fixture"}]}\n')
    declared = bind_site_scan.scan(root=root)
    if not declared["ok"]:
        bad.append("declared-bind-still-refused")
    if declared["sites"] != 1:
        bad.append("sites-%d" % declared["sites"])
    report("AC-BSC2", bool(bad), ",".join(bad))

    # ---- AC-BSC3: the exclusions are live, both ways --------------------
    bad = []
    root = fresh_world("bsc3")
    write(root, "test_fixture.py", RAW)
    write(root, os.path.join("vendor", "third_party.py"), RAW)
    quiet = bind_site_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("excluded-world-refused")
    if quiet["sites"] != 0:
        bad.append("excluded-sites-%d" % quiet["sites"])
    write(root, "shipped_face.py", RAW)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("shipped-raw-passed")
    if not [r for r in loud["refused"] if r["path"] == "shipped_face.py"]:
        bad.append("shipped-file-not-named")
    if len(loud["refused"]) != 1:
        bad.append("refused-%d" % len(loud["refused"]))
    report("AC-BSC3", bool(bad), ",".join(bad))

    # ---- AC-BSC4: the front door is born through the same gate ----------
    bad = []
    with open(FRONTDOOR, encoding="utf-8") as handle:
        source = handle.read()
    if "import birth_gate" not in source:
        bad.append("no-gate-import")
    tree = ast.parse(source)
    main_body = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            main_body = node
            break
    if main_body is None:
        bad.append("no-main")
    else:
        called = any(isinstance(sub, ast.Call) and
                     isinstance(sub.func, ast.Attribute) and
                     sub.func.attr == "checked_server"
                     for sub in ast.walk(main_body))
        if not called:
            bad.append("main-not-gated")
    verdict = bind_site_scan.scan(root=HERE)
    doors = [r for r in verdict["refused"] if r["path"] == "frontdoor.py"]
    if doors:
        bad.append("frontdoor-still-unbounded")
    rows = [r for r in bind_site_scan.scan_rows(root=HERE)
            if r["path"] == "frontdoor.py" and r["kind"] == "http-server"]
    if len(rows) != 1:
        bad.append("frontdoor-sites-%d" % len(rows))
    report("AC-BSC4", bool(bad), ",".join(bad))

    # ---- AC-BSC5: the scan is a read, and the leaf is a leaf ------------
    bad = []
    before = {}
    for path in (FRONTDOOR, START_ALL, BASELINE):
        stat = os.stat(path)
        before[path] = (stat.st_size, stat.st_mtime_ns)
    first = bind_site_scan.scan(root=HERE)
    second = bind_site_scan.scan(root=HERE)
    for path, stamp in before.items():
        stat = os.stat(path)
        if (stat.st_size, stat.st_mtime_ns) != stamp:
            bad.append("wrote-" + os.path.basename(path))
    if not first["ok"]:
        bad.append("shipped-tree-refused")
    if first["sites"] != second["sites"]:
        bad.append("sites-moved-%d/%d" % (first["sites"], second["sites"]))
    with open(LEAF, "rb") as handle:
        raw = handle.read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad.append("leaf-bom")
    if b"\r\n" in raw:
        bad.append("leaf-crlf")
    try:
        text = raw.decode("utf-8")
        text.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        bad.append("leaf-not-ascii")
        text = raw.decode("utf-8", "replace")
    if "import subprocess" in text or "import urllib" in text:
        bad.append("leaf-shells")
    if "import socket" in text or "socket.socket(" in text:
        bad.append("leaf-binds")
    allowed = {"ast", "json", "os", "sys"}
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or
                stripped.startswith("from ")):
            continue
        root_name = stripped.split()[1].split(".")[0]
        if root_name not in allowed:
            bad.append("leaf-imports-" + root_name)
    with open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)
    with open(os.path.abspath(__file__), "rb") as handle:
        own = handle.read()
    if b"\r\n" in own or own[:3] == b"\xef\xbb\xbf":
        bad.append("suite-dialect")
    report("AC-BSC5", bool(bad), ",".join(bad))

    # ---- AC-BSC6: an asyncio server is refused until it is guarded ------
    bad = []
    root = fresh_world("bsc6")
    asyncio_raw = (
        "import asyncio\n"
        "\n"
        "async def boot(handler):\n"
        "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
    )
    loop_raw = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, loop):\n"
        "    return await loop.create_server(handler, \"127.0.0.1\", 0)\n"
    )
    asyncio_gated = asyncio_raw.replace(
        "async def boot(handler):\n",
        "async def boot(handler):\n"
        "    birth_gate.guard()\n")
    write(root, "face_a.py", asyncio_raw)
    write(root, "face_b.py", loop_raw)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("asyncio-sites-passed")
    rows = {r["path"]: r for r in loud["refused"]}
    for rel, want in (("face_a.py", 4), ("face_b.py", 4)):
        row = rows.get(rel)
        if row is None:
            bad.append("not-named-" + rel)
            continue
        if row["kind"] != "asyncio-server":
            bad.append("kind-%s-%s" % (rel, row["kind"]))
        if row["line"] != want:
            bad.append("line-%s-%s" % (rel, row["line"]))
        if row["function"] != "boot":
            bad.append("function-%s-%s" % (rel, row["function"]))
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("code-%s-%s" % (rel, row["code"]))
    # red control: the SAME file with a guard line inside the same function
    # must pass - the red was the missing door, not the word asyncio.
    write(root, "face_a.py", asyncio_gated)
    healed = bind_site_scan.scan(root=root)
    if [r for r in healed["refused"] if r["path"] == "face_a.py"]:
        bad.append("guarded-asyncio-still-refused")
    if not [r for r in healed["refused"] if r["path"] == "face_b.py"]:
        bad.append("guard-healed-both-files")
    # a guard call in a DIFFERENT function does not heal the site
    write(root, "face_a.py",
          "import asyncio\n"
          "\n"
          "async def boot(handler):\n"
          "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
          "\n"
          "def elsewhere():\n"
          "    birth_gate.guard()\n")
    scoped = bind_site_scan.scan(root=root)
    if scoped["ok"]:
        bad.append("other-function-guard-healed")
    report("AC-BSC6", bool(bad), ",".join(bad))

    # ---- AC-BSC7: the shapes are recognised, the lookalikes are not -----
    bad = []
    root = fresh_world("bsc7")
    own_helper = (
        "def start_server(host, port):\n"
        "    return (host, port)\n"
        "\n"
        "def main():\n"
        "    httpd = start_server(\"127.0.0.1\", 0)\n"
        "    return httpd\n"
    )
    qualified = (
        "import ledger_page\n"
        "\n"
        "def main():\n"
        "    return ledger_page.start_server(\"127.0.0.1\", 0, None)\n"
    )
    mention_only = (
        "NOTE = \"start_server is not called here\"\n"
    )
    write(root, "own_helper.py", own_helper)
    write(root, "qualified.py", qualified)
    write(root, "mention.py", mention_only)
    quiet = bind_site_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("lookalikes-refused")
    if quiet["sites"] != 0:
        bad.append("lookalike-sites-%d" % quiet["sites"])
    # and the bare name IS recognised once it is imported from asyncio
    write(root, "imported.py",
          "from asyncio import start_server\n"
          "\n"
          "async def boot(handler):\n"
          "    return await start_server(handler, \"127.0.0.1\", 0)\n")
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("bare-imported-passed")
    hits = [r for r in loud["refused"] if r["path"] == "imported.py"]
    if not hits or hits[0]["kind"] != "asyncio-server":
        bad.append("bare-imported-kind")
    # live tree: the new rule costs nothing today and moves no count
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["by_kind"].get("asyncio-server"):
        bad.append("live-asyncio-%d" % live["by_kind"]["asyncio-server"])
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    report("AC-BSC7", bool(bad), ",".join(bad))

    # ---- AC-BSC8: a guard AFTER the await is too late -------------------
    bad = []
    root = fresh_world("bsc8")
    late = (
        "import asyncio\n"
        "\n"
        "async def boot(handler):\n"
        "    server = await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
        "    birth_gate.guard()\n"
        "    return server\n"
    )
    early = (
        "import asyncio\n"
        "\n"
        "async def boot(handler):\n"
        "    birth_gate.guard()\n"
        "    server = await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
        "    return server\n"
    )
    write(root, "late.py", late)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("late-guard-passed")
    rows = [r for r in loud["refused"] if r["path"] == "late.py"]
    if not rows:
        bad.append("late-not-named")
    else:
        row = rows[0]
        if row["line"] != 4:
            bad.append("late-line-%s" % row["line"])
        if row["function"] != "boot":
            bad.append("late-function-%s" % row["function"])
        if row["kind"] != "asyncio-server":
            bad.append("late-kind-%s" % row["kind"])
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("late-code-%s" % row["code"])
    # red control: the SAME file with the SAME guard moved one line up passes
    write(root, "late.py", early)
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("early-guard-still-refused")
    # the bare from-asyncio shape is judged the same way, both directions
    bare_late = (
        "from asyncio import start_server\n"
        "\n"
        "async def boot(handler):\n"
        "    server = await start_server(handler, \"127.0.0.1\", 0)\n"
        "    birth_gate.guard()\n"
        "    return server\n"
    )
    bare_early = (
        "from asyncio import start_server\n"
        "\n"
        "async def boot(handler):\n"
        "    birth_gate.guard()\n"
        "    server = await start_server(handler, \"127.0.0.1\", 0)\n"
        "    return server\n"
    )
    write(root, "bare.py", bare_late)
    bare_loud = bind_site_scan.scan(root=root)
    if not [r for r in bare_loud["refused"] if r["path"] == "bare.py"]:
        bad.append("bare-late-passed")
    write(root, "bare.py", bare_early)
    bare_healed = bind_site_scan.scan(root=root)
    if not bare_healed["ok"]:
        bad.append("bare-early-still-refused")
    report("AC-BSC8", bool(bad), ",".join(bad))

    # ---- AC-BSC9: a guard inside a branch is not a gate -----------------
    bad = []
    root = fresh_world("bsc9")
    nested_false = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, ready):\n"
        "    if False:\n"
        "        birth_gate.guard()\n"
        "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
    )
    nested_ready = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, ready):\n"
        "    if ready:\n"
        "        birth_gate.guard()\n"
        "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
    )
    hoisted = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, ready):\n"
        "    birth_gate.guard()\n"
        "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
    )
    assigned = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, ready):\n"
        "    ok = birth_gate.guard()\n"
        "    return await asyncio.start_server(handler, \"127.0.0.1\", 0)\n"
    )
    write(root, "dead.py", nested_false)
    write(root, "branch.py", nested_ready)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("nested-guards-passed")
    named = set(r["path"] for r in loud["refused"])
    if "dead.py" not in named:
        bad.append("if-false-guard-counted")
    if "branch.py" not in named:
        bad.append("branch-guard-counted")
    # red control: hoisting the SAME call to statement level passes, and an
    # assignment statement counts too (the rule is about nesting, not syntax)
    write(root, "dead.py", hoisted)
    write(root, "branch.py", assigned)
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("hoisted-still-refused")
    report("AC-BSC9", bool(bad), ",".join(bad))

    # ---- AC-BSC10: a ws guard AFTER serve is too late -------------------
    bad = []
    root = fresh_world("bsc10")
    ws_late = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port):\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
        "    birth_gate.guard()\n"
    )
    ws_early = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port):\n"
        "    birth_gate.guard()\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
    )
    ws_elsewhere = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port):\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
        "\n"
        "def main():\n"
        "    birth_gate.guard()\n"
    )
    write(root, "late.py", ws_late)
    write(root, "elsewhere.py", ws_elsewhere)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("late-guard-passed")
    late_rows = [r for r in loud["refused"] if r["path"] == "late.py"]
    if not late_rows:
        bad.append("late-not-named")
    else:
        row = late_rows[0]
        if row["kind"] != "ws-serve":
            bad.append("late-kind-%s" % row["kind"])
        if row["line"] != 4:
            bad.append("late-line-%s" % row["line"])
        if row["function"] != "run":
            bad.append("late-function-%s" % row["function"])
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("late-code-%s" % row["code"])
    # the shape that passed until R2946: a guard in ANOTHER function
    if not [r for r in loud["refused"] if r["path"] == "elsewhere.py"]:
        bad.append("other-function-guard-healed")
    # red control: the SAME file with the SAME guard moved one line up
    write(root, "late.py", ws_early)
    os.remove(os.path.join(root, "elsewhere.py"))
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("early-guard-still-refused")
    report("AC-BSC10", bool(bad), ",".join(bad))

    # ---- AC-BSC11: the shipped lobby is judged at the site --------------
    bad = []
    with open(LOBBY, encoding="utf-8") as handle:
        shipped = handle.read()
    tree = ast.parse(shipped)
    run_node = None
    for node in tree.body:
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run_server":
            run_node = node
            break
    if run_node is None:
        bad.append("no-run_server")
    else:
        site = serve_line(shipped)
        guards = top_level_guard_lines(run_node.body)
        if not guards:
            bad.append("no-site-guard")
        elif not any(line < site for line in guards):
            bad.append("site-guard-not-before-serve")
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    if live["by_kind"].get("ws-serve") != 1:
        bad.append("live-ws-%s" % live["by_kind"].get("ws-serve"))
    if live["by_kind"].get("asyncio-server"):
        bad.append("live-asyncio-%d" % live["by_kind"]["asyncio-server"])
    # real-bytes red control: the door's OWN shipped source with the one guard
    # statement removed must be refused by name, and restoring the same bytes
    # must turn that world green.
    root = fresh_world("bsc11")
    doctored_lines = shipped.splitlines(True)
    drop = None
    for node in ast.walk(run_node):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else getattr(func, "id", ""))
            if name == "guard" and node.lineno <= serve_line(shipped):
                drop = node.lineno
                break
    if drop is None:
        bad.append("no-guard-statement-to-drop")
    else:
        doctored = "".join(doctored_lines[:drop - 1] + doctored_lines[drop:])
        write(root, os.path.join("lobby", "server.py"), doctored)
        loud = bind_site_scan.scan(root=root)
        if loud["ok"]:
            bad.append("doctored-lobby-passed")
        rows = [r for r in loud["refused"] if r["path"] == "lobby/server.py"]
        if not rows:
            bad.append("doctored-not-named")
        else:
            row = rows[0]
            if row["kind"] != "ws-serve":
                bad.append("doctored-kind-%s" % row["kind"])
            if row["function"] != "run_server":
                bad.append("doctored-function-%s" % row["function"])
            if row["line"] != serve_line(doctored):
                bad.append("doctored-line-%s-%s" % (row["line"],
                                                    serve_line(doctored)))
        write(root, os.path.join("lobby", "server.py"), shipped)
        restored = bind_site_scan.scan(root=root)
        if not restored["ok"]:
            bad.append("restored-lobby-refused")
    report("AC-BSC11", bool(bad), ",".join(bad))

    # ---- AC-BSC12: a ws guard inside a branch is not a gate -------------
    bad = []
    root = fresh_world("bsc12")
    ws_dead = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port):\n"
        "    if False:\n"
        "        birth_gate.guard()\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
    )
    ws_branch = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port, ready):\n"
        "    if ready:\n"
        "        birth_gate.guard()\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
    )
    ws_hoisted = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port):\n"
        "    birth_gate.guard()\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
    )
    ws_assigned = (
        "import websockets\n"
        "\n"
        "async def run(handler, host, port, ready):\n"
        "    ok = birth_gate.guard()\n"
        "    async with websockets.serve(handler, host, port):\n"
        "        await asyncio.sleep(0)\n"
    )
    write(root, "dead.py", ws_dead)
    write(root, "branch.py", ws_branch)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("nested-ws-guards-passed")
    named = set(r["path"] for r in loud["refused"])
    if "dead.py" not in named:
        bad.append("if-false-guard-counted")
    if "branch.py" not in named:
        bad.append("branch-guard-counted")
    write(root, "dead.py", ws_hoisted)
    write(root, "branch.py", ws_assigned)
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("hoisted-still-refused")
    report("AC-BSC12", bool(bad), ",".join(bad))

    # ---- AC-BSC13: the unix half of the asyncio family is judged --------
    bad = []
    root = fresh_world("bsc13")
    unix_attr = (
        "import asyncio\n"
        "\n"
        "async def boot(handler):\n"
        "    return await asyncio.start_unix_server(handler, path=\"/tmp/a.sock\")\n"
    )
    unix_loop = (
        "import asyncio\n"
        "\n"
        "async def boot(handler, loop):\n"
        "    return await loop.create_unix_server(handler, path=\"/tmp/b.sock\")\n"
    )
    unix_bare = (
        "from asyncio import start_unix_server\n"
        "\n"
        "async def boot(handler):\n"
        "    return await start_unix_server(handler, path=\"/tmp/c.sock\")\n"
    )
    write(root, "face_a.py", unix_attr)
    write(root, "face_b.py", unix_loop)
    write(root, "face_c.py", unix_bare)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("unix-sites-passed")
    got = {r["path"]: r for r in loud["refused"]}
    want_detail = {
        "face_a.py": "asyncio.start_unix_server",
        "face_b.py": "create_unix_server",
        "face_c.py": "start_unix_server(from asyncio)",
    }
    for rel, detail in want_detail.items():
        row = got.get(rel)
        if row is None:
            bad.append("not-named-" + rel)
            continue
        if row["kind"] != "asyncio-server":
            bad.append("kind-%s-%s" % (rel, row["kind"]))
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("code-%s-%s" % (rel, row["code"]))
        if row["line"] != 4:
            bad.append("line-%s-%s" % (rel, row["line"]))
        if row["function"] != "boot":
            bad.append("function-%s-%s" % (rel, row["function"]))
        if row["detail"] != detail:
            bad.append("detail-%s-%s" % (rel, row["detail"]))
    # red control: the same three files with a statement-level guard BEFORE
    # the site must all turn green - the red is the missing door, not the
    # word unix.
    for rel, text in (("face_a.py", unix_attr), ("face_b.py", unix_loop),
                      ("face_c.py", unix_bare)):
        write(root, rel, text.replace(
            "):\n    return await",
            "):\n    birth_gate.guard()\n    return await", 1))
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("guarded-unix-still-refused")
    # and a guard AFTER the site is too late for the same shape
    write(root, "face_a.py",
          "import asyncio\n"
          "\n"
          "async def boot(handler):\n"
          "    server = await asyncio.start_unix_server(handler, path=\"/tmp/a.sock\")\n"
          "    birth_gate.guard()\n"
          "    return server\n")
    late = bind_site_scan.scan(root=root)
    late_rows = [r for r in late["refused"] if r["path"] == "face_a.py"]
    if not late_rows:
        bad.append("late-unix-guard-passed")
    elif late_rows[0]["detail"] != "asyncio.start_unix_server":
        bad.append("late-unix-detail-%s" % late_rows[0]["detail"])
    report("AC-BSC13", bool(bad), ",".join(bad))

    # ---- AC-BSC14: the boundary is named, the live tree does not move ----
    bad = []
    root = fresh_world("bsc14")
    own_helper = (
        "def start_unix_server(path):\n"
        "    return path\n"
        "\n"
        "def main():\n"
        "    return start_unix_server(\"/tmp/own.sock\")\n"
    )
    qualified = (
        "import ledger_page\n"
        "\n"
        "def main():\n"
        "    return ledger_page.start_unix_server(\"/tmp/q.sock\")\n"
    )
    write(root, "own_helper.py", own_helper)
    write(root, "qualified.py", qualified)
    quiet = bind_site_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("lookalikes-refused")
    if quiet["sites"] != 0:
        bad.append("lookalike-sites-%d" % quiet["sites"])
    # the receiver-blind side of the SAME family, measured rather than denied:
    # create_unix_server on a non-asyncio receiver is judged, exactly as
    # create_server already was before this round.
    write(root, "worker.py",
          "import worker_pool\n"
          "\n"
          "async def boot(handler):\n"
          "    return await worker_pool.create_unix_server(handler, path=\"/tmp/w.sock\")\n")
    blind = bind_site_scan.scan(root=root)
    rows = [r for r in blind["refused"] if r["path"] == "worker.py"]
    if not rows:
        bad.append("receiver-blind-not-judged")
    elif rows[0]["detail"] != "create_unix_server":
        bad.append("receiver-blind-detail-%s" % rows[0]["detail"])
    os.remove(os.path.join(root, "worker.py"))
    # live tree: no site moved, and the new shapes have no live bearer
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    if live["by_kind"].get("asyncio-server"):
        bad.append("live-asyncio-%d" % live["by_kind"]["asyncio-server"])
    # red control against a PINNED revision: the pre-round bytes must read the
    # unix world as clean, or this criterion would be measuring argparse
    old = subprocess.run(["git", "show", PRE_R2969_REV
                          + ":src/sandbox/bind_site_scan.py"],
                         cwd=REPO, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if old.returncode != 0 or not old.stdout:
        bad.append("no-old-bytes")
    else:
        after = fresh_world("bsc14-old")
        write(after, "face_a.py", unix_attr)
        write(after, "face_b.py", unix_loop)
        write(after, "face_c.py", unix_bare)
        old_leaf = os.path.join(WORLD, "bind_site_scan_prer2969.py")
        with open(old_leaf, "wb") as handle:
            handle.write(old.stdout)
        ran = subprocess.run([sys.executable, old_leaf, "--root", after],
                             stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=120)
        text = ran.stdout.decode("utf-8", "replace")
        if ran.returncode != 0:
            bad.append("old-binary-refused-rc-%d" % (ran.returncode,))
        if "BIND-SCAN PASS" not in text:
            bad.append("old-binary-not-clean")
        if "asyncio-server=" in text:
            bad.append("old-binary-already-counted")
        fresh = subprocess.run([sys.executable, LEAF, "--root", after],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=120)
        fresh_text = fresh.stdout.decode("utf-8", "replace")
        if fresh.returncode != 2:
            bad.append("new-binary-rc-%d" % (fresh.returncode,))
        if "kind=asyncio-server" not in fresh_text:
            bad.append("new-binary-did-not-name-kind")
        if fresh_text.count("[refuse] " + bind_site_scan.UNGUARDED) != 3:
            bad.append("new-binary-refusals-%d"
                       % fresh_text.count("[refuse] "))
        os.remove(old_leaf)
    report("AC-BSC14", bool(bad), ",".join(bad))

    # ---- AC-BSC15: the socketserver family is judged at construction -----
    bad = []
    root = fresh_world("bsc15")
    ss_raw = (
        "import socketserver\n"
        "\n"
        "class Handler(socketserver.BaseRequestHandler):\n"
        "    def handle(self):\n"
        "        pass\n"
        "\n"
        "def boot(host, port):\n"
        "    return socketserver.UDPServer((host, port), Handler)\n"
    )
    ss_gated = (
        "import socketserver\n"
        "import birth_gate\n"
        "\n"
        "class Handler(socketserver.BaseRequestHandler):\n"
        "    def handle(self):\n"
        "        pass\n"
        "\n"
        "def boot(host, port):\n"
        "    return birth_gate.checked_server(\n"
        "        lambda: socketserver.UDPServer((host, port), Handler))\n"
    )
    ss_module_alias = (
        "import socketserver as ss\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return ss.ForkingTCPServer((host, port), handler)\n"
    )
    ss_by_name = (
        "from socketserver import ThreadingUDPServer\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return ThreadingUDPServer((host, port), handler)\n"
    )
    ss_chain = (
        "import socketserver\n"
        "\n"
        "Base = socketserver.UDPServer\n"
        "Maker = Base\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return Maker((host, port), handler)\n"
    )
    write(root, "raw.py", ss_raw)
    write(root, "module_alias.py", ss_module_alias)
    write(root, "by_name.py", ss_by_name)
    write(root, "chain.py", ss_chain)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("socketserver-sites-passed")
    got = {r["path"]: r for r in loud["refused"]}
    want = {
        "raw.py": ("socketserver-server", "socketserver.UDPServer", 8, "boot"),
        "module_alias.py": ("socketserver-server", "ss.ForkingTCPServer",
                            4, "boot"),
        "by_name.py": ("socketserver-server",
                       "ThreadingUDPServer(from socketserver)", 4, "boot"),
        "chain.py": ("socketserver-server",
                     "Maker->Base->socketserver.UDPServer", 7, "boot"),
    }
    for rel, (kind, detail, line, function) in want.items():
        row = got.get(rel)
        if row is None:
            bad.append("not-named-" + rel)
            continue
        if row["kind"] != kind:
            bad.append("kind-%s-%s" % (rel, row["kind"]))
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("code-%s-%s" % (rel, row["code"]))
        if row["detail"] != detail:
            bad.append("detail-%s-%s" % (rel, row["detail"]))
        if row["line"] != line:
            bad.append("line-%s-%s" % (rel, row["line"]))
        if row["function"] != function:
            bad.append("function-%s-%s" % (rel, row["function"]))
    # red control: gate the SAME construction and the same world passes - the
    # red was the missing door, not the word socketserver.
    write(root, "raw.py", ss_gated)
    for rel in ("module_alias.py", "by_name.py", "chain.py"):
        os.remove(os.path.join(root, rel))
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("gated-socketserver-still-refused")
    # positive controls: a handler is not a server, and a bare name nobody
    # imported is not licensed by the word appearing in the file.
    boundary = fresh_world("bsc15-boundary")
    write(boundary, "handler.py",
          "import socketserver\n"
          "\n"
          "def make(handler):\n"
          "    return socketserver.BaseRequestHandler(handler)\n")
    write(boundary, "bare.py",
          "def boot(host, port, handler):\n"
          "    return UDPServer((host, port), handler)\n")
    quiet = bind_site_scan.scan(root=boundary)
    if not quiet["ok"]:
        bad.append("boundary-refused")
    if quiet["sites"] != 0:
        bad.append("boundary-sites-%d" % quiet["sites"])
    report("AC-BSC15", bool(bad), ",".join(bad))

    # ---- AC-BSC16: the live tree does not move a single line -------------
    bad = []
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    want_kinds = {"http-server": 8, "server-subclass": 2, "socket-bind": 3,
                  "ws-serve": 1}
    if live["by_kind"] != want_kinds:
        bad.append("live-kinds-%s" % sorted(live["by_kind"].items()))
    old = subprocess.run(["git", "show", PRE_R2970_REV
                          + ":src/sandbox/bind_site_scan.py"],
                         cwd=REPO, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if old.returncode != 0 or not old.stdout:
        bad.append("no-old-bytes")
    else:
        old_leaf = os.path.join(WORLD, "bind_site_scan_prer2970.py")
        with open(old_leaf, "wb") as handle:
            handle.write(old.stdout)
        before = subprocess.run(
            [sys.executable, old_leaf, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        after = subprocess.run(
            [sys.executable, LEAF, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        if before.returncode != 0 or after.returncode != 0:
            bad.append("list-rc-%d/%d" % (before.returncode, after.returncode))
        if before.stdout != after.stdout:
            bad.append("live-lines-moved")
        os.remove(old_leaf)
    report("AC-BSC16", bool(bad), ",".join(bad))

    # ---- AC-BSC17: serve_forever is declared out of range, with the
    # measurement that makes the declaration checkable ---------------------
    bad = []
    sites = serve_forever_sites(HERE)
    if len(sites) != 2:
        bad.append("serve-forever-%d" % len(sites))
    paths = sorted(set(s["path"] for s in sites))
    if paths != ["frontdoor.py", "member/member_page.py"]:
        bad.append("paths-%s" % paths)
    unresolved = [s for s in sites if not s["resolved"]]
    if unresolved:
        bad.append("unresolved-%s"
                   % [(s["path"], s["line"]) for s in unresolved])
    report("AC-BSC17", bool(bad), ",".join(bad))

    # ---- AC-BSC18: a server class RE-EXPORTED by another repo module is
    # judged where it is constructed ---------------------------------------
    bad = []
    root = fresh_world("bsc18")
    helper_export = "from socketserver import UDPServer\n"
    site_alias = (
        "import helper as h\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return h.UDPServer((host, port), handler)\n"
    )
    site_gated = (
        "import birth_gate\n"
        "import helper as h\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return birth_gate.checked_server(\n"
        "        lambda: h.UDPServer((host, port), handler))\n"
    )
    site_bare = (
        "from helper import UDPServer\n"
        "\n"
        "def boot(host, port, handler):\n"
        "    return UDPServer((host, port), handler)\n"
    )
    write(root, "helper.py", helper_export)
    write(root, "site.py", site_alias)
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("reexport-site-passed")
    row = [r for r in loud["refused"] if r["path"] == "site.py"]
    if not row:
        bad.append("reexport-not-named")
    else:
        row = row[0]
        if row["kind"] != "socketserver-server":
            bad.append("kind-%s" % row["kind"])
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("code-%s" % row["code"])
        if row["line"] != 4:
            bad.append("line-%s" % row["line"])
        if row["function"] != "boot":
            bad.append("function-%s" % row["function"])
        if row["detail"] != "h.UDPServer->socketserver.UDPServer":
            bad.append("detail-%s" % row["detail"])
    # red control: the SAME construction through the SAME re-export passes once
    # it sits inside the gate - the red was the missing door, not the name.
    write(root, "site.py", site_gated)
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("gated-reexport-still-refused")
    # the bare from-import form names where the class came from.
    write(root, "site.py", site_bare)
    bare_loud = bind_site_scan.scan(root=root)
    if bare_loud["ok"]:
        bad.append("bare-reexport-passed")
    bare_rows = [r for r in bare_loud["refused"] if r["path"] == "site.py"]
    if not bare_rows:
        bad.append("bare-reexport-not-named")
    elif bare_rows[0]["detail"] != "UDPServer(from helper)->socketserver.UDPServer":
        bad.append("bare-detail-%s" % bare_rows[0]["detail"])
    report("AC-BSC18", bool(bad), ",".join(bad))

    # ---- AC-BSC18b: the chain, the subclass base, and the boundary -------
    bad = []
    root = fresh_world("bsc18b")
    write(root, "helper1.py", "from socketserver import UDPServer\n")
    write(root, "helper2.py", "from helper1 import UDPServer\n")
    write(root, "site.py",
          "import helper2 as h2\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return h2.UDPServer((host, port), handler)\n")
    chain = bind_site_scan.scan(root=root)
    if chain["ok"]:
        bad.append("chain-site-passed")
    chain_rows = [r for r in chain["refused"] if r["path"] == "site.py"]
    if not chain_rows:
        bad.append("chain-not-named")
    elif chain_rows[0]["detail"] != (
            "h2.UDPServer->helper1.UDPServer->socketserver.UDPServer"):
        bad.append("chain-detail-%s" % chain_rows[0]["detail"])
    # a subclass of a re-exported class is a server-subclass, like any other.
    sub_root = fresh_world("bsc18b-sub")
    write(sub_root, "helper.py", "from socketserver import UDPServer\n")
    write(sub_root, "site.py",
          "import helper as h\n"
          "\n"
          "class Face(h.UDPServer):\n"
          "    allow_reuse_address = True\n")
    sub = bind_site_scan.scan(root=sub_root)
    if sub["ok"]:
        bad.append("reexport-subclass-passed")
    sub_rows = [r for r in sub["refused"] if r["kind"] == "server-subclass"]
    if not sub_rows:
        bad.append("subclass-not-named")
    elif not sub_rows[0]["detail"].startswith("h.UDPServer"):
        bad.append("subclass-detail-%s" % sub_rows[0]["detail"])
    # boundary: a module re-exporting a HANDLER exports no server class, so
    # the same construction through it is not a site - the map carries server
    # classes, not every name from socketserver.
    bound_root = fresh_world("bsc18b-bound")
    write(bound_root, "handlers.py",
          "from socketserver import BaseRequestHandler\n")
    write(bound_root, "site.py",
          "import handlers as h\n"
          "\n"
          "def make(handler):\n"
          "    return h.BaseRequestHandler(handler)\n")
    quiet = bind_site_scan.scan(root=bound_root)
    if not quiet["ok"]:
        bad.append("handler-world-refused")
    if quiet["sites"] != 0:
        bad.append("handler-sites-%d" % quiet["sites"])
    # and a name bound twice keeps the server shape: a static read cannot prove
    # which assignment runs, so the shape is refused rather than guessed away.
    twice_root = fresh_world("bsc18b-twice")
    write(twice_root, "helper.py",
          "class Fake(object):\n"
          "    pass\n"
          "\n"
          "try:\n"
          "    from socketserver import UDPServer\n"
          "except ImportError:\n"
          "    UDPServer = Fake\n")
    write(twice_root, "site.py",
          "import helper as h\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return h.UDPServer((host, port), handler)\n")
    twice = bind_site_scan.scan(root=twice_root)
    if twice["ok"]:
        bad.append("twice-bound-passed")
    report("AC-BSC18b", bool(bad), ",".join(bad))

    # ---- AC-BSC19: the live tree does not move a single line -------------
    bad = []
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    want_kinds = {"http-server": 8, "server-subclass": 2, "socket-bind": 3,
                  "ws-serve": 1}
    if live["by_kind"] != want_kinds:
        bad.append("live-kinds-%s" % sorted(live["by_kind"].items()))
    old = subprocess.run(["git", "show", PRE_R2971_REV
                          + ":src/sandbox/bind_site_scan.py"],
                         cwd=REPO, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if old.returncode != 0 or not old.stdout:
        bad.append("no-old-bytes")
    else:
        old_leaf = os.path.join(WORLD, "bind_site_scan_prer2971.py")
        with open(old_leaf, "wb") as handle:
            handle.write(old.stdout)
        before = subprocess.run(
            [sys.executable, old_leaf, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        after = subprocess.run(
            [sys.executable, LEAF, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        if before.returncode != 0 or after.returncode != 0:
            bad.append("list-rc-%d/%d" % (before.returncode, after.returncode))
        if before.stdout != after.stdout:
            bad.append("live-lines-moved")
        os.remove(old_leaf)
    report("AC-BSC19", bool(bad), ",".join(bad))

    # ---- AC-BSC20: the two remaining shapes are declared out of range with
    # the measurement that makes the declaration checkable ------------------
    bad = []
    composed = composed_class_sites(HERE)
    if composed:
        bad.append("composed-%s" % [(c["path"], c["line"]) for c in composed])
    modules, non_server = socketserver_facts(HERE)
    if modules:
        bad.append("socketserver-importers-%s" % sorted(modules))
    if non_server:
        bad.append("non-server-names-%s" % non_server)
    report("AC-BSC20", bool(bad), ",".join(bad))

    # ---- AC-BSC21: the same exports reached through a DOTTED module path
    # are judged where the construction sits -------------------------------
    bad = []
    root = fresh_world("bsc21")
    write(root, "pkg/helper.py", "from socketserver import UDPServer\n")
    write(root, "site.py",
          "from pkg.helper import UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return UDPServer((host, port), handler)\n")
    loud = bind_site_scan.scan(root=root)
    if loud["ok"]:
        bad.append("dotted-from-passed")
    rows = [r for r in loud["refused"] if r["path"] == "site.py"]
    if not rows:
        bad.append("dotted-from-not-named")
    else:
        row = rows[0]
        if row["kind"] != "socketserver-server":
            bad.append("kind-%s" % row["kind"])
        if row["code"] != bind_site_scan.UNGUARDED:
            bad.append("code-%s" % row["code"])
        if row["line"] != 4:
            bad.append("line-%s" % row["line"])
        if row["function"] != "boot":
            bad.append("function-%s" % row["function"])
        if row["detail"] != "UDPServer(from pkg.helper)->socketserver.UDPServer":
            bad.append("detail-%s" % row["detail"])
    # the alias form names the dotted source too, and the SAME construction
    # passes once it sits inside the gate - the red was the door, not the name.
    write(root, "site.py",
          "import pkg.helper as ph\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return ph.UDPServer((host, port), handler)\n")
    alias = bind_site_scan.scan(root=root)
    if alias["ok"]:
        bad.append("dotted-alias-passed")
    alias_rows = [r for r in alias["refused"] if r["path"] == "site.py"]
    if not alias_rows:
        bad.append("dotted-alias-not-named")
    elif alias_rows[0]["detail"] != "ph.UDPServer->socketserver.UDPServer":
        bad.append("alias-detail-%s" % alias_rows[0]["detail"])
    write(root, "site.py",
          "import birth_gate\n"
          "import pkg.helper as ph\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return birth_gate.checked_server(\n"
          "        lambda: ph.UDPServer((host, port), handler))\n")
    healed = bind_site_scan.scan(root=root)
    if not healed["ok"]:
        bad.append("gated-dotted-still-refused")
    # a dotted path that names nothing under the root is NOT a repo module, so
    # it buys no export - the map reads files, not dotted-looking strings.
    write(root, "site.py",
          "from pkg.nosuch import UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return UDPServer((host, port), handler)\n")
    absent = bind_site_scan.scan(root=root)
    if not absent["ok"] or absent["sites"] != 0:
        bad.append("absent-dotted-sites-%d" % absent["sites"])
    # positive control: a package that carries a HANDLER carries no server
    # class, so the same call shape is not a site.
    write(root, "pkg/helper.py", "from socketserver import BaseRequestHandler\n")
    write(root, "site.py",
          "import pkg.helper as ph\n"
          "\n"
          "def make(handler):\n"
          "    return ph.BaseRequestHandler(handler)\n")
    quiet = bind_site_scan.scan(root=root)
    if not quiet["ok"]:
        bad.append("dotted-handler-world-refused")
    if quiet["sites"] != 0:
        bad.append("dotted-handler-sites-%d" % quiet["sites"])
    report("AC-BSC21", bool(bad), ",".join(bad))

    # ---- AC-BSC21b: the dotted chain, the subclass base, and the ambiguous
    # stem the dotted path narrows -----------------------------------------
    bad = []
    root = fresh_world("bsc21b")
    write(root, "pkg/helper1.py", "from socketserver import UDPServer\n")
    write(root, "pkg/helper2.py", "from pkg.helper1 import UDPServer\n")
    write(root, "site.py",
          "import pkg.helper2 as ph2\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return ph2.UDPServer((host, port), handler)\n")
    chain = bind_site_scan.scan(root=root)
    if chain["ok"]:
        bad.append("chain-site-passed")
    chain_rows = [r for r in chain["refused"] if r["path"] == "site.py"]
    if not chain_rows:
        bad.append("chain-not-named")
    elif chain_rows[0]["detail"] != (
            "ph2.UDPServer->pkg.helper1.UDPServer->socketserver.UDPServer"):
        bad.append("chain-detail-%s" % chain_rows[0]["detail"])
    # both dotted modules are identities the export map carries, so the
    # intermediate hop is measured rather than inferred from the detail text.
    exports = bind_site_scan.repo_reexports(root)
    for name in ("pkg.helper1", "pkg.helper2"):
        if name not in exports:
            bad.append("map-missing-%s" % name)
    if exports.get("pkg.helper2", {}).get("UDPServer") != (
            "pkg.helper1.UDPServer->socketserver.UDPServer"):
        bad.append("map-chain-%s" % exports.get("pkg.helper2"))
    # a subclass of a dotted re-export is a server-subclass like any other.
    sub_root = fresh_world("bsc21b-sub")
    write(sub_root, "pkg/helper.py", "from socketserver import UDPServer\n")
    write(sub_root, "site.py",
          "import pkg.helper as ph\n"
          "\n"
          "class Face(ph.UDPServer):\n"
          "    allow_reuse_address = True\n")
    sub = bind_site_scan.scan(root=sub_root)
    if sub["ok"]:
        bad.append("dotted-subclass-passed")
    sub_rows = [r for r in sub["refused"] if r["kind"] == "server-subclass"]
    if not sub_rows:
        bad.append("dotted-subclass-not-named")
    elif not sub_rows[0]["detail"].startswith("ph.UDPServer"):
        bad.append("subclass-detail-%s" % sub_rows[0]["detail"])
    # the ambiguous stem: two directories carry the same stem, so the STEM
    # identity is dropped (the R2971 rule) while each dotted path still
    # answers - the new dimension narrows, it does not loosen.
    amb_root = fresh_world("bsc21b-amb")
    write(amb_root, "pkg1/helper.py", "from socketserver import UDPServer\n")
    write(amb_root, "pkg2/helper.py", "from socketserver import UDPServer\n")
    write(amb_root, "site.py",
          "from helper import UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return UDPServer((host, port), handler)\n")
    bare = bind_site_scan.scan(root=amb_root)
    if not bare["ok"] or bare["sites"] != 0:
        bad.append("ambiguous-bare-sites-%d" % bare["sites"])
    write(amb_root, "site.py",
          "from pkg1.helper import UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return UDPServer((host, port), handler)\n")
    aimed = bind_site_scan.scan(root=amb_root)
    if aimed["ok"]:
        bad.append("ambiguous-dotted-passed")
    aimed_rows = [r for r in aimed["refused"] if r["path"] == "site.py"]
    if not aimed_rows:
        bad.append("ambiguous-dotted-not-named")
    elif "pkg1.helper" not in aimed_rows[0]["detail"]:
        bad.append("ambiguous-detail-%s" % aimed_rows[0]["detail"])
    report("AC-BSC21b", bool(bad), ",".join(bad))

    # ---- AC-BSC22: the live tree does not move a line, and the shape this
    # round leaves out is declared with the measurement that bounds it ------
    bad = []
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    want_kinds = {"http-server": 8, "server-subclass": 2, "socket-bind": 3,
                  "ws-serve": 1}
    if live["by_kind"] != want_kinds:
        bad.append("live-kinds-%s" % sorted(live["by_kind"].items()))
    old = subprocess.run(["git", "show", PRE_R2972_REV
                          + ":src/sandbox/bind_site_scan.py"],
                         cwd=REPO, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if old.returncode != 0 or not old.stdout:
        bad.append("no-old-bytes")
    else:
        old_leaf = os.path.join(WORLD, "bind_site_scan_prer2972.py")
        with open(old_leaf, "wb") as handle:
            handle.write(old.stdout)
        before = subprocess.run(
            [sys.executable, old_leaf, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        after = subprocess.run(
            [sys.executable, LEAF, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        if before.returncode != 0 or after.returncode != 0:
            bad.append("list-rc-%d/%d" % (before.returncode, after.returncode))
        if before.stdout != after.stdout:
            bad.append("live-lines-moved")
        os.remove(old_leaf)
    # the declared boundary, measured: dotted identities never collide, they
    # recover every file whose stem collides, and no dotted import in this
    # tree names a module under the root (so the triple-attribute chain this
    # round leaves out has no live instance to misjudge).
    facts = dotted_import_facts(HERE)
    if facts["ambiguous_dotted"]:
        bad.append("dotted-collides-%s" % facts["ambiguous_dotted"])
    if not facts["ambiguous_files"]:
        bad.append("no-ambiguous-stem")
    if facts["recovered"] != facts["ambiguous_files"]:
        bad.append("not-recovered-%s"
                   % [rel for rel in facts["ambiguous_files"]
                      if rel not in facts["recovered"]])
    landed = [row for row in facts["imports"] + facts["froms"] if row[3]]
    if landed:
        bad.append("dotted-lands-on-repo-%s" % landed[:3])
    report("AC-BSC22", bool(bad), ",".join(bad))

    # ---- AC-BSC23: a bare `import a.b` licenses its three-part chain --------
    bad = []
    root = fresh_world("bsc23-bare")
    write(root, "pkg/helper.py", "from socketserver import UDPServer\n")
    raw_site = ("import pkg.helper\n"
                "\n"
                "def boot(host, port, handler):\n"
                "    return pkg.helper.UDPServer((host, port), handler)\n")
    write(root, "site.py", raw_site)
    bare = bind_site_scan.scan(root=root)
    if bare["ok"]:
        bad.append("triple-passed")
    rows = [r for r in bare["refused"] if r["path"] == "site.py"]
    if not rows:
        bad.append("triple-not-named")
    else:
        row = rows[0]
        if row["kind"] != "socketserver-server":
            bad.append("triple-kind-%s" % row["kind"])
        if row["line"] != 4 or row["function"] != "boot":
            bad.append("triple-place-%d/%s" % (row["line"], row["function"]))
        if row["detail"] != "pkg.helper.UDPServer->socketserver.UDPServer":
            bad.append("triple-detail-%s" % row["detail"])
    # the same construction behind the shipped gate turns the world green:
    # what was red is the missing door, not the dotted name.
    write(root, "site.py",
          "import birth_gate\n"
          "import pkg.helper\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return birth_gate.checked_server(\n"
          "        lambda: pkg.helper.UDPServer((host, port), handler))\n")
    gated = bind_site_scan.scan(root=root)
    if not gated["ok"]:
        bad.append("triple-gated-refused")
    # depth is not a licence of its own: the licence is the exact spelling.
    deep = fresh_world("bsc23-deep")
    write(deep, "pkg/deep/sub/helper.py",
          "from socketserver import UDPServer\n")
    write(deep, "site.py",
          "import pkg.deep.sub.helper\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return pkg.deep.sub.helper.UDPServer((host, port), handler)\n")
    dv = bind_site_scan.scan(root=deep)
    if dv["ok"]:
        bad.append("deep-passed")
    drows = [r for r in dv["refused"] if r["path"] == "site.py"]
    if not drows:
        bad.append("deep-not-named")
    elif "pkg.deep.sub.helper.UDPServer" not in drows[0]["detail"]:
        bad.append("deep-detail-%s" % drows[0]["detail"])
    # an export that merely RESOLVES is not a licence: pkg.other carries the
    # same class but no import statement in this module names it.
    write(deep, "pkg/other.py", "from socketserver import UDPServer\n")
    write(deep, "site.py",
          "import pkg.helper\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return pkg.other.UDPServer((host, port), handler)\n")
    unlicensed = bind_site_scan.scan(root=deep)
    if not unlicensed["ok"] or unlicensed["sites"] != 0:
        bad.append("unlicensed-sites-%d" % unlicensed["sites"])
    # a subclass through the chain is a server-subclass like any other.
    sub = fresh_world("bsc23-sub")
    write(sub, "pkg/helper.py", "from socketserver import UDPServer\n")
    write(sub, "site.py",
          "import pkg.helper\n"
          "\n"
          "class Face(pkg.helper.UDPServer):\n"
          "    allow_reuse_address = True\n")
    sv = bind_site_scan.scan(root=sub)
    if sv["ok"]:
        bad.append("triple-subclass-passed")
    srows = [r for r in sv["refused"] if r["kind"] == "server-subclass"]
    if not srows:
        bad.append("triple-subclass-not-named")
    elif not srows[0]["detail"].startswith("pkg.helper.UDPServer"):
        bad.append("subclass-detail-%s" % srows[0]["detail"])
    report("AC-BSC23", bool(bad), ",".join(bad))

    # ---- AC-BSC23b: the chain is followed through aliases and modules ------
    bad = []
    alias_root = fresh_world("bsc23b-alias")
    write(alias_root, "pkg/helper.py", "from socketserver import UDPServer\n")
    write(alias_root, "site.py",
          "import pkg.helper\n"
          "\n"
          "Maker = pkg.helper.UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return Maker((host, port), handler)\n")
    av = bind_site_scan.scan(root=alias_root)
    if av["ok"]:
        bad.append("alias-passed")
    arows = [r for r in av["refused"] if r["path"] == "site.py"]
    if not arows:
        bad.append("alias-not-named")
    elif arows[0]["detail"] != (
            "Maker->pkg.helper.UDPServer->socketserver.UDPServer"):
        bad.append("alias-detail-%s" % arows[0]["detail"])
    # the middle hop is measured on the map, not inferred from the detail text.
    exports = bind_site_scan.repo_reexports(alias_root)
    if exports.get("site", {}).get("Maker") != (
            "pkg.helper.UDPServer->socketserver.UDPServer"):
        bad.append("alias-map-%s" % exports.get("site"))
    # a second module borrowing the alias resolves through the same chain.
    write(alias_root, "borrow.py",
          "from site import Maker\n"
          "\n"
          "def boot2(host, port, handler):\n"
          "    return Maker((host, port), handler)\n")
    bv = bind_site_scan.scan(root=alias_root)
    brows = [r for r in bv["refused"] if r["path"] == "borrow.py"]
    if not brows:
        bad.append("borrow-not-named")
    elif not brows[0]["detail"].startswith("Maker(from site)->"):
        bad.append("borrow-detail-%s" % brows[0]["detail"])
    # without the bare dotted import, the same assignment is not a licence.
    bad_root = fresh_world("bsc23b-unlicensed")
    write(bad_root, "pkg/helper.py", "from socketserver import UDPServer\n")
    write(bad_root, "pkg/other.py", "from socketserver import UDPServer\n")
    write(bad_root, "site.py",
          "import pkg.helper\n"
          "\n"
          "Maker = pkg.other.UDPServer\n"
          "\n"
          "def boot(host, port, handler):\n"
          "    return Maker((host, port), handler)\n")
    uv = bind_site_scan.scan(root=bad_root)
    if not uv["ok"] or uv["sites"] != 0:
        bad.append("alias-unlicensed-sites-%d" % uv["sites"])
    report("AC-BSC23b", bool(bad), ",".join(bad))

    # ---- AC-BSC24: the live tree does not move a line, and the red control
    # is the PRE-R2973 binary on the same private world ----------------------
    bad = []
    live = bind_site_scan.scan(root=HERE)
    if not live["ok"]:
        bad.append("shipped-tree-refused")
    if live["sites"] != 14:
        bad.append("live-sites-%d" % live["sites"])
    if live["by_kind"] != {"http-server": 8, "server-subclass": 2,
                           "socket-bind": 3, "ws-serve": 1}:
        bad.append("live-kinds-%s" % sorted(live["by_kind"].items()))
    old = subprocess.run(["git", "show", PRE_R2973_REV
                          + ":src/sandbox/bind_site_scan.py"],
                         cwd=REPO, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if old.returncode != 0 or not old.stdout:
        bad.append("no-old-bytes")
    else:
        old_leaf = os.path.join(WORLD, "bind_site_scan_prer2973.py")
        with open(old_leaf, "wb") as handle:
            handle.write(old.stdout)
        before = subprocess.run(
            [sys.executable, old_leaf, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        after = subprocess.run(
            [sys.executable, LEAF, "--list", "--root", HERE],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        if before.returncode != 0 or after.returncode != 0:
            bad.append("list-rc-%d/%d" % (before.returncode, after.returncode))
        if before.stdout != after.stdout:
            bad.append("live-lines-moved")
        # red control on the world AC-BSC23 built in its unguarded form.
        red_world = fresh_world("bsc24-red")
        write(red_world, "pkg/helper.py",
              "from socketserver import UDPServer\n")
        write(red_world, "site.py", raw_site)
        old_world = subprocess.run(
            [sys.executable, old_leaf, "--root", red_world],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        new_world = subprocess.run(
            [sys.executable, LEAF, "--root", red_world],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=120)
        if b"sites=0" not in old_world.stdout:
            bad.append("old-saw-the-shape")
        if not (old_world.returncode == 0 and new_world.returncode != 0):
            bad.append("red-rc-%d/%d" % (old_world.returncode,
                                         new_world.returncode))
        if b"E_BIND_UNGUARDED_FACE" not in new_world.stdout:
            bad.append("new-not-refused")
        os.remove(old_leaf)
    # the declaration, measured independently: the new shape has no live
    # instance, so what this round buys is a shape that can no longer pass
    # unjudged - not a live hole that was closed.
    facts = triple_attr_facts(HERE)
    if facts["landing_imports"]:
        bad.append("dotted-imports-land-%s" % facts["landing_imports"][:3])
    if facts["landing_calls"]:
        bad.append("triple-calls-land-%s" % facts["landing_calls"][:3])
    if facts["export_hits"]:
        bad.append("triple-export-hits-%s" % facts["export_hits"][:3])
    if facts["triple_bases"]:
        bad.append("triple-bases-%s" % facts["triple_bases"][:3])
    report("AC-BSC24", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
