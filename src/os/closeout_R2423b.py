"""R2423 closeout repair: dedupe the double append, restore the tick, then fold."""
import io
import json
import os
import re
import sys

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
SRC = os.path.join(ROOT, "src", "os")
PATH = os.path.join(SRC, "state.json")
GATE = 78500
RESERVE = 6000
ROUND_MARK = "2026-11-04 R2423 "
TOKENS_MARK = "R2423 tokens:"

if SRC not in sys.path:
    sys.path.insert(0, SRC)


def write_state(state):
    import state_io
    text = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    payload = state_io.canon(text).encode("utf-8")
    tmp = PATH + ".tmp"
    with io.open(tmp, "wb") as handle:
        handle.write(payload)
    os.replace(tmp, PATH)
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        back = json.load(handle)
    if back["tick"] != state["tick"] or len(back["log"]) != len(state["log"]):
        raise SystemExit("E_REPAIR_READBACK")
    return os.path.getsize(PATH)


def main():
    with io.open(PATH, "r", encoding="utf-8", newline="") as handle:
        state = json.load(handle)
    log = state["log"]
    starts = [i for i, item in enumerate(log)
              if str(item).startswith(ROUND_MARK + "verification window")]
    tok = [i for i, item in enumerate(log) if str(item).startswith(TOKENS_MARK)]
    print("starts=%s tokens=%s" % (starts, tok))
    if len(starts) == 2 and len(tok) == 2 and starts[1] > starts[0]:
        del log[starts[1]:starts[1] + 8]
        print("removed duplicate R2423 block at %d" % starts[1])
    state["tick"] = 2423
    size = write_state(state)
    print("tick=%d lines=%d bytes=%d" % (state["tick"], len(state["log"]), size))
    if size <= GATE - RESERVE:
        print("fold not due")
        return
    import state_fold
    ends = [i + 1 for i, item in enumerate(log)
            if re.search(r"R\d+ tokens:", str(item))]
    chosen = None
    for end in ends:
        if end < 2:
            continue
        window = log[1:end]
        if state_fold.round_split(window, log[end:]):
            continue
        tokens = set()
        for line in window:
            tokens |= set(state_fold.PAT.findall(str(line)))
        summary = ("Fold R2423: log items 2..%d moved verbatim into the monthly "
                   "archive at a true round-block boundary; tokens covered %s."
                   % (end, ",".join(sorted(tokens))))
        with io.open(PATH, "rb") as handle:
            raw = handle.read()
        plan, _ = state_fold.plan_fold(raw, state, 2, end, summary,
                                       reserve=RESERVE, gate=GATE)
        if plan.get("gate_ok") and not plan.get("tokens_missing"):
            chosen = (end, summary)
            break
    if not chosen:
        print("NO CLEAN FOLD WINDOW - kept at %dB" % size)
        return
    end, summary = chosen
    result = state_fold.fold(ROOT, "R2423", 651, 2, end, summary,
                             reserve=RESERVE, gate=GATE, execute=True)
    print("fold end=%d predicted=%s tokens=%s missing=%s"
          % (end, result.get("predicted_bytes"), result.get("tokens_total"),
             result.get("token_missing")))
    print("after=%dB" % os.path.getsize(PATH))


if __name__ == "__main__":
    main()