# append_log_R2250.py - add the floor-disclosure line to the R2250 log.
# The round line says the gauge read tech 10/10 at OPEN; closing the claimed
# head row then dropped claimable tech to 9, and the standing seeding duty
# put it back to 10 in the same window. That is a fact about the window and
# belongs in the log, not in prose elsewhere.
import io
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

LINE = (
    "R2250 floor disclosure: the gauge read tech 10/10 claimable at open, then "
    "the claimed head row closing took it to 9/10, so the standing seeding "
    "duty was discharged in the same window - one real gap row appended to "
    "state/queue/tech.md (battery follow-up as one callable: the four "
    "per-round scripts battery_followup_R2235/_R2239/_R2247/_R2249 "
    "re-implement the same four sections and differ only by evidence path and "
    "label, so a fix in one round's copy can stay broken in the next), with "
    "criteria AC-BFU1..AC-BFU6 written into the row BEFORE any code. The "
    "first attempted prefix AC-BF was refused by the seed script's own "
    "idempotence guard because that prefix is already occupied 21 times by "
    "the fingerprint_regen row, so a fresh non-colliding AC-BFU prefix was "
    "registered instead - disclosed, and no criterion relaxed. Gauge at "
    "closeout reads main 5/5 tech 10/10 explore 10/10 FLOOR-MET."
)


def main():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    if "R2250 floor disclosure" in text:
        raise SystemExit("already present")
    eol = "\r\n" if "\r\n" in text else "\n"
    tail = eol + "  ]" + eol + "}"
    if text.count(tail) != 1:
        raise SystemExit("log tail anchor not unique")
    text = text.replace(tail, eol * 0 + "," + eol + " " * 16
                        + json.dumps(LINE, ensure_ascii=True) + tail, 1)
    payload = json.loads(text)
    assert payload["log"][-1] == LINE
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("LOG appended log=%d bytes=%d" % (len(payload["log"]),
                                            len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())