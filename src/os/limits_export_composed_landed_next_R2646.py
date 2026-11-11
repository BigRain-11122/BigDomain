"""Measure the NEXT row limits of the BOM precedence second wave, AFTER R2646.

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
    tmp = tempfile.mkdtemp(prefix="edwx2646-next-")
    try:
        def world(name, raw, text):
            path = os.path.join(tmp, name + ".json")
            with open(path, "wb") as fh:
                fh.write(raw)
            report = CLF.account(path, text)
            rows.append(
                "WORLD %-26s word=%-22s transport=%-5s bom=%s kind=%s"
                " composed=%s disk=%s delta=%s"
                % (name, report["word"], report["transport"], report["bom"],
                   report.get("bom_kind"), report["composed"],
                   report["disk"], report["delta"]))

        # (a) a truncated BOM prefix over a MIXED body that is NOT the composed
        # text: the truncation fact is dropped again, because the second wave
        # only names a cut when the body is the composed text up to separators.
        world("a_trunc_mixed_extra", b"\xef\xbb" + b'{\r\n "a": 1\n}\r\nX\n',
              LF)
        # (b) a BOM-only landing against a NON-EMPTY composed text: the word
        # says the payload is empty but the composed text it was measured
        # against is not carried at all.
        world("b_bom_only_vs_text", BOM, LF)
        # (c) a truncated prefix with an EMPTY body against an EMPTY text: it
        # reads truncated at delta=2 although nothing lies behind the prefix.
        world("c_trunc_empty_body", b"\xef\xbb", "")
        # (d) a UTF-8 BOM followed by a UTF-16 marker: two markers on one
        # landing, named only as a body gap.
        world("d_bom_then_utf16", BOM + b"\xff\xfe", LF)
        # (e) a legitimate 0xef-leading payload with MIXED separators that is
        # not the composed text: must NOT be accused of being a cut marker.
        world("e_legit_ef_mixed", "\uf000".encode("utf-8") + b'{\r\n 1\n}\r\n',
              "\uf000" + '{\r\n 1\n}\r\n')
        # (f) a UTF-16 marker with ONE zero byte behind it against empty text.
        world("f_utf16_one_byte", b"\xff\xfe\x00", "")
        # (g) a REFERENCE clean LF landing.
        world("g_clean_lf", LF.encode("utf-8"), LF)
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
