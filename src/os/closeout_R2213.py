# -*- coding: utf-8 -*-
"""R2213 closeout: state.json tick/log/watermark and status-export.
Run only after the battery evidence is on disk."""
import io
import json
import os
import re
import datetime

STATE = os.path.join("src", "os", "state.json")
EXPORT = os.path.join("docs", "status-export.json")
DEC = r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md"

ROUND = (
    "2026-10-28 R2213 (five-silence scan clean at open: decisions.md "
    "measured 172 content-addressed D/C/O/T tokens with ZERO new and four "
    "dropped - D-20261006-05, D-20261007-04, D-20261007-05 and "
    "D-20261008-05, the known body-text citations the group-side rotation "
    "drops - so zero domain action and the baseline is re-anchored to the "
    "measured set; the group ledger carries the same @BigDomain patrol rows "
    "already paid off with zero unreplied; the group orders tail is "
    "unchanged at the 2026-10-28 15:01 fleet auto-dispatch "
    "OB-20261028-150100-267, acknowledged as a fleet dispatcher face with "
    "zero domain action; benchmarks refreshed 2026-10-27 inside the "
    "seven-day gate; tree clean, no index.lock; both daily standing rows "
    "for 2026-10-28 were already on disk so neither was re-run) - the P1 "
    "canonical rows stay blocked-on-CEO, the weekly proposal duty is met by "
    "BD-PROP-005, all four tech heads stayed gated (docker host absent, "
    "logs toolkit standing maintenance, member refunded schema "
    "product-gated, the live-mtime row waiting on a real normalized-mtime "
    "event) and the explore queue held only the merchant-gated benchmark "
    "row, so this window reseeded the queue 10/10 (each seed verified "
    "zero-occupancy on three anchors against HEAD by name, suite and runner "
    "label, all rc=1) and claimed the R2213 head in the SAME window, with "
    "criteria AC-BWM1..AC-BWM8 registered in that row BEFORE the code "
    "(AC-BWM, api_buyer_watch_months, test_apimarket_buyerwatchmonths, "
    "ledger-apimarket-buyerwatchmonths, opened_month, net_watch_change, "
    "live_watch_at_month_end and _watch_events all git grep -F rc=1; "
    "watch_month_count was already taken by api_market_watch_months, so "
    "this face avoids that key - one dishonest claim was caught and fixed "
    "in this same window: the criteria first said a seventeen-key envelope "
    "and the measured envelope is fifteen, so both the queue row and the "
    "suite docstring were corrected to fifteen before any evidence was "
    "written). Product: APIMarketFace.api_buyer_watch_months(buyer_id) - "
    "the buyer-side monthly watch flow the family never had (the market "
    "face answers the whole market and the seller face one seller, both "
    "monthly, while a buyer carried only a live category mix and a "
    "lifetime funnel). Fifteen-key envelope and eight-key month rows on the "
    "cash-basis double stamp shared with both siblings (a watch books in "
    "the watched_utc month, an unwatch in the unwatched_utc month, a later "
    "unwatch never rewrites the watch month, so a pure-unwatch month "
    "carries an honestly negative net), a contiguous grid whose zero month "
    "sits next to a month that carried only a PURCHASE (proving purchases "
    "do not book watch rows), and the face's own new axis: the DIRECTIONAL "
    "conversion law - a watch converts only when an unrefunded purchase is "
    "stamped at or after watched_utc, the conversion is booked in the WATCH "
    "month (the same credit-the-leg-to-the-asking-month rule the question "
    "face pins), a purchase made before the watch never converts and a "
    "refunded purchase stops converting. Plus conservation per row and "
    "envelope, the running active_count landing on the live count, "
    "event-derived participants, both peak laws with the earlier-month "
    "tie-break, cross-face identity with api_watchlist, strict buyer "
    "isolation against an identical-looking neighbour and the seven-form "
    "account gate failing closed before any read. Evidence: SUITE PASS 8/8 "
    "double-run byte-identical sha16 5f454d4f3cbdde83 "
    "(qa/apimarket-buyerwatchmonths-R2213.log and -b.log, 810 bytes, single "
    "UTF-8 LF writer after the first attempt leaked the child's CRLF and "
    "was regenerated), wired as ledger-apimarket-buyerwatchmonths(8), six "
    "adjacent watch-family suites green. Product committed as f2123263 and "
    "pushed before the battery so the battery walked a committed tree."
)

