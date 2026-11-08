"""Measure three candidate limits of THIS face. Read-only.

Every world is private and the honest answer is `b`; the three answers are the
seed for the next tech row and are measured, never guessed.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_scope as MAA2  # noqa: E402

HW = 'ATTR = "b"\n'
TAIL = 'for name in hw.NAMES:\n    pass\n'
HW2 = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnam-lim2-")
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
    measure("(1) ANNOTATED module-alias head (M: object = consts)",
            {"hw.py": HW2,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nM: object = consts\nBASE = M.HW\n"
                      "REG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(2) WALRUS module-alias head ((M := consts))",
            {"hw.py": HW2,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\n(M := consts)\nBASE = M.HW\n"
                      "REG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(3) a THREE-step attribute path (a.B.C.HW)",
            {"hw.py": HW2,
             "consts.py": 'HW = "hw"\n',
             "b.py": "B = consts\n",
             "a.py": "C = b\n",
             "mk.py": "import a\nBASE = a.C.B.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())