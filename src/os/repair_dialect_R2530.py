"""Rewrite evidence files into the tee dialect (utf-8, no BOM, bare LF).

Born at R2530: two evidence logs from the R2529 window were landed by a
PowerShell redirection and therefore carry UTF-16LE with BOM, which the
shipped writer census flags as a NEW non-tee dialect drift. This helper is
the explicit rewrite face the census does not ship: it decodes each named
file with its own detected encoding and writes the SAME text back as
utf-8 with newline="\\n" through a temp file + os.replace, then reads the
bytes back and prints the measured dialect. No qa/ directory is scanned
here and no baseline is touched.

Usage: python src/os/repair_dialect_R2530.py PATH [PATH ...]
"""

import io
import os
import sys
import tempfile


def detect(raw):
    if raw[:2] == b"\xff\xfe":
        return "utf-16-le-bom"
    if raw[:2] == b"\xfe\xff":
        return "utf-16-be-bom"
    if raw[:3] == b"\xef\xbb\xbf":
        return "utf-8-bom"
    if b"\x00" in raw:
        return "nul-bearing"
    return "utf-8"


def decode(raw, kind):
    if kind == "utf-16-le-bom":
        return raw.decode("utf-16")
    if kind == "utf-16-be-bom":
        return raw.decode("utf-16")
    if kind == "utf-8-bom":
        return raw.decode("utf-8-sig")
    if kind == "nul-bearing":
        raise SystemExit("refused: nul-bearing without a BOM")
    return raw.decode("utf-8")


def dialect(raw):
    return {
        "size": len(raw),
        "bom": raw[:3] in (b"\xef\xbb\xbf",) or raw[:2] in (
            b"\xff\xfe", b"\xfe\xff"),
        "nul": raw.count(b"\x00"),
        "crlf": raw.count(b"\r\n"),
        "bare_cr": raw.count(b"\r") - raw.count(b"\r\n"),
    }


def rewrite(path):
    raw = open(path, "rb").read()
    kind = detect(raw)
    text = decode(raw, kind)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    handle, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    os.close(handle)
    try:
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as out:
            out.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    after = open(path, "rb").read()
    print("%s from=%s to=utf-8 %s" % (path.replace(os.sep, "/"), kind,
                                      dialect(after)))
    return after


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: repair_dialect_R2530.py PATH [PATH ...]")
        return 5
    for path in args:
        if not os.path.exists(path):
            print("missing: %s" % path)
            return 3
        rewrite(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())