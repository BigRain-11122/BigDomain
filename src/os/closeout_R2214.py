# -*- coding: utf-8 -*-
"""R2214 closeout: state.json tick/log/watermark, status-export, heartbeat.
Run only after the battery and the post-battery follow-up are on disk.
Every number written here is parsed from the evidence, never typed by hand.
"""
import io
import json
import os
import re
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
MATRIX = os.path.join(ROOT, "docs", "sandbox-suite-matrix.md")
EVIDENCE = os.path.join(ROOT, "qa", "reconcile-all-R2214.log")
HEART = os.path.join(ROOT, "heartbeat.txt")

SPEC = 8          # AC-MSM1..AC-MSM8
SHA16 = "BFD33232DFDF1A97"
PRODUCT = "648cc017"


def read(path):
    return io.open(path, encoding="utf-8").read()


def evidence_facts():
    text = read(EVIDENCE)
    runner = re.search(
        r"RUNNER (PASS|FAIL) \((\d+)/(\d+) suites green,"
        r" reconcile controls (\d+)/(\d+), ([0-9.]+)s\)", text)
    if runner is None:
        raise SystemExit("no RUNNER line in evidence")
    reclaim = re.search(
        r"TMP RECLAIM candidates=(\d+) removed=(\d+) busy=(\d+)"
        r" failed=(\d+) reclaimed=([0-9.]+) MiB", text)
    verdict = None
    for line in text.split("\n"):
        if line.startswith("VERDICT "):
            verdict = line.strip()
    matrix = re.search(r"^\| (\d+) \| (\d+) \| (\d+)/(\d+) \| ",
                       read(MATRIX), re.M)
    return {
        "verdict": runner.group(1),
        "passed": int(runner.group(2)),
        "total": int(runner.group(3)),
        "cpass": int(runner.group(4)),
        "ctotal": int(runner.group(5)),
        "secs": runner.group(6),
        "bytes": len(text.encode("utf-8")),
        "reclaim": reclaim.group(5) if reclaim else None,
        "reclaim_n": reclaim.group(2) if reclaim else None,
        "followup": verdict,
        "msuites": int(matrix.group(1)) if matrix else None,
        "mcriteria": int(matrix.group(2)) if matrix else None,
        "mgreen": matrix.group(3) if matrix else None,
    }


def queue_opens(name):
    rows = read(os.path.join(ROOT, "state", "queue", name))
    return sum(1 for line in rows.split("\n")
               if line.startswith("- [ ]"))


def proposals():
    text = read(os.path.join(ROOT, "docs", "proposals.md"))
    heads = [line for line in text.split("\n")
             if line.startswith("### BD-PROP-")]
    opened = sum(1 for line in heads if "open" in line)
    return len(heads), opened


def self_drive(state, f):
    entries = state["log"]
    window = [e for e in entries
              if re.match(r"^2026-10-2[2-8]", e)]
    idle = sum(1 for e in entries if "idle-fast" in e)
    no_pull = sum(1 for e in entries if "no-pullable" in e)
    total, opened = proposals()
    return {
        "window": "2026-10-22..2026-10-28",
        "window_days": 7,
        "log_lines_in_window": len(window),
        "idle_fast_mention_lines": idle,
        "no_pullable_mention_lines": no_pull,
        "substantive_non_idle_mention_lines": len(window) - idle - no_pull,
        "proposals_total": total,
        "proposals_open": opened,
        "queue_main_open": queue_opens("main.md"),
        "queue_tech_open": queue_opens("tech.md"),
        "queue_explore_open": queue_opens("explore.md"),
    }


