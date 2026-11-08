"""Measure the four shapes this window closes (AC-PNAA1..AC-PNAA4). Read-only.

Every world is private and the honest answer is `b`; the reading is taken with
the SHIPPED face, so the numbers printed here are what a reader could get
BEFORE this window own code existed.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_scope as MAA2  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = 'for name in hw.NAMES:\n    pass\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
CALL = ("with mk.REG() as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnaa-lim-")
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
        rows = MAA2.module_alias_alias_report(probe, root)["loops"]
        row = rows[-1]
        got = MAA2.module_alias_entry("KEY", probe, row["scope"], row["line"],
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
    measure("(A) WALRUS module-alias head ((M := consts))",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\n(M := consts)\nBASE = M.HW\n"
                      "REG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(B) RELATIVE from-import at the call site",
            {"hw.py": HW,
             "pkg/__init__.py": "",
             "pkg/mk.py": 'def mkmod():\n    return "hw"\n',
             "pkg/probe_conf.py": "from .mk import mkmod as REG\n"},
            "from . import probe_conf as mk\n" + CALL + TAIL, out)
    measure("(C) RELATIVE from-import of a name that is NOT a function",
            {"hw.py": HW,
             "pkg/__init__.py": "",
             "pkg/mk.py": 'CONST = "hw"\n',
             "pkg/probe_conf3.py": "from .mk import CONST as REG\n"},
            "from . import probe_conf3 as mk\n" + CALL + TAIL, out)
    measure("(D) RELATIVE from-imported MODULE alias head",
            {"hw.py": HW,
             "pkg/__init__.py": "",
             "pkg/consts.py": 'HW = "hw"\n',
             "pkg/mk4.py": "from . import consts\nM = consts\nBASE = M.HW\n"
                           "REG = BASE\n"},
            "import pkg.mk4 as mk\n" + RECV + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())