"""Measure the AC-EDXA successor limits AFTER the fifth wave landed.

Private temp files only; the repo is read, never written except for the one
optional UTF-8 LF log this script composes itself.

The four shapes below are what the fifth wave still does not say. Each is
printed with the word it earns, so the successor row can be seeded from a
measurement rather than from an opinion:

  a_utf16_cut_even      a UTF-16 landing cut by ONE code unit (even body, a
                        strict PREFIX of the text encoding) - the loss of a
                        character is not named by any word or delta;
  b_utf16_other_body    an even body that is neither the text nor a head of it
                        - kept as the historical whole-landing word;
  c_utf16_empty_text    a whole UTF-16 landing against EMPTY composed text -
                        decided this window as a gap, named rather than
                        claimed;
  d_double_even_two     an EVEN two byte body behind two markers - body_short
                        must read False on it (named, already correct).
"""

import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_composed_landed_face as CLF  # noqa: E402

TEXT = '{\n "a": 1\n}\n'
BOM = b"\xef\xbb\xbf"
U16LE = b"\xff\xfe"


def world(rows, tmp, name, raw, text):
    path = os.path.join(tmp, name + ".json")
    with open(path, "wb") as fh:
        fh.write(raw)
    report = CLF.account(path, text)
    rows.append(
        "WORLD %-22s word=%-24s composed=%-5s disk=%-3s delta=%-5s"
        " bom_kind=%s body=%s body_short=%s agrees=%s"
        % (name, report["word"], report["composed"], report["disk"],
           report["delta"], report.get("bom_kind"), report.get("body"),
           report.get("body_short"), report.get("agrees")))


def main(argv):
    out = None
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    body16 = TEXT.encode("utf-16-le")
    rows = []
    tmp = tempfile.mkdtemp(prefix="edxa2657-next-")
    try:
        world(rows, tmp, "a_utf16_cut_even", U16LE + body16[:-2], TEXT)
        world(rows, tmp, "b_utf16_other_body", U16LE + b"\x00\x00", TEXT)
        world(rows, tmp, "c_utf16_empty_text", U16LE + body16, "")
        world(rows, tmp, "d_double_even_two", BOM + U16LE + b"\x00\x00", TEXT)
        world(rows, tmp, "e_utf16_agree_be",
              b"\xfe\xff" + TEXT.encode("utf-16-be"), TEXT)
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
