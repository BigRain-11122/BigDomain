"""R2212 closeout: state tick/log, heartbeat, backlog, queue done marker
and the derived status export, all through in-process writers (utf-8 LF).

The export self_drive block is recomputed with the canonical caliber by
importing src/os/check_export_consistency.py rather than by hand, so the
flush and the checker cannot drift apart (the two-caliber lesson).
"""
import datetime
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import check_export_consistency as C   # noqa: E402

P_STATE = os.path.join(ROOT, "src", "os", "state.json")
P_EXPORT = os.path.join(ROOT, "docs", "status-export.json")
P_BACKLOG = os.path.join(ROOT, "src", "os", "backlog.md")
P_EXPLORE = os.path.join(ROOT, "state", "queue", "explore.md")
P_HEART = os.path.join(ROOT, "heartbeat.txt")

HEADLINE = (
    "2026-10-28 R2212 (five-silence scan clean at open: decisions.md "
    "measured 174 content-addressed D/C tokens with zero new and zero "
    "dropped, so zero domain action and the baseline stands unchanged; the "
    "group ledger carries the same three @BigDomain patrol rows already "
    "paid off with zero unreplied; the group orders tail is unchanged at "
    "the 2026-10-28 15:01 fleet auto-dispatch OB-20261028-150100-267, "
    "acknowledged as a fleet dispatcher execution face with zero domain "
    "action; benchmarks refreshed 2026-10-27 inside the seven-day gate; "
    "tree clean, no index.lock) - the P1 canonical rows stay blocked-on-CEO, "
    "all four tech heads stayed gated (docker host absent, logs toolkit "
    "standing maintenance, member refunded schema product-gated, the "
    "live-mtime row waiting on a real normalized-mtime event) and the "
    "explore queue head was the last open R2202 seed, so this window "
    "claimed it after an anchor check (AC-FMD, test_apimarket_feedmonths, "
    "ledger-apimarket-feedmonths, feed_month_count and monthly_event all "
    "git grep -F rc=1; the face name appeared only in queue, state and docs "
    "prose) and registered AC-FMD1..AC-FMD8 in that row BEFORE the code: "
    "api_market_feed_months, the monthly activity-volume timeline over the "
    "merged feed. Gap: the feed answers what just happened as one flat "
    "ordered stream behind a window filter, so the shape of activity over "
    "months could only be counted by hand, and every shipped month face "
    "reads a single family. Product: a seventeen-key envelope with six-key "
    "month rows; each event books in the month of its own immutable stamp "
    "and a revision is its own event in its own month; the contiguous grid "
    "carries an honest zero month with an empty by_kind and a flat running "
    "total; conservation holds three ways; the peak takes the earlier month "
    "and the module-pinned feed rank on a family tie; the window, kinds and "
    "seller filters compose exactly as the feed does; the gate chain is the "
    "feed's own, fail-closed before any read; and event_total equals "
    "api_market_feed(...)[total] by construction. Evidence: SUITE PASS 8/8 "
    "double-run byte-identical sha256 "
    "81bfdc06e8cf58e2e9382d6213ed37c40d71ca985d2ec2f061716fae94dd5a6e "
    "(qa/apimarket-feedmonths-R2212-a.log and -b.log, 1014 bytes each, "
    "single-writer utf-8 LF, criterion sha16 6302771e7382633c); wired "
    "ledger-apimarket-feedmonths(8); nine adjacent feed/month/stats suites "
    "green (qa/regression-R2212.log). Honest gap: the full reconcile "
    "battery and the suite-matrix regeneration were NOT run inside the "
    "25-minute window (the R2168 mixed-tree rule plus budget) and are "
    "recorded as the R2213 first item; the explore queue is also down to "
    "one open row (the merchant-gated benchmark row), so the next window "
    "must reseed before it can claim again.")

LEDGER = ("R2212 tokens: local=~60k api=0 api_reason=explore claim with "
          "criteria registered before the code, one new product face with "
          "an eight-criterion suite double-run to byte-identical evidence, "
          "nine adjacent regression suites, plus queue/backlog/state/export "
          "closeout; zero cloud calls; the full battery deferred")

