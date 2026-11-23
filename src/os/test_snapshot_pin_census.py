"""AC-SPC1..AC-SPC7 for tools/snapshot_pin_census.py (R3348).

The criteria were pinned in src/os/backlog.md BEFORE this suite or the tool
existed. Every arm builds its own corpus inside a private temp dir and asks the
shipped functions, so nothing here can pass on live-tree state - and the one
live reading is deliberately a floor (files > 700, zero unreadable shipped)
rather than a pinned count, which would be the very defect this tool names.

Pure ASCII, stdlib only, no network, no clock, no writes outside the temp dir.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL_REL = os.path.join(ROOT, "tools", "snapshot_pin_census.py")
REGISTRY_REL = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

FAILS = []


def check(name, ok, detail):
    print("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)


def load(path, alias):
    spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(directory, name, text, bom=False, binary=False):
    path = os.path.join(directory, name)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        payload = text.encode("utf-8") if not binary else text
        if bom:
            payload = b"\xef\xbb\xbf" + payload
        handle.write(payload)
    return path


def labels_of(result):
    return dict((pin["file"], pin["label"]) for pin in result["rows"])


def main():
    tool = load(TOOL_REL, "_spc_tool")
    source = open(TOOL_REL, "r", encoding="utf-8").read()
    tmp = tempfile.mkdtemp(prefix="spc-")
    try:
        # ---------------- AC-SPC1 ----------------
        corpus = os.path.join(tmp, "corpus")
        write(corpus, "test_ok.py",
              "ITEMS = [1, 2, 3]\n"
              "def case():\n"
              "    assert len(ITEMS) == 3, 'pinned'\n")
        write(corpus, "test_bom.py",
              "def case():\n"
              "    assert len([1]) == 1\n", bom=True)
        write(corpus, "test_bad.py", "def case(:\n    pass\n")
        write(corpus, "helper.py", "assert len([1]) == 1\n")
        write(os.path.join(corpus, "qa"), "test_hidden.py",
              "def case():\n    assert len([1]) == 1\n")
        result = tool.census(corpus)
        live = tool.census()
        shipped = [path for path in live["unreadable"]
                   if not os.path.basename(path).startswith("test_")]
        counted = set(pin["file"] for pin in result["rows"])
        check("AC-SPC1", result["files"] == 3
              and result["bom"] == ["test_bom.py"]
              and result["unreadable"] == ["test_bad.py"]
              and "test_bom.py" in counted
              and "test_bad.py" not in counted
              and "helper.py" not in counted
              and live["files"] > 700 and not shipped,
              "files=%d bom=%s unreadable=%s counted=%s live_files=%d "
              "unreadable_shipped=%d"
              % (result["files"], result["bom"], result["unreadable"],
                 sorted(counted), live["files"], len(shipped)))

        # ---------------- AC-SPC2 ----------------
        shape = os.path.join(tmp, "shape")
        write(shape, "test_shape.py",
              "def case():\n"
              "    a = [1]\n"
              "    b = [1, 2]\n"
              "    x = 1\n"
              "    assert len(a) == 1\n"
              "    assert len(a) > 0\n"
              "    assert len(a) == len(b)\n"
              "    assert x == 1\n"
              "    assert len(a) != 2\n"
              "    assert len(a) >= 1\n"
              "    assert (len(a) == 1)\n")
        shaped = tool.census(shape)
        lines = sorted(pin["line"] for pin in shaped["rows"])
        mutated = os.path.join(tmp, "mutated")
        write(mutated, "test_shape.py",
              "def case():\n"
              "    a = [1]\n"
              "    b = [1, 2]\n"
              "    x = 1\n"
              "    assert len(a) >= 1\n"
              "    assert len(a) > 0\n"
              "    assert len(a) == len(b)\n"
              "    assert x == 1\n"
              "    assert len(a) != 2\n"
              "    assert len(a) >= 1\n"
              "    assert (len(a) == 1)\n")
        after = tool.census(mutated)
        check("AC-SPC2", lines == [5, 9, 11] and after["pins"] == 2,
              "lines=%s pins=%d mutated_pins=%d"
              % (lines, shaped["pins"], after["pins"]))

        # ---------------- AC-SPC3 ----------------
        trace = os.path.join(tmp, "trace")
        write(trace, "test_ambient.py",
              "PAGE = '/tmp/whatever.html'\n"
              "TEXT = open(PAGE, encoding='utf-8').read()\n"
              "def case():\n"
              "    assert TEXT.count('fetch(') == 1\n")
        write(trace, "test_private.py",
              "def case():\n"
              "    items = [1, 2, 3]\n"
              "    assert len(items) == 3\n")
        write(trace, "test_foreign.py",
              "import json\n"
              "def case():\n"
              "    assert len(json.loads('[]')) == 0\n")
        write(trace, "test_local_open.py",
              "def _open(world):\n"
              "    return world\n"
              "def case():\n"
              "    assert len(_open([])) == 0\n")
        traced = labels_of(tool.census(trace))
        check("AC-SPC3", traced == {
            "test_ambient.py": "ambient",
            "test_private.py": "private",
            "test_foreign.py": "foreign",
            "test_local_open.py": "private",
        }, "labels=%s" % traced)

        # ---------------- AC-SPC4 ----------------
        pair = os.path.join(tmp, "pair")
        write(pair, "test_from_disk.py",
              "def case():\n"
              "    value = open('/tmp/x.txt').read()\n"
              "    assert value.count('a') == 1\n")
        write(pair, "test_from_literal.py",
              "def case():\n"
              "    value = 'abc'\n"
              "    assert value.count('a') == 1\n")
        paired = labels_of(tool.census(pair))
        same_expr = [pin["expr"] for pin in tool.census(pair)["rows"]]
        check("AC-SPC4", paired == {"test_from_disk.py": "ambient",
                                    "test_from_literal.py": "private"}
              and same_expr[0] == same_expr[1],
              "labels=%s same_expr=%s" % (paired, same_expr))

        # ---------------- AC-SPC5 ----------------
        order = os.path.join(tmp, "order")
        write(order, "test_b.py",
              "def case():\n"
              "    items = [1]\n"
              "    assert len(items) == 1\n")
        write(order, "test_a.py",
              "import json\n"
              "def case():\n"
              "    assert len(json.loads('[]')) == 0\n"
              "    assert len([1]) == 1\n")
        ordered = tool.census(order)
        repin = tool.repin_order(ordered)
        expected = [pin for pin in ordered["rows"]
                    if pin["label"] != "private"]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = tool.main(["--root", order, "--order"])
        rendered = [line for line in buffer.getvalue().splitlines()
                    if line.startswith("REPIN ")]
        check("AC-SPC5", rc == 0
              and [pin["file"] for pin in repin] == [pin["file"] for pin in expected]
              and len(rendered) == len(repin)
              and "test_b.py" not in "".join(rendered),
              "repin=%d private_excluded=%d rc=%d lines=%d"
              % (len(repin), len(expected) - len(repin), rc, len(rendered)))

        # ---------------- AC-SPC6 ----------------
        listing_before = sorted(os.listdir(order))
        runs = []
        for _ in range(2):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = tool.main(["--root", order, "--json", "--order"])
            runs.append((rc, buf.getvalue()))
        listing_after = sorted(os.listdir(order))
        no_clock = "import time" not in source and "time." not in source
        no_write = ("os.makedirs" not in source
                    and 'raw = open(path, "rb").read()' in source
                    and '"w"' not in source)
        check("AC-SPC6", runs[0][0] == 0 and runs[1][0] == 0
              and runs[0][1] == runs[1][1]
              and listing_before == listing_after
              and no_clock and no_write,
              "json_bytes=%d identical=%s dir_unchanged=%s no_clock=%s "
              "no_write=%s"
              % (len(runs[0][1]), runs[0][1] == runs[1][1],
                 listing_before == listing_after, no_clock, no_write))

        # ---------------- AC-SPC7 ----------------
        budget = io.StringIO()
        with contextlib.redirect_stdout(budget):
            tight = tool.main(["--root", pair, "--max-ambient", "0"])
        loose_buf = io.StringIO()
        with contextlib.redirect_stdout(loose_buf):
            loose = tool.main(["--root", pair, "--max-ambient", "5"])
        off_buf = io.StringIO()
        with contextlib.redirect_stdout(off_buf):
            off = tool.main(["--root", pair])
        refuse_buf = io.StringIO()
        with contextlib.redirect_stdout(refuse_buf):
            refused = tool.main(["--root", os.path.join(tmp, "nope")])
        ambient = tool.census(pair)["counts"]["ambient"]
        check("AC-SPC7", tight == 2 and loose == 0 and off == 0
              and refused == 3 and ambient == 1
              and "excess=1" in budget.getvalue()
              and "REFUSE E_ROOT_MISSING" in refuse_buf.getvalue(),
              "ambient=%d tight=%d loose=%d off=%d refused=%d"
              % (ambient, tight, loose, off, refused))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    criteria = 7
    passed = criteria - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (passed, criteria, ",".join(FAILS)))
        return 1
    print("SUITE PASS %d/%d" % (criteria, criteria))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
