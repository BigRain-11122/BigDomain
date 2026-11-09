"""Measure the NEXT row's four shapes on the committed tree, read-only.

Every world is private, nothing shipped is written, and the honest answer of
each world is stated in its label so a mismatch is visible rather than judged.
The reading is the R2590 face, i.e. the parent this round extends.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_scope as PNAD  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

WORLDS = [
    ("while else section (honest b)",
     "import consts\nwhile a1:\n    pass\nelse:\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("two while bodies same name (honest refused, names both)",
     "import consts\nimport consts2\n"
     "while a1:\n    (M := consts)\n"
     "while a2:\n    (M := consts2)\nBASE = M.HW\nREG = BASE\n"),
    ("lone match nested in a while body (honest b)",
     "import consts\nwhile a1:\n    match x:\n        case 1:\n"
     "            (M := consts)\nBASE = M.HW\nREG = BASE\n"),
    ("with body nested in a while body (honest refused)",
     "import consts\nwhile a1:\n    with a2:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("branch nested two deep in a while body (honest refused)",
     "import consts\nwhile a1:\n    if a2:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("for body (honest refused)",
     "import consts\nfor a1 in (1,):\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
]


def world(files):
    root = tempfile.mkdtemp(prefix="pnae-next-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def entry(module, text, root):
    rows = module.module_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return module.module_alias_entry("KEY", text, row["scope"], row["line"],
                                     root=root)


def main():
    for label, body in WORLDS:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n', "mk.py": body})
        try:
            got = entry(PNAD, "import mk\n" + RECV + TAIL, root)
            print("%s\n  -> state=%s value=%s reason=%s reads=%s"
                  % (label, got.get("state"), got.get("value"),
                     got.get("reason"), got.get("branch_reads")))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())