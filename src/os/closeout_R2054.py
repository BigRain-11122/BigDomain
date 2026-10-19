# closeout_R2054.py - R2054 closeout surgery: tick bump, two log
# lines appended to the log tail, DEC row-count baseline refreshed
# (no new tokens this round - content-addressed face was clean), the
# tech.md FIFO head row flipped done and two reseed rows appended.
# Raw-text edits only (no full json rewrite; R1710 layout-drift
# disease), json.loads validates before write-back. Pure ASCII source.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

ROUND = (
    "2026-10-20 R2054 (tech FIFO head claim, R2052 reseed seed 6: funnel "
    "per-sku order totals read face) - five-silence scan: DEC "
    "content-addressed clean (D-20261020-04..07 already judged in the "
    "R2053 baseline; row count 393 -> 396 is layout drift only, baseline "
    "refreshed as auxiliary proof); ledger zero new @BigDomain rows; "
    "group orders tail still 2026-10-20 00:5x = no new orders; tree "
    "clean, no index.lock; benchmarks refreshed today. AC-FST1..AC-FST8 "
    "pre-registered in the tech.md claim row BEFORE the code existed. "
    "Delivered: funnel_daily.py grows sku_totals(day=None) - a pure read "
    "over the append-only orders table grouped by sku into order count "
    "plus summed amount_cent, ascending sku order, the blank sku as its "
    "own bucket, lifetime vs explicit-day window with an honest empty "
    "day, and bad day forms rejecting E_FN_BAD_ARGS before any row is "
    "touched. Suite src/sandbox/funnel/test_funnel_sku.py (pure ASCII) "
    "SUITE 8/8, double-run stdout byte-identical; wiring reconcile_all "
    "SUITES +(\"funnel-sku\", 8) with the criteria count registered "
    "first; full battery RUNNER PASS 263/263 suites green + controls 7/7 "
    "455.1s exit=0 = qa/reconcile-all-R2054.log (262-suite baseline zero "
    "regression after the ASCII fix below); matrix regen 263 suites / "
    "2214 criteria --check byte-identical; census DRIFT-CLEAN flags=0. "
    "Honest note: the first battery run FAILed 260/263 because the new "
    "reconcile_all comment block carried three em-dash bytes (0xe2 0x80 "
    "0x94) - three registry-ASCII suites (pay-notify-revoke, "
    "ledger-apidev-devboard-limit, ledger-apidev-keyviewpersist) abort on "
    "decode('ascii'), the R1888/R1884 hygiene-gate family doing its job; "
    "replaced with ASCII hyphens, all three re-ran green, full battery "
    "re-ran green. Score 2 (runnable artifact: new read face + suite + "
    "battery wiring all green)."
)

TOKENS = (
    "R2054 tokens: local=~610k api=0 api_reason=five-silence scan + sku "
    "totals read face (AC-FST1..8 pre-registered) + suite 8/8 double-run "
    "+ reconcile_all wiring + two full battery runs (first run exposed "
    "the em-dash ASCII violation, fixed, second run green 263/263) + "
    "matrix regen/check + census + export flush, zero cloud calls"
)

RESEED = [
    "- [ ] funnel SKU 单量与金额跨重启持久窗（R2054 补种·查重前置已过："
    "AC-FST7 只证单实例 close/reopen 同读面，三实例级联+新单注入后窗读"
    "冻结的持久化例零例·AC-FSP 前缀全仓 git grep 零占用 2026-10-20·"
    "判据预注册留给认领轮）——面缺口=sku_totals 的 close->reopen 逐面"
    "字节回放+新单注入后旧窗冻结+缺省终身面漂移实证——种子=R2054 守恒"
    "邻位",
    "- [ ] funnel 订单金额 top-N 读数面（R2054 补种·查重前置已过："
    "sku_totals 只作全量分组，单量/金额降序 top-n 榜（并列按 sku 字典序"
    "定序）零例·AC-FTP 前缀全仓 git grep 零占用 2026-10-20·判据预注册"
    "留给认领轮）——面缺口=amount_cent 降序榜（并列按 sku 稳定序+空库"
    "诚实空表+坏 n 形 fail-closed）——种子=R2054 邻位",
]

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

old_tick = '"tick": 2053,'
assert text.count(old_tick) == 1, "tick anchor"
text = text.replace(old_tick, '"tick": 2054,', 1)

old_rows = '"last_decision_rows": 393,'
assert text.count(old_rows) == 1, "rows anchor"
text = text.replace(old_rows, '"last_decision_rows": 396,', 1)

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
assert doc["tick"] == 2054
assert doc["log"][-2] == ROUND
assert doc["log"][-1] == TOKENS

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)

with io.open(TECH, "r", encoding="utf-8", newline="") as f:
    tech = f.read()

assert tech.count("- [ ] funnel 订单 SKU 汇总读数面") == 1, "tech head anchor"
tech = tech.replace("- [ ] funnel 订单 SKU 汇总读数面",
                    "- [x] funnel 订单 SKU 汇总读数面", 1)
done_note = ("［done 2026-10-20 R2054：AC-FST1..AC-FST8 全过·SUITE 8/8 "
             "双跑 stdout 字节同一·RUNNER PASS 263/263 controls 7/7 "
             "455.1s=qa/reconcile-all-R2054.log·matrix 263/2214 "
             "--check byte-identical·census DRIFT-CLEAN·新行注入 "
             "reconcile_all SUITES 判据数先注册；首轮 battery 260/263 "
             "FAIL=注释区三枚 em-dash 字节撞三套 registry-ASCII 卫生闸，"
             "改 ASCII 连字符后全绿（遗障如实记）］")
anchor = "AC-FST1** 空库诚实空表"
pos = tech.find(anchor)
assert pos != -1, "AC block anchor"
line_end = tech.find("\n", pos)
assert line_end != -1, "line end"
tech = tech[:line_end] + done_note + tech[line_end:]

if not tech.endswith("\n"):
    tech += "\n"
tech += "\n".join(RESEED) + "\n"

with io.open(TECH, "w", encoding="utf-8", newline="") as f:
    f.write(tech)

print("STATE-OK disk=%d log_lines=%d tick=%d"
      % (len(text.encode("utf-8")), len(doc["log"]), doc["tick"]))
print("TECH-OK bytes=%d" % len(tech.encode("utf-8")))