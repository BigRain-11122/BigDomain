#!/usr/bin/env python3
"""Render the buyer price-reaction face on one page a human opens.

Why this exists: api_buyer_price_reaction answers "of the shelves I
watched, what did the price do afterwards and did I buy", with its own
AC-BPR1..AC-BPR8 criteria, but a grep over tools/, preview/ and the report
collector answered zero hits, so that reading could only be taken by
calling the sandbox from a shell. api_watch_alerts says what moved and
api_watch_budget says what the shelf costs now; neither links a movement
to the purchase that followed it.

Nothing here re-implements a market rule. The shipped demo world holds no
watch row and no price revision at all, so the fixture is built only with
the shipped doors publish_api / watch_api / revise_price / purchase_api
under a deterministic clock - no sqlite rewrite, no typed ids, no padded
rows. Every number on the page comes from the shipped face read over that
fixture; the page prints it and never recomputes a counter.

Scope: a market card that adds the per-buyer envelopes column by column
(and says so), then one section per buyer enumerated from the shipped
sales face, each read through the face's own buyer gate.

The real sandbox is never opened for writing and nothing touches the
network.

Usage:
  python tools/price_reaction_board.py
  python tools/price_reaction_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BPRB1..AC-BPRB6 are pre-registered in src/os/backlog.md (R3437 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/price-reaction-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "price-reaction-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "price-reaction-board.json")
COPY = os.path.join(ROOT, "preview", "price-reaction-board-copy.json")

FACE = "api_buyer_price_reaction"
BOARD_FACE = "api_board"
SALES_FACE = "api_sales"
DIRECTIONS = ("drop", "flat", "rise")

PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "scope", "buyer_id", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "drop_count",
    "drop_converted_count", "drop_rate", "flat_count",
    "flat_converted_count", "flat_rate", "rise_count",
    "rise_converted_count", "rise_rate", "delta_sum", "avg_delta",
    "largest_drop", "largest_rise", "listing_count", "seller_count",
    "directions", "disclaimer",
)

ROW_KEYS = (
    "direction", "watch_count", "pre_owned_count", "funnel_count",
    "converted_count", "pending_count", "conversion_rate", "delta_sum",
    "avg_delta", "largest_drop", "largest_rise",
)

COUNTERS = ("watch_count", "pre_owned_count", "funnel_count",
            "converted_count", "pending_count")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "kpi_watch", "kpi_funnel", "kpi_converted", "kpi_pending",
    "kpi_preowned", "kpi_rate", "kpi_avg", "kpi_delta", "kpi_drop",
    "kpi_rise", "kpi_listing", "kpi_seller",
    "kpi_dir_watch", "kpi_dir_funnel", "kpi_dir_converted",
    "kpi_dir_pending", "kpi_dir_rate", "kpi_dir_avg", "kpi_dir_delta",
    "kpi_dir_drop", "kpi_dir_rise",
    "col_direction", "col_watch", "col_preowned", "col_funnel",
    "col_converted", "col_pending", "col_rate", "col_avg", "col_delta",
    "col_extreme", "col_bar",
    "badge_drop", "badge_flat", "badge_rise", "badge_conv", "badge_pend",
    "market_scope", "buyer_scope",
    "empty_buyer", "none", "bar_caption",
    "law_count", "law_preowned", "law_funnel", "law_pending", "law_rate",
    "law_order", "law_delta", "law_rollup", "law_bar", "law_notadvice",
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
.badge.drop{background:#fdeeee;border-color:#f0cccc;color:#8a3030}
.badge.rise{background:#eef7ee;border-color:#c9e2c9;color:#2e6b34}
.badge.flat{background:#f2f5f8;color:var(--muted)}
.badge.conv{background:#eef4fb;border-color:#c8d9ef;color:#28527f}
.badge.pend{background:#f6f7f9;color:var(--muted)}
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
    code = "E_PRB_FACE"


class LawError(Exception):
    code = "E_PRB_LAW"


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
    """Build the reaction fixture through the shipped doors only.

      data  (dana): bob watches d1 at 10, d1 drops to 6, bob buys  -> converted drop
                    bob watches d2 at 20, d2 rises to 26, no buy  -> pending rise
                    bob watches d3 at 5, never revised, no buy    -> pending flat
      tools (frank): carol buys f1 at 7 then watches it           -> pre_owned flat
                    carol watches f2 at 12, f2 drops to 5, buys  -> converted drop
                    erin watches f1 at 7, f1 rises to 9, no buy   -> pending rise
      usr:dave never watches anything                              -> honest empty
    """
    clock = R.Clock()
    orig_now = A._now_utc
    orig_led_now = L.now_utc
    A._now_utc = clock.now_utc
    L.now_utc = clock.now_utc
    try:
        led.mint_to_pool("pool:reserve", 20000, "SETTLE-PRB-A",
                         "settlement")
        led.mint_to_pool("pool:share", 20000, "SETTLE-PRB-S",
                         "settlement")
        for who in ("bob", "carol", "erin", "dave"):
            led.ensure_account("usr:" + who, census_avatar_id=who)
            led.adjust([("pool:reserve", "debit", 300),
                        ("usr:" + who, "credit", 300)],
                       "manual:fund-" + who, "board demo funding " + who)
        dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
        dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

        clock.value = "2026-10-01T00:00:00Z"
        d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                            "portfolio risk scan endpoint", PAYLOAD, 10,
                            False, category="data")["listing_id"]
        d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                            "daily macro data feed", PAYLOAD, 20, True,
                            category="data")["listing_id"]
        d3 = am.publish_api("usr:dana", "chart-raw", "Raw Chart API",
                            "uncategorized chart payloads", PAYLOAD, 5,
                            False)["listing_id"]
        f1 = am.publish_api("usr:frank", "chart-kit", "Chart Kit API",
                            "deterministic chart payloads", PAYLOAD, 7,
                            False, category="tools")["listing_id"]
        f2 = am.publish_api("usr:frank", "grid-kit", "Grid Kit API",
                            "deterministic grid payloads", PAYLOAD, 12,
                            False, category="tools")["listing_id"]
        f3 = am.publish_api("usr:frank", "log-kit", "Log Kit API",
                            "deterministic log payloads", PAYLOAD, 3,
                            False, category="tools")["listing_id"]

        clock.value = "2026-10-02T09:00:00Z"
        am.watch_api("usr:bob", d1)
        clock.value = "2026-10-03T09:00:00Z"
        am.revise_price("usr:dana", d1, 6)
        clock.value = "2026-10-04T09:00:00Z"
        am.purchase_api("usr:bob", d1, "ref-bob-d1")

        clock.value = "2026-10-05T09:00:00Z"
        am.watch_api("usr:bob", d2)
        clock.value = "2026-10-06T09:00:00Z"
        am.revise_price("usr:dana", d2, 26)

        clock.value = "2026-10-07T09:00:00Z"
        am.watch_api("usr:bob", d3)

        clock.value = "2026-10-08T09:00:00Z"
        am.purchase_api("usr:carol", f1, "ref-carol-f1")
        clock.value = "2026-10-09T09:00:00Z"
        am.watch_api("usr:carol", f1)

        clock.value = "2026-10-10T09:00:00Z"
        am.watch_api("usr:carol", f2)
        clock.value = "2026-10-11T09:00:00Z"
        am.revise_price("usr:frank", f2, 5)
        clock.value = "2026-10-12T09:00:00Z"
        am.purchase_api("usr:carol", f2, "ref-carol-f2")

        clock.value = "2026-10-13T09:00:00Z"
        am.watch_api("usr:erin", f1)
        clock.value = "2026-10-14T09:00:00Z"
        am.revise_price("usr:frank", f1, 9)

        # erin and dave buy a shelf they never watch, so the shipped sales
        # face enumerates them: erin then carries a pending watch, dave is
        # the honest empty envelope that is landed rather than probed.
        clock.value = "2026-10-15T09:00:00Z"
        am.purchase_api("usr:erin", d3, "ref-erin-d3")
        clock.value = "2026-10-16T09:00:00Z"
        am.purchase_api("usr:dave", f3, "ref-dave-f3")
    finally:
        A._now_utc = orig_now
        L.now_utc = orig_led_now


def read_world():
    """Market envelope plus one envelope per buyer on the shipped sales face."""
    tmp_root = tempfile.mkdtemp(prefix="prb-")
    db = os.path.join(tmp_root, "prb.db")
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
        buyers = []
        for seller in sellers:
            for row in am.api_sales(seller)["sales"]:
                buyer = str(row["buyer_id"])
                if buyer not in buyers:
                    buyers.append(buyer)
        buyers.sort()
        blocks = [dict(am.api_buyer_price_reaction(buyer))
                  for buyer in buyers]
        disclaimer = blocks[0]["disclaimer"] if blocks else None
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
        raise FaceError("no buyer on the shipped sales face")
    for envelope in blocks:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("buyer_id"), ",".join(missing)))
        order = [row["direction"] for row in envelope["directions"]]
        if order != list(DIRECTIONS):
            raise FaceError("direction order moved on %r: %s"
                            % (envelope.get("buyer_id"), ",".join(order)))
        for row in envelope["directions"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("direction"), ",".join(missing)))
    return blocks, buyers, disclaimer


def block_problems(envelope, label):
    """AC-BPRB3 read at the source: refuse rather than print."""
    problems = []
    total = int(envelope["watch_count"])
    pre_owned = int(envelope["pre_owned_count"])
    funnel = int(envelope["funnel_count"])
    converted = int(envelope["converted_count"])
    pending = int(envelope["pending_count"])
    if funnel != total - pre_owned:
        problems.append("%s funnel != watch - pre_owned" % label)
    if funnel != converted + pending:
        problems.append("%s funnel != converted + pending" % label)
    for counter in COUNTERS:
        walked = sum(int(row[counter]) for row in envelope["directions"])
        if walked != int(envelope[counter]):
            problems.append("%s %s != sum of direction rows"
                            % (label, counter))
    delta_sum = sum(int(row["delta_sum"]) for row in envelope["directions"])
    if delta_sum != int(envelope["delta_sum"]):
        problems.append("%s delta_sum != sum of direction rows" % label)
    rate = envelope["conversion_rate"]
    if funnel == 0 and rate is not None:
        problems.append("%s rate printed with an empty funnel" % label)
    if funnel > 0 and rate is None:
        problems.append("%s rate lost with a non-empty funnel" % label)
    avg = envelope["avg_delta"]
    if total == 0 and avg is not None:
        problems.append("%s avg printed over an empty watch set" % label)
    if total > 0 and avg is None:
        problems.append("%s avg lost over a non-empty watch set" % label)
    for row in envelope["directions"]:
        if row["funnel_count"] and row["conversion_rate"] is None:
            problems.append("%s %s rate lost" % (label, row["direction"]))
        if not row["funnel_count"] and row["conversion_rate"] is not None:
            problems.append("%s %s rate printed" % (label, row["direction"]))
    return problems


def rollup(blocks):
    """The page's own column-wise sum; every cell is a sum of shipped cells."""
    out = {"scope": "market", "buyer_id": None}
    for key in COUNTERS:
        out[key] = sum(int(block[key]) for block in blocks)
    out["delta_sum"] = sum(int(block["delta_sum"]) for block in blocks)
    out["listing_count"] = sum(int(block["listing_count"]) for block in blocks)
    out["seller_count"] = sum(int(block["seller_count"]) for block in blocks)
    out["conversion_rate"] = (float(out["converted_count"]) / out["funnel_count"]
                              if out["funnel_count"] else None)
    out["avg_delta"] = (int(out["delta_sum"]) // out["watch_count"]
                        if out["watch_count"] else None)
    drops = [int(b["largest_drop"]) for b in blocks
             if b["largest_drop"] is not None]
    rises = [int(b["largest_rise"]) for b in blocks
             if b["largest_rise"] is not None]
    out["largest_drop"] = min(drops) if drops else None
    out["largest_rise"] = max(rises) if rises else None
    rows = []
    for name in DIRECTIONS:
        row = {"direction": name}
        for key in ("watch_count", "pre_owned_count", "funnel_count",
                    "converted_count", "pending_count", "delta_sum"):
            row[key] = sum(int(block["directions"][DIRECTIONS.index(name)][key])
                           for block in blocks)
        row["conversion_rate"] = (float(row["converted_count"])
                                  / row["funnel_count"]
                                  if row["funnel_count"] else None)
        row["avg_delta"] = (int(row["delta_sum"]) // row["watch_count"]
                            if row["watch_count"] else None)
        row_drops = [int(b["directions"][DIRECTIONS.index(name)]["largest_drop"])
                     for b in blocks
                     if b["directions"][DIRECTIONS.index(name)]["largest_drop"]
                     is not None]
        row_rises = [int(b["directions"][DIRECTIONS.index(name)]["largest_rise"])
                     for b in blocks
                     if b["directions"][DIRECTIONS.index(name)]["largest_rise"]
                     is not None]
        row["largest_drop"] = min(row_drops) if row_drops else None
        row["largest_rise"] = max(row_rises) if row_rises else None
        rows.append(row)
    out["directions"] = rows
    for name in DIRECTIONS:
        row = rows[DIRECTIONS.index(name)]
        out[name + "_count"] = row["watch_count"]
        out[name + "_converted_count"] = row["converted_count"]
        out[name + "_rate"] = row["conversion_rate"]
    out["disclaimer"] = blocks[0]["disclaimer"]
    return out


