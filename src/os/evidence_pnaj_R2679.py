"""Normalise the two PNJA legs into single-writer utf-8 LF evidence (R2679)."""

import hashlib
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.join(os.path.dirname(os.path.dirname(BASE)), "qa")
TEMP = os.environ.get("TEMP", "")


def read_text(path):
    raw = open(path, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16"), "utf-16-bom"
    if len(raw) >= 4 and raw[1:2] == b"\x00" and raw[3:4] == b"\x00":
        return raw.decode("utf-16-le"), "utf-16-le"
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise SystemExit("cannot decode %s" % path)


def normalise(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line for line in text.split("\n")]
    return ("\n".join(lines).rstrip("\n") + "\n").encode("utf-8")


def main():
    if not os.path.isdir(QA):
        os.makedirs(QA)
    legs = []
    for tag in ("a", "b"):
        src = os.path.join(TEMP, "pnaj_leg_%s.txt" % tag)
        text, encoding = read_text(src)
        data = normalise(text)
        path = os.path.join(QA, "prefix-unnameable-R2679-%s.log" % tag)
        with open(path, "wb") as handle:
            handle.write(data)
        legs.append((tag, src, encoding, data, path))
    data_a, data_b = legs[0][3], legs[1][3]
    identical = data_a == data_b
    raw = open(legs[0][4], "rb").read()
    sha16 = hashlib.sha256(raw).hexdigest()[:16]
    crlf = raw.count(b"\r\n")
    lone_cr = raw.count(b"\r") - crlf
    nul = raw.count(b"\0")
    bom = raw.startswith(b"\xef\xbb\xbf")
    passed = raw.count(b"PASS ")
    failed = raw.count(b"FAIL ")
    summary = ("legs=2 identical=%s bytes=%d sha16=%s utf8=True bom=%s "
               "crlf=%d lone_cr=%d nul=%d pass_lines=%d fail_lines=%d"
               % (identical, len(raw), sha16, bom, crlf, lone_cr, nul,
                  passed, failed))
    print(summary)
    for tag, src, encoding, _data, path in legs:
        print("leg %s decoded as %s -> %s" % (tag, encoding, path))
    with open(os.path.join(QA, "prefix-unnameable-R2679.summary"),
              "wb") as handle:
        handle.write((summary + "\n").encode("ascii"))
    ok = (identical and crlf == 0 and lone_cr == 0 and nul == 0
          and not bom and failed == 0 and passed >= 30)
    print("EVIDENCE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
