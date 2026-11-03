# append_R2409.py - append the two closeout-continuation log items to state.
# Surgical, CRLF-preserving, payload-verified; writes nothing else.

import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

ITEMS = [
    "2026-11-03 R2409 closeout fold, measured not assumed: the closeout landed "
    "state.json at 78511B against the 78500B waterline (margin -11), so fold "
    "650 moved log items 2..77 (76 items, the R2398..R2408 blocks) verbatim "
    "into logs/state-log-archive-2026-11.md at a true round-block boundary - "
    "predicted 9141B and measured 9141B exactly, margin 69359B, 63 window "
    "tokens covered with token_missing=[], round_split=None. The fold created "
    "residue for the eight rounds whose stamps moved out of the live window, so "
    "they were spliced in ONE write through the shipped batch CLI (R2398..R2404 "
    "and R2406 declared DELIVERED, entries 252 -> 260, 70797 -> 73325 bytes "
    "exactly as predicted, residue_triage then reads TRIAGED 260/260 with "
    "untriaged=0 unmatched=0 disagrees=0 expired=0) and the four ledger suites "
    "plus the residue suites read green afterwards.",
    "2026-11-03 R2409 closeout correction, stated instead of silently repaired: "
    "the first export refresh left three derived counters stale "
    "(log_lines_in_window, substantive_non_idle_mention_lines and the results "
    "tick row) and the tick label row was duplicated by the repair itself; the "
    "counters were set to the checker own recomputation, the duplicate label "
    "row was removed and the single label row carries 2409, after which "
    "check_export_consistency reads 21/21 PASS. The export was written twice for "
    "this reason and the first attempt is disclosed rather than swept.",
]


def main():
    text = io.open(STATE, "r", encoding="utf-8", newline="").read()
    marker = '"' + "\r\n  ]\r\n}"
    if text.count(marker) != 1:
        sys.stdout.write("APPEND R2409: log tail not unique\n")
        return 1
    pad = " " * 16
    block = "".join(",\r\n" + pad + json.dumps(item, ensure_ascii=True)
                    for item in ITEMS)
    text = text.replace(marker, '"' + block + "\r\n  ]\r\n}")
    payload = json.loads(text)
    if payload["tick"] != 2409:
        sys.stdout.write("APPEND R2409: tick moved\n")
        return 1
    io.open(STATE, "wb").write(text.encode("utf-8"))
    back = json.loads(io.open(STATE, "r", encoding="utf-8", newline="").read())
    if len(back["log"]) != 10:
        sys.stdout.write("APPEND R2409: read-back log length %d\n"
                         % len(back["log"]))
        return 1
    sys.stdout.write("APPEND R2409 items=2 log=%d bytes=%d\n"
                     % (len(back["log"]), len(text.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())