"""R2196 evidence capture for the buyer purchase-gap rhythm suite.

Runs the suite twice and writes both logs through the house single
writer (src/os/evidence_writer.py) so the newline dialect is the tee
one the census accepts; never a shell redirection.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, "src", "os"))

from evidence_writer import write_evidence  # noqa: E402

SUITE = os.path.join(BASE, "src", "sandbox", "ledger",
                     "test_apimarket_buyergapmonths.py")
QA = os.path.join(BASE, "qa")


def run(tag):
    proc = subprocess.run([sys.executable, SUITE],
                          capture_output=True, cwd=BASE)
    body = proc.stdout.decode("utf-8", "strict")
    err = proc.stderr.decode("utf-8", "strict")
    text = body if not err else body + "\n[stderr]\n" + err
    path = os.path.join(QA, "apimarket-buyergapmonths-R2196%s.log" % tag)
    info = write_evidence(path, text)
    crit = [line for line in text.splitlines()
            if line.startswith("PASS ") or line.startswith("FAIL ")]
    sha16 = hashlib.sha256(
        "\n".join(crit).encode("utf-8")).hexdigest()[:16]
    print("run%s rc=%s criteria=%d sha16=%s bytes=%s"
          % (tag, proc.returncode, len(crit), sha16, info.get("bytes")))
    return proc.returncode, text, sha16


rc1, text1, sha1 = run("")
rc2, text2, sha2 = run("-run2")
print("identical_text=%r identical_criteria=%r"
      % (text1 == text2, sha1 == sha2))
sys.exit(0 if rc1 == 0 and rc2 == 0 else 1)