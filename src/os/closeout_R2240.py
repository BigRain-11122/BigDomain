"""R2240 closeout: state log, tick and the CEO-visible export face.

Product window: the explore seed 6/6 face api_seller_price_demand_months
plus its 8/8 double-run evidence pair. Writes only the fields this
window owns; every other key is read back and rewritten untouched.
"""

import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))

ROUND = (
    "2026-10-29 R2240 (five-silence scan clean at open: decisions.md "
    "carries 283 non-empty rows and a content-addressed token diff of "
    "183 D/C/O/T/P/XL tokens that EQUALS the stored baseline exactly - "
    "zero new and zero gone - so zero domain action; the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with "
    "zero unreplied; the group orders tail is unchanged at the "
    "2026-10-29 02:1x CEO-PROXY fleet event round R2.48 already consumed "
    "in R2226; benchmarks refreshed 2026-10-29 inside the seven-day gate; "
    "tree clean, no index.lock) - the P1 canonical rows stay blocked-on-CEO "
    "and all four tech heads stayed gated (docker host absent, the logs "
    "toolkit in standing maintenance, the member refunded schema "
    "product-gated, the live-mtime row waiting on a real normalized-mtime "
    "event), so this window claimed the explore head, seed 6/6 of the "
    "R2230 family. Anchor check at HEAD 2026-10-29: the AC-SPD prefix, "
    "api_seller_price_demand_months, "
    "test_apimarket_sellerpricedemandmonths, "
    "ledger-apimarket-sellerpricedemandmonths, response_month_count and "
    "market_response_rate were git grep -F zero-occupancy rc=1 (the only "
    "AC-SPD text hit was the R2230 closeout seed description). Criteria "
    "AC-SPD1..AC-SPD8 were written into that queue row BEFORE the code. "
    "Gap: api_seller_price_cadence_months answers how often a seller "
    "reprices, api_seller_watch_months how much attention arrived and "
    "api_seller_question_months how many pre-sale questions came in, so "
    "'when interest rose, did I actually move the price' had no face. "
    "Product: APIMarketFace.api_seller_price_demand_months(dev_account="
    "None) - a twenty-two-key envelope with ten-key month rows, all "
    "derived from revisions x watchlist x unwatchings x questions x "
    "listings with zero new tables. The join law books each leg in the "
    "UTC month of its own immutable stamp (a revision in revised_utc, a "
    "watch in watched_utc, an unwatch in unwatched_utc, a question in "
    "asked_utc), an answer is not an event and an earlier month is frozen. "
    "The response law needs a revision AND demand for a response month and "
    "a positive watch delta or a question for a demand month, so "
    "November's two revisions against a net-zero watch delta is honestly "
    "NOT a demand month while December's question with no revision is a "
    "non-response month - market 1/2 = 0.5, dana 1/1 = 1.0, lia 0/1 = 0.0, "
    "gina 0/1 = 0.0, and an empty world answers None instead of a "
    "fabricated 0.0. The grid is the UNION of the four event families "
    "(OCT..DEC) with nets [0,0,0], watch_nets [1,0,0] and running [2,4,4] "
    "landing on the envelope total. Seller isolation is strict and the "
    "four legs partition the market totals (1+1+2 revisions, 1+1+0 "
    "watches, 1+0+0 unwatches, 1+0+1 questions). The market benchmark "
    "never measures itself (None on the market scope, 0.5 on every seller "
    "scope) and the peak tie-break goes to the earlier month (October 2 "
    "beats November 2). Cross-face identity holds against "
    "api_seller_price_cadence_months, api_seller_watch_months, "
    "api_seller_question_months and api_market_question_months, including "
    "the cadence window month rows. Evidence: SUITE PASS 8/8 double-run "
    "byte-identical (qa/apimarket-sellerpricedemandmonths-R2240-a.log and "
    "-b.log, 869B each, sha256 "
    "9f8fcd66b6e836c6b96d53ddd11e25a31b94b2a7fce3eca77c1375f9b1fe6bab, "
    "CRLF=0, no BOM, single writer utf-8 LF through "
    "src/os/evidence_R2240.py, never a shell redirection), wired "
    "ledger-apimarket-sellerpricedemandmonths(8), four adjacent suites "
    "green 8/8 each (qa/regression-R2240.log). Honest note: the first run "
    "was 8/8; the one correction was a test-side reference to the market "
    "question face key (asked_count -> question_count, a pre-registration "
    "erratum corrected into the queue row before any evidence landed, "
    "product code unchanged). Queue floor debt: the carried R2239 row "
    "demanded seeding to the self-drive floors (tech >= 10, explore >= 10); "
    "six real explore gaps and four real tech gaps were seeded through "
    "src/os/seed_queue_R2240.py, which leaves the OPEN counts at explore 7 "
    "and tech 8 against the floors - still short, disclosed rather than "
    "padded to the number.")

