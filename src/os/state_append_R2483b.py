"""R2483b: append the push receipt line and re-derive the export after it,
so the published document carries the line rather than predating it
(the R2449/R2433 ordering law).
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

LINES = [
    "2026-11-06 R2483 push: git push origin main SUCCEEDED this window (709e4e30..651b6074 main -> main) and git rev-parse read HEAD equal to origin/main at 651b6074 with an empty git status afterwards, so both R2483 commits - the evidence-dialect repair 6f2e6eb4 and the verification closeout 651b6074 - are delivered and nothing is left staged. The export is re-derived through the shipped driver AFTER this state append (the R2449/R2433 ordering law), so the published document carries this line rather than predating it.",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return 0
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = len(back["log"]) == len(state["log"]) and back["tick"] == 2483
    print("APPEND tick=%d log_items=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())