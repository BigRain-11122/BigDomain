"""R2161 evidence driver: run the repeat-purchase suite twice through
the single-writer evidence helper so both files land in the tee
dialect (utf-8, LF) and the two runs can be compared byte for byte."""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

from evidence_writer import write_evidence  # noqa: E402

SUITE = os.path.join(ROOT, "src", "sandbox", "ledger",
                     "test_apimarket_repeatpurchase.py")
CWD = os.path.dirname(SUITE)


def main():
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    outs = []
    codes = []
    for letter in ("a", "b"):
        proc = subprocess.run([sys.executable, SUITE], cwd=CWD,
                              env=env, capture_output=True, text=True)
        outs.append(proc.stdout)
        codes.append(proc.returncode)
        name = os.path.join(ROOT, "qa",
                            "apimarket-repeatpurchase-R2161-%s.log"
                            % letter)
        write_evidence(name, proc.stdout)
        print("%s rc=%d bytes=len" % (letter, proc.returncode))
    print("identical=%r rc_pair=%r" % (outs[0] == outs[1], codes))
    return 0 if outs[0] == outs[1] and codes == [0, 0] else 1


if __name__ == "__main__":
    sys.exit(main())