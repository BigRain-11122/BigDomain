"""R2237 closeout: append the round log lines to src/os/state.json with
the canonical PS layout preserved (CRLF, 16-space items, verify before
write), bump the tick, then refresh docs/status-export.json and
heartbeat.txt. Stdlib only, ASCII source."""

import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
STATE = os.path.join(ROOT, "src", "os", "state.json")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")
BEAT = os.path.join(ROOT, "heartbeat.txt")

NARRATIVE = (
    "2026-10-29 R2237 (five-silence scan clean at open: decisions.md "
    "283 non-empty rows carrying 185 content-addressed D/C/O/T tokens "
    "with ZERO new against the stored baseline, so zero domain action; "
    "the group ledger carries the same three @BigDomain patrol rows "
    "already paid off with zero unreplied; the own-orders baseline is "
    "unchanged at the 2026-10-29 02:1x CEO-PROXY fleet event round "
    "R2.48 already consumed in R2226; benchmarks refreshed 2026-10-29 "
    "inside the seven-day gate; tree clean, no index.lock) - the P1 "
    "canonical rows stay blocked-on-CEO, the weekly proposal duty is "
    "met by BD-PROP-005, all four tech heads stayed gated (docker host "
    "absent, logs toolkit standing maintenance, member refunded schema "
    "product-gated, the live-mtime row waiting on a real "
    "normalized-mtime event), so this window claimed the explore head, "
    "seed 5/6 of the R2230 family. Anchor check at HEAD 2026-10-29: "
    "AC-CWC, test_apimarket_categorywatchconversionmonths, "
    "ledger-apimarket-categorywatchconversionmonths, "
    "category_conversion_month_count and market_conversion_rate were "
    "git grep -F zero-occupancy rc=1. Criteria AC-CWC1..AC-CWC8 were "
    "written into that queue row BEFORE the code. Gap: "
    "api_market_conversion_months answers the whole market on a month "
    "axis, api_watch_conversion one listing over its lifetime and "
    "api_category_watch_months the volume alone, so whether one "
    "CATEGORY's attention actually converted, month over month, had no "
    "face - a bucket flooded with watchers who never buy read exactly "
    "like a converting one once the market rate was quoted. Product: "
    "APIMarketFace.api_category_watch_conversion_months("
    "include_uncategorized=True) - a sixteen-key envelope with "
    "fourteen-key month rows and twelve-key category cells. Booking "
    "law: a watch books in the UTC month of its own watched_utc, an "
    "unwatch is not an event for this face and a purchase never "
    "re-dates the month; the bucket is the category in force AT THE "
    "WATCH INSTANT (_category_at_instant), so bob's March watch on d1 "
    "stays under data while kit's May watch on the same listing books "
    "under analytics after the 03-20 re-file. Leg law, shared with the "
    "market face: converted when the unrefunded purchase is stamped at "
    "or after the watch stamp (equal stamps convert at zero seconds), "
    "pre_owned when the purchase predates the watch and is excluded "
    "from the funnel denominator, pending when there is no purchase OR "
    "the purchase was refunded - so the April refund drops that row to "
    "a real 0.0 and leaves January's pre_owned-only data cell at an "
    "honest None rather than a fabricated zero. Latency is pooled over "
    "every converted watch (average and median 216000.0 against the "
    "172800 and 259200 extremes) and all four latency fields are None "
    "on a zero month. The grid is contiguous JAN..MAY with an honest "
    "zero February. market_conversion_rate is the TRUE market rate of "
    "that month computed over every watch regardless of the flag, so "
    "the trimmed January row reads 0.5 while its benchmark stays 1/3 - "
    "a stable column that changes no meaning. Identity holds against "
    "api_category_watch_months (7 watches, matching per-month counts) "
    "and api_market_conversion_months (2 converted / 1 pre_owned / 4 "
    "pending); include_uncategorized=False drops the bucket AND "
    "recomputes every aggregate (6 watches / 5 cells); the flag is "
    "bool-only and seven bad forms fail closed before any read with "
    "frozen table digests and a constant ledger_tx set. Evidence: "
    "SUITE 8/8 double-run byte-identical criterion sha16 "
    "50e5228778f319c9 (qa/apimarket-categorywatchconversionmonths-"
    "R2237-a.log and -b.log, 904 bytes each, utf-8 LF written by "
    "src/os/evidence_R2237.py, never a shell redirection), wired "
    "ledger-apimarket-categorywatchconversionmonths(8), six adjacent "
    "watch and conversion suites green 8/8 each (qa/regression-"
    "R2237.log), PRODUCT_SHA_STABLE True. Honest note: the first run "
    "read 7/8 because the trimmed cell count was expected as 4 while "
    "the grid honestly carries 5 - the test expectation was corrected, "
    "neither the implementation nor any criterion was relaxed. Same "
    "window, folded rather than carried: the state log measured "
    "83849B against the 78500B waterline (fold_needed true), so fold "
    "R592 moved log lines 1:21 (34538 content bytes, R2217..R2225) "
    "into logs/state-log-archive-2026-10.md verbatim with "
    "token_missing [] over 462 window tokens and predicted_eq_actual "
    "true, landing 53651B / 34 live lines / margin 24849. Debt: the "
    "full reconcile battery and the suite-matrix regeneration were NOT "
    "run this window (25-minute budget) and are the R2238 first item.")

