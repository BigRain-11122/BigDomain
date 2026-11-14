"""R2723 one-off: two suite legs with a digest comparison, then a live leg.

Runs the shipped suite twice through its own file, hashes each leg output byte
for byte, and writes one evidence file that names both legs, whether they are
adjacent and identical, and how many FAIL lines they carried. The live leg then
reads the real committed evidence file and a real fixture through the shipped
CLI, so the face is proved on the tree rather than in a scratch dir.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
SUITE = os.path.join(BASE, "test_evidence_capture_precedence_derived.py")
FACE = os.path.join(BASE, "evidence_capture_precedence_derived.py")
OUT = os.path.join(ROOT, "qa", "evidence-capture-precedence-derived-R2723.log")
LIVE = os.path.join(ROOT, "qa",
                    "evidence-capture-precedence-derived-live-R2723.log")
REAL = os.path.join(ROOT, "qa", "reconcile-all-R2721.log")


def run(argv, timeout=900):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, cwd=BASE, env=env)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace")


def main():
    legs = []
    for _ in range(2):
        rc, text = run([sys.executable, SUITE])
        legs.append((rc, text))
    digests = [hashlib.sha256(text.encode("utf-8")).hexdigest().upper()[:16]
               for _, text in legs]
    fails = sum(1 for _, text in legs
                for line in text.splitlines() if line.startswith("FAIL "))
    green = all(rc == 0 for rc, _ in legs) and fails == 0
    lines = ["EVIDENCE capture-precedence-derived R2723",
             "face: src/os/evidence_capture_precedence_derived.py",
             "suite: src/os/test_evidence_capture_precedence_derived.py",
             "legs=2 identical=%s adjacent=%s both_green=%s fails=%d"
             % (len(set(digests)) == 1, digests[0] == digests[1],
                green, fails),
             "leg1 rc=%d digest=%s" % (legs[0][0], digests[0]),
             "leg2 rc=%d digest=%s" % (legs[1][0], digests[1]),
             ""]
    lines.extend(legs[0][1].splitlines())
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    live = ["LIVE capture-precedence-derived R2723",
            "face: src/os/evidence_capture_precedence_derived.py"]
    rc, text = run([sys.executable, FACE, "--order"])
    live.append("order rc=%d line=%s" % (rc, text.strip()))
    live.append("real evidence: %s" % os.path.relpath(REAL, ROOT))
    rc, text = run([sys.executable, FACE, "--source", REAL, "--check"])
    live.append("real rc=%d line=%s" % (rc, text.strip()))
    for name, payload in (("bom+nul+tail", "\xef\xbb\xbfa\x00b"),
                          ("crlf+nul", "a\r\n\x00\n")):
        probe = os.path.join(ROOT, "tmp", "ecord-live-%d.txt" % os.getpid())
        with io.open(probe, "wb") as fh:
            fh.write(payload.encode("latin-1"))
        rc, text = run([sys.executable, FACE, "--source", probe, "--check"])
        live.append("%s rc=%d line=%s" % (name, rc, text.strip()))
        if os.path.isfile(probe):
            os.remove(probe)
    with io.open(LIVE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(live) + "\n")
    print("EVIDENCE %s bytes=%d" % (os.path.basename(OUT),
                                    os.path.getsize(OUT)))
    print("LIVE %s bytes=%d" % (os.path.basename(LIVE),
                                os.path.getsize(LIVE)))
    print("VERDICT %s fails=%d identical=%s"
          % ("PASS" if green else "FAIL", fails, len(set(digests)) == 1))
    return 0 if green else 2


if __name__ == "__main__":
    sys.exit(main())
