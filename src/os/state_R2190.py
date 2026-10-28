import io
import json
import os

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")

PRODUCT = (
    "2026-10-28 R2190 (five-silence scan clean at open: the group ledger"
    " carries the same three @BigDomain patrol rows already paid off with"
    " zero unreplied; decisions.md reads 251 non-empty rows carrying 170"
    " content-addressed D/C tokens with ZERO new against the stored"
    " baseline, so zero domain action and the baseline stands; the group"
    " orders tail is unchanged at the 2026-10-28 03:0x CEO-PROXY fleet"
    " event round #4, acknowledged with zero domain action; benchmarks"
    " refreshed 2026-10-27 inside the seven-day gate; tree clean, no"
    " index.lock) - the P1 canonical rows stay blocked-on-CEO, the weekly"
    " proposal duty is met by BD-PROP-005, all four tech heads stayed"
    " gated (docker host absent, logs toolkit standing maintenance,"
    " member refunded schema product-gated, the live-mtime row waiting on"
    " a real normalized-mtime event) and the head of the explore queue"
    " above the seeds is the merchant-gated benchmark row, so this window"
    " claimed seed 1/10 (R2189) and shipped the seller-side refund reason"
    " structure. Gap statement: api_refund_reasons aggregates the reason"
    " text market-wide and api_seller_quality carries only the seller's"
    " refund count and amount, so a seller could not read what their own"
    " refunds are caused by - a description mismatch and a service that"
    " keeps breaking were indistinguishable on their own ledger. Product:"
    " APIMarketFace.api_seller_refund_reasons(dev_account=None) - a"
    " seventeen-key envelope with eight-key reason rows. The bucket law is"
    " deliberately the same narrow one as the market face (strip() and"
    " lower() only, so case and surrounding whitespace fold while a"
    " different spelling stays a different bucket, no stemming and no"
    " synonym merging); an empty reason is an HONEST bucket carrying"
    " reason=None, pinned LAST however large, excluded from top_reason and"
    " still counted as one bucket of the concentration measure. Refund"
    " rows are attributed by the stored dev_account, so another seller's"
    " refunds never enter the envelope, and the seller's purchase"
    " denominator comes from purchases joined to that seller's listings."
    " Conservation holds against the scoped raw tables (count, amount and"
    " the dev plus platform split per row, labeled plus unlabeled equals"
    " the refund count); share, average and top share are derived with"
    " None instead of a fabricated zero; reason_herfindahl is computed"
    " from exact fractions (one bucket 10000.0, four buckets of 2/1/1/1"
    " over five refunds 2800.0, the six-refund market 2777.78); and the"
    " total order (-refund_count, -refunded, reason ascending with the"
    " unlabeled bucket pinned last) keeps equally sized buckets from"
    " swapping between calls. Scope law mirrors the sibling seller faces:"
    " the market scope never benchmarks itself (market_refund_rate and"
    " market_refund_share None), while a seller scope carries the market"
    " refund rate and that seller's share of the market refunded total"
    " (0.878 for dana, 0.122 for frank), and the face is a pure read with"
    " frozen table digests and a constant ledger_tx set. Suite"
    " src/sandbox/ledger/test_apimarket_sellerrefundreasons.py SUITE 8/8"
    " double-run byte-identical criterion lines sha16 aea3ccbc7c14b8f2"
    " (qa/apimarket-sellerrefundreasons-R2190-a.log and -b.log, 1355"
    " bytes each, crlf=0, single-writer utf-8 LF); wired"
    " ledger-apimarket-sellerrefundreasons(8); six adjacent refund and"
    " seller suites green (qa/regression-R2190.log). Honest notes: (a) the"
    " first run read 6/8 red on two of this window's own expectations -"
    " the dana herfindahl was written as 3200.0 when the fixture math is"
    " 2/1/1/1 over five refunds = 2800.0, and api_seller_quality does not"
    " carry a refund count at all (it is a rating scorecard), so the"
    " cross-face identity check now uses api_refund_register with"
    " dev_account; (b) a third red was a real test defect found by that"
    " same run - dumps() was applied twice to the already-serialized"
    " retirement snapshot, and the seller envelope legitimately moves on"
    " the market benchmark keys when another seller's refund lands, so"
    " the criterion now asserts the seller rows and count stay frozen"
    " while the benchmark moves honestly (0.8571/0.878 to 1.0/0.7826); no"
    " implementation was loosened in any of the three; (c) the full"
    " reconcile battery and the suite-matrix regeneration were NOT run in"
    " this 25-minute window, recorded as first-item debt for R2191; (d)"
    " the explore queue keeps nine open seeds after this claim, so R2191"
    " has real work without a reseed.")

TOKENS = (
    "R2190 tokens: local=~72k api=0 api_reason=five-silence scan +"
    " explore seed 1/10 claim with criteria pre-registered before code +"
    " seller refund reason product face + suite 8/8 double-run"
    " byte-identical + six adjacent regressions + state/export closeout,"
    " zero cloud calls")


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2190
    state["last_decision_rows"] = 251
    state["log"].extend([PRODUCT, TOKENS])
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("tick", state["tick"], "log", len(state["log"]))


if __name__ == "__main__":
    main()