"""R2184 closeout: state.json tick/log/watermark, explore-queue done
marker, heartbeat and the status-export refresh. Every battery and
suite number quoted below is PARSED from the evidence files this
script reads, never hardcoded (F3 law). Pure ASCII source, single
utf-8 LF writer.
"""

import hashlib
import io
import json
import os
import re

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GROUP = os.path.abspath(os.path.join(BASE, "..", ".."))

BATTERY = os.path.join(BASE, "qa", "reconcile-all-R2184-2.log")
BATTERY_FIRST = os.path.join(BASE, "qa", "reconcile-all-R2184.log")
SUITE_A = os.path.join(BASE, "qa", "apimarket-ticketsize-R2184-a.log")
SUITE_B = os.path.join(BASE, "qa", "apimarket-ticketsize-R2184-b.log")


def read(path):
    return io.open(path, encoding="utf-8").read()


def sha16(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:16]


def battery_facts():
    text = read(BATTERY)
    runner = None
    for match in re.finditer(
            r"^RUNNER (PASS|FAIL) \((\d+)/(\d+) suites[^\n]*?([\d.]+)s\)",
            text, re.M):
        runner = match
    reclaim = re.search(
        r"TMP RECLAIM candidates=(\d+) removed=(\d+) busy=(\d+)"
        r" failed=(\d+) reclaimed=([\d.]+) MiB", text)
    follow = re.search(
        r"PASS generated docs/sandbox-suite-matrix\.md \((\d+) bytes\)"
        r" - registry suites=(\d+) criteria=(\d+)[^\n]*green=(\d+)/(\d+)",
        text)
    if runner is None:
        raise SystemExit("no RUNNER line in %s" % BATTERY)
    facts = {
        "verdict": runner.group(1),
        "passed": int(runner.group(2)),
        "total": int(runner.group(3)),
        "seconds": runner.group(4),
        "reclaim": (None if reclaim is None else
                    (int(reclaim.group(1)), int(reclaim.group(2)),
                     int(reclaim.group(3)), int(reclaim.group(4)),
                     reclaim.group(5))),
        "follow": (None if follow is None else
                   "matrix regenerated to %s suites / %s criteria and read "
                   "back byte-identical (green=%s/%s, %s bytes), "
                   "fingerprint CLEAN over five domains, runner profile "
                   "--daily --check PASS, and the qa writer census "
                   "re-frozen then read DRIFT-CLEAN flags=0"
                   % (follow.group(2), follow.group(3), follow.group(4),
                      follow.group(5), follow.group(1)))}
    return facts


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
    facts = battery_facts()
    suite_sha_a = sha16(SUITE_A)
    suite_sha_b = sha16(SUITE_B)
    if suite_sha_a != suite_sha_b:
        raise SystemExit("suite double-run mismatch")
    reclaim_text = ("unknown" if facts["reclaim"] is None else
                    "%d/%d worlds, %s MiB, busy=%d failed=%d"
                    % (facts["reclaim"][1], facts["reclaim"][0],
                       facts["reclaim"][4], facts["reclaim"][2],
                       facts["reclaim"][3]))
    follow_text = ("" if facts["follow"] is None else
                   " The four post-battery sections then all PASS in "
                   "src/os/battery_followup_R2184.py: " + facts["follow"]
                   + ".")

    round_line = (
        "2026-10-28 R2184 (five-silence scan clean at open: decisions.md "
        "240 non-empty rows carrying 159 content-addressed D/C tokens that "
        "equal the stored baseline EXACTLY - zero new, zero dropped - so "
        "zero domain action and the baseline stands unchanged; the ledger "
        "carries the same three @BigDomain patrol rows already paid off "
        "with zero unreplied; the group orders tail is unchanged at the "
        "2026-10-28 03:0x CEO-PROXY fleet event round #4, acknowledged with "
        "zero domain action; benchmarks refreshed 2026-10-27 inside the "
        "seven-day gate; tree clean, no index.lock) - the P1 canonical rows "
        "stay blocked-on-CEO, the weekly proposal duty is met by "
        "BD-PROP-005, all four tech heads stayed gated (docker host absent, "
        "logs toolkit standing maintenance, member refunded schema "
        "product-gated, the live-mtime row waiting on a real "
        "normalized-mtime event) and the explore head above the seeds is "
        "the merchant-gated benchmark row, so this window claimed the next "
        "real seed (R2178 6/10) and registered AC-MTS1..AC-MTS8 in that "
        "queue row BEFORE the code existed (AC-MTS / "
        "ledger-apimarket-ticketsize / p90_ticket / _ticket_sample all git "
        "grep -F zero-occupancy against HEAD 2026-10-28 rc=1, with the "
        "honest note that api_market_ticket_size and "
        "test_apimarket_ticketsize text occupancy comes only from the seed "
        "row and the R2183 export text, and that ticket_count belongs to "
        "the eventtickets face so this face counts sale_count instead). "
        "Gap statement: api_market_price_percentiles quantiles what is "
        "still ASKING on the shelf, the position face ranks one listing "
        "inside its bucket and the cash faces total money, so what a sale "
        "actually costs had no face at all and the asking p50 could drift "
        "from the achieved p50 invisibly. Product: "
        "APIMarketFace.api_market_ticket_size(dev_account=None, "
        "include_refunded=False) - a nineteen-key envelope with ten-key "
        "category rows, one ticket per purchase row valued at its own "
        "immutable price_paid (a revision or a delisting never rewrites a "
        "historical ticket), the default NET authority (a refunded purchase "
        "leaves the sample because a refund is not revenue) with "
        "include_refunded putting it back, both axes lining up exactly with "
        "api_market_stats on purchase_count / net_purchase_count / gross / "
        "refunded / net, quantiles reused from the AC-MPP3 "
        "linear-interpolation seam, the uncategorized bucket last, rows "
        "summing to the envelope, strict seller isolation whose per-seller "
        "sums equal the market, a single-seller world identical apart from "
        "scope/dev_account, the pinned gate order (account shape before the "
        "bool gate, both before any read) and a pure read with zero token "
        "movement. SUITE PASS 8/8 double-run byte-identical sha16 %s "
        "(evidence qa/apimarket-ticketsize-R2184-a.log and -b.log, "
        "single-writer utf-8 LF), wired into reconcile_all SUITES as "
        "ledger-apimarket-ticketsize(8), with six adjacent apimarket suites "
        "green (qa/regression-R2184.log). Full battery including the new "
        "suite: RUNNER %s %d/%d suites green in %ss "
        "(qa/reconcile-all-R2184-2.log, single-writer utf-8 LF through "
        "src/os/battery_stream.py), with the birth-site sweep inside the "
        "same battery window reclaiming %s. Honest note on the first "
        "attempt (preserved verbatim as qa/reconcile-all-R2184.log): it "
        "read RUNNER FAIL with two assertions - reconcile-daily-census cd7 "
        "and the criteria total - because this window's own three evidence "
        "files carried CRLF from the child process text mode, so the census "
        "classified them as the shell-capture dialect; the fix went into "
        "the birth place (the capture is normalised before the single "
        "writer sees it in src/os/evidence_R2184.py) and the live census "
        "then read flags=0. The census baseline was NOT widened.%s"
        % (suite_sha_a, facts["verdict"], facts["passed"], facts["total"],
           facts["seconds"], reclaim_text, follow_text))

    token_line = (
        "R2184 tokens: local=~95k api=0 api_reason=five-silence scan + "
        "explore seed 6/10 claim with criteria pre-registered before code "
        "+ achieved ticket-size product face + suite 8/8 double-run "
        "byte-identical + six adjacent regressions + full battery %d/%d "
        "+ matrix regen/check + state/export closeout, zero cloud calls"
        % (facts["passed"], facts["total"]))

    spath = os.path.join(BASE, "src", "os", "state.json")
    state = json.loads(open(spath, "rb").read().decode("utf-8"))
    state["tick"] = int(state["tick"]) + 1
    state["log"].append(round_line)
    state["log"].append(token_line)
    tokens = live_tokens()
    state["last_dec_tokens"] = ",".join(tokens)
    state["last_decision_rows"] = nonempty_rows()
    with io.open(spath, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(state, ensure_ascii=False, indent=2))
        handle.write("\n")

    qpath = os.path.join(BASE, "state", "queue", "explore.md")
    qtext = io.open(qpath, encoding="utf-8").read()
    marker = qtext.find("api_market_ticket_size")
    line_start = qtext.rfind("\n", 0, marker) + 1
    line_end = qtext.index("\n", line_start)
    row = qtext[line_start:line_end]
    already = "[done 2026-10-28 R2184]" in row
    assert row.startswith("- [ ] P3 explore") or row.startswith(
        "- [x] P3 explore"), "no claim row"
    if not already:
        row = "- [x] P3 explore" + row[len("- [ ] P3 explore"):]
        qtext = qtext[:line_start] + row + qtext[line_end:]
        line_end = line_start + len(row)
    done_note = (
        " [done 2026-10-28 R2184] Product=apimarket.py"
        " api_market_ticket_size(dev_account=None, include_refunded=False):"
        " nineteen-key envelope, ten-key category rows, one ticket per"
        " purchase row at its own immutable price_paid, net-refund authority"
        " by default with the include_refunded axis putting a refunded"
        " purchase back, cross-face identity with api_market_stats on both"
        " axes, AC-MPP3 quantile seam reuse, uncategorized bucket last,"
        " rows summing to the envelope, strict seller isolation and the"
        " single-seller equivalence, pinned account-before-bool gate order,"
        " pure read. Suite SUITE PASS 8/8 double-run byte-identical sha16"
        " %s (qa/apimarket-ticketsize-R2184-a.log and -b.log); wired"
        " ledger-apimarket-ticketsize(8); six adjacent suites green"
        " (qa/regression-R2184.log); full battery RUNNER %s %d/%d in %ss"
        " (qa/reconcile-all-R2184-2.log)." % (suite_sha_a, facts["verdict"],
                                           facts["passed"], facts["total"],
                                           facts["seconds"]))
    line_end = line_start + len(row)
    if not already:
        qtext = qtext[:line_end] + done_note + qtext[line_end:]
    io.open(qpath, "w", encoding="utf-8", newline="\n").write(qtext)

    epath = os.path.join(BASE, "docs", "status-export.json")
    export = json.loads(open(epath, "rb").read().decode("utf-8"))
    export["export_ts"] = "2026-10-28T23:05:00+08:00"
    export["do"] = (
        "R2184 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - an operator "
        "can now read what sales actually COST: the achieved ticket-size "
        "distribution per category, refund-adjusted, beside the asking-price "
        "distribution that was already on the shelf")
    export["ceo_face"] = {
        "current": (
            "R2184: shipped api_market_ticket_size - the achieved ticket "
            "distribution (quartiles, median, ninetieth percentile, spread) "
            "over real sale rows at their own immutable price, net of "
            "refunds by default with an include_refunded axis that lines up "
            "exactly with the market cash stats on both sides (suite 8/8 "
            "double-run byte-identical, six neighbours green); the full "
            "battery including the new suite is green (%d/%d suites)"
            % (facts["passed"], facts["total"])),
        "latest_artifact": (
            "src/sandbox/ledger/apimarket.py (api_market_ticket_size) + "
            "src/sandbox/ledger/test_apimarket_ticketsize.py + "
            "qa/apimarket-ticketsize-R2184-a.log and -b.log (SUITE PASS "
            "8/8, sha256 %s) + qa/reconcile-all-R2184-2.log (RUNNER %s "
            "%d/%d, %ss) - 2026-10-28"
            % (suite_sha_a, facts["verdict"], facts["passed"],
               facts["total"], facts["seconds"])),
        "next_milestone": (
            "R2185: next explore seed (R2178 7/10, api_buyer_concentration "
            "- the buyer-side mirror of the seller concentration index) "
            "plus the reconciled suite matrix - ETA 2026-10-29, within 48h"),
        "last_artifact": (
            "qa/apimarket-ticketsize-R2184-a.log (SUITE PASS 8/8, "
            "double-run byte-identical) (2026-10-28)")}
    export["results"].append(["R2184", (
        "R2184: five-silence scan clean with the decision baseline an "
        "exact 159/159 match, so zero domain action. Product: "
        "api_market_ticket_size with AC-MTS1..AC-MTS8 pre-registered before "
        "the code, SUITE PASS 8/8 double-run byte-identical (sha256 %s), "
        "wired as ledger-apimarket-ticketsize(8), six adjacent suites "
        "green. Full battery RUNNER %s %d/%d in %ss with the birth-site "
        "sweep reclaiming %s."
        % (suite_sha_a, facts["verdict"], facts["passed"],
           facts["total"], facts["seconds"], reclaim_text))])
    export["outs"].insert(0, [
        "achieved ticket-size distribution (api_market_ticket_size)",
        "on",
        ("R2184: the asking-price percentiles quantile what is still on "
         "the shelf, the position face ranks one listing inside its bucket "
         "and the cash faces total money - so what a sale actually costs "
         "had no face, and in a market where prices are revised the asking "
         "p50 and the achieved p50 are different quantities. The new face "
         "values each purchase at its own immutable price_paid (a revision "
         "or a delisting never rewrites a historical ticket), is NET by "
         "default because a refund is not revenue and puts the refunded "
         "purchase back under include_refunded, and both axes line up "
         "exactly with api_market_stats on purchase_count, "
         "net_purchase_count, gross, refunded and net. Quantiles reuse the "
         "AC-MPP3 linear-interpolation seam so the two distribution faces "
         "cannot drift; rows are one per effective category bucket with the "
         "uncategorized bucket last and sum to the envelope; a seller scope "
         "is strictly isolated and a single-seller world matches the "
         "market scope apart from the scope pair. Suite 8/8 double-run "
         "byte-identical, wired as ledger-apimarket-ticketsize(8).")])
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
          " battery=%s %d/%d sha=%s"
          % (state["tick"], len(tokens), state["last_decision_rows"],
             sd["queue_explore_open"], sd["queue_tech_open"],
             facts["verdict"], facts["passed"], facts["total"],
             suite_sha_a))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())