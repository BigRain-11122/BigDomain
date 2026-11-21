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

R2807 (AC-QALB8): a source that still carries NUL after decoding is REFUSED
rather than stored - BOM-less UTF-16 used to be written as a NUL-riddled file
with VERDICT PASS and read back as the healthy utf-8/lf dialect by this tool and
by the writer census. --check names such a file nul-bytes.
R3203 (AC-QAL9): a generator's carrier proof line is not a relogged file's
proof. The preview generator prints "LOG OK path=<p> bytes=<n> lines=<n>
sha16=<h>" on stdout, proving the file it just wrote; storing that whole stdout
through this writer kept the line verbatim inside a new file whose own sha16 was
a different number (measured: 761 bytes, carried 271ba9eb7b2d1230, own
4210a333be0b1d92) while both dialect faces stayed green. Such a line is now
prefixed CARRIED, so no reader can take it for this log's proof; a near-miss
shape is left untouched, and the line is never dropped. This is the writer's
job because --from (and stdin) is the only door through which one file's bytes
become another file's evidence.

R3204 (AC-QAL10): --check now names the count instead of leaving it to the eye.
Measured before this change: files holding 0, 1 and 2 CARRIED lines all read
rc=0 with the same QA-LOG OK line naming only dialect and bytes, the writer
census answered class=tee for all three, and the pre-commit gate refused none
of them - it reads row["class"] only. Zero files in the tree parse that text,
so the OK line gained carried=<n> at its tail with the old fields untouched.
The count is exact shapes only (a near miss is not counted), and it is not a
verdict: it says this file quotes N proofs of other files, not that the
quoted text is right and not that this file is wrong. A RED line never gains
the field, because a red dialect means the body was never judged.

R3205 (AC-QAL11): the other direction - an UNMARKED proof line was invisible.
Measured before this change: three files holding 0, 1 and 2 bare proof lines
all answered rc=0 with text that differed only in bytes=, the writer census
answered class=tee for all three, and the pre-commit gate compares the dialect
class only, never the body. A bare line can only be born one way today:
battery_shard.stream_evidence writes progress in place without going through
do_write (measured: one bare proof line landed unmarked, 102 bytes), while the
real qa/ tree holds zero bare lines across 4617 files. So --check now also
names bare_proofs=<n>, exact shapes only, old fields byte for byte the same.
It is a count, not a verdict: the line proves another file, and a RED line
still gains no field because its body was never judged. The name avoids a
prefix clash - bare_lf= and rows==bare= already exist elsewhere.

