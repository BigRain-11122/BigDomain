"""Evidence capture tail guard (R2718).

The shipped pair of capture faces refuses CRLF, lone CR, non-utf-8 bytes, a
BOM prefix and NUL, but MEASURED this window on that pair a payload whose last
line is UNTERMINATED still LANDS on BOTH readers (bytes=18 on a two-line
fixture), so an evidence file can end mid-line while every downstream line
reader counts that fragment as a line.

This face refuses a non-empty payload whose last byte is not LF, naming the
form and the measured byte count plus that last byte, while every byte the
shipped pair lands is handed to that pair unchanged. Its one positive
decision is named in AC-ETAIL5: a ZERO-byte payload is ACCEPTED and landed as
an empty file, because there is no unterminated tail to refuse.

Criteria AC-ETAIL1..AC-ETAIL6 were pinned in state/queue/tech.md:692 at R2716
BEFORE this code existed. Stdlib only, ASCII source, no clock, zero network.
"""

import argparse
import json
import os
import sys

import evidence_utf8_capture as EUC
import evidence_utf8_capture_bom_guard as EBG

LABEL = "os-evidence-capture-tail-guard"

E_ARGS = EUC.E_ARGS
E_TAIL = "E_ETAIL_TAIL"
E_EXISTS = EUC.E_EXISTS

USAGE = ("usage: evidence_capture_tail_guard.py --target PATH --source PATH "
         "[--root PATH] [--json]\n")


class Refused(EUC.CaptureRefused):
    """A refused capture that also names the last byte it saw, when relevant."""

    def __init__(self, code, detail="", counters=None, last=None):
        EUC.CaptureRefused.__init__(self, code, detail, counters)
        self.last = last


def refusal_of(data):
    """None when the bytes may land; otherwise the code that names why."""
    raw = EUC.as_bytes(data)
    refusal = EBG.refusal_of(raw)
    if refusal is not None:
        return refusal
    if raw and not raw.endswith(b"\n"):
        return {"code": E_TAIL, "counters": EUC.measure(raw),
                "last": raw[-1]}
    return None


def capture(target, data, root=None):
    """Refuse an unterminated tail, otherwise land exactly as the pair does."""
    raw = EUC.as_bytes(data)
    path = EUC.resolve(root, target)
    counts = EUC.measure(raw)
    if os.path.exists(path):
        raise Refused(E_EXISTS, path, counts)
    refusal = refusal_of(raw)
    if refusal is not None:
        raise Refused(refusal["code"], path, refusal["counters"],
                      refusal.get("last"))
    report = EBG.capture(path, raw, root=root)
    report["tail_ok"] = True
    return report


def refusal_line(err):
    """One ASCII line naming the code, the target and every measured count."""
    line = "REFUSED code=%s target=%s" % (err.code, err.detail)
    for key, name in (("bytes", "bytes"), ("crlf", "crlf"),
                      ("lone_cr", "lone_cr"), ("nul", "nul"),
                      ("bad_offset", "offset")):
        value = err.counters.get(key)
        if value is not None:
            line += " %s=%s" % (name, value)
    if err.last is not None:
        line += " tail_last=0x%02x" % err.last
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
    source = EUC.resolve(args.root, args.source)
    try:
        with open(source, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError):
        print("REFUSED code=%s source=%s" % (EUC.E_NO_SOURCE, source))
        return 3
    try:
        report = capture(args.target, raw, root=args.root)
    except Refused as err:
        print(refusal_line(err))
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print("capture target=%s bytes=%d sha256=%s crlf=%d lone_cr=%d"
              " nul=%d tail_ok=%s verdict=%s"
              % (report["target"], report["bytes"], report["sha256"],
                 report["crlf"], report["lone_cr"], report["nul"],
                 report["tail_ok"], report["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
