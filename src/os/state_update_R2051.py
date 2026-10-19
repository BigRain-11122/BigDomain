# state_update_R2051.py - raw-text surgery for the R2051 closeout
# (tick bump + two log lines appended to the tail of the log array).
# No full json rewrite (R1710 layout-drift disease); json.loads
# validates before write-back. Pure ASCII source.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROUND = (
    "2026-10-20 R2051 (tech FIFO head claim, R2047 reseed seed 3: funnel "
    "late-arrival re-rollup) - five-silence scan clean (DEC 389 tokens / "
    "389 lines flat, ledger zero new @BigDomain rows, orders 22:38 flat, "
    "benchmarks today, tree clean no lock); the P1 board is blocked so the "
    "P2 head was pulled (docker / standing-maintenance / gated seats "
    "skipped). AC-FRL1..FRL8 pre-registered in the tech.md claim row BEFORE "
    "the suite existed. Delivered src/sandbox/funnel/test_funnel_rerollup.py "
    "(pure ASCII): a late lead/order/flow dropped into day D's inbox books "
    "on the re-run (ring2 dispatches it same day, first-round rows "
    "byte-frozen), the re-derived D counts follow and the rollups face "
    "still holds exactly one day row, a second re-run books zero and "
    "reproduces the envelope bytes, the PREV stored envelope stays frozen "
    "while D's delta stays anchored to it key-by-key, the conservation "
    "identity holds after a late spend (60 = 140-80) with day windows "
    "zero-penetrated, a late duplicate id is a no-op on every face, and "
    "the correction propagates into the NEXT day's delta (leads -2 / "
    "granted -125 / spent -50 / outstanding 0) while D stays frozen. Two "
    "honest in-round findings: AC-FRL5 arithmetic was first written as "
    "105/80 against the real 60 (the criteria value is anchored to the "
    "actual run, semantics unchanged); `reconcile_all.py --help` treated "
    "--help as an evidence path and produced a root artifact (571714B "
    "moved byte-preserved to .codely-cli/tmp/, R2046 precedent). Wiring: "
    "reconcile_all SUITES +(\"funnel-rerollup\", 8); full battery RUNNER "
    "PASS 260/260 suites green + controls 7/7 465.7s = "
    "qa/reconcile-all-R2051.log; matrix regen 260 suites/2190 criteria "
    "--check byte-identical; census DRIFT-CLEAN (files=1612 flags=0); "
    "tech open 7->6. Score 2 (runnable artifact + battery wiring)."
)

TOKENS = (
    "R2051 tokens: local=~410k api=0 api_reason=five-silence scan + "
    "funnel late-rerollup suite (AC-FRL1..8 + AC-FRL5 value anchored to "
    "the actual run) + reconcile_all wiring + full battery 260/260 + "
    "matrix regen/check + census + stray --help artifact relocation, "
    "zero cloud calls"
)

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

old_tick = '"tick": 2050,'
assert text.count(old_tick) == 1, "tick anchor"
text = text.replace(old_tick, '"tick": 2051,', 1)

NL = "\r\n" if "\r\n" in text else "\n"
tail = "  ]" + NL + "}" + NL
assert text.endswith(tail), repr(text[-20:])

def jline(s, comma=True):
    return ("        " + json.dumps(s, ensure_ascii=False)
            + ("," if comma else "") + NL)

new_lines = jline(ROUND, True) + jline(TOKENS, False)

# insert before the closing "  ]" of the log array (last element
# keeps its trailing comma from the previous round, so a plain
# insertion works)
idx = text.rindex("  ]" + NL + "}" + NL)
head = text[:idx]
if not head.endswith("," + NL):
    head = head.rstrip("\r\n") + "," + NL
text = head + new_lines + text[idx:]

doc = json.loads(text)
assert doc["tick"] == 2051
assert doc["log"][-2] == ROUND
assert doc["log"][-1] == TOKENS
assert doc["log"][-1].endswith("zero cloud calls")
assert doc["last_order"] == "2026-10-19 22:38"
assert doc["last_decision_rows"] == 390 or doc["last_decision_rows"] == 389

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("STATE-OK disk=%d log_lines=%d tick=%d"
      % (len(text.encode("utf-8")), len(doc["log"]), doc["tick"]))