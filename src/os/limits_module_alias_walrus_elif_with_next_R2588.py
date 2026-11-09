"""Measure the NEXT shapes on the R2588 elif/with face (queue successor seed).

Run BEFORE any successor code exists, so the next row states a measured limit
rather than a guess. Private temporary worlds only.

Shapes measured on the committed face:
  (a) a WALRUS inside a module-level `while` body
  (b) a WALRUS inside a `match` case body
  (c) a WALRUS inside a module-level `with` whose body also holds a nested
      `if` branch (must keep the with read and not descend)
  (d) a WALRUS inside an `elif` whose if-chain is three links long

Exit 0 = the four answers are published.
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
    ("N5 while body",
     "import consts\nwhile a1:\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("N6 match case body",
     "import consts\nmatch a1:\n    case 1:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("N7 with body holding a nested if",
     "import consts\nwith a1:\n    if a2:\n        pass\n"
     "    (M := consts)\nBASE = M.HW\nREG = BASE\n"),
    ("N8 three-link if/elif/elif chain",
     "import consts\nif a1:\n    pass\nelif a2:\n    pass\n"
     "elif a3:\n    (M := consts)\nelse:\n    pass\n"
     "BASE = M.HW\nREG = BASE\n"),
]


def world(body):
    root = tempfile.mkdtemp(prefix="pnac-next-")
    for name, text in (("hw.py", HW), ("consts.py", 'HW = "hw"\n'),
                       ("mk.py", body)):
        with open(os.path.join(root, name), "w", encoding="utf-8",
                  newline="\n") as handle:
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
    for label, body in SHAPES:
        root = world(body)
        try:
            got = entry(PNAC, "import mk\n" + RECV + TAIL, root)
            print("%s -> state=%s value=%s reason=%s reads=%s"
                  % (label, got.get("state"), got.get("value"),
                     got.get("reason"), got.get("branch_reads") or []))
        finally:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())