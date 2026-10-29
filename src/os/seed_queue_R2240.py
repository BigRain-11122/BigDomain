"""Seed the R2240 queue-floor debt with real gaps (not filler rows).

Inserts short seed rows at the head of state/queue/explore.md and
state/queue/tech.md. Full acceptance criteria are pinned into each row
at CLAIM time, before the code, per the standing practice; the seed
carries the face name, the measured gap and the criteria prefix.
"""

import io
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
Q = os.path.join(ROOT, "state", "queue")

EXPLORE = """- [ ] P3 explore seed (R2240 a): apimarket **seller-scoped monthly watch-to-purchase conversion** (`api_seller_watch_conversion_months`) - api_market_conversion_months answers the whole market, api_category_watch_conversion_months one category and api_watch_conversion one listing over its lifetime, so a single seller cannot read whether its own attention converted month over month. Criteria prefix AC-SWCV1..8 (contract, watch-month cohort booking, the pre_owned / pending / converted split, contiguous grid, seller isolation, market benchmark, identity against the two source faces, purity).
- [ ] P3 explore seed (R2240 b): apimarket **per-category monthly rating intake** (`api_category_rating_months`) - api_market_rating_months and api_seller_rating_months both publish the month axis but never by category, so a bucket whose service quality moved reads identically to the market average. Criteria prefix AC-CRM2-1..8 (contract, rated_utc booking with the revision seam, per-category month cells, contiguous grid, pooled star mean, category seam on revise_category, uncategorized flag, purity).
- [ ] P3 explore seed (R2240 c): apimarket **seller-scoped monthly refund flow** (`api_seller_refund_months`) - api_buyer_refund_months is the buyer axis, api_category_refund_months the category axis and api_seller_refund_reasons only a lifetime reason mix, so a seller's month-by-month refund pressure and its money weight have no face. Criteria prefix AC-SRFM1..8 (contract, refunded_utc booking, money split gross/refunded/net, refund_rate None on a zero denominator, contiguous grid, seller isolation, identity against buyer/category axes, purity).
- [ ] P3 explore seed (R2240 d): apimarket **seller-scoped monthly claim pressure** (`api_seller_claim_months`) - api_market_claim_months and api_category_claim_months exist and api_claims lists a seller's claims lifetime, so a seller cannot read whether after-sales pressure is rising month over month. Criteria prefix AC-SCLM1..8 (contract, opened_utc booking, five-state seam, money on the claim side, contiguous grid, seller isolation, identity against the market face, purity).
- [ ] P3 explore seed (R2240 e): apimarket **market monthly restock pressure** (`api_market_restock_months`) - api_seller_restock_months is seller-scoped and api_market_supply_months only counts units live, so how fast the whole market's sold-out shelves come back had no reading. Criteria prefix AC-MRS1..8 (contract, restock stamp booking, sold-out denominator, contiguous grid, honest zero month, pooled latency, identity against the seller face, purity).
- [ ] P3 explore seed (R2240 f): apimarket **buyer monthly claim outcome mix** (`api_buyer_claim_outcome_months`) - api_buyer_claim_months counts the claims a buyer opened, but whether they were answered, withdrawn or refunded month over month (the outcome, not the volume) has no face. Criteria prefix AC-BCO1..8 (contract, opened_utc booking, outcome seam precedence, money split, contiguous grid, buyer isolation, identity against the buyer claim face, purity).
"""

TECH = """- [ ] P2 tech seed (R2240 a): `src/os/queue_floor.py` - a read-only gauge that counts OPEN rows per queue against the self-drive standing floors (main >= 5, tech >= 10, explore >= 10) and reports the shortfall per queue in one line, so floor debt is measured instead of discovered mid-window. Criteria prefix AC-QF1..6 (contract, gated-row exclusion, floor table, honest zero, CLI codes, purity).
- [ ] P2 tech seed (R2240 b): `src/os/state_fold.py` - the state.json log fold has been executed by hand in several windows (archive-aware slicing, verbatim byte preservation, waterline gate); this module owns the fold predicate and the verbatim archive append behind one callable, with a --check mode. Criteria prefix AC-SF1..6 (waterline law, verbatim preservation, archive append, --check read-only, idempotence, purity).
- [ ] P2 tech seed (R2240 c): `state/debt.md` plus a checker - every window that ships a product face defers the reconcile battery, and the deferral currently lives only in prose; a machine-readable debt register (round, what is owed, since when, first-item flag) with a checker would stop the carried item from being re-derived by reading log prose. Criteria prefix AC-DEBT1..6 (register format, first-item flag, stale-debt alarm, checker CLI, honest empty, purity).
- [ ] P2 tech seed (R2240 d): status-export freshness gate - docs/status-export.json is required to carry a live line, a last artifact and a milestone within 48h; a checker that fails when the milestone window is stale or the three lines are missing would make the CEO-visible face self-policing. Criteria prefix AC-EXP1..6 (three-line contract, ISO8601 timestamps, 48h window check, stale verdict, CLI codes, purity).
"""


def seed(name, block):
    path = os.path.join(Q, name)
    with io.open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    text = text.replace("\r\n", "\n")
    if not text.endswith("\n"):
        text += "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(block + text)
    print("seeded %s: +%d rows" % (name, block.count("\n- [ ]")))


def main():
    seed("explore.md", EXPLORE)
    seed("tech.md", TECH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())