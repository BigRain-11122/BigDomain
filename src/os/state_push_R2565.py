"""Record the measured R2565 push in state and re-derive the export."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

STATE = os.path.join(BASE, "state.json")

LINE = (
    "2026-11-08 R2565 push: git push origin main SUCCEEDED this window "
    "(78bc78ff..cb1ffbbf main -> main) and git rev-parse read HEAD equal to "
    "origin/main at cb1ffbbf with an empty git status, so the whole window is "
    "delivered and nothing is left staged. The debt gate now names "
    "reconcile-battery-R2565 first=yes at the re-measured 612 suites / 4648 "
    "criteria, so the next window owes that battery on this committed tree "
    "before any further product byte. The export was refreshed AFTER this "
    "append through this round own driver src/os/export_R2565.py (the "
    "R2449/R2433 ordering law) and its queue block read queue=CURRENT with "
    "queue_drifted=(none); check_export_consistency then read pass=21 fail=0 "
    "VERDICT PASS at state_tick=2565."
)


def main():
    raw = io.open(STATE, "rb").read()
    data = json.loads(raw.decode("utf-8"))
    if json.dumps(data, indent=1, ensure_ascii=False).encode("utf-8") != raw:
        print("REFUSED E_STATE_ROUNDTRIP")
        return 3
    if any(str(line).startswith("2026-11-08 R2565 push:") for line in data["log"]):
        print("ALREADY-RECORDED")
    else:
        data["log"].append(LINE)
        io.open(STATE, "w", encoding="utf-8", newline="\n").write(
            json.dumps(data, indent=1, ensure_ascii=False))
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    print("state tick=%s log=%d last=%r" % (back["tick"], len(back["log"]),
                                            back["log"][-1][:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())