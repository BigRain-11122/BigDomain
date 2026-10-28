"""R2181 closeout: state.json tick/log/watermark, backlog done marker,
and the status-export refresh (all derived, nothing hard-coded beyond
the round facts this script was written for).
"""

import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GROUP = os.path.abspath(os.path.join(BASE, "..", ".."))

ROUND_LINE = (
    "R2181 (five-silence scan clean at open: the group ledger carries "
    "the same three @BigDomain patrol rows with zero unreplied; "
    "decisions.md carries 163 content-addressed D/C tokens, four above "
    "the stored baseline - D-20261006-05, D-20261007-04, D-20261007-05, "
    "D-20261008-05 - and every one of them is a citation inside another "
    "company's decision row (BigMoney x3, CPH4 Labs x1, BigStream x1), "
    "so zero domain action and the baseline is re-anchored to 163; the "
    "group orders tail is unchanged at the 2026-10-28 03:0x CEO-PROXY "
    "event round #4; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
    "stay blocked-on-CEO and all four tech heads stayed gated, so this "
    "window took the next explore seed (R2178 3/10) and shipped the "
    "seller-cohort face. Gap statement: the buyer side carries a cohort "
    "face and a retention matrix while the seller side had only a "
    "lifetime view (api_repeat_purchase) and a running total "
    "(dev_sales_board), so 'are the sellers who listed in January still "
    "listing in March' had no reading at all. Product: "
    "APIMarketFace.api_market_seller_cohort() - a twelve-key envelope "
    "with nine-key rows built from exactly two stored event sources "
    "(one event per apimarket_listings row at listed_utc, one per "
    "apimarket_relistings row at relisted_utc, no wall clock and no "
    "derived cycle table), the cohort law (a seller is new exactly once, "
    "in the earliest month across the whole history, including a "
    "re-listing whose stamp is EARLIER than the listing stamp - "
    "disclosed and never clamped), the repeat-seller law with a "
    "zero-denominator None, a re-listing subset that can never exceed "
    "the event count, no zero rows for empty months, retirement and "
    "sold-out explicitly not being events, a pure read with frozen table "
    "digests and a constant ledger_tx set, and byte identity across four "
    "post-restart instances. Evidence: SUITE PASS 8/8 double-run "
    "byte-identical criterion sha256 "
    "57a23d5d943bea5d8b5a1f5f49f7c3c00d8415da137ceb4ff97b15fa45873465 "
    "(qa/apimarket-sellercohort-R2181-a.log and -b.log, 788 bytes each, "
    "written through the python single writer as utf-8 LF); wired as "
    "ledger-apimarket-sellercohort(8); the full battery and suite-matrix "
    "regeneration that R2180 deferred were launched against this final "
    "tree (qa/reconcile-all-R2181.log, launcher PID in "
    "logs/battery-R2181.out) and their outcome is reported honestly in "
    "the next round's first line rather than claimed here. Honest notes: "
    "(a) the first run failed AC-MSC3 on my own fixture arithmetic - I "
    "had counted a seller in March whose second listing actually landed "
    "in February - and the expectation was corrected to the true event "
    "stream with no criterion relaxed; (b) the same run also exposed two "
    "missing listing_id subscripts in the fixture, fixed before any "
    "criterion went green; (c) the suite was wired into reconcile_all "
    "only after the first green run, so that run read wired=False and the "
    "wiring was added rather than the criterion relaxed."
)

TOKEN_LINE = (
    "R2181 tokens: local=~85k api=0 api_reason=five-silence scan + "
    "explore seed 3/10 claim with criteria pre-registered before code + "
    "seller-cohort product face + suite 8/8 double-run byte-identical + "
    "runner wiring + the deferred full battery and matrix regeneration "
    "launched on the final tree + state/backlog/export closeout, zero "
    "cloud calls"
)

DONE_NOTE = (
    "[done 2026-10-28 R2181] 产品=apimarket.py `api_market_seller_cohort()`"
    "（十二键信封/九键行·两个存储事件源合成·队列月=全史最早事件月含倒签复挂·"
    "复挂子集≤事件数·零事件月不造零行·退役与售罄不是事件·纯读冻结表摘要）·"
    "套件 src/sandbox/ledger/test_apimarket_sellercohort.py 双跑 rc=0/0 判据行"
    "逐字节同一 sha256 57a23d5d943bea5d8b5a1f5f49f7c3c00d8415da137ceb4ff97b15fa45873465"
    "（qa/apimarket-sellercohort-R2181-a.log + -b.log 各 788B）·接线 "
    "ledger-apimarket-sellercohort(8)·电池与矩阵重生成已对最终树启动"
    "（qa/reconcile-all-R2181.log）结果下轮首行如实报。"
)


