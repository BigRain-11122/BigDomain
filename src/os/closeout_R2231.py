"""R2231 closeout: bump the tick and append the window's log lines.

Usage: python src/os/closeout_R2231.py
"""

import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROUND = (
    "2026-10-29 R2231 (five-silence scan clean at open: decisions.md 274 "
    "rows carrying 178 content-addressed D/C/O/T tokens that EQUAL the "
    "stored baseline exactly - zero new and zero dropped, so zero domain "
    "action; the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-29 00:52 fleet event round already consumed in "
    "R2226; benchmarks refreshed 2026-10-29 inside the seven-day gate; tree "
    "clean, no index.lock) - the P1 canonical rows stay blocked-on-CEO and "
    "all four tech heads stayed gated (docker host absent, logs toolkit "
    "standing maintenance, member refunded schema product-gated, the "
    "live-mtime row waiting on a real normalized-mtime event), so the "
    "explore queue head was worked. That head row (R2213 seed, "
    "api_market_catalog_months) was judged NEGATIVE WITH EVIDENCE rather "
    "than built: the premise that the market had no catalog-scale month "
    "timeline is false, because api_market_supply_months (R2214) already "
    "publishes live_listing_count plus in_stock/sold_out/unlimited and "
    "units per month together with opened_total/closed_total flows and "
    "seller breadth, so active shelves, retired shelves and total scale all "
    "read on that one face and a second face would be the repeat-wheel red "
    "line. The row is closed on that evidence and the next open seed (R2230 "
    "1/6, api_seller_question_months, criteria AC-SQM1..AC-SQM8 already "
    "pre-registered in that row before any code) was claimed. Gap: "
    "api_market_question_months answers the whole market by month, "
    "api_category_question_months one category, api_seller_answer_months a "
    "seller's OWN answers, and api_seller_questions one lifetime inbox - so "
    "a seller drowning in pre-sale questions last month and a seller nobody "
    "asked read identically, because INCOMING pressure had no month axis. "
    "Product: APIMarketFace.api_seller_question_months(dev_account) - an "
    "eighteen-key envelope with nine-key month rows. Booking law: a "
    "question books in the UTC month of its own immutable asked_utc and the "
    "ANSWERING leg is credited to the ASKING month, never to the month the "
    "answer landed in, so the suite's March discharge of a January question "
    "raises January to 2/2 answered while March stays at 2 asked / 1 "
    "answered. Grid: contiguous rows with an honest zero February whose "
    "answer_rate is None and both monotone accumulators (running_question "
    "2,2,4 and running_answer 2,2,3) landing on the envelope totals. Peak: "
    "the 2 vs 2 tie resolves to the earlier January month and a zero month "
    "is never a peak. Participation is event-derived per month (2/1, 0/0, "
    "2/2) against lifetime distinct envelope counts (4 buyers, 3 owned "
    "listings), the market_question_count benchmark reads 5, and identity "
    "holds against a raw join over the question table (4 questions, 1 open). "
    "Scope is strict seller isolation on the usr: gate with gina reading her "
    "own single January question. Evidence: SUITE PASS 8/8 double-run "
    "byte-identical (qa/apimarket-sellerquestionmonths-R2231-a.log and "
    "-b.log, 763 bytes each, utf-8 LF written directly by "
    "src/os/evidence_R2231.py - never a shell redirection, the ps-utf16 "
    "trap), wired as ledger-apimarket-sellerquestionmonths(8) in "
    "reconcile_all.py, six adjacent question/answer suites green 8/8 each "
    "(qa/regression-R2231.log; there is no separate sellerquestions suite, "
    "noted in that log), PRODUCT_SHA_STABLE True. Honest debts: the full "
    "reconcile battery and the suite-matrix regeneration were NOT run in "
    "this 25-minute window (the R2168 mixed-tree rule) and are the next "
    "window's first item; the state.json log crossed the waterline gate "
    "before this window opened (disk 79732B, margin -1232B) so a fold is "
    "also owed."
)

TOKENS = (
    "R2231 tokens: local=~40k api=0 api_reason=product window on the "
    "R2230 explore head seed - one stale head row closed negative with "
    "supply-face evidence, one new seller incoming-pressure month face, an "
    "eight-criterion suite double-run to byte-identical evidence through a "
    "single python writer, six adjacent question/answer regressions, and "
    "the queue/backlog/state/export closeout; zero cloud calls; the full "
    "battery, the matrix regeneration and the state fold are deferred and "
    "recorded"
)


def main():
    with io.open(STATE, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = int(state["tick"]) + 1
    state["log"].append(ROUND)
    state["log"].append(TOKENS)
    blob = json.dumps(state, indent=2, ensure_ascii=False)
    with io.open(STATE, "w", encoding="utf-8", newline="\r\n") as handle:
        handle.write(blob)
    print("tick=%d log_lines=%d" % (state["tick"], len(state["log"])))


if __name__ == "__main__":
    main()