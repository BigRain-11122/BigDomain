"""Measure the composed/landed gap named by tech:658 BEFORE any face is written.

Criteria AC-EDWT1..AC-EDWT6 were pinned in state/queue/tech.md:658 at R2596
BEFORE this file existed. This script only MEASURES; it writes nothing into
the repo and touches only a private temp directory.

Four worlds are built with the shipped dialect owner (general_writer_dialect_
audit.payload_for) so the transport is asked of the real law, not transcribed:

  A  an LF target  - composed equals landed, the honest baseline
  B  a CRLF target - a legal transport whose landed bytes are LONGER than the
                     composed text by one byte per line, which is exactly the
                     shape a naive composed/landed compare would call a defect
  C  the shipped classify() asked with a composed gap it cannot even express:
                     queue_bytes == disk_bytes while the composed text is three
                     bytes shorter - today it still answers PASS
  D  a target whose transport cannot be resolved (absent file), naming the
                     refusal the writer already owns
"""

import io
import os
import sys
import tempfile
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import export_R2431 as EX          # noqa: E402
import general_writer_dialect_audit as GWDA  # noqa: E402

TEXT = '{\n "a": 1\n}\n'          # three lines, LF composed text
LINES = TEXT.count("\n")


def measured(name, value):
    print("WORLD %s %s" % (name, value))


def main():
    tmp = tempfile.mkdtemp(prefix="edwt2637-")
    try:
        lf_path = os.path.join(tmp, "lf.json")
        crlf_path = os.path.join(tmp, "crlf.json")
        with io.open(lf_path, "wb") as fh:
            fh.write(b'{\n "a": 1\n}\n')
        with io.open(crlf_path, "wb") as fh:
            fh.write(b'{\r\n "a": 1\r\n}\r\n')

        lf_payload = GWDA.payload_for(lf_path, TEXT)
        crlf_payload = GWDA.payload_for(crlf_path, TEXT)
        composed = len(TEXT.encode("utf-8"))
        measured("A", "transport=lf composed=%d landed=%d delta=%d"
                 % (composed, len(lf_payload), len(lf_payload) - composed))
        measured("B", "transport=crlf composed=%d landed=%d delta=%d lines=%d"
                 % (composed, len(crlf_payload),
                    len(crlf_payload) - composed, LINES))
        same_b = (len(crlf_payload) == composed)
        measured("B", "naive_composed_equals_landed=%s" % same_b)

        # C: the shipped verdict, asked with identical queue/disk bytes while a
        # composed gap exists - the gap has no argument to travel on.
        word = EX.classify({"k": 1}, {"k": 1}, {"k": 1}, True,
                           len(crlf_payload), len(crlf_payload))
        measured("C", "shipped_verdict=%s composed_gap_visible=False" % word)

        # D: an absent target names the refusal the writer already owns.
        absent = os.path.join(tmp, "absent.json")
        try:
            GWDA.payload_for(absent, TEXT)
            measured("D", "absent_target=resolved")
        except GWDA.AuditError as exc:
            measured("D", "absent_target=refused:%s" % exc.code)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
