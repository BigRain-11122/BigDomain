"""Suite for the static bind-site gate that bounds R2942's disclosed hole.

Criteria AC-BSC1..AC-BSC14. AC-BSC1..AC-BSC5 were pinned in src/os/backlog.md
BEFORE this file, src/sandbox/bind_site_scan.py and src/sandbox/bind_sites.json
existed (in-window pre-registration, disclosed); AC-BSC6..AC-BSC7 came with the
asyncio kind (R2944), AC-BSC8..AC-BSC9 with its order/level rule (R2945),
AC-BSC10..AC-BSC12 with the same rule applied to ws-serve (R2946), and
AC-BSC13..AC-BSC14 with the unix half of the asyncio family (R2969).

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

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
