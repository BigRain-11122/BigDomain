"""Measure the NEXT row limits after the AC-EDWY third wave (R2649).

Private temp files only; the repo is read but never written except for the
optional --out log this script composes itself in UTF-8 LF.
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


def main(argv):
    out_path = None
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    rows = []
    tmp = tempfile.mkdtemp(prefix="edwy2649-next-")
    try:
        def world(name, raw, text):
            path = os.path.join(tmp, name + ".json")
            with open(path, "wb") as fh:
                fh.write(raw)
            report = CLF.account(path, text)
            rows.append(
                "WORLD %-26s word=%-24s transport=%-5s bom=%s kind=%s"
                " composed=%s disk=%s delta=%s"
                % (name, report["word"], report["transport"], report["bom"],
                   report.get("bom_kind"), report["composed"],
                   report["disk"], report["delta"]))

        # (a) a UTF-16 marker with ONE zero byte behind it: still read as a
        # whole UTF-16 landing, so a one byte remnant is unnamed.
        world("a_utf16_one_byte", b"\xff\xfe\x00", "")
        # (b) a UTF-16 marker with one zero byte against a NON-EMPTY text.
        world("b_utf16_one_byte_text", b"\xff\xfe\x00", LF)
        # (c) two markers WITH a body behind them: the double-marker word
        # carries no body description at all.
        world("c_double_marker_body", BOM + b"\xff\xfe" + b"abc", LF)
        # (d) a prefix-only landing against a NON-EMPTY text: the cut-alone
        # word carries no composed count.
        world("d_cut_only_vs_text", b"\xef\xbb", LF)
        # (e) a one byte cut against a non-empty text (reference).
        world("e_cut1_vs_text", b"\xef", LF)
        # (f) a REFERENCE clean LF landing.
        world("f_clean_lf", LF.encode("utf-8"), LF)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    body = "\n".join(rows) + "\n"
    sys.stdout.write(body)
    if out_path:
        with io.open(out_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
        sys.stdout.write("WROTE %s bytes=%d\n"
                         % (out_path, len(body.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
