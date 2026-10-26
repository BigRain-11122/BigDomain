"""R2148 state closeout: tick, measured baseline fields, log lines."""

import io
import json
import os

ROOT = r"C:\Users\sjs20\Desktop\FluxGroup\domain\BigDomain"
STATE = os.path.join(ROOT, "src", "os", "state.json")

ROUND = (
    "2026-10-27 R2148 (five-silence scan clean: decisions.md 288 rows / "
    "213 content-addressed tokens with zero new against the stored "
    "baseline; the ledger's two @BigDomain patrol rows already paid off "
    "with zero unreplied; the group orders baseline unchanged at the "
    "2026-10-26 22:36 dispatch-deck row; benchmarks refreshed 2026-10-26 "
    "inside the seven-day gate; tree clean, no index.lock; all four tech "
    "heads stayed gated - docker host absent, logs toolkit standing "
    "maintenance, member refunded schema product-gated, the live-mtime "
    "row waiting on a real normalized-mtime event - and the single "
    "explore row was gated on the merchant id) - so this window first "
    "honoured the R2147 carry-over (its own log line said the full "
    "battery was NOT run and was the first item of the next round) and "
    "then seeded and claimed a fresh P3 row in the SAME window with "
    "AC-AMSI1..AC-AMSI8 registered BEFORE the code existed (six anchors "
    "- AC-AMSI, api_similar_listings, apimarket_similar, the suite name, "
    "the runner label and abs_price_delta - all git grep -F "
    "zero-occupancy against HEAD, rc=1). Gap statement: every existing "
    "discovery door makes the caller state the criteria first (api_search "
    "wants a keyword, seller, price band or category; api_categories "
    "describes a bucket; api_category_demand asks whether it sells; "
    "api_listing_position ranks one listing inside its own bucket), so "
    "the buyer's most natural follow-up after opening a listing - 'what "
    "else is like this one' - had no face and a caller had to read the "
    "listing, harvest its category and price, rebuild the neighbour set "
    "through api_search and sort it by hand. Product: "
    "APIMarketFace.api_similar_listings(listing_id, limit=None, "
    "include_delisted=False) pins the definition of 'similar' the market "
    "never had - the candidate set is the listing's EFFECTIVE category "
    "bucket minus the head, ordered by asking-price distance from the "
    "head, then price, then listing_id, so the order is a TOTAL order and "
    "two equally distant neighbours never swap between calls. Price rides "
    "_current_price, rating rides the effective stars, net sales ride the "
    "scarcity seam and titles ride the metadata seam, so a repricing, a "
    "rating revision, a refund, a restock or a metadata edit moves the "
    "neighbour set in the same step it moves every other read face and no "
    "listing row is ever rewritten. An uncategorized head recruits only "
    "uncategorized listings (zero cross-bucket permeation) and a retired "
    "head stays readable so history is not erased. The pinned gate order "
    "is listing shape, existence, limit shape, then the include_delisted "
    "flag, so an unknown listing answers E_AM_UNKNOWN_LISTING even when "
    "the limit or flag is also malformed, and every refusal writes zero "
    "rows and moves zero tokens. Twelve-key envelope, thirteen-key rows, "
    "derived price_delta/abs_price_delta, the head never in its own rows, "
    "and the bucket conservation identity against api_categories. "
    "Verification: suite SUITE PASS 8/8 double-run rc=0/0 with "
    "byte-identical evidence files sha16 de2a2967933737d1 "
    "(qa/apimarket-similar-R2148-a.log and -b.log, 2052 bytes each, "
    "single-writer UTF-8 LF); wired as ledger-apimarket-similar(8); six "
    "adjacent suites re-ran green (search, searchstock, category, "
    "categoryrev, listingposition, supply - 8/8 each); the full battery "
    "the R2147 window deferred completed RUNNER PASS 351/351 suites green "
    "plus reconcile controls 7/7 in 636.6s (qa/reconcile-all-R2148.log, "
    "4192 lines, 688996 bytes, zero CR, no BOM, single writer) with TMP "
    "RECLAIM candidates=803 removed=803 busy=0 failed=0 reclaimed=287.53 "
    "MiB; the suite matrix was regenerated to 351 suites / 2916 criteria "
    "and --check reports byte-identical. Honest notes: (a) the first "
    "suite cut expected a retired head's default neighbour set to be "
    "empty, but the LIVE neighbour correctly stays, so the test "
    "expectation was corrected instead of the criteria being loosened; "
    "(b) the battery was launched through the stream driver with a "
    "scratch stdout tee, and that scratch file is not evidence - the "
    "authoritative evidence is the single-writer file quoted above; (c) "
    "no product defect was found by the suite this window."
)

TOKENS = (
    "R2148 tokens: local=~120k api=0 api_reason=five-silence scan + "
    "nearest-neighbour product change + suite 8/8 double-run + six "
    "adjacent regressions + full battery 351/351 + TMP reclaim 803 worlds "
    "+ matrix regen/check + export refresh + state closeout, zero cloud "
    "calls"
)

with io.open(STATE, "rb") as handle:
    data = json.loads(handle.read().decode("utf-8"))

data["tick"] = int(data["tick"]) + 1
data["last_decision_rows"] = 288
data["log"].append(ROUND)
data["log"].append(TOKENS)

out = json.dumps(data, ensure_ascii=False, indent=2)
with io.open(STATE, "wb") as handle:
    handle.write((out + "\n").encode("utf-8"))

print("tick", data["tick"], "log", len(data["log"]))