# fix_dialect_R1990.py - R1880/R1883 dialect law repair: the
# fold evidence log qa/reorg-R1990.log was written through a
# PowerShell Tee (ps-utf16 dialect class) which the writer
# census flags (cd7 DRIFT). Read the utf-16 content, normalize
# CRLF->LF, rewrite as utf-8 through this python single writer
# (content preserved verbatim). Pure ASCII source.
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
P = os.path.join(ROOT, "qa", "reorg-R1990.log")

raw = open(P, "rb").read()
for enc in ("utf-16", "utf-16-le", "utf-16-be"):
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        text = None
if text is None:
    raise SystemExit("ABORT: cannot decode utf-16 content")
if text.startswith("\ufeff"):
    text = text[1:]
text = text.replace("\r\n", "\n").replace("\r", "\n")
if not text.endswith("\n"):
    text += "\n"
with open(P, "wb") as fh:
    fh.write(text.encode("utf-8"))
print("DIALECT-OK: reorg-R1990.log rewritten utf-8 LF, "
      "bytes=%d lines=%d" % (os.path.getsize(P),
                             text.count("\n")))
