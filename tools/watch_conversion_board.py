#!/usr/bin/env python3
"""Render the watch-to-purchase conversion funnel on one page a human opens.

Why this exists: api_watch_conversion answers "of everything residents
watched, what actually sold, how long did it take and what share converted"
with its own AC-WCV1..8 criteria, but a git grep over tools/, preview/ and
the report collector answered rc=1 with zero hits, so the funnel could only
be read by calling the sandbox from a shell. api_listing_demand answers
counts per listing and publishes no rate, no latency and no aggregate - and
it counts a purchase that predates the watch as a conversion.

Nothing here re-implements a market rule. Every number comes from the shipped
api_watch_conversion() face read over a fresh throwaway world seeded through
the shipped publish/watch/purchase/refund doors (the shipped demo world holds
no watch rows at all, so the funnel fixture is built with those doors under a
deterministic clock - no sqlite rewrite, no typed ids, no padded rows). The
page prints what the face hands it and never recomputes a counter; the laws
below are the face's own published laws, and a broken law refuses the render
instead of printing a plausible page.

Scope: the market card is the market-wide envelope, then one card per seller
enumerated from the shipped board face, each read through the face's own
dev_account scope so the isolation law is what the page shows.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/watch_conversion_board.py
  python tools/watch_conversion_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-WCVB1..AC-WCVB6 are pre-registered in src/os/backlog.md (R3436 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/watch-conversion-board-copy.json and appear in the rendered document
only, never in this file.
"""
import argparse
import datetime
import hashlib
import html
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
sys.path.insert(0, LEDGER_DIR)

import apimarket as A  # noqa: E402
import ledger as L  # noqa: E402
import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "watch-conversion-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "watch-conversion-board.json")
COPY = os.path.join(ROOT, "preview", "watch-conversion-board-copy.json")

FACE = "api_watch_conversion"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-WCVB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "market", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 15 keys.
ENVELOPE_KEYS = (
    "dev_account", "include_uncategorized", "watch_count",
    "pre_owned_count", "funnel_count", "converted_count", "pending_count",
    "conversion_rate", "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "oldest_pending_watch_utc", "categories", "disclaimer",
)

# One category row, 12 keys.
ROW_KEYS = (
    "category", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate",
    "avg_convert_seconds", "median_convert_seconds",
    "fastest_convert_seconds", "slowest_convert_seconds",
    "oldest_pending_watch_utc",
)

