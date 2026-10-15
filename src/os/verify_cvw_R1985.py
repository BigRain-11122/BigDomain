# verify_cvw_R1985.py - takeover three-green leg 1: independent
# suite double-run byte-identity check with in-memory byte capture
# (no PS redirect dialect interference): sha16 must match the
# preserved crashed-round evidence value 57d176daa223d55f if the
# suite is deterministic and the payload unchanged.
import hashlib
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LEDGER = os.path.join(ROOT, "src", "sandbox", "ledger")
SUITE = os.path.join(LEDGER, "test_coverage_board_window.py")
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def main():
    outs = []
    for i in (1, 2):
        p = subprocess.run([sys.executable, SUITE], cwd=LEDGER,
                           capture_output=True, env=ENV)
        raw = (p.stdout + p.stderr).replace(b"\r\n", b"\n")
        outs.append((p.returncode, raw))
        print("run%d rc=%d sha16=%s bytes=%d"
              % (i, p.returncode,
                 hashlib.sha256(raw).hexdigest()[:16], len(raw)))
    ident = outs[0][1] == outs[1][1]
    match = hashlib.sha256(outs[0][1]).hexdigest()[:16] == \
        "57d176daa223d55f"
    print("identical=%s anchor-match=%s" % (ident, match))
    if not (ident and outs[0][0] == 0 and match):
        print("---- first run raw output ----")
        print(outs[0][1].decode("utf-8", "replace"))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
