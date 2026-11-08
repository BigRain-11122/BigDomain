"""Measure three candidate limits through the NEW face (module-alias-attribute).

Read-only. Prints the measured answer for shapes where the honest answer is `b`.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_scope as MAA  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = "for name in hw.NAMES:\n    pass\n"
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
CALL = ("with mk.REG() as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnpma-lim2-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def measure(label, files, probe, out):
    root = world(files)
    try:
        rows = MAA.module_alias_attribute_report(probe, root)["loops"]
        row = rows[-1]
        got = MAA.module_alias_entry("KEY", probe, row["scope"], row["line"],
                                     root=root)
        line = "%s -> state=%s value=%s reason=%s hop=%s chain=%s" % (
            label, got.get("state"), got.get("value"), got.get("reason"),
            got.get("ma_hop"), got.get("ma_chain"))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(line)
    out.append(line)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out = []
    measure("(a) attribute head bound by a module ALIAS (M = consts)",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nM = consts\nBASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(b) two-step attribute path (consts.INNER.HW)",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "inner.py": "INNER = consts\n",
             "mk.py": ("import consts\nimport inner\n"
                       "BASE = inner.INNER.HW\nREG = BASE\n")},
            "import mk\n" + RECV + TAIL, out)
    measure("(d) call context on a FROM-imported function name",
            {"hw.py": HW,
             "mk.py": ('def mkmod():\n    return "hw"\n'),
             "probe_conf.py": "from mk import mkmod as REG\n"},
            "import probe_conf as mk\n" + CALL + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
