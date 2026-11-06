"""state_push_R2497 - append the push receipt line after delivery."""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import state_io  # noqa: E402

PATH = os.path.join(BASE, "state.json")

LINE = (
    "2026-11-06 R2497 push: git push origin main SUCCEEDED this window "
    "(62713a50..2eba4cf8 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 2eba4cf8, so the closeout commit is delivered and nothing "
    "is left staged. The export was re-derived through the shipped driver "
    "AFTER this state append (the R2449/R2433 ordering law) and the driver now "
    "carries the queue face itself, so the document the CEO reads reports "
    "queue=CURRENT with no drift rather than needing a hand-landed block."
)


def main():
    state = json.load(io.open(PATH, encoding="utf-8", newline=""))
    if state["log"] and state["log"][-1] == LINE:
        print("already appended")
        return
    state["log"].append(LINE)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    back = json.load(io.open(PATH, encoding="utf-8", newline=""))
    if back["log"][-1] != LINE:
        raise SystemExit("E_PUSH_RECEIPT_READBACK")
    print("appended push line lines=%d bytes=%d"
          % (len(back["log"]), os.path.getsize(PATH)))


if __name__ == "__main__":
    main()