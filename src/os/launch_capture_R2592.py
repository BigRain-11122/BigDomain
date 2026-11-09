"""Launch the R2592 evidence capture detached, stream and pid in SEPARATE files.

The capture runs the suite twice plus an adjacent suite, which is far past the
shell tool five-minute silence limit, so it must not be launched inline. This
launcher writes the child stream to logs/ and its pid beside it, then exits.
"""

import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
LOGS = os.path.join(ROOT, "logs")

SUITE = ("src/os/test_probe_seam_name_binding_arm_mixed_residual_alias_"
         "attribute_import_alias_scope_module_alias_attribute_alias_walrus_"
         "relative_branch_elif_with_while_match_while_else_nested_scope.py")
ADJACENT = ("src/os/test_probe_seam_name_binding_arm_mixed_residual_alias_"
            "attribute_import_alias_scope_module_alias_attribute_alias_"
            "walrus_relative_branch_elif_with_while_match_scope.py")
EVIDENCE = "qa/module-alias-walrus-while-else-nested-scope-R2592.log"


def main():
    if not os.path.isdir(LOGS):
        os.makedirs(LOGS)
    stream = os.path.join(LOGS, "capture-R2592.stream.log")
    pidpath = os.path.join(LOGS, "capture-R2592.pid")
    cmd = [sys.executable, os.path.join(BASE, "evidence_capture.py"),
           "--round", "R2592", "--suite", SUITE,
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