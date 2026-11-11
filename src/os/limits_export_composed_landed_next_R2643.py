"""Measure the NEXT row limits of the BOM precedence word space, AFTER R2643.

Private temp files only; the repo is read but never written except for the
optional --out log this script composes itself in UTF-8 LF (never a shell
redirection into qa/, the ps-utf16 trap).

Each world answers what an honest reader would call it, not what is convenient.
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
    tmp = tempfile.mkdtemp(prefix="edww2643-next-")
    try:
        def world(name, raw, text):
            path = os.path.join(tmp, name + ".json")
            with open(path, "wb") as fh:
                fh.write(raw)
            report = CLF.account(path, text)
            line = ("WORLD %-22s word=%-18s transport=%-5s bom=%s kind=%s"
                    " composed=%s disk=%s delta=%s"
                    % (name, report["word"], report["transport"],
                       report["bom"], report.get("bom_kind"),
                       report["composed"], report["disk"], report["delta"]))
            rows.append(line)

        # (a) a TRUNCATED BOM prefix whose body carries MIXED separators: the
        # truncation fact is not named because the law needs a clean body.
        world("a_truncated_mixed", b"\xef\xbb" + b'{\r\n "a": 1\n}\r\n', LF)
        # (b) a UTF-16 BOM against an EMPTY composed text: still a UTF-16 BOM.
        world("b_utf16_against_empty", b"\xff\xfe", "")
        # (c) a BOM-ONLY landing (three bytes, no body) against empty text.
        world("c_bom_only", BOM, "")
        # (d) a UTF-16 payload with NO BOM: the encoding is unnameable, so it
        # can only be a content delta.
        world("d_utf16_no_bom", LF.encode("utf-16-le"), LF)
        # (e) a legitimate UTF-8 payload whose FIRST byte is 0xef and whose
        # rest is not the composed text: must stay a plain compare, not a BOM.
        world("e_legit_ef_start", "\uf000".encode("utf-8") + b'{"x":2}\n',
              "\uf000" + '{"x":2}\n')
        # (f) a REFERENCE clean landing, so the log carries a known-good row.
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
