"""Measure the limits THIS window leaves open, with the face it just shipped.

Read-only; every world is private. The three shapes below are NOT followed by
the branch face on purpose, so they are named rather than claimed.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_scope as PNAB  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = 'for name in hw.NAMES:\n    pass\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnab-next-")
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
        rows = PNAB.module_alias_report(probe, root)["loops"]
        row = rows[-1]
        got = PNAB.module_alias_entry("KEY", probe, row["scope"], row["line"],
                                      root=root)
        line = "%s -> state=%s value=%s reason=%s reads=%s" % (
            label, got.get("state"), got.get("value"), got.get("reason"),
            got.get("branch_reads"))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(line)
    out.append(line)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out = []
    measure("(N1) WALRUS inside a module-level elif branch",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nif a0:\n    pass\nelif a1:\n"
                      "    (M := consts)\nBASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(N2) WALRUS inside a module-level with body",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nwith open(__file__):\n"
                      "    (M := consts)\nBASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(N3) WALRUS inside a module-level for body",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nfor _i in range(1):\n"
                      "    (M := consts)\nBASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    measure("(N4) WALRUS inside a branch nested two levels deep",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nif a0:\n    if a1:\n"
                      "        (M := consts)\nBASE = M.HW\nREG = BASE\n"},
            "import mk\n" + RECV + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())