TOKENS = ("R2237 tokens: local=~42k api=0 api_reason=product window on "
          "one explore seed - a zero-occupancy anchor check, one new "
          "per-category monthly conversion face with an eight-criterion "
          "suite, a single-writer double-run evidence pair, six adjacent "
          "regressions, the fold surgery plus gauge verification, and "
          "the state/export/backlog closeout; zero cloud calls")

SELF_HEAL = ("R2237 self-heal check: the BigDomain-OSLoop scheduled task "
             "exists and is Running (last run 2026-10-29 07:14, next "
             "07:19), but its principal still reads LogonType=Interactive "
             "with RunLevel=Limited, which the 2026-09-29 machine law "
             "forbids for every lane task. src/os/register_loop_task.ps1 "
             "already passes an explicit S4U principal and needs an "
             "elevated shell to apply it; this session runs unelevated, "
             "so the definition of the loop hosting this window was left "
             "untouched. Open local-lane item for an elevated window "
             "(seventh consecutive disclosure).")


def append_log():
    raw = open(STATE, "rb").read()
    text = raw.decode("utf-8")
    old = json.loads(text)
    lines = text.split("\r\n")
    close_idx = None
    for idx in range(len(lines) - 1, -1, -1):
        if lines[idx].strip() == "]":
            close_idx = idx
            break
    if close_idx is None:
        raise SystemExit("no log close bracket found")
    last_item = lines[close_idx - 1]
    if not last_item.rstrip().endswith('"'):
        raise SystemExit("last log item does not end with a quote")
    new_lines = []
    for item in (NARRATIVE, TOKENS, SELF_HEAL):
        escaped = item.replace('"', '\\"')
        new_lines.append(' ' * 16 + '"' + escaped + '"')
    rebuilt = (lines[:close_idx - 1]
               + [last_item.rstrip() + ","]
               + [nl + "," for nl in new_lines[:-1]]
               + [new_lines[-1]]
               + lines[close_idx:])
    out = "\r\n".join(rebuilt)
    out = re.sub(r'"tick": 2236,', '"tick": 2237,', out, count=1)
    new_state = json.loads(out)
    if new_state["tick"] != 2237:
        raise SystemExit("tick bump failed")
    if new_state["log"][:len(old["log"])] != old["log"]:
        raise SystemExit("log prefix changed")
    if new_state["log"][-3:] != [NARRATIVE, TOKENS, SELF_HEAL]:
        raise SystemExit("appended lines do not round-trip")
    with open(STATE, "wb") as handle:
        handle.write(out.encode("utf-8"))
    print("state bytes %d -> %d, log lines %d -> %d"
          % (len(raw), len(out.encode("utf-8")),
             len(old["log"]), len(new_state["log"])))
    return new_state


CLAIMS = []


def count_open(path):
    n = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("- [ ]"):
                n += 1
    return n