def fmt_rate(value):
    if value is None:
        return None
    return "%.1f%%" % (float(value) * 100.0)


def fmt_int(value):
    return None if value is None else "%d" % int(value)


def text(labels, key, value):
    if value is None:
        return '<span class="empty">%s</span>' % html.escape(labels["none"])
    return html.escape(str(value))


def card(labels, label, value, marker=None):
    attr = ' data-%s' % marker if marker else ""
    return ('<div%s><b>%s</b><span>%s</span></div>'
            % (attr, text(labels, "none", value), html.escape(labels[label])))


def bar(value):
    if value is None:
        return '<span class="empty">-</span>'
    width = max(0, min(100, int(round(float(value) * 100.0))))
    return ('<span class="bar"><span style="width:%d%%"></span></span>'
            % width)


def direction_rows(labels, envelope):
    out = ['<table><thead><tr>',
           '<th>%s</th>' % html.escape(labels["col_direction"]),
           '<th class="n">%s</th>' % html.escape(labels["col_watch"]),
           '<th class="n">%s</th>' % html.escape(labels["col_preowned"]),
           '<th class="n">%s</th>' % html.escape(labels["col_funnel"]),
           '<th class="n">%s</th>' % html.escape(labels["col_converted"]),
           '<th class="n">%s</th>' % html.escape(labels["col_pending"]),
           '<th class="n">%s</th>' % html.escape(labels["col_rate"]),
           '<th class="n">%s</th>' % html.escape(labels["col_bar"]),
           '<th class="n">%s</th>' % html.escape(labels["col_avg"]),
           '<th class="n">%s</th>' % html.escape(labels["col_delta"]),
           '<th>%s</th>' % html.escape(labels["col_extreme"]),
           '</tr></thead><tbody>']
    for row in envelope["directions"]:
        name = row["direction"]
        extreme = None
        if name == "drop" and row["largest_drop"] is not None:
            extreme = "%d" % int(row["largest_drop"])
        elif name == "rise" and row["largest_rise"] is not None:
            extreme = "%d" % int(row["largest_rise"])
        out.append(
            '<tr data-direction="%s"><td><span class="badge %s">%s</span></td>'
            '<td class="n">%d</td><td class="n">%d</td><td class="n">%d</td>'
            '<td class="n">%d</td><td class="n">%d</td>'
            '<td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%d</td><td>%s</td></tr>'
            % (name, name, html.escape(labels["badge_" + name]),
               int(row["watch_count"]), int(row["pre_owned_count"]),
               int(row["funnel_count"]), int(row["converted_count"]),
               int(row["pending_count"]),
               text(labels, "none", fmt_rate(row["conversion_rate"])),
               bar(row["conversion_rate"]),
               text(labels, "none", fmt_int(row["avg_delta"])),
               int(row["delta_sum"]),
               text(labels, "none", extreme)))
    out.append("</tbody></table>")
    out.append('<p class="note">%s</p>' % html.escape(labels["bar_caption"]))
    return "".join(out)


