# closeout_R2058.py - R2058 closeout surgery: tick bump, two log
# lines appended to the log tail (after the pre-closeout fold R580),
# the DEC row-count auxiliary baseline refreshed to the live count
# (content-addressed token set was clean - zero new tokens), the
# tech.md FIFO head row flipped done with its honest amendment note,
# and one true-live reseed row (the sku type-coercion gap found while
# building the suite). Raw-text edits only (no full json rewrite;
# R1710 layout-drift disease), json.loads validates before write-back.
# Pure ASCII source; CJK lives only in written data values.
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
STATE = os.path.join(ROOT, "src", "os", "state.json")
TECH = os.path.join(ROOT, "state", "queue", "tech.md")

ROUND = (
    "2026-10-20 R2058 (P2 tech-queue FIFO head after skipping the gated "
    "heads: docker-compose needs a docker host, the member refunded "
    "schema window is design-gated, the suite-matrix live-normalized "
    "window awaits a real git-checkout mtime event, the daily profile "
    "window is time-gated to 10-24) - five-silence scan: DEC "
    "content-addressed zero new tokens (212 tokens, baseline held; row "
    "count 315 vs stored 396 = file restructuring drift, auxiliary "
    "baseline refreshed), ledger zero new @BigDomain rows, no new orders "
    "(last_order 2026-10-20 00:5x held), benchmarks refreshed today, "
    "tree clean no index.lock. Claimed the funnel per-sku totals "
    "cross-restart window (R2054 reseed row) with AC-FSP1..AC-FSP8 "
    "pre-registered in tech.md BEFORE the suite existed. Delivered "
    "src/sandbox/funnel/test_funnel_sku_persist.py (pure ASCII, shipped "
    "library untouched): three-instance cascade over a three-day order "
    "world - instance one anchors the lifetime face plus three day "
    "windows plus an honest no-row day; the reopened instance "
    "reproduces all five byte-for-byte; a late day-three batch then "
    "grows the lifetime book (named bucket 3->4 orders / 5980->6480 "
    "cent, blank sku 1->2 / 500->800, the new sku takes its byte-order "
    "slot) while day one and two stay frozen byte-identical; "
    "re-booking the original inbox after the restart is idempotent "
    "(0 new of 3 seen); no-row days stay honest empty at every point; "
    "the read path writes nothing and the restart itself writes "
    "nothing; a second restart keeps the injected state stable with "
    "orders pinned at 9; hygiene is AST-checked (imports, clock face, "
    "shipped config/library sha). Suite SUITE PASS 8/8, double-run "
    "stdout byte-identical sha16 1DFDF3FCECC14343; wiring reconcile_all "
    "SUITES +(\"funnel-sku-persist\", 8) with the criteria count "
    "registered first; full battery RUNNER PASS 267/267 suites green + "
    "controls 7/7 258.5s exit=0 = qa/reconcile-all-R2058.log (266-suite "
    "baseline zero regression); matrix regen 267 suites / 2246 criteria "
    "--check byte-identical; fold R580 pre-closeout (77706B->74296B, "
    "predicted==actual). Honest delivery-time amendment: the AC-FSP3 "
    "criteria text mis-stated the named-bucket order count as 3->5 (the "
    "late batch adds one compute-pack order, so 3->4; the amounts "
    "5980->6480 were right) - criteria text and suite both corrected in "
    "the same window, zero product behaviour change. Honest finding "
    "logged for the queue: book_orders coerces a non-string sku through "
    "str() (int/dict/list land as literal strings) while order_id and "
    "amount are strictly typed - reseeded as a real gap, not fixed this "
    "round. Score 2 (runnable artifact: new cross-restart suite + "
    "battery wiring green)."
)

TOKENS = (
    "R2058 tokens: local=~540k api=0 api_reason=five-silence scan + "
    "gated-head judgement + sku totals cross-restart suite (AC-FSP1..8 "
    "pre-registered, one criteria arithmetic amendment) + reconcile_all "
    "wiring + full battery RUNNER 267/267 + matrix regen/check + fold "
    "R580 + export flush, zero cloud calls"
)