SELFHEAL = (
    "R2212 self-heal check: the BigDomain-OSLoop scheduled task exists and "
    "is Running, but its principal still reads LogonType=Interactive with "
    "RunLevel=Limited, which the 2026-09-29 machine law forbids for every "
    "lane task. src/os/register_loop_task.ps1 already passes an explicit "
    "S4U principal and needs an elevated shell to apply it; this session "
    "runs unelevated, so the task was left untouched rather than risk "
    "replacing the definition of the loop hosting this window. Open "
    "local-lane item for an elevated window.")

BACKLOG_ROW = (
    "- [x] P3 explore head claim (R2212, seed R2202 8/8, criteria "
    "AC-FMD1..AC-FMD8 registered in the claim row BEFORE the code after a "
    "zero-occupancy anchor check): apimarket monthly activity-volume "
    "timeline api_market_feed_months(since_utc, until_utc, kinds, "
    "dev_account) over the merged eleven-family feed. Product: every event "
    "books in the month of its own immutable stamp and a revision is its "
    "own event; the contiguous grid carries an honest zero month; family "
    "counts, monthly totals and envelope totals conserve three ways; the "
    "peak takes the earlier month and the pinned feed rank on a family tie; "
    "window, kinds and seller filters compose as the feed does; the gate "
    "chain is the feed's own and fail-closed before any read; event_total "
    "equals api_market_feed(...)[total] by construction. Evidence: SUITE "
    "PASS 8/8 double-run byte-identical sha256 81bfdc06e8cf58e2e9382d6213e"
    "d37c40d71ca985d2ec2f061716fae94dd5a6e (qa/apimarket-feedmonths-R2212-a"
    ".log / -b.log, criterion sha16 6302771e7382633c), wired "
    "ledger-apimarket-feedmonths(8), nine adjacent suites green "
    "(qa/regression-R2212.log). Honest gap: full battery and matrix "
    "regeneration deferred to R2213. [done 2026-10-28 R2212]")

EXPLORE_DONE = (
    " [done 2026-10-28 R2212] Product=api_market_feed_months: seventeen-key "
    "envelope, six-key month rows, booking law per event stamp, contiguous "
    "grid with an honest zero month, three-way conservation, earlier-month "
    "peak and pinned-rank family tie-break, window/kinds/seller filters "
    "composed as the feed, cross-face identity by construction, pure read. "
    "Evidence: SUITE PASS 8/8 double-run byte-identical sha256 "
    "81bfdc06e8cf58e2e9382d6213ed37c40d71ca985d2ec2f061716fae94dd5a6e "
    "(qa/apimarket-feedmonths-R2212-a.log / -b.log, criterion sha16 "
    "6302771e7382633c); wired ledger-apimarket-feedmonths(8); nine adjacent "
    "suites green (qa/regression-R2212.log); full battery deferred to R2213.")


