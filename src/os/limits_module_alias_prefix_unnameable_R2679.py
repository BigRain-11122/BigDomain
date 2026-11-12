"""Measure the AC-PNAJ gap BEFORE and AFTER the unnameable-label face.

Two shapes are measured against the R2678 shipped face:

  * ['x', 'xy'] - a label that is a STRICT PREFIX of a sibling can never be
    named by any prefix, yet ack_prefix answers None, ack_unmatched names it,
    and prefix_free still reads True because it only looks at PUBLISHED
    prefixes. A COVERED verdict beside a non-empty ack_unmatched is a false
    green.
  * ['a', 'a'] - one string published twice. ack_prefix answers None for the
    same reason and prefix_free reads True on an empty prefix set.

Pure ASCII, stdlib only, no clock, zero network.
"""

import importlib.util
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
FACE = os.path.join(
    BASE,
    "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
    "alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_"
    "with_while_match_while_else_nested_match_ordinal_unique_prefix_scope.py")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def shape(face):
    out = {}
    for key, labels in (("x_xy", ["x", "xy"]),
                        ("aa", ["a", "a"]),
                        ("three_binding", ["while>case", "while2>case",
                                           "while2_body>case"]),
                        ("else_pair", ["while_else>case", "while_else2>case"])):
        index = face.ack_index(labels)
        out[key] = {
            "index": index,
            "unmatched": face.ack_unmatched(labels),
            "prefix_free": face.prefix_free(index),
        }
    return out


def main():
    face = load(FACE, "pnai_limits_R2679")
    before = shape(face)
    new_path = os.path.join(
        BASE,
        "probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
        "alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
        "elif_with_while_match_while_else_nested_match_ordinal_unique_"
        "prefix_unnameable_scope.py")
    after = None
    if os.path.isfile(new_path):
        after = shape(load(new_path, "pnaj_limits_R2679"))
    print(json.dumps({"before": before, "after": after},
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
