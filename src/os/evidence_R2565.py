import os
import sys

sys.path.insert(0, "src/os")
import evidence_capture as EVC

ROOT = os.getcwd()
OSDIR = "src/os/"
report = EVC.capture(
    ROOT,
    "R2565",
    OSDIR + "test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
             "import_alias_scope_from_scope.py",
    adjacent=[
        OSDIR + "test_probe_seam_name_binding_arm_mixed_residual_alias_"
                "attribute_import_alias_scope.py",
        OSDIR + "test_probe_seam_name_binding_arm_mixed_residual_alias_"
                "attribute_predicate_scope.py",
        OSDIR + "test_probe_seam_name_binding_arm_mixed_residual_alias_"
                "attribute_base.py",
        OSDIR + "test_probe_seam_name_binding_arm_mixed_residual_alias_"
                "position.py",
        OSDIR + "test_probe_seam_dynamic_import_scope.py",
    ],
    evidence="qa/probe-seam-name-binding-arm-mixed-residual-alias-attribute-"
             "import-alias-scope-from-scope-R2565.log",
)
print(EVC.render(report))