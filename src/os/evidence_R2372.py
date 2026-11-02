"""evidence_R2372 - the live leg, written by ONE utf-8 LF writer.

Nothing here is a shell redirection: the file is opened once, encoded utf-8
with newline="\\n", and every line below is a measurement taken at run time.
The run is READ-ONLY: both CLIs are dry runs (the default), and the
declaration digest is compared before and after to prove it.
"""

import hashlib
import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
SHIPPED = os.path.join(BASE, "residue_triage_repin.py")
WIRE = os.path.join(BASE, "residue_triage_repin_idempotent.py")
DECL = os.path.join(REPO, "state", "residue_triage.json")
OUT = os.path.join(REPO, "qa", "residue-triage-repin-idempotent-live-R2372.log")
ARGS = ["--round", "R2372", "--until", "R2390",
        "--reason", "would re-pin at R2372", "--drop-unmatched"]


def digest(path):
    with io.open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def transport(text):
    """Normalise the child's console transport EOL, nothing else.

    R2373 measured the defect this fixes: the child CLI prints through the
    Windows console, so its stdout arrives with CRLF, and embedding it
    verbatim put six CRLF lines inside a file the census reads as ONE utf-8
    LF dialect (class=other). The payload is the printed LINE set; only the
    transport EOL is normalised here, exactly the R2366 AC-BFH4 lesson.
    """
    return text.replace("\r\n", "\n")


def run(module, extra):
    argv = [sys.executable, module] + list(extra)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, cwd=REPO)
    out, err = proc.communicate()
    return proc.returncode, transport(out.decode("utf-8", "replace")), \
        transport(err.decode("utf-8", "replace"))


def main():
    before = digest(DECL)
    size_before = os.path.getsize(DECL)
    shipped = run(SHIPPED, ARGS)
    wire = run(WIRE, ARGS)
    after = digest(DECL)
    size_after = os.path.getsize(DECL)
    json_wire = run(WIRE, ARGS + ["--json"])
    lines = [
        "LIVE R2372 residue_triage_repin_idempotent (read-only dry runs)",
        "declaration_before %s %dB" % (before, size_before),
        "declaration_after  %s %dB" % (after, size_after),
        "declaration_unchanged %s" % (before == after == digest(DECL)),
        "shipped rc=%d bytes=%d" % (shipped[0], len(shipped[1])),
        "wire    rc=%d bytes=%d" % (wire[0], len(wire[1])),
        "byte_identical %s" % (shipped[0] == wire[0]
                               and shipped[1] == wire[1]),
        "SHIPPED %s" % shipped[1].strip(),
        "WIRE    %s" % wire[1].strip(),
        "json rc=%d" % json_wire[0],
        "JSON %s" % json_wire[1].strip(),
        "verdict %s" % ("LIVE-PARITY"
                        if shipped[0] == wire[0] and shipped[1] == wire[1]
                        and before == after else "LIVE-MISMATCH"),
    ]
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    for line in lines:
        print(line)
    return 0 if lines[-1].endswith("LIVE-PARITY") else 1


if __name__ == "__main__":
    sys.exit(main())