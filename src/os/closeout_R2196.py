"""R2196 closeout: state tick and log, backlog row, status export.

The buyer purchase-gap rhythm face shipped this window; every counter
that the export carries is derived by check_export_consistency so no
figure is written dead.
"""
import io
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(BASE, "src", "os", "state.json")
EXPORT = os.path.join(BASE, "docs", "status-export.json")
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")

NARRATIVE = (
    "2026-10-28 R2196 (five-silence scan clean at open: decisions.md "
    "251 non-empty rows carrying 172 content-addressed D/C/O tokens "
    "against the stored 170-token baseline, and the two apparent "
    "additions O-20261012-2330 and O-20261026-0735 are the O-family "
    "citations that the group-side rotation restores inside other "
    "seats' rows - neither is a BigDomain execution face, so zero "
    "action and the baseline is re-anchored to the measured 172; the "
    "group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-28 03:0x CEO-PROXY fleet event round "
    "#4, acknowledged with zero domain action; benchmarks refreshed "
    "2026-10-27 inside the seven-day gate; tree clean, no "
    "index.lock) - the P1 canonical rows stay blocked-on-CEO and the "
    "weekly proposal duty is met by BD-PROP-005, all four tech heads "
    "stayed gated (docker host absent, logs toolkit standing "
    "maintenance, member refunded schema product-gated, the "
    "live-mtime row waiting on a real normalized-mtime event) and the "
    "explore head above the seeds is the merchant-gated benchmark "
    "row, so this window claimed the next real seed (R2189 7/10) and "
    "registered AC-BGM1..AC-BGM8 in that queue row BEFORE the code "
    "existed (api_buyer_gap_months, _month_index, "
    "trailing_dormant_months, test_apimarket_buyergapmonths and "
    "ledger-apimarket-buyergapmonths were all git grep -F "
    "zero-occupancy against HEAD 2026-10-28, rc=1; the face name "
    "itself only ever lived in the seed row). Gap statement: "
    "api_buyer_months answers the money in each month and "
    "api_market_buyer_retention the market-wide survival curve, so "
    "the rhythm of ONE resident - how many months passed between two "
    "purchases, how long the longest silence ran, how many months sit "
    "dormant inside the observed extent - had no face, and a regular "
    "repurchase cadence and a sleeping account read identically. "
    "Product: APIMarketFace.api_buyer_gap_months(buyer_id, as_of=None) "
    "- a sixteen-key envelope with four-key gap rows. Activity is the "
    "NET purchase month (the repeat-purchase and retention authority): "
    "a refunded purchase is not a purchase, so a refund REMOVES an "
    "activity month and can widen the silence around it, disclosed "
    "rather than patched over, and a month carrying only refunds is "
    "not an activity month. gap_months counts the EMPTY months "
    "strictly between two consecutive activity months while "
    "span_months counts the pair distance, so gap_months == "
    "span_months - 1 on every row and two consecutive calendar months "
    "read 0 (unbroken rhythm, never absent rhythm); rows are strictly "
    "ascending and chained end to end with count == "
    "activity_month_count - 1. No wall clock is ever read: the "
    "trailing silence is measured against as_of, which defaults to "
    "the buyer's own last activity month (hence 0), and an as_of "
    "preceding the last activity month fails closed, as does the "
    "unpadded / month-13 / month-00 / non-string / trailing-garbage "
    "shape family - all E_AM_BAD_WINDOW after the account gate, so a "
    "bad account never reaches the window gate. Aggregates: "
    "dormant_months_total is the row sum, avg_gap_months an exact "
    "float, median by odd-middle/even-midpoint, max_gap_months with "
    "the EARLIER pair on a tie, and an honest empty world (zeros, None "
    "aggregates, empty rows) for a buyer with no purchase. Suite "
    "src/sandbox/ledger/test_apimarket_buyergapmonths.py: a six-"
    "purchase world across 2026-09/2026-10/2026-12/2027-01/2027-03 "
    "pins the activity law (two purchases in one month collapse to one "
    "activity month, gap_count 4, dormant 2) and then refunds the "
    "December purchase in place, after which the activity months drop "
    "to four, the October..January silence widens from one empty month "
    "to two and the aggregates move with it (gap_count 3, avg 1.0, "
    "median 1, max 2 with the 2026-10 -> 2027-01 pair). SUITE PASS "
    "8/8 double-run rc=0/0 with byte-identical output (747 bytes each, "
    "criterion lines sha16 74c0420f27a6d2b7, evidence "
    "qa/apimarket-buyergapmonths-R2196.log and -run2.log written "
    "through src/os/evidence_writer.py, never a shell redirection), "
    "wired as ledger-apimarket-buyergapmonths(8); five adjacent "
    "buyer-family suites re-ran green (buyermonths, buyerretention, "
    "repeatpurchase, buyerprofile, claimmonths at 8/8 each). Honest "
    "boundary: the first suite attempt failed at the seed step because "
    "the purchase door is unique on (buyer, listing), so the world now "
    "publishes one shelf per purchase - a test-world defect, no "
    "implementation loosened; the full reconcile battery and the "
    "suite-matrix regeneration were NOT run inside this window and are "
    "recorded as R2197 first-item debt.")

TOKENS = ("R2196 tokens: local=~70k api=0 api_reason=five-silence scan "
          "with a two-token rotation re-anchor + explore seed 7/10 claim "
          "with criteria pre-registered before code + buyer purchase-gap "
          "rhythm product face + suite 8/8 double-run byte-identical + "
          "five adjacent buyer-family regressions + state/backlog/export "
          "closeout, zero cloud calls (full battery deferred to R2197 and "
          "recorded as debt)")

