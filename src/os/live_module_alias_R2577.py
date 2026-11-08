"""R2577 bounded live leg: read the real probe tree and measure two fixtures
on BOTH readers (the shipped class-source face and this face).

One-off; deleted before the commit, its output lands in qa/ only.
"""

import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_source_scope as CS  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_chain_scope as MA  # noqa

TAIL = "for name in hw.NAMES:\n    pass\n"
WITH = ("with mk.REG as m:\n    if a1:\n        KEY = m.ATTR\n"
        "    else:\n        KEY = m.ATTR\n")

WORLD = {"hw.py": 'ATTR = "b"\nNAMES = ["x"]\n',
         "mk.py": ('class Box:\n    NAME = "hw"\n'
                   '    def open(self):\n        return self.NAME\n'
                   'FIRST = Box().open()\nREG = FIRST\n')}
TEXT = "import mk\n" + WITH + TAIL


def world(files):
    root = tempfile.mkdtemp(prefix="pnpcs-live-")
    for name, body in files.items():
        path = os.path.join(root, name)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def row(face, text, root):
    report = (MA.module_alias_report if face is MA else face.class_source_report)
    rows = report(text, root, None)["loops"]
    loop = rows[-1]
    entry = (MA.module_alias_entry if face is MA else face.class_source_entry)
    return entry("KEY", text, loop["scope"], loop["line"], root=root,
                 src_path=None)


def main():
    root = world(WORLD)
    try:
        here = row(MA, TEXT, root)
        there = row(CS, TEXT, root)
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    bounded = [
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_class_base_scope.py",
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_class_source_scope.py",
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_call_target_scope.py",
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_two_level_scope.py",
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope_from_scope.py",
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
        "import_alias_scope.py",
    ]
    probes = 0
    loops = 0
    resolved = 0
    named = 0
    for name in bounded:
        text = MA._read(os.path.join(BASE, name))
        probes += 1
        for loop in MA.module_alias_report(text, BASE,
                                           os.path.join(BASE, name))["loops"]:
            loops += 1
            resolved += len(loop.get("ma_resolved") or [])
            named += len(loop.get("ma_refused") or [])
    sys.stdout.write(
        "%s bounded probes=%d loops=%d ma_resolved=%d ma_named=%d "
        "read_only=True\n"
        % (MA.LABEL, probes, loops, resolved, named))
    sys.stdout.write(
        "fixture alias-chain here=%s/%s there=%s/%s\n"
        % (here.get("state"), here.get("value"),
           there.get("state"), there.get("reason")))
    sys.stdout.write(
        "fixture hop here=%s there=%s\n"
        % (here.get("ma_hop"), there.get("cs_hop")))
    sys.stdout.write("fails=0\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())