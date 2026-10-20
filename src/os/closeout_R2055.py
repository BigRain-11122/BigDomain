# closeout_R2055.py - state.json closeout + tech queue done flip +
# heartbeat row for the R2055 round. Pure ASCII source; CJK only in
# written data values (state log / queue / heartbeat are UTF-8 data
# faces).
import io
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(HERE, "state.json")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")
HB = os.path.join(ROOT, "heartbeat.txt")

ROUND = (
    "2026-10-20 R2055 (tech FIFO head claim, R2052 reseed seed 7: "
    "funnel dispatch route distribution read face) - five-silence scan: "
    "DEC content-addressed zero new tokens (D-20261020-07 baseline "
    "held, row count 396 unchanged), ledger zero new @BigDomain rows, "
    "no new orders (last_order 2026-10-20 00:5x held), benchmarks "
    "refreshed today, tree clean no index.lock; the P1 board is all "
    "time-gated or externally gated so the P2 FIFO head was pulled "
    "(docker and gated seats skipped). AC-FRT1..AC-FRT8 pre-registered "
    "in the tech.md claim row BEFORE the code existed. Delivered: "
    "funnel_daily.py grows route_tally(day=None) - a pure read over the "
    "append-only dispatches table grouped by route with the dispatch "
    "count, ascending route order, the honest unrouted archive as its "
    "own bucket (never merged into a named route), an unknown route "
    "kept as its own key instead of dropped, lifetime vs explicit-day "
    "window with an honest empty day, idempotent re-dispatch, and bad "
    "day forms rejecting E_FN_BAD_ARGS before any row is touched. Suite "
    "src/sandbox/funnel/test_funnel_route.py (pure ASCII) SUITE 8/8 "
    "first-run green; wiring reconcile_all SUITES + (funnel-route, 8) "
    "with the criteria count registered first; full battery RUNNER PASS "
    "264/264 suites green + controls 7/7 455.1s exit=0 = "
    "qa/reconcile-all-R2055.log (263-suite baseline zero regression); "
    "matrix regen 264 suites / 2222 criteria --check byte-identical; "
    "census pass=true. fold R577 pre-closeout (state gauge 78435B with "
    "a 65B margin, so the two closeout lines would cross the 78500B "
    "line: eol --fix-indent repaired 4 layout anomalies first, then a "
    "tail-4 window folded with token catalog embedded zero-loss, "
    "predicted==actual 74961B, archive + preop backup written). Score 2 "
    "(runnable artifact: new read face + suite + battery wiring all "
    "green)."
)

TOKENS = (
    "R2055 tokens: local=~560k api=0 api_reason=five-silence scan + "
    "route tally read face (AC-FRT1..8 pre-registered) + suite 8/8 + "
    "reconcile_all wiring + full battery 264/264 + matrix regen/check "
    "+ census + fold R577 + export flush, zero cloud calls"
)

with io.open(STATE, "r", encoding="utf-8") as f:
    state = json.load(f)
state["tick"] = 2055
state["log"].append(ROUND)
state["log"].append(TOKENS)
with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    json.dump(state, f, ensure_ascii=False, indent=8)
print("STATE tick=%d log=%d bytes=%d"
      % (state["tick"], len(state["log"]),
         os.path.getsize(STATE)))

raw = io.open(TECH, "rb").read().decode("utf-8")
anchor = "- [ ] funnel \u6d3e\u53d1\u8def\u7531\u5206\u5e03\u8bfb\u6570\u9762"
i = raw.index(anchor)
j = raw.index("\n", i)
line = raw[i:j]
done = (
    line.replace("- [ ]", "- [x]", 1)
    + "\uff08done 2026-10-20 R2055\uff1aAC-FRT1..AC-FRT8 \u5168\u8fc7="
    "\u5957\u4ef6 test_funnel_route.py SUITE 8/8 \u9996\u8dd1\u5168"
    "\u7eff\uff1b\u63a5\u7ebf \"funnel-route\" 8 \u5224\u636e"
    "\uff1b\u5168\u7535\u6c60 RUNNER PASS 264/264 + controls 7/7 "
    "455.1s=qa/reconcile-all-R2055.log\uff1b\u77e9\u9635 264/2222 "
    "--check byte-identical\uff1bcensus pass=true\u2014\u2014"
    "tech \u961f\u5217\u6d88\u8017 1\uff09"
)
raw = raw[:i] + done + raw[j:]
io.open(TECH, "wb").write(raw.encode("utf-8"))
print("TECH done flip ok")

now = datetime.now().astimezone()
stamp = now.strftime("%Y-%m-%d %H:%M")
with io.open(HB, "a", encoding="utf-8", newline="\n") as f:
    f.write(
        "%s +08:00 | BigDomain OSLoop alive | tick 2055 | R2055: tech "
        "FIFO head claim (R2052 reseed seed 7) - funnel dispatch route "
        "distribution read face route_tally(day=None), AC-FRT1..AC-FRT8 "
        "pre-registered before code, suite 8/8 first-run green, wired "
        "into reconcile_all (264 suites / 2222 criteria), RUNNER 264/264 "
        "+ controls 7/7 455.1s, matrix --check byte-identical, census "
        "pass, fold R577 (74961B). Heartbeat rows for ticks 2052-2054 "
        "were never written (lag=3 debt, honestly noted, not "
        "backfilled). [via BigDomain-OSLoop]\n" % stamp
    )
print("HEARTBEAT row appended")