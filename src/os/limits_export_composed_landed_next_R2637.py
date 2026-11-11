"""Measure the NEXT row limits of the composed/landed face, after the fix.

Every world is a private temp file; nothing in the repo is written. The
question each world answers is "does the shipped face give the answer an
honest reader would give", not "is the face pretty".
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_composed_landed_face as CLF  # noqa: E402

LF = '{\n "a": 1\n}\n'
CRLF = LF.replace("\n", "\r\n")


def world(name, path, text):
    report = CLF.account(path, text)
    print("WORLD %s transport=%s composed=%s disk=%s word=%s delta=%s"
          % (name, report["transport"], report["composed"], report["disk"],
             report["word"], report["delta"]))


def main():
    tmp = tempfile.mkdtemp(prefix="edwt2637-next-")
    try:
        # (a) MIXED landing: one CRLF and one lone LF.
        mixed = os.path.join(tmp, "mixed.json")
        with open(mixed, "wb") as fh:
            fh.write(b'{\r\n "a": 1\n}\r\n')
        world("a_mixed", mixed, LF)

        # (b) empty landing.
        empty = os.path.join(tmp, "empty.json")
        with open(empty, "wb") as fh:
            fh.write(b"")
        world("b_empty", empty, LF)

        # (c) a landing that carries a UTF-8 BOM.
        bom = os.path.join(tmp, "bom.json")
        with open(bom, "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + LF.encode("utf-8"))
        world("c_bom", bom, LF)

        # (d) the caller hands CRLF composed text while the landing is CRLF.
        crlf = os.path.join(tmp, "crlf.json")
        with open(crlf, "wb") as fh:
            fh.write(CRLF.encode("utf-8"))
        world("d_caller_crlf", crlf, CRLF)
        print("WORLD d_caller_crlf naive_normalised=%d disk=%d"
              % (len(CRLF.replace("\n", "\r\n").encode("utf-8")),
                 len(CRLF.encode("utf-8"))))

        # (e) a single line with no newline at all.
        one = os.path.join(tmp, "one.json")
        with open(one, "wb") as fh:
            fh.write(b'{"a":1}')
        world("e_single_line", one, '{"a":1}')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
