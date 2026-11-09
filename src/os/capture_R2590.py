"""Capture this window own evidence as one utf-8 LF file, written by the
writer rather than by a shell redirection (the ps-utf16 trap, R2587/R2588).

Legs: this face own suite TWICE (compared byte for byte), then the R2588 parent
suite as an adjacent reading, then the limits script.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))

SUFFIX = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
          "alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
          "elif_with_while_match_scope.py")
PARENT = ("probe_seam_name_binding_arm_mixed_residual_alias_attribute_import_"
          "alias_scope_module_alias_attribute_alias_walrus_relative_branch_"
          "elif_with_scope.py")

OWN = os.path.join(REPO, "src", "os", "test_" + SUFFIX)
ADJACENT = (os.path.join(REPO, "src", "os", "test_" + PARENT),
            os.path.join(REPO, "src", "os", "test_" +
                         "probe_seam_name_binding_arm_mixed_residual_alias_"
                         "attribute_import_alias_scope_module_alias_attribute_"
                         "alias_walrus_relative_branch_scope.py"))
LIMITS = os.path.join(
    REPO, "src", "os", "limits_module_alias_walrus_elif_with_next_R2590.py")
EVIDENCE = os.path.join(
    REPO, "qa", "module-alias-walrus-while-match-scope-R2590.log")


def run(script):
    argv = [sys.executable, script]
    proc = subprocess.run(argv, capture_output=True, cwd=REPO)
    text = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0:
        text += proc.stderr.decode("utf-8", "replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return proc.returncode, text


def main():
    legs = []
    for index in (1, 2):
        print("running own suite leg %d ..." % index, flush=True)
        code, text = run(OWN)
        legs.append((code, text))
        print("leg %d rc=%d bytes=%d" % (index, code, len(text)), flush=True)
    identical = legs[0][1] == legs[1][1]
    print("identical=%s" % (identical,), flush=True)

    adj = []
    for script in ADJACENT:
        name = os.path.basename(script)
        print("running adjacent %s ..." % name, flush=True)
        adj.append((name,) + run(script))
        print("%s rc=%d" % (name, adj[-1][1]), flush=True)

    print("running limits ...", flush=True)
    lim_code, lim_text = run(LIMITS)
    print("limits rc=%d" % (lim_code,), flush=True)

    chunks = []
    for index, (code, text) in enumerate(legs, start=1):
        chunks.append("== own leg %d rc=%d ==\n%s" % (index, code, text))
    chunks.append("== own legs identical=%s ==\n" % (identical,))
    for name, code, text in adj:
        chunks.append("== adjacent %s rc=%d ==\n%s" % (name, code, text))
    chunks.append("== limits rc=%d ==\n%s" % (lim_code, lim_text))

    fails = sum(1 for code, _ in legs if code != 0)
    fails += sum(1 for _, code, _ in adj if code != 0)
    fails += 1 if lim_code != 0 else 0
    chunks.append("EVIDENCE identical=%s adjacent=%d fails=%d\n"
                  % (identical, len(adj), fails))
    payload = "".join(chunks)
    with io.open(EVIDENCE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print("wrote %s (%d bytes)" % (os.path.basename(EVIDENCE),
                                   len(payload.encode("utf-8"))), flush=True)
    ok = (all(code == 0 for code, _ in legs) and identical
          and all(code == 0 for _, code, _ in adj) and lim_code == 0)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())