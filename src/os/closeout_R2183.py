"""R2183 closeout: state.json tick/log/watermark, backlog done marker,
explore-queue done marker, heartbeat, and the status-export refresh
(all derived from the round facts this script was written for).
Pure ASCII source, single utf-8 LF writer.
"""

import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GROUP = os.path.abspath(os.path.join(BASE, "..", ".."))

ROUND_LINE = (
    "R2183 (five-silence scan clean at open: the group ledger carries "
    "the same three @BigDomain patrol rows with zero unreplied; "
    "decisions.md reads 240 non-empty rows carrying 159 content-addressed "
    "D/C tokens against a stored 163-token baseline - ZERO new and four "
    "present-but-absent tokens D-20261006-05 / D-20261007-04 / "
    "D-20261007-05 / D-20261008-05, all body-text citations inside other "
    "seats' rows already acknowledged in R2181, so zero domain action and "
    "the baseline is re-anchored to the measured 159; the group orders "
    "tail is unchanged at the 2026-10-28 03:0x CEO-PROXY event round #4, "
    "acknowledged with zero domain action; benchmarks refreshed 2026-10-27 "
    "inside the seven-day gate; tree clean, no index.lock) - this window "
    "FIRST discharged the debt R2182 recorded and THEN shipped the next "
    "explore seed. Debt: the full reconcile battery ran on the current "
    "tree and passed cleanly on the second invocation - the first was "
    "cancelled by the five-minute no-output rule because its output was "
    "piped through a truncating selector; the ownership check found no "
    "surviving python child and no partial evidence file (zero loss, "
    "nothing to clean) - RUNNER PASS 380/380 suites green plus reconcile "
    "controls 7/7 in 660.8s (qa/reconcile-all-R2183.log, single-writer "
    "utf-8 LF through src/os/battery_stream.py), with the birth-site sweep "
    "inside the same battery window reclaiming 851 of 851 candidate worlds, "
    "302.22 MiB, busy=0 failed=0. Four post-battery sections then all "
    "passed in the new helper src/os/battery_followup_R2183.py and were "
    "appended to the same log: matrix regenerated to 380 suites / 3162 "
    "criteria and read back byte-identical (docs/sandbox-suite-matrix.md, "
    "36753 bytes, green=380/380), fingerprint --chain --check CLEAN over "
    "five domains, runner profile --daily --check PASS, and the qa writer "
    "census re-frozen then re-read DRIFT-CLEAN files=1999 tee=1471 "
    "baselined=528 disappeared=0 flags=0. Product: the next explore seed "
    "(R2178 5/10) with AC-WBG1..AC-WBG8 registered in that queue row BEFORE "
    "the code (the AC-WBG prefix and this suite name were git grep -F "
    "zero-occupancy rc=1 on 2026-10-28; the face name api_watch_budget "
    "appeared only as a text pointer in src/os/closeout_R2182.py, so the "
    "code face was untouched) - the buyer watchlist BUDGET face. Gap "
    "statement: api_watchlist answers which rows a resident watches and "
    "api_watch_alerts answers what happened to them, so the question a "
    "budget review actually asks - what would it cost me to take the whole "
    "watchlist, and how much has it already dropped since I saved it - had "
    "no face at all. Product: APIMarketFace.api_watch_budget(buyer_id) - a "
    "fourteen-key envelope with ten-key rows derived from the live watches "
    "only, one bucket per row in a pinned precedence (purchased > delisted "
    "> sold_out > buyable) whose four counts sum to watch_count; spend "
    "authority is the buyable bucket alone (total, min, max with a "
    "listing_id tie-break, and an avg that is None rather than a fabricated "
    "zero on an empty bucket); savings_from_drops sums max(0, "
    "price_at_watch - current) over the buyable rows only, so a rise "
    "elsewhere never nets a genuine drop down, while a row in another "
    "bucket still reports its own saved figure and contributes nothing; "
    "rows are a total order on (current_price, listing_id); cross-face "
    "identity with api_watchlist (watch_count and the purchased flag), "
    "retirement flipping a shelf into the delisted bucket in the same step, "
    "unwatch removing a row and a re-watch returning with a new watch_id, "
    "strict buyer isolation, the prefix-only account gate before any read, "
    "frozen table digests with a constant ledger_tx set, and byte identity "
    "across three instances after restarts. SUITE PASS 8/8 double-run "
    "byte-identical criterion sha256 19d87a47cd089df6 (evidence "
    "qa/apimarket-watchbudget-R2183-a.log and -b.log, 905B each, "
    "single-writer utf-8 LF), wired as ledger-apimarket-watchbudget(8), "
    "four adjacent suites green (watchlist / watchalerts / "
    "watchconversion / listingdemand, qa/regression-R2183.log). Honest "
    "notes: (a) AC-WBG7's first draft claimed a refund pulls a bought "
    "watch back into the buyable bucket; the run proved the purchase row "
    "survives a refund and a re-purchase is refused by E_AM_PURCHASE_DUP, "
    "so the bucket follows purchase existence exactly like api_watchlist's "
    "purchased flag - the criterion was corrected to the measured seam and "
    "the implementation was not widened; (b) the full battery was run on "
    "the tree BEFORE this product slice, so the new suite is covered by its "
    "own eight criteria plus the four regressions and a fresh battery "
    "including it is recorded as R2184's first item; (c) the battery log "
    "needed the routine newline-axis normalisation from evidence_writer "
    "--fix before the census read DRIFT-CLEAN (720682 bytes, crlf=0, every "
    "line's content preserved).")

