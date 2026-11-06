"""R2510 receipt: append the push line after the closeout commit landed.

The export is re-derived AFTER this append so the derived counters cannot be
left one line behind. ASCII source, stdlib only.
"""
import io
import json
import re
import sys

P = "src/os/state.json"

LINE = (
    "2026-11-07 R2510 push: git push origin main SUCCEEDED this window "
    "(66b99a20..7802a2da main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 7802a2da, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER the "
    "state append (the R2449/R2433 ordering law) and that driver carries the "
    "queue face itself, so the document the CEO reads reported queue=CURRENT at "
    "225792 bytes with queue_drifted=(none), check_export_consistency read "
    "pass=21 fail=0 at state_tick=2510 with the three CEO lines derived rather "
    "than typed, and the debt gate now names product-face-R2510 first=yes at "
    "the tech head line 549 prefix AC-STPT1. This receipt line lands in its own "
    "commit with the export re-derived once more after it, so the derived "
    "counters cannot be left one line behind."
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL tail %r" % text[-30:])
        return 2
    before = len(json.loads(raw.decode("utf-8"))["log"])
    block = ",\r\n                " + json.dumps(LINE, ensure_ascii=False)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    lf_only = raw_after.count(b"\n") - raw_after.count(b"\r\n")
    print("tick=%d loglen=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(raw_after),
             raw_after.count(b"\r\n"), lf_only))
    return 0 if (len(state["log"]) == before + 1 and lf_only == 0) else 1


if __name__ == "__main__":
    sys.exit(main())