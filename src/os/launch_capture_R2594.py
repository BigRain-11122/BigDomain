"""Launch the R2594 evidence capture detached, stream and pid in SEPARATE files.

The capture runs the suite twice plus the adjacent parent suites, which is far
past the shell tool five-minute silence limit, so it must not be launched
inline. This launcher writes the child stream to logs/ and its pid beside it,
then exits.

The suite and adjacent names carry the `test_` prefix: R2594 measured that a
launcher which names the MODULE instead of its SUITE runs the reading itself
and produces no verdict line, so the prefix is spelled out here.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(ROOT, "logs")

STEM = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
        "alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
        "elif_with_while_match_while_else_nested_")
SUITE = "src/os/test_" + STEM + "match_ordinal_scope.py"
ADJACENT = ",".join([
    "src/os/test_" + STEM + "scope.py",
    "src/os/test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "elif_with_while_match_scope.py",
    "src/os/test_probe_seam_name_binding_arm_mixed_residual_alias_attribute_"
    "import_alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
    "scope.py",
])
EVIDENCE = "qa/module-alias-walrus-match-ordinal-scope-R2594.log"


def main():
    if not os.path.isdir(LOGS):
        os.makedirs(LOGS)
    stream = os.path.join(LOGS, "capture-R2594.stream.log")
    pidpath = os.path.join(LOGS, "capture-R2594.pid")
    cmd = [sys.executable, os.path.join(BASE, "evidence_capture.py"),
           "--round", "R2594", "--suite", SUITE,
           "--adjacent", ADJACENT, "--evidence", EVIDENCE,
           "--root", ROOT]
    with open(stream, "wb") as out:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=out,
                                stderr=subprocess.STDOUT,
                                creationflags=0x00000008)
    with open(pidpath, "w", encoding="ascii", newline="\n") as handle:
        handle.write("%d\n" % proc.pid)
    print("launched pid=%d stream=%s" % (proc.pid, stream))
    return 0


if __name__ == "__main__":
    sys.exit(main())