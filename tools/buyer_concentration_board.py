#!/usr/bin/env python3
"""Render the per-buyer spend concentration reading into one page a human can
open.

Why this exists: api_buyer_concentration answers "is my money all on one shop
and one category, or is it spread" with its own AC-BC1..8 criteria, but a git
grep over tools/ and preview/ answered rc=1 with zero hits, so the reading
could only be had by calling the sandbox from a shell. The seller side has
api_seller_concentration; the buyer side has api_buyer_seller_spend and
api_buyer_category_spend - two lists of shares with no index at all - so a
resident could read every row and still not know whether the spend is
concentrated.

Nothing here re-implements a market rule. Every number comes from the shipped
api_buyer_concentration() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Buyers are enumerated through the shipped
board, sales and ratings faces instead of being typed by hand. The page prints
what the face hands it and never recomputes a total; the only checks it runs
are the face's own published laws, and a broken law refuses the render instead
of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/buyer_concentration_board.py
  python tools/buyer_concentration_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BCCB1..AC-BCCB6 are pre-registered in src/os/backlog.md (R3428 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-concentration-board-copy.json and appear in the rendered
document only, never in this file.
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

import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "buyer-concentration-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-concentration-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-concentration-board-copy.json")

FACE = "api_buyer_concentration"
BOARD_FACE = "api_board"
SALES_FACE = "api_sales"
RATINGS_FACE = "api_ratings"

# Pinned payload keys (AC-BCCB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "sales_face", "ratings_face",
    "buyer_count", "buyers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 20 keys.
ENVELOPE_KEYS = (
    "buyer_id", "purchase_count", "refund_count", "seller_count",
    "category_count", "refunded_sellers", "gross_spend", "refunded_tokens",
    "net_spend", "top1_seller_share", "top3_seller_share",
    "seller_herfindahl", "pareto_seller_count", "top1_category_share",
    "top3_category_share", "category_herfindahl", "pareto_category_count",
    "disclaimer", "sellers", "categories",
)

# One bucket row, 11 keys on each axis: the key column differs by axis.
ROW_COMMON = (
    "purchase_count", "refund_count", "net_purchase_count", "gross_spend",
    "refunded_tokens", "net_spend", "listing_count", "share",
    "cumulative_share", "rank",
)
SELLER_ROW_KEYS = ("dev_account",) + ROW_COMMON
CATEGORY_ROW_KEYS = ("category",) + ROW_COMMON

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_summary", "sec_sellers",
    "sec_categories", "sec_law", "sec_disc", "sec_rep",
    "col_buyer", "col_purchases", "col_refunds", "col_gross", "col_refunded",
    "col_net", "col_sellers", "col_categories", "col_verdict",
    "axis_sellers", "axis_categories",
    "col_rank", "col_bucket", "col_netpurch", "col_listings", "col_share",
    "col_cumulative", "col_bar",
    "kpi_top1", "kpi_top3", "kpi_hhi", "kpi_pareto",
    "label_uncategorized", "label_axis_seller", "label_axis_category",
    "empty_axis", "zero_net", "none", "tight", "spread", "mixed", "single",
    "law_totals", "law_rows", "law_rank", "law_share", "law_cumulative",
    "law_top1", "law_hhi", "law_pareto", "law_bar", "law_zero",
    "law_notadvice", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:16px 0 6px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:120px}
.bar i{display:block;height:9px;border-radius:999px;background:#6f8fb0}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.tight{border-color:#e0b4a8;color:#a4422c}
.badge.spread{border-color:#a8c4b0;color:#2f6b45}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_BCCB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_BCCB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_buyers(am, board):
    """Buyer ids through the shipped sales and ratings faces, never typed."""
    seen = set()
    devs = sorted(set(str(row["dev_account"]) for row in board["listings"]))
    for dev in devs:
        sales = getattr(am, SALES_FACE)(dev)
        for row in sales.get("sales") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    for listing in board["listings"]:
        rated = getattr(am, RATINGS_FACE)(listing["listing_id"])
        for row in rated.get("ratings") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    return sorted(seen)


def read_world():
    """Read one concentration block per buyer the shipped faces enumerate."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-concentration-board-")
    db = os.path.join(tmp_root, "buyer-concentration-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        buyers = [dict(getattr(am, FACE)(buyer))
                  for buyer in enumerate_buyers(am, board)]
        disclaimer = board["disclaimer"]
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not buyers:
        raise FaceError("no buyer enumerated through the shipped faces")
    for block in buyers:
        missing = [key for key in ENVELOPE_KEYS if key not in block]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (block.get("buyer_id"), ",".join(missing)))
        for axis, wanted in (("sellers", SELLER_ROW_KEYS),
                             ("categories", CATEGORY_ROW_KEYS)):
            for row in block[axis]:
                gap = [key for key in wanted if key not in row]
                if gap:
                    raise FaceError("row keys missing on %r %s: %s"
                                    % (block.get("buyer_id"), axis,
                                       ",".join(gap)))
    return buyers, disclaimer


