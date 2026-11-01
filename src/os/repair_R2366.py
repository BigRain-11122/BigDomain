"""repair_R2366.py - undo fold 642's over-wide window and refold correctly.

Disclosed defect: closeout_R2366.py chose the LARGEST block boundary whose
predicted size fit the gate, and the boundary it found (line 74) was this
round's OWN tokens line - so fold 642 archived the R2366 round narrative
instead of the older rounds. Repaired the way R2225 was: the state file is
restored byte-exact from the fold's own backup, the archive section the fold
appended is trimmed back off, and the fold is redone over a window that ends
BEFORE this round's block.

Usage: python src/os/repair_R2366.py
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
BACKUP = os.path.join(REPO, "logs", "state-preop-R2366.bak")
ARCHIVE = os.path.join(REPO, "logs", "state-log-archive-2026-11.md")
GATE = 78500
RESERVE = 6000
HEADER = "# --- R2366 fold append"
FOLD_NO = 642


def main():
    # 1. Trim the section this window's fold appended.
    with io.open(ARCHIVE, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    before = len(text.encode("utf-8"))
    cut = text.rfind(HEADER)
    if cut < 0:
        print("REFUSE no %r section found" % HEADER)
        return 2
    trimmed = text[:cut]
    if HEADER in trimmed:
        print("REFUSE more than one R2366 section")
        return 2
    with io.open(ARCHIVE, "w", encoding="utf-8", newline="") as handle:
        handle.write(trimmed)
    after = len(trimmed.encode("utf-8"))
    print("ARCHIVE trimmed %dB -> %dB (removed %dB)"
          % (before, after, before - after))

    # 2. Restore the state file byte-exact from the fold's own backup.
    with io.open(BACKUP, "rb") as handle:
        raw = handle.read()
    state = json.loads(raw.decode("utf-8"))
    log_len = len(state["log"])
    with io.open(STATE, "wb") as handle:
        handle.write(raw)
    with io.open(STATE, "rb") as handle:
        back = handle.read()
    print("STATE restored %dB identical=%s tick=%d log=%d"
          % (len(raw), back == raw, state["tick"], log_len))
    if back != raw:
        return 1

    # 3. Refold over a window that stops before this round's own block, and
    #    at the TRUE end of the previous round's block. Measured defect: the
    #    first attempt ended on a tokens LINE (line 66, inside the R2365
    #    block), which left three R2365 items live with their ledger line
    #    archived - ledger_lines then read rounds_without_ledger=2365 and
    #    new_missing=2365, i.e. the split the R2277/R2336 fold repair exists
    #    for. A tokens line is NOT a block boundary; the last item of the
    #    round is. The round appended its eight items at the tail, so the
    #    boundary is exactly log_len - 8.
    limit = log_len - 8
    probe = state["log"][limit - 1].strip()[:60]
    nxt = state["log"][limit].strip()[:60] if limit < log_len else ""
    print("BOUNDARY end=%d last=%r next=%r" % (limit, probe, nxt))
    window = state["log"][:limit]
    found = set()
    for line in window:
        found |= set(state_fold.PAT.findall(line))
    rounds = sorted(set(re.findall(r"R(\d{4})", " ".join(window))))
    summary = ("Fold %d: log lines 1..%d folded verbatim into the archive at "
               "a TRUE round-block boundary; rounds %s; tokens %s"
               % (FOLD_NO, limit, ",".join("R" + r for r in rounds),
                  " ".join(sorted(found))))
    try:
        plan, _folded = state_fold.plan_fold(
            raw, state, 1, limit, summary, reserve=0, gate=GATE)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print("PLAN refused end=%d %s" % (limit, exc))
        return 1
    print("PLAN end=%d lines=%d predicted=%dB tokens=%d missing=%d gate_ok=%s"
          % (limit, plan["window_lines"], plan["predicted_bytes"],
             plan["tokens_total"], len(plan["tokens_missing"]),
             plan["gate_ok"]))
    if not plan["token_ok"] or not plan["gate_ok"]:
        print("REFUSE plan not clean")
        return 1
    end = limit
    result = state_fold.fold(REPO, "R2366", FOLD_NO, 1, end, summary,
                             reserve=0, gate=GATE, execute=True)
    size = os.path.getsize(STATE)
    print("FOLD %d window=1..%d lines=%d predicted=%dB measured=%dB"
          % (FOLD_NO, end, plan["window_lines"], plan["predicted_bytes"], size))
    print("FOLD result keys: %s" % sorted(result.keys())
          if isinstance(result, dict) else "FOLD rc=%r" % (result,))

    # 4. Prove this round's own narrative is still live.
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        final = json.loads(handle.read())
    live = final["log"]
    keep = [line[:60] for line in live]
    own = [line for line in live if line.startswith("R2366 ")
           or "R2366 " in line[:6]]
    measure = state_fold.measure(size, GATE)
    print("VERIFY log=%d r2366_items=%d margin=%d verdict=%s"
          % (len(live), len(own), measure["margin"], measure["verdict"]))
    for line in keep:
        print("  LIVE %s" % line)
    return 0 if len(own) >= 5 else 1


if __name__ == "__main__":
    sys.exit(main())