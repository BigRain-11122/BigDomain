"""R2517 one-off: prove the AC-PSL suite twice and land one evidence file."""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(REPO, "qa")
SUITE = os.path.join(BASE, "test_probe_seam_lazy_scope.py")
ADJACENT = ("test_probe_seam_forwarding_scope.py",
            "test_probe_seam_registry.py")

sys.path.insert(0, BASE)
import evidence_writer  # noqa: E402


def run(path):
    proc = subprocess.run([sys.executable, path], capture_output=True)
    out = (proc.stdout or b"").decode("utf-8", "replace")
    err = (proc.stderr or b"").decode("utf-8", "replace")
    return proc.returncode, out + err


def main():
    legs = []
    fails = 0
    body = []
    for n in (1, 2):
        code, text = run(SUITE)
        legs.append(text)
        fails += 1 if code != 0 else 0
        body.append("=== LEG %d rc=%d ===" % (n, code))
        body.append(text.rstrip("\n"))
    same = hashlib.sha256(legs[0].encode()).hexdigest() == \
        hashlib.sha256(legs[1].encode()).hexdigest()
    adjacent = []
    for name in ADJACENT:
        code, text = run(os.path.join(BASE, name))
        fails += 1 if code != 0 else 0
        adjacent.append("%s rc=%d %s" % (name, code,
                                         text.strip().splitlines()[-1]))
    body.append("=== ADJACENT ===")
    body.extend(adjacent)
    body.append("=== SUMMARY legs=2 identical=%s fails=%d adjacent=%d ==="
                % (same, fails, len(adjacent)))
    target = os.path.join(QA, "probe-seam-lazy-scope-R2517.log")
    row = evidence_writer.write_evidence(target, "\n".join(body) + "\n")
    print("legs=2 identical=%s fails=%d class=%s bytes=%d"
          % (same, fails, row.get("class"), row.get("bytes")))
    return 0 if (same and fails == 0) else 1


if __name__ == "__main__":
    sys.exit(main())