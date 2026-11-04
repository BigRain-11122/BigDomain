"""One-off repair for the R2439 verification window.

The census named three R2438 evidence logs as pwsh-capture: utf-8 bodies whose
every line ends CRLF because they were taken through a PowerShell redirect.
The payload is intact; only the transport is wrong.  This script proves the
line set is identical on both sides of the normalisation BEFORE writing,
lands the normalised text as utf-8 LF through ONE atomic replace, and reads
the bytes back.  It never widens the census baseline.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run_identity as RI

FILES = (
    "owner-table-triage-expiry-R2438-a.log",
    "owner-table-triage-expiry-R2438-b.log",
    "owner-table-triage-expiry-live-R2438.log",
)


def repair(qa_dir):
    rows = []
    for name in FILES:
        path = os.path.join(qa_dir, name)
        with open(path, "rb") as fh:
            before = fh.read()
        text = before.decode("utf-8")
        normalised = RI.normalize(text)
        if normalised.splitlines() != text.splitlines():
            raise SystemExit("payload changed for %s" % name)
        out = normalised.encode("utf-8")
        tmp = path + ".repair-tmp"
        with open(tmp, "wb") as fh:
            fh.write(out)
        os.replace(tmp, path)
        with open(path, "rb") as fh:
            after = fh.read()
        rows.append({
            "name": name,
            "before": len(before),
            "after": len(after),
            "crlf": after.count(b"\r\n"),
            "lone_cr": after.count(b"\r") - after.count(b"\r\n"),
            "lines": len(after.decode("utf-8").splitlines()),
            "readback": after == out,
        })
    return rows


def main():
    qa_dir = sys.argv[1] if len(sys.argv) > 1 else "qa"
    for row in repair(qa_dir):
        print(
            "%(name)s %(before)dB -> %(after)dB crlf=%(crlf)d lone_cr=%(lone_cr)d "
            "lines=%(lines)d readback=%(readback)s" % row
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())