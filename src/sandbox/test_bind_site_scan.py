"""Suite for the static bind-site gate that bounds R2942's disclosed hole.

Five criteria AC-BSC1..AC-BSC5. They were pinned in src/os/backlog.md BEFORE
this file, src/sandbox/bind_site_scan.py and src/sandbox/bind_sites.json
existed (in-window pre-registration, disclosed).

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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAF = os.path.join(HERE, "bind_site_scan.py")
BASELINE = os.path.join(HERE, "bind_sites.json")
FRONTDOOR = os.path.join(HERE, "frontdoor.py")
START_ALL = os.path.join(HERE, "start_all.py")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "bind-site-scan"
WORLD = os.path.join(REPO, "logs", "bind-scan-suite")

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

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
