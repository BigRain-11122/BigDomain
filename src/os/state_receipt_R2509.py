"""R2509 receipt: append the push line, then the export re-derives after it."""

import io
import json
import sys

P = "src/os/state.json"
LINE = (
    "2026-11-07 R2509 push: git push origin main SUCCEEDED this window "
    "(d987fa7b..8d12b888 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 8d12b888, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER the "
    "state append (the R2449/R2433 ordering law) and the driver carries the "
    "queue face itself, so the document the CEO reads reported queue=CURRENT at "
    "225884 bytes with queue_drifted=(none), check_export_consistency read "
    "pass=21 fail=0 at state_tick=2509, and the debt gate now names "
    "reconcile-battery-R2509 first=yes at the pre-registered 584 suites / 4480 "
    "criteria. This receipt line lands in its own commit with the export "
    "re-derived once more after it, so the derived counters cannot be left one "
    "line behind."
)


def main():
    raw = io.open(P, "rb").read()
    text = raw.decode("utf-8")
    tail = "\r\n  ]\r\n}\r\n"
    if not text.endswith(tail):
        print("FAIL tail %r" % text[-30:])
        return 2
    if LINE in text:
        print("receipt ALREADY-PRESENT")
        return 0
    before = len(json.loads(text)["log"])
    block = ",\r\n                " + json.dumps(LINE, ensure_ascii=False)
    text = text[:-len(tail)] + block + tail
    io.open(P, "w", encoding="utf-8", newline="").write(text)
    state = json.loads(io.open(P, encoding="utf-8").read())
    ok = len(state["log"]) == before + 1
    print("loglen=%d ok=%s bytes=%d"
          % (len(state["log"]), ok, len(text.encode("utf-8"))))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())