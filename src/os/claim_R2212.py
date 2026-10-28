"""R2212 explore-head claim: register AC-FMD1..AC-FMD8 in the queue row
BEFORE the product code exists (acceptance-criteria-first law)."""
import io

PATH = "state/queue/explore.md"

OLD = ("- [ ] P3 explore seed (R2202, monthly event-volume timeline, "
       "`api_market_feed_months`): api_market_feed lists event rows with a "
       "window filter, so the shape of activity volume over months (a burst "
       "month versus a quiet one) must be counted by hand. Suggested prefix "
       "next free family; anchor law = git grep -F zero-occupancy on the "
       "prefix, the face name, the suite name and the runner label BEFORE the "
       "code, criteria registered in this row first.")

NEW = "\n".join([
    "- [ ] P3 explore head claim (R2212, seed R2202 8/8, anchor check "
    "2026-10-28: AC-FMD, test_apimarket_feedmonths, "
    "ledger-apimarket-feedmonths, feed_month_count and monthly_event all "
    "git grep -F rc=1; api_market_feed_months appears only in queue, state "
    "and docs prose, never in code): apimarket **monthly activity-volume "
    "timeline** api_market_feed_months(since_utc=None, until_utc=None, "
    "kinds=None, dev_account=None). Gap: api_market_feed answers \"what just "
    "happened\" as one flat ordered stream behind a window filter, so the "
    "shape of activity over months (a burst month versus a quiet one) can "
    "only be counted by hand, and every month face already shipped reads ONE "
    "family (ratings, questions, answers, watch, supply), never the merged "
    "market volume.",
    "  **AC-FMD1 shape** = a seventeen-key envelope (scope, dev_account, "
    "since_utc, until_utc, kinds, month_count, active_month_count, "
    "event_total, by_kind, busiest_kind, peak_month, peak_event_count, "
    "first_month, last_month, latest_month_event_count, disclaimer, months) "
    "with six-key month rows (month, event_count, by_kind, busiest_kind, "
    "active_kind_count, running_total), and an honest empty world "
    "(month_count 0, months [], first/last/peak None, event_total 0) rather "
    "than an invented month.",
    "  **AC-FMD2 booking law** = every event books in the UTC month of its "
    "own immutable stamp (event_utc[:7]) across all eleven feed families; a "
    "revision is its own event in its own month and never rewrites the month "
    "of the row it revises; nothing reads a wall clock, so the same rows "
    "always answer the same grid.",
    "  **AC-FMD3 contiguous grid** = the month rows run first..last with no "
    "gap, so a month without events carries an honest zero row (event_count "
    "0, by_kind {}, busiest_kind None, active_kind_count 0, running_total "
    "held flat) instead of being silently absent.",
    "  **AC-FMD4 conservation** = each row's by_kind values sum to its "
    "event_count, the monthly event_counts sum to the envelope event_total, "
    "the envelope by_kind sums to the same total, active_kind_count equals "
    "len(by_kind), running_total is monotone and its last value equals "
    "event_total.",
    "  **AC-FMD5 peak laws** = peak_month ignores zero months and resolves a "
    "tie to the EARLIER month; busiest_kind is the envelope-wide leader "
    "resolved by the module-pinned feed rank order on a tie "
    "(published first, then relisted, price_revised, metadata_revised, "
    "restocked, purchased, rated, rating_revised, rating_replied, refunded, "
    "delisted); a zero month has no busiest_kind.",
    "  **AC-FMD6 filters** = the half-open [since_utc, until_utc) window, the "
    "kinds normalization to the pinned rank order and the seller scope "
    "compose exactly as api_market_feed does; the envelope echoes the scope "
    "and every filter given (dev_account None on the market scope, the "
    "resolved kinds list always); a shape-valid seller that owns no listing "
    "answers an honest empty timeline.",
    "  **AC-FMD7 gates** = refusals are fail-closed before any read in the "
    "pinned feed order (window shape, inverted window, kinds shape, account "
    "prefix) with zero side effects, and the face never invents its own gate "
    "order.",
    "  **AC-FMD8 identity and purity** = event_total is exactly "
    "api_market_feed(same window, same kinds, same seller)[\"total\"] on every "
    "case; the read is pure (frozen table digests, constant ledger_tx set, "
    "zero token movement); three instances across two restarts answer "
    "byte-identical JSON; the source stays ASCII/LF and the suite is wired "
    "as ledger-apimarket-feedmonths(8).",
])

with io.open(PATH, encoding="utf-8") as handle:
    text = handle.read()

if OLD not in text:
    raise SystemExit("claim: seed row not found verbatim, nothing written")

if NEW.splitlines()[0] in text:
    raise SystemExit("claim: row already present, nothing written")

text = text.replace(OLD, NEW, 1)
with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(text)

print("claim: criteria AC-FMD1..AC-FMD8 registered in the R2202 seed row")