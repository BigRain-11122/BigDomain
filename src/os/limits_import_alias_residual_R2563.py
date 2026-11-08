"""R2563 residual limits on the alias attribute import-alias face.

Measured AFTER the face shipped, against one private world per shape, so the
next seed row cites readings rather than guesses.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope as I  # noqa

TAIL = 'for name in hw.NAMES:\n    pass\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n'
            % (binding, binding)) + TAIL


SHAPES = {
    # (1) a module bound by `from pkg import helper`
    "from-import-module": (
        'from pkg import helper\n' + arms('helper.ATTR'),
        {"pkg/__init__.py": '', "pkg/helper.py": 'ATTR = "b"\n'},
    ),
    # (2) a helper constant declared only inside a function body
    "function-body-constant": (
        'import helper\n' + arms('helper.ATTR'),
        {"helper.py": 'def factory():\n    ATTR = "b"\n    return ATTR\n'},
    ),
    # (3) a with-as module whose context is a CALL
    "with-as-call": (
        'with open_module() as m:\n'
        '    if a1:\n        KEY = m.ATTR\n'
        '    else:\n        KEY = m.ATTR\n' + TAIL,
        {"helper.py": 'ATTR = "b"\n'},
    ),
    # (4) a re-export under a different name
    "reexport-alias": (
        'import helper\n' + arms('helper.A'),
        {"helper.py": 'from hc import ATTR as A\n', "hc.py": 'ATTR = "b"\n'},
    ),
    # (5) a helper constant bound by a module-level walrus
    "walrus-constant": (
        'import helper\n' + arms('helper.ATTR'),
        {"helper.py": '(ATTR := "b")\n'},
    ),
}


def build(root, body, extra):
    with open(os.path.join(root, "probe_mod.py"), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write(body)
    for name, text in extra.items():
        path = os.path.join(root, *name.split("/"))
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


def measure(label, body, extra):
    root = tempfile.mkdtemp(prefix="pndc-res-")
    try:
        build(root, body, extra)
        line = body.split("\n").index("for name in hw.NAMES:") + 1
        got = I.import_alias_entry("KEY", body, "module", line, root=root)
        print("%-22s state=%-8s reason=%-42s value=%s hop=%s"
              % (label, got.get("state"), str(got.get("reason"))[:42],
                 got.get("value"), got.get("ia_hop")))
        return got
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    print("== R2563 residual limits on the alias attribute import-alias face ==")
    for label in sorted(SHAPES):
        body, extra = SHAPES[label]
        measure(label, body, extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())