def _close(a, b, tol=1e-6):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def check_laws(blocks):
    """AC-BCCB3 read at the source: refuse rather than print."""
    problems = []
    for block in blocks:
        name = str(block["buyer_id"])
        for axis, key in (("sellers", "dev_account"),
                          ("categories", "category")):
            rows = list(block[axis])
            total_net = int(block["net_spend"])
            if int(block["purchase_count"]) != sum(
                    int(r["purchase_count"]) for r in rows):
                problems.append("%s %s purchase sum != envelope" % (name, axis))
            if int(block["refund_count"]) != sum(
                    int(r["refund_count"]) for r in rows):
                problems.append("%s %s refund sum != envelope" % (name, axis))
            if int(block["gross_spend"]) != sum(
                    int(r["gross_spend"]) for r in rows):
                problems.append("%s %s gross sum != envelope" % (name, axis))
            if int(block["refunded_tokens"]) != sum(
                    int(r["refunded_tokens"]) for r in rows):
                problems.append("%s %s refunded sum != envelope" % (name, axis))
            if total_net != sum(int(r["net_spend"]) for r in rows):
                problems.append("%s %s net sum != envelope" % (name, axis))
            want_count = len(rows)
            if int(block["seller_count" if axis == "sellers"
                          else "category_count"]) != want_count:
                problems.append("%s %s bucket count != rows" % (name, axis))
            for index, row in enumerate(rows, 1):
                if int(row["rank"]) != index:
                    problems.append("%s %s rank %r at %d"
                                    % (name, axis, row["rank"], index))
                if int(row["net_purchase_count"]) != (
                        int(row["purchase_count"]) - int(row["refund_count"])):
                    problems.append("%s %s net purchases != purchases-refunds"
                                    % (name, axis))
                if int(row["net_spend"]) != (
                        int(row["gross_spend"]) - int(row["refunded_tokens"])):
                    problems.append("%s %s net spend != gross-refunded"
                                    % (name, axis))
            order = sorted(rows, key=lambda r: (
                -int(r["net_spend"]), -int(r["gross_spend"]),
                str(r[key])))
            if [r[key] for r in order] != [r[key] for r in rows]:
                problems.append("%s %s row order broken" % (name, axis))
            top1 = block["top1_%s_share" % ("seller" if axis == "sellers"
                                            else "category")]
            top3 = block["top3_%s_share" % ("seller" if axis == "sellers"
                                            else "category")]
            hhi = block.get("%s_herfindahl" % ("seller" if axis == "sellers"
                                               else "category"))
            pareto = block.get("pareto_%s_count" % ("seller"
                                                    if axis == "sellers"
                                                    else "category"))
            if total_net > 0:
                exact = [float(r["net_spend"]) / total_net for r in rows]
                if not rows or not _close(top1, round(exact[0], 6)):
                    problems.append("%s %s top1 %r != %r"
                                    % (name, axis, top1,
                                       round(exact[0], 6) if rows else None))
                if not _close(top3, round(sum(exact[:3]), 6)):
                    problems.append("%s %s top3 %r != %r"
                                    % (name, axis, top3,
                                       round(sum(exact[:3]), 6)))
                want_hhi = round(sum(v * v for v in exact) * 10000, 2)
                if not _close(hhi, want_hhi, 1e-3):
                    problems.append("%s %s hhi %r != %r"
                                    % (name, axis, hhi, want_hhi))
                running = 0
                want_pareto = None
                for index, row in enumerate(rows, 1):
                    running += int(row["net_spend"])
                    if running * 5 >= total_net * 4:
                        want_pareto = index
                        break
                if pareto != want_pareto:
                    problems.append("%s %s pareto %r != %r"
                                    % (name, axis, pareto, want_pareto))
                running = 0
                for row in rows:
                    if not _close(row["share"],
                                  round(float(row["net_spend"]) / total_net,
                                        6)):
                        problems.append("%s %s row share broken" % (name, axis))
                    running += int(row["net_spend"])
                    if not _close(row["cumulative_share"],
                                  round(float(running) / total_net, 6)):
                        problems.append("%s %s cumulative broken"
                                        % (name, axis))
                if not _close(rows[-1]["cumulative_share"], 1.0):
                    problems.append("%s %s last cumulative != 1.0"
                                    % (name, axis))
            else:
                for field, value in (("top1", top1), ("top3", top3),
                                     ("hhi", hhi), ("pareto", pareto)):
                    if value is not None:
                        problems.append("%s %s %s %r on a non-positive net"
                                        % (name, axis, field, value))
                for row in rows:
                    if row["share"] is not None or \
                            row["cumulative_share"] is not None:
                        problems.append("%s %s share %r on a non-positive net"
                                        % (name, axis, row["share"]))
            if int(block["seller_count"]) != len(block["sellers"]):
                problems.append("%s seller_count mismatch" % name)
            if int(block["category_count"]) != len(block["categories"]):
                problems.append("%s category_count mismatch" % name)
            if axis == "sellers":
                refunded = sum(1 for r in rows if int(r["refund_count"]) > 0)
                if int(block["refunded_sellers"]) != refunded:
                    problems.append("%s refunded_sellers %r != %d"
                                    % (name, block["refunded_sellers"],
                                       refunded))
            if int(block["gross_spend"]) - int(block["refunded_tokens"]) != \
                    total_net:
                problems.append("%s net != gross-refunded at envelope" % name)
    return problems


