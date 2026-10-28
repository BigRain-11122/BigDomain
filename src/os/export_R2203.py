"""R2203 closeout: state tick/log, the explore claim row marked done,
the backlog line and the status-export refresh with every counter
machine-derived from state (F3 law). ASCII source."""
import io
import json
import os
import re
import sys
import time

BASE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXPORT = os.path.join(BASE, "docs", "status-export.json")
STATE = os.path.join(BASE, "src", "os", "state.json")
BACKLOG = os.path.join(BASE, "src", "os", "backlog.md")
QUEUE = os.path.join(BASE, "state", "queue", "explore.md")
DECISIONS = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                         "docs", "decisions.md")

NARRATIVE = (
    "2026-10-28 R2203 (five-silence scan clean at open: decisions.md 261"
    " non-empty rows carrying 172 content-addressed D/C/O tokens against"
    " the stored 174-token baseline, with ZERO new - the six absentees"
    " D-20261006-05 / D-20261007-04 / D-20261007-05 / D-20261008-05 /"
    " O-20261012-2330 / O-20261026-0735 are the known body-text"
    " citations the group-side rotation drops, so zero action and the"
    " baseline is re-anchored to the measured 172; the group ledger"
    " carries the same three @BigDomain patrol rows already paid off with"
    " zero unreplied; the group orders tail is unchanged at the"
    " 2026-10-28 15:01 fleet auto-dispatch OB-20261028-150100-267,"
    " acknowledged as a fleet dispatcher face with zero domain action;"
    " benchmarks refreshed 2026-10-27 inside the seven-day gate; tree"
    " clean, no index.lock) - the P1 canonical rows stay blocked-on-CEO,"
    " the weekly proposal duty is met by BD-PROP-005, all four tech heads"
    " stayed gated (docker host absent, logs toolkit standing"
    " maintenance, member refunded schema product-gated, the live-mtime"
    " row waiting on a real normalized-mtime event) and the explore queue"
    " carried eight unclaimed seeds from the R2202 reseed, so this window"
    " claimed its head and registered AC-BRM1..AC-BRM8 in that row BEFORE"
    " the code existed (the AC-BRM prefix, refund_month_count and"
    " refunded_month were git grep -F zero-occupancy against HEAD"
    " 2026-10-28 rc=1; api_buyer_refund_months,"
    " test_apimarket_buyerrefundmonths and"
    " ledger-apimarket-buyerrefundmonths were occupied ONLY by the seed"
    " row that announced them - disclosed). Gap statement:"
    " api_buyer_profile answers lifetime refunded money and count and"
    " api_refund_latency answers the market-wide settlement delay with"
    " one monthly leg, so a resident who returned one purchase in March"
    " and one who churned steadily read identically and the resident's"
    " own refund rhythm had no face. Product:"
    " APIMarketFace.api_buyer_refund_months(buyer_id) - a twenty-one-key"
    " envelope with ten-key month rows. Booking law: a refund books ONLY"
    " in the UTC month of its own refunded_utc, so a September purchase"
    " refunded in October is an October event and September stays an"
    " honest zero month; the month rows are the contiguous grid from the"
    " first to the last refund month, a zero month carries a None average"
    " rather than a fabricated 0.0, and the running accumulator is"
    " carried across those zero months and lands on the envelope count."
    " Money conservation is per row and in the envelope (refunded == dev"
    " + platform, integer split) and is checked against the raw join; the"
    " envelope average is POOLED over every refund (6.25) rather than a"
    " mean of monthly means (6.83); same_month_count is the new"
    " settlement-speed signal; listing_count and seller_count are"
    " distinct, so a month can carry two refunds on two shelves of the"
    " SAME seller (seller_count 1 against refund_count 2) and the"
    " envelope seller_count 2 sits under a row sum of 3 - the disclosed"
    " asymmetry; buyers never leak and the envelope count/money equal"
    " api_buyer_profile; the peak takes the highest month with the"
    " earlier-month tie-break. Suite"
    " src/sandbox/ledger/test_apimarket_buyerrefundmonths.py SUITE PASS"
    " 8/8 on the first run and on the second, evidence byte-identical"
    " (qa/apimarket-buyerrefundmonths-R2203-a.log / -b.log, 911 bytes"
    " each, single-writer utf-8 LF, crlf=0, sha256"
    " d530197188a7ef2b...), wired as"
    " ledger-apimarket-buyerrefundmonths(8); five adjacent refund and"
    " buyer-family suites green (refundlatency / refundreasons /"
    " sellerrefundreasons / categoryrefundmonths / buyerprofile 8/8"
    " each, qa/regression-R2203.log). Honest note: one test-side"
    " arithmetic expectation was wrong on the first run (the envelope"
    " row sum of seller_count is 3, not 4) and was fixed in the TEST,"
    " never by widening the implementation; a second honesty note is that"
    " the evidence files first came out with CRLF because the child"
    " process writes \\r\\n through its stdout pipe, so they were"
    " normalised to LF by a single writer before being adopted - the"
    " class=tee census contract. The full reconcile battery and matrix"
    " regeneration are recorded as the R2204 first item (this window"
    " closed the product face first, per the R2168 mixed-tree rule).")

