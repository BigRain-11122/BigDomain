"""Wire the R2571 suite into reconcile_all.SUITES (one row, 6 criteria)."""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
PATH = os.path.join(REPO, "src", "sandbox", "reconcile_all.py")

OLD = ('dual_alias_attribute_import_alias_scope_call_target_scope.py"),\n'
       '     6),\n    ]')
NEW = ('dual_alias_attribute_import_alias_scope_call_target_scope.py"),\n'
       '     6),\n'
       '    # R2571 two-level face: a level-bearing from-import resolves against\n'
       '    # the parent package once an anchor is known, a with-as call on a\n'
       '    # method defined in ANOTHER module resolves or is NAMED attr-cross-call,\n'
       '    # a class-body constant resolves through its class path, and a relative\n'
       '    # FROM-imported NAME is refused with its own word instead of being\n'
       '    # published as a local; every shipped answer rides beside it\n'
       '    # (614 -> 615 suites, 4660 -> 4666 criteria).\n'
       '    ("os-probe-seam-name-binding-arm-mixed-residual-alias-attribute-'
       'import-alias-scope-two-level-scope",\n'
       '     os.path.join(\n'
       '         "..", "os",\n'
       '         "test_probe_seam_name_binding_arm_mixed_residual_alias_'
       'attribute_import_alias_scope_two_level_scope.py"),\n'
       '     6),\n    ]')


def main():
    text = io.open(PATH, encoding="utf-8").read()
    if NEW in text:
        print("already wired")
        return 0
    if text.count(OLD) != 1:
        print("REFUSED anchor count=%d" % text.count(OLD))
        return 3
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.replace(OLD, NEW))
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox"))
    import reconcile_all as R
    names = [row[0] for row in R.SUITES]
    criteria = sum(row[2] for row in R.SUITES)
    print("suites=%d criteria=%d unique_names=%d unique_paths=%d"
          % (len(R.SUITES), criteria, len(set(names)),
             len(set(row[1] for row in R.SUITES))))
    return 0 if len(set(names)) == len(names) == len(R.SUITES) else 2


if __name__ == "__main__":
    sys.exit(main())