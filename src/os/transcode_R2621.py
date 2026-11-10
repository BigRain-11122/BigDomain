"""Transcode this window two shell-written logs from UTF-16 to utf-8 LF.

The ps-utf16 trap (R2587/R2588): a shell redirection writes UTF-16, which the
shipped evidence readers refuse. The bytes are the measured output; only the
encoding changes. The pre-fix file keeps its own header line saying it was
recorded BEFORE any code.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
QA = os.path.join(REPO, "qa")
NAMES = ("limits-matrix-reconcile-fence-table-R2621.log",
         "limits-matrix-reconcile-fence-table-next-R2621.log")


def main():
    for name in NAMES:
        path = os.path.join(QA, name)
        raw = open(path, "rb").read()
        if raw[:2] not in (b"\xff\xfe", b"\xfe\xff"):
            print("SKIP %s already not utf-16" % name)
            continue
        text = raw.decode("utf-16")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.endswith("\n"):
            text += "\n"
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        back = open(path, "rb").read()
        print("OK %s bytes=%d bom=%s crlf=%d"
              % (name, len(back), back[:3] == b"\xef\xbb\xbf",
                 back.count(b"\r\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