TOKENS = ("R2203 tokens: local=~80k api=0 api_reason=five-silence scan"
          " with a rotation re-anchor + explore seed claim with criteria"
          " pre-registered before code + buyer-side monthly refund flow"
          " product face + suite 8/8 double-run byte-identical + five"
          " adjacent refund/buyer regressions + state/backlog/queue/export"
          " closeout, zero cloud calls (full battery and matrix carried to"
          " R2204 and recorded as debt)")

CURRENT = ("R2203 buyer-side monthly refund flow: a resident now reads"
           " how much money came back in each month and whether a refund"
           " landed in the purchase month or a later one")

ARTIFACT = ("qa/apimarket-buyerrefundmonths-R2203-a.log / -b.log"
            " (SUITE 8/8, sha256 d530197188a7ef2b..., 911 bytes) +"
            " src/sandbox/ledger/apimarket.py"
            " (api_buyer_refund_months, written 2026-10-28)")

NEXT = ("full reconcile battery plus suite-matrix regeneration on the"
        " committed tree (the R2202 and R2203 carry-over), then the next"
        " explore seed (seller-side monthly watch inflow) with its"
        " criteria registered before the code (within 48h)")

OUT = ("buyer-side monthly refund flow (api_buyer_refund_months)",
       "on",
       "R2203: api_buyer_profile answers lifetime refunded money and"
       " count and api_refund_latency the market-wide settlement delay,"
       " so a resident's own refund rhythm had no face."
       " api_buyer_refund_months(buyer_id) returns a twenty-one-key"
       " envelope with ten-key month rows. A refund books only in the UTC"
       " month of its own refunded_utc, never in the purchase month, so a"
       " September purchase refunded in October is an October event and"
       " September stays an honest zero month. Month rows are the"
       " contiguous grid from the first to the last refund month, a month"
       " with no refund carries a None average rather than a fabricated"
       " zero, and the running accumulator is carried across those zero"
       " months and lands on the envelope count. Money conservation is"
       " per row and in the envelope (refunded equals dev plus platform,"
       " integer split) and is checked against the raw join. The envelope"
       " average is pooled over every refund rather than a mean of"
       " monthly means. same_month_count is the settlement-speed signal"
       " this face adds. listing_count and seller_count are distinct, so"
       " a month can carry two refunds on two shelves of the same seller,"
       " and the envelope distinct count can sit under the row sum -"
       " disclosed rather than smoothed. Buyers never leak into each"
       " other, the envelope count and money equal api_buyer_profile"
       " exactly, the peak takes the highest month with the"
       " earlier-month tie-break, and the account gate fails closed"
       " before any read with the bare usr: prefix reading honestly"
       " empty. Suite 8/8 double-run byte-identical, wired"
       " ledger-apimarket-buyerrefundmonths(8); five adjacent refund and"
       " buyer suites green.")

RESULT = ("R2203",
          "R2203: five-silence scan clean (261 rows / 172 D-C-O tokens,"
          " zero new against the stored 174-token baseline because the"
          " two apparent additions are the rotation-restored O-family"
          " citations inside other seats' rows; ledger patrol rows already"
          " paid; group orders tail unchanged at the 2026-10-28 15:01"
          " fleet dispatch; benchmarks inside the seven-day gate; tree"
          " clean, no index.lock). Product: api_buyer_refund_months with"
          " AC-BRM1..AC-BRM8 registered in the R2203 queue row BEFORE the"
          " code - the refunded_utc booking law that never rewrites the"
          " purchase month, the contiguous grid with honest zero months"
          " carried by the running accumulator, money and split"
          " conservation against the raw join, the pooled average against"
          " a mean of monthly means, the same-month settlement count,"
          " distinct participant counts with the disclosed asymmetry,"
          " cross-face identity with api_buyer_profile and strict buyer"
          " isolation, the earlier-month peak tie-break, and a pure read"
          " with frozen digests and three-instance byte identity. Suite"
          " SUITE PASS 8/8 on both runs with byte-identical evidence"
          " (sha256 d530197188a7ef2b, 911 bytes, crlf=0), wired"
          " ledger-apimarket-buyerrefundmonths(8), five adjacent refund"
          " and buyer suites green. Honest notes: one test-side row-sum"
          " expectation was wrong on the first run and was fixed in the"
          " test, and the evidence was normalised from the child's CRLF"
          " pipe output to LF by a single writer. The full battery and"
          " matrix regeneration were not run in this window and are"
          " R2204's first item.")


