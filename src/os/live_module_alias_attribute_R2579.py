"""Bounded live leg: read six REAL probe modules per file and measure the same
fixture on BOTH readers. Read-only; writes only the log it is asked to write.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_scope as MAA  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa

MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_source_scope",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope",
]

HW = 'ATTR = "b"\nNAMES = ["x"]\n'
TAIL = "for name in hw.NAMES:\n    pass\n"


def _world(files):
    root = tempfile.mkdtemp(prefix="pnpma-live-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def both_readers():
    """The SAME fixture measured on the base face and on this face."""
    files = {"hw.py": HW,
             "consts.py": 'HW = "hw"\n',
             "mk.py": "import consts\nBASE = consts.HW\nREG = BASE\n"}
    text = ("import mk\n"
            "with mk.REG as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" + TAIL)
    root = _world(files)
    try:
        rows = MA.module_alias_report(text, root)["loops"]
        row = rows[-1]
        base = MA.module_alias_entry("KEY", text, row["scope"], row["line"],
                                     root=root)
        rows = MAA.module_alias_attribute_report(text, root)["loops"]
        row = rows[-1]
        mine = MAA.module_alias_entry("KEY", text, row["scope"], row["line"],
                                      root=root)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return ("here=%s/%s hop=%s there=%s/%s"
            % (mine.get("state"), mine.get("value"), mine.get("ma_hop"),
               base.get("state"), base.get("reason")))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    loops = 0
    resolved = 0
    named = 0
    unreadable = 0
    for module in MODULES:
        path = os.path.join(BASE, module + ".py")
        if not os.path.isfile(path):
            unreadable += 1
            continue
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for row in MAA.module_alias_attribute_report(text, BASE,
                                                     path)["loops"]:
            loops += 1
            resolved += len(row["ma_resolved"])
            named += len(row["ma_refused"])
    lines = ["LIVE modules=%d loops=%d ma_resolved=%d ma_named=%d "
             "unreadable=%d read_only=True"
             % (len(MODULES), loops, resolved, named, unreadable),
             "SAME-FIXTURE %s" % (both_readers(),)]
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())