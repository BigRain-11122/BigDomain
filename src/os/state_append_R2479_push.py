"""R2479 push receipt: append the delivered-push line and move nothing else.

The export is re-derived AFTER this append (the R2449/R2433 ordering law).
The first push attempt was rejected by the server with
"remote: fatal error in commit_refs", which is a remote-side fault rather
than a non-fast-forward, so it is recorded instead of hidden.
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

LINE = (
    "2026-11-06 R2479 push: the FIRST attempt was rejected by the remote with "
    "'remote: fatal error in commit_refs' and a non-fast-forward was not the "
    "cause (local 19b9fdb1 was the remote tip), so it was retried once after "
    "eight seconds instead of being worked around by rewriting history. The "
    "retry SUCCEEDED (19b9fdb1..e7d07771 main -> main); git rev-parse now "
    "reads HEAD equal to origin/main at e7d07771 and git status is empty, so "
    "the R2479 tech commit is delivered and nothing is left staged. The export "
    "is re-derived through the shipped driver AFTER this state append, so the "
    "published document carries this line rather than predating it."
)


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
    ok = back["log"][-1] == LINE and back["tick"] == 2479
    print("APPEND log_items=%d tick=%d bytes=%d readback=%s"
          % (len(back["log"]), back["tick"], os.path.getsize(PATH),
             "ok" if ok else "MISMATCH"))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())