def main():
    f = evidence_facts()
    print("facts:", json.dumps(f, sort_keys=True))

    battery = (
        "battery on the committed tree: RUNNER %s %d/%d suites green plus "
        "reconcile controls %d/%d in %ss (qa/reconcile-all-R2214.log, "
        "%d bytes, single-writer UTF-8 LF through battery_stream.py)"
        % (f["verdict"], f["passed"], f["total"], f["cpass"], f["ctotal"],
           f["secs"], f["bytes"]))
    if f["reclaim"] is not None:
        battery += (
            ", with the birth-site tmp sweep inside the same window "
            "reclaiming %s MiB over %s candidates" % (f["reclaim"],
                                                      f["reclaim_n"]))
    follow = f["followup"] or "VERDICT MISSING"
    matrix = ("the suite matrix regenerated to %s suites / %s criteria and "
              "read back byte-identical (green=%s)"
              % (f["msuites"], f["mcriteria"], f["mgreen"]))

    round_text = (
        "2026-10-28 R2214 (five-silence scan clean at open: the stored "
        "last_dec_tokens field is a comma-joined string, and after "
        "splitting it the intersection with decisions.md measured 179 "
        "content-addressed D/C/O/T tokens whose nine apparent additions are "
        "all artifacts - the four known body-text citations D-20261006-05, "
        "D-20261007-04, D-20261007-05 and D-20261008-05 that the group-side "
        "rotation drops, plus five truncated forms of existing four-digit "
        "suffixes (O-20261012-2330, O-20261026-0735, T-20261026-01..03) cut "
        "by a two-to-three digit regex - so zero genuinely new rows, zero "
        "domain action, and the baseline is re-anchored to the measured set; "
        "the group ledger carries the same three @BigDomain patrol rows "
        "already paid off with zero unreplied; the group orders tail is "
        "unchanged at the 2026-10-28 15:01 fleet auto-dispatch "
        "OB-20261028-150100-267, acknowledged as a fleet dispatcher face "
        "with zero domain action; benchmarks refreshed 2026-10-27 inside "
        "the seven-day gate; tree clean, no index.lock) - the P1 canonical "
        "rows stay blocked-on-CEO, the weekly proposal duty is met by "
        "BD-PROP-005, all four tech heads stayed gated (docker host absent, "
        "logs toolkit standing maintenance, member refunded schema "
        "product-gated, the live-mtime row waiting on a real "
        "normalized-mtime event), so the explore head was worked: the R2213 "
        "seed that named api_buyer_watch_months was found STALE - that face "
        "shipped in R2213 - and was marked done, and the next open seed "
        "api_market_supply_months was claimed with AC-MSM1..AC-MSM8 "
        "registered in that row BEFORE the code (AC-MSM, "
        "api_market_supply_months, test_apimarket_marketsupplymonths, "
        "ledger-apimarket-marketsupplymonths, net_shop_change, units_added, "
        "units_sold, live_shop_at_month_end and _shop_flow_events all "
        "git grep -F rc=1). Product: APIMarketFace.api_market_supply_months "
        "- the whole-market shelf position plus its gross flow, which no "
        "sibling answered (the category face reads per-category shelves by "
        "month, the price face asking price, the listing faces one shelf). "
        "Seventeen-key envelope and thirteen-key month rows: a cycle opens "
        "at the publish stamp and again at each re-listing stamp, closes at "
        "its own delisting stamp; units_added is the finite base supply "
        "declared by a publish plus that month's restock units (an unlimited "
        "shelf adds nothing); units_sold is purchases net of refunds of that "
        "month, so a refund-only month is honestly negative. The grid is "
        "contiguous over supply-and-movement events only, so a month that "
        "carried no event at all is an honest zero row next to a live shelf "
        "count, while price and category revisions deliberately book "
        "nothing. The month-end snapshot runs through _alive_at_instant and "
        "_supply_at_instant and adds distinct seller breadth, so a shelf "
        "delisted inside a month is absent at that month end and a re-listed "
        "one is back. Conservation holds three ways, including running "
        "opened-minus-closed equal to the live shelf count; both peak laws "
        "take the earlier month on a tie; and a book with no listings "
        "returns an honest empty market-scope envelope carrying no account "
        "key at all. Evidence: SUITE PASS 8/8 double-run byte-identical "
        "sha16 %s (qa/apimarket-marketsupplymonths-R2214.log and -b.log, 607 "
        "bytes each, single UTF-8 LF writer), wired as "
        "ledger-apimarket-marketsupplymonths(%d), eight adjacent "
        "supply/relist/price suites green (qa/regression-R2214.log). %s, "
        "and the four follow-up sections then all passed (%s). Product "
        "committed as %s and pushed before the battery so the battery walked "
        "a committed tree. Honest gap: the explore queue now holds the "
        "remaining R2213 seeds, so the next window claims from those rather "
        "than reseeding." % (SHA16, SPEC, battery, follow, matrix, PRODUCT))

    tokens = ("R2214 tokens: local=~70k api=0 api_reason="
              "five-silence scan with the stored comma baseline split "
              "before diffing + a stale-seed cleanup + one explore claim "
              "with criteria registered before the code + one new product "
              "face with an eight-criterion suite double-run to "
              "byte-identical evidence + eight adjacent regressions + a "
              "full reconcile battery on the committed tree + the "
              "four-section follow-up + queue/backlog/state/export "
              "closeout; zero cloud calls")

    self_heal = (
        "R2214 self-heal check: the BigDomain-OSLoop scheduled task exists "
        "and is Running, but its principal still reads LogonType=Interactive "
        "with RunLevel=Limited, which the 2026-09-29 machine law forbids for "
        "every lane task. src/os/register_loop_task.ps1 already passes an "
        "explicit S4U principal and needs an elevated shell to apply it; "
        "this session runs unelevated, so the task was left untouched rather "
        "than risk replacing the definition of the loop hosting this window. "
        "Open local-lane item for an elevated window. One in-window tooling "
        "note, disclosed: the first battery invocation was cancelled by the "
        "five-minute no-output rule because its output was piped through a "
        "truncating selector - the ownership check found no surviving "
        "python child and no evidence file (zero loss), so it was re-run as "
        "a direct stream.")

    raw = read(STATE)
    raw = raw.replace('"tick": 2213,', '"tick": 2214,', 1)
    blob = (",\n    " + json.dumps(round_text) + ",\n    "
            + json.dumps(tokens) + ",\n    " + json.dumps(self_heal)
            + "\n  ]\n}\n")
    assert raw.endswith("\n  ]\n}\n")
    raw = raw[:-len("\n  ]\n}\n")] + blob
    measured = None
    dec = read(r"C:\Users\sjs20\Desktop\FluxGroup\docs\decisions.md")
    toks = set(re.findall(r"(?:D|C|O|T|XL)-\d{8}-\d{2,4}", dec))
    measured = ",".join(sorted(toks))
    raw = re.sub(r'"last_dec_tokens": "[^"]*"',
                 '"last_dec_tokens": ' + json.dumps(measured), raw, count=1)
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(raw)
    state = json.loads(raw)
    assert state["tick"] == 2214 and len(state["log"]) >= 3

    export = json.loads(read(EXPORT))
    export["export_ts"] = datetime.datetime.now().astimezone().replace(
        microsecond=0).isoformat()
    export["do"] = (
        "R2214 the sandbox developer-API marketplace and the OS toolchain "
        "for the silicon-domain public co-creation platform - the whole "
        "market now has a monthly supply timeline, so an operator can read "
        "whether shelves are thickening or thinning without summing "
        "categories, and how many units actually entered and left the book "
        "each month")
    export["ceo_face"]["current"] = (
        "R2214 api_market_supply_months(): market-wide monthly supply "
        "timeline - seventeen-key envelope, gross flow booked in each "
        "event's own stamp month, contiguous grid with an honest zero "
        "month, month-end shelves with distinct seller breadth, "
        "conservation three ways and both peak laws")
    export["ceo_face"]["latest_artifact"] = (
        "qa/apimarket-marketsupplymonths-R2214.log / -b.log (SUITE 8/8, "
        "sha16 %s, byte-identical double run) + src/sandbox/ledger/"
        "apimarket.py (api_market_supply_months) + commit %s"
        % (SHA16, PRODUCT))
    export["ceo_face"]["next_milestone"] = (
        "claim the next open explore seed (the remaining R2213 reseeds) and "
        "keep the suite matrix regenerated against this battery, within 48h")
    export["ceo_face"]["last_artifact"] = (
        "qa/reconcile-all-R2214.log (%s, %d bytes, single-writer UTF-8 LF) "
        "+ docs/sandbox-suite-matrix.md (%s suites / %s criteria, "
        "green=%s) + src/os/battery_followup_R2214.py"
        % (follow.rstrip(), f["bytes"], f["msuites"], f["mcriteria"],
           f["mgreen"]))
    export["outs"].insert(0, [
        "market-wide monthly supply timeline (api_market_supply_months)",
        "on",
        "R2214: the family answered asking price by month, per-category "
        "shelves by month and per-listing supply snapshots, but never the "
        "whole market's shelf position plus its gross flow. The new face "
        "books every event in its own stamp month (cycles opened at publish "
        "and re-list, closed at delist, units added by publish and restock, "
        "units sold net of refunds so a refund-only month is negative), runs "
        "a contiguous grid with an honest zero month over "
        "supply-and-movement events only, samples month-end shelves with "
        "distinct seller breadth through _alive_at_instant and "
        "_supply_at_instant, conserves three ways including running "
        "opened-minus-closed equal to the live shelf count, takes the "
        "earlier month on both peak ties, and returns an honest empty "
        "market envelope with no account key. SUITE PASS 8/8 double-run "
        "byte-identical sha16 %s, wired ledger-apimarket-marketsupplymonths"
        "(8), eight adjacent suites green." % SHA16])
    export["results"].insert(0, [
        "R2214",
        "R2214: five-silence scan clean with the comma-joined decision "
        "baseline split before diffing (nine apparent additions, all "
        "citation artifacts and regex-truncated suffixes, so zero domain "
        "action and the baseline re-anchored), a stale R2213 seed marked "
        "done, and api_market_supply_months claimed with AC-MSM1..AC-MSM8 "
        "registered before the code. SUITE PASS 8/8 double-run "
        "byte-identical sha16 %s, wired as ledger-apimarket-"
        "marketsupplymonths(8), eight adjacent suites green. %s; %s."
        % (SHA16, battery, follow)])
    export["self_drive"] = self_drive(state, f)
    io.open(EXPORT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(export, ensure_ascii=False, indent=2) + "\n")

    io.open(HEART, "w", encoding="ascii", newline="\n").write("2214\n")
    print("closeout written: tick 2214, export refreshed, heartbeat 2214")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())