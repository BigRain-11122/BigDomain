"""Repair a mixed-EOL evidence log in place through the one canon.

R2262 found qa/reconcile-all-R2260.log classified class=other by the
qa writer census: its R2260 follow-up appended subprocess bodies that
still carried CRLF, so the file ended LF-dominant with 35 CRLF lines
and the census - which ran BEFORE that append in the same round - had
frozen it as tee. The repair is the R2233 precedent: rewrite the file
through run_identity.normalize (drop BOM, unify EOL, single trailing
newline) with one utf-8 writer, then prove the payload line set is
unchanged.

Usage: python src/os/evidence_normalize_R2262.py [PATH ...]
Exit: 0 normalized+verified, 3 path missing, 4 not strict utf-8.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import run_identity as RID  # noqa: E402  (single normalization source)

DEFAULT = [os.path.join(ROOT, "qa", "reconcile-all-R2260.log")]


def measure(text):
    return (text.count("\r\n"), text.count("\r") - text.count("\r\n"),
            len(text.encode("utf-8")), RID.digest16(text))


def repair(path):
    if not os.path.exists(path):
        print("MISSING %s" % path)
        return 3
    raw = io.open(path, "rb").read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        print("NOT-UTF8 %s %s" % (path, exc))
        return 4
    bom = raw.startswith(b"\xef\xbb\xbf")
    crlf_b, cr_b, size_b, sha_b = measure(text)
    fixed = RID.normalize(text)
    data = fixed.encode("utf-8")
    with io.open(path, "wb") as handle:
        handle.write(data)
    back = io.open(path, "rb").read().decode("utf-8")
    crlf_a, cr_a, size_a, sha_a = measure(back)
    same_lines = (RID.normalize(back).split("\n")
                  == RID.normalize(text).split("\n"))
    print("%s bom=%s before crlf=%d bare_cr=%d bytes=%d sha16=%s"
          % (os.path.relpath(path, ROOT), bom, crlf_b, cr_b, size_b, sha_b))
    print("%s after  crlf=%d bare_cr=%d bytes=%d sha16=%s"
          % (os.path.relpath(path, ROOT), crlf_a, cr_a, size_a, sha_a))
    print("payload_line_set_identical=%s" % same_lines)
    ok = (crlf_a == 0 and cr_a == 0 and not data.startswith(b"\xef\xbb\xbf")
          and same_lines)
    return 0 if ok else 5


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    paths = args or DEFAULT
    code = 0
    for path in paths:
        got = repair(path)
        code = got if got != 0 else code
    return code


if __name__ == "__main__":
    sys.exit(main())