Stdlib only, ASCII source, zero network, zero shell.
"""

import hashlib
import io
import os
import re
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
QA = os.path.join(REPO, "qa")

BOM_UTF8 = b"\xef\xbb\xbf"
BOM_16LE = b"\xff\xfe"
BOM_16BE = b"\xfe\xff"


def read_source(raw):
    """AC-QAL1: decode whatever the shell produced, without guessing silently.

    AC-QALB8 (R2807): a decoded NUL is never legitimate in an evidence log. It
    means the source was BOM-less UTF-16, the one encoding the old fallback
    could not tell from plain text - it used to be accepted as readable, land a
    NUL-riddled file, and report VERDICT PASS. Refusing is the honest face: the
    endianness cannot be verified without a BOM, so the writer names the
    corruption instead of storing it.
    """
    if raw.startswith(BOM_UTF8):
        text = raw[len(BOM_UTF8):].decode("utf-8")
    elif raw.startswith(BOM_16LE):
        text = raw[2:].decode("utf-16-le")
    elif raw.startswith(BOM_16BE):
        text = raw[2:].decode("utf-16-be")
    else:
        for enc in ("utf-8", "gb18030"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("undecodable source bytes")
    if "\x00" in text:
        raise ValueError("source carries NUL bytes (BOM-less UTF-16 is not "
                         "an evidence dialect)")
    return text


def normalize(text):
    """AC-QAL1: LF only, exactly one trailing newline."""
    out = text.replace("\r\n", "\n").replace("\r", "\n")
    out = out.rstrip("\n")
    return out + "\n"


def check_name(name):
    """AC-QAL6: one flat file name, never a path. AC-QAL8: never a flag."""
    if not name or not name.strip():
        raise ValueError("empty name")
    if "/" in name or "\\" in name or ":" in name:
        raise ValueError("name must be a flat file name, got %r" % name)
    if name in (".", "..") or name.startswith("."):
        raise ValueError("name must not start with a dot, got %r" % name)
    if name.startswith("-"):
        # AC-QAL8 (pinned at R2809 BEFORE this branch): a leading dash made
        # `python tools/qa_log.py --help` write qa/--help at 1 byte, twice -
        # R2808 recorded it and R2809 reproduced it. The pollution was silent
        # because a one-byte file lands in the healthy tee dialect, which the
        # writer census never flags. main() routes its three known flags
        # before a name reaches this guard, so nothing legitimate is blocked.
        raise ValueError("name must not start with a dash, got %r" % name)


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
    """AC-QAL4: name the dialect of an existing file, read-only.

    AC-QALB8 (R2807): a BOM-less UTF-16 file has no BOM to catch it and decodes
    as valid utf-8 once the NULs are ignored, so it used to be named utf-8/lf -
    the healthy dialect - by both this face and the writer census. NUL is the
    signature that catches it, and it is named here rather than absorbed.
    """
    if raw.startswith(BOM_16LE) or raw.startswith(BOM_16BE):
        return "ps-utf16"
    if raw.startswith(BOM_UTF8):
        return "utf-8-bom"
    if b"\x00" in raw:
        return "nul-bytes"
    if b"\r" in raw:
        return "crlf"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "undecodable"
    if raw and not raw.endswith(b"\n"):
        return "no-trailing-newline"
    return "utf-8/lf"


PROOF_LINE_RE = re.compile(
    r"^LOG OK path=(\S+) bytes=(\d+) lines=(\d+) sha16=([0-9a-f]{16})$")


def mark_carried_proofs(text):
    """R3203 (AC-QAL9): a proof line carried in by a relog is not this
    file's proof.

    Measured before this function existed: a generator that prints
    "LOG OK path=... bytes=... lines=... sha16=..." on stdout had its
    whole stdout stored through this writer, and the new file carried
    that line unchanged while its own sha16 was a different number
    (761 bytes, carried 271ba9eb7b2d1230, own 4210a333be0b1d92). The
    dialect faces cannot see it - classify() answered utf-8/lf and
    verify_written() read back clean - so the only reader who could
    catch it was a human comparing hashes.

    The line is kept, never dropped (the information is real: it proves
    another file), and prefixed with CARRIED so no reader can take it for
    this log's own proof. A line that does not match the exact shipped
    shape is left alone: guessing at a near miss would be a second guess
    on top of the first.
    """
    carried = 0
    out = []
    for line in text.split("\n"):
        if PROOF_LINE_RE.match(line):
            out.append("CARRIED " + line)
            carried += 1
        else:
            out.append(line)
    if not carried:
        return text, 0
    return "\n".join(out), carried


def count_carried_proofs(text):
    """R3204 (AC-QAL10): how many carried proofs a body quotes, exact shapes.

    A reader could see a CARRIED line but no machine face could count it:
    --check answered the same text for 0, 1 and 2 of them, and both the
    writer census and the pre-commit gate judge the dialect class only. So
    the count is named here. Exact shape after the prefix, same rule as
    mark_carried_proofs: a near miss is not a count.
    """
    carried = 0
    for line in text.split("\n"):
        if line.startswith("CARRIED ") and PROOF_LINE_RE.match(line[8:]):
            carried += 1
    return carried


def count_bare_proofs(text):
    """R3205 (AC-QAL11): how many UNMARKED proof lines a body carries.

    The same exact shape mark_carried_proofs marks, asked without the
    CARRIED prefix. A bare line proves some other file and reached this body
    without going through do_write - measured today the only such door is
    battery_shard.stream_evidence, which opens the file in place. Counting
    it is not a verdict about the body, only a name for what is in it.
    """
    bare = 0
    for line in text.split("\n"):
        if PROOF_LINE_RE.match(line):
            bare += 1
    return bare


def do_write(name, source_bytes, directory=QA):
    check_name(name)
    text = normalize(read_source(source_bytes))
    text, carried = mark_carried_proofs(text)
    path = write_atomic(directory, name, text)
    proof = verify_written(path)
    if carried:
        sys.stdout.write(
            "QA-LOG CARRIED proofs=%d (a LOG OK line names another file, so "
            "it is marked CARRIED and is not this log's proof)\n" % carried)
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
    body = raw.decode("utf-8")
    sys.stdout.write("QA-LOG OK name=%s dialect=utf-8/lf bytes=%d carried=%d "
                     "bare_proofs=%d\n"
                     % (name, len(raw), count_carried_proofs(body),
                        count_bare_proofs(body)))
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

        # R3203 (AC-QAL9): a carried proof line is marked, never certified.
        # Measured before the repair: a relog of a generator's stdout kept
        # "LOG OK ... sha16=<other file>" verbatim inside a file whose own
        # sha16 was a different number.
        proof = (b"PASS one\n"
                 b"LOG OK path=qa/preview.log bytes=661 lines=9 "
                 b"sha16=271ba9eb7b2d1230\n")
        do_write("carried-qal9.log", proof, directory=tmp)
        first = io.open(os.path.join(tmp, "carried-qal9.log"), "rb").read()
        do_write("carried2-qal9.log", first, directory=tmp)
        second = io.open(os.path.join(tmp, "carried2-qal9.log"), "rb").read()
        plain = b"PASS x\n"
        do_write("plain-qal9.log", plain, directory=tmp)
        plain_out = io.open(os.path.join(tmp, "plain-qal9.log"), "rb").read()
        near = (b"LOG OK path=qa/preview.log bytes=six lines=9 "
                b"sha16=271ba9eb7b2d1230\n")
        do_write("near-qal9.log", near, directory=tmp)
        near_out = io.open(os.path.join(tmp, "near-qal9.log"), "rb").read()
        check(first.count(b"CARRIED LOG OK path=") == 1
              and b"\nLOG OK path=" not in first
              and second.count(b"CARRIED") == 1
              and plain_out == plain
              and near_out == near,
              "qal9-carried-proof-marked-once-and-only-exact-shapes")
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
