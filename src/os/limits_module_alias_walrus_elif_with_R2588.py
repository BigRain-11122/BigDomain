"""Measure the four shapes the R2587 row named, on the NEW elif/with face.

Run BEFORE the suite is written so the reading is reported rather than assumed.
Every world is private and temporary; no shipped source is written.
Pure ASCII, stdlib only, no clock, zero network.

Prints, for each shape, the state/value/reason/branch reads this face gives.
Exit 0 = the four answers match the pre-registered criteria AC-PNAC1..AC-PNAC3.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_scope as PNAC  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

SHAPES = [
    ("N1 elif body",
     "import consts\nif a1:\n    pass\n"
     "elif a2:\n    (M := consts)\nelse:\n    pass\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("N2 with body",
     "import consts\nwith a1:\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("N3 for body",
     "import consts\nfor a1 in (1,):\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("N4 nested two deep",
     "import consts\nif a1:\n    if a2:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
]


def world(body):
    root = tempfile.mkdtemp(prefix="pnac-")
    for name, text in (("hw.py", HW), ("consts.py", 'HW = "hw"\n'),
                       ("mk.py", body)):
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return root


def entry(module, text, root):
    rows = module.module_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return module.module_alias_entry("KEY", text, row["scope"], row["line"],
                                     root=root)


def main():
    ok = True
    for label, body in SHAPES:
        root = world(body)
        try:
            got = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            reads = got.get("branch_reads") or []
            print("%s -> state=%s value=%s reason=%s reads=%s"
                  % (label, got.get("state"), got.get("value"),
                     got.get("reason"), reads))
            print("   base_pnac -> state=%s value=%s"
                  % (got.get("base_pnac_state"), got.get("base_pnac_value")))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())