"""R2507 receipt: append the push line to state.json in its own commit.

The export is re-derived again after this line lands (the R2449/R2433 ordering
law), so the derived counters cannot be left one line behind. ASCII source.
"""
import io
import json
import re
import sys

P = "src/os/state.json"

LINE = (
    "2026-11-07 R2507 push: git push origin main SUCCEEDED this window "
    "(e4808d95..c048aafa main -> main) and git rev-parse read HEAD equal to "
    "origin/main at c048aafa, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER "
    "the state append (the R2449/R2433 ordering law) and the driver carries "
    "the queue face itself, so the document the CEO reads reported "
    "queue=CURRENT with no drift, check_export_consistency read pass=21 "
    "fail=0 at state_tick=2507 with the three CEO lines derived rather than "
    "typed, and the debt gate now names reconcile-battery-R2507 first=yes at "
    "the measured 583 suites and 4474 criteria. This receipt line lands in its "
    "own commit and the export is re-derived once more after it, so the "
    "derived counters cannot be left one line behind."
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL tail %r" % text[-30:])
        return 2
    if "R2507 push:" in text:
        print("NOOP already carries the receipt")
        return 0
    before = len(json.loads(text)["log"])
    block = ",\r\n                " + json.dumps(LINE, ensure_ascii=False)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    raw_after = io.open(P, "rb").read()
    state = json.loads(raw_after.decode("utf-8"))
    lf_only = raw_after.count(b"\n") - raw_after.count(b"\r\n")
    print("receipt tick=%d loglen=%d bytes=%d crlf=%d lf_only=%d"
          % (state["tick"], len(state["log"]), len(raw_after),
             raw_after.count(b"\r\n"), lf_only))
    return 0 if (len(state["log"]) == before + 1 and lf_only == 0) else 1


if __name__ == "__main__":
    sys.exit(main())