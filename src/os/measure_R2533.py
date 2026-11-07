"""Measure the remaining limits of the subscript face, before seeding a row."""

import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_subscript_container_scope as P  # noqa: E402

NESTED = (
    'D = {"a": {"b": ("pcsc_x",)}}\n'
    'for n in D["a"]["b"]:\n'
    '    pass\n'
)

ITEMS = (
    'D = {"a": ("pcsc_x",)}\n'
    'for k, v in D.items():\n'
    '    pass\n'
)

TWO_KEYS = (
    'D = {"a": ("x",)}\n'
    'for n in D["a"][0]:\n'
    '    pass\n'
)

for name, text in (("nested", NESTED), ("items", ITEMS),
                   ("two_keys", TWO_KEYS)):
    print(name, P.subscript_report(text))