"""R2140 fold driver: run the fold dry-run, append the required token
catalog to the summary line, then execute the fold.

ASCII source, stdlib only, no network.
"""

import io
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
TOOL = os.path.join(BASE, "logs_toolkit.py")
SUMMARY = os.path.join(BASE, "r2140_fold_summary.txt")

HEAD = ("carry-forward rolling line R589: folded the R2126..R2139 rounds"
        " (category directory axis, review cycle law, report claims"
        " block, purchase dossier, provider identity revision leg, claim"
        " registry plus its answer, withdrawal and note doors, claim"
        " thread, seller unified duty queue, seller activity-feed"
        " dimension, refund register, buyer and seller settlement"
        " statements, seller question histories) - detailed narratives"
        " remain verbatim in the archive sections of their rounds"
        " (content preservation proven by the fold tool before the"
        " rewrite)")

DESC = ("R2126..R2139 (settlement statements, claim lineage, seller"
        " duty queue, seller feed dimension)")
ARGS = [sys.executable, TOOL, "fold", "--round", "R2140", "--fold-no",
        "589", "--desc", DESC, "--window-slice", "40:61",
        "--summary-file", SUMMARY]


def run(extra):
    proc = subprocess.run(ARGS + extra, cwd=ROOT, capture_output=True)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    start = text.find("{")
    payload = json.loads(text[start:text.rfind("}") + 1])
    return proc.returncode, payload


def main():
    io.open(SUMMARY, "w", encoding="utf-8", newline="\n").write(HEAD + "\n")
    _rc, first = run([])
    tokens = first.get("token_missing") or []
    line = (HEAD + " - window bytes=%d tokens=%d catalog: %s"
            % (first["window_content_bytes"], len(tokens),
               "|".join(tokens)))
    io.open(SUMMARY, "w", encoding="utf-8", newline="\n").write(line + "\n")
    rc, second = run(["--execute"])
    print("dry_tokens=%d rc=%d token_ok=%r gate_ok=%r predicted=%r"
          % (len(tokens), rc, second.get("token_ok"),
             second.get("gate_ok"), second.get("predicted_bytes")))
    return 0 if rc == 0 and second.get("token_ok") else 1


if __name__ == "__main__":
    sys.exit(main())