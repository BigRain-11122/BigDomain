"""R2200 closeout: state tick/log, then the status-export refresh with
every counter machine-derived from state (F3 law). ASCII source."""
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
DECISIONS = os.path.join(os.path.dirname(os.path.dirname(BASE)),
                         "docs", "decisions.md")

NARRATIVE = (
    "2026-10-28 R2200 (five-silence scan clean at open: decisions.md 251"
    " non-empty rows carrying 172 content-addressed D/C/O tokens against"
    " the stored baseline, and the two apparent additions"
    " O-20261012-2330 and O-20261026-0735 are the O-family citations the"
    " group-side rotation restores inside other seats' rows - neither is"
    " a BigDomain execution face, so zero action and the baseline is"
    " re-anchored to the measured 172; the group ledger carries the same"
    " three @BigDomain patrol rows already paid off with zero unreplied;"
    " the group orders tail is unchanged at the 2026-10-28 15:01 fleet"
    " auto-dispatch OB-20261028-150100-267, acknowledged as a fleet"
    " dispatcher face with zero domain action; benchmarks refreshed"
    " 2026-10-27 inside the seven-day gate; tree clean, no index.lock) -"
    " the P1 canonical rows stay blocked-on-CEO and the weekly proposal"
    " duty is met by BD-PROP-005, all four tech heads stayed gated"
    " (docker host absent, logs toolkit standing maintenance, member"
    " refunded schema product-gated, the live-mtime row waiting on a real"
    " normalized-mtime event) and the explore head above the seeds is the"
    " merchant-gated benchmark row, so this window claimed the last two"
    " real seeds' head (R2189 9/10) and registered AC-MRM1..AC-MRM8 in"
    " that queue row BEFORE the code existed (the AC-MRM prefix,"
    " api_market_relist_months, test_apimarket_marketrelistmonths,"
    " ledger-apimarket-marketrelistmonths and running_delist were all"
    " git grep -F zero-occupancy against HEAD 2026-10-28, rc=1). Product:"
    " APIMarketFace.api_market_relist_months - the market-wide monthly"
    " retirement / re-listing timeline. Gap statement: api_relist_gap"
    " answers one listing's retirement-to-return interval under the"
    " pairing law, api_listing_lifecycle answers the raw open/close event"
    " rows and api_market_months answers cash, so 'how many shelves left"
    " the market this month, how many came back, and is the return rate"
    " deteriorating' had no face, and a return-heavy delisting wave read"
    " identically to a seasonal rotation. The face runs the same"
    " cash-basis double stamp the trade months use (a delisting books in"
    " the UTC month of its own delisted_utc, a re-listing in the UTC"
    " month of its own relisted_utc, so a December return never rewrites"
    " the October month the shelf left in), lays month rows on the"
    " contiguous grid from the first to the last event month so a"
    " zero-event month carries an honest row, reports relist_rate as the"
    " SAME-MONTH FLOW RATIO with None instead of a fabricated zero on a"
    " pure-return month (pairing one delisting with one re-listing stays"
    " api_relist_gap's job, disclosed rather than hidden), derives"
    " everything from the rows (two monotone running accumulators landing"
    " exactly on the envelope totals), counts participants per month"
    " against lifetime distinct in the envelope, and takes the peaks with"
    " the earlier-month tie-break so an empty world reports None instead"
    " of inventing a month. Suite src/sandbox/ledger/"
    "test_apimarket_marketrelistmonths.py SUITE PASS 8/8 on the first run"
    " and on the second, evidence byte-identical (qa/"
    "apimarket-marketrelistmonths-R2200-a.log / -b.log, 655 bytes each,"
    " single-writer utf-8 LF, crlf=0, sha256 aa34b84df93acf93, criterion"
    " sha16 6b74f063474a408f), wired as"
    " ledger-apimarket-marketrelistmonths(8); five adjacent suites green"
    " (relistgap / listingvelocity / marketmonths / marketwatchmonths /"
    " categoryvelocitymonths 8/8 each); the cross-face check pins three"
    " closed gaps plus one pending equal to the four delistings, which is"
    " exactly the relist count plus the open cycle. Honest note: the full"
    " reconcile battery and the suite-matrix regeneration were NOT run"
    " inside this 25-minute window - shipping apimarket.py while the"
    " battery walks the tree would have measured a mixed tree (the R2168"
    " rule) - so they are recorded as the first item of R2201.")

