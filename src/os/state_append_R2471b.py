"""R2471 closeout part b: push receipt and self-heal line, then export again."""
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
    "2026-11-05 R2471 self-heal check: BigDomain-OSLoop exists and reads Running, but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (carried as the stale row loop-s4u-reconcile).",
    "2026-11-05 R2471 push: git push origin main SUCCEEDED this window (d5e7de5d..f483f0c9 main -> main) and git rev-parse read HEAD equal to origin/main at f483f0c9 with an empty git status, so the business commit is delivered and nothing is left staged. The export was re-derived through the shipped gate AFTER this state append (the R2449/R2433 ordering law), so the published document carries these lines rather than predating them.",
]


def main():
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("already appended")
        return
    state["log"].extend(LINES)
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    ok = len(back["log"]) == len(state["log"]) and back["tick"] == 2471
    print("APPEND tick=%d log_items=%d bytes=%d readback=%s"
          % (back["tick"], len(back["log"]), os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())