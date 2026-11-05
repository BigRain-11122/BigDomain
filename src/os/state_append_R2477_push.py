"""R2477 push closeout: record the delivered push, then re-derive the export.

Ordering matters (the R2449/R2433 law): the state line lands first and the
published document is derived AFTER it, so the export carries this line rather
than predating it.
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

LINE = ("2026-11-05 R2477 push: git push origin main SUCCEEDED this window "
        "(92e5e494..a90201a4 main -> main) and git status read empty afterwards, "
        "so the R2477 business commit is delivered and nothing is left staged. "
        "The export is re-derived through the shipped driver AFTER this state "
        "append, so the published document carries this line rather than "
        "predating it.")


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
    ok = back["log"][-1] == LINE and back["tick"] == state["tick"]
    print("APPEND push_line log_items=%d tick=%d readback=%s"
          % (len(back["log"]), back["tick"], "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())