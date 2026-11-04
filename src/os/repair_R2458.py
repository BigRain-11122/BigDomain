"""Repair the R2458 closeout transport defect at its birth site.

The R2458 closeout wrote src/os/state.json with newline="\n", while the
committed document is a CRLF declaration: the whole file transport was
converted by a writer that never asked the shared dialect law. This script
re-renders the SAME content through src/os/declaration_writer_dialect_preservation
so the document keeps its own dialect, proves the line set identical on both
sides before writing, lands one atomic replace and reads the bytes back.

Run with --execute to write; the default is a dry run.
"""

import io
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import declaration_writer_dialect_preservation as DDP  # noqa: E402

STATE = os.path.join(BASE, "state.json")


def head_bytes():
    return subprocess.run(["git", "cat-file", "blob", "HEAD:src/os/state.json"],
                          cwd=os.path.dirname(os.path.dirname(BASE)),
                          stdout=subprocess.PIPE, check=True).stdout


def main(argv):
    execute = "--execute" in argv
    raw = open(STATE, "rb").read()
    # The dialect source is the WORKING copy the repository checks out under
    # core.autocrlf (CRLF), not the index blob (git-normalised LF): asking the
    # blob is what turned this repair into a second conversion the first time.
    head = raw if ("--crlf" in argv) else head_bytes()
    if "--crlf" in argv and b"\r\n" not in raw:
        composed_text = raw.decode("utf-8").replace("\r\n", "\n")
        head = composed_text.replace("\n", "\r\n").encode("utf-8")
        print("dialect source seeded as CRLF from the working composition")
    composed = raw.decode("utf-8").replace("\r\n", "\n")
    name, payload = DDP.encode(head, composed)
    same_lines = (payload.decode("utf-8").replace("\r\n", "\n")
                  == composed)
    reading = DDP.report(head, composed)
    print("REPAIR R2458 state transport before=%dB crlf=%d lf=%d"
          % (len(raw), raw.count(b"\r\n"), raw.count(b"\n") - raw.count(b"\r\n")))
    print("dialect=%s composed=%dB payload=%dB line_set_identical=%s"
          % (name, len(composed), len(payload), same_lines))
    print("reading=%s" % DDP.one_line(reading))
    if not same_lines:
        print("REFUSED: the line set moved, nothing written")
        return 2
    if not execute:
        print("DRY RUN - nothing written")
        return 0
    tmp = STATE + ".tmp-r2458eol"
    with open(tmp, "wb") as fh:
        fh.write(payload)
    os.replace(tmp, STATE)
    back = open(STATE, "rb").read()
    ok = back == payload
    print("WROTE %dB crlf=%d lone_lf=%d readback=%s"
          % (len(back), back.count(b"\r\n"),
             back.count(b"\n") - back.count(b"\r\n"), ok))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))