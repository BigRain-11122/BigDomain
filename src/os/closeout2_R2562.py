"""closeout2_R2562 - record the measured push in the state log after delivery."""

import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")

LINE = (
    "2026-11-08 R2562 push and export: git push origin main SUCCEEDED this "
    "window (6281f5a9..422a8285 main -> main) and git rev-parse read HEAD "
    "equal to origin/main at 422a8285 with an empty git status after the "
    "commit, so the whole window is delivered. The export was refreshed "
    "AFTER the state append (the R2449/R2433 ordering law) through "
    "src/os/export_R2562.py to 355394 bytes at tick 2562 with queue=CURRENT "
    "and queue_drifted=(none), and check_export_consistency read pass=21 "
    "fail=0 VERDICT PASS with the three CEO lines derived rather than typed. "
    "The debt gate now names product-face-R2562 first=yes on tech line 599 "
    "AC-PNDC1, so the next window owes that product face before any further "
    "byte."
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
    print("tick", json.loads(back.decode("utf-8"))["tick"], "bytes", len(back))


if __name__ == "__main__":
    main()