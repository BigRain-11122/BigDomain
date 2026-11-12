"""Measure the AC-EDXA fifth wave shapes against whatever the face answers NOW.

Run BEFORE any byte of the fifth wave exists and again AFTER it, so a word that
moved is named rather than claimed. Private temp files only; the repo is read,
never written except for the one optional UTF-8 LF log this script composes.

The six worlds are the ones pinned in state/queue/tech.md:664 at R2653:
  a_utf16_whole_agree    a WHOLE UTF-16LE landing that IS the composed text
  b_utf16_whole_disagree a WHOLE UTF-16LE landing that is the text PLUS a line
  c_double_odd_body      an ODD body behind TWO markers
  d_utf16be_short        a UTF-16BE marker with an odd body
  e_utf16_even_two       an EVEN two byte body that is not the text at all
  f_clean_lf             the clean LF reference (must stay PASS)
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
BOM = b"\xef\xbb\xbf"
U16LE = b"\xff\xfe"
U16BE = b"\xfe\xff"


def world(rows, tmp, name, raw, text):
    path = os.path.join(tmp, name + ".json")
    with open(path, "wb") as fh:
        fh.write(raw)
    report = CLF.account(path, text)
    rows.append(
        "WORLD %-24s word=%-26s composed=%-5s disk=%-3s delta=%-5s"
        " bom=%s kind=%s body=%s body_short=%s agrees=%s"
        % (name, report["word"], report["composed"], report["disk"],
           report["delta"], report["bom"], report.get("bom_kind"),
           report.get("body"), report.get("body_short"),
           report.get("agrees")))


def main(argv):
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    rows = []
    tmp = tempfile.mkdtemp(prefix="edxa2657-")
    try:
        world(rows, tmp, "a_utf16_whole_agree",
              U16LE + LF.encode("utf-16-le"), LF)
        world(rows, tmp, "b_utf16_whole_disagree",
              U16LE + (LF + "X\n").encode("utf-16-le"), LF)
        world(rows, tmp, "c_double_odd_body", BOM + U16LE + b"\x00", LF)
        world(rows, tmp, "d_utf16be_short", U16BE + b"\x00", LF)
        world(rows, tmp, "e_utf16_even_two", U16LE + b"\x00\x00", LF)
        world(rows, tmp, "f_clean_lf", LF.encode("utf-8"), LF)
        world(rows, tmp, "g_utf16_whole_be",
              U16BE + LF.encode("utf-16-be"), LF)
        world(rows, tmp, "h_utf16_whole_empty_text",
              U16LE + LF.encode("utf-16-le"), "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    body = "\n".join(rows) + "\n"
    sys.stdout.write(body)
    if out:
        with io.open(out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        sys.stdout.write("WROTE %s bytes=%d\n"
                         % (out, len(body.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