def kpi_block(labels, envelope, prefix):
    return "".join([
        card(labels, "kpi_watch", fmt_int(envelope["watch_count"]),
             prefix + "watch"),
        card(labels, "kpi_funnel", fmt_int(envelope["funnel_count"])),
        card(labels, "kpi_converted", fmt_int(envelope["converted_count"])),
        card(labels, "kpi_pending", fmt_int(envelope["pending_count"])),
        card(labels, "kpi_preowned", fmt_int(envelope["pre_owned_count"])),
        card(labels, "kpi_rate", fmt_rate(envelope["conversion_rate"])),
        card(labels, "kpi_avg", fmt_int(envelope["avg_delta"])),
        card(labels, "kpi_delta", fmt_int(envelope["delta_sum"])),
        card(labels, "kpi_drop", fmt_int(envelope["largest_drop"])),
        card(labels, "kpi_rise", fmt_int(envelope["largest_rise"])),
        card(labels, "kpi_listing", fmt_int(envelope["listing_count"])),
        card(labels, "kpi_seller", fmt_int(envelope["seller_count"])),
    ])


def render(payload, labels):
    market = payload["market"]
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<title>%s</title><style>%s</style></head><body><main>'
             % (html.escape(labels["title"]), CSS),
             '<h1>%s</h1>' % html.escape(labels["title"]),
             '<p class="meta">%s</p>' % html.escape(labels["sub"]),
             '<p class="meta">%s %s</p>'
             % (html.escape(labels["gen"]), html.escape(payload["generated_utc"])),
             '<div class="card"><span class="badge">%s</span>'
             % html.escape(labels["aigc"]),
             '<h2>%s</h2>' % html.escape(labels["sec_market"]),
             '<div class="kpi" data-market>%s</div>'
             % kpi_block(labels, market, "m_"),
             direction_rows(labels, market),
             '</div>',
             '<h2>%s</h2>' % html.escape(labels["sec_buyers"])]
    for block in payload["buyers"]:
        parts.append('<div class="card" data-buyer="%s">'
                     % html.escape(str(block["buyer_id"])))
        parts.append('<h3>%s &middot; %s</h3>'
                     % (html.escape(labels["buyer_scope"]),
                        html.escape(str(block["buyer_id"]))))
        if int(block["watch_count"]) == 0:
            parts.append('<p class="empty">%s</p>'
                         % html.escape(labels["empty_buyer"]))
        else:
            parts.append('<div class="kpi">%s</div>'
                         % kpi_block(labels, block, ""))
            parts.append(direction_rows(labels, block))
        parts.append("</div>")
    parts.append('<div class="card"><h2>%s</h2>' % html.escape(labels["sec_law"]))
    for key in ("law_count", "law_preowned", "law_funnel", "law_pending",
                "law_rate", "law_order", "law_delta", "law_rollup", "law_bar",
                "law_notadvice"):
        parts.append('<p class="law">%s</p>' % html.escape(labels[key]))
    parts.append("</div>")
    parts.append('<div class="card"><h2>%s</h2><p class="disclaimer">%s</p>'
                 '<p class="disclaimer">%s</p></div>'
                 % (html.escape(labels["sec_disc"]),
                    html.escape(payload["disclaimer"] or ""),
                    html.escape(labels["law_notadvice"])))
    parts.append('<div class="card"><h2>%s</h2><p class="note"><code>%s</code></p>'
                 % (html.escape(labels["sec_rep"]), html.escape(labels["cmd"])))
    parts.append('<p class="note">%s %s</p>'
                 % (html.escape(labels["foot"]),
                    html.escape(payload["face"])))
    parts.append("</div>")
    parts.append("</main></body></html>")
    return "".join(parts)


