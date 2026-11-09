"""Measure the successor row's candidate shapes with THIS round face.

Read-only: every world is private and nothing shipped is written. Each label
states the honest answer, so a mismatch is visible rather than judged.
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_scope as PNAE  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

WORLDS = [
    ("while body and while else on one name (honest ambiguous, both named)",
     "import consts\nimport consts2\n"
     "while a1:\n    (M := consts)\n"
     "else:\n    (M := consts2)\nBASE = M.HW\nREG = BASE\n"),
    ("two lone matches in ONE while body (honest refused, named once)",
     "import consts\nimport consts2\n"
     "while a1:\n"
     "    match x:\n        case 1:\n            (M := consts)\n"
     "    match y:\n        case 1:\n            (M := consts2)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("for else section (honest refused)",
     "import consts\nfor a1 in (1,):\n    pass\nelse:\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("match nested in a while else section (honest refused)",
     "import consts\nwhile a1:\n    pass\nelse:\n    match x:\n"
     "        case 1:\n            (M := consts)\nBASE = M.HW\nREG = BASE\n"),
    ("match nested two levels in a while body (honest refused)",
     "import consts\nwhile a1:\n    with a2:\n        match x:\n"
     "            case 1:\n                (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("two cases nested in one while body naming both (honest refused, both "
     "named)",
     "import consts\nimport consts2\n"
     "while a1:\n"
     "    match x:\n        case 1:\n            (M := consts)\n"
     "        case 2:\n            (M := consts2)\n"
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
            got = entry(PNAE, "import mk\n" + RECV + TAIL, root)
            print("%s\n  -> state=%s value=%s reason=%s reads=%s"
                  % (label, got.get("state"), got.get("value"),
                     got.get("reason"), got.get("branch_reads")))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())