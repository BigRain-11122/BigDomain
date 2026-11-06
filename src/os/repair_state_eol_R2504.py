"""R2504 birth-site repair: two lone-LF lines inside src/os/state.json.

Lines 91 and 92 of the token array were written with LF while the rest of the
document is CRLF, which made the shipped fold writer refuse E_DWPP_MIXED. The
repair changes ONLY the two line terminators; every value, key and position is
kept byte for byte.
"""
import io
import sys

P = "src/os/state.json"
PAIRS = [(b"  ,\n", b"  ,\r\n"),
         (b'    "D-20261105-0",\n', b'    "D-20261105-0",\r\n')]


def main():
    raw = io.open(P, "rb").read()
    crlf_before = raw.count(b"\r\n")
    for old, new in PAIRS:
        hits = raw.count(old)
        if hits != 1:
            print("FAIL anchor hits=%d for %r" % (hits, old[:20]))
            return 2
        raw = raw.replace(old, new, 1)
    lf_total = raw.count(b"\n")
    lf_only = lf_total - raw.count(b"\r\n")
    io.open(P, "wb").write(raw)
    print("bytes=%d crlf=%d->%d lf_only=%d"
          % (len(raw), crlf_before, raw.count(b"\r\n"), lf_only))
    return 0 if lf_only == 0 else 1


if __name__ == "__main__":
    sys.exit(main())