"""R2689 limits probe: the part joiner is escaped but never escaped FROM.

Measured on the R2685 sibling-escaped face BEFORE any code of this window, and
re-measured on the part-joiner face once it exists. Read-only, no fixtures on
disk, stdlib only.
"""

import importlib
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

BASE_NAME = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
             "import_alias_scope_module_alias_attribute_alias_walrus_"
             "relative_branch_elif_with_while_match_while_else_nested_"
             "match_ordinal_unique_prefix_unnameable_siblings_escaped_"
             "scope")
NEW_NAME = "probe_seam_unnameable_part_joiner_escaped_scope"

SHAPES = [
    ("one-label-with-part-joiner", ["a", "ab+duplicate:2"]),
    ("genuine-two-copy", ["a", "ab", "a"]),
    ("one-label-with-list-joiner", ["a", "ab,ac"]),
    ("two-sibling", ["a", "ab", "ac"]),
    ("single-sibling", ["x", "xy"]),
    ("duplicate-only", ["a", "a"]),
    ("one-label-with-backslash", ["a", "ab\\,ac"]),
]


def measure(mod, label):
    print("[%s] module=%s" % (label, getattr(mod, "LABEL", "?")))
    for name, labels in SHAPES:
        ack = mod.ack_unnameable(labels)
        row = {"shape": name, "labels": labels, "ack_unnameable": ack}
        for key, word in ack.items():
            row["parse:" + key] = mod.parse_strict_prefix_word(word)
            row["count:" + key] = mod.sibling_count_from_word(word)
        print("  " + json.dumps(row, sort_keys=True))


def main():
    base = importlib.import_module(BASE_NAME)
    measure(base, "BEFORE R2685 face")
    path = os.path.join(BASE, NEW_NAME + ".py")
    if os.path.exists(path):
        new = importlib.import_module(NEW_NAME)
        measure(new, "AFTER R2689 face")
    else:
        print("[AFTER] absent: %s not on disk" % NEW_NAME)
    return 0


if __name__ == "__main__":
    sys.exit(main())
