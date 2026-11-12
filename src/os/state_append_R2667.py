"""state_append_R2667 - the R2667 verification window narrative and tokens.

Every number below was measured off this tree in this window: the five
readings at open, the registry target recounted by import, the live leg read
off its own stream on seven byte axes, and the two process ids confirmed by
command line. The lines are deliberately compact because the state log was
1566 bytes under its waterline at open and no round block was folded here.
"""

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import general_writer_dialect_audit as GWDA  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")

LINES = [
    "2026-11-12 R2667 VERIFICATION window on the battery the debt gate named"
    " first (reconcile-battery-R2661, 653/4894). Five readings: tree EMPTY at"
    " HEAD 5aac6b7d=origin/main, no index.lock; atbd_lines=0"
    " unreplied_groups=0; decisions rows=114 tokens=63 new=0; group orders tail"
    " NEW row 2026-11-12 12:45 read and judged knowledge-only (a bm-a"
    " station_drive lane dispatch, no BigDomain face), so last_order advanced to"
    " it; benchmarks 2026-11-10 inside the gate. debt_gate CLAIM-FIRST"
    " item=reconcile-battery-R2661 carried=6 stale=yes open=45 first=1.",
    "R2667 THE R2665 LEG WAS ADOPTED, MEASURED ON BYTES AND IS STILL LIVE AT"
    " CLOSEOUT: pids 45996 and its child 53916 live by command line;"
    " logs/battery-R2665.stream 613014B utf-8 True bom=False lone_cr=0 nul=0"
    " crlf=4220, 353 PASS suite rows, 0 FAIL, 353 unique names, partial"
    " criteria 2956 of 4894; registry re-measured by import 653/4894/653/653;"
    " tail is the long probe-seam family at a measured 4.75 suites per minute,"
    " so no follow-up section ran and no evidence file exists yet. The row"
    " STAYS OPEN at its unmoved 653/4894 and the next window adopts this leg.",
    "R2667 honest: (a) ZERO product points and no product byte, the owed"
    " battery holding the tree; (b) the battery is NOT green and NOT claimed"
    " green; (c) this closeout lands UNDER the live leg, so its verdict is"
    " admissible only beside a re-run of the export trio on the final committed"
    " tree (R2614 discipline) - named, not left to be discovered; (d)"
    " scan_five_still.py still crashes at its final [ORD-TOP] print on the GBK"
    " console, run under PYTHONIOENCODING=utf-8, WORKED AROUND NOT REPAIRED;"
    " (e) Docker absent; (f) the real 19.9 debit and msgSecCheck still wait on"
    " CEO physical items; (g) tasks.md untouched; (h) BigDomain-OSLoop still"
    " InteractiveToken, needs an ELEVATED shell.",
    "R2667 tokens: local=~6k api=0 api_reason=verification window - one"
    " five-silence scan, one new order row judged knowledge-only, one debt gate"
    " plus queue head and floor, one registry by import on four axes, one live"
    " leg on seven byte axes with two pids confirmed, state/export closeout;"
    " zero cloud calls and zero external API touches",
]


def main():
    with io.open(STATE, "r", encoding="utf-8") as fh:
        raw = fh.read()
    state = json.loads(raw)
    if not isinstance(state.get("log"), list):
        print("E_APPEND_NO_LOG")
        return 3
    state["tick"] = int(state.get("tick", 0)) + 1
    for line in LINES:
        state["log"].append(line)
    state["last_order"] = "2026-11-12 12:45"
    text = json.dumps(state, indent=1, ensure_ascii=False)
    payload = GWDA.payload_for(STATE, text)
    before = len(raw.encode("utf-8"))
    with io.open(STATE, "wb") as fh:
        fh.write(payload)
    with io.open(STATE, "rb") as fh:
        check = fh.read()
    reread = json.loads(check.decode("utf-8"))
    ok = (len(reread["log"]) == len(state["log"])
          and reread["tick"] == state["tick"]
          and reread["last_order"] == "2026-11-12 12:45")
    print("APPEND tick=%d lines=%d bytes %d -> %d readback=%s"
          % (state["tick"], len(LINES), before, len(check),
             "ok" if ok else "FAILED"))
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main())
