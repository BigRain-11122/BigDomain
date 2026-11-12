# limits_export_composed_landed_next_R2661.py - measure what the SIXTH wave
# still cannot say, so the next seed row is pinned from measurement rather
# than from a guess.
#
# The sixth wave taught the face to name a UTF-16 body that is a strict PREFIX
# of the composed text as UTF16-BOM-CUT with the code units it lost. This
# script asks four questions that law does not answer, and prints one line per
# world: the word, the counts, and the fields the answer carries.
#
# Read-only: private temporary files, nothing under the repository is written.

import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_composed_landed_face as CLF  # noqa: E402

U16LE = b"\xff\xfe"
U16BE = b"\xfe\xff"
BOM = b"\xef\xbb\xbf"

# A text whose LAST character is a surrogate pair in UTF-16, so cutting two
# bytes removes HALF a character while the remainder is still a prefix.
EMOJI = "a\U0001F600b\n"
PLAIN = "a\r\nb\n"


def world(name, raw, text):
    path = os.path.join(TMP, name + ".json")
    with io.open(path, "wb") as handle:
        handle.write(raw)
    report = CLF.account(path, text)
    print("WORLD %-22s word=%-22s composed=%-6s disk=%-4d delta=%-5s"
          " kind=%-12s body=%-5s cut_units=%-4s refusal=%s"
          % (name, report["word"], report["composed"], report["disk"],
             report["delta"], report.get("bom_kind"), report.get("body"),
             report.get("cut_units"), report.get("refusal")))


TMP = tempfile.mkdtemp(prefix="edxb-next-2659-")
try:
    # (a) a cut that leaves a LONE SURROGATE HALF: the body is a prefix and the
    #     even-length law passes, so it reads CUT - but the lost two bytes are
    #     half a character, not one whole one.
    body = EMOJI.encode("utf-16-le")
    world("a_surrogate_half", U16LE + body[:-2], EMOJI)
    # (b) the same cut taken from a CRLF text: the face folds CRLF to LF first,
    #     so the landed CRLF bytes are no longer a prefix of the folded text.
    crlf_body = PLAIN.encode("utf-16-le")
    world("b_crlf_cut", U16LE + crlf_body[:-2], PLAIN)
    # (c) a cut behind the UTF-8 BOM and a UTF-16 marker at once: the double
    #     marker law runs first, so the cut is never named.
    world("c_cut_behind_two", BOM + U16LE + body[:-2], EMOJI)
    # (d) a UTF-16BE cut by three code units on a text that is pure ASCII, so
    #     the lost count is large and the remainder is still a prefix.
    ascii_body = "abcdef\n".encode("utf-16-be")
    world("d_be_three_units", U16BE + ascii_body[:-6], "abcdef\n")
finally:
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
