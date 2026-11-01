"""closeout_R2367.py - append this window's items and fold if the gate demands.

One-off for the round, same shape as closeout_R2366: the state file is written
through state_io.canon and any fold runs through state_fold.fold.

Usage: python src/os/closeout_R2367.py
"""

import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import state_fold  # noqa: E402
import state_io  # noqa: E402

STATE = os.path.join(REPO, "src", "os", "state.json")
GATE = 78500
RESERVE = 6000
FOLD_BASE = 643

ITEMS = [
    "2026-11-02 R2367 QA charter daily crawl round (five-silence scan at open: "
    "git status empty and no .git/index.lock, which the TREE face confirms; "
    "LEDGER 247 lines with atbd_lines=0 and unreplied_groups=0; DEC 165 rows "
    "against 81 known tokens and ZERO new ones; group orders tail still the "
    "2026-11-01 10:4x model-policy baseline already acknowledged as "
    "non-execution while the company own orders tail is older than that "
    "baseline, so ORD is informational not a new order; benchmarks 1 day old "
    "and inside the seven-day gate). The scan raised exactly two flags and both "
    "belong to this company itself, not to the group: [QA] today_png=0 "
    "today_log=0 bench_today=False, the charter daily crawl round due, and [HB] "
    "heartbeat_missing_or_unparsed.",
    "R2367 HB root cause measured, not assumed: tools/skills/bigdomain-loop-scan"
    "/scripts/scan_five_still.ps1 reads the LAST non-blank line of heartbeat.txt "
    "and matches 'tick (\\d+)' in it. The R2366 heartbeat row was written as "
    "pure narrative with no tick token, so the row existed and the parser still "
    "read missing_or_unparsed - a row-shape defect, not a missing row. Repaired "
    "by writing the token INTO the new line (src/os/heartbeat_R2367.py, "
    "read-back proved) rather than adding a second numeric row that would have "
    "left two competing shapes in a rolling one-line-per-round file. The R2366 "
    "line itself was left byte-identical: history is not rewritten.",
    "R2367 daily crawl executed (zero key, read-only, ONE fetch, no retry "
    "needed): the official client API page for wx.requestVirtualPayment at "
    "developers.weixin.qq.com/miniprogram/dev/api/payment/"
    "wx.requestVirtualPayment.html. READ FOR THE FIRST TIME IN THIS COMPANY: "
    "the parameter table and the error-code table. signData is an Object but "
    "must be passed as a JSON STRING; its fields are offerId (required, mp pay "
    "base config), buyQuantity (required), env (optional, 0 live / 1 sandbox, "
    "default 0), currencyType (required, CNY only), productId and goodsPrice "
    "(required only when mode=short_series_goods, goodsPrice in fen and used "
    "to check the console item price), activitySellingPrice (optional, must "
    "travel with goodsPrice), outTradeNo (required, 8-32 chars, "
    "[A-Za-z0-9 _-|@], no leading underscore, one use only, and the page says "
    "uniqueness is not guaranteed in extreme cases so business must not depend "
    "on it) and attach (required, passed through to the delivery notification). "
    "Error codes recorded verbatim: 1001/-1/-2/-4/-5/-15001..-15021.",
    "R2367 three constraints taken from that page and written as design gates, "
    "not as inference: (1) -15011 says the live build accepts env=0 only and "
    "refuses env=1, so a sandbox leg cannot be assumed to exist in production "
    "and the sandbox strategy becomes a contract-level fixture instead of a "
    "real endpoint; (2) -15002 plus the outTradeNo note means the order number "
    "is one-use AND not a uniqueness law, so the idempotency key stays OURS "
    "(strengthening AC-Y3, not restating it); (3) -15013 checks goodsPrice "
    "against the console item price, so the 19.9 item must be published and "
    "priced before any order is sent, which adds one bootstrap physical "
    "checklist row (item/currency publication). Two faces left unproven and "
    "recorded as M rather than asserted: base-library version line, and the "
    "iOS/Android split (Apple pay is a different source already on file, W34).",
    "R2367 consumed into three faces: docs/global-benchmarks.md section 1 "
    "(virtual-payment bullet gains the field-level note), section 3 (new "
    "source row) and section 4 (W37 update row); "
    "docs/research/intelligence-wall.md gains W37 main row plus its conclusion "
    "row, both naming the consumer (P-47 item 4 pay spec field gate, P-47 item "
    "2 ledger idempotency, bootstrap physical checklist); state.json "
    "benchmarks_refreshed := 2026-11-02 (was 2026-11-01, the seven-day gate "
    "would have expired 2026-11-09 and the charter 15h clock is satisfied). "
    "Evidence: qa/smoke-R2367.log (64 lines) and qa/smoke-R2367.png rendered "
    "from THAT log by tools/skills/bigdomain-loop-scan/scripts/"
    "render_smoke_png.ps1 (904x1415, 70-line cap) - a real render, never a "
    "hand-drawn image.",
    "R2367 battery NOT run and the row is NOT closed: debt_gate reads "
    "CLAIM-FIRST item=reconcile-battery-R2367 opened=R2366 with the measured "
    "target 494 suites / 3940 criteria (the matrix doc at HEAD still reads "
    "492/3928 from the R2364 leg, plus the R2365 os-queue-floor-delivered-wire "
    "suite and the R2366 os-battery-followup-help-wire suite, six criteria "
    "each). The charter crawl was the flag the scan raised and it takes "
    "precedence in this round budget; the battery is carried as the next "
    "window first item, on a committed tree, before any product edit. Scoring "
    "honestly: this window shipped no product code - a crawl round is "
    "0 product points - and the queue head state/queue/tech.md:413 AC-QFR1 "
    "carries unchanged.",
    "R2367 tokens: local=~18k api=0 api_reason=daily crawl round - one official "
    "page read once through the host fetch tool (zero key, no cloud LLM call), "
    "with the reading written into three canon faces and one evidence pair; the "
    "only other work was the heartbeat row-shape repair and the state/export "
    "closeout; zero external API touches beyond the single page read",
]


