"""Measure the AC-EDWZ fourth wave AFTER the fix and the FIFTH row limits.

Private temp files only. The repo is read, never written except for the two
optional logs this script composes itself in UTF-8 LF.
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
        "WORLD %-30s word=%-26s transport=%-5s bom=%s kind=%s body=%s"
        " body_transport=%s composed=%s disk=%s delta=%s"
        % (name, report["word"], report["transport"], report["bom"],
           report.get("bom_kind"), report.get("body"),
           report.get("body_transport"), report["composed"],
           report["disk"], report["delta"]))


def main(argv):
    after_out = None
    next_out = None
    if "--after-out" in argv:
        after_out = argv[argv.index("--after-out") + 1]
    if "--next-out" in argv:
        next_out = argv[argv.index("--next-out") + 1]
    after = []
    nxt = []
    tmp = tempfile.mkdtemp(prefix="edwz2653-")
    try:
        # --- AFTER the fourth wave: the four shapes this window closed.
        world(after, tmp, "a_utf16_one_byte", U16LE + b"\x00", "")
        world(after, tmp, "b_utf16_one_byte_text", U16LE + b"\x00", LF)
        world(after, tmp, "c_double_marker_body", BOM + U16LE + b"abc", LF)
        world(after, tmp, "d_cut_only_vs_text", b"\xef\xbb", LF)
        world(after, tmp, "e_cut1_vs_text", b"\xef", LF)
        world(after, tmp, "f_clean_lf", LF.encode("utf-8"), LF)

        # --- NEXT row limits: what the fourth wave still does not say.
        # (a) a WHOLE UTF-16LE landing that AGREES with the composed text ...
        world(nxt, tmp, "a_utf16_whole_agree",
              U16LE + LF.encode("utf-16-le"), LF)
        # (b) ... and one that DISAGREES with it read the SAME word with no
        # count at all, so agreement is never decided for a UTF-16 landing.
        world(nxt, tmp, "b_utf16_whole_disagree",
              U16LE + (LF + "X\n").encode("utf-16-le"), LF)
        # (c) an ODD body behind TWO markers: the double-marker law fires
        # first, so the odd remnant is described only by its count.
        world(nxt, tmp, "c_double_odd_body", BOM + U16LE + b"\x00", LF)
        # (d) a UTF-16BE marker with an odd body is answered in its own byte
        # order - named as already correct rather than claimed.
        world(nxt, tmp, "d_utf16be_short", U16BE + b"\x00", LF)
        # (e) an EVEN body that is not the text at all still reads a whole
        # landing, so a two byte remnant is a landing by this law.
        world(nxt, tmp, "e_utf16_even_two", U16LE + b"\x00\x00", LF)
        # (f) reference: a clean LF landing still reads PASS.
        world(nxt, tmp, "f_clean_lf", LF.encode("utf-8"), LF)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for rows, out_path in ((after, after_out), (nxt, next_out)):
        body = "\n".join(rows) + "\n"
        sys.stdout.write(body)
        if out_path:
            with io.open(out_path, "w", encoding="utf-8",
                         newline="\n") as handle:
                handle.write(body)
            sys.stdout.write("WROTE %s bytes=%d\n"
                             % (out_path, len(body.encode("utf-8"))))
        sys.stdout.write("---\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
