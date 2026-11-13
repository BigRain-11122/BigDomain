"""Evidence UTF-8 capture guard (R2714).

The shipped capture ritual src/os/evidence_capture.py runs a suite twice and
lands one utf-8 LF body for its OWN callers, but nothing refuses the bytes a
window is about to land as evidence from anywhere else. MEASURED this window
on the shipped tree before this module existed:

  evidence_capture._flat(text)  rewrites CRLF and lone CR into LF silently,
                               so mangled bytes are normalised into the
                               artifact instead of being refused;
  evidence_capture.run_suite   decodes child output with errors="replace",
                               so a non-UTF-8 byte becomes U+FFFD and the
                               offset that caused it is lost;
  qa_writer_census / the census family only name a bad artifact on the NEXT
                               battery, after it has been committed.

This face refuses at CALL time instead: the bytes handed in must decode as
UTF-8, carry no CRLF and no lone CR, and only then are they landed through
one atomic write with a read-back. A refusal carries its own code and the
measured counters, and writes nothing.

Criteria AC-EUC1..AC-EUC6 were pinned in state/queue/tech.md:689 at R2494
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import hashlib
import json
import os
import sys

LABEL = "os-evidence-utf8-capture"

E_ARGS = "E_EUC_ARGS"
E_NO_SOURCE = "E_EUC_NO_SOURCE"
E_NOT_UTF8 = "E_EUC_NOT_UTF8"
E_CRLF = "E_EUC_CRLF"
E_LONE_CR = "E_EUC_LONE_CR"
E_EXISTS = "E_EUC_EXISTS"
E_BADDIR = "E_EUC_BADDIR"
E_WRITE = "E_EUC_WRITE"

REPORT_KEYS = ("target", "bytes", "sha256", "crlf", "lone_cr", "nul",
               "utf8", "verdict")
COUNT_KEYS = ("bytes", "crlf", "lone_cr", "nul", "utf8", "bad_offset")

USAGE = ("usage: evidence_utf8_capture.py --target PATH --source PATH "
         "[--root PATH] [--json]\n")


class CaptureRefused(Exception):
    """A refused capture: the code names why, counters keep the measurement."""

    def __init__(self, code, detail="", counters=None):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail
        self.counters = dict(counters or {})


def resolve(root, name):
    """A target or source is relative to the given root, never the CWD."""
    if not root:
        return name
    if os.path.isabs(name):
        return name
    return os.path.join(root, name)


def as_bytes(data):
    """Accept exactly bytes or text; anything else is a caller defect."""
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, str):
        return data.encode("utf-8", "strict")
    raise CaptureRefused(E_ARGS, "%r is neither bytes nor text"
                         % (type(data).__name__,))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()[:16].upper()


def measure(data):
    """The counters a refusal reports and a landing publishes."""
    raw = as_bytes(data)
    crlf = raw.count(b"\r\n")
    lone_cr = raw.count(b"\r") - crlf
    nul = raw.count(b"\x00")
    utf8 = True
    bad_offset = None
    try:
        raw.decode("utf-8", "strict")
    except UnicodeDecodeError as err:
        utf8 = False
        bad_offset = err.start
    return {"bytes": len(raw), "crlf": crlf, "lone_cr": lone_cr,
            "nul": nul, "utf8": utf8, "bad_offset": bad_offset}


def refusal_of(data):
    """None when the bytes may land; otherwise its own code and counters."""
    counts = measure(data)
    if not counts["utf8"]:
        return {"code": E_NOT_UTF8, "offset": counts["bad_offset"],
                "counters": counts}
    if counts["crlf"]:
        return {"code": E_CRLF, "counters": counts}
    if counts["lone_cr"]:
        return {"code": E_LONE_CR, "counters": counts}
    return None


def _temp_name(path):
    """One free sibling name; the pid keeps concurrent windows apart."""
    for attempt in range(16):
        candidate = path + ".euc-tmp-%d-%d" % (os.getpid(), attempt)
        if not os.path.exists(candidate):
            return candidate
    return None


def _write_atomic(path, raw):
    """One atomic write with a read-back; no partial or wrong file survives."""
    directory = os.path.dirname(path) or "."
    counters = measure(raw)
    if not os.path.isdir(directory):
        raise CaptureRefused(E_BADDIR, path, counters)
    temp = _temp_name(path)
    if temp is None:
        raise CaptureRefused(E_WRITE, path, counters)
    try:
        handle = open(temp, "xb")
        try:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            handle.close()
        os.replace(temp, path)
    except (IOError, OSError):
        try:
            os.unlink(temp)
        except (IOError, OSError):
            pass
        raise CaptureRefused(E_WRITE, path, counters)
    with open(path, "rb") as back:
        landed = back.read()
    if landed != raw:
        try:
            os.unlink(path)
        except (IOError, OSError):
            pass
        raise CaptureRefused(E_WRITE, path, counters)
    return len(landed)


def capture(target, data, root=None):
    """Refuse or land the bytes; the report names exactly what was measured."""
    raw = as_bytes(data)
    path = resolve(root, target)
    if os.path.exists(path):
        raise CaptureRefused(E_EXISTS, path, measure(raw))
    refusal = refusal_of(raw)
    if refusal is not None:
        raise CaptureRefused(refusal["code"], path, refusal["counters"])
    landed = _write_atomic(path, raw)
    counts = measure(raw)
    return {"target": path, "bytes": landed, "sha256": digest(raw),
            "crlf": counts["crlf"], "lone_cr": counts["lone_cr"],
            "nul": counts["nul"], "utf8": True, "verdict": "LANDED"}


def refusal_line(err):
    """One ASCII line an operator can read without the exception object."""
    line = "REFUSED code=%s target=%s" % (err.code, err.detail)
    for key, name in (("bytes", "bytes"), ("crlf", "crlf"),
                      ("lone_cr", "lone_cr"), ("nul", "nul"),
                      ("bad_offset", "offset")):
        value = err.counters.get(key)
        if value is not None:
            line += " %s=%s" % (name, value)
    return line


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--target")
    parser.add_argument("--source")
    parser.add_argument("--root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args(argv)
    if args.help:
        sys.stdout.write(USAGE)
        return 0
    if not args.target or not args.source:
        sys.stderr.write(USAGE)
        return 5
    source = resolve(args.root, args.source)
    try:
        with open(source, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        print("REFUSED code=%s source=%s" % (E_NO_SOURCE, source))
        return 3
    try:
        report = capture(args.target, raw, root=args.root)
    except CaptureRefused as err:
        print(refusal_line(err))
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print("capture target=%s bytes=%d sha256=%s crlf=%d lone_cr=%d"
              " nul=%d verdict=%s"
              % (report["target"], report["bytes"], report["sha256"],
                 report["crlf"], report["lone_cr"], report["nul"],
                 report["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