COUNTERS = ("watch_count", "pre_owned_count", "funnel_count",
            "converted_count", "pending_count")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_sellers", "sec_law", "sec_disc", "sec_rep",
    "kpi_watch", "kpi_funnel", "kpi_converted", "kpi_pending",
    "kpi_preowned", "kpi_rate", "kpi_avg", "kpi_median", "kpi_fastest",
    "kpi_slowest", "kpi_oldest",
    "col_category", "col_watch", "col_preowned", "col_funnel",
    "col_converted", "col_pending", "col_rate", "col_avg", "col_median",
    "col_fastest", "col_slowest", "col_oldest", "col_bar",
    "badge_converted", "badge_pending", "badge_preowned",
    "market_scope", "seller_scope",
    "empty_seller", "empty_categories", "none", "bar_caption",
    "law_count", "law_preowned", "law_funnel", "law_pending", "law_rate",
    "law_latency", "law_order", "law_scope", "law_bar", "law_notadvice",
    "cmd",
)

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:16px 0 6px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);
white-space:nowrap}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;
border:1px solid var(--line);font-size:11.5px;background:#f2f5f8;
color:#3c4653}
.badge.conv{background:#eef7ee;border-color:#c9e2c9;color:#2e6b34}
.badge.pend{background:#f6f7f9;color:var(--muted)}
.badge.own{background:#eef4fb;border-color:#c8d9ef;color:#28527f}
.bar{display:inline-block;height:8px;width:120px;background:#eef1f5;
border-radius:999px;overflow:hidden;vertical-align:middle}
.bar span{display:block;height:100%;background:#5b8def}
.note{color:var(--muted);font-size:12.5px;margin:8px 0 0}
.law{color:#3c4653;font-size:13px;margin:2px 0}
.empty{color:var(--muted);font-size:13px;margin:6px 0}
.disclaimer{color:var(--muted);font-size:12.5px}
code{font-size:12px;background:#f2f5f8;padding:1px 5px;border-radius:5px}
footer{color:var(--muted);font-size:12px;margin:26px 0 8px}
"""


class FaceError(Exception):
    code = "E_WCVB_FACE"


class LawError(Exception):
    code = "E_WCVB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if key not in labels]
    if missing:
        raise FaceError("label copy missing keys: %s" % ",".join(missing))
    return labels


def seed_world(am, led, dk):
    """Build the funnel through the shipped doors under a fixed clock.

    The shipped demo world carries no watch rows, so the fixture is made
    only with publish_api / watch_api / purchase_api / refund_api - the
    stamps come from the patched clock, never from a sqlite rewrite.

      data  (dana):  carol buys d1 then watches it  -> pre_owned
                     bob watches d1 then buys (+100) -> converted
                     bob watches d2, never buys      -> pending
      tools (frank): carol watches f1 then buys (+300) -> converted
                     erin watches f1 then buys (+1)   -> converted
                     dave buys f2 then watches        -> pre_owned
                     bob watches f2, never buys       -> pending
      no category:   erin watches d3, buys, refunds   -> pending (net law)
    """
    clock = R.Clock()
    orig_now = A._now_utc
    orig_led_now = L.now_utc
    A._now_utc = clock.now_utc
    L.now_utc = clock.now_utc
    try:
        led.mint_to_pool("pool:reserve", 20000, "SETTLE-WCVB-A",
                         "settlement")
        led.mint_to_pool("pool:share", 20000, "SETTLE-WCVB-S",
                         "settlement")
        for who in ("bob", "carol", "dave", "erin"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 300),
                        ("usr:" + who, "credit", 300)],
                       "manual:fund-" + who, "board demo funding " + who)
        dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
        dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

        clock.value = "2026-10-31T23:43:20Z"
        d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                            "portfolio risk scan endpoint", PAYLOAD,
                            10, False, category="data")["listing_id"]
        d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                            "daily macro data feed", PAYLOAD, 3, True,
                            category="data")["listing_id"]
        d3 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                            "uncategorized chart payloads", PAYLOAD,
                            5, False)["listing_id"]
        f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                            "deterministic chart payloads", PAYLOAD, 7,
                            False, category="tools")["listing_id"]
        f2 = am.publish_api("usr:frank", "grid-kit", "Grid Kit API",
                            "deterministic grid payloads", PAYLOAD, 4,
                            False, category="tools")["listing_id"]

        clock.value = "2026-10-31T23:59:10Z"
        am.purchase_api("usr:carol", d1, "ref-carol-d1")
        clock.value = "2026-11-01T00:00:00Z"
        am.watch_api("usr:carol", d1)
        am.watch_api("usr:bob", d1)
        clock.value = "2026-11-01T00:01:40Z"
        am.purchase_api("usr:bob", d1, "ref-bob-d1")
        clock.value = "2026-11-01T00:03:20Z"
        am.watch_api("usr:bob", d2)
        clock.value = "2026-11-01T00:05:00Z"
        am.watch_api("usr:carol", f1)
        clock.value = "2026-11-01T00:10:00Z"
        am.purchase_api("usr:carol", f1, "ref-carol-f1")
        clock.value = "2026-11-01T00:10:00Z"
        am.watch_api("usr:erin", f1)
        clock.value = "2026-11-01T00:10:01Z"
        am.purchase_api("usr:erin", f1, "ref-erin-f1")
        clock.value = "2026-11-01T00:06:40Z"
        am.purchase_api("usr:dave", f2, "ref-dave-f2")
        clock.value = "2026-11-01T00:08:20Z"
        am.watch_api("usr:dave", f2)
        clock.value = "2026-11-01T00:11:40Z"
        am.watch_api("usr:bob", f2)
        clock.value = "2026-11-01T00:00:00Z"
        am.watch_api("usr:erin", d3)
        clock.value = "2026-11-01T00:08:20Z"
        bought = am.purchase_api("usr:erin", d3, "ref-erin-d3")
        clock.value = "2026-11-01T00:20:00Z"
        am.refund_api("usr:erin", bought["purchase_id"],
                      "listing did not match description")
    finally:
        A._now_utc = orig_now
        L.now_utc = orig_led_now


def read_world():
    """Market envelope plus one scoped envelope per seller on the board."""
    tmp_root = tempfile.mkdtemp(prefix="wcvb-")
    db = os.path.join(tmp_root, "wcvb.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        seed_world(am, led, dk)
        board = am.api_board()
        sellers = []
        for row in board["listings"]:
            seller = str(row["dev_account"])
            if seller not in sellers:
                sellers.append(seller)
        market = dict(am.api_watch_conversion())
        blocks = [dict(am.api_watch_conversion(dev_account=seller))
                  for seller in sellers]
        disclaimer = market["disclaimer"]
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not blocks:
        raise FaceError("no seller on the shipped board face")
    for envelope in [market] + blocks:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("dev_account"), ",".join(missing)))
        for row in envelope["categories"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("category"), ",".join(missing)))
    return market, blocks, sellers, disclaimer


def block_problems(envelope, label):
    """AC-WCVB3 read at the source: refuse rather than print."""
    problems = []
    watches = int(envelope["watch_count"])
    pre_owned = int(envelope["pre_owned_count"])
    funnel = int(envelope["funnel_count"])
    converted = int(envelope["converted_count"])
    pending = int(envelope["pending_count"])
    if watches != pre_owned + funnel:
        problems.append("%s watch != pre_owned + funnel" % label)
    if funnel != converted + pending:
        problems.append("%s funnel != converted + pending" % label)
    rate = envelope["conversion_rate"]
    want = (float(converted) / funnel) if funnel else None
    if rate is None and want is not None:
        problems.append("%s rate missing" % label)
    if rate is not None and (want is None or abs(float(rate) - want) > 1e-9):
        problems.append("%s rate != converted/funnel" % label)
    lat = [envelope["fastest_convert_seconds"],
           envelope["median_convert_seconds"],
           envelope["slowest_convert_seconds"],
           envelope["avg_convert_seconds"]]
    if converted == 0:
        if any(item is not None for item in lat):
            problems.append("%s latency non-null with zero conversions" % label)
    else:
        if any(item is None for item in lat):
            problems.append("%s latency null with conversions" % label)
        else:
            if not (lat[0] <= lat[1] <= lat[2]):
                problems.append("%s fastest/median/slowest out of order" % label)
            if not (lat[0] <= lat[3] <= lat[2]):
                problems.append("%s avg outside extremes" % label)
            if lat[0] < 0:
                problems.append("%s negative latency" % label)
    oldest = envelope["oldest_pending_watch_utc"]
    if (oldest is None) != (pending == 0):
        problems.append("%s oldest pending stamp vs pending count" % label)
    seen = []
    for row in envelope["categories"]:
        cat = row.get("category")
        if cat in seen:
            problems.append("%s duplicate category %r" % (label, cat))
        seen.append(cat)
    ordered = sorted(seen, key=lambda c: (c is None, c))
    if seen != ordered:
        problems.append("%s category order" % label)
    for key in COUNTERS:
        want_sum = sum(int(row[key]) for row in envelope["categories"])
        if want_sum != int(envelope[key]):
            problems.append("%s %s rows sum %d != %d"
                            % (label, key, want_sum, int(envelope[key])))
    for row in envelope["categories"]:
        row_pool = (int(row["watch_count"]), int(row["pre_owned_count"]),
                    int(row["funnel_count"]), int(row["converted_count"]),
                    int(row["pending_count"]))
        if row_pool[0] != row_pool[1] + row_pool[2]:
            problems.append("%s %r watch split" % (label, row.get("category")))
        if row_pool[2] != row_pool[3] + row_pool[4]:
            problems.append("%s %r funnel split" % (label, row.get("category")))
    return problems


def check_laws(market, blocks):
    problems = block_problems(market, "market")
    for envelope in blocks:
        problems.extend(block_problems(envelope, str(envelope["dev_account"])))
    for key in COUNTERS:
        want = sum(int(envelope[key]) for envelope in blocks)
        if want != int(market[key]):
            problems.append("market %s %d != seller sum %d"
                            % (key, int(market[key]), want))
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    return str(value)


def pct(rate, none_text):
    if rate is None:
        return none_text
    return "%.1f%%" % (float(rate) * 100.0)


def dur(seconds, none_text):
    if seconds is None:
        return none_text
    value = int(seconds)
    if value < 60:
        return "%ds" % value
    if value < 3600:
        return "%dm %ds" % (value // 60, value % 60)
    return "%dh %dm" % (value // 3600, (value % 3600) // 60)


def kpi_html(block, labels, e, dash):
    items = [
        (labels["kpi_watch"], fmt(block["watch_count"], dash)),
        (labels["kpi_preowned"], fmt(block["pre_owned_count"], dash)),
        (labels["kpi_funnel"], fmt(block["funnel_count"], dash)),
        (labels["kpi_converted"], fmt(block["converted_count"], dash)),
        (labels["kpi_pending"], fmt(block["pending_count"], dash)),
        (labels["kpi_rate"], pct(block["conversion_rate"], dash)),
        (labels["kpi_avg"], dur(block["avg_convert_seconds"], dash)),
        (labels["kpi_median"], dur(block["median_convert_seconds"], dash)),
        (labels["kpi_fastest"], dur(block["fastest_convert_seconds"], dash)),
        (labels["kpi_slowest"], dur(block["slowest_convert_seconds"], dash)),
        (labels["kpi_oldest"],
         fmt(block["oldest_pending_watch_utc"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def bar_html(row, labels, e):
    rate = row["conversion_rate"]
    if rate is None:
        return '<span class="badge pend">%s</span>' % e(labels["none"])
    width = max(0.0, min(100.0, float(rate) * 100.0))
    return ('<span class="bar"><span style="width:%.1f%%"></span></span>'
            % width)


def mix_cell(row, labels, e):
    return ('<span class="badge conv">%s %s</span> '
            '<span class="badge pend">%s %s</span> '
            '<span class="badge own">%s %s</span>'
            % (e(labels["badge_converted"]), e(str(row["converted_count"])),
               e(labels["badge_pending"]), e(str(row["pending_count"])),
               e(labels["badge_preowned"]), e(str(row["pre_owned_count"]))))


def rows_table(block, labels, e, dash):
    if not block["categories"]:
        return ('<p class="empty" data-categories-empty="1">%s</p>'
                % e(labels["empty_categories"]))
    head = "".join("<th>%s</th>" % e(labels[key]) for key in (
        "col_category", "col_watch", "col_preowned", "col_funnel",
        "col_converted", "col_pending", "col_rate", "col_avg", "col_median",
        "col_fastest", "col_slowest", "col_oldest", "col_bar"))
    body = []
    for row in block["categories"]:
        cat = row["category"]
        body.append(
            '<tr data-category="%s"><td>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td>%s</td><td>%s</td></tr>'
            % (e("__none__" if cat is None else str(cat)),
               e(dash if cat is None else str(cat)),
               e(fmt(row["watch_count"], dash)),
               e(fmt(row["pre_owned_count"], dash)),
               e(fmt(row["funnel_count"], dash)),
               e(fmt(row["converted_count"], dash)),
               e(fmt(row["pending_count"], dash)),
               e(pct(row["conversion_rate"], dash)),
               e(dur(row["avg_convert_seconds"], dash)),
               e(dur(row["median_convert_seconds"], dash)),
               e(dur(row["fastest_convert_seconds"], dash)),
               e(dur(row["slowest_convert_seconds"], dash)),
               e(fmt(row["oldest_pending_watch_utc"], dash)),
               bar_html(row, labels, e)))
    return ('<table><tr>%s</tr>%s</table>'
            '<p class=note>%s</p>'
            % (head, "".join(body), e(labels["bar_caption"])))


def mix_line(block, labels, e):
    return ('<p class=note>%s</p>'
            % mix_cell({"converted_count": block["converted_count"],
                        "pending_count": block["pending_count"],
                        "pre_owned_count": block["pre_owned_count"]},
                       labels, e))


def section_body(block, labels, e, dash, scope_text):
    return ('<p class=note>%s</p><div class=kpi>%s</div>%s%s'
            % (e(scope_text), kpi_html(block, labels, e, dash),
               mix_line(block, labels, e),
               rows_table(block, labels, e, dash)))


def build_html(market, blocks, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_preowned"],
            labels["law_funnel"], labels["law_pending"], labels["law_rate"],
            labels["law_latency"], labels["law_order"], labels["law_scope"],
            labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    seller_cards = "".join(
        '<div class=card data-seller="%s"><h3><code>%s</code></h3>%s</div>'
        % (e(str(block["dev_account"])), e(str(block["dev_account"])),
           section_body(block, labels, e, dash, labels["seller_scope"]))
        for block in blocks)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card data-market=1>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_market"]),
           section_body(market, labels, e, dash, labels["market_scope"]),
           e(labels["sec_sellers"]),
           seller_cards or ('<div class=card data-seller-empty="1">'
                            '<p class=empty>%s</p></div>'
                            % e(labels["empty_seller"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer or ""))


DISCLAIMER_SLOT = "[[NONADVICE_SLOT]]"


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def source_fingerprints():
    return {
        "driver": sha16(os.path.abspath(__file__)),
        "copy": sha16(COPY),
        "apimarket": sha16(os.path.join(LEDGER_DIR, "apimarket.py")),
        "report": sha16(os.path.join(LEDGER_DIR, "apimarket_report.py")),
    }


def check_sizes(html_path, json_path):
    fails = []
    if not (os.path.exists(html_path) and os.path.exists(json_path)):
        return ["artifacts missing: %s / %s" % (html_path, json_path)]
    with open(json_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    sizes = doc.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(html_path):
        fails.append("sizes html %s != %d on disk"
                     % (sizes.get("html"), os.path.getsize(html_path)))
    if sizes.get("json") != os.path.getsize(json_path):
        fails.append("sizes json %s != %d on disk"
                     % (sizes.get("json"), os.path.getsize(json_path)))
    return fails


def check_sources(json_path):
    if not os.path.exists(json_path):
        return ["artifacts missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    recorded = doc.get("sources") or {}
    live = source_fingerprints()
    fails = []
    for key in sorted(live):
        if recorded.get(key) != live[key]:
            fails.append("E_SOURCE_STALE %s recorded %s current %s"
                         % (key, recorded.get(key), live[key]))
    return fails


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--out", default=OUT_HTML)
    ap.add_argument("--json", default=OUT_JSON)
    ap.add_argument("--check", action="store_true",
                    help="verify landed sizes and that no recorded input moved")
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit:
        return 5
    if not os.path.exists(os.path.join(LEDGER_DIR, "apimarket.py")):
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py "
                         "missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("WATCH-CONVERSION CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, blocks, sellers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, blocks)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(market, blocks, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "market+seller",
        "seller_count": len(blocks),
        "sellers": [{key: block[key] for key in ENVELOPE_KEYS}
                    for block in blocks],
        "market": {key: market[key] for key in ENVELOPE_KEYS},
        "disclaimer": disclaimer,
        "report": os.path.relpath(args.out, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    # The json states both artifact sizes; only its own byte count is
    # self-referential, so iterate to the fixed point.
    for _ in range(6):
        payload["sizes"] = {
            "html": os.path.getsize(args.out),
            "json": (os.path.getsize(args.json)
                     if os.path.exists(args.json) else 0),
        }
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        if payload["sizes"]["json"] == os.path.getsize(args.json):
            break

    print("WATCH-CONVERSION %s bytes=%d sellers=%d watches=%d funnel=%d "
          "converted=%d pending=%d rate=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"], market["watch_count"],
             market["funnel_count"], market["converted_count"],
             market["pending_count"],
             pct(market["conversion_rate"], "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
