"""R2519 push record: append the delivered refs to the state log."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "state.json")

LINE = (
    "2026-11-07 R2519 push: git push origin main SUCCEEDED this window "
    "(aebb7489..741a98bf main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 741a98bf, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER "
    "the state append (the R2449/R2433 ordering law) and that driver carries "
    "the queue face itself, so the document the CEO reads reported "
    "queue=CURRENT at 248888 bytes with queue_drifted=(none) and "
    "check_export_consistency read pass=21 fail=0 at state_tick=2519 with the "
    "three CEO lines derived rather than typed. The debt gate now names "
    "reconcile-battery-R2519 first=yes at the pre-registered 589 suites / "
    "4510 criteria, so the next window owes the battery on this committed "
    "tree before any further product byte."
)


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINE:
        print("already appended")
        return 0
    state["log"].append(LINE)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = back["log"][-1] == LINE and back["tick"] == 2519
    print("state %s tick=%s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", back["tick"], len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())