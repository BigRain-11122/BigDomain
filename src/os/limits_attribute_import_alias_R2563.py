"""R2563 limits: what the alias attribute-predicate face still cannot read.

Every shape is run against ONE private world built in a temp directory and the
reading is asked at the loop own line. Whatever the faces answer is printed and
that is what the module docstring and the seed row may cite.
"""

import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as PNDA  # noqa
import probe_seam_name_binding_arm_mixed_residual_alias_attribute_predicate_scope as P  # noqa

TAIL = 'for name in hw.NAMES:\n    pass\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n' % (binding, binding)) + TAIL


SHAPES = {
    # (1) a plain `import m` base followed by m.ATTR
    "plain-import": (
        'import helper\n'
        + arms('helper.ATTR'),
        {"helper.py": 'ATTR = "b"\n'},
    ),
    # (2) a module bound by `import m as x`, read as x.ATTR
    "import-alias": (
        'import helper as h\n'
        + arms('h.ATTR'),
        {"helper.py": 'ATTR = "b"\n'},
    ),
    # (3) a module reached by `with hw2 as m`
    "with-as-module": (
        'with hw2 as m:\n'
        '    if a1:\n        KEY = m.ATTR\n'
        '    else:\n        KEY = m.ATTR\n'
        + TAIL,
        {"hw2.py": 'ATTR = "b"\n'},
    ),
    # (4) a helper constant that is itself an alias of another constant
    "helper-alias": (
        'import helper\n'
        + arms('helper.ATTR'),
        {"helper.py": 'BASE = "b"\nATTR = BASE\n'},
    ),
    # (5) a helper constant re-exported by `from other import NAME`
    "reexport": (
        'import helper\n'
        + arms('helper.ATTR'),
        {"helper.py": 'from hc import ATTR\n',
         "hc.py": 'ATTR = "b"\n'},
    ),
    # (6) a helper constant carrying TWO values through an alias
    "alias-mixed": (
        'import helper\n'
        + arms('helper.ATTR'),
        {"helper.py": 'BASE = "b"\nATTR = BASE\nif z:\n    ATTR = "c"\n'},
    ),
}


def build(root, body, extra):
    with open(os.path.join(root, "probe_mod.py"), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write(body)
    for name, text in extra.items():
        with open(os.path.join(root, name), "w", encoding="utf-8",
                  newline="\n") as handle:
            handle.write(text)


def measure(label, body, extra):
    root = tempfile.mkdtemp(prefix="pndc-lim-")
    try:
        build(root, body, extra)
        text = body
        line = text.split("\n").index('for name in hw.NAMES:') + 1
        shipped = PNDA.attribute_entry("KEY", text, "module", line, root=root)
        face = P.predicate_entry("KEY", text, "module", line, root=root)
        print("%-16s base=%-8s %-26s pred=%-8s %s"
              % (label, shipped.get("attr_state"),
                 str(shipped.get("attr_reason"))[:26],
                 face.get("pred_state"), face.get("pred_reason")))
        return (shipped, face)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    print("== R2563 limits on the alias attribute-predicate face ==")
    for label in sorted(SHAPES):
        body, extra = SHAPES[label]
        measure(label, body, extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())