TOKENS = ("R2200 tokens: local=~75k api=0 api_reason=five-silence scan"
          " with a two-token rotation re-anchor + explore seed 9/10 claim"
          " with criteria pre-registered before code + market-wide monthly"
          " retirement/re-listing timeline product face + suite 8/8"
          " double-run byte-identical + five adjacent regressions +"
          " state/export closeout, zero cloud calls (full battery deferred"
          " to R2201 and recorded as debt)")

CURRENT = ("R2200 market-wide retirement timeline: the market now reads"
           " how many shelves left and how many came back each month,"
           " with the return rate honestly empty on a pure-return month")
ARTIFACT = ("qa/apimarket-marketrelistmonths-R2200-a.log / -b.log"
            " (SUITE 8/8, sha256 aa34b84df93acf93, criterion sha16"
            " 6b74f063474a408f) + src/sandbox/ledger/apimarket.py"
            " (api_market_relist_months, written 2026-10-28)")
NEXT = ("full reconcile battery and suite-matrix regeneration carried"
        " from this window, then explore seed 10/10 (seller price cadence"
        " months) with its criteria pre-registered first (within 48h)")

OUT = ("market-wide retirement / re-listing timeline"
       " (api_market_relist_months)",
       "on",
       "R2200: api_relist_gap answers one listing's retirement-to-return"
       " interval and api_market_months answers cash, so the market"
       " carried no monthly view of how many shelves left and how many"
       " came back. api_market_relist_months() returns a fifteen-key"
       " envelope with seven-key month rows on the same cash-basis double"
       " stamp the trade months use: a delisting books in the UTC month"
       " of its own delisted_utc and a re-listing in the UTC month of its"
       " own relisted_utc, so a later return never rewrites the month the"
       " shelf left in. Month rows are the contiguous grid from the first"
       " to the last event month, so a zero-event month carries an honest"
       " row; relist_rate is the same-month flow ratio with None instead"
       " of a fabricated zero when a month carries no delisting (pairing"
       " one delisting with one re-listing stays api_relist_gap's job,"
       " and that asymmetry is disclosed); net_count is delist minus"
       " relist and may honestly be negative; two monotone running"
       " accumulators land exactly on the envelope totals; seller_count"
       " and listing_count are the distinct participants behind that"
       " month's events while the envelope carries lifetime distinct; and"
       " the peaks take the highest monthly count with ties resolved to"
       " the earlier month, so an empty world reports None instead of"
       " inventing one. No arguments, so no gate: pure read, frozen table"
       " digests, constant ledger_tx, and three-instance byte identity"
       " after restarts. Suite 8/8 double-run byte-identical, wired"
       " ledger-apimarket-marketrelistmonths(8); five adjacent shelves"
       " suites green.")

RESULT = ("R2200",
          "R2200: five-silence scan clean (251 rows / 172 D-C-O tokens,"
          " the two apparent additions being the rotation-restored"
          " O-family citations inside other seats' rows, baseline"
          " re-anchored; ledger patrol rows already paid; group orders"
          " tail unchanged at the 2026-10-28 15:01 fleet dispatch;"
          " benchmarks inside the seven-day gate; tree clean, no"
          " index.lock). Product: api_market_relist_months with"
          " AC-MRM1..AC-MRM8 registered in the R2189 seed 9/10 queue row"
          " BEFORE the code - cash-basis double stamp that never rewrites"
          " the delisting month, the contiguous grid with an honest zero"
          " month, the same-month flow ratio that stays None on a"
          " pure-return month, conservation against the raw tables and"
          " the two running accumulators, event-derived participants, the"
          " earlier-month peak tie-break, cross-face identity with"
          " api_relist_gap (three closed gaps plus one pending equal to"
          " the four delistings), and a pure read with frozen digests,"
          " constant ledger_tx and three-instance byte identity. Suite"
          " SUITE PASS 8/8 on both runs with byte-identical evidence"
          " (sha256 aa34b84df93acf93), wired"
          " ledger-apimarket-marketrelistmonths(8), five adjacent suites"
          " green. Honest note: the full battery and matrix regeneration"
          " were not run in this window and are R2201's first item.")


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

    with io.open(EXPORT, encoding="utf-8") as handle:
        export = json.load(handle)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import check_export_consistency as C
    derived, _state, _export, pat = C.recompute()
    export["export_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    export["do"] = "R2200 " + export["do"].split(":", 1)[-1].strip()
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
        handle.write("2200\n")

    print("tick", state["tick"], "dec_rows", rows, "dec_tokens",
          len(toks), "outs", len(export["outs"]), "results",
          len(export["results"]), "log_lines",
          sd["log_lines_in_window"], "tech_open", sd["queue_tech_open"],
          "explore_open", sd["queue_explore_open"])


if __name__ == "__main__":
    main()