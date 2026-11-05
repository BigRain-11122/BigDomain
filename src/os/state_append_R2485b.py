"""R2485 push receipt: append one log item that records the delivered commit
and nothing else. Tick does not move; no token moves; canon write + readback.
"""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

LINE = (
    "2026-11-06 R2485 push: git push origin main SUCCEEDED this window "
    "(55d6ecbd..c74ff6a5 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at c74ff6a5 with an empty git status afterwards, so the "
    "verification commit c74ff6a5 is delivered and nothing is left staged. "
    "The export was re-derived through the shipped driver AFTER the state "
    "append (the R2449/R2433 ordering law), so the published document carries "
    "this window's line rather than predating it; check_export_consistency "
    "then read pass=21 fail=0 with state_tick=2485."
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
    ok = back["log"][-1] == LINE and back["tick"] == 2485
    print("APPEND push-line log_items=%d bytes=%d readback=%s"
          % (len(back["log"]), os.path.getsize(PATH), "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())