def build_payload():
    labels = read_copy()
    blocks, buyers, disclaimer = read_world()
    for block in blocks:
        problems = block_problems(block, str(block["buyer_id"]))
        if problems:
            raise LawError("; ".join(problems))
    market = rollup(blocks)
    problems = block_problems(market, "market")
    if problems:
        raise LawError("; ".join(problems))
    payload = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "market",
        "buyer_count": len(blocks),
        "buyers": blocks,
        "market": market,
        "disclaimer": disclaimer,
        "report": os.path.relpath(OUT_HTML, ROOT).replace(os.sep, "/"),
        "sources": source_fingerprints(),
        "sizes": {},
    }
    document = render(payload, labels)
    payload["sizes"]["html"] = len(document.encode("utf-8"))
    blob = ""
    for _pass in range(8):
        blob = json.dumps(payload, ensure_ascii=False, indent=2,
                          sort_keys=True)
        size = len(blob.encode("utf-8"))
        if payload["sizes"].get("json") == size:
            break
        payload["sizes"]["json"] = size
    else:
        raise FaceError("json size did not settle")
    return payload, document, labels, blob


def write_outputs(payload, document, blob):
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(document)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(blob)
    if os.path.getsize(OUT_JSON) != payload["sizes"]["json"]:
        raise FaceError("json size did not settle on disk")
    return (os.path.getsize(OUT_HTML), os.path.getsize(OUT_JSON))


