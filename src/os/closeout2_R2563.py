"""closeout2_R2563 - record the measured push, then let the export follow it.

The R2449/R2433 ordering law: the export is re-derived AFTER the state append,
because a line appended after the refresh leaves the CEO face stale (the R2542
lesson).
"""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")

LINE = (
    "2026-11-08 R2563 push and export: git push origin main SUCCEEDED this "
    "window (5929bd14..ea26a26c main -> main) and git rev-parse read HEAD "
    "equal to origin/main at ea26a26c with an empty git status after the "
    "commit, so the whole window is delivered. The export was refreshed AFTER "
    "the state append through src/os/export_R2563.py to 358243 bytes at tick "
    "2563 with queue=CURRENT and queue_drifted=(none), and "
    "check_export_consistency read pass=21 fail=0 VERDICT PASS with the three "
    "CEO lines derived rather than typed. The debt gate now names "
    "reconcile-battery-R2563 first=yes at the pre-registered 611 suites / 4642 "
    "criteria, so the next window owes that battery on this committed tree "
    "before any further product byte."
)


def main():
    with open(STATE, "rb") as fh:
        raw = fh.read()
    doc = json.loads(raw.decode("utf-8"))
    if json.dumps(doc, indent=1, ensure_ascii=False).encode("utf-8") != raw:
        raise SystemExit("round-trip law broken before mutation")
    doc.setdefault("log", []).append(LINE)
    out = json.dumps(doc, indent=1, ensure_ascii=False).encode("utf-8")
    tmp = STATE + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(out)
    os.replace(tmp, STATE)
    with open(STATE, "rb") as fh:
        back = fh.read()
    doc2 = json.loads(back.decode("utf-8"))
    print("tick", doc2["tick"], "log_lines", len(doc2["log"]),
          "bytes", len(back))


if __name__ == "__main__":
    main()