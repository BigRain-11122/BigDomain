"""Measure this window own limits so the next seed row is a fact (R2559)."""

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_base as A  # noqa

C = 'D = {"a": {"b": ("x",)}}\n'
T = 'for n in D["a"][KEY]:\n    pass\n'


def arms(binding):
    return ('if q:\n    KEY = %s\nelse:\n    KEY = %s\n' % (binding, binding)) + T


def measure(text, root=None):
    row = A.attribute_report(text, root)["loops"][-1]
    return A.attribute_entry("KEY", text, row["scope"], row["line"],
                             root=root)


def main():
    root = tempfile.mkdtemp(prefix="pnda-limits-")
    with io.open(os.path.join(root, "h.py"), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write('ATTR = "b"\n')
    package = os.path.join(root, "pkg3")
    os.makedirs(package)
    with io.open(os.path.join(package, "__init__.py"), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write('ATTR = "b"\n')
    cases = [
        ("walrus-attr", C + 'import h\n(B := h.ATTR)\n' + arms("B")),
        ("subscript", C + 'import h\nB = items[0].ATTR\n' + arms("B")),
        ("pkg-init", C + 'import pkg3\nB = pkg3.ATTR\n' + arms("B")),
        ("with-helper", C + 'import h\nB = h.WITHTARGET\n' + arms("B")),
    ]
    for label, text in cases:
        got = measure(text, root)
        print("%-12s state=%s reason=%s value=%s"
              % (label, got.get("attr_state"), got.get("attr_reason"),
                 got.get("attr_value")))
    return 0


if __name__ == "__main__":
    sys.exit(main())