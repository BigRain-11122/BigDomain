"""Re-measure the two gaps the R2588 row named, BEFORE any R2590 code.

Private worlds only; nothing shipped is written. Each world is built so the
honest answer is `b` and the parent readers are asked what they really say.
Exit 0 = every measurement matches the row; 2 = a mismatch.
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

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_scope as PNAC  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_scope as PNT  # noqa

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

WORLDS = [
    ("while body",
     "import consts\nwhile a1:\n    (M := consts)\nBASE = M.HW\nREG = BASE\n"),
    ("match case body",
     "import consts\nmatch x:\n    case 1:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("for body (kept refusal)",
     "import consts\nfor a1 in (1,):\n    (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
    ("nested branch (kept refusal)",
     "import consts\nif a1:\n    if a2:\n        (M := consts)\n"
     "BASE = M.HW\nREG = BASE\n"),
]


def world(files):
    root = tempfile.mkdtemp(prefix="pnad-lim-")
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
    print("LIMITS R2590 re-measured on the committed tree, before any code")
    fails = 0
    for label, body in WORLDS:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n', "mk.py": body})
        try:
            text = "import mk\n" + RECV + TAIL
            parent = entry(PNAC, text, root)
            base = entry(PNT, text, root)
            print("  %-28s pnac=%s/%s base=%s/%s"
                  % (label, parent.get("state"), parent.get("reason"),
                     base.get("state"), base.get("reason")))
            if parent.get("state") != PNAC.STATE_REFUSED:
                fails += 1
            if parent.get("reason") != "attr-module-alias-unbound:M.HW":
                fails += 1
            if [i for i in parent.get("branch_reads") or []
                    if i.startswith("branch:")]:
                fails += 1
        finally:
            shutil.rmtree(root, ignore_errors=True)
    print("LIMITS %s fails=%d" % ("MATCHED" if not fails else "MISMATCH",
                                  fails))
    return 0 if not fails else 2


if __name__ == "__main__":
    sys.exit(main())