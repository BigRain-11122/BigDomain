# -*- coding: utf-8 -*-
"""R2108 closeout: state.json, queue row flip, backlog row, status export."""

import io
import json
import os

ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

LOG_ROUND = (
    "2026-10-25 R2108 (five-silence scan clean: decisions.md yields zero new "
    "content-addressed tokens against the stored baseline (newest still "
    "D-20261025-04, acknowledged in R2104) while the assistive UTF-8 row "
    "count reads 204; ledger zero new @BigDomain transfer rows; group orders "
    "baseline unchanged at 2026-10-24 12:17; benchmarks refreshed 2026-10-24 "
    "inside 7 days; tree clean, no index.lock; both daily standing rows for "
    "2026-10-25 were already stamped by R2105 so neither was re-run; all four "
    "tech heads stayed gated and the single open explore row stays gated on "
    "the merchant id) - the scan also found that the R2107 api_market_feed "
    "had ZERO product call sites (only its own suite and bookkeeping lines), "
    "the no-consumer idle form again, so this window did not seed a sixth "
    "face: it seeded and claimed the consumer row in the SAME window with "
    "AC-AMAF1..AC-AMAF8 pre-registered BEFORE the code existed (AC-AMAF / "
    "api_market_activity / activity_block / FEED_LIMIT / "
    "test_apimarket_report_activity.py / ledger-apimarket-activity all git "
    "grep -F zero-occupancy anchored 2026-10-25, rc=1) - the public activity "
    "section on the settlement report. Product: apimarket_report.collect() "
    "gains an activity block reading api_market_feed(limit=FEED_LIMIT=40) "
    "fresh on every collect, the page renders a Public activity section "
    "(pinned six columns event_utc/kind/listing/title/detail/value, the value "
    "cell folding amount/units/stars/price into one readable string), "
    "REPORT_SCHEMA moves 2 -> 3 additively (envelope still exactly "
    "schema_version/report/attention, every earlier report key keeps its "
    "value, buyer blocks unchanged), and a legacy report dict without the "
    "key renders the honest empty state. Suite "
    "src/sandbox/ledger/test_apimarket_report_activity.py SUITE PASS 8/8 "
    "double-run criterion lines identical sha16 0d6f12bb569e107b "
    "(qa/apimarket-activity-R2108.log + -2); wired ledger-apimarket-activity "
    "(8); battery RUNNER PASS 313/313 suites plus controls 7/7 in 297.1s "
    "(qa/reconcile-all-R2108.log); matrix 313 suites / 2612 criteria --check "
    "byte-identical; census DRIFT-CLEAN files=1762; preview artifacts "
    "preview/apimarket-report-activity.html (14444B sha256 26d2448d6d14b89d) "
    "and preview/apimarket-report-activity.json (21777B, schema 3). One "
    "honest note: the R2106 suite asserted REPORT_SCHEMA == 2 as a literal, "
    "so the additive bump broke it; that assertion now follows the module "
    "constant while its v2 key sets stay pinned as literals, disclosed in the "
    "suite docstring and in the claim row."
)

LOG_TOKENS = (
    "R2108 tokens: local=~95k api=0 api_reason=five-silence scan + activity "
    "section product change (feed consumer + schema 2->3 additive + HTML "
    "section + value folding) + suite 8/8 double-run + one birth-station "
    "assertion repair + battery 313/313 + matrix regen/check + census + "
    "preview artifacts + state/export closeout, zero cloud calls"
)

DONE_NOTE = (
    u" [done 2026-10-25 R2108] 交付=apimarket_report.py 增 FEED_LIMIT=40 与 "
    u"collect() 的 activity 块（每次采集现读 api_market_feed(tail 最新 N 条)）"
    u"+ HTML Public activity 段（固定六列 event_utc/kind/listing/title/"
    u"detail/value·value 单元把 amount/units/stars/price 折成一格）+ "
    u"REPORT_SCHEMA 2→3 加法升级（信封仍恰三键·旧键逐字节不动·buyer 块键集不变）"
    u"+ 缺键旧 report 降级为诚实空态；套件 SUITE PASS 8/8 双跑判据行同一 "
    u"sha16 0d6f12bb569e107b（qa/apimarket-activity-R2108.log + -2）；接线 "
    u"ledger-apimarket-activity(8)；电池 RUNNER PASS 313/313 suites+controls "
    u"7/7 297.1s=qa/reconcile-all-R2108.log；矩阵 313 suites/2612 criteria "
    u"--check byte-identical；census DRIFT-CLEAN files=1762；呈看件 "
    u"preview/apimarket-report-activity.html（14444B sha256 26d2448d6d14b89d）。"
    u"诚实注=R2106 套件把 REPORT_SCHEMA 写死为 2，本窗加法升级撞红；该断言已改为"
    u"动态对照模块常量（v2 键集仍写死为字面量），在套件与认领行双处留痕。"
)

