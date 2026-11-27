#!/usr/bin/env python3
"""Render the seller shelf-supply rollup on one page a human opens.

Why this exists: api_supply answers ONE listing and api_supply_history answers
that one listing's restock history, so a seller holding N shelves had to open
api_supply N times to learn what the shop actually carries. api_seller_supply
rolls the shop up with its own AC-SSUP1..8 law, but a git grep over tools/ and
preview/ answered zero hits, so "how many shelves are live, how many are
limited, which are sold out, which sit at the low-stock line, how many units
are left, how many sold, how often did I restock" could only be asked of a
shell.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_supply() face read over a fresh throwaway demo world seeded through
the shipped report helpers. Sellers are enumerated through the shipped board
face instead of being typed by hand. The page prints what the face hands it and
never recomputes a total; the only checks it runs are the face's own published
laws, and a broken law refuses the render instead of printing a plausible page.

An unlimited shelf (published without a supply) reports None supply and None
remaining; it is excluded from the two supply totals while its sales still
count, so a shop whose every shelf is unlimited answers None for both totals.
That is printed as a dash, never as 0.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_supply_board.py
  python tools/seller_supply_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SSSB1..AC-SSSB6 are pre-registered in src/os/backlog.md (R3432 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-supply-board-copy.json and appear in the rendered document
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

import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "seller-supply-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-supply-board.json")
COPY = os.path.join(ROOT, "preview", "seller-supply-board-copy.json")

FACE = "api_seller_supply"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-SSSB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 16 keys.
ENVELOPE_KEYS = (
    "dev_account", "listing_count", "live_listing_count",
    "retired_listing_count", "tracked_listing_count",
    "unlimited_listing_count", "sold_out_listing_count",
    "low_stock_listing_count", "total_effective_supply", "total_sold",
    "total_remaining", "total_restocked_units", "total_restock_count",
    "low_stock_threshold", "disclaimer", "listings",
)

# One shelf row, 11 keys.
ROW_KEYS = (
    "listing_id", "listing_key", "delisted", "supply", "base_supply",
    "restocked_units", "restock_count", "sold", "remaining", "sold_out",
    "low_stock",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_sellers", "sec_law",
    "sec_disc", "sec_rep",
    "kpi_listings", "kpi_live", "kpi_retired", "kpi_tracked",
    "kpi_unlimited", "kpi_soldout", "kpi_low", "kpi_effective",
    "kpi_sold", "kpi_remaining", "kpi_restocked", "kpi_restocks",
    "kpi_threshold",
    "col_id", "col_key", "col_shelf", "col_track", "col_supply",
    "col_base", "col_restocked", "col_restocks", "col_sold",
    "col_remaining", "col_soldout", "col_low",
    "label_live", "label_retired", "label_tracked", "label_unlimited",
    "label_yes", "label_no", "empty_scope", "none",
    "law_count", "law_partition", "law_totals", "law_unlimited",
    "law_soldout", "law_low", "law_restock", "law_order", "law_scope",
    "law_notadvice",
    "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:18px 0 6px;font-weight:620;color:#3c4653}
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
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.live{border-color:#a9c6b0;color:#3f6a4c}
.badge.retired{border-color:#cfcfcf;color:#6b6b6b}
.badge.tracked{border-color:#b9c6d8;color:#3d5268}
.badge.unlimited{border-color:#d6ccb6;color:#6f5d33}
.badge.soldout{border-color:#dcb0b0;color:#8a4242}
.badge.low{border-color:#e0c898;color:#7a5f28}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
.note{color:var(--muted);font-size:12.5px;margin:6px 0 0}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_SSSB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_SSSB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


PAYLOAD = {"kind": "backtest", "calls": 50, "docs": "api/v1"}


def seed_scarcity(am):
    """Add the finite-shelf side the factory demo world never carries.

    The demo world publishes every shelf unlimited, so the tracked, sold-out,
    low-stock, restocked and retired rows would only ever be proved by a probe.
    These shelves are published, bought, restocked and retired through the
    shipped doors under a pinned clock, so the page proves those laws on
    landed rows. The fixture is a world builder, never a data source: every
    number on the page is still read back from api_seller_supply().
    """
    clock = R.Clock()
    orig = R.A._now_utc
    R.A._now_utc = clock.now_utc
    try:
        clock.value = "2026-11-01T00:00:00Z"
        bulk = am.publish_api("usr:dana", "bulk-scan", "Bulk Scan API",
                              "batch scan endpoint", PAYLOAD, 3, False,
                              supply=4, category="data")["listing_id"]
        edge = am.publish_api("usr:dana", "edge-pack", "Edge Pack API",
                              "edge feature pack", PAYLOAD, 2, False,
                              supply=2, category="data")["listing_id"]
        kit = am.publish_api("usr:dana", "report-kit", "Report Kit API",
                             "monthly report kit", PAYLOAD, 2, False,
                             supply=2, category="tools")["listing_id"]
        clock.value = "2026-11-02T00:00:00Z"
        am.purchase_api("usr:bob", bulk, "ref-bob-bulk")
        clock.value = "2026-11-03T00:00:00Z"
        am.purchase_api("usr:carol", edge, "ref-carol-edge")
        am.purchase_api("usr:dave", edge, "ref-dave-edge")
        clock.value = "2026-11-04T00:00:00Z"
        am.purchase_api("usr:erin", kit, "ref-erin-kit")
        clock.value = "2026-11-05T00:00:00Z"
        am.restock_api("usr:dana", kit, 2)
        clock.value = "2026-11-06T00:00:00Z"
        am.delist_api("usr:dana", kit)
    finally:
        R.A._now_utc = orig
    return bulk, edge, kit


def enumerate_sellers(board):
    """Seller ids through the shipped board face, never typed."""
    return sorted(set(str(row["dev_account"]) for row in board["listings"]))


def read_world():
    """Read one shelf envelope per seller from the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="seller-supply-board-")
    db = os.path.join(tmp_root, "seller-supply-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        seed_scarcity(am)
        board = getattr(am, BOARD_FACE)()
        sellers = [dict(getattr(am, FACE)(seller))
                   for seller in enumerate_sellers(board)]
        disclaimer = sellers[0]["disclaimer"] if sellers else None
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    for envelope in sellers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("dev_account"), ",".join(missing)))
        for row in envelope["listings"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("listing_id"), ",".join(missing)))
    return sellers, disclaimer


