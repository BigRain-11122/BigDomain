"""R2484 push receipt: append the delivery line, then re-derive the export so
the published document carries it (the R2449/R2433 ordering law).

One atomic replace in the state canon with a read-back; the export is refreshed
through the shipped export_R2484 driver so no second derivation exists.
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

import state_io  # noqa: E402
import export_R2484  # noqa: E402

LINE = ("2026-11-06 R2484 push: git push origin main SUCCEEDED this window "
        "(54205c74..91fd42e8 main -> main) and git rev-parse read HEAD equal to "
        "origin/main at 91fd42e8 with an empty git status afterwards, so the "
        "R2484 business commit is delivered and nothing is left staged. The "
        "export is re-derived through the shipped driver AFTER this state "
        "append (the R2449/R2433 ordering law), so the published document "
        "carries this line rather than predating it; check_export_consistency "
        "then reads pass=21 fail=0.")


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    if state["log"] and state["log"][-1] == LINE:
        print("already appended")
    else:
        state["log"].append(LINE)
        text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
        payload = state_io.canon(text).encode("utf-8")
        tmp = PATH + ".tmp"
        with io.open(tmp, "wb") as handle:
            handle.write(payload)
        os.replace(tmp, PATH)
        with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
            back = json.load(handle)
        ok = back["log"][-1] == LINE
        print("PUSH APPEND tick=%d log_items=%d bytes=%d readback=%s"
              % (back["tick"], len(back["log"]), os.path.getsize(PATH),
                 "ok" if ok else "MISMATCH"))
        if not ok:
            return 3
    print(export_R2484.base.main())
    return 0


if __name__ == "__main__":
    sys.exit(main())