BACKLOG_ROW = (
    u"- [x] P3 explore 自补种并同窗认领（R2108）：apimarket 结算报告**公共活动流段**"
    u"（activity 接线 + REPORT_SCHEMA 2→3 加法升级）——[done 2026-10-25 R2108]"
    u"（判据 AC-AMAF1..AMAF8 预注册先于代码·六锚零占用 rc=1·套件 8/8 双跑判据行"
    u"同一 sha16 0d6f12bb569e107b=qa/apimarket-activity-R2108.log+-2·电池 RUNNER "
    u"PASS 313/313 suites+controls 7/7 297.1s=qa/reconcile-all-R2108.log·矩阵 "
    u"313/2612 --check byte-identical·census DRIFT-CLEAN files=1762·呈看件 "
    u"preview/apimarket-report-activity.html sha256 26d2448d6d14b89d·详见 "
    u"state/queue/explore.md 同名行）\n"
)


def main():
    # 1. state.json
    p = "src/os/state.json"
    st = json.loads(io.open(p, encoding="utf-8").read())
    st["tick"] = st["tick"] + 1
    st["log"].append(LOG_ROUND)
    st["log"].append(LOG_TOKENS)
    st["last_decision_rows"] = 204
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(st, ensure_ascii=False, indent=1) + "\n")
    print("state tick", st["tick"])

    # 2. queue row: flip to done and append the note
    q = "state/queue/explore.md"
    text = io.open(q, encoding="utf-8").read()
    head = u"- [ ] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2108\uff09\uff1a"
    assert text.startswith(head), "R2108 row not at the queue head"
    rest = text[len(head):]
    nl = rest.index(u"\n")
    row = rest[:nl]
    text = (u"- [x] P3 explore \u81ea\u8865\u79cd\u5e76\u540c\u7a97\u8ba4\u9886\uff08R2108\uff09\uff1a"
            + row + DONE_NOTE + rest[nl:])
    io.open(q, "w", encoding="utf-8", newline="\n").write(text)
    print("queue row flipped")

    # 3. backlog row on top
    b = "src/os/backlog.md"
    btext = io.open(b, encoding="utf-8").read()
    io.open(b, "w", encoding="utf-8", newline="\n").write(
        BACKLOG_ROW + btext)
    print("backlog prepended")

    # 4. status export
    e = "docs/status-export.json"
    doc = json.loads(io.open(e, encoding="utf-8").read())
    doc["export_ts"] = "2026-10-25T02:15:00+08:00"
    doc["ceo_face"]["current"] = (
        u"R2108：结算报告多了「公共活动」一段——R2107 造的活动流此前没有任何产品消费者"
        u"（只有自己的套件），本窗把它接进唯一消费者 apimarket_report：每次采集现读流尾"
        u"最新 40 条，页面在 Attention 之后新增 Public activity 表（时间/事件/挂牌/标题/"
        u"细节/数值六列，数值格把金额、份数、星级、价格折成一格），机读契约 v2→v3 加法"
        u"升级（信封仍恰三键、旧键一字不动），旧报告字典缺键时诚实空态。")
    doc["ceo_face"]["latest_artifact"] = (
        u"preview/apimarket-report-activity.html（14444B·sha256 26d2448d6d14b89d·"
        u"可直接双击打开：市场总账+月度时间线+待办+公共活动流+卖家/买家全表）+ "
        u"preview/apimarket-report-activity.json（21777B·schema 3）+ "
        u"src/sandbox/ledger/apimarket_report.py + "
        u"src/sandbox/ledger/test_apimarket_report_activity.py + "
        u"qa/apimarket-activity-R2108.log（SUITE PASS 8/8·双跑同一 sha16 "
        u"0d6f12bb569e107b）+ qa/reconcile-all-R2108.log（RUNNER PASS 313/313 "
        u"suites + controls 7/7·297.1s）")
    doc["ceo_face"]["next_milestone"] = (
        u"48 小时内：给活动流做「按类聚焦」与「时间窗」两个消费面——"
        u"结算页现在只给全市场最近 40 条，运营者想只看成交/退款/评价三类或"
        u"只看某一天时仍要自己筛（feed 已支持 kinds 与 since/until，缺的是报告侧的"
        u"参数面与第二段表格）；其后是把活动流接进 HTML 的跳转锚（点卖家直接跳到月表），"
        u"让页面从「账本」变成「可追的账本」。两项均不依赖 CEO 物理件。")
    doc["outs"].insert(0, [
        u"apimarket 结算报告公共活动流段（activity 接线 + REPORT_SCHEMA 2→3）",
        "on",
        u"R2108：R2107 的 api_market_feed 此前零产品调用点（只有套件与簿记行），"
        u"本窗把它接进唯一消费者 apimarket_report.collect()——每次采集现读 "
        u"api_market_feed(limit=FEED_LIMIT=40)，HTML 在 Attention 之后新增 Public "
        u"activity 段（固定六列·数值格把 amount/units/stars/price 折成一格·"
        u"shown/total 摘要·无事件诚实空态），机读契约 v2→v3 加法升级（信封仍恰 "
        u"schema_version/report/attention·旧键逐字节不动·buyer 块键集不变·"
        u"缺键旧 report 降级空态）。判据 AC-AMAF1..AC-AMAF8 预注册于代码前（六锚 "
        u"git grep -F 零占用 rc=1）：同源等价+零缓存·加法契约·HTML 面·转义与标识·"
        u"纯读（13 表摘要+ledger_tx 恒定）·双种子逐字节同一·降级·回归+接线。"
        u"套件 8/8 双跑同一 sha16 0d6f12bb569e107b；接线 ledger-apimarket-activity(8)；"
        u"电池 RUNNER PASS 313/313 + controls 7/7 297.1s；矩阵 313/2612 --check "
        u"byte-identical；census DRIFT-CLEAN files=1762；呈看件 "
        u"preview/apimarket-report-activity.html sha256 26d2448d6d14b89d。"
        u"诚实注=R2106 套件曾把 REPORT_SCHEMA 写死为 2，加法升级撞红后改为动态对照"
        u"模块常量（v2 键集仍写死），双处留痕。"])
    doc["results"].insert(0, [
        "R2108",
        "R2108: the report finally consumes the public activity feed. The "
        "R2107 api_market_feed had zero product call sites (only its own "
        "suite and bookkeeping lines) - the no-consumer idle form - so "
        "instead of a sixth face this window wired it into the one consumer: "
        "collect() reads api_market_feed(limit=FEED_LIMIT=40) fresh on every "
        "call, the page renders a Public activity section with six pinned "
        "columns and a value cell folding amount/units/stars/price, and "
        "REPORT_SCHEMA moves 2 -> 3 additively (envelope still exactly "
        "schema_version/report/attention, every earlier key keeps its value, "
        "buyer blocks unchanged, a legacy report dict degrades to the honest "
        "empty state). AC-AMAF1..AC-AMAF8 pre-registered before the code "
        "(six anchors git grep -F zero-occupancy, rc=1); suite 8/8 "
        "double-run criterion lines identical sha16 0d6f12bb569e107b; wired "
        "ledger-apimarket-activity (8); battery RUNNER PASS 313/313 suites "
        "plus controls 7/7 in 297.1s; matrix 313 suites / 2612 criteria "
        "--check byte-identical; census DRIFT-CLEAN files=1762; preview "
        "preview/apimarket-report-activity.html (14444B, sha256 "
        "26d2448d6d14b89d) plus .json (21777B, schema 3). Honest note: the "
        "R2106 suite had REPORT_SCHEMA == 2 as a literal, so the additive "
        "bump broke it; that assertion now follows the module constant while "
        "its v2 key sets stay pinned as literals."])
    sd = doc["self_drive"]
    sd["log_lines_in_window"] = sd.get("log_lines_in_window", 26) + 1
    sd["substantive_non_idle_mention_lines"] = (
        sd.get("substantive_non_idle_mention_lines", 25) + 1)
    sd["queue_explore_open"] = 1
    io.open(e, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("export refreshed", len(doc["outs"]), len(doc["results"]))


if __name__ == "__main__":
    main()