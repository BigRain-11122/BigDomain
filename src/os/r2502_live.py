"""R2502 live reading: the shipped module asked about the real patterns file,
then about a doctored copy, written as one utf-8 LF log."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
MODULE = os.path.join(BASE, "patterns_label_readability.py")
PATTERNS = os.path.join(SRC, "sandbox", "suite_matrix_patterns.json")
OUT = os.path.join(REPO, "qa", "patterns-label-readability-live-R2502.log")


def run(args):
    proc = subprocess.run([sys.executable, MODULE] + args, cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").replace(
        "\r\n", "\n").replace("\r", "\n")


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    before = digest(PATTERNS)
    rc_live, live = run(["--patterns", PATTERNS])
    world = tempfile.mkdtemp(prefix="plr-live-")
    document = json.load(open(PATTERNS, encoding="utf-8"))
    document["labels"]["stamp_from"] = "\u04e1\ufffd\ufffd\ufffd\ufffd\u04d4"
    bad = os.path.join(world, "patterns.json")
    with open(bad, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    rc_bad, doctored = run(["--patterns", bad])
    after = digest(PATTERNS)
    chunks = ["PATTERNS LABEL READABILITY live reading (R2502)",
              "patterns=%s" % os.path.relpath(PATTERNS, REPO).replace("\\", "/"),
              "digest before=%s after=%s unchanged=%s"
              % (before[:16], after[:16], before == after),
              "live exit=%d publishable=%s" % (rc_live, "true" if rc_live == 0
                                               else "false"),
              "doctored exit=%d" % rc_bad, "",
              "===== LIVE (the shipped file) =====", live.rstrip("\n"), "",
              "===== DOCTORED (a copy with one label replaced) =====",
              doctored.rstrip("\n"), "",
              "EVIDENCE %s" % ("PASS" if rc_live == 0 and rc_bad == 2
                               and before == after else "FAIL")]
    payload = "\n".join(chunks) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    print("\n".join(chunks[-4:]))
    return 0 if rc_live == 0 and rc_bad == 2 and before == after else 1


if __name__ == "__main__":
    sys.exit(main())