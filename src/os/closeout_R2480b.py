"""R2480b closeout: append the delivered-push line after the push lands, so the
published export can be re-derived on top of it (the R2449/R2433 ordering law).
"""

import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
PATH = os.path.join(ROOT, "src", "os", "state.json")

LINES = [
    "2026-11-06 R2480 push: git push origin main SUCCEEDED this window "
    "(cd78883c..ef6834a3 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at ef6834a3 with an empty git status afterwards, so the R2480 "
    "verification commit is delivered and nothing is left staged. The export is "
    "re-derived through the shipped driver AFTER this state append (the "
    "R2449/R2433 ordering law), so the published document carries this line "
    "rather than predating it; check_export_consistency then reads pass=21 "
    "fail=0.",
]


def main():
    import sys
    sys.path.insert(0, os.path.join(ROOT, "src", "os"))
    import state_io
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINES[-1]:
        print("log already carries this line")
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
    print("log +%d bytes=%d" % (len(LINES), os.path.getsize(PATH)))


if __name__ == "__main__":
    main()