def read_state():
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_state(text):
    with io.open(STATE, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    with io.open(STATE, "r", encoding="utf-8", newline="") as handle:
        back = handle.read()
    return back


def block_boundaries(log):
    out = []
    for index, line in enumerate(log):
        if re.match(r"^(?:\d{4}-\d{2}-\d{2} )?R\d+ tokens:", line.strip()):
            out.append(index + 1)
    return out


def main():
    raw = read_state()
    before = len(raw.encode("utf-8"))
    data = json.loads(raw)
    tick = data.get("tick", 0) + 1
    data["tick"] = tick
    data["benchmarks_refreshed"] = "2026-11-02"
    data["log"] = list(data["log"]) + ITEMS
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    text = state_io.canon(text)
    write_state(text)
    size = len(text.encode("utf-8"))
    print("STATE tick=%d items=+%d before=%dB after=%dB"
          % (tick, len(ITEMS), before, size))

    guard = 0
    while True:
        measure = state_fold.measure(size, GATE)
        if not measure["fold_needed"]:
            print("FOLD none needed bytes=%d margin=%d"
                  % (size, measure["margin"]))
            break
        current = read_state()
        state = json.loads(current)
        log = state["log"]
        ends = block_boundaries(log)
        target = GATE - RESERVE
        chosen = None
        for end in ends:
            if end >= len(log):
                continue
            window = log[:end]
            found = set()
            for line in window:
                found |= set(state_fold.PAT.findall(line))
            rounds = sorted(set(re.findall(r"R(\d{4})", " ".join(window))))
            summary = ("Fold %d: log lines 1..%d folded verbatim into the "
                       "archive at a TRUE round-block boundary; rounds %s; "
                       "tokens %s"
                       % (FOLD_BASE + guard, end,
                          ",".join("R" + r for r in rounds),
                          " ".join(sorted(found))))
            try:
                plan, _folded = state_fold.plan_fold(
                    current.encode("utf-8"), state, 1, end, summary,
                    reserve=0, gate=GATE)
            except Exception as exc:  # noqa: BLE001 - reported, not hidden
                print("FOLD plan refused end=%d %s" % (end, exc))
                continue
            if not plan["token_ok"]:
                print("FOLD token gap end=%d missing=%d"
                      % (end, len(plan["tokens_missing"])))
                continue
            if plan["predicted_bytes"] <= target:
                chosen = (end, summary, plan)
        if chosen is None:
            print("FOLD none fits target=%d bytes=%d" % (target, size))
            break
        end, summary, plan = chosen
        state_fold.fold(REPO, "R2367", FOLD_BASE + guard, 1, end, summary,
                        reserve=0, gate=GATE, execute=True)
        size = os.path.getsize(STATE)
        print("FOLD %d window=1..%d predicted=%dB measured=%dB"
              % (FOLD_BASE + guard, end, plan["predicted_bytes"], size))
        guard += 1
        if guard > 6:
            print("FOLD guard tripped")
            break
    final = state_fold.measure(os.path.getsize(STATE), GATE)
    print("FINAL bytes=%d margin=%d fold_needed=%s verdict=%s"
          % (final["bytes"], final["margin"], final["fold_needed"],
             final["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())