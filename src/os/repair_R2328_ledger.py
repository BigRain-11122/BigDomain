"""R2328 closeout repair, second defect of the window: the R2327 closeout
wrote its round ledger item WITHOUT the round prefix, so the pinned
'^R<n> tokens:' law could not see it and ledger_lines read
rounds_without_ledger=2327 with VERDICT DIRTY, which gated the whole
ledger family (AC-LGR8, AC-LGA7, AC-LGA8, AC-LGB8, AC-LGN8) red in this
window's battery. Same class as the R2288 defect (a closeout writer that
emitted 'R2288 round ledger: tokens: ...').

Repair at the birth site: the ONE item is prefixed with "R2327 " so it
reads "R2327 tokens: ...". Nothing else changes, the payload of every other
item is proved equal, the file keeps its canonical layout, one atomic
replace, a predicted byte delta and a read-back proof.

Pure ASCII, stdlib only, no network, no clock.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_io as SIO  # noqa: E402

STATE = os.path.join(ROOT, "src", "os", "state.json")
ROUND = "R2327"
NEEDLE = "tokens: local=1 api=0 api_reason=none"


def main():
    raw = io.open(STATE, encoding="utf-8", newline="").read()
    data = json.loads(raw)
    hits = [i for i, it in enumerate(data["log"]) if it.startswith(NEEDLE)]
    if len(hits) != 1:
        raise SystemExit("E_R2328_LEDGER_COUNT %d" % len(hits))
    index = hits[0]
    stale = data["log"][index]
    if stale.startswith(ROUND + " "):
        raise SystemExit("E_R2328_LEDGER_ALREADY_PREFIXED")
    fixed = ROUND + " " + stale
    data["log"][index] = fixed
    text = json.dumps(data, ensure_ascii=False, indent=2)
    # keep the canonical CRLF + sixteen-space item layout through state_io
    canon, report = SIO.canon(text)
    predicted = len(canon.encode("utf-8"))
    before = os.path.getsize(STATE)
    print("before=%dB predicted=%dB delta=%+d layout=%r"
          % (before, predicted, predicted - before, report.get("layout_ok")))
    tmp = STATE + ".tmp-r2328b"
    with io.open(tmp, "w", encoding="utf-8", newline="") as handle:
        handle.write(canon)
    written = os.path.getsize(tmp)
    if written != predicted:
        os.remove(tmp)
        raise SystemExit("E_R2328_PREDICT %d != %d" % (written, predicted))
    os.replace(tmp, STATE)
    if os.path.exists(tmp):
        raise SystemExit("E_R2328_TEMP")
    back = json.loads(io.open(STATE, encoding="utf-8", newline="").read())
    other_equal = [i for i, it in enumerate(back["log"])
                   if i != index and it != data["log"][i]]
    if other_equal:
        raise SystemExit("E_R2328_PAYLOAD %r" % other_equal)
    if back["log"][index] != fixed:
        raise SystemExit("E_R2328_READBACK")
    print("readback=%dB log_len=%d tick=%s"
          % (os.path.getsize(STATE), len(back["log"]), back.get("tick")))


if __name__ == "__main__":
    main()