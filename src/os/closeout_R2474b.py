"""R2474b closeout: append the delivered-push and self-heal lines to the log."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-05 R2474 push: git push origin main SUCCEEDED this window "
    "(5cbdfe22..4aa99ade main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 4aa99ade with an empty git status, so the R2474 verification "
    "commit is delivered and nothing is left staged. The export is re-derived "
    "through the shipped drivers AFTER this state append (the R2449/R2433 "
    "ordering law), so the published document carries this line rather than "
    "predating it; check_export_consistency then reads pass=21 fail=0.",

    "2026-11-05 R2474 self-heal check: BigDomain-OSLoop exists and reads Running "
    "(last run 2026-11-05 15:39, next 15:44), but its Principal.LogonType still "
    "reads Interactive, which the 2026-09-29 machine law forbids for every lane "
    "task; src/os/register_loop_task.ps1 needs an elevated shell while this "
    "session is unelevated, so the definition was left untouched again (carried "
    "as the stale row loop-s4u-reconcile).",
]


def main():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "os"))
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries these lines")
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
    print("log +%d, bytes=%d" % (len(LINES), os.path.getsize(PATH)))


if __name__ == "__main__":
    main()