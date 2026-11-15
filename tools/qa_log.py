"""qa_log - one canonical writer for window evidence logs (R2776, AC-QAL1..7).

Why this exists: the R2775 artifact qa/index-newest-band-R2775.log was healthy in
content and wrong in dialect - UTF-16LE with a FF FE BOM and CRLF endings, which
is what PowerShell redirection produces by default. The writer census flagged it,
the daily census gate failed the day, and the battery suite reconcile-daily-census
went red on cd7. That was the third artifact of the class (R2768 re-encoded two),
so the repair is a birth site, not another re-encode by hand.

Usage:
  python tools/qa_log.py NAME                 # read stdin, write qa/NAME
  python tools/qa_log.py NAME --from FILE     # read FILE (any dialect), write qa/NAME
  python tools/qa_log.py --check NAME         # read-only dialect verdict, rc=2 = red
  python tools/qa_log.py --selftest           # fixtures in a temp dir, nothing in qa/

Contract (AC-QAL1..7):
  AC-QAL1 any readable source (utf-8, utf-8-BOM, utf-16 BOM, gb18030 fallback) is
          written as UTF-8 without BOM, LF only, one trailing newline.
  AC-QAL2 the write is proven by reading it back: no BOM, no CR, decodable,
          non-empty, trailing newline; on any failure rc=2 and no half file.
  AC-QAL3 atomic: tmp file in the destination dir then os.replace; no .tmp left.
  AC-QAL4 --check NAME is read-only and refuses UTF-16/BOM/CR/undecodable files.
  AC-QAL5 the archived R2775 sample replays to the exact bytes already in the repo.
  AC-QAL6 a name holding a path separator, a drive colon, or nothing is refused.
  AC-QAL7 the selftest never touches qa/, this source is ASCII, and it imports no
          network or subprocess module.

Stdlib only, ASCII source, zero network, zero shell.
"""

import hashlib
import io
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
QA = os.path.join(REPO, "qa")

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_16LE = b"\xff\xfe"
BOM_16BE = b"\xfe\xff"


