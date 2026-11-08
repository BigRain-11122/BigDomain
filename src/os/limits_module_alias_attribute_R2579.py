"""Measure the three limits the AC-PNMA1 row names, through the shipped face.

Read-only. Each shape is built in a private temporary world where the honest
answer is "b" and the shipped reading is printed as measured, not predicted.
Stdlib only, ASCII source, zero network, no clock.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = "for name in hw.NAMES:\n    pass\n"


def world(files):
    root = tempfile.mkdtemp(prefix="pnpma-lim-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def read(got):
    return ("state=%s value=%s reason=%s cs_state=%s cs_reason=%s "
            "ma_state=%s ma_value=%s ma_reason=%s ma_hop=%s chain=%s"
            % (got.get("state"), got.get("value"), got.get("reason"),
               got.get("cs_state"), got.get("cs_reason"),
               got.get("ma_state"), got.get("ma_value"),
               got.get("ma_reason"), got.get("ma_hop"), got.get("ma_chain")))


def measure(label, files, probe, out):
    root = world(files)
    try:
        rows = MA.module_alias_report(probe, root)["loops"]
        row = rows[-1]
        got = MA.module_alias_entry("KEY", probe, row["scope"], row["line"],
                                    root=root)
        line = "%s -> %s" % (label, read(got))
        print(line)
        out.append(line)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    out = []
    receiver = ("with mk.REG as m:\n"
                "    if a1:\n        KEY = m.ATTR\n"
                "    else:\n        KEY = m.ATTR\n")
    measure("(1) attribute-final alias chain",
            {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nBASE = consts.HW\nREG = BASE\n"},
            "import mk\n" + receiver + TAIL, out)
    measure("(2) function returning a name bound to a class attribute",
            {"hw.py": HW,
             "mk.py": ('class Box:\n    NAME = "hw"\n'
                       'REG2 = Box.NAME\n'
                       'def make():\n    return REG2\n'
                       'REG = make()\n')},
            "import mk\n" + receiver + TAIL, out)
    call_receiver = ("with mk.REG() as m:\n"
                     "    if a1:\n        KEY = m.ATTR\n"
                     "    else:\n        KEY = m.ATTR\n")
    measure("(3) call context on an alias chain name",
            {"hw.py": HW,
             "mk.py": ('def mkmod():\n    return "hw"\n'
                       'REG = mkmod\n')},
            "import mk\n" + call_receiver + TAIL, out)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())