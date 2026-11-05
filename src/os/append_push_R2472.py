"""R2472: append the push line to state.json after the push succeeded."""
import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
sys_path = SRC

import sys
sys.path.insert(0, sys_path)
import state_io  # noqa: E402

LINE = (
    "2026-11-05 R2472 push: git push origin main SUCCEEDED this window "
    "(b1938c87..9c451991 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 9c451991 with an empty git status, so the R2472 verification "
    "commit and its birth-site repair are delivered and nothing is left staged. "
    "The export is re-derived through the shipped drivers AFTER this state append "
    "(the R2449/R2433 ordering law), so the published document carries this line "
    "rather than predating it."
)


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINE:
        print("push line already present")
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
    if back["log"][-1] != LINE:
        raise SystemExit("E_PUSH_READBACK")
    print("push line appended bytes=%d items=%d" % (os.path.getsize(PATH),
                                                    len(back["log"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())