def _envelope_problems(envelope, label):
    """AC-SSSB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["listings"]
    threshold = int(envelope["low_stock_threshold"])
    if int(envelope["listing_count"]) != len(rows):
        problems.append("%s listing_count %r != rows %d"
                        % (label, envelope["listing_count"], len(rows)))
    live = sum(1 for row in rows if not row["delisted"])
    retired = sum(1 for row in rows if row["delisted"])
    if int(envelope["live_listing_count"]) != live:
        problems.append("%s live_listing_count %r != %d"
                        % (label, envelope["live_listing_count"], live))
    if int(envelope["retired_listing_count"]) != retired:
        problems.append("%s retired_listing_count %r != %d"
                        % (label, envelope["retired_listing_count"], retired))
    if live + retired != len(rows):
        problems.append("%s live+retired != listing_count" % label)
    tracked = [row for row in rows if row["supply"] is not None]
    unlimited = [row for row in rows if row["supply"] is None]
    if int(envelope["tracked_listing_count"]) != len(tracked):
        problems.append("%s tracked_listing_count %r != %d"
                        % (label, envelope["tracked_listing_count"],
                           len(tracked)))
    if int(envelope["unlimited_listing_count"]) != len(unlimited):
        problems.append("%s unlimited_listing_count %r != %d"
                        % (label, envelope["unlimited_listing_count"],
                           len(unlimited)))
    if len(tracked) + len(unlimited) != len(rows):
        problems.append("%s tracked+unlimited != listing_count" % label)
    sold_out = sum(1 for row in tracked if bool(row["sold_out"]))
    low = sum(1 for row in tracked if bool(row["low_stock"]))
    if int(envelope["sold_out_listing_count"]) != sold_out:
        problems.append("%s sold_out_listing_count %r != %d"
                        % (label, envelope["sold_out_listing_count"], sold_out))
    if int(envelope["low_stock_listing_count"]) != low:
        problems.append("%s low_stock_listing_count %r != %d"
                        % (label, envelope["low_stock_listing_count"], low))
    if sold_out > len(tracked) or low > len(tracked):
        problems.append("%s a scarcity count outruns the tracked shelves"
                        % label)
    if int(envelope["total_sold"]) != sum(int(row["sold"]) for row in rows):
        problems.append("%s total_sold %r != row sum"
                        % (label, envelope["total_sold"]))
    if int(envelope["total_restocked_units"]) != sum(
            int(row["restocked_units"]) for row in rows):
        problems.append("%s total_restocked_units %r != row sum"
                        % (label, envelope["total_restocked_units"]))
    if int(envelope["total_restock_count"]) != sum(
            int(row["restock_count"]) for row in rows):
        problems.append("%s total_restock_count %r != row sum"
                        % (label, envelope["total_restock_count"]))
    want_effective = (sum(int(row["supply"]) for row in tracked)
                      if tracked else None)
    want_remaining = (sum(int(row["remaining"] or 0) for row in tracked)
                      if tracked else None)
    if envelope["total_effective_supply"] != want_effective:
        problems.append("%s total_effective_supply %r != %r"
                        % (label, envelope["total_effective_supply"],
                           want_effective))
    if envelope["total_remaining"] != want_remaining:
        problems.append("%s total_remaining %r != %r"
                        % (label, envelope["total_remaining"],
                           want_remaining))
    ids = [int(row["listing_id"]) for row in rows]
    if ids != sorted(ids):
        problems.append("%s listings are not ordered by listing_id" % label)
    if len(ids) != len(set(ids)):
        problems.append("%s carries one listing_id twice" % label)
    for row in rows:
        name = "%s/%s" % (label, row["listing_id"])
        if (row["supply"] is None) != (row["base_supply"] is None):
            problems.append("%s supply/base_supply disagree" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s carries an empty listing_key" % name)
        if not isinstance(row["delisted"], bool):
            problems.append("%s delisted %r is not a boolean"
                            % (name, row["delisted"]))
        for key in ("sold", "restocked_units", "restock_count"):
            if int(row[key]) < 0:
                problems.append("%s %s %r < 0" % (name, key, row[key]))
        if row["supply"] is None:
            if row["remaining"] is not None:
                problems.append("%s unlimited shelf carries a remaining"
                                % name)
            if row["sold_out"] or row["low_stock"]:
                problems.append("%s unlimited shelf claims scarcity" % name)
            continue
        if bool(row["sold_out"]) != (int(row["remaining"] or 0) == 0):
            problems.append("%s sold_out does not follow remaining" % name)
        if bool(row["low_stock"]) != (int(row["remaining"] or 0) <= threshold):
            problems.append("%s low_stock does not follow the threshold"
                            % name)
        if int(row["supply"]) < 0 or int(row["base_supply"]) < 0:
            problems.append("%s carries a negative shelf quantity" % name)
    return problems


def check_laws(sellers):
    problems = []
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s is not a seller account" % name)
    if sellers and sellers[0]["disclaimer"] != sellers[-1]["disclaimer"]:
        problems.append("sellers disagree on the disclaimer")
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_listings"], fmt(envelope["listing_count"], dash)),
        (labels["kpi_live"], fmt(envelope["live_listing_count"], dash)),
        (labels["kpi_retired"], fmt(envelope["retired_listing_count"], dash)),
        (labels["kpi_tracked"], fmt(envelope["tracked_listing_count"], dash)),
        (labels["kpi_unlimited"],
         fmt(envelope["unlimited_listing_count"], dash)),
        (labels["kpi_soldout"],
         fmt(envelope["sold_out_listing_count"], dash)),
        (labels["kpi_low"], fmt(envelope["low_stock_listing_count"], dash)),
        (labels["kpi_effective"],
         fmt(envelope["total_effective_supply"], dash)),
        (labels["kpi_sold"], fmt(envelope["total_sold"], dash)),
        (labels["kpi_remaining"], fmt(envelope["total_remaining"], dash)),
        (labels["kpi_restocked"],
         fmt(envelope["total_restocked_units"], dash)),
        (labels["kpi_restocks"], fmt(envelope["total_restock_count"], dash)),
        (labels["kpi_threshold"], fmt(envelope["low_stock_threshold"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def summary_table(sellers, labels, e, dash):
    head = (labels["sec_sellers"], labels["kpi_listings"], labels["kpi_live"],
            labels["kpi_retired"], labels["kpi_tracked"],
            labels["kpi_unlimited"], labels["kpi_soldout"], labels["kpi_low"],
            labels["kpi_effective"], labels["kpi_sold"],
            labels["kpi_remaining"], labels["kpi_restocked"],
            labels["kpi_restocks"])
    head_html = "<th>%s</th>" % e(head[0]) + "".join(
        '<th class=n>%s</th>' % e(cell) for cell in head[1:])
    body = []
    for block in sellers:
        cells = (fmt(block["listing_count"], dash),
                 fmt(block["live_listing_count"], dash),
                 fmt(block["retired_listing_count"], dash),
                 fmt(block["tracked_listing_count"], dash),
                 fmt(block["unlimited_listing_count"], dash),
                 fmt(block["sold_out_listing_count"], dash),
                 fmt(block["low_stock_listing_count"], dash),
                 fmt(block["total_effective_supply"], dash),
                 fmt(block["total_sold"], dash),
                 fmt(block["total_remaining"], dash),
                 fmt(block["total_restocked_units"], dash),
                 fmt(block["total_restock_count"], dash))
        body.append('<tr data-seller="%s"><td><code>%s</code></td>%s</tr>'
                    % (e(str(block["dev_account"])),
                       e(str(block["dev_account"])),
                       "".join('<td class=n>%s</td>' % e(str(cell))
                               for cell in cells)))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def rows_table(envelope, labels, e, dash):
    head = (labels["col_id"], labels["col_key"], labels["col_shelf"],
            labels["col_track"], labels["col_supply"], labels["col_base"],
            labels["col_restocked"], labels["col_restocks"], labels["col_sold"],
            labels["col_remaining"], labels["col_soldout"], labels["col_low"])
    left = (labels["col_id"], labels["col_key"], labels["col_shelf"],
            labels["col_track"], labels["col_soldout"], labels["col_low"])
    head_html = "".join(
        ("<th>%s</th>" % e(cell)) if cell in left
        else ('<th class=n>%s</th>' % e(cell)) for cell in head)
    body = []
    for row in envelope["listings"]:
        shelf = ("retired" if row["delisted"] else "live")
        track = ("unlimited" if row["supply"] is None else "tracked")
        badges = '<span class="badge %s">%s</span>' % (
            e(shelf), e(labels["label_retired" if row["delisted"]
                            else "label_live"]))
        badges += '<span class="badge %s">%s</span>' % (
            e(track), e(labels["label_unlimited" if row["supply"] is None
                            else "label_tracked"]))
        yes = labels["label_yes"]
        no = labels["label_no"]

        def flag(value, name):
            if not value:
                return no
            return '<span class="badge %s">%s</span>' % (e(name), e(yes))

        cells_left = (
            fmt(row["listing_id"], dash), fmt(row["listing_key"], dash),
            badges, flag(row["sold_out"], "soldout"),
            flag(row["low_stock"], "low"),
        )
        cells_right = (
            fmt(row["supply"], dash), fmt(row["base_supply"], dash),
            fmt(row["restocked_units"], dash), fmt(row["restock_count"], dash),
            fmt(row["sold"], dash), fmt(row["remaining"], dash),
        )
        tds = "".join("<td>%s</td>" % cell for cell in cells_left)
        tds += "".join('<td class=n>%s</td>' % e(str(cell))
                       for cell in cells_right)
        body.append('<tr data-shelf="%s" data-track="%s"'
                    ' data-listing="%s">%s</tr>'
                    % (e(shelf), e(track), e(str(row["listing_id"])), tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash)))


def build_html(sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_partition"],
            labels["law_totals"], labels["law_unlimited"],
            labels["law_soldout"], labels["law_low"], labels["law_restock"],
            labels["law_order"], labels["law_scope"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])),
           seller_section(block, labels, e, dash))
        for block in sellers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_sellers"]),
           summary_table(sellers, labels, e, dash),
           e(labels["sec_sellers"]),
           sections or ('<div class=card data-seller-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_scope"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer or ""))


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
    """AC-PWC76 (R3598): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: the landing already
    happened, so a refusal must not turn a good page into a traceback.
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
        print("SELLER-SUPPLY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        sellers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(sellers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "seller",
        "seller_count": len(sellers),
        "sellers": [{key: block[key] for key in ENVELOPE_KEYS}
                    for block in sellers],
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
    print("SELLER-SUPPLY %s bytes=%d sellers=%d shelves=%d tracked=%d"
          " sold_out=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"],
             sum(int(b["listing_count"]) for b in sellers),
             sum(int(b["tracked_listing_count"]) for b in sellers),
             sum(int(b["sold_out_listing_count"]) for b in sellers),
             face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
