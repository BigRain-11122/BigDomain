"""Closeout writer for the R2241 window: state.json, status-export.json,
heartbeat, the explore queue row flip and the backlog done row.

Writes both JSON files as utf-8 LF in place (no BOM), appending the round
narrative while leaving every earlier log line byte-identical.
"""

import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(BASE, "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
HEART = os.path.join(ROOT, "heartbeat.txt")
QUEUE = os.path.join(ROOT, "state", "queue", "explore.md")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
DECISIONS = os.path.join(os.path.dirname(ROOT), "..", "docs",
                         "decisions.md")

ROUND = "R2241"

NARRATIVE = (
    "2026-10-29 R2241 (five-silence scan clean at open: decisions.md "
    "carries 283 non-empty rows and a content-addressed diff of 190 "
    "D/C/O/T/P/XL tokens whose only seven apparent additions are the "
    "known group-side rotation artefacts (D-20261006-05, D-20261007-04, "
    "D-20261007-05, D-20261008-05) plus three truncation variants of "
    "T-20261026-01..03, so zero genuinely new rows and zero domain "
    "action, and the baseline is re-anchored to the measured set; the "
    "group ledger carries the same three @BigDomain patrol rows already "
    "paid off with zero unreplied; the own-orders baseline is unchanged "
    "at the 2026-10-29 02:1x CEO-PROXY fleet event round R2.48 already "
    "consumed in R2226; benchmarks refreshed 2026-10-29 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, "
    "all four tech heads stayed gated (docker host absent, the logs "
    "toolkit in standing maintenance, the member refunded schema "
    "product-gated, the live-mtime row waiting on a real "
    "normalized-mtime event), so this window claimed the explore head, "
    "seed a of the R2240 family. Anchor check at HEAD 2026-10-29: the "
    "AC-SWCV prefix, test_apimarket_sellerwatchconversionmonths and "
    "ledger-apimarket-sellerwatchconversionmonths were git grep -F "
    "zero-occupancy rc=1 (the face name itself appeared only in the seed "
    "row text and src/os/seed_queue_R2240.py). Criteria AC-SWCV1..AC-SWCV8 "
    "were written into that queue row BEFORE the code. Gap: "
    "api_market_conversion_months answers the whole market on a month "
    "axis, api_category_watch_conversion_months one category and "
    "api_watch_conversion one listing over its lifetime, so a seller "
    "holding N shelves could not read whether its OWN attention converted "
    "month over month - a shop whose watchers stopped buying in March "
    "read exactly like one whose watchers never bought. Product: "
    "APIMarketFace.api_seller_watch_conversion_months(dev_account=None) - "
    "a twenty-key envelope with fourteen-key month rows. Booking law: a "
    "watch books only in the UTC month of its own watched_utc, an unwatch "
    "is not an event for this face (the withdrawn watch keeps its month "
    "and the unwatch month gains no weight), and a purchase never "
    "re-dates the month. Directional law shared with the two sibling "
    "faces: converted when the unrefunded purchase is stamped at or after "
    "the watch stamp (equal stamps at zero seconds), pre_owned when the "
    "purchase predates the watch and is excluded from the funnel, "
    "pending when there is no purchase or the purchase was refunded, so "
    "one later refund cancels a conversion without moving a month key; "
    "the three legs conserve per row and in the envelope. Rate and "
    "latency: conversion_rate is converted over funnel, None on an empty "
    "funnel and never a fabricated zero; the average is pooled over "
    "converted watches, the median takes the middle value or the midpoint "
    "for an even count, and all four latency fields are None when nothing "
    "converted. The grid is contiguous from the first to the last watch "
    "month so a month with no watch carries an honest zero row. "
    "Benchmark: the market scope publishes no self-benchmark (None on "
    "rows and envelope) while a seller scope carries the TRUE market rate "
    "of every month on its rows plus the pooled market rate in the "
    "envelope. Strict seller isolation: the two seller envelopes "
    "partition the market on all four counts (2+4 watches, 1+1 converted, "
    "0+1 pre_owned, 1+2 pending), and a prefix-valid unknown seller "
    "reads an honest empty envelope rather than the market. Evidence: "
    "SUITE PASS 8/8 on both legs with byte-identical bodies "
    "(qa/apimarket-sellerwatchconversionmonths-R2241-a.log and -b.log, "
    "617 bytes each, utf-8 LF written by src/os/evidence_R2241.py, never "
    "a shell redirection), criterion lines sha16 774347968EA72ECE; wired "
    "as ledger-apimarket-sellerwatchconversionmonths(8) in "
    "reconcile_all.py; six adjacent watch/conversion suites green "
    "(qa/regression-R2241.log, 5379 bytes, fails=0); PRODUCT_SHA_STABLE "
    "True. Honest debt: the full reconcile battery and the suite-matrix "
    "regeneration were NOT run in this 25-minute window (the R2168 "
    "mixed-tree rule) and are the R2242 first item; both queues still sit "
    "below the self-drive floors after this claim (tech 8, explore 6 "
    "against >=10/>=10), so the next window must seed real gaps rather "
    "than manufacture rows; and BigDomain-OSLoop still reads "
    "LogonType=InteractiveToken, which needs an elevated shell (eleventh "
    "consecutive disclosure).")

TOKENS = (
    "R2241 tokens: local=~30k api=0 api_reason=product window on one "
    "explore seed - a zero-occupancy anchor check, one new seller "
    "watch-conversion month face plus its eight-criterion suite that "
    "passed 8/8 on the first run, one single-writer double-run evidence "
    "pair, six adjacent regressions, and the queue/backlog/state/export "
    "closeout; zero cloud calls and zero external API touches; the full "
    "battery and the matrix regeneration are deferred and recorded")

SELFHEAL = (
    "R2241 self-heal check: BigDomain-OSLoop exists and is Running, but "
    "its principal still reads LogonType=InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task. "
    "src/os/register_loop_task.ps1 already passes an explicit S4U "
    "principal and needs an elevated shell to apply it; this session runs "
    "unelevated, so the definition of the loop hosting this window was "
    "left untouched. Open local-lane item for an elevated window "
    "(eleventh consecutive disclosure).")

CURRENT = (
    "R2241 产品轮：卖家侧「我的关注有没有变成成交」这一面落地 - "
    "api_seller_watch_conversion_months 把每个关注按自己的 UTC 月入桶"
    "（取关不算事件、成交不重写月份），三腿转成/先买后关/挂起逐行守恒，"
    "连续网格带诚实零月（二月无关注，改价与取关都不算），"
    "dana 2 关注 1 成交（0.5）、lia 4 关注 1 先买 1 成交 2 挂起（1/3）、"
    "全市场 6 关注 2 成交（0.4）；卖家行的 market_conversion_rate 列出当月"
    "真实市场转化率（一月 0.5 / 三月 0.5 / 四月 0.0 / 二月诚实 None），"
    "市场视角自身不给自己挂基准；两卖家计数之和恰等于市场、未知卖家诚实空。"
    "判据 AC-SWCV1..8 全部通过。")

ARTIFACT = (
    "qa/apimarket-sellerwatchconversionmonths-R2241-a.log 与 -b.log"
    "（各 617 字节，双跑逐字节同一，判据行 sha16 774347968EA72ECE） + "
    "src/sandbox/ledger/apimarket.py 新面 + qa/regression-R2241.log"
    "（相邻六套件 fails=0）；时间戳 2026-10-29 08:5x")

NEXT = (
    "R2242（48 小时内）：补跑全量对账电池与套件矩阵再生（本轮因 25 分钟"
    "预算未跑，记录在案）；并把 tech 8/10、explore 6/10 的队列地板欠账"
    "用真实缺口补齐；另有一项悬挂的本地事项=BigDomain-OSLoop 仍是 "
    "InteractiveToken，需提权窗改 S4U")

OUT_ROW = [
    "seller-scoped monthly watch-to-purchase conversion face (R2241)",
    "on",
    ("api_seller_watch_conversion_months(dev_account=None): twenty-key "
     "envelope, fourteen-key month rows; the watch-month cohort law with "
     "an unwatch proven not to be an event (dana keeps 2 watches across a "
     "February unwatch and the February row stays an honest zero); the "
     "three legs (converted at or after the watch stamp incl. equal "
     "stamps at zero seconds, pre_owned excluded from the funnel, pending "
     "that also absorbs a refunded purchase) conserving per row and in "
     "the envelope; contiguous grid with None rate and None latencies on "
     "the zero month; strict isolation partitioning the market (2+4 "
     "watches, 1+1 converted, 0+1 pre_owned, 1+2 pending); the monthly "
     "market benchmark column a seller reads against (0.5 / None / 0.5 / "
     "0.0 with 0.4 pooled) while the market scope carries none of its "
     "own; identity with api_market_conversion_months on all ten shared "
     "keys and the month grid, and with api_seller_watch_months per "
     "seller; seven-form usr: gate failing closed before any read with "
     "frozen digests and a constant ledger_tx set. Evidence: SUITE 8/8 "
     "double-run byte-identical criterion sha16 774347968EA72ECE (617B "
     "per leg, utf-8 LF by src/os/evidence_R2241.py), wired "
     "ledger-apimarket-sellerwatchconversionmonths(8), six adjacent "
     "suites green (qa/regression-R2241.log, fails=0).")]

RESULT_ROW = [
    "R2241",
    ("product window on the explore head seed R2240 a: "
     "api_seller_watch_conversion_months closes the seller-scope gap - "
     "SUITE 8/8 on the first run, double-run byte-identical (617B per "
     "leg, criterion sha16 774347968EA72ECE, single-writer utf-8 LF), six "
     "adjacent watch/conversion suites green, PRODUCT_SHA_STABLE True; "
     "honest debt = the full battery and the matrix regeneration deferred "
     "to R2242, both queues still under the standing floor (tech 8, "
     "explore 6), and the loop task still needs an elevated S4U "
     "re-registration.")]


def _dump(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    if not text.endswith("\n"):
        text += "\n"
    with open(path, "wb") as handle:
        handle.write(text.encode("utf-8"))
    return len(text.encode("utf-8"))


def _open_counts(path):
    with io.open(path, encoding="utf-8") as handle:
        body = handle.read()
    return len(re.findall(r"(?m)^- \[ \] ", body))


def _measured_tokens():
    with io.open(DECISIONS, encoding="utf-8") as handle:
        body = handle.read()
    toks = sorted(set(re.findall(
        r"(?:D|C|O|T|P|XL)-\d{8}-\d{2,4}", body)))
    return toks


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = int(state.get("tick", 0)) + 1
    state["last_decision_rows"] = 283
    toks = _measured_tokens()
    state["last_dec_tokens"] = ",".join(toks)
    state["log"].extend([NARRATIVE, TOKENS, SELFHEAL])
    size_state = _dump(STATE, state)

    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    export["export_ts"] = "2026-10-29T08:58:00+08:00"
    export["do"] = ("product window R2241: the seller-scope "
                    "watch-to-purchase conversion face lands, so a shop "
                    "can finally read whether its own watchers turned "
                    "into buyers month over month")
    export["ceo_face"]["current"] = CURRENT
    export["ceo_face"]["latest_artifact"] = ARTIFACT
    export["ceo_face"]["next_milestone"] = NEXT
    export["outs"].insert(0, OUT_ROW)
    export["results"].insert(0, RESULT_ROW)
    sd = export.get("self_drive", {})
    sd["window"] = "2026-10-23..2026-10-29"
    sd["queue_tech_open"] = _open_counts(
        os.path.join(ROOT, "state", "queue", "tech.md"))
    sd["queue_explore_open"] = _open_counts(QUEUE)
    export["self_drive"] = sd
    size_export = _dump(EXPORT, export)

    with open(HEART, "ab") as handle:
        handle.write(("2241 tick 2026-10-29 R2241 product window: "
                      "api_seller_watch_conversion_months (explore R2240 "
                      "a) - suite 8/8 double-run; battery + matrix "
                      "regeneration carried to R2242\n").encode("utf-8"))

    with io.open(QUEUE, encoding="utf-8") as handle:
        queue = handle.read()
    queue = queue.replace(
        "- [ ] P3 explore seed (R2240 a) CLAIMED R2241, criteria",
        "- [x] [done 2026-10-29 R2241] P3 explore seed (R2240 a), "
        "criteria", 1)
    with open(QUEUE, "wb") as handle:
        handle.write(queue.encode("utf-8"))

    with io.open(BACKLOG, encoding="utf-8") as handle:
        backlog = handle.read()
    row = ("- [x] [done 2026-10-29 R2241] P3 explore head claim (R2240 "
           "seed a, criteria AC-SWCV1..AC-SWCV8 registered in that queue "
           "row BEFORE the code; anchor check at HEAD 2026-10-29: the "
           "AC-SWCV prefix, "
           "test_apimarket_sellerwatchconversionmonths and "
           "ledger-apimarket-sellerwatchconversionmonths were git grep -F "
           "zero-occupancy rc=1): apimarket **seller-scoped monthly "
           "watch-to-purchase conversion** "
           "(api_seller_watch_conversion_months). Gap: the market, "
           "category and lifetime-listing conversion faces existed, so a "
           "single seller could not read whether its own attention "
           "converted month over month. Product: twenty-key envelope, "
           "fourteen-key month rows; the watch-month cohort law with an "
           "unwatch proven not to be an event; the three legs conserving "
           "per row and in the envelope; the contiguous grid with an "
           "honest zero month reading None rate and None latencies; "
           "strict isolation partitioning the market 2+4 / 1+1 / 0+1 / "
           "1+2; the monthly market benchmark column (0.5 / None / 0.5 / "
           "0.0, pooled 0.4) that the market scope itself never carries; "
           "identity with api_market_conversion_months on ten shared keys "
           "and the grid plus api_seller_watch_months per seller; "
           "seven-form usr: gate failing closed before any read with "
           "frozen digests and a constant ledger_tx set. Evidence: SUITE "
           "PASS 8/8 double-run byte-identical (qa/"
           "apimarket-sellerwatchconversionmonths-R2241-a.log and -b.log, "
           "617B each, criterion sha16 774347968EA72ECE, single writer "
           "utf-8 LF by src/os/evidence_R2241.py), wired "
           "ledger-apimarket-sellerwatchconversionmonths(8), six adjacent "
           "suites green (qa/regression-R2241.log, fails=0). Honest "
           "debt: the full reconcile battery and the suite-matrix "
           "regeneration are the R2242 first item; both queues still sit "
           "below the standing floors (tech 8, explore 6).\n")
    marker = "- [x] [done 2026-10-29 R2240] P3 explore head claim"
    if marker in backlog:
        backlog = backlog.replace(marker, row + marker, 1)
    else:
        backlog = row + backlog
    with open(BACKLOG, "wb") as handle:
        handle.write(backlog.encode("utf-8"))

    print("STATE bytes=%d tick=%d lines=%d tokens=%d"
          % (size_state, state["tick"], len(state["log"]), len(toks)))
    print("EXPORT bytes=%d outs=%d results=%d tech=%d explore=%d"
          % (size_export, len(export["outs"]), len(export["results"]),
             sd["queue_tech_open"], sd["queue_explore_open"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())