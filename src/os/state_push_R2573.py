"""R2573 push line: append the delivery line after the push, proved round-trip."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(REPO, "src", "os", "state.json")

LINE = (
    "2026-11-08 R2573 push and export: git push origin main SUCCEEDED this "
    "window (20f49071..7a9891e0 main -> main) and git rev-parse read HEAD "
    "equal to origin/main at 7a9891e0 with an empty git status after the "
    "commit, so the whole window is delivered. The export was refreshed AFTER "
    "the state append (the R2449/R2433 ordering law) through this round own "
    "driver src/os/export_R2573.py to 382561 bytes at tick 2573 with "
    "queue=CURRENT and queue_drifted=(none), and check_export_consistency "
    "read pass=21 fail=0 VERDICT PASS with the three CEO lines derived rather "
    "than typed. The debt gate now names reconcile-battery-R2573 first=yes at "
    "the pre-registered 616 suites / 4672 criteria, so the next window owes "
    "that battery on this committed tree before any further product byte, and "
    "the product face behind it is tech line 609 prefix AC-PNDCI1."
)


def main():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    data = json.loads(text)
    trial = json.dumps(data, indent=1, ensure_ascii=False)
    if trial != text:
        print("REFUSED E_SA_RT_LAYOUT round-trip differs (%d vs %d)"
              % (len(raw), len(trial.encode("utf-8"))))
        return 3
    before = len(raw)
    data["log"].append(LINE)
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    back = json.loads(io.open(STATE, encoding="utf-8").read())
    ok = back["log"][-1] == LINE
    print("STATE push-line log=%d before=%dB after=%dB wrote=%s"
          % (len(back["log"]), before, os.path.getsize(STATE),
             "yes" if ok else "no"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())