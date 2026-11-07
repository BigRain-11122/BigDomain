"""R2551 live leg: BOUNDED real tree (the probe_seam_* family only).

The full src/os tree audit is too slow for this window budget, so this leg
copies every real probe_seam_*.py module from src/os into one private
directory and audits THAT, stating the scope in the log rather than claiming a
whole-tree reading. The same fixture is measured on BOTH readers.
"""

import glob
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(os.path.dirname(BASE), "sandbox"))

import probe_seam_name_binding_nested_arm_mixed_scope as P  # noqa: E402
import probe_seam_name_binding_nested_exhaustive_path as B  # noqa: E402
import suite_matrix as SM  # noqa: E402

FIXTURE = (
    'D = {"a": {"b": ("pndp_live_helper",)}}\n'
    '\n'
    'if flag:\n'
    '    KEY = "b"\n'
    '    if other:\n'
    '        KEY = "b"\n'
    '    else:\n'
    '        KEY = "b"\n'
    'else:\n'
    '    KEY = "b"\n'
    'for name in D["a"][KEY]:\n'
    '    pass\n'
)


def main():
    root = tempfile.mkdtemp(prefix="pndp-live-")
    copied = 0
    try:
        for path in sorted(glob.glob(os.path.join(BASE, "probe_seam_*.py"))):
            shutil.copyfile(path, os.path.join(root, os.path.basename(path)))
            copied += 1
        report = P.reading(root, SM)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    covered = [row for row in report["probes"] if row["verdict"] == "COVERED"]
    loops = sum(len(row["arm_loops"]) for row in report["probes"])
    mine = P.arm_report(FIXTURE)["loops"]
    base = B.nested_report(FIXTURE)["loops"]
    lines = [
        "scope=BOUNDED real tree, %d probe_seam_*.py modules copied from "
        "src/os (whole-tree audit declined on budget)" % copied,
        "tool=%s" % report["tool"],
        "base_tool=%s" % report.get("base_tool"),
        "verdict=%s" % report["verdict"],
        "counts=%s" % json.dumps(report["counts"], sort_keys=True),
        "covered_probes=%d arm_loop_rows=%d probes=%d"
        % (len(covered), loops, len(report["probes"])),
        "MINE_followed=%s" % json.dumps(mine[-1].get("followed"),
                                        sort_keys=True),
        "MINE_resolved=%s" % json.dumps(
            mine[-1].get("resolved_by_arm_mixed"), sort_keys=True),
        "BASE_refused=%s" % json.dumps(base[-1].get("refused"),
                                       sort_keys=True),
        "BASE_followed=%s" % json.dumps(base[-1].get("followed"),
                                        sort_keys=True),
    ]
    repo = os.path.dirname(os.path.dirname(BASE))
    path = os.path.join(
        repo, "qa",
        "probe-seam-name-binding-nested-arm-mixed-scope-live-R2551.log")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if report["verdict"] == P.SEAMS_ARM_MIXED_COVERED else 2


if __name__ == "__main__":
    sys.exit(main())