def live_tokens():
    text = io.open(os.path.join(GROUP, "docs", "decisions.md"),
                   encoding="utf-8").read()
    tokens = set(re.findall(r"\b[DC]-\d{8}-\d+\b", text))
    return sorted(tokens)


def nonempty_rows():
    path = os.path.join(GROUP, "docs", "decisions.md")
    rows = io.open(path, encoding="utf-8").read().split("\n")
    return sum(1 for line in rows if line.strip())


def queue_open(path):
    text = io.open(path, encoding="utf-8").read()
    return sum(1 for line in text.split("\n") if line.startswith("- [ ]"))


def main():
    spath = os.path.join(BASE, "src", "os", "state.json")
    state = json.loads(open(spath, "rb").read().decode("utf-8"))
    state["tick"] = int(state["tick"]) + 1
    state["log"].append(ROUND_LINE)
    state["log"].append(TOKEN_LINE)
    tokens = live_tokens()
    state["last_dec_tokens"] = ",".join(tokens)
    state["last_decision_rows"] = nonempty_rows()
    with io.open(spath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    bpath = os.path.join(BASE, "src", "os", "backlog.md")
    btext = io.open(bpath, encoding="utf-8").read()
    head = "- [ ] P3 explore 队头认领（R2181"
    assert btext.count(head) == 1, "claim row missing"
    btext = btext.replace(head, "- [x] P3 explore 队头认领（R2181", 1)
    first_nl = btext.index("\n")
    btext = (btext[:first_nl] + " " + DONE_NOTE + btext[first_nl:])
    io.open(bpath, "w", encoding="utf-8", newline="\n").write(btext)

    epath = os.path.join(BASE, "docs", "status-export.json")
    export = json.loads(open(epath, "rb").read().decode("utf-8"))
    export["export_ts"] = "2026-10-28T09:05:00+08:00"
    export["do"] = (
        "R2181 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - the seller "
        "side finally has the retention reading the buyer side already "
        "had: who put supply on the shelf for the first time in a given "
        "month, and whether they came back")
    export["ceo_face"] = {
        "current": (
            "R2181: shipped api_market_seller_cohort - a twelve-key "
            "monthly seller cohort built from two stored event sources "
            "only, new exactly once at the earliest event month "
            "(backdated re-listing included), repeat-seller rate, and "
            "retirement explicitly not an event (suite 8/8 double-run "
            "byte-identical); the deferred full battery and matrix "
            "regeneration were launched on this tree"),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py (api_market_seller_cohort) + "
            "src/sandbox/ledger/test_apimarket_sellercohort.py + "
            "qa/apimarket-sellercohort-R2181-a.log and -b.log (SUITE PASS "
            "8/8, sha256 57a23d5d...) + qa/reconcile-all-R2181.log "
            "(launched) - 2026-10-28"),
        "next_milestone": (
            "R2182: read the R2181 battery and suite-matrix regeneration "
            "result line by line, then take the next explore seed "
            "(R2178 4/10, api_category_supply_months) - ETA 2026-10-29, "
            "within 48h"),
        "last_artifact": (
            "qa/apimarket-sellercohort-R2181-a.log (SUITE PASS 8/8, "
            "double-run byte-identical) (2026-10-28)")}
    export["results"].append(["R2181", (
        "R2181: five-silence scan clean with four apparent new decision "
        "tokens, all citation-only inside other companies' rows, so zero "
        "domain action and the baseline re-anchored at 163. Product: "
        "api_market_seller_cohort with AC-MSC1..AC-MSC8 pre-registered "
        "before the code, SUITE PASS 8/8 double-run byte-identical "
        "(sha256 57a23d5d943bea5d), wired as "
        "ledger-apimarket-sellercohort(8). The R2180 deferred battery and "
        "suite-matrix regeneration were launched against the final tree "
        "and are reported next round rather than claimed here.")])
    if len(export["results"]) > 12:
        del export["results"][0]
    sd = export["self_drive"]
    sd["log_lines_in_window"] = sd["log_lines_in_window"] + 2
    sd["substantive_non_idle_mention_lines"] = (
        sd["substantive_non_idle_mention_lines"] + 2)
    sd["queue_explore_open"] = queue_open(
        os.path.join(BASE, "state", "queue", "explore.md"))
    sd["queue_tech_open"] = queue_open(
        os.path.join(BASE, "state", "queue", "tech.md"))
    with io.open(epath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("state tick=%d tokens=%d rows=%d explore_open=%d"
          % (state["tick"], len(tokens), state["last_decision_rows"],
             sd["queue_explore_open"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())