"""Bounded live leg for the R2573 class-base face.

Reads a fixed list of real probe modules under src/os without writing anything,
then measures the same fixtures on BOTH readers so the log carries the shipped
answer and this face own answer side by side. Writes one utf-8 LF log.
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_class_base_scope as CB  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope as TL  # noqa

OUT = os.path.join(
    REPO, "qa",
    "probe-seam-name-binding-arm-mixed-residual-alias-attribute-import-"
    "alias-scope-class-base-scope-live-R2573.log")

MODULES = [
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_base.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_two_level_scope.py",
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope.py",
]

TAIL = "for name in hw.NAMES:\n    pass\n"


def arms(binding):
    return ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n"
            % (binding, binding))


def with_body(receiver, opened):
    return ("with %s.%s as m:\n"
            "    if a1:\n        KEY = m.ATTR\n"
            "    else:\n        KEY = m.ATTR\n" % (receiver, opened))


def world(files):
    root = tempfile.mkdtemp(prefix="live-pndch-")
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
    mine_rows = CB.class_base_report(text, root, src)["loops"]
    theirs_rows = TL.two_level_report(text, root, src)["loops"]
    mine = (CB.class_base_entry("KEY", text, mine_rows[-1]["scope"],
                                mine_rows[-1]["line"], root=root,
                                src_path=src) if mine_rows else {})
    theirs = (TL.two_level_entry("KEY", text, theirs_rows[-1]["scope"],
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
    lines = []
    for name in MODULES:
        path = os.path.join(BASE, name)
        if not os.path.isfile(path):
            continue
        files += 1
        text = io.open(path, encoding="utf-8").read()
        report = CB.class_base_report(text, path)
        for loop in report["loops"]:
            loops += 1
            resolved += len(loop["cb_resolved"])
            named += len(loop["cb_refused"])
    lines.append("live files=%d loops=%d cb_resolved=%d cb_named=%d "
                 "read_only=True" % (files, loops, resolved, named))

    fixtures = []
    root = world({"cls.py": 'class Base:\n    ATTR = "b"\n\nclass K(Base):\n'
                            '    pass\n'})
    fixtures.append(("inherited",) + both(
        "import cls\n" + arms("cls.K.ATTR") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"cls.py": 'class K:\n    ATTR = "b"\n'})
    fixtures.append(("from-class",) + both(
        "from cls import K\n" + arms("K.ATTR") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"hw3.py": 'ATTR = "b"\n',
                  "mk.py": 'class Box:\n    NAME = "hw3"\n'
                           '    def open(self):\n        return self.NAME\n'})
    fixtures.append(("self-attribute",) + both(
        "import mk\n" + with_body("mk.Box()", "open()") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    root = world({"hw3.py": 'ATTR = "b"\n',
                  "pkg/mk.py": 'class Box:\n    NAME = "hw3"\n'
                               '    def open(self):\n        return self.NAME\n'})
    fixtures.append(("from-alias",) + both(
        "from pkg import mk as m2\n"
        + with_body("m2.Box()", "open()") + TAIL, root))
    shutil.rmtree(root, ignore_errors=True)

    for name, mine, theirs in fixtures:
        lines.append("fixture %-15s mine=%s there=%s"
                     % (name, label(mine), label(theirs)))

    body_text = "\n".join(lines) + "\n"
    parent = os.path.dirname(OUT)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body_text)
    back = io.open(OUT, encoding="utf-8", newline="").read()
    print("wrote %s bytes=%d crlf=%d bom=%s"
          % (OUT, os.path.getsize(OUT), back.count("\r\n"),
             back.startswith("\ufeff")))
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())