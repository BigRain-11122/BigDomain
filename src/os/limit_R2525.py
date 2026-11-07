"""Measure the limits this face leaves, before seeding them as a row."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import probe_seam_annotated_constant_scope as PLAC


def main():
    alias = 'BASE_NAME = "plac_helper"\nALIAS: str = BASE_NAME\n'
    print("alias_table=%r" % (PLAC.module_bindings(alias),))
    kwarg = ('NAME: str = "plac_helper"\n'
             'FMT = "%s"\n'
             'NAME: str = FMT % NAME\n')
    print("rebind_table=%r" % (PLAC.module_bindings(kwarg),))
    with_expr = ('import importlib\n'
                 '\n'
                 'def run():\n'
                 '    with open("x", encoding="ascii") as handle:\n'
                 '        name = handle.read()\n'
                 '    return importlib.import_module(name).QUIETED\n')
    print("with_local=%r" % (PLAC.local_bindings(with_expr),))
    deep = ('X = {"A": {"NAMES": ("plac_unused", "plac_helper")}}\n')
    print("deep_chain=%r" % (PLAC.resolve_expression(
        'cfg.X.A.NAMES[1]', 'import cfg\nimport importlib\n', BASE),))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())