"""R2467 post-push state append (one-off): push receipt and self-heal check."""
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
    "2026-11-05 R2467 push: git push origin main SUCCEEDED this window (06f4473d..e9047c63 main -> main) and git rev-parse read HEAD equal to origin/main at e9047c63, so the R2467 console commit is delivered and nothing is left staged. The export and the queue block were re-derived and re-applied through the shipped drivers AFTER this state append (the R2449/R2433 ordering law, which is exactly the defect R2465 paid for), so the published document carries this line rather than predating it.",

    "2026-11-05 R2467 self-heal check: BigDomain-OSLoop exists and is Running (last run 2026-11-05 12:04), but its Principal.LogonType still reads Interactive, which the 2026-09-29 machine law forbids for every lane task; src/os/register_loop_task.ps1 needs an elevated shell while this session is unelevated, so the definition was left untouched again (two-hundred-and-twenty-third consecutive disclosure, carried as the stale row loop-s4u-reconcile).",
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
    print("appended lines=%d bytes=%d" % (len(back["log"]), os.path.getsize(PATH)))


if __name__ == "__main__":
    main()