RESEED = (
    "- [ ] funnel book_orders sku 类型门（R2058 认领轮实证发现·非造活："
    "orders 落库前 `str(item.get(\"sku\", \"\"))` 对非字符串 sku 静默强转——"
    "int 5 落为 \"5\"、list/dict 落为字面串，而 order_id/amount 均严格类型门"
    "拒（E_FN_BAD_ARGS 零行）——面缺口=类型门立项裁定（严格拒 vs 显式"
    "字符串化+审计行）+驳回零行律+既有行为保真边界（历史行不动）·"
    "AC-FSK 前缀认领前 git grep 零占用·判据预注册留给认领轮）——"
    "种子=R2058 AC-FSP 窗内代码面实证"
)

with io.open(STATE, "r", encoding="utf-8", newline="") as f:
    text = f.read()

old_tick = '"tick": 2057,'
assert text.count(old_tick) == 1, "tick anchor"
text = text.replace(old_tick, '"tick": 2058,', 1)

old_rows = '"last_decision_rows": 396,'
assert text.count(old_rows) == 1, "rows anchor"
text = text.replace(old_rows, '"last_decision_rows": 315,', 1)

NL = "\r\n" if "\r\n" in text else "\n"
tail = "        ]" + NL + "}"
assert text.endswith(tail), repr(text[-40:])


def jline(s, comma=True):
    return ("                " + json.dumps(s, ensure_ascii=False)
            + ("," if comma else "") + NL)


new_lines = jline(ROUND, True) + jline(TOKENS, False)
idx = text.rindex(tail)
head = text[:idx]
if not head.endswith("," + NL):
    head = head.rstrip("\r\n") + "," + NL
text = head + new_lines + text[idx:]

doc = json.loads(text)
assert doc["tick"] == 2058
assert doc["log"][-2] == ROUND
assert doc["log"][-1] == TOKENS

with io.open(STATE, "w", encoding="utf-8", newline="") as f:
    f.write(text)

with io.open(TECH, "r", encoding="utf-8", newline="") as f:
    tech = f.read()

claim = "- [ ] funnel SKU 单量与金额跨重启持久窗"
assert tech.count(claim) == 1, "tech claim anchor"
tech = tech.replace(claim, "- [x] funnel SKU 单量与金额跨重启持久窗", 1)

done_note = (
    "［done 2026-10-20 R2058：AC-FSP1..AC-FSP8 全过·套件 "
    "test_funnel_sku_persist.py SUITE 8/8·双跑 stdout 逐字节同一 "
    "sha16 1DFDF3FCECC14343·RUNNER PASS 267/267 suites + controls 7/7 "
    "258.5s=qa/reconcile-all-R2058.log·matrix 267/2246 --check "
    "byte-identical·fold R580 前置（77706B->74296B "
    "predicted==actual）·交付期诚实更正=AC-FSP3 判据初稿把命名桶单量"
    "写成 3→5（注入批只加一单 compute-pack·实为 3→4，金额 5980→6480 "
    "无误）——判据文字与套件同窗改正，产品行为零变更·附带实证发现"
    "（book_orders 的 sku str 强转）=另立补种行不并入本窗］"
)
pos = tech.find("- [x] funnel SKU 单量与金额跨重启持久窗")
assert pos != -1
line_end = tech.find("\n", pos)
assert line_end != -1
tech = tech[:line_end] + done_note + tech[line_end:]

if not tech.endswith("\n"):
    tech += "\n"
tech += RESEED + "\n"

with io.open(TECH, "w", encoding="utf-8", newline="") as f:
    f.write(tech)

print("STATE-OK disk=%d log_lines=%d tick=%d"
      % (len(text.encode("utf-8")), len(doc["log"]), doc["tick"]))
print("TECH-OK bytes=%d" % len(tech.encode("utf-8")))