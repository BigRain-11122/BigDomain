"""Measure the limits this R2569 face still carries, on one private world.

Every shape is run through the shipped entry so the reading is measured rather
than assumed. Writes nothing outside a temp dir.
"""

import io
import os
import sys
import tempfile

sys.path.insert(0, "src/os")
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_call_target_scope as CT  # noqa

ARMS = ("if a1:\n    KEY = %s\nelse:\n    KEY = %s\n")
TAIL = "for name in hw.NAMES:\n    pass\n"


def run(files, text):
    root = tempfile.mkdtemp(prefix="lim-pndcf-")
    for rel, body in files.items():
        path = os.path.join(root, *rel.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    rows = CT.call_target_report(text, root)["loops"]
    got = CT.call_target_entry("KEY", text, rows[-1]["scope"], rows[-1]["line"],
                               root=root) if rows else {}
    return got


def show(label, got):
    print("%-28s state=%s value=%s hop=%s reason=%s"
          % (label, got.get("state"), got.get("value"), got.get("ct_hop"),
             got.get("reason")))


base = {"hw3.py": 'ATTR = "b"\n', "helper.py": 'ATTR = "b"\n'}

show("two-level-relative", run(
    dict(base),
    "from .. import helper\n" + ARMS % ("helper.ATTR", "helper.ATTR") + TAIL))

show("cross-module-method", run(
    dict(base, **{"mk.py": ('class Box:\n'
                            '    def open(self):\n'
                            '        n = "hw3"\n'
                            '        return n\n')}),
    ('import mk\n'
     'with mk.Box().open() as m:\n'
     '    if a1:\n        KEY = m.ATTR\n'
     '    else:\n        KEY = m.ATTR\n' + TAIL)))

show("same-text-method-local", run(
    dict(base),
    ('class Box:\n'
     '    def open(self):\n'
     '        n = "hw3"\n'
     '        return n\n'
     'with Box().open() as m:\n'
     '    if a1:\n        KEY = m.ATTR\n'
     '    else:\n        KEY = m.ATTR\n' + TAIL)))

show("class-body-constant", run(
    dict(base, **{"cls.py": 'class K:\n    ATTR = "b"\n'}),
    "import cls\n" + ARMS % ("cls.K.ATTR", "cls.K.ATTR") + TAIL))

show("relative-from-name", run(
    dict(base, **{"cls.py": 'class K:\n    ATTR = "b"\n'}),
    "from .cls import K\n" + ARMS % ("K.ATTR", "K.ATTR") + TAIL))