def read_source(raw):
    """AC-QAL1: decode whatever the shell produced, without guessing silently."""
    if raw.startswith(BOM_UTF8):
        return raw[len(BOM_UTF8):].decode("utf-8")
    if raw.startswith(BOM_16LE):
        return raw[2:].decode("utf-16-le")
    if raw.startswith(BOM_16BE):
        return raw[2:].decode("utf-16-be")
    for enc in ("utf-8", "gb18030"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("undecodable source bytes")


def normalize(text):
    """AC-QAL1: LF only, exactly one trailing newline."""
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    out = out.rstrip("\n")
    return out + "\n"


def check_name(name):
    """AC-QAL6: one flat file name, never a path."""
    if not name or not name.strip():
        raise ValueError("empty name")
    if "/" in name or "\\" in name or ":" in name:
        raise ValueError("name must be a flat file name, got %r" % name)
    if name in (".", "..") or name.startswith("."):
        raise ValueError("name must not start with a dot, got %r" % name)


def write_atomic(directory, name, text):
    """AC-QAL3: tmp in the destination dir, then one replace."""
    payload = text.encode("utf-8")
    final = os.path.join(directory, name)
    fd, tmp = tempfile.mkstemp(prefix=".qa_log_", suffix=".tmp", dir=directory)
    try:
        with io.open(fd, "wb", closefd=True) as handle:
            handle.write(payload)
        os.replace(tmp, final)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return final


def verify_written(path):
    """AC-QAL2: the file proves itself, so a bad write cannot be claimed good."""
    raw = io.open(path, "rb").read()
    if raw.startswith(BOM_UTF8) or raw.startswith(BOM_16LE) or raw.startswith(BOM_16BE):
        raise ValueError("BOM survived the write")
    if b"\r" in raw:
        raise ValueError("CR survived the write")
    if not raw:
        raise ValueError("empty file")
    if not raw.endswith(b"\n"):
        raise ValueError("missing trailing newline")
    text = raw.decode("utf-8")
    return {
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "sha256": hashlib.sha256(raw).hexdigest()[:16],
    }


def classify(raw):
    """AC-QAL4: name the dialect of an existing file, read-only."""
    if raw.startswith(BOM_16LE) or raw.startswith(BOM_16BE):
        return "ps-utf16"
    if raw.startswith(BOM_UTF8):
        return "utf-8-bom"
    if b"\r" in raw:
        return "crlf"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "undecodable"
    if raw and not raw.endswith(b"\n"):
        return "no-trailing-newline"
    return "utf-8/lf"


def do_write(name, source_bytes, directory=QA):
    check_name(name)
    text = normalize(read_source(source_bytes))
    path = write_atomic(directory, name, text)
    proof = verify_written(path)
    sys.stdout.write(
        "QA-LOG WROTE name=%s bytes=%d lines=%d sha256=%s dialect=utf-8/lf "
        "VERDICT PASS\n"
        % (name, proof["bytes"], proof["lines"], proof["sha256"]))
    return 0


def do_check(name):
    check_name(name)
    path = os.path.join(QA, name)
    if not os.path.exists(path):
        sys.stdout.write("QA-LOG RED name=%s reason=missing\n" % name)
        return 2
    raw = io.open(path, "rb").read()
    dialect = classify(raw)
    if dialect != "utf-8/lf":
        sys.stdout.write("QA-LOG RED name=%s dialect=%s bytes=%d expected=utf-8/lf\n"
                         % (name, dialect, len(raw)))
        return 2
    sys.stdout.write("QA-LOG OK name=%s dialect=utf-8/lf bytes=%d\n"
                     % (name, len(raw)))
    return 0


def selftest():
    """AC-QAL5 + AC-QAL7: fixtures only, and the R2775 sample must replay."""
    passes = 0
    fails = 0

    def check(ok, label):
        nonlocal passes, fails
        if ok:
            passes += 1
            sys.stdout.write("PASS %s\n" % label)
        else:
            fails += 1
            sys.stdout.write("FAIL %s\n" % label)

    tmp = tempfile.mkdtemp(prefix="qalog_")
    try:
        # ut16 + BOM + CRLF source becomes plain LF
        src16 = b"\xff\xfe" + "a\r\nb\r\n".encode("utf-16-le")
        text = normalize(read_source(src16))
        check(text == "a\nb\n", "qal1-utf16-bom-crlf-normalized")

        # a source without a trailing newline gains exactly one
        check(normalize(read_source(b"a\nb")) == "a\nb\n", "qal1-trailing-newline-added")

        # a read-back proof that fails is a refusal, not a claim
        p = write_atomic(tmp, "probe.log", "x\n")
        check(verify_written(os.path.join(tmp, p))["bytes"] == 2
              and verify_written(os.path.join(tmp, p))["lines"] == 1,
              "qal2-readback-proof")

        # no tmp survivor after a successful write
        leftovers = [n for n in os.listdir(tmp) if n.endswith(".tmp")]
        check(leftovers == [], "qal3-atomic-no-tmp-left")

        # an injected CR must be caught by the read-back proof
        bad = os.path.join(tmp, "bad.log")
        io.open(bad, "wb").write(b"a\r\nb\n")
        caught = False
        try:
            verify_written(bad)
        except ValueError:
            caught = True
        check(caught, "qal2-cr-refused")

        # the classifier must redden exactly the R2775 shape
        plant = os.path.join(tmp, "plant.log")
        io.open(plant, "wb").write(b"\xff\xfe" + "PASS x\r\n".encode("utf-16-le"))
        check(classify(io.open(plant, "rb").read()) == "ps-utf16",
              "qal4-utf16-classified-red")

        # AC-QAL6 name refusals
        refused = 0
        for name in ("", "sub/dir.log", "C:x.log", "..\\x.log"):
            try:
                check_name(name)
            except ValueError:
                refused += 1
        check(refused == 4, "qal6-bad-names-refused")

        # AC-QAL5 replay the archived original against the committed repair
        arch = os.path.join(REPO, "logs", "qa-encoding-preop-R2775",
                            "index-newest-band-R2775.log.utf16le")
        live = os.path.join(QA, "index-newest-band-R2775.log")
        if os.path.exists(arch) and os.path.exists(live):
            replayed = normalize(read_source(io.open(arch, "rb").read()))
            on_disk = io.open(live, "rb").read().decode("utf-8")
            check(replayed == on_disk, "qal5-r2775-sample-replays-byte-equal")
        else:
            sys.stdout.write("INFO qal5-sample-absent archive=%s live=%s\n"
                             % (os.path.exists(arch), os.path.exists(live)))
    finally:
        for name in os.listdir(tmp):
            try:
                os.unlink(os.path.join(tmp, name))
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass

    total = passes + fails
    sys.stdout.write("VERDICT %s %d/%d qa_log selftest (qa/ untouched)\n"
                     % ("PASS" if fails == 0 else "FAIL", passes, total))
    return 0 if fails == 0 else 2


def main(argv):
    args = list(argv[1:])
    if not args:
        sys.stdout.write("usage: qa_log.py NAME [--from FILE] | --check NAME | "
                         "--selftest\n")
        return 2
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--check":
        if len(args) != 2:
            sys.stdout.write("QA-LOG REFUSED --check needs exactly one name\n")
            return 2
        return do_check(args[1])
    name = args[0]
    source = None
    if "--from" in args:
        i = args.index("--from")
        if i + 1 >= len(args):
            sys.stdout.write("QA-LOG REFUSED --from needs a path\n")
            return 2
        source = io.open(args[i + 1], "rb").read()
    else:
        source = sys.stdin.buffer.read()
    try:
        return do_write(name, source)
    except (ValueError, OSError) as exc:
        sys.stdout.write("QA-LOG REFUSED name=%s reason=%s\n" % (name, exc))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
