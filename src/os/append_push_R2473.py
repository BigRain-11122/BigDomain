"""R2473: append the push line and the self-heal line after the push succeeded."""
import io
import json
import os
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
sys.path.insert(0, SRC)
import state_io  # noqa: E402

LINES = [
    "2026-11-05 R2473 self-heal check: BigDomain-OSLoop exists and reads Ready, "
    "but its Principal.LogonType still reads Interactive, which the 2026-09-29 "
    "machine law forbids for every lane task; src/os/register_loop_task.ps1 needs "
    "an elevated shell while this session is unelevated, so the definition was "
    "left untouched again (carried as the stale row loop-s4u-reconcile).",
    "2026-11-05 R2473 push: git push origin main SUCCEEDED this window "
    "(f9f83a3f..49139e3c main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 49139e3c, so the UGC console commit is delivered and nothing "
    "is left staged. The export is re-derived through the shipped drivers AFTER "
    "this state append (the R2449/R2433 ordering law), so the published document "
    "carries these lines rather than predating them.",
]


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    added = 0
    for line in LINES:
        if line not in state["log"]:
            state["log"].append(line)
            added += 1
    if not added:
        print("lines already present")
        return 0
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if back["log"][-1] != LINES[-1]:
        raise SystemExit("E_PUSH_READBACK")
    print("appended=%d bytes=%d items=%d" % (added, os.path.getsize(PATH),
                                             len(back["log"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())