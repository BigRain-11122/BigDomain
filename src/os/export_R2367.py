"""export_R2367 - refresh docs/status-export.json from live state (R2367).

Every count is derived in this run through check_export_consistency.recompute();
only the round label and the prose summaries are this window's own words.
Dry run by default; --execute writes with a read-back proof.
"""

import io
import json
import os
import sys
from datetime import datetime, timedelta

import check_export_consistency as CEC

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

NOW = datetime.strptime("2026-11-02T06:30:16", "%Y-%m-%dT%H:%M:%S")
STAMP = "2026-11-02T06:30:16+08:00"
DUE = (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

DO = (
    "R2367 QA charter daily crawl round: one official source read (the "
    "wx.requestVirtualPayment API page) and three design gates taken from its "
    "own error codes - production has no sandbox env, the order number is "
    "one-use but not guaranteed unique so the idempotency key stays ours, and "
    "the item must be published and priced before any order. No product code "
    "this window; the battery is carried."
)

ARTIFACT = (
    "qa/smoke-R2367.log (64 lines) and qa/smoke-R2367.png (904x1415, rendered "
    "from that log by the shipped renderer), plus docs/global-benchmarks.md "
    "W37 rows and docs/research/intelligence-wall.md W37 main + conclusion."
)

NEXT = (
    "R2368: the battery on the committed R2367 tree, pre-registered at 494 "
    "suites / 3940 criteria (matrix doc at HEAD still 492/3928 from R2364, plus "
    "the R2365 os-queue-floor-delivered-wire and R2366 "
    "os-battery-followup-help-wire suites, six criteria each), then the P-47 "
    "item 4 pay-spec field gate that W37 now makes writable without the "
    "merchant number."
)


def read_json(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv):
    execute = "--execute" in argv
    data = read_json(EXPORT)
    derived, _state, _export, _pat = CEC.recompute()
    window = derived["window"]
    data["export_ts"] = STAMP
    data["do"] = DO
    face = data["ceo_face"]
    face["current"] = DO
    face["latest_artifact"] = ARTIFACT
    face["last_artifact"] = ARTIFACT
    face["next_milestone"] = NEXT
    face["next_milestone_due"] = DUE
    face["updated_at"] = STAMP
    data["outs"].append([
        "qa/smoke-R2367.png", "on",
        "R2367 QA charter daily crawl: one official API page read once and "
        "rendered into a real log+png evidence pair; the reading is the "
        "wx.requestVirtualPayment field table and its twenty-five error codes, "
        "consumed as three design gates in the pay spec",
    ])
    data["results"].append([
        "R2367",
        "QA charter daily crawl round: [QA] was the flag the scan raised and "
        "[HB] was this company own row-shape defect - the scanner reads the "
        "LAST heartbeat line and needs 'tick <n>', while R2366 wrote pure "
        "narrative, so the row existed but could not parse; repaired by "
        "carrying the token in the new line, history untouched. CRAWL: "
        "wx.requestVirtualPayment official API page, one fetch, zero key, zero "
        "retry - signData is an Object passed as a JSON STRING and its nine "
        "fields plus twenty-five error codes are now on file; three gates "
        "follow from the page itself: -15011 (live builds accept env=0 only, "
        "so sandbox is not a production verification path), -15002 with the "
        "outTradeNo note (one-use and not guaranteed unique, so the "
        "idempotency key stays ours), -15013 (goodsPrice checked against the "
        "console item price, so publish before ordering). Consumed into "
        "benchmarks sections 1/3/4, wall W37 plus conclusion, and the pay-spec "
        "field gate. Battery NOT run: reconcile-battery-R2367 remains open at "
        "its measured 494 suites / 3940 criteria and is the next window first "
        "item. Zero product code, 0 product points, disclosed.",
    ])
    data["self_drive"] = {
        "window": window,
        "window_days": derived["window_days"],
        "log_lines_in_window": derived["log_lines_in_window"],
        "idle_fast_mention_lines": derived["idle_fast_mention_lines"],
        "no_pullable_mention_lines": derived["no_pullable_mention_lines"],
        "substantive_non_idle_mention_lines":
            derived["substantive_non_idle_mention_lines"],
        "proposals_total": derived["proposals_total"],
        "proposals_open": derived["proposals_open"],
        "queue_main_open": derived["queue_main_open"],
        "queue_tech_open": derived["queue_tech_open"],
        "queue_explore_open": derived["queue_explore_open"],
    }
    tick_rows = [row for row in data["results"]
                 if isinstance(row, list) and len(row) >= 2
                 and row[1] == "OSLoop \u6267\u884c tick"]
    if len(tick_rows) != 1:
        raise SystemExit("E_EXP_TICK rows=%d" % len(tick_rows))
    tick_rows[0][0] = str(_state["tick"])
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(text)
    print("EXPORT R2367 self_drive=%s" % json.dumps(data["self_drive"]))
    print("EXPORT bytes=%d" % len(text.encode("utf-8")))
    if not execute:
        print("DRY RUN: pass --execute to write")
        return 0
    with io.open(EXPORT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    with io.open(EXPORT, "r", encoding="utf-8") as handle:
        back = handle.read()
    ok = back == text and json.loads(back)["export_ts"] == STAMP
    print("READBACK ok=%s" % ok)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))