"""R2565 residual limits on the from-scope face, measured not assumed.

Every shape runs against one private world where the honest answer would be
`b`; whatever the face does is printed as measured.
"""

import io
import os
import sys
import tempfile

sys.path.insert(0, "src/os")
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_from_scope as FSC

TAIL = "for name in hw.NAMES:\n    pass\n"


def world(files):
    root = tempfile.mkdtemp(prefix="lim-pndce-")
    for name, body in files.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return root


def entry(root, text):
    rows = FSC.from_scope_report(text, root)["loops"]
    if not rows:
        return {}
    return FSC.from_scope_entry("KEY", text, rows[-1]["scope"],
                                rows[-1]["line"], root=root)


CASES = []

root = world({"hw3.py": 'ATTR = "b"\n'})
CASES.append((
    "with-as-attribute-call",
    root,
    'class Box:\n    def open(self):\n        return "hw3"\n'
    'with Box().open() as m:\n'
    "    if a1:\n        KEY = m.ATTR\n"
    "    else:\n        KEY = m.ATTR\n" + TAIL,
))

root = world({"hw3.py": 'ATTR = "b"\n'})
CASES.append((
    "with-as-local-return",
    root,
    'def open_module():\n    m = "hw3"\n    return m\n'
    "with open_module() as m:\n"
    "    if a1:\n        KEY = m.ATTR\n"
    "    else:\n        KEY = m.ATTR\n" + TAIL,
))

root = world({"pkg/helper.py": 'ATTR = "b"\n'})
CASES.append((
    "relative-from-import",
    root,
    "from . import helper\nif a1:\n    KEY = helper.ATTR\n"
    "else:\n    KEY = helper.ATTR\n" + TAIL,
))

root = world({"helper.py": 'def outer():\n    def inner():\n'
                            '        ATTR = "b"\n        return ATTR\n'
                            "    return inner\n"})
CASES.append((
    "nested-function-constant",
    root,
    "import helper\nif a1:\n    KEY = helper.ATTR\n"
    "else:\n    KEY = helper.ATTR\n" + TAIL,
))

print("== R2565 residual limits on the from-scope face ==")
for label, root, text in CASES:
    got = entry(root, text)
    print("%-26s state=%-8s reason=%-40s value=%s hop=%s"
          % (label, got.get("state"), got.get("reason"), got.get("value"),
             got.get("from_hop")))