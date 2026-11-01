"""heartbeat_R2344 - append this round's heartbeat line, derived from evidence."""

import io
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
HB = os.path.join(ROOT, "heartbeat.txt")
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2344.log")

RUNNER_RE = re.compile(r"RUNNER\s+(PASS|FAIL)[^\n]*", re.IGNORECASE)
BATCH_RE = re.compile(r"BATTERY rc=(-?\d+) ([\d.]+)s")


def reading():
    if not os.path.exists(EVIDENCE):
        return "EVIDENCE-ABSENT"
    text = io.open(EVIDENCE, "r", encoding="utf-8", errors="replace").read()
    runner = ""
    batch = ""
    for hit in RUNNER_RE.finditer(text):
        runner = hit.group(0).strip()
    for hit in BATCH_RE.finditer(text):
        batch = hit.group(0).strip()
    if not batch and runner:
        tail = re.search(r"in ([\d.]+)s", runner)
        batch = "wall %ss" % tail.group(1) if tail else ""
    return "%s; %s" % (runner or "NO-RUNNER-LINE", batch or "NO-RUNTIME-LINE")


def main():
    text = io.open(HB, "r", encoding="utf-8").read()
    if "tick 2344 " in text:
        print("ALREADY-PRESENT")
        return 0
    line = ("tick 2344 R2344 tooling-defect window: DEC baseline parse fixed at "
            "its birth site (array stringified to 65 tokens, comma split left 1) "
            "plus a collapse guard, re-scan [DEC] PASS, committed tree battery %s"
            % reading())
    body = text if text.endswith("\n") else text + "\n"
    body += line + "\n"
    temp = HB + ".tmp"
    with io.open(temp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    os.replace(temp, HB)
    with io.open(HB, "r", encoding="utf-8") as handle:
        back = handle.read()
    if back != body or os.path.exists(temp):
        print("E_READBACK")
        return 3
    print("HEARTBEAT appended lines=%d" % len(back.splitlines()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())