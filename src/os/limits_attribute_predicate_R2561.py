"""R2561 limits: measure what the alias attribute-predicate face still cannot read.

Every shape below is run against ONE private world built in a temp directory,
and the reading is asked at the loop own line. Nothing is guessed: whatever the
face answers is printed and that is what the next seed row may cite.
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

CONTAINER = 'D = {"a": {"b": ("seed",)}}\n'
TAIL = 'for name in D["a"][KEY]:\n    pass\n'


def arms(binding):
    return ('if a1:\n    KEY = %s\nelse:\n    KEY = %s\n' % (binding, binding)) + TAIL


SHAPES = {
    # (1) the helper constant is itself an alias of another constant
    "helper-alias": (
        CONTAINER
        + 'BASE = "b"\n'
        + 'if a1:\n    KEY = ha.ATTR\nelse:\n    KEY = ha.ATTR\n'
        + TAIL,
        {"ha.py": 'BASE = "b"\nATTR = BASE\n'},
    ),
    # (2) two different with-as bindings of one helper name
    "with-as-twice": (
        CONTAINER
        + 'if a1:\n    with hw.ctx as h:\n        KEY = h.ATTR\n'
        + 'else:\n    with hx.ctx as h:\n        KEY = h.ATTR\n'
        + TAIL,
        {"hw.py": 'ATTR = "b"\nctx = 1\n', "hx.py": 'ATTR = "b"\nctx = 1\n'},
    ),
    # (3) attribute on a base imported under an alias
    "import-alias": (
        CONTAINER
        + 'import helper as h\n'
        + 'if a1:\n    KEY = h.ATTR\nelse:\n    KEY = h.ATTR\n'
        + TAIL,
        {"helper.py": 'ATTR = "b"\n'},
    ),
    # (4) a call base whose callee is a plain function name
    "call-base": (
        CONTAINER
        + 'def factory():\n    return hw\n'
        + 'if a1:\n    KEY = factory().ATTR\nelse:\n    KEY = factory().ATTR\n'
        + TAIL,
        {"hw.py": 'ATTR = "b"\n'},
    ),
    # (5) a subscript base whose index is a name
    "subscript-name": (
        CONTAINER
        + 'import hw\n'
        + 'ITEMS = (hw,)\n'
        + 'IDX = 0\n'
        + 'if a1:\n    KEY = ITEMS[IDX].ATTR\nelse:\n    KEY = ITEMS[IDX].ATTR\n'
        + TAIL,
        {"hw.py": 'ATTR = "b"\n'},
    ),
    # (6) the attribute edge bound by a with-as NAME that is itself an alias
    "with-as-chain": (
        CONTAINER
        + 'if a1:\n    with hw2 as h:\n        KEY = h.ATTR\n'
        + 'else:\n    with hw2 as h:\n        KEY = h.ATTR\n'
        + TAIL,
        {"hw.py": 'ATTR = "b"\n', "hw2.py": 'from hw import ATTR\nTEST = ATTR\n'},
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
    root = tempfile.mkdtemp(prefix="pndb-lim-")
    try:
        build(root, body, extra)
        text = body
        line = text.split("\n").index('for name in D["a"][KEY]:') + 1
        shipped = PNDA.attribute_entry("KEY", text, "module", line, root=root)
        face = P.predicate_entry("KEY", text, "module", line, root=root)
        print("%-16s base=%-6s %-28s pred=%-8s %s"
              % (label, shipped.get("attr_state"),
                 str(shipped.get("attr_reason"))[:28],
                 face.get("pred_state"), face.get("pred_reason")))
        return (shipped, face)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    print("== R2561 limits on the alias attribute-predicate face ==")
    for label in sorted(SHAPES):
        body, extra = SHAPES[label]
        measure(label, body, extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())