def read_text(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def main():
    with io.open(P_STATE, encoding="utf-8") as handle:
        state = json.load(handle)

    state["tick"] = int(state["tick"]) + 1
    state.setdefault("log", []).extend([HEADLINE, LEDGER, SELFHEAL])
    write_text(P_STATE, json.dumps(state, indent=2, ensure_ascii=False)
               + "\n")

    # Recompute AFTER the state write so the flush caliber sees this
    # round's own log lines (the two-caliber lesson).
    derived, state, export, pat = C.recompute()

    write_text(P_HEART, "%d\n" % state["tick"])

    backlog = read_text(P_BACKLOG)
    if BACKLOG_ROW not in backlog:
        write_text(P_BACKLOG, BACKLOG_ROW + "\n" + backlog)

    explore = read_text(P_EXPLORE)
    head = "- [ ] P3 explore head claim (R2212"
    if head in explore:
        explore = explore.replace(head, "- [x] P3 explore head claim (R2212",
                                  1)
        marker = "as ledger-apimarket-feedmonths(8).\n"
        if marker in explore:
            explore = explore.replace(marker,
                                      "as ledger-apimarket-feedmonths(8)."
                                      + EXPLORE_DONE + "\n", 1)
        write_text(P_EXPLORE, explore)

    export["export_ts"] = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=8))
    ).replace(microsecond=0).isoformat()
    export["do"] = (
        "R2212 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - the market now "
        "has a monthly activity-volume timeline over all eleven event "
        "families, so a burst month and a quiet month are one call apart "
        "instead of a hand merge")
    export["ceo_face"] = {
        "current": (
            "R2212 api_market_feed_months(): the monthly activity-volume "
            "timeline over the merged feed - every event books in the month "
            "of its own immutable stamp, the grid is contiguous with honest "
            "zero months, family counts conserve three ways, and the total "
            "is byte-equal to the feed's own total"),
        "latest_artifact": (
            "qa/apimarket-feedmonths-R2212-a.log / -b.log (SUITE 8/8, "
            "sha256 81bfdc06e8cf58e2..., byte-identical double run) + "
            "qa/regression-R2212.log (nine adjacent suites 8/8) + "
            "src/sandbox/ledger/apimarket.py (api_market_feed_months, "
            "written 2026-10-28 22:5x)"),
        "next_milestone": (
            "the full reconcile battery plus the suite-matrix regeneration "
            "on the committed R2212 tree (verification debt), and a fresh "
            "explore reseed because only one gated row remains, within 48h"),
        "last_artifact": (
            "qa/reconcile-all-R2211.log (RUNNER PASS 404/404 suites green + "
            "controls 7/7 in 980.0s, 744224 bytes after the four follow-up "
            "sections) + docs/sandbox-suite-matrix.md (404 suites / 3354 "
            "criteria, 39296 bytes, green=404/404) + "
            "src/os/battery_followup_R2211.py"),
    }
    export["self_drive"].update(derived)
    export["outs"].insert(0, [
        "monthly activity-volume timeline (api_market_feed_months)", "on",
        "R2212: the feed answered what just happened as one flat stream "
        "behind a window, so the shape of activity over months was only "
        "countable by hand and every shipped month face read a single "
        "family. The new face merges all eleven families onto the month "
        "axis: seventeen-key envelope, six-key month rows, a revision as "
        "its own event in its own month, a contiguous grid with honest zero "
        "months and a flat accumulator, three-way conservation, the "
        "earlier-month peak and the pinned-rank family tie-break, the "
        "window and kinds and seller filters composed as the feed, the same "
        "fail-closed gate chain, and event_total byte-equal to the feed's "
        "total by construction. SUITE PASS 8/8 double-run byte-identical "
        "sha256 81bfdc06e8cf58e2..., wired ledger-apimarket-feedmonths(8), "
        "nine adjacent suites green."])
    export["results"].append([
        "R2212",
        "R2212: five-silence scan clean with the decision baseline an exact "
        "174-token match and zero new rows, so zero domain action. Product: "
        "api_market_feed_months with AC-FMD1..AC-FMD8 registered before the "
        "code, SUITE PASS 8/8 double-run byte-identical (sha256 "
        "81bfdc06e8cf58e2e9382d6213ed37c40d71ca985d2ec2f061716fae94dd5a6e), "
        "wired as ledger-apimarket-feedmonths(8), nine adjacent suites "
        "green. Full battery NOT run this window and recorded as the R2213 "
        "first item."])
    label = pat["tick_row_label"]
    for row in export["results"]:
        if isinstance(row, list) and len(row) >= 2 and row[1] == label:
            row[0] = str(state["tick"])
    write_text(P_EXPORT, json.dumps(export, indent=1, ensure_ascii=False)
               + "\n")

    print("closeout: tick=%d export_ts=%s outs=%d results=%d "
          "self_drive_window=%s"
          % (state["tick"], export["export_ts"], len(export["outs"]),
             len(export["results"]), derived["window"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())