TOKEN_LINE = (
    "R2183 tokens: local=~95k api=0 api_reason=five-silence scan + full "
    "reconcile battery 380/380 with controls 7/7 + four-section follow-up "
    "(matrix regen to 380/3162, fingerprint, profile, writer census) + "
    "watch-budget product face with suite 8/8 double-run + four adjacent "
    "regressions + evidence newline repair + state/backlog/queue/export "
    "closeout, zero cloud calls")

DONE_NOTE = (
    " [done 2026-10-28 R2183] Product=apimarket.py "
    "api_watch_budget(buyer_id): fourteen-key envelope, ten-key rows, "
    "pinned bucket precedence (purchased > delisted > sold_out > buyable) "
    "with the four counts summing to watch_count, spend authority on the "
    "buyable bucket only (avg None instead of a fabricated zero), "
    "savings_from_drops summing max(0, price_at_watch - current) over "
    "buyable rows only so a rise never nets a drop down, total order on "
    "(current_price, listing_id), cross-face identity with api_watchlist, "
    "retirement and unwatch flips, buyer isolation, prefix account gate "
    "before any read, frozen table digests, three-instance byte identity. "
    "Suite SUITE PASS 8/8 double-run byte-identical criterion sha256 "
    "19d87a47cd089df6 (qa/apimarket-watchbudget-R2183-a.log and -b.log, "
    "905B each, single-writer utf-8 LF); wired "
    "ledger-apimarket-watchbudget(8); four adjacent suites green "
    "(qa/regression-R2183.log). Same-window debt clearance: full battery "
    "RUNNER PASS 380/380 + controls 7/7 660.8s (qa/reconcile-all-R2183.log) "
    "with matrix 380/3162 byte-identical, fingerprint CLEAN, profile PASS, "
    "census DRIFT-CLEAN flags=0. Honest notes: AC-WBG7's refund clause was "
    "corrected to the measured purchase seam (a refunded purchase row "
    "survives and re-purchase is refused by DUP), not widened in code; the "
    "battery predates this product slice, so a fresh battery including the "
    "new suite is R2184's first item.")


def live_tokens():
    text = io.open(os.path.join(GROUP, "docs", "decisions.md"),
                   encoding="utf-8").read()
    tokens = set(re.findall(r"\b[DC]-\d{8}-\d+\b", text))
    return sorted(tokens)


def nonempty_rows():
    path = os.path.join(GROUP, "docs", "decisions.md")
    rows = io.open(path, encoding="utf-8").read().split("\n")
    return sum(1 for line in rows if line.strip())


def queue_open(path):
    text = io.open(path, encoding="utf-8").read()
    return sum(1 for line in text.split("\n") if line.startswith("- [ ]"))