BACKLOG_ROW = (
    "- [ ] P2 tech head (R2196 debt): the FULL reconcile battery plus "
    "the suite-matrix regeneration were NOT run inside the R2196 window "
    "(shipping apimarket.py while the battery walks the tree would have "
    "measured a mixed tree) - first item of the next round, on the "
    "committed tree, through src/os/battery_stream.py with the four "
    "follow-up sections (matrix regen/check, fingerprint --chain "
    "--check, runner profile --daily --check, writer census "
    "re-freeze then --check) appended to the same evidence file.\n")


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)
    state["tick"] = 2196
    state["last_decision_rows"] = 251
    state["last_dec_tokens"] = ",".join(sorted(set(
        state["last_dec_tokens"].split(",")) | {
            "O-20261012-2330", "O-20261026-0735"}))
    state["log"].append(NARRATIVE)
    state["log"].append(TOKENS)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    with io.open(BACKLOG, "r", encoding="utf-8", newline="") as handle:
        existing = handle.read()
    if "R2196 debt" not in existing:
        with io.open(BACKLOG, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(BACKLOG_ROW + existing)

    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_export_consistency as C
    derived, _state, _export, pat = C.recompute()
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = ("R2196 " + export["do"].split(":", 1)[-1].strip())
    face = export["ceo_face"]
    face["current"] = (
        "R2196 buyer purchase-gap rhythm: a resident can now read how "
        "many months sat between their own purchases, how long the "
        "longest silence ran and how much of the observed stretch was "
        "dormant - a regular repurchase cadence and a sleeping account "
        "no longer read the same")
    face["latest_artifact"] = (
        "qa/apimarket-buyergapmonths-R2196.log / -run2.log (SUITE PASS "
        "8/8 double-run, 747 bytes each, criterion sha16 "
        "74c0420f27a6d2b7) + src/sandbox/ledger/apimarket.py "
        "(api_buyer_gap_months, written 2026-10-28)")
    face["next_milestone"] = (
        "R2197 runs the full reconcile battery plus suite-matrix "
        "regeneration carried from this window, then claims explore "
        "seed 8/10 (price step distribution) with its criteria "
        "pre-registered first; the P1 commercial rows and the "
        "merchant-number benchmark row stay blocked on CEO physical "
        "items (within 48h)")
    out = (
        "buyer purchase-gap rhythm (api_buyer_gap_months)",
        "on",
        "R2196: api_buyer_months answers the money in each month and "
        "api_market_buyer_retention the market-wide survival curve, so "
        "the rhythm of one resident had no face - a repurchase cadence "
        "and a sleeping account read identically. "
        "api_buyer_gap_months(buyer_id, as_of=None) returns a sixteen-"
        "key envelope with four-key gap rows. Activity is the NET "
        "purchase month: a refunded purchase is not a purchase, so a "
        "refund removes an activity month and widens the silence "
        "around it (never patched over), and a refund-only month is not "
        "an activity month. gap_months counts the empty months strictly "
        "between two consecutive activity months, so gap_months == "
        "span_months - 1 and two consecutive calendar months read 0; "
        "rows are strictly ascending, chained end to end and count == "
        "activity_month_count - 1. No wall clock is read: the trailing "
        "silence is measured against as_of, defaulting to the buyer's "
        "own last activity month, and an as_of before that month or an "
        "unpadded/impossible/non-string month fails closed after the "
        "account gate. Aggregates: dormant_months_total as the row sum, "
        "exact float average, odd-middle/even-midpoint median, max with "
        "the earlier pair on a tie, and an honest empty world. Suite "
        "8/8 double-run byte-identical criterion lines sha16 "
        "74c0420f27a6d2b7, wired ledger-apimarket-buyergapmonths(8); "
        "five adjacent buyer-family suites green.")
    result = (
        "R2196",
        "R2196: five-silence scan clean (251 rows / 172 content tokens "
        "with the two O-family rotation citations re-anchored and zero "
        "BigDomain action; ledger three paid-off patrol rows; group "
        "orders tail unchanged; benchmarks inside the seven-day gate; "
        "tree clean, no index.lock). Product: api_buyer_gap_months with "
        "AC-BGM1..AC-BGM8 pre-registered in the R2189 seed 7/10 row "
        "BEFORE the code - net-purchase activity months, the "
        "gap_months == span_months - 1 law, aggregates with the earlier "
        "tie break, as_of-based trailing silence with no wall clock, the "
        "fail-closed as_of family after the account gate, a pure read "
        "with frozen digests and buyer isolation, and two-restart byte "
        "identity. Evidence: SUITE PASS 8/8 double-run rc=0/0, 747 "
        "bytes each, criterion sha16 74c0420f27a6d2b7, five adjacent "
        "buyer suites green. Honest notes: the first attempt failed in "
        "the test world (the purchase door is unique on buyer+listing, "
        "so one shelf per purchase was published) and the full battery "
        "plus matrix regeneration are R2197 first-item debt.")
    if export["outs"][0][0] != out[0]:
        export["outs"].insert(0, list(out))
    if export["results"][0][0] != result[0]:
        export["results"].insert(0, list(result))
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and \
                row[1] == pat["tick_row_label"]:
            row[0] = str(state["tick"])
    export["self_drive"].update(derived)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")
    print("tick", state["tick"], "log_lines", len(state["log"]),
          "export_ts", export["export_ts"],
          "explore_open", export["self_drive"]["queue_explore_open"],
          "tech_open", export["self_drive"]["queue_tech_open"],
          "results", len(export["results"]))


if __name__ == "__main__":
    main()