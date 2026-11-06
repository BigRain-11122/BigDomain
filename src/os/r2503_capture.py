"""R2503 evidence capture: run the new suite twice, then three neighbours.

Writes one utf-8 LF log so the census cannot class it as a pwsh capture
(the R2486 lesson). Exit 0 only when both legs agree and every neighbour is
green.
"""

import hashlib
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
QA = os.path.join(REPO, "qa")
SUITE = os.path.join(BASE, "test_patterns_label_readability_render_consumer.py")
NEIGHBOURS = [
    os.path.join(BASE, "test_patterns_label_readability.py"),
    os.path.join(BASE, "test_matrix_stamp_provenance_line.py"),
    os.path.join(BASE, "test_matrix_stamp_from_liveness.py"),
]
OUT = os.path.join(QA, "patterns-render-consumer-R2503.log")


def run(path):
    proc = subprocess.run([sys.executable, path], cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, text.replace("\r\n", "\n").replace("\r", "\n")


def main():
    legs = [run(SUITE), run(SUITE)]
    digests = [hashlib.sha256(text.encode("utf-8")).hexdigest()
               for _, text in legs]
    bodies = [line for line in legs[0][1].splitlines()
              if line.startswith("  PASS") or line.startswith("  FAIL")]
    body2 = [line for line in legs[1][1].splitlines()
             if line.startswith("  PASS") or line.startswith("  FAIL")]
    adjacent = [run(path)[0] for path in NEIGHBOURS]
    fails = sum(1 for line in bodies if line.startswith("  FAIL"))
    identical = digests[0] == digests[1] and bodies == body2
    green = (all(code == 0 for code, _ in legs)
             and identical and all(code == 0 for code in adjacent)
             and fails == 0)

    chunks = ["PATTERNS RENDER CONSUMER evidence (R2503)",
              "leg1 exit=%d leg2 exit=%d identical=%s fails=%d adjacent=%d"
              % (legs[0][0], legs[1][0], identical, fails, len(adjacent)),
              "adjacent exit codes=%r" % (adjacent,),
              "leg1 digest=%s" % digests[0],
              "leg2 digest=%s" % digests[1], ""]
    for index, (code, text) in enumerate(legs, 1):
        chunks.append("===== LEG %d (exit %d) =====" % (index, code))
        chunks.append(text.rstrip("\n"))
        chunks.append("")
    for path in NEIGHBOURS:
        code, text = run(path)
        tail = [line for line in text.splitlines()
                if line.startswith("SUITE ") or line.startswith("SUITE\t")]
        chunks.append("ADJACENT %s exit=%d tail=%s"
                      % (os.path.basename(path), code,
                         tail[-1] if tail else "-"))
    chunks.append("")
    chunks.append("EVIDENCE %s identical=%s fails=%d adjacent_green=%d/%d"
                  % ("PASS" if green else "FAIL", identical, fails,
                     sum(1 for code in adjacent if code == 0), len(adjacent)))
    payload = "\n".join(chunks) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print("\n".join(chunks[-6:]))
    print("bytes=%d" % len(payload.encode("utf-8")))
    return 0 if green else 1


if __name__ == "__main__":
    sys.exit(main())