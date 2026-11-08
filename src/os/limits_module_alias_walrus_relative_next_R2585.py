"""Measure the two limits THIS window leaves open, with the face it just
shipped. Read-only; every world is private.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNAW  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = 'for name in hw.NAMES:\n    pass\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnaa-next-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def measure(label, files, probe, out):
    root = world(files)
    try:
        rows = PNAW.module_alias_report(probe, root)["loops"]
        row = rows[-1]
        got = PNAW.module_alias_entry("KEY", probe, row["scope"], row["line"],
                                      root=root)
        line = "%s -> state=%s value=%s reason=%s chain=%s" % (
            label, got.get("state"), got.get("value"), got.get("reason"),
            got.get("ma_chain"))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(line)
    out.append(line)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out = []
    measure("(N1) WALRUS inside a module-level if block",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nif True:\n    (M := consts)\n"
                      "BASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(N2) TWO-LEVEL relative from-import module alias head",
            {"hw.py": HW,
             "pkg/__init__.py": "",
             "pkg/consts.py": 'HW = "hw"\n',
             "pkg/inner/__init__.py": "",
             "pkg/inner/mk6.py": "from .. import consts\nM = consts\n"
                                 "BASE = M.HW\nREG = BASE\n"},
            "import pkg.inner.mk6 as mk\n" + RECV + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())