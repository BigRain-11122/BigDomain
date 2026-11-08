"""R2561 evidence capture: two legs plus five adjacent suites, one writer."""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import evidence_capture as EVC  # noqa

SUITE = os.path.join("src", "os", "test_probe_seam_name_binding_arm_mixed_"
                            "residual_alias_attribute_predicate_scope.py")
ADJACENT = [
    os.path.join("src", "os", "test_probe_seam_name_binding_arm_mixed_"
                             "residual_alias_attribute_base.py"),
    os.path.join("src", "os", "test_probe_seam_name_binding_arm_mixed_"
                             "residual_alias_position.py"),
    os.path.join("src", "os", "test_probe_seam_name_binding_arm_mixed_"
                             "residual_alias_chain.py"),
    os.path.join("src", "os", "test_probe_seam_dynamic_import_scope.py"),
    os.path.join("src", "os", "test_probe_seam_registry.py"),
]
EVIDENCE = os.path.join(
    "qa", "probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
          "predicate-R2561.log")


def main():
    report = EVC.capture(ROOT, "R2561", SUITE, ADJACENT, EVIDENCE)
    path = os.path.join(ROOT, EVIDENCE)
    print("EVIDENCE legs=%s identical=%s adjacent=%s fails=%s bytes=%d"
          % (report.get("legs"), report.get("identical"),
             report.get("adjacent"), report.get("fails"),
             os.path.getsize(path) if os.path.isfile(path) else -1))
    return 0 if os.path.isfile(path) else 2


if __name__ == "__main__":
    sys.exit(main())