SELF_HEAL = (
    "R2213 self-heal check: the BigDomain-OSLoop scheduled task exists and "
    "is Running, but its principal still reads LogonType=Interactive with "
    "RunLevel=Limited, which the 2026-09-29 machine law forbids for every "
    "lane task. src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply it; this session "
    "runs unelevated, so the task was left untouched rather than risk "
    "replacing the definition of the loop hosting this window. Open "
    "local-lane item for an elevated window."
)


def measured_tokens():
    text = io.open(DEC, encoding="utf-8", errors="replace").read()
    toks = set(re.findall(r"\b(?:D|C|O|T|P)-2026\d{4}-\d{2,4}\b", text))
    drops = {"D-20260930-1"}
    return sorted(t for t in toks if t not in drops)


def main(battery_line, battery_pass):
    with io.open(STATE, encoding="utf-8") as fh:
        st = json.load(fh)
    st["tick"] = int(st.get("tick", 0)) + 1
    toks = measured_tokens()
    st["last_dec_tokens"] = ",".join(toks)
    rows = len([l for l in io.open(DEC, encoding="utf-8",
                                   errors="replace").read().split("\n")
                if l.strip()])
    st["last_decision_rows"] = rows
    log = st.setdefault("log", [])
    log.append(ROUND)
    log.append(
        "R2213 tokens: local=~90k api=0 api_reason=five-silence scan + "
        "explore reseed 10/10 with three-anchor dedup + buyer monthly watch "
        "flow product face (directional conversion law booked in the watch "
        "month) + suite 8/8 double-run byte-identical + six adjacent "
        "watch-family regressions + " + battery_line + ", zero cloud calls")
    log.append(SELF_HEAL)
    with io.open(STATE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(st, ensure_ascii=False, indent=2))
        fh.write("\n")

    with io.open(EXPORT, encoding="utf-8") as fh:
        ex = json.load(fh)
    now = datetime.datetime.now().astimezone()
    ex["export_ts"] = now.replace(microsecond=0).isoformat()
    ex["do"] = (
        "R2213 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - the buyer "
        "side now has its own monthly attention timeline, and a watch's "
        "conversion is booked in the month it was watched, so a resident "
        "can read whether interest is heating up and how much of it "
        "actually became a purchase")
    face = ex.setdefault("ceo_face", {})
    face["current"] = (
        "R2213 api_buyer_watch_months(buyer_id): the buyer-side monthly "
        "watch flow - fifteen-key envelope, contiguous grid with an honest "
        "zero month, the directional conversion law (unrefunded purchase at "
        "or after the watch, booked in the WATCH month), both peak laws and "
        "cross-face identity with api_watchlist")
    face["latest_artifact"] = (
        "qa/apimarket-buyerwatchmonths-R2213.log / -b.log (SUITE 8/8, "
        "sha16 5f454d4f3cbdde83, byte-identical double run) + "
        "src/sandbox/ledger/apimarket.py (api_buyer_watch_months, written "
        "2026-10-28 23:2x) + commit f2123263")
    face["last_artifact"] = battery_pass
    face["next_milestone"] = (
        "a fresh explore seed from the ten reseeded rows, plus the suite "
        "matrix regeneration against this battery, within 48h")
    sd = ex.setdefault("self_drive", {})
    sd["queue_explore_open"] = 11
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(ex, ensure_ascii=False, indent=2))
        fh.write("\n")
    print("state tick=%d tokens=%d rows=%d" % (st["tick"], len(toks), rows))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "battery pending",
         sys.argv[2] if len(sys.argv) > 2 else "battery pending")