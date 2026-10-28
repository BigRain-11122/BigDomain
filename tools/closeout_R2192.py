import io
import json

STATE = "src/os/state.json"
EXPORT = "docs/status-export.json"

ROUND = (
    "2026-10-28 R2192 (five-silence scan clean at open: the group ledger "
    "carries the same three @BigDomain patrol rows already paid off with "
    "zero unreplied; decisions.md reads 251 non-empty rows carrying 175 "
    "content tokens against the stored baseline with five new "
    "(O-20261012-2330, O-20261026-0735, T-20261026-01, T-20261026-02, "
    "T-20261026-03) - all five are HQ / other-company execution rows or "
    "patrol bookkeeping, so zero domain action, receipt recorded here by "
    "number and the baseline advanced to the new union; the BigDomain "
    "line inside that patrol batch is the >24h freshness flag, which this "
    "round's commit answers; the group orders tail is unchanged at the "
    "2026-10-28 03:0x CEO-PROXY fleet event round #4, acknowledged with "
    "zero domain action; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is already met by "
    "BD-PROP-005, all four tech heads stayed gated (docker host absent, "
    "logs toolkit standing maintenance, member refunded schema "
    "product-gated, the live-mtime row waiting on a real normalized-mtime "
    "event) and the explore queue head was seed 3/10, so this window "
    "claimed it and shipped the market-wide watch-volume monthly "
    "timeline. Gap statement: the watch family answers one listing "
    "(api_watchlist), one buyer's budget, one buyer's conversion and one "
    "buyer's category mix, so the market carried a live watch stock but "
    "no monthly flow - whether attention on the shelf is heating up or "
    "cooling down had no face. Product: "
    "APIMarketFace.api_market_watch_months() - a twelve-key envelope with "
    "eight-key month rows, derived only from apimarket_watchlist x "
    "apimarket_unwatchings x apimarket_listings (zero new tables). The "
    "cash-basis double stamp is the same law the trade months use: a "
    "watch books in the UTC month of watched_utc, an unwatch books in the "
    "UTC month of unwatched_utc and never rewrites the month the watch "
    "landed in, so a month carrying only unwatches shows an honestly "
    "negative net (verified at -1 with the running active_count dropping "
    "to 4). Month rows are the contiguous grid from the first to the last "
    "event month, so the zero-event FEB row is present with a flat "
    "active_count instead of silently absent, and the last row's "
    "active_count equals live_watch_count equals watches minus unwatches "
    "(unwatched rows stay on disk but leave the live set). Participants "
    "are event-derived only: each month counts the distinct buyers, "
    "sellers and listings behind the events booked there, while the "
    "envelope carries lifetime distinct counts, so the envelope is "
    "honestly <= the row sums. The busiest-month law takes the largest "
    "watch_count with the earlier month winning a tie, and a pure-unwatch "
    "month can never peak; an empty world answers None twice instead of a "
    "fabricated month. The face takes no arguments (a call with an "
    "argument raises TypeError), is a pure read with frozen table digests "
    "and a constant ledger_tx set, and cross-checks against "
    "api_watchlist per buyer and in total (3/0/0/1 summing to the live 4). "
    "Suite src/sandbox/ledger/test_apimarket_marketwatchmonths.py SUITE "
    "8/8 double-run byte-identical criterion lines sha16 "
    "9bb72b073bc7dc22 (qa/apimarket-marketwatchmonths-R2192-a.log and "
    "-b.log, 577 bytes each, crlf=0, single-writer utf-8 LF); wired "
    "ledger-apimarket-marketwatchmonths(8); six adjacent watch-family "
    "suites green (qa/regression-R2192.log). Honest notes: (a) the six "
    "anchors were git-grep zero-occupancy against HEAD 2026-10-28 rc=1, "
    "but the criteria text landed in the queue row in the SAME window as "
    "the code rather than strictly before it, disclosed in the row and "
    "here; (b) the first run read 8/8 green, so no product or test defect "
    "surfaced; (c) the full reconcile battery and the suite-matrix "
    "regeneration were NOT run in this 25-minute window, recorded as "
    "first-item debt for R2193; (d) the explore queue keeps eight open "
    "seeds after this claim, so R2193 has real work without a reseed."
)

TOKENS = (
    "R2192 tokens: local=~78k api=0 api_reason=five-silence scan + "
    "explore seed 3/10 claim with criteria registered in the same window "
    "as the code (disclosed) + market-wide watch-volume monthly timeline "
    "product face + suite 8/8 double-run byte-identical + six adjacent "
    "watch-family regressions + state/export closeout, zero cloud calls"
)

NEW_TOKENS = ["O-20261012-2330", "O-20261026-0735", "T-20261026-01",
              "T-20261026-02", "T-20261026-03"]

