"""R2539 limit probe: measure this face own boundaries before seeding a row."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_name_binding_scope_awareness as P  # noqa: E402

CLASS_BODY = (
    'D = {"a": {"b": ("pnsb_x",)}}\n'
    '\n'
    'class Holder:\n'
    '    KEY = "b"\n'
    '    for item in D["a"][KEY]:\n'
    '        pass\n'
)

BOUND_AFTER = (
    'D = {"a": {"b": ("pnsb_x",)}}\n'
    '\n'
    'def run():\n'
    '    for item in D["a"][KEY]:\n'
    '        pass\n'
    '    KEY = "b"\n'
)

COMPREHENSION = (
    'D = {"a": {"b": ("pnsb_x",)}}\n'
    'KEY = "b"\n'
    'ROWS = [item for item in D["a"][KEY]]\n'
)


def main():
    for name, text in (("class_body", CLASS_BODY),
                       ("bound_after_loop", BOUND_AFTER),
                       ("comprehension", COMPREHENSION)):
        print("%s %s" % (name, P.scope_report(text)["loops"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())