"""Measure the three seed-R2594 limits on private worlds (AC-PNAG probe).

Usage: python src/os/limits_module_alias_match_ordinal_unique_R2675.py
                                                    [--reader new|parent]

`parent` measures the shipped R2594 reader, `new` measures this window own
face. Nothing on the real tree is written: every world is a temporary
directory. Pure ASCII, stdlib only, no clock, zero network.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_scope as PNAF  # noqa: E402

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
TAIL = "for name in hw.NAMES:\n    pass\n"

THREE_BINDINGS = ("import consts\nimport consts2\nimport consts3\n"
                  "while a1:\n"
                  "    match x:\n        case 1:\n            (M := consts)\n"
                  "    match y:\n        case 1:\n            (M := consts2)\n"
                  "while a2:\n"
                  "    match z:\n        case 1:\n            (M := consts3)\n"
                  "BASE = M.HW\nREG = BASE\n")
ELSE_TWO = ("import consts\nimport consts2\n"
            "while a1:\n    pass\nelse:\n"
            "    match x:\n        case 1:\n            (M := consts)\n"
            "    match y:\n        case 1:\n            (M := consts2)\n"
            "BASE = M.HW\nREG = BASE\n")
FOR_IN_WHILE = ("import consts\nwhile a1:\n"
                "    for a2 in items:\n        match x:\n"
                "            case 1:\n                (M := consts)\n"
                "BASE = M.HW\nREG = BASE\n")
WHILE_IN_WHILE = ("import consts\nwhile a1:\n"
                  "    while a2:\n        match x:\n"
                  "            case 1:\n                (M := consts)\n"
                  "BASE = M.HW\nREG = BASE\n")
IF_IN_CASE = ("import consts\nwhile a1:\n"
              "    match x:\n        case 1:\n"
              "            if a2:\n                (M := consts)\n"
              "BASE = M.HW\nREG = BASE\n")
TWO_WHILES_ONE_MATCH = ("import consts\nimport consts2\n"
                        "while a1:\n"
                        "    match x:\n        case 1:\n"
                        "            (M := consts)\n"
                        "while a2:\n"
                        "    match y:\n        case 1:\n"
                        "            (M := consts2)\n"
                        "BASE = M.HW\nREG = BASE\n")


def world(files):
    root = tempfile.mkdtemp(prefix="pnaq-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def reader():
    text = sys.argv[1:]
    if "--reader" in text:
        tag = text[text.index("--reader") + 1]
    else:
        tag = "parent"
    if tag == "new":
        import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_scope as PNAG  # noqa: E402
        return PNAG
    return PNAF


def entry(module, text, root):
    rows = module.module_alias_report(text, root)["loops"]
    if not rows:
        return {}
    row = rows[-1]
    return module.module_alias_entry("KEY", text, row["scope"], row["line"],
                                     root=root)


def main():
    module = reader()
    cases = [
        ("three bindings across two whiles (two matches + one)", THREE_BINDINGS),
        ("two matches inside ONE while else section", ELSE_TWO),
        ("match inside a for body nested in a while", FOR_IN_WHILE),
        ("match nested one level in a while inside another while",
         WHILE_IN_WHILE),
        ("walrus bound by an if nested inside a match case", IF_IN_CASE),
        ("two while bodies each with one match", TWO_WHILES_ONE_MATCH),
    ]
    print("%s reader=%s" % (os.path.basename(__file__), module.LABEL))
    for label, body in cases:
        root = world({"hw.py": HW, "consts.py": 'HW = "hw"\n',
                      "consts2.py": 'HW = "hw2"\n',
                      "consts3.py": 'HW = "hw3"\n', "mk.py": body})
        try:
            got = entry(module, "import mk\n" + RECV + TAIL, root)
        finally:
            shutil.rmtree(root, ignore_errors=True)
        reason = got.get("reason") or ""
        labels = []
        if "ambiguous:" in reason and "@" in reason:
            labels = [item for item in reason.split("@", 1)[1].split("+")
                      if item]
        print("  %s" % label)
        print("    state=%s value=%s labels=%d %s"
              % (got.get("state"), got.get("value"), len(labels),
                 labels))
        print("    reason=%s" % (reason,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
