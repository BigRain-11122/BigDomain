"""Capture this window own evidence as one utf-8 LF file, written by the
writer rather than by a shell redirection (the ps-utf16 trap).
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

SOURCES = [
    ("suite", os.path.join(REPO, "src", "os",
                           "test_probe_seam_name_binding_arm_mixed_residual_"
                           "alias_attribute_import_alias_scope_module_alias_"
                           "attribute_alias_walrus_relative_branch_scope.py")),
    ("adjacent", os.path.join(REPO, "src", "os",
                              "test_probe_seam_name_binding_arm_mixed_"
                              "residual_alias_attribute_import_alias_scope_"
                              "module_alias_attribute_alias_walrus_relative_"
                              "scope.py")),
]
LIMITS = os.path.join(REPO, "src", "os",
                      "limits_module_alias_walrus_branch_next_R2587.py")
EVIDENCE = os.path.join(REPO, "qa", "module-alias-walrus-branch-scope-R2587.log")
LIMITS_LOG = os.path.join(REPO, "qa",
                          "module-alias-walrus-branch-limits-R2587.log")


def run(script, extra=None):
    argv = [sys.executable, script] + list(extra or [])
    proc = subprocess.run(argv, capture_output=True, cwd=REPO)
    text = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0:
        text += proc.stderr.decode("utf-8", "replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return proc.returncode, text


def main():
    chunks = []
    for label, script in SOURCES:
        print("running %s ..." % label, flush=True)
        code, text = run(script)
        print("%s rc=%d bytes=%d" % (label, code, len(text)), flush=True)
        chunks.append("== %s rc=%d ==\n%s" % (label, code, text))
    with open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(chunks))
    print("running limits ...", flush=True)
    code, text = run(LIMITS)
    with open(LIMITS_LOG, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote %s and %s (limits rc=%d)"
          % (os.path.basename(EVIDENCE), os.path.basename(LIMITS_LOG), code))
    return 0


if __name__ == "__main__":
    sys.exit(main())