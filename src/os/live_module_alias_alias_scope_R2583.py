"""Bounded live leg: read six REAL probe modules and measure the SAME fixtures
on BOTH readers (this face and the R2579 face it extends).

Read-only; writes only the log it is asked to write.
"""

import argparse
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_scope as MAA2  # noqa: E402
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_scope as MAA  # noqa: E402

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
RECV = ("with mk.REG as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")
CALL = ("with mk.REG() as m:\n"
        "    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")


def _world(files):
    root = tempfile.mkdtemp(prefix="pnam-live-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def _measure(reader_entry, reader_report, files, text):
    root = _world(files)
    try:
        rows = reader_report(text, root)["loops"]
        row = rows[-1]
        got = reader_entry("KEY", text, row["scope"], row["line"], root=root)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return got


def both(alias_files, alias_text, call_files, call_text):
    """The SAME two fixtures measured on the base face and on this face."""
    my_alias = _measure(MAA2.module_alias_entry,
                        MAA2.module_alias_alias_report, alias_files, alias_text)
    base_alias = _measure(MAA.module_alias_entry,
                          MAA.module_alias_attribute_report, alias_files,
                          alias_text)
    my_call = _measure(MAA2.module_alias_entry,
                       MAA2.module_alias_alias_report, call_files, call_text)
    base_call = _measure(MAA.module_alias_entry,
                         MAA.module_alias_attribute_report, call_files,
                         call_text)
    return ("alias-head here=%s/%s hop=%s there=%s/%s; from-import-call "
            "here=%s/%s hop=%s there=%s/%s"
            % (my_alias.get("state"), my_alias.get("value"),
               my_alias.get("ma_hop"), base_alias.get("state"),
               base_alias.get("reason"), my_call.get("state"),
               my_call.get("value"), my_call.get("ma_hop"),
               base_call.get("state"), base_call.get("reason")))


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
        for row in MAA2.module_alias_alias_report(text, BASE, path)["loops"]:
            loops += 1
            resolved += len(row["ma_resolved"])
            named += len(row["ma_refused"])
    fixture = both(
        {"hw.py": HW,
         "consts.py": 'HW = "hw"\n',
         "mk.py": "import consts\nM = consts\nBASE = M.HW\nREG = BASE\n"},
        "import mk\n" + RECV + TAIL,
        {"hw.py": HW,
         "mk.py": 'def mkmod():\n    return "hw"\n',
         "probe_conf.py": "from mk import mkmod as REG\n"},
        "import probe_conf as mk\n" + CALL + TAIL)
    lines = ["LIVE modules=%d loops=%d ma_resolved=%d ma_named=%d "
             "unreadable=%d read_only=True"
             % (len(MODULES), loops, resolved, named, unreadable),
             "SAME-FIXTURE %s" % (fixture,)]
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())