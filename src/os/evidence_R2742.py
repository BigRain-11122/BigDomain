"""Evidence driver for the R2742 order-field face (one ASCII log, one leg pair).

Runs the face own six-criteria suite TWICE through its own process, compares
the two bodies by sha256, then runs three adjacent suites, and lands the whole
account through the shipped utf-8 capture callable so a red capture cannot
become an artifact. Stdlib only, ASCII source, no clock read for the verdict.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, BASE)
sys.path.insert(0, SANDBOX)

import evidence_utf8_capture as EUC  # noqa

TARGET = "qa/export-parity-difference-order-field-R2742.log"
SUITE = "test_export_parity_difference_order_field.py"
ADJACENT = ("test_export_closeout_gate_parity.py",
            "test_closeout_export_parity_wire_binding_consumer.py",
            "test_closeout_export_parity_text_binding.py")


def run_suite(name):
    """Run one suite in its own process; return (code, body lines)."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, os.path.join(BASE, name)],
                            cwd=BASE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    out, _err = proc.communicate()
    text = out.decode("utf-8", "replace").replace("\r\n", "\n")
    return proc.returncode, [line for line in text.split("\n") if line]


def summary_of(lines):
    """The SUITE line a suite publishes, or None."""
    for line in lines:
        if line.startswith("SUITE "):
            return line
    return None


def green(code, lines):
    """Green means the suite process exited 0 and printed no FAIL row.

    The first version of this verdict demanded a 'SUITE PASS' line and read
    two adjacent suites red at rc=0 because one prints its own suite label
    and the other prints no suite line at all. The exit code is the
    authoritative signal; a printed FAIL row is the only veto on top of it.
    """
    if code != 0:
        return False
    for line in lines:
        if line.startswith("FAIL") or line.startswith("SUITE FAIL"):
            return False
    return True


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    target = argv[0] if argv else TARGET
    code1, lines1 = run_suite(SUITE)
    code2, lines2 = run_suite(SUITE)
    body1 = "\n".join(lines1)
    body2 = "\n".join(lines2)
    digest1 = hashlib.sha256(body1.encode("utf-8")).hexdigest()[:16].upper()
    digest2 = hashlib.sha256(body2.encode("utf-8")).hexdigest()[:16].upper()
    identical = digest1 == digest2 and body1 == body2
    adjacent = []
    fails = 0
    for name in ADJACENT:
        code, lines = run_suite(name)
        ok = green(code, lines)
        if not ok:
            fails += 1
        adjacent.append("%s %s rc=%d %s"
                        % ("PASS" if ok else "FAIL", name, code,
                           summary_of(lines) or "(no suite line)"))
    out = []
    out.append("EXPORT PARITY DIFFERENCE ORDER FIELD R2742")
    out.append("SUITE %s" % SUITE)
    out.append("LEG 1 rc=%d digest=%s %s"
               % (code1, digest1, summary_of(lines1) or "(no suite line)"))
    out.extend(lines1)
    out.append("LEG 2 rc=%d digest=%s %s"
               % (code2, digest2, summary_of(lines2) or "(no suite line)"))
    out.extend(lines2)
    for row in adjacent:
        out.append("ADJACENT " + row)
    out.append("SUMMARY legs=2 identical=%s adjacent=%d fails=%d"
               % (identical, len(ADJACENT), fails))
    text = "\n".join(out) + "\n"
    landed = EUC.capture(target, text.encode("utf-8"), root=REPO)
    print("EVIDENCE target=%s bytes=%d sha256=%s legs=2 identical=%s "
          "adjacent=%d fails=%d"
          % (landed["target"], landed["bytes"], landed["sha256"],
             identical, len(ADJACENT), fails))
    if not identical or fails or code1 != 0 or code2 != 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
