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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_scope as PNAF  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

WORLDS = [
    ("one while with TWO matches and a SECOND while with one (label clash)",
     "import consts\nimport consts2\nimport consts3\n"
     "while a1:\n"
     "    match x:\n        case 1:\n            (M := consts)\n"
     "    match y:\n        case 1:\n            (M := consts2)\n"
     "while a2:\n"
     "    match z:\n        case 1:\n            (M := consts3)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("two matches inside ONE while else section (ordinal label shape)",
     "import consts\nimport consts2\nwhile a1:\n    pass\nelse:\n"
     "    match x:\n        case 1:\n            (M := consts)\n"
     "    match y:\n        case 1:\n            (M := consts2)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("match inside a for body nested in a while (refused)",
     "import consts\nwhile a1:\n    for x in (1,):\n"
     "        match y:\n            case 1:\n                (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("match nested one level in a while inside another while (refused)",
     "import consts\nwhile a1:\n    while a2:\n"
     "        match x:\n            case 1:\n                (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("walrus bound by an if nested inside a match case (refused)",
     "import consts\nwhile a1:\n    match x:\n        case 1:\n"
     "            if a2:\n                (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("two while bodies each with one match on one name (both named)",
     "import consts\nimport consts2\n"
     "while a1:\n    match x:\n        case 1:\n            (M := consts)\n"
     "while a2:\n    match y:\n        case 1:\n            (M := consts2)\n"
     "BASE = M.HW\nREG = BASE\n"),
]


def world(files):
    root = tempfile.mkdtemp(prefix="pnaf-next-")
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
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            got = entry(PNAF, "import mk\n" + RECV + TAIL, root)
            print("%s\n  -> state=%s value=%s reason=%s reads=%s"
                  % (label, got.get("state"), got.get("value"),
                     got.get("reason"), got.get("branch_reads")))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())