"""Measure the NEXT row limits of the composed/landed WORD SPACE, after R2638.

Private temp files only; nothing in the repo is written. The question each
world answers is what an honest reader would call it, not what is convenient.
"""

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
    print("WORLD %s word=%-16s transport=%-5s bom=%s composed=%s disk=%s"
          " delta=%s"
          % (name, report["word"], report["transport"], report["bom"],
             report["composed"], report["disk"], report["delta"]))


def main():
    tmp = tempfile.mkdtemp(prefix="edwv2638-next-")
    try:
        # (a) a BOM landing whose BODY disagrees with the composed text.
        bom_gap = os.path.join(tmp, "bom_gap.json")
        with open(bom_gap, "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + LF.encode("utf-8") + b"extra\n")
        world("a_bom_body_gap", bom_gap, LF)

        # (b) a BOM landing that also carries MIXED separators.
        bom_mixed = os.path.join(tmp, "bom_mixed.json")
        with open(bom_mixed, "wb") as fh:
            fh.write(b"\xef\xbb\xbf" + b'{\r\n "a": 1\n}\r\n')
        world("b_bom_mixed", bom_mixed, LF)

        # (c) a UTF-16LE BOM, which this face does not recognise.
        utf16 = os.path.join(tmp, "utf16.json")
        with open(utf16, "wb") as fh:
            fh.write(b"\xff\xfe" + LF.encode("utf-16-le"))
        world("c_utf16_bom", utf16, LF)

        # (d) a TRUNCATED BOM prefix of two bytes only.
        short = os.path.join(tmp, "short.json")
        with open(short, "wb") as fh:
            fh.write(b"\xef\xbb" + LF.encode("utf-8"))
        world("d_short_bom", short, LF)

        # (e) EMPTY landing against an empty composed text (already correct).
        empty = os.path.join(tmp, "empty.json")
        with open(empty, "wb") as fh:
            fh.write(b"")
        world("e_empty_both", empty, "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