def month_claim_done():
    text = io.open(QUEUE, encoding="utf-8").read()
    old = ("- [ ] P3 explore head claim (R2203, seed R2202 row claimed,"
           " criteria AC-BRM1..AC-BRM8")
    if old not in text:
        raise SystemExit("claim row missing")
    text = text.replace(old, "- [x] P3 explore head claim (R2203, seed"
                        " R2202 row claimed, criteria AC-BRM1..AC-BRM8", 1)
    marker = "ledger-apimarket-buyerrefundmonths(8) wiring, ASCII/LF."
    if marker not in text:
        raise SystemExit("claim tail missing")
    text = text.replace(
        marker, marker + " [done 2026-10-28 R2203] SUITE PASS 8/8"
        " double-run byte-identical sha256 d530197188a7ef2b (911 bytes,"
        " crlf=0), five adjacent refund/buyer suites green.", 1)
    io.open(QUEUE, "w", encoding="utf-8", newline="\n").write(text)


def backlog_line():
    text = io.open(BACKLOG, encoding="utf-8").read()
    if "R2203" in text:
        return
    line = ("- [x] P3 explore head claim (R2203, seed R2202 row claimed,"
            " criteria AC-BRM1..AC-BRM8 registered in that queue row"
            " BEFORE the code): apimarket buyer-side monthly refund flow"
            " api_buyer_refund_months(buyer_id) - a refund books only in"
            " the UTC month of its own refunded_utc so the purchase month"
            " is never rewritten, the contiguous grid carries honest zero"
            " months whose average is None with the running accumulator"
            " carried across them, money and integer dev/platform split"
            " conserve against the raw join, the envelope average is"
            " pooled (6.25) rather than a mean of monthly means (6.83),"
            " same_month_count adds the settlement-speed signal, distinct"
            " participant counts disclose the asymmetry (a month with two"
            " refunds on one seller's two shelves reads seller_count 1),"
            " cross-face identity with api_buyer_profile holds, buyers"
            " never leak, the peak takes the earlier month on a tie, and"
            " the face is a pure read. Evidence: SUITE PASS 8/8"
            " double-run byte-identical sha256 d530197188a7ef2b"
            " (qa/apimarket-buyerrefundmonths-R2203-a.log / -b.log, 911"
            " bytes, crlf=0); wired"
            " ledger-apimarket-buyerrefundmonths(8); five adjacent refund"
            " and buyer suites green (qa/regression-R2203.log). [done"
            " 2026-10-28 R2203]\n")
    head = text.split("\n")
    for index, row in enumerate(head):
        if row.startswith("- ["):
            head.insert(index, line.rstrip("\n"))
            break
    io.open(BACKLOG, "w", encoding="utf-8", newline="\n").write(
        "\n".join(head))


def main():
    with io.open(STATE, encoding="utf-8") as handle:
        state = json.load(handle)

    text = io.open(DECISIONS, encoding="utf-8", errors="replace").read()
    toks = set(re.findall(r"[DCO]-2026\d{4}-\d{2,4}", text))
    rows = sum(1 for line in text.splitlines() if line.strip())

    state["tick"] = int(state["tick"]) + 1
    state["last_decision_rows"] = rows
    state["last_dec_tokens"] = ",".join(sorted(toks))
    state["log"].append(NARRATIVE)
    state["log"].append(TOKENS)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    month_claim_done()
    backlog_line()

    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_export_consistency as C
    derived, _state, _export, pat = C.recompute()
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = "R2203 " + export["do"].split(":", 1)[-1].strip()
    face = export["ceo_face"]
    face["current"] = CURRENT
    face["latest_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    if export["outs"][0][0] != OUT[0]:
        export["outs"].insert(0, list(OUT))
    if export["results"][0][0] != RESULT[0]:
        export["results"].insert(0, list(RESULT))
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and \
                row[1] == pat["tick_row_label"]:
            row[0] = str(state["tick"])
    sd = export["self_drive"]
    sd.update(derived)
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")

    with io.open(os.path.join(BASE, "heartbeat.txt"), "w",
                 encoding="ascii", newline="\n") as handle:
        handle.write("2203\n")

    print("tick", state["tick"], "dec_rows", rows, "dec_tokens",
          len(toks), "outs", len(export["outs"]), "results",
          len(export["results"]), "log_lines",
          sd["log_lines_in_window"], "tech_open", sd["queue_tech_open"],
          "explore_open", sd["queue_explore_open"])


if __name__ == "__main__":
    main()