"""R2171: normalise the newline axis only (CRLF -> LF) on evidence files
that the census flagged as pwsh-capture dialect. Every line is preserved
byte for byte apart from the line terminator, UTF-8 without BOM, LF only."""

import io
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TARGETS = [
    os.path.join(BASE, "qa", "apimarket-concentration-R2170.log"),
    os.path.join(BASE, "qa", "apimarket-concentration-R2170-run2.log"),
    os.path.join(BASE, "qa", "reconcile-all-R2168.log"),
]


def normalise(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    before = (len(raw), raw.count(b"\r\n"), raw.count(b"\n"))
    text = raw.decode("utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body += "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    with open(path, "rb") as handle:
        check = handle.read()
    after = (len(check), check.count(b"\r\n"), check.count(b"\n"))
    print("%s before=%s after=%s cr_lines=%d" % (
        os.path.basename(path), before, after,
        len([ln for ln in lines if ln.strip()])))
    return 0


def main():
    for path in TARGETS:
        if not os.path.exists(path):
            print("MISSING %s" % path)
            continue
        normalise(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())