def window_log_lines(state):
    pat = re.compile(r"2026-10-2[3-9]")
    return sum(1 for line in state["log"] if pat.search(line))


def update_export(state):
    raw = open(EXPORT, "rb").read()
    text = raw.decode("utf-8")
    doc = json.loads(text)
    crlf = "\r\n" in text
    doc["export_ts"] = "2026-10-29T07:35:00+08:00"
    doc["do"] = ("product window R2237: per-category monthly "
                 "watch-to-purchase conversion (explore seed R2230 5/6) "
                 "plus the state fold")
    doc["ceo_face"]["current"] = (
        "R2237 \u4ea7\u54c1\u7a97\u53e3\uff1aapimarket \u5206\u7c7b\u76ee"
        "\u6708\u5ea6\u300c\u5173\u6ce8\u2192\u4e70\u5355\u8f6c\u5316"
        "\u300d\u9762 api_category_watch_conversion_months\uff08\u63a2"
        "\u7d22\u79cd\u5b50 R2230 5/6\uff09\uff1a\u5173\u6ce8\u8ba1\u5165"
        "\u5176\u81ea\u8eab\u6708\u4efd\u3001\u53d6\u6d88\u4e0d\u7b97"
        "\u4e8b\u4ef6\u3001\u8d2d\u4e70\u4e0d\u56de\u6eaf\u6539\u6708"
        "\uff1b\u8f6c\u5316/\u5148\u62e5\u6709/\u60ac\u7f6e\u4e09\u817f"
        "\u4e0e\u9000\u6b3e\u5373\u53d6\u6d88\u8f6c\u5316\uff1b\u5206\u7c7b"
        "\u5f52\u5c5e\u53d6\u300c\u5173\u6ce8\u90a3\u4e00\u77ac\u95f4"
        "\u300d\u7684\u7c7b\u76ee\uff08\u6539\u7c7b\u4e0d\u56de\u6539"
        "\u65e7\u6708\uff09\uff1b\u5e02\u573a\u57fa\u51c6\u5217\u4e0d"
        "\u53d7\u5254\u9664\u5f00\u5173\u5f71\u54cd\uff1b\u4e0e\u5173"
        "\u6ce8\u91cf\u9762\u3001\u5e02\u573a\u8f6c\u5316\u9762\u4e09"
        "\u65b9\u6052\u7b49\u3002\u540c\u7a97\u628a state.json \u65e5"
        "\u5fd7\u8001\u7a97\u53e3\u6298\u53e0\u5165\u6863\uff0883849B"
        "\u2192 53651B\uff0c\u6c34\u4f4d\u9600\u6062\u590d\u5b89\u5168"
        "\u4f59\u91cf\uff09\u3002")
    doc["ceo_face"]["latest_artifact"] = (
        "qa/apimarket-categorywatchconversionmonths-R2237-a.log \u4e0e "
        "-b.log\uff08\u5404 904 \u5b57\u8282\u00b7utf-8 LF\u00b7\u96f6 CR"
        "\u00b7SUITE 8/8 \u53cc\u8dd1\u5224\u636e\u540c\u4e00 sha16 "
        "50e5228778f319c9\uff09+ qa/regression-R2237.log\uff08\u516d\u90bb"
        "\u57df\u5747 8/8\uff09\uff1b\u4ea7\u54c1\u4f53 src/sandbox/"
        "ledger/apimarket.py api_category_watch_conversion_months\uff1b"
        "\u65f6\u95f4\u6233 2026-10-29\u3002")
    doc["ceo_face"]["next_milestone"] = (
        "R2238\uff08\u7a97 \u226448h\uff09\uff1a\u5728\u63d0\u4ea4\u6811"
        "\u4e0a\u8dd1\u5168\u91cf\u5bf9\u8d26\u7535\u6c60 + \u5957\u4ef6"
        "\u77e9\u9635\u518d\u751f\uff08\u9884\u671f 418\u2192419 \u5957"
        "\u4ef6 / 3467\u21923475 \u5224\u636e\uff0c+8 \u5373\u672c\u7a97"
        "\u65b0\u5957\u4ef6\uff09\uff0c\u5e76\u7ee7\u7eed\u63a8\u8fdb"
        "\u63a2\u7d22\u79cd\u5b50 R2230 6/6\uff08\u5356\u5bb6\u4ef7\u683c"
        "\u5bf9\u9700\u6c42\u54cd\u5e94\uff09\u3002")
    doc["outs"].insert(0, [
        "per-category monthly watch-to-purchase conversion face (R2237)",
        "on",
        "api_category_watch_conversion_months(include_uncategorized=True):"
        " sixteen-key envelope, fourteen-key month rows, twelve-key "
        "category cells; the watch-month cohort law (an unwatch is not an "
        "event, a purchase never re-dates the month); the three legs "
        "(converted at or after the watch stamp incl. equal stamps at "
        "zero seconds, pre_owned excluded from the funnel, pending that "
        "also absorbs a refunded purchase so the April cancellation lands "
        "as a real 0.0 and a pre_owned-only January cell reads None); "
        "contiguous JAN..MAY grid with a zero February carrying None rate "
        "and None latencies; the watch-instant category seam; the TRUE "
        "market benchmark column that survives the trimmed view (0.5 row "
        "against a 1/3 benchmark); identity with api_category_watch_months "
        "(7 watches) and api_market_conversion_months (2 converted / 1 "
        "pre_owned / 4 pending); pooled 216000.0 average and median "
        "against 172800/259200 extremes; seven-form bool gate failing "
        "closed before any read. Evidence: SUITE 8/8 double-run "
        "byte-identical criterion sha16 50e5228778f319c9 (904B per leg, "
        "utf-8 LF by src/os/evidence_R2237.py), wired "
        "ledger-apimarket-categorywatchconversionmonths(8), six adjacent "
        "suites green."])
    doc["results"].insert(0, [
        "R2237",
        "product window: explore head seed R2230 5/6 delivered as "
        "api_category_watch_conversion_months; SUITE 8/8 double-run with "
        "byte-identical criterion sha16 50e5228778f319c9 (904B per leg, "
        "single-writer utf-8 LF, zero CR); six adjacent watch/conversion "
        "suites green 8/8; PRODUCT_SHA_STABLE True; first run 7/8 with a "
        "test expectation corrected (trimmed cells 4 -> the honest 5), no "
        "criterion or implementation relaxed. Same window: fold R592 moved "
        "log lines 1:21 into the October archive (83849B -> 53651B, "
        "token_missing [] over 462 tokens, predicted_eq_actual true). "
        "Debt: full battery and matrix regeneration deferred to R2238."])
    drive = doc["self_drive"]
    drive["log_lines_in_window"] = window_log_lines(state)
    drive["substantive_non_idle_mention_lines"] = drive[
        "log_lines_in_window"]
    drive["queue_main_open"] = count_open(
        os.path.join(ROOT, "src", "os", "backlog.md"))
    drive["queue_tech_open"] = count_open(
        os.path.join(ROOT, "state", "queue", "tech.md"))
    drive["queue_explore_open"] = count_open(
        os.path.join(ROOT, "state", "queue", "explore.md"))
    out = json.dumps(doc, indent=2, ensure_ascii=True)
    if not out.endswith("\n"):
        out += "\n"
    if crlf:
        out = out.replace("\n", "\r\n")
    with open(EXPORT, "wb") as handle:
        handle.write(out.encode("utf-8"))
    print("export bytes %d -> %d" % (len(raw), len(out.encode("utf-8"))))


def update_beat():
    raw = open(BEAT, "rb").read()
    crlf = b"\r\n" in raw
    line = ("2237 tick 2026-10-29 R2237 product window: "
            "api_category_watch_conversion_months (explore R2230 5/6) - "
            "suite 8/8 double-run; state fold 83849B->53651B; battery "
            "carried to R2238")
    data = line + ("\r\n" if crlf else "\n")
    with open(BEAT, "wb") as handle:
        handle.write(data.encode("utf-8"))
    print("heartbeat rewritten (%d bytes)" % len(data))


if __name__ == "__main__":
    state = append_log()
    update_export(state)
    update_beat()
    sys.exit(0)