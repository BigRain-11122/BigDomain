"""One-off repair for the R2451 verification window.

The reconcile battery on the committed R2450 tree went RED on three real
birth-site defects.  This script repairs the evidence one only:

  qa/status-export-writer-dialect-wire-live-R2450.log was captured through a
  PowerShell redirect, so the 414-byte body carries five CRLF lines inside a
  file the census reads as one utf-8 LF dialect (class=pwsh-capture).  The
  payload is intact; only the transport is wrong.

The script proves the line set is identical on both sides of the
normalisation BEFORE writing, lands the normalised text as utf-8 LF through
ONE atomic replace, and reads the bytes back.  It never widens the census
baseline: the baseline file is not opened here at all.

The other two reds are source repairs, not evidence repairs, and live in
their own commits: the R2450 suite asked the shipped audit with a
cwd-relative root, and the residue declaration carried five untriaged rounds
which were spliced through the shipped batch append channel.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_identity as RI

FILES = (
    "status-export-writer-dialect-wire-live-R2450.log",
)


def repair(qa_dir):
    rows = []
    for name in FILES:
        path = os.path.join(qa_dir, name)
        with open(path, "rb") as fh:
            before = fh.read()
        text = before.decode("utf-8")
        normalised = RI.normalize(text)
        if normalised.splitlines() != text.splitlines():
            raise SystemExit("payload changed for %s" % name)
        out = normalised.encode("utf-8")
        tmp = path + ".repair-tmp"
        with open(tmp, "wb") as fh:
            fh.write(out)
        os.replace(tmp, path)
        with open(path, "rb") as fh:
            after = fh.read()
        if after.decode("utf-8").splitlines() != text.splitlines():
            raise SystemExit("read-back mismatch for %s" % name)
        rows.append({
            "name": name,
            "before": len(before),
            "after": len(after),
            "crlf_before": before.count(b"\r\n"),
            "crlf_after": after.count(b"\r\n"),
        })
    return rows


def main(argv):
    qa_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "qa")
    if len(argv) > 1 and argv[1] == "--qa":
        qa_dir = argv[2]
    rows = repair(qa_dir)
    for row in rows:
        print("REPAIR %s %dB -> %dB crlf=%d -> %d readback=ok"
              % (row["name"], row["before"], row["after"],
                 row["crlf_before"], row["crlf_after"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))