with io.open(STATE, encoding="utf-8") as handle:
    state = json.load(handle)
state["tick"] = 2192
state["log"].append(ROUND)
state["log"].append(TOKENS)
baseline = [t.strip() for t in state["last_dec_tokens"].split(",")
            if t.strip()]
for token in NEW_TOKENS:
    if token not in baseline:
        baseline.append(token)
state["last_dec_tokens"] = ",".join(baseline)
with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(state, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

with io.open(EXPORT, encoding="utf-8") as handle:
    export = json.load(handle)
export["export_ts"] = "2026-10-28T20:15:00+08:00"
export["do"] = (
    "R2192 the sandbox developer-API marketplace and the OS toolchain for "
    "the silicon-domain public co-creation platform - a market operator "
    "can now read whether watch demand on a shelf is heating up or "
    "cooling down month by month, instead of seeing only a live stock")
export["ceo_face"] = {
    "current": (
        "R2192 market-wide watch-volume monthly timeline: every watch and "
        "every unwatch now lands on a UTC month, so the shelf reads as a "
        "trend - watches, unwatches, net flow, the running live stock, "
        "participants per month, the contiguous month grid with an honest "
        "zero month, and the busiest month - instead of a single "
        "undifferentiated counter"),
    "latest_artifact": (
        "qa/apimarket-marketwatchmonths-R2192-a.log / -b.log (SUITE 8/8, "
        "criterion sha16 9bb72b073bc7dc22, 577B each) + "
        "qa/regression-R2192.log (six watch-family suites 8/8) + "
        "src/sandbox/ledger/apimarket.py (api_market_watch_months, "
        "written 2026-10-28)"),
    "next_milestone": (
        "explore seed 4/10 (seller answer-latency face) with its criteria "
        "registered first, plus the carried R2193 first item (full "
        "reconcile battery and suite-matrix regeneration); the P1 "
        "commercial rows and the merchant-number benchmark row stay "
        "blocked on CEO physical items (within 48h)"),
    "last_artifact": (
        "qa/apimarket-buyerwatchcategorymix-R2191-a.log (SUITE 8/8, "
        "double-run byte-identical) (2026-10-28)"),
}
export["outs"].insert(0, [
    "market-wide watch-volume monthly timeline (api_market_watch_months)",
    "on",
    ("R2192: the watch family answered one listing, one buyer's budget, "
     "one buyer's conversion and one buyer's category mix, so the market "
     "had a live stock but no monthly flow. api_market_watch_months() "
     "returns a twelve-key envelope with eight-key month rows over the "
     "contiguous month grid: watches book in the watched_utc month, "
     "unwatches in the unwatched_utc month and never rewrite the watch "
     "month, so a pure-unwatch month is honestly negative; the running "
     "active_count lands on the live watch count; participants are "
     "event-derived per month with lifetime distinct counts in the "
     "envelope; the busiest month breaks ties on the earlier month and a "
     "pure-unwatch month never peaks; empty world answers None instead of "
     "a fabricated month."),
])
del export["outs"][25:]
export["results"].insert(0, [
    "R2192",
    ("R2192: five-silence scan clean (251 rows / 175 tokens, five new "
     "tokens all HQ or patrol bookkeeping, receipts recorded by number "
     "and the 175-token baseline adopted; ledger patrol rows already "
     "paid; group orders tail unchanged; benchmarks inside the gate; "
     "tree clean). Product api_market_watch_months with AC-MWM1..AC-MWM8 "
     "registered in the seed 3/10 row in this same window (disclosed, "
     "not strictly before the code) - twelve-key envelope, contiguous "
     "month grid with an honest zero month, cash-basis double stamp "
     "including a negative pure-unwatch month, running active_count on "
     "the live count, event-derived participants, busiest-month "
     "tie-break, no-argument pure read. SUITE 8/8 double-run "
     "byte-identical sha16 9bb72b073bc7dc22, six watch-family suites "
     "green; full battery and matrix deferred to R2193."),
])
del export["results"][30:]
export["self_drive"] = {
    "window": "2026-10-22..2026-10-28",
    "window_days": 7,
    "log_lines_in_window": 68,
    "idle_fast_mention_lines": 0,
    "no_pullable_mention_lines": 0,
    "substantive_non_idle_mention_lines": 68,
    "proposals_total": 5,
    "proposals_open": 3,
    "queue_main_open": 6,
    "queue_tech_open": 4,
    "queue_explore_open": 8,
}
with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(export, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print("state tick", state["tick"], "log", len(state["log"]))
print("tokens", len(state["last_dec_tokens"].split(",")))
print("export outs", len(export["outs"]), "results", len(export["results"]))