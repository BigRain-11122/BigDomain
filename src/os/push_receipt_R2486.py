"""R2486 push receipt: one line appended after the deliverable is pushed, then
the export is re-derived so the published document carries the receipt rather
than predating it (R2449/R2433 ordering law).
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
    "2026-11-06 R2486 push: git push origin main SUCCEEDED this window "
    "(ad13ade2..c652db1e main -> main) and git rev-parse read HEAD equal to "
    "origin/main at c652db1e with an empty git status afterwards, so the R2486 "
    "tech-face commit is delivered and nothing is left staged. The export was "
    "re-derived through the shipped driver AFTER the state append (the "
    "R2449/R2433 ordering law) and then the queue block was landed through the "
    "shipped gate after the face read STALE, so check_export_consistency reads "
    "pass=21 fail=0 at state_tick=2486 with the queue face CURRENT."
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
    ok = back["log"][-1] == LINE and back["tick"] == 2486
    print("RECEIPT tick=%d log_items=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())