TOKENS = (
    "R2240 tokens: local=~45k api=0 api_reason=product window on one "
    "explore seed - a zero-occupancy anchor check, one new seller price-"
    "demand month face plus its eight-criterion suite that passed 8/8 on "
    "the first run, one single-writer double-run evidence pair, four "
    "adjacent regressions, a queue-floor seeding script, the pre-"
    "registration erratum repair, and the state/export/backlog closeout; "
    "zero cloud calls and zero external API touches; the full battery and "
    "the matrix regeneration are deferred and recorded")

SELF_HEAL = (
    "R2240 self-heal check: BigDomain-OSLoop exists and is Running, but "
    "its principal still reads LogonType=InteractiveToken, which the "
    "2026-09-29 machine law forbids for every lane task. "
    "src/os/register_loop_task.ps1 already passes an explicit S4U "
    "principal and needs an elevated shell to apply it; this session runs "
    "unelevated, so the definition of the loop hosting this window was "
    "left untouched. Open local-lane item for an elevated window (tenth "
    "consecutive disclosure).")


def main():
    state_path = os.path.join(BASE, "state.json")
    state = json.load(io.open(state_path, encoding="utf-8"))
    state["tick"] = int(state.get("tick", 0)) + 1
    state.setdefault("log", []).extend([ROUND, TOKENS, SELF_HEAL])
    with io.open(state_path, "w", encoding="utf-8", newline="\n") as h:
        json.dump(state, h, indent=2, ensure_ascii=False)
        h.write("\n")

    export_path = os.path.join(ROOT, "docs", "status-export.json")
    export = json.load(io.open(export_path, encoding="utf-8"))
    export["export_ts"] = "2026-10-29T08:2x+08:00"
    export["do"] = (
        "product window R2240: the last seed of the R2230 family ships as "
        "api_seller_price_demand_months, joining the repricing, watch and "
        "question month axes so a seller can read whether it moved the "
        "price when demand arrived")
    export["ceo_face"] = {
        "current": (
            "R2240 产品轮：卖家「改价是否跟着需求走」这一面落地——"
            "api_seller_price_demand_months 把改价、关注、取关、提问四腿按各自 UTC 月"
            "并入一张连续网格（OCT..DEC），响应月=有改价且有需求、需求月=净关注>0 或有提问，"
            "市场 0.5 / dana 1.0 / lia 0.0 / gina 0.0；净关注为 0 的十一月即使有两次改价"
            "也诚实记为非需求月，十二月有提问无改价记为非响应月；卖家隔离与四腿分账守恒，"
            "市场基准不自比，峰值并列取较早月。判据 AC-SPD1..8 全部通过。"),
        "latest_artifact": (
            "qa/apimarket-sellerpricedemandmonths-R2240-a.log 与 -b.log"
            "（各 869 字节，双跑逐字节同一，sha256 9f8fcd66b6e836c6b96d53ddd11e25a31b94b2a7fce3eca77c1375f9b1fe6bab）"
            " + src/sandbox/ledger/apimarket.py 新面"
            " + qa/regression-R2240.log（相邻四套件 8/8×4）；时间戳 2026-10-29 08:2x"),
        "next_milestone": (
            "R2241（48 小时内）：补跑全量对账电池与套件矩阵再生（本轮因 25 分钟预算未跑，"
            "记录在案）；并把 explore 7/10、tech 8/10 的队列地板欠账继续用真实缺口补齐；"
            "另有一项悬挂的本地事项=BigDomain-OSLoop 仍是 InteractiveToken，需提权窗改 S4U"),
    }
    with io.open(export_path, "w", encoding="utf-8", newline="\n") as h:
        json.dump(export, h, indent=2, ensure_ascii=False)
        h.write("\n")
    print("state tick=%d log=%d export_ts=%s"
          % (state["tick"], len(state["log"]), export["export_ts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())