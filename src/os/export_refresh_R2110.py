# -*- coding: utf-8 -*-
"""R2110 export face refresh (indent 1, matching the repo's JSON style)."""
import io
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)


def open_rows(path):
    if not os.path.isfile(path):
        return 0
    return len([l for l in io.open(path, encoding="utf-8").read().splitlines()
                if l.startswith("- [ ]")])


pt = io.open("docs/proposals.md", encoding="utf-8").read().splitlines()
heads = [l for l in pt if l.startswith("### BD-PROP")]
prop_open = len([l for l in heads if re.search(r"状态\s*open", l)])

ep = "docs/status-export.json"
exp = json.loads(io.open(ep, encoding="utf-8").read())
exp["export_ts"] = "2026-10-25T04:20:00+08:00"
exp["ceo_face"]["current"] = (
    "R2110：结算报告多了「买家全史」——买家库（买了什么、还拥有什么）、关注清单、"
    "退款溯源、评分史四张面此前在生产代码里零调用点（与 R2101/R2106/R2108/R2109 "
    "同一种空转形态）；更实的一条：评分史面只收 rating_id，而任何列表级读面都不给 "
    "rating_id（只在卖家待答收件箱里露过），所以那张面事实上不可能被调用。本窗给评分行"
    "加法暴露 rating_id，再把四张面接进报告唯一消费者：每个买家名下新增四张子表"
    "（持有库/关注/退款/评分史），空态诚实呈现；机读契约 v4→v5 加法升级"
    "（信封仍恰三键、旧键一字不动）。")
exp["ceo_face"]["latest_artifact"] = (
    "preview/apimarket-report-buyers.html（24167B·sha256 981a59af8f83823e·"
    "可直接双击打开：市场总账+月度时间线+待办+公共活动+在架清单+挂牌全史档案+"
    "每个买家的持有库/关注/退款/评分史+卖家全表）+ "
    "preview/apimarket-report-buyers.json（38330B·schema 5）+ "
    "src/sandbox/ledger/apimarket_report.py + "
    "qa/apimarket-buyerhistory-R2110.log（SUITE PASS 10/10·双跑判据行同一 "
    "sha16 50999cbdeecb5975）+ qa/reconcile-all-R2110.log"
    "（RUNNER PASS 315/315 suites + controls 7/7·404.5s）")
exp["ceo_face"]["next_milestone"] = (
    "48 小时内：继续把零消费者的读面接进产品面，并给买家全史相机读侧车"
    "（--buyer-history-out，按 buyer_id 给结构化四块，便于自动化比对两次采集）；"
    "商户号未到之前不碰支付对接，本地沙箱与证据链照跑。")
exp["outs"].insert(0, {
    "ts": "2026-10-25T04:20:00+08:00",
    "kind": "product",
    "what": "apimarket report buyer history: library/watchlist/refund/"
            "rating-history faces consumed",
    "artifact": "preview/apimarket-report-buyers.html"})
exp["results"].insert(0, {
    "ts": "2026-10-25T04:20:00+08:00",
    "suite": "test_apimarket_report_buyerhistory.py",
    "verdict": "SUITE PASS 10/10 double-run sha16 50999cbdeecb5975",
    "evidence": "qa/apimarket-buyerhistory-R2110.log"})
sd = exp["self_drive"]
sd["log_lines_in_window"] = 20
sd["proposals_total"] = len(heads)
sd["proposals_open"] = prop_open
sd["queue_tech_open"] = open_rows("state/queue/tech.md")
sd["queue_explore_open"] = open_rows("state/queue/explore.md")
io.open(ep, "w", encoding="utf-8", newline="\n").write(
    json.dumps(exp, ensure_ascii=False, indent=1) + "\n")
print("export refreshed proposals %d/%d tech %d explore %d"
      % (prop_open, len(heads), sd["queue_tech_open"],
         sd["queue_explore_open"]))