def main():
    spath = os.path.join(BASE, "src", "os", "state.json")
    state = json.loads(open(spath, "rb").read().decode("utf-8"))
    state["tick"] = int(state["tick"]) + 1
    state["log"].append(ROUND_LINE)
    state["log"].append(TOKEN_LINE)
    tokens = live_tokens()
    state["last_dec_tokens"] = ",".join(tokens)
    state["last_decision_rows"] = nonempty_rows()
    with io.open(spath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    bpath = os.path.join(BASE, "src", "os", "backlog.md")
    btext = io.open(bpath, encoding="utf-8").read()
    row = ("- [x] P3 explore head claim (R2183, seed R2178 5/10, criteria "
           "AC-WBG1..AC-WBG8 registered in state/queue/explore.md BEFORE "
           "the code): apimarket watchlist budget face api_watch_budget."
           + DONE_NOTE + "\n")
    head = "- [x] P3 explore"
    assert btext.count(head) >= 1, "no done row anchor"
    first_nl = btext.index("\n")
    btext = btext[:first_nl + 1] + row + btext[first_nl + 1:]
    io.open(bpath, "w", encoding="utf-8", newline="\n").write(btext)

    qpath = os.path.join(BASE, "state", "queue", "explore.md")
    qtext = io.open(qpath, encoding="utf-8").read()
    stale = "- [ ] P3 explore seed (R2178 seed 5/10"
    if stale not in qtext:
        # the row text is Chinese; match on the stable ASCII prefix
        stale = "- [ ] P3 explore"
        prefix_end = qtext.index("api_watch_budget")
        start = qtext.rindex("\n- [ ] P3 explore", 0, prefix_end) + 1
        line_end = qtext.index("\n", prefix_end)
        qtext = (qtext[:start] + qtext[start:line_end]
                 .replace("- [ ] P3 explore", "- [x] P3 explore", 1)
                 + DONE_NOTE + qtext[line_end:])
    else:
        qtext = qtext.replace(stale, "- [x] P3 explore seed (R2178 seed 5/10",
                              1)
    io.open(qpath, "w", encoding="utf-8", newline="\n").write(qtext)

    epath = os.path.join(BASE, "docs", "status-export.json")
    export = json.loads(open(epath, "rb").read().decode("utf-8"))
    export["export_ts"] = "2026-10-28T21:40:00+08:00"
    export["do"] = (
        "R2183 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - a resident "
        "can now price a whole watchlist: what the buyable shelves would "
        "cost together, which shelves are already bought, retired or sold "
        "out, and how much the saved ones have dropped since the watch")
    export["ceo_face"] = {
        "current": (
            "R2183: shipped api_watch_budget - a fourteen-key budget "
            "reading over the live watchlist with one bucket per row "
            "(purchased / delisted / sold_out / buyable), spend authority "
            "on the buyable bucket alone, and savings that never net a "
            "price rise against a genuine drop (suite 8/8 double-run "
            "byte-identical, four neighbours green); the R2182 battery "
            "debt is cleared as well (380/380 suites, matrix 380/3162 "
            "byte-identical, census DRIFT-CLEAN)"),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py (api_watch_budget) + "
            "src/sandbox/ledger/test_apimarket_watchbudget.py + "
            "qa/apimarket-watchbudget-R2183-a.log and -b.log (SUITE PASS "
            "8/8, sha256 19d87a47...) + qa/reconcile-all-R2183.log "
            "(RUNNER PASS 380/380) - 2026-10-28"),
        "next_milestone": (
            "R2184: fresh full battery including the new watch-budget "
            "suite, then the next explore seed (R2178 6/10, "
            "api_market_ticket_size - achieved ticket-size distribution) - "
            "ETA 2026-10-29, within 48h"),
        "last_artifact": (
            "qa/apimarket-watchbudget-R2183-a.log (SUITE PASS 8/8, "
            "double-run byte-identical) (2026-10-28)")}
    export["results"].append(["R2183", (
        "R2183: five-silence scan clean with zero new decision tokens "
        "(baseline re-anchored 163->159) and no new orders. Debt cleared: "
        "battery RUNNER PASS 380/380 + controls 7/7 660.8s with matrix "
        "380/3162 byte-identical, fingerprint CLEAN, profile PASS, census "
        "DRIFT-CLEAN. Product: api_watch_budget with AC-WBG1..AC-WBG8 "
        "pre-registered before the code, SUITE PASS 8/8 double-run "
        "byte-identical (sha256 19d87a47cd089df6), wired as "
        "ledger-apimarket-watchbudget(8), four adjacent suites green. "
        "Honest notes: the AC-WBG7 refund clause was corrected to the "
        "measured purchase seam, and a fresh battery including the new "
        "suite is recorded as R2184's first item.")])
    if len(export["results"]) > 12:
        del export["results"][0]
    sd = export["self_drive"]
    sd["log_lines_in_window"] = sd["log_lines_in_window"] + 2
    sd["substantive_non_idle_mention_lines"] = (
        sd["substantive_non_idle_mention_lines"] + 2)
    sd["queue_explore_open"] = queue_open(qpath)
    sd["queue_tech_open"] = queue_open(
        os.path.join(BASE, "state", "queue", "tech.md"))
    with io.open(epath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(export, ensure_ascii=False, indent=2))
        handle.write("\n")

    hpath = os.path.join(BASE, "heartbeat.txt")
    with io.open(hpath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("%d\n" % state["tick"])

    print("state tick=%d tokens=%d rows=%d explore_open=%d tech_open=%d"
          % (state["tick"], len(tokens), state["last_decision_rows"],
             sd["queue_explore_open"], sd["queue_tech_open"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())