def check():
    if not os.path.exists(OUT_JSON) or not os.path.exists(OUT_HTML):
        print("E_PRB_FACE landed pair missing")
        return 3
    with open(OUT_JSON, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    keys = set(payload.keys())
    if keys != set(PAYLOAD_KEYS):
        print("E_PRB_FACE top-level keys moved: %s"
              % ",".join(sorted(keys ^ set(PAYLOAD_KEYS))))
        return 2
    if payload["buyer_count"] != len(payload["buyers"]):
        print("E_PRB_FACE buyer_count != len(buyers)")
        return 2
    if not os.path.exists(os.path.join(ROOT, payload["report"])):
        print("E_PRB_FACE report path missing")
        return 2
    for block in [payload["market"]] + payload["buyers"]:
        problems = block_problems(block, str(block.get("buyer_id") or "market"))
        if problems:
            print("E_PRB_LAW %s" % "; ".join(problems))
            return 2
    sizes = payload["sizes"]
    if sizes.get("html") != os.path.getsize(OUT_HTML):
        print("E_PRB_FACE recorded html size moved")
        return 2
    if sizes.get("json") != os.path.getsize(OUT_JSON):
        print("E_PRB_FACE recorded json size moved")
        return 2
    page = open(OUT_HTML, "r", encoding="utf-8").read()
    for marker in ('data-market', 'data-buyer', 'data-direction'):
        if marker not in page:
            print("E_PRB_FACE page marker missing: %s" % marker)
            return 2
    print("PRICE-REACTION CHECK PASS fails=0 html=%dB json=%dB"
          % (sizes["html"], sizes["json"]))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.check:
        return check()
    try:
        payload, document, labels, blob = build_payload()
    except FaceError as exc:
        print("%s %s" % (exc.code, exc))
        return 3
    except LawError as exc:
        print("%s %s" % (exc.code, exc))
        return 3
    html_size, json_size = write_outputs(payload, document, blob)
    print("PRICE-REACTION CHECK PASS fails=0 html=%dB json=%dB"
          % (html_size, json_size))
    return 0


if __name__ == "__main__":
    sys.exit(main())