def pct(value):
    """Percent text for a 0..1 share; None stays None so the page can dash."""
    if value is None:
        return None
    return "%.1f%%" % (float(value) * 100.0)


def bar_width(share):
    if share is None:
        return 0.0
    return max(0.0, min(100.0, float(share) * 100.0))


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def verdict(block, labels):
    """A plain word about the seller axis; never a score, never a risk word."""
    top1 = block["top1_seller_share"]
    count = int(block["seller_count"])
    if top1 is None:
        return labels["zero_net"], "tight"
    if count <= 1:
        return labels["single"], "tight"
    if float(top1) >= 0.8:
        return labels["tight"], "tight"
    if float(top1) <= 0.4:
        return labels["spread"], "spread"
    return labels["mixed"], ""


def axis_table(rows, axis, labels, e):
    key = "dev_account" if axis == "sellers" else "category"
    head_cells = (labels["col_rank"], labels["col_bucket"],
                  labels["col_purchases"], labels["col_refunds"],
                  labels["col_netpurch"], labels["col_gross"],
                  labels["col_refunded"], labels["col_net"],
                  labels["col_listings"], labels["col_share"],
                  labels["col_cumulative"], labels["col_bar"])
    right = {labels["col_purchases"], labels["col_refunds"],
             labels["col_netpurch"], labels["col_gross"],
             labels["col_refunded"], labels["col_net"],
             labels["col_listings"], labels["col_share"],
             labels["col_cumulative"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head_cells)
    if not rows:
        return ('<table><tr>%s</tr></table><p class=empty>%s</p>'
                % (head_html, e(labels["empty_axis"])))
    body = []
    for row in rows:
        bucket = row.get(key)
        bucket_text = (labels["label_uncategorized"]
                       if bucket in (None, "") else str(bucket))
        if row["share"] is None:
            # An undefined share never draws a bar: the width would read as a
            # zero share, which the face itself refuses to state.
            bar = '<span class=empty>%s</span>' % e(labels["none"])
        else:
            bar = ('<div class=bar><i style="width:%.1f%%"></i></div>'
                   % bar_width(row["share"]))
        cells = (
            ("n", fmt(row["rank"], labels["none"])),
            ("", fmt(bucket_text, labels["none"])),
            ("n", fmt(row["purchase_count"], labels["none"])),
            ("n", fmt(row["refund_count"], labels["none"])),
            ("n", fmt(row["net_purchase_count"], labels["none"])),
            ("n", fmt(row["gross_spend"], labels["none"])),
            ("n", fmt(row["refunded_tokens"], labels["none"])),
            ("n", fmt(row["net_spend"], labels["none"])),
            ("n", fmt(row["listing_count"], labels["none"])),
            ("n", fmt(pct(row["share"]), labels["none"])),
            ("n", fmt(pct(row["cumulative_share"]), labels["none"])),
        )
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        body.append('<tr class="%s" data-axis="%s" data-rank="%d">%s'
                    '<td class=bar-cell>%s</td></tr>'
                    % (axis, axis, int(row["rank"]), tds, bar))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def kpi_html(block, axis, labels, e):
    suffix = "seller" if axis == "sellers" else "category"
    items = [
        (labels["kpi_top1"], fmt(pct(block["top1_%s_share" % suffix]),
                                 labels["none"])),
        (labels["kpi_top3"], fmt(pct(block["top3_%s_share" % suffix]),
                                 labels["none"])),
        (labels["kpi_hhi"], fmt(block["%s_herfindahl" % suffix],
                                labels["none"])),
        (labels["kpi_pareto"], fmt(block["pareto_%s_count" % suffix],
                                   labels["none"])),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def build_html(blocks, labels, now, disclaimer):
    e = html.escape

    head = (labels["col_buyer"], labels["col_purchases"], labels["col_refunds"],
            labels["col_gross"], labels["col_refunded"], labels["col_net"],
            labels["col_sellers"], labels["col_categories"],
            labels["col_verdict"])
    right = {labels["col_purchases"], labels["col_refunds"],
             labels["col_gross"], labels["col_refunded"], labels["col_net"],
             labels["col_sellers"], labels["col_categories"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)

    summary = []
    for block in blocks:
        word, klass = verdict(block, labels)
        cells = (
            ("", block["buyer_id"]),
            ("n", fmt(block["purchase_count"], labels["none"])),
            ("n", fmt(block["refund_count"], labels["none"])),
            ("n", fmt(block["gross_spend"], labels["none"])),
            ("n", fmt(block["refunded_tokens"], labels["none"])),
            ("n", fmt(block["net_spend"], labels["none"])),
            ("n", fmt(block["seller_count"], labels["none"])),
            ("n", fmt(block["category_count"], labels["none"])),
            ("", "<span class=badge %s>%s</span>" % (klass, e(word))),
        )
        tds = []
        for klass_cell, value in cells:
            if klass_cell == "" and str(value).startswith("<span"):
                tds.append("<td>%s</td>" % value)
            else:
                tds.append('<td class="%s%s">%s</td>'
                           % (klass_cell,
                              " neg" if str(value).startswith("-") else "",
                              e(str(value))))
        summary.append('<tr class=buyer data-buyer="%s">%s</tr>'
                       % (e(str(block["buyer_id"])), "".join(tds)))
    summary_table = "<table><tr>%s</tr>%s</table>" % (head_html,
                                                      "".join(summary))

    sections = []
    for block in blocks:
        sections.append(
            "<h2>%s &middot; <code>%s</code></h2>\n"
            "<div class=card><div class=kpi>%s</div>%s</div>\n"
            "<div class=card><div class=kpi>%s</div>%s</div>\n"
            % (e(labels["sec_sellers"]), e(str(block["buyer_id"])),
               kpi_html(block, "sellers", labels, e),
               axis_table(block["sellers"], "sellers", labels, e),
               kpi_html(block, "categories", labels, e),
               axis_table(block["categories"], "categories", labels, e)))
        if int(block["net_spend"]) <= 0:
            sections.append('<div class=card><p class=empty>%s</p></div>\n'
                            % e(labels["zero_net"]))

    laws = [labels["law_totals"], labels["law_rows"], labels["law_rank"],
            labels["law_share"], labels["law_cumulative"], labels["law_top1"],
            labels["law_hhi"], labels["law_pareto"], labels["law_bar"],
            labels["law_zero"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "%s"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/buyer_concentration_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_summary"]),
           summary_table, "".join(sections), e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer))


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


def _landing_is_default(html_path, json_path):
    """True only when both halves land under THIS root's own preview/.

    The wanted folder is computed from ROOT, not from the rebindable --out and
    --json flags, so a run that redirects its outputs cannot pose as the root.
    """
    want = os.path.realpath(os.path.join(ROOT, "preview"))
    for path in (html_path, json_path):
        if os.path.dirname(os.path.realpath(path)) != want:
            return False
    return True


def _refresh_face(html_path, json_path):
    """AC-PWC38 (R3560): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: both halves are
    already on disk when this runs, so the caller's exit code stays its own.
    """
    if not _landing_is_default(html_path, json_path):
        return "SKIPPED scratch"
    try:
        os_src = os.path.join(ROOT, "src", "os")
        if os_src not in sys.path:
            sys.path.insert(0, os_src)
        import board_face_landing
        ok, note, _proof = board_face_landing.refresh_export_face(ROOT)
        return "WRITTEN" if ok else "REFUSED %s" % note
    except Exception as exc:  # the landing already happened; name the refusal
        return "SKIPPED %s" % type(exc).__name__


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
        print("BUYER-CONCENTRATION CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        blocks, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(blocks)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(blocks, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "sales_face": SALES_FACE,
        "ratings_face": RATINGS_FACE,
        "buyer_count": len(blocks),
        "buyers": blocks,
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

    face = _refresh_face(args.out, args.json)

    print("BUYER-CONCENTRATION %s bytes=%d buyers=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(blocks), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
