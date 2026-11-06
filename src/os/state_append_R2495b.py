"""R2495 post-push state append (one-off): push receipt and self-heal check."""

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
    "2026-11-06 R2495 push: git push origin main SUCCEEDED this window "
    "(a02210b5..b1296f7a main -> main) and git rev-parse read HEAD equal to "
    "origin/main at b1296f7a, so the closeout commit is delivered and nothing "
    "is left staged. The export was re-derived through the shipped driver AFTER "
    "this state append (the R2449/R2433 ordering law) and the queue block was "
    "landed through queue_export_gate_wire --execute, so the document the CEO "
    "reads carries this round rather than predating it.",

    "2026-11-06 R2495 self-heal check: BigDomain-OSLoop exists and is Running, "
    "but its Principal.LogonType still reads Interactive, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 "
    "needs an elevated shell while this session is unelevated, so the "
    "definition was left untouched again (carried as the stale row "
    "loop-s4u-reconcile).",
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
    if len(back["log"]) != len(state["log"]):
        raise SystemExit("E_CLOSEOUT_READBACK")
    print("appended lines=%d bytes=%d" % (len(back["log"]),
                                          os.path.getsize(PATH)))


if __name__ == "__main__":
    main()