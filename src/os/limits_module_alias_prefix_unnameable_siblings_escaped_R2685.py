"""Measure the separator shapes of the R2682 sibling face BEFORE any code.

Run once before the successor face exists and once after, so both readings
are measured rather than quoted. Pure ASCII, stdlib only, no clock.
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_scope as PNAK  # noqa: E402

SHAPES = [
    ("one label carrying the list separator", ["a", "ab,ac"]),
    ("two ordinary siblings", ["a", "ab", "ac"]),
    ("single sibling carried from R2679", ["x", "xy"]),
    ("one label carrying the part joiner", ["a", "ab+duplicate:2"]),
    ("one label carrying a backslash", ["a", "ab\\ac"]),
    ("one label carrying a backslash then a comma", ["a", "ab\\,ac"]),
]


def main():
    print("tool=limits-R2685 base=%s" % (PNAK.LABEL,))
    try:
        import probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_elif_with_while_match_while_else_nested_match_ordinal_unique_prefix_unnameable_siblings_escaped_scope as PNAL  # noqa: E402
    except ImportError:
        PNAL = None
    print("successor_present=%s" % (PNAL is not None,))
    for name, labels in SHAPES:
        got = PNAK.ack_unnameable(labels)
        word = got.get("a") or got.get("x")
        print("%-44s labels=%s" % (name, labels))
        print("%-44s base_answer=%s" % ("", got))
        if PNAL is not None:
            now = PNAL.ack_unnameable(labels)
            print("%-44s new_answer=%s" % ("", now))
            print("%-44s new_sibling_count=%s"
                  % ("", PNAL.sibling_count_from_word((now.get("a")
                                                       or now.get("x")
                                                       or ""))))
        if "strict-prefix-of:" in (word or ""):
            raw = word.split("strict-prefix-of:")[1].split("+")[0]
            print("%-44s comma_split_parts=%d %s"
                  % ("", len(raw.split(",")), raw.split(",")))
    same = (PNAK.ack_unnameable(["a", "ab,ac"])
            == PNAK.ack_unnameable(["a", "ab", "ac"]))
    print("BASE-SHAPES-INDISTINGUISHABLE=%s" % (same,))
    if PNAL is not None:
        print("NEW-SHAPES-INDISTINGUISHABLE=%s"
              % (PNAL.ack_unnameable(["a", "ab,ac"])
                 == PNAL.ack_unnameable(["a", "ab", "ac"]),))
        print("TWO-SIBLING-WORD-BYTE-EQUAL=%s"
              % (PNAL.ack_unnameable(["a", "ab", "ac"])
                 == PNAK.ack_unnameable(["a", "ab", "ac"]),))
        print("SINGLE-SIBLING-WORD-BYTE-EQUAL=%s"
              % (PNAL.ack_unnameable(["x", "xy"])
                 == PNAK.ack_unnameable(["x", "xy"]),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
