# state_update_R2053.py - raw-text surgery for the R2053 closeout
# (tick bump + two log lines appended to the tail of the log array +
# the four judged DEC tokens folded into the baseline). No full json
# rewrite (R1710 layout-drift disease); json.loads validates before
# write-back. Pure ASCII source.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROUND = (
    "2026-10-20 R2053 (tech FIFO head claim, R2052 reseed seed 5: funnel "
    "per-account token ledger read face) - five-silence scan: four fresh "
    "DEC tokens D-20261020-04..07 all judged NOT this company's execution "
    "face (FluxVerse / HQ admin / task-health night shift / orders "
    "distillation) - acknowledged no-action, baseline 389 -> 393; ledger "
    "zero new @BigDomain rows; no new orders; tree clean no lock; P1 board "
    "blocked, P2 head pulled with the docker/gated seats skipped. "
    "AC-FAR1..AC-FAR8 pre-registered in the tech.md claim row BEFORE the "
    "code existed. Delivered: funnel_daily.py grows account_ledger(day=None) "
    "- a pure read over the append-only flows table grouped by account "
    "into granted/spent/outstanding, sorted-account order, the blank "
    "account as its own bucket, honest negative overdraft never clamped, "
    "day window vs lifetime vs honest-empty-day law, and bad day forms "
    "rejecting E_FN_BAD_ARGS before any row is touched. Suite "
    "src/sandbox/funnel/test_funnel_account.py (pure ASCII) SUITE 8/8; "
    "wiring reconcile_all SUITES +(\"funnel-account\", 8) with the "
    "criteria count registered first; full battery RUNNER PASS 262/262 "
    "suites green + controls 7/7 343.5s exit=0 = "
    "qa/reconcile-all-R2053.log (261-suite baseline zero regression); "
    "matrix regen 262 suites / 2206 criteria --check byte-identical; "
    "census pass=true. Score 2 (runnable artifact: new read face + suite "
    "+ battery wiring all green)."
)

TOKENS = (
    "R2053 tokens: local=~560k api=0 api_reason=five-silence scan + "
    "account ledger read face (AC-FAR1..8 pre-registered) + suite 8/8 + "
    "reconcile_all wiring + full battery 262/262 + matrix regen/check + "
    "census + export flush, zero cloud calls"
)

NEW_TOKENS = ("D-20261020-04", "D-20261020-05",
              "D-20261020-06", "D-20261020-07")

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

old_tick = '"tick": 2052,'
assert text.count(old_tick) == 1, "tick anchor"
text = text.replace(old_tick, '"tick": 2053,', 1)

old_rows = '"last_decision_rows": 390,'
assert text.count(old_rows) == 1, "rows anchor"
text = text.replace(old_rows, '"last_decision_rows": 393,', 1)

marker = '"last_dec_tokens": "'
start = text.index(marker) + len(marker)
end = text.index('"', start)
baseline = text[start:end]
missing = [t for t in NEW_TOKENS if t not in baseline.split(",")]
assert len(missing) == len(NEW_TOKENS), "baseline already carries tokens"
text = (text[:end] + "," + ",".join(NEW_TOKENS) + text[end:])

NL = "\r\n" if "\r\n" in text else "\n"
tail = "  ]" + NL + "}" + NL
assert text.endswith(tail), repr(text[-20:])


def jline(s, comma=True):
    return ("        " + json.dumps(s, ensure_ascii=False)
            + ("," if comma else "") + NL)


new_lines = jline(ROUND, True) + jline(TOKENS, False)

idx = text.rindex("  ]" + NL + "}" + NL)
head = text[:idx]
if not head.endswith("," + NL):
    head = head.rstrip("\r\n") + "," + NL
text = head + new_lines + text[idx:]

doc = json.loads(text)
assert doc["tick"] == 2053
assert doc["log"][-2] == ROUND
assert doc["log"][-1] == TOKENS
assert doc["last_decision_rows"] == 393
for tok in NEW_TOKENS:
    assert tok in doc["last_dec_tokens"].split(","), tok

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)

print("STATE-OK disk=%d log_lines=%d tick=%d"
      % (len(text.encode("utf-8")), len(doc["log"]), doc["tick"]))