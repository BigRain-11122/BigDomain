"""R2515 push line: record the delivered refs after the push succeeded."""
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
    "2026-11-07 R2515 push: git push origin main SUCCEEDED this window "
    "(f80b75a9..49d47243 main -> main) and git rev-parse read HEAD equal to "
    "origin/main at 49d47243, so the whole window is delivered and nothing is "
    "left staged. The export was refreshed through the shipped driver AFTER "
    "the state append (the R2449/R2433 ordering law) and that driver carries "
    "the queue face itself, so the document the CEO reads reported queue="
    "CURRENT at 240025 bytes with queue_drifted=(none) and "
    "check_export_consistency read pass=21 fail=0 at state_tick=2515 with the "
    "three CEO lines derived rather than typed. The debt gate now names "
    "reconcile-battery-R2515 first=yes at the pre-registered 587 suites / "
    "4498 criteria, so the next window owes the battery on this committed "
    "tree before any further product byte."
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
    ok = back["log"][-1] == LINE and back["tick"] == 2515
    print("state %s log=%d bytes=%d readback=%s"
          % ("OK" if ok else "FAIL", len(back["log"]),
             os.path.getsize(PATH), "ok" if ok else "mismatch"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())