"""R2209 closeout: state log, status export, backlog row (ASCII source).

Product of this round: api_buyer_claim_months (criteria AC-BCM1..AC-BCM8
registered in the R2209 explore-queue claim row before the code).
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
DECISIONS = os.path.abspath(os.path.join(
    ROOT, "..", "..", "docs", "decisions.md"))

ROUND = "R2209"
EXPORT_TS = "2026-10-28T23:10:00+08:00"

ROUND_LINE = (
    "2026-10-28 R2209 (five-silence scan clean at open: decisions.md 261 "
    "non-empty rows carrying four apparent additions - D-20261006-05, "
    "D-20261007-04, D-20261007-05 and D-20261008-05 - each one a "
    "citation inside another seat's executed row rather than a BigDomain "
    "action face, already acknowledged in R2173/R2181/R2183/R2186/R2194/"
    "R2201, so zero domain action and the baseline is re-anchored to the "
    "measured set; the group ledger carries the same three @BigDomain "
    "patrol rows already paid off with zero unreplied; the group orders "
    "tail is unchanged at the 2026-10-28 15:01 fleet auto-dispatch "
    "OB-20261028-150100-267, a fleet dispatcher face acknowledged with "
    "zero domain action; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
    "stay blocked-on-CEO, the weekly proposal duty is met by BD-PROP-005, "
    "all four tech heads stayed gated (docker host absent, logs toolkit "
    "standing maintenance, member refunded schema product-gated, the "
    "live-mtime row waiting on a real normalized-mtime event) and the "
    "explore queue carried the merchant-gated benchmark row plus three "
    "R2202 seeds, so this window claimed the seed head. Gap statement: "
    "api_buyer_claim_todo answers the present debt of one resident but "
    "carries no dates at all, and api_market_claim_months aggregates the "
    "whole market, so a resident who opened one claim in June and kept a "
    "long-running dispute in October read identically. Product: "
    "APIMarketFace.api_buyer_claim_months(buyer_id) - a twenty-two-key "
    "envelope with eleven-key month rows. The booking law books a claim "
    "ONLY in the UTC month of its own opened_utc: a refund landing two "
    "months later neither re-dates the claim nor invents a row in the "
    "refund month, and the amount frozen at open is never rewritten. "
    "That is deliberately the opposite of api_buyer_refund_months, which "
    "books that cash in the month it came back - the fixture proves both "
    "faces hold on the same world, with the refund face spanning "
    "2026-06..2026-12 contiguously while the claim face stops at "
    "2026-10. The grid is contiguous with honest zero months whose "
    "average is None and whose running accumulator is carried flat; the "
    "five-state partition (refunded > withdrawn > answered > open) sums "
    "to claim_count per row and in the envelope, closed_count is "
    "refunded + withdrawn, resolved_share reads None at zero claims "
    "(0.6 measured here), and the average is POOLED (6.2) rather than a "
    "mean of monthly means (6.33). noted_count is the buyer-side signal "
    "this face adds: the claims of a month carrying an append-only "
    "follow-up note, counted regardless of later resolution. Strict "
    "buyer isolation with the usr: gate before any read (seven bad forms "
    "fail-closed, the bare prefix reading honestly empty), the "
    "earlier-month peak tie-break that never peaks on a zero month, "
    "cross-face identity of claim_count against api_buyer_claim_todo and "
    "of the money sum against the raw claims table, and a pure read with "
    "frozen digests, a constant ledger_tx set and three-instance byte "
    "identity over two restarts. Verification: SUITE PASS 8/8 "
    "double-run byte-identical, both runs 909 bytes, body sha256 "
    "55ac56980c0025be7ca7a60cdd2b5849a665692d40a2c0c95fad34cda7bdbcf2, "
    "criterion lines sha16 bb17e94828053a50 (qa/"
    "apimarket-buyerclaimmonths-R2209-a.log and -b.log, crlf=0 lone "
    "cr=0), wired ledger-apimarket-buyerclaimmonths(8), eight adjacent "
    "claim-family suites green (qa/regression-R2209.log: claims, "
    "claims_respond, claims_withdraw, claimnote, buyerclaimtodo, "
    "claimlatency, claimmonths, sellertodo). Honest notes: the first run "
    "read 6/8 and BOTH reds were this window's test expectations, not "
    "product defects - the neighbouring refund face runs a contiguous "
    "grid so its months are 06..12 rather than the two refund months I "
    "first asserted, and the mean of monthly means is 6.33 by float "
    "rounding rather than the 6.34 I wrote; test and docstring were "
    "corrected and no implementation was widened. The adjacent sweep was "
    "first pointed at a suite filename that does not exist "
    "(test_apimarket_marketclaimmonths.py; the real file is "
    "test_apimarket_claimmonths.py), so the log on disk is the second "
    "run. The full reconcile battery and the suite-matrix regeneration "
    "were NOT run inside this window (25-minute budget, the R2168 "
    "mixed-tree rule) and lead the next round; two R2202 seeds remain "
    "open."
)

TOKENS_LINE = (
    "R2209 tokens: local=~80k api=0 api_reason=five-silence scan with a "
    "four-token citation re-anchor + explore seed claim with criteria "
    "registered before the code + buyer monthly claim flow product face "
    "(booking law on opened_utc, contiguous grid, five-state partition, "
    "closed share, pooled average, follow-up note count, peak tie-break) "
    "+ suite 8/8 double-run byte-identical + eight adjacent regressions "
    "+ queue/backlog/state/export closeout, zero cloud calls; battery "
    "and matrix regeneration deferred"
)

BACKLOG_ROW = (
    "- [x] P3 explore head claim (R2209, seed R2202 row claimed, criteria "
    "AC-BCM1..AC-BCM8 registered in that queue row BEFORE the code): "
    "apimarket buyer-side monthly claim flow "
    "api_buyer_claim_months(buyer_id) - twenty-two-key envelope with "
    "eleven-key month rows; the booking law that books a claim ONLY in "
    "the UTC month of its own opened_utc so a refund landing two months "
    "later neither re-dates the claim nor invents a row in the refund "
    "month (and does not rewrite the amount frozen at open), which is "
    "deliberately different from api_buyer_refund_months booking that "
    "cash in the month it came back; the contiguous grid with an honest "
    "zero month whose average is None and whose running accumulator is "
    "carried flat; the five-state partition open + answered + withdrawn "
    "+ refunded == claim_count per row and in the envelope with "
    "closed_count == refunded + withdrawn and resolved_share reading "
    "None at zero claims; the POOLED average (6.2) against a mean of "
    "monthly means (6.33); noted_count as the buyer-side follow-up "
    "signal counted regardless of later resolution; the earlier-month "
    "peak tie-break that never peaks on a zero month; strict buyer "
    "isolation with the usr: gate before any read, seven bad forms "
    "fail-closed and the bare prefix reading honestly empty; and a pure "
    "read with frozen digests, a constant ledger_tx set and "
    "three-instance byte identity over two restarts. Evidence: SUITE "
    "PASS 8/8 double-run byte-identical, body sha256 "
    "55ac56980c0025be7ca7a60cdd2b5849a665692d40a2c0c95fad34cda7bdbcf2 "
    "and criterion sha16 bb17e94828053a50 "
    "(qa/apimarket-buyerclaimmonths-R2209-a.log / -b.log, 909 bytes "
    "each, crlf=0, single writer utf-8 LF); wired "
    "ledger-apimarket-buyerclaimmonths(8); eight adjacent claim-family "
    "suites green (qa/regression-R2209.log). Honest note: the first run "
    "read 6/8 and both reds were this-window test expectations (the "
    "neighbour's contiguous refund grid, and the 6.33 float mean of "
    "means) corrected without widening any implementation; the full "
    "battery and matrix regeneration were NOT run (25-minute budget) and "
    "are the R2210 first item; two R2202 seeds remain open. "
    "[done 2026-10-28 R2209]\n"
)

DO_TEXT = (
    "R2209 the sandbox developer-API marketplace and the OS toolchain "
    "for the silicon-domain public co-creation platform - a resident can "
    "now read their own after-sales history month by month: each claim "
    "stays in the month it was opened however late it resolves, a quiet "
    "month is an honest zero, and the face separates closed claims from "
    "open ones and counts the months the buyer had to push back."
)

OUTS = [
    "buyer monthly claim flow (api_buyer_claim_months)",
    "on",
    "R2209: the buyer claim debt face carries no dates at all, so one "
    "claim in June and a long dispute in October read identically. The "
    "new face books each claim in the UTC month of its own opened_utc "
    "and never re-dates it when a refund lands later, runs a contiguous "
    "grid with honest zero months and a flat accumulator, partitions the "
    "four states, reports closed_count and resolved_share, keeps a "
    "pooled average distinct from a mean of monthly means, and counts "
    "the follow-up notes the buyer filed.",
]

RESULT_LINE = (
    "R2209: five-silence scan clean with four apparent decision tokens, "
    "all citation-only inside other seats' rows, so zero domain action "
    "and the baseline re-anchored. Product: api_buyer_claim_months with "
    "AC-BCM1..AC-BCM8 anchored and registered before the code, SUITE "
    "PASS 8/8 double-run byte-identical body sha256 "
    "55ac56980c0025be7ca7a60cdd2b5849a665692d40a2c0c95fad34cda7bdbcf2, "
    "wired as ledger-apimarket-buyerclaimmonths(8), eight adjacent "
    "claim-family suites green. Honest debt: full battery and "
    "suite-matrix regeneration deferred to R2210.")


def main():
    with io.open(STATE, encoding="utf-8") as fh:
        state = json.load(fh)

    with io.open(DECISIONS, encoding="utf-8") as fh:
        dec = fh.read()
    tokens = sorted(set(re.findall(r"(?:D|C|O)-20\d{6}-\d{2,4}", dec)))
    rows = sum(1 for line in dec.splitlines() if line.strip())

    state["tick"] = int(state.get("tick", 0)) + 1
    state["last_decision_rows"] = rows
    state["last_dec_tokens"] = ",".join(tokens)
    state["log"].append(ROUND_LINE)
    state["log"].append(TOKENS_LINE)

    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    with io.open(BACKLOG, encoding="utf-8") as fh:
        back = fh.read()
    # keep exactly one copy of this round's row, at the top of the board:
    # drop every existing R2209 claim row, then prepend the canonical one
    kept = [line for line in back.split("\n")
            if not line.startswith("- [x] P3 explore head claim (R2209")]
    back = "\n".join(kept)
    if back.startswith("\n"):
        back = back.lstrip("\n")
    back = BACKLOG_ROW + back
    with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(back)

    with io.open(EXPORT, encoding="utf-8") as fh:
        exp = json.load(fh)
    exp["export_ts"] = EXPORT_TS
    exp["do"] = DO_TEXT
    face = exp["ceo_face"]
    face["last_artifact"] = face.get("latest_artifact")
    face["current"] = (
        "R2209 buyer monthly claim flow: api_buyer_claim_months() books "
        "each claim in the month it was opened however late it resolves, "
        "runs a contiguous grid with honest zero months, partitions the "
        "four states with a closed share and counts the buyer's own "
        "follow-up notes")
    face["latest_artifact"] = (
        "qa/apimarket-buyerclaimmonths-R2209-a.log / -b.log (SUITE 8/8, "
        "sha256 55ac56980c0025be..., byte-identical double run) + "
        "qa/regression-R2209.log (eight adjacent suites 8/8) + "
        "src/sandbox/ledger/apimarket.py (api_buyer_claim_months, "
        "written 2026-10-28)")
    face["next_milestone"] = (
        "full reconcile battery plus suite-matrix regeneration on this "
        "tree (matrix 402 -> 403 suites), then the next explore seed "
        "with its criteria registered before the code - within 48h")
    exp["outs"].insert(0, OUTS)
    exp["results"].insert(0, [ROUND, RESULT_LINE])
    sd = exp.get("self_drive", {})
    sd["log_lines_in_window"] = int(sd.get("log_lines_in_window", 0)) + 2
    sd["queue_explore_open"] = max(
        0, int(sd.get("queue_explore_open", 0)) - 1)
    exp["self_drive"] = sd

    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(exp, ensure_ascii=False, indent=2) + "\n")

    print("tick", state["tick"], "rows", rows, "tokens", len(tokens))


if __name__ == "__main__":
    main()