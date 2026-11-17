"""Battery suite for tools/lobby_protocol_map.py - criteria AC-LPM1..AC-LPM6.

AC-LPM1..AC-LPM6 were pinned in src/os/backlog.md at R2787, BEFORE the tool
existed; this suite is what finally puts them under a battery row. Every check
runs inside a PRIVATE world created under a temp directory, because AC-LPM5 is a
negative control that rewrites the spec and the shipped docs/spec file must
never be touched by a test run.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""
import ast
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "lobby_protocol_map.py")

FAILS = []
CHECKS = []


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("  | PASS %s %s" % (name, detail))
    else:
        FAILS.append(name)
        print("  | FAIL %s %s" % (name, detail))


def write(path, text):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def read(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_tool():
    spec = importlib.util.spec_from_file_location("lpm_under_test", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def world():
    """A private world: one spec section, two crit rows, one impl file."""
    d = tempfile.mkdtemp(prefix="lpm-")
    spec = os.path.join(d, "docs", "spec", "lobby-websocket-spec.md")
    write(spec,
          "# spec\n"
          "\n"
          "## \u4e00\u3001 protocol surface\n"
          "\n"
          "The server answers `sys.hello` first, then `room.ping` on demand.\n"
          "A sample frame carries `payload.rooms` as a field path, and\n"
          "`room.spec_only` is specified but never implemented.\n"
          "\n"
          "| # | row | method |\n"
          "|---|---|---|\n"
          "| AC-S1 | first frame is `sys.hello` | assert |\n"
          "\n"
          "## \u4e8c\u3001 production rows\n"
          "\n"
          "| # | row | method |\n"
          "|---|---|---|\n"
          "| AC-P1 | not local | blocked |\n")
    impl = os.path.join(d, "src", "sandbox", "lobby", "server.py")
    write(impl, "# both names exist in the shipped surface\n"
                "HELLO = 'sys.hello'\nPING = 'room.ping'\n")
    write(os.path.join(d, "docs", "readme.txt"), "placeholder so the walk has a file\n")
    return d, spec, impl


def point(mod, d):
    mod.ROOT = d
    mod.SPEC = os.path.join(d, "docs", "spec", "lobby-websocket-spec.md")
    mod.HTML = os.path.join(d, "preview", "lobby-protocol-map.html")
    mod.JSON_OUT = os.path.join(d, "preview", "lobby-protocol-map.json")
    mod.IMPL = os.path.join(d, "src", "sandbox", "lobby", "server.py")


def tool_literals():
    """Every string literal in the tool source, by AST."""
    tree = ast.parse(read(TOOL))
    return [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def imports_of(path):
    tree = ast.parse(read(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def main():
    # the real tree is read first, so AC-LPM1 compares against the vocabulary
    # that actually ships instead of a hand-written list inside this test.
    real = load_tool().payload()
    real_vocab = set(m["token"] for m in real["messages"]) | set(
        m["token"] for m in real["field_paths"])

    mod = load_tool()
    d, spec, impl = world()
    try:
        point(mod, d)

        # ---------------- AC-LPM1 ----------------
        try:
            lits = tool_literals()
            bad = sorted(set(l for l in lits if l in real_vocab))
            ok("AC-LPM1a", real["message_count"] > 0 and not bad,
               "real_vocab=%d literals_equal=%r" % (len(real_vocab), bad[:3]))
            # derivation proof: a name that exists ONLY in the private spec lands
            text = read(spec).replace("room.ping", "room.custom_probe")
            write(spec, text)
            write(impl, read(impl).replace("room.ping", "room.custom_probe"))
            p = mod.payload()
            names = [m["token"] for m in p["messages"]]
            ok("AC-LPM1b", "room.custom_probe" in names and "room.ping" not in names,
               "derived messages=%r" % (sorted(names),))
        except Exception as exc:  # noqa: BLE001
            ok("AC-LPM1", False, "%s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-LPM2 ----------------
        try:
            msgs = {m["token"]: m for m in p["messages"]}
            hello = msgs.get("sys.hello", {})
            ok("AC-LPM2a", hello.get("criteria") == ["AC-S1"],
               "sys.hello criteria=%r" % (hello.get("criteria"),))
            ok("AC-LPM2b", bool(hello.get("sections")) and hello["sections"][0].startswith("\u4e00"),
               "section=%r" % (hello.get("sections"),))
            unc = p["uncovered"]
            ok("AC-LPM2c", "room.custom_probe" in unc and hello["covered"] is True
               and msgs["room.custom_probe"]["covered"] is False,
               "uncovered=%r" % (unc,))
            spec_only = [t["token"] for t in p["field_paths"]]
            ok("AC-LPM2d", msgs["room.custom_probe"]["implemented"] is True
               and "room.spec_only" in spec_only,
               "implemented probe=True spec_only=%r" % (spec_only,))
        except Exception as exc:  # noqa: BLE001
            ok("AC-LPM2", False, "%s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-LPM3 ----------------
        try:
            mod.write_artifacts()
            html = read(mod.HTML)
            ok("AC-LPM3a", "http://" not in html and "https://" not in html,
               "scheme literals=0")
            import re as _re
            hrefs = _re.findall(r'(?:href|src)="([^"]+)"', html)
            missing = [h for h in hrefs
                       if not h.startswith("#") and not os.path.exists(os.path.join(d, h))]
            ok("AC-LPM3b", not missing, "hrefs=%d missing=%r" % (len(hrefs), missing[:3]))
        except Exception as exc:  # noqa: BLE001
            ok("AC-LPM3", False, "%s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-LPM4 ----------------
        try:
            before = read(mod.HTML)
            jbefore = read(mod.JSON_OUT)
            mod.write_artifacts()
            same = (read(mod.HTML) == before and read(mod.JSON_OUT) == jbefore)
            rec = json.loads(jbefore)
            ok("AC-LPM4a", same, "second render byte-identical=%s" % same)
            ok("AC-LPM4b", rec.get("spec_bytes") == os.path.getsize(spec),
               "recorded=%r disk=%d" % (rec.get("spec_bytes"), os.path.getsize(spec)))
        except Exception as exc:  # noqa: BLE001
            ok("AC-LPM4", False, "%s: %s" % (type(exc).__name__, exc))

        # ---------------- AC-LPM5 ----------------
        try:
            h0 = os.stat(mod.HTML)
            b0 = read(mod.HTML)
            j0 = os.stat(mod.JSON_OUT)
            jb0 = read(mod.JSON_OUT)
            rc = mod.check()
            h1 = os.stat(mod.HTML)
            j1 = os.stat(mod.JSON_OUT)
            ok("AC-LPM5a", rc == 0 and (h0.st_mtime_ns, h0.st_size) == (h1.st_mtime_ns, h1.st_size)
               and (j0.st_mtime_ns, j0.st_size) == (j1.st_mtime_ns, j1.st_size)
               and read(mod.HTML) == b0 and read(mod.JSON_OUT) == jb0,
               "rc=%d read-only=True" % rc)
            # negative control: a whole criterion row is deleted after the
            # artifacts landed, so the recorded spec size can no longer match
            original = read(spec)
            keep = [l for l in original.splitlines() if "AC-S1" not in l]
            write(spec, "\n".join(keep) + "\n")
            rc2 = mod.check()
            ok("AC-LPM5b", rc2 == 2, "rc=%d after a spec row vanished" % rc2)
            # restore the exact original, and prove the red was about the spec
            # rather than a sticky failure
            write(spec, original)
            mod.write_artifacts()
            ok("AC-LPM5c", mod.check() == 0, "restored rc=0")
        except Exception as exc:  # noqa: BLE001
            ok("AC-LPM5", False, "%s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(d, ignore_errors=True)

    # ---------------- AC-LPM6 ----------------
    try:
        src = read(TOOL)
        ok("AC-LPM6a", all(ord(c) < 128 for c in src), "pure ascii=True")
        names = imports_of(TOOL)
        allowed = {"argparse", "json", "os", "re", "sys", "io", "ast", "tempfile"}
        bad = sorted(n for n in names if n not in allowed)
        ok("AC-LPM6b", not bad, "imports=%r bad=%r" % (sorted(names), bad))
        html = read(os.path.join(ROOT, "preview", "lobby-protocol-map.html"))
        ok("AC-LPM6c", html.count("<script") == 1, "inline scripts=%d" % html.count("<script"))
        ok("AC-LPM6d", html.count(mod.NS) >= 1, "namespace=%s hits=%d"
           % (mod.NS, html.count(mod.NS)))
    except Exception as exc:  # noqa: BLE001
        ok("AC-LPM6", False, "%s: %s" % (type(exc).__name__, exc))

    total = len(CHECKS)
    # Declared units (R2860): the AC inventory below is derived from CHECKS,
    # never echoed from the registry - a declaration copied out of the
    # registry could never disagree with it.
    acs = set()
    for name in CHECKS:
        token = name.split(' ', 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print('suite: %d assertions over %d criteria' % (total, len(acs)))
    if FAILS:
        print("SUITE FAIL %d/%d :: %r" % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
