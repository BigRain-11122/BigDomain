"""Bounded live leg for the R2575 class-source face.

Reads a fixed list of real probe modules under src/os without writing anything,
then measures the four seeded shapes on BOTH readers (the shipped class-base
face and this face) so the log carries both answers side by side. The log is
landed through the shipped single writer, utf-8 LF, refusing an existing path.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import evidence_capture as EVC  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope as CB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_source_scope as CS  # noqa

OUT = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-source-scope-live-R2575.log")

MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_base.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope.py",
]

TAIL = "for name in hw.NAMES:\n    pass\n"


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_body(receiver, opened):
    return ("with %s.%s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver, opened))


def with_attr(receiver):
    return ("with %s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver,))


def world(files):
    root = tempfile.mkdtemp(prefix="live-pndci-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def both(text, root, src_rel=None):
    src = os.path.join(root, *src_rel.split("/")) if src_rel else None
    mine_rows = CS.class_source_report(text, root, src)["loops"]
    theirs_rows = CB.class_base_report(text, root, src)["loops"]
    mine = (CS.class_source_entry("KEY", text, mine_rows[-1]["scope"],
                                  mine_rows[-1]["line"], root=root,
                                  src_path=src) if mine_rows else {})
    theirs = (CB.class_base_entry("KEY", text, theirs_rows[-1]["scope"],
                                  theirs_rows[-1]["line"], root=root,
                                  src_path=src) if theirs_rows else {})
    return mine, theirs


def label(got):
    if got.get("state") == CB.STATE_OK:
        return "ok/%s" % (got.get("value"),)
    return "refused/%s" % (got.get("reason"),)


def main():
    files = 0
    loops = 0
    resolved = 0
    named = 0
    for name in MODULES:
        path = os.path.join(BASE, name)
        if not os.path.isfile(path):
            continue
        files += 1
        text = io.open(path, encoding="utf-8").read()
        for loop in CS.class_source_report(text, path)["loops"]:
            loops += 1
            resolved += len(loop["cs_resolved"])
            named += len(loop["cs_refused"])
    lines = ["live files=%d loops=%d cs_resolved=%d cs_named=%d "
             "read_only=True" % (files, loops, resolved, named)]

    fixtures = []
    root = world({"base.py": 'class Base:\n    ATTR = "b"\n',
                  "cls.py": "from base import Base\n\nclass K(Base):\n"
                            "    pass\n"})
    fixtures.append(("cross-module-base",) + both(
        "import cls\n" + arms("cls.K.ATTR") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"base.py": 'class Base:\n    NAME = "hw3"\n',
                  "hw3.py": 'ATTR = "b"\n',
                  "mk.py": 'from base import Base\n\nclass Box(Base):\n'
                           '    def open(self):\n        return self.NAME\n'})
    fixtures.append(("self-cross-base",) + both(
        "import mk\n" + with_body("mk.Box()", "open()") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"hw3.py": 'ATTR = "b"\n',
                  "mk.py": 'class Box:\n    NAME = "hw3"\n'
                           '    def open(self):\n        return self.NAME\n',
                  "reg.py": 'from mk import Box\nREG = Box().open()\n'})
    fixtures.append(("module-value",) + both(
        "import reg\n" + with_attr("reg.REG") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                            '    OTHER = ATTR\n'})
    fixtures.append(("class-alias",) + both(
        "import cls\n" + arms("cls.K.OTHER") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    for name, mine, theirs in fixtures:
        lines.append("fixture %-19s mine=%s there=%s"
                     % (name, label(mine), label(theirs)))

    body_text = "\n".join(lines) + "\n"
    parent = os.path.dirname(OUT)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    EVC._write_once(OUT, body_text)
    back = io.open(OUT, encoding="utf-8", newline="").read()
    print("wrote %s bytes=%d crlf=%d bom=%s lf=%d"
          % (OUT, os.path.getsize(OUT), back.count("\r\n"),
             back.startswith("\ufeff"), back.count("\n")))
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())