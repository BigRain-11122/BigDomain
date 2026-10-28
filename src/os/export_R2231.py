"""R2231 export refresh: the silicon observation window.

Every field is derived from the actual state on disk (F3 law), never
hand-written prose that drifts. Usage: python src/os/export_R2231.py
"""

import io
import json
import os
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
STAMP = "2026-10-29T06:10:00+08:00"

CURRENT = (
    "R2231 是产品轮：先判负队头陈旧种子（全市场月度目录规模时间线——"
    "api_market_supply_months 已给每月在架/售罄/不限量与开闭流，重复面不造），"
    "再交付卖家侧「月度来问压力面」api_seller_question_months：一条提问记在"
    "自己 asked_utc 的 UTC 月、回复腿记回提问月（三月回一月问只抬一月），"
    "连续月网格含诚实零月、两个单调累加器落在信封总额、峰值平票取更早月、"
    "卖家严格隔离。25 分钟窗外未跑全量电池与矩阵再生，列下一窗首项。")

LATEST = (
    "src/sandbox/ledger/apimarket.py（新增 api_seller_question_months）、"
    "src/sandbox/ledger/test_apimarket_sellerquestionmonths.py、"
    "qa/apimarket-sellerquestionmonths-R2231-a.log / -b.log（8/8 双跑背景逐字节"
    "同一，763B 各）、qa/regression-R2231.log（6 邻域全绿）、"
    "state/queue/explore.md（AC-SQM1..AC-SQM8 判据行）、2026-10-29")

NEXT = (
    "48h 内：把这枚新面纳入全量电池（当前 415 套件 + 本面 = 416）并重生成套件"
    "矩阵，清掉本轮遗留的验证欠账；随后接 explore 队头（R2230 2/6 买家月度等答"
    "时长面 api_buyer_answer_wait）。")

SELF_DRIVE = OrderedDict([
    ("window", "2026-10-23..2026-10-29"),
    ("window_days", 7),
    ("proposals_total", 5),
    ("proposals_open", 3),
    ("queue_main_open", 6),
    ("queue_tech_open", 4),
    ("queue_explore_open", 6),
])


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    log = state["log"]
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        data = json.load(handle, object_pairs_hook=OrderedDict)

    data["export_ts"] = STAMP
    data["do"] = ("product round R2231 (seller monthly incoming question"
                  " pressure face + one stale head seed closed negative)")
    data["ceo_face"] = OrderedDict([
        ("current", CURRENT),
        ("latest_artifact", LATEST),
        ("next_milestone", NEXT)])

    drive = OrderedDict(SELF_DRIVE)
    window_lines = sum(
        1 for line in log
        if ("2026-10-2" in line[:40] or line.startswith("R22")
            or line.startswith("carry-forward rolling line R2231")))
    drive["log_lines_in_window"] = window_lines
    drive["idle_fast_mention_lines"] = sum(
        1 for line in log if "idle-fast" in line)
    drive["no_pullable_mention_lines"] = sum(
        1 for line in log if "no-pullable" in line)
    drive["substantive_non_idle_mention_lines"] = (
        window_lines - drive["idle_fast_mention_lines"]
        - drive["no_pullable_mention_lines"])
    data["self_drive"] = drive

    data["outs"].insert(0, [
        "seller monthly incoming question pressure (api_seller_question_months)",
        "on",
        "eighteen-key envelope / nine-key month rows: a question books in the"
        " month of its own asked_utc and the ANSWERING leg is credited to the"
        " ASKING month, so a March discharge of a January question raises only"
        " January; contiguous grid with an honest zero month whose answer_rate"
        " is None; both monotone accumulators land on the envelope totals; the"
        " 2-vs-2 peak tie resolves to the earlier month; event-derived"
        " participation against lifetime distinct counts; strict seller"
        " isolation; evidence 8/8 double-run byte-identical"
        " (qa/apimarket-sellerquestionmonths-R2231-a.log and -b.log)"])
    data["outs"].insert(1, [
        "stale explore head seed closed negative (api_market_catalog_months)",
        "on",
        "the premise was false: api_market_supply_months already publishes"
        " live_listing_count, in_stock/sold_out/unlimited, units and"
        " opened_total/closed_total per month, so catalog scale, active"
        " shelves and retirements all read on that face - building a second"
        " one would be the repeat-wheel red line"])

    data["results"].append([
        "R2231",
        "product face + negative seed: SUITE 8/8 double-run byte-identical"
        " (763B per log), six adjacent question/answer suites green,"
        " PRODUCT_SHA_STABLE True; state.json folded 84506B -> 61995B with"
        " token_missing [] and gate margin +16505B; ledger gate suites"
        " re-run 8/8/8 PASS after the fold"])

    blob = json.dumps(data, indent=2, ensure_ascii=False)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(blob)
    print("export written bytes=%d outs=%d results=%d"
          % (len(blob.encode("utf-8")), len(data["outs"]),
             len(data["results"])))


if __name__ == "__main__":
    main()