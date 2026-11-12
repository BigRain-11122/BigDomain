"""Single-writer evidence for the R2678 prefix-free ack face.

Runs the suite twice in this process and writes each run through ONE utf-8 LF
writer, never a shell redirection, then reports the sha16 of both files so a
reader can see whether the two runs are byte-identical.

Pure ASCII, stdlib only, no clock, zero network.
"""

import hashlib
import importlib.util
import io
import os
import sys
from contextlib import redirect_stdout

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(REPO, "qa")
SUITE_NAME = ("test_probe_seam_name_binding_arm_mixed_residual_alias_"
              "attribute_import_alias_scope_module_alias_attribute_alias_"
              "walrus_relative_branch_elif_with_while_match_while_else_"
              "nested_match_ordinal_unique_prefix_scope.py")


def load_suite():
    path = os.path.join(BASE, SUITE_NAME)
    spec = importlib.util.spec_from_file_location("pnai_suite", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_once(module):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = module.main()
    return code, buffer.getvalue()


def write_evidence(name, text):
    if not os.path.isdir(QA):
        os.makedirs(QA)
    path = os.path.join(QA, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text if text.endswith("\n") else text + "\n")
    with open(path, "rb") as handle:
        raw = handle.read()
    return path, raw


def main():
    module = load_suite()
    first_code, first_text = run_once(module)
    second_code, second_text = run_once(module)
    a_path, a_raw = write_evidence("prefix-ack-R2678-a.log", first_text)
    b_path, b_raw = write_evidence("prefix-ack-R2678-b.log", second_text)
    a_sha = hashlib.sha256(a_raw).hexdigest()[:16]
    b_sha = hashlib.sha256(b_raw).hexdigest()[:16]
    print("EVIDENCE a=%s bytes=%d sha16=%s" % (a_path, len(a_raw), a_sha))
    print("EVIDENCE b=%s bytes=%d sha16=%s" % (b_path, len(b_raw), b_sha))
    print("EVIDENCE codes=%d/%d identical=%s"
          % (first_code, second_code, a_raw == b_raw))
    return 0 if first_code == 0 and second_code == 0 and a_raw == b_raw else 2


if __name__ == "__main__":
    sys.exit(main())
