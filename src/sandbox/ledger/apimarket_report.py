"""Market ledger report generator for the BigDomain API marketplace.

BigDomain R2101. Claim row = state/queue/explore.md R2101; criteria
AC-AMRPT1..AC-AMRPT8 were registered there BEFORE this file existed
(honesty law; the AC-AMRPT prefix, this module name, the suite name and
the ledger-apimarket-report runner label were git-grep -F
zero-occupancy anchored 2026-10-24, rc=1).

Why this file exists: R2096..R2100 shipped five read faces
(api_seller_inbox, api_revenue_months, api_search sort, api_market_months,
api_buyer_months) and a git-grep of every one of them showed zero call
sites outside tests and bookkeeping - the "no consumer" idle form. This
module is the missing consumer: one command turns the settlement faces
into a self-contained, offline-openable HTML ledger report.

R2108 wires the public activity stream in: the R2107 api_market_feed
had zero product call sites (the no-consumer idle form again), so the
report now carries an "activity" block read fresh on every collect and
renders it as the Public activity section (schema 2 -> 3, additive).

R2110 wires the buyer's own history in: api_library, api_watchlist,
api_refund and api_rating_history had zero product call sites (the same
idle form), and api_rating_history was in fact unreachable because its
only handle, rating_id, was not exposed on any listing-wide face - so
the rating rows now carry it (additive key) and the report renders a
Buyer dossiers section (schema 4 -> 5, additive).

Faces consumed (read-only): api_market_stats, api_market_months,
api_revenue_months, api_buyer_profile, api_buyer_months, api_board,
api_sales, api_seller_inbox, api_buyer_todo, api_watch_alerts,
api_supply, api_market_feed, api_library, api_watchlist, api_refund,
api_rating_history.

Usage:
    python apimarket_report.py --db ledger.db --seed --out report.html
    python apimarket_report.py --db ledger.db --out report.html

ASCII source. The rendered report is UTF-8 with LF endings, carries the
standing presentation-face markers (sandbox/AIGC label line and the
resident non-advisory disclaimer) and references no external resource.
"""

import argparse
import hashlib
import html
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
LOBBY = os.path.join(os.path.dirname(BASE), "lobby")
for _d in (BASE, LOBBY):
    if _d not in sys.path:
        sys.path.insert(0, _d)

import ledger as L                    # noqa: E402
import metered as M                   # noqa: E402
import apidev as D                    # noqa: E402
import apimarket as A                 # noqa: E402
from sec_gate import SecGate          # noqa: E402

DISCLAIMER = ("sandbox stand-in disclaimer: developer API"
              " marketplace is a service listing face, not"
              " investment advice")
PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}
MARKER = ("AIGC / sandbox artifact: synthetic demo data rendered locally"
          " by BigDomain OSLoop; every price is a service listing, not"
          " investment advice.")

# Machine-readable contract version for --json-out. Bump only on a
# breaking change to the envelope keys or the per-face payload shape.
# v2 (R2106) is an ADDITIVE bump: every v1 key keeps its value, and a
# buyer block gains the two resident faces todo/watch_alerts.
# v3 (R2108) is the same additive shape: the envelope keys are still
# exactly schema_version/report/attention and the report gains one key
# (activity) while every earlier key keeps its value.
# v4 (R2109) adds the dossiers key the same way.
# v5 (R2110) adds the history key inside every buyer block: the envelope
# is unchanged and every earlier buyer key keeps its value.
# v6 (R2111) adds the market-wide refunds register key at the report
# top level (same additive rule: no envelope change, no earlier value
# touched).
# v7 (R2113) adds the per-listing feed key inside every dossier block:
# the envelope is unchanged and every earlier dossier key keeps its
# value.
REPORT_SCHEMA = 7

BUYER_HISTORY_KEYS = ("library", "watchlist", "refunds", "rating_history")

REFUND_KEYS = ("refunds", "months", "by_dev")

REFUND_EMPTY = "no refunds in this market"

DOSSIER_KEYS = ("view", "lifecycle", "price_history",
                "metadata_history", "supply", "supply_history",
                "ratings", "rating_replies", "feed")
DOSSIER_EMPTY = "no listings in this market"

# How many of the newest activity events the report keeps. The feed's
# limit keeps the TAIL of the ordered stream, so the page always shows
# what happened most recently, and total still reports the full count.
FEED_LIMIT = 40

# Rows whose values are already month tables are rendered as tables, not
# as scalar key/value pairs.
TABLE_KEYS = ("months",)
SKIP_KEYS = ("disclaimer",)


class Clock(object):
    """Deterministic stamp holder used by the demo seeder."""

    def __init__(self):
        self.value = "2026-08-31T23:59:59Z"

    def now_utc(self):
        return self.value


def load_configs():
    with open(os.path.join(BASE, "config.json"), "rb") as handle:
        cfg = json.loads(handle.read().decode("utf-8"))
    with open(os.path.join(LOBBY, "config.json"), "rb") as handle:
        lobby_cfg = json.loads(handle.read().decode("utf-8"))
    return cfg, lobby_cfg


def build_stack(db_path, cfg=None, lobby_cfg=None):
    if cfg is None or lobby_cfg is None:
        cfg, lobby_cfg = load_configs()
    led = L.Ledger(db_path, cfg)
    metered = M.MeteredFace(led)
    dk = D.DevKeyFace(metered, DISCLAIMER)
    gate = SecGate.from_config(lobby_cfg)
    am = A.APIMarketFace(led, dk, gate, DISCLAIMER)
    return led, metered, dk, am


def seed_demo(am, led, dk):
    """Deterministic demo world: two sellers, four buyers, three
    listings, five purchases across three UTC months and one
    month-crossing refund. Same shape as the market-month suite so the
    report exercises a real settlement surface rather than one month of
    toy rows."""
    clock = Clock()
    led.mint_to_pool("pool:reserve", 9000, "SETTLE-REPORT-A",
                     "settlement")
    led.mint_to_pool("pool:share", 9000, "SETTLE-REPORT-S",
                     "settlement")
    for who in ("bob", "carol", "dave", "erin"):
        led.ensure_account("usr:" + who, census_avatar_id=who)
        led.adjust([("pool:reserve", "debit", 300),
                    ("usr:" + who, "credit", 300)],
                   "manual:fund-" + who, "report demo funding " + who)
    dk.issue_key("usr:dana", "dana-key", 10, ["backtest"], False)
    dk.issue_key("usr:frank", "frank-key", 10, ["backtest"], False)

    orig_now = A._now_utc
    orig_led_now = L.now_utc
    A._now_utc = clock.now_utc
    L.now_utc = clock.now_utc
    try:
        clock.value = "2026-08-20T10:00:00Z"
        d1 = am.publish_api("usr:dana", "risk-scan", "Risk Scan API",
                            "portfolio risk scan endpoint", PAYLOAD,
                            10, False)["listing_id"]
        d2 = am.publish_api("usr:dana", "macro-feed", "Macro Feed API",
                            "daily macro data feed", PAYLOAD, 3, True)[
                                "listing_id"]
        d3 = am.publish_api("usr:frank", "chart-render",
                            "Chart Render API",
                            "chart image render endpoint", PAYLOAD, 5,
                            False)["listing_id"]
        clock.value = "2026-08-31T23:59:59Z"
        p1 = am.purchase_api("usr:bob", d1, "ref-bob-d1")["purchase_id"]
        clock.value = "2026-09-01T00:00:00Z"
        am.purchase_api("usr:carol", d1, "ref-carol-d1")
        clock.value = "2026-09-15T12:00:00Z"
        am.purchase_api("usr:bob", d2, "ref-bob-d2")
        clock.value = "2026-09-20T08:30:00Z"
        p4 = am.purchase_api("usr:erin", d3, "ref-erin-d3")[
            "purchase_id"]
        clock.value = "2026-09-22T09:00:00Z"
        am.rate_api("usr:carol", d1, 5)
        am.rate_api("usr:bob", d2, 4)
        clock.value = "2026-10-02T00:00:00Z"
        am.refund_api("usr:bob", p1, "month-crossing refund")
        clock.value = "2026-10-03T00:00:00Z"
        am.refund_api("usr:erin", p4, "demo refund same month")
    finally:
        A._now_utc = orig_now
        L.now_utc = orig_led_now
    return {"listings": [d1, d2, d3], "refunded": [p1, p4]}


def collect_dossiers(am):
    """Read every per-listing history face once for every listing the
    market holds, live or retired.

    The report so far was market-wide, seller-wide and buyer-wide; the
    per-listing history faces (price, metadata, supply, lifecycle,
    ratings, replies) had no consumer at all, so an operator asking why
    one listing is not selling had to open six faces by hand. The
    listing set is derived from the market itself through api_search
    with include_delisted=True, so a retired listing keeps its dossier
    (retirement erases no history). Each call re-reads the faces -
    nothing is cached."""
    rows = am.api_search(include_delisted=True)["listings"]
    out = {}
    for row in rows:
        listing_id = int(row["listing_id"])
        out[str(listing_id)] = {
            "view": am.api_view(listing_id),
            "lifecycle": am.api_listing_lifecycle(listing_id),
            "price_history": am.api_price_history(listing_id),
            "metadata_history": am.api_metadata_history(listing_id),
            "supply": am.api_supply(listing_id),
            "supply_history": am.api_supply_history(listing_id),
            "ratings": am.api_ratings(listing_id),
            "rating_replies": am.api_rating_replies(listing_id),
            "feed": am.api_market_feed(listing_id=listing_id,
                                       limit=FEED_LIMIT),
        }
    return out


def collect_buyer_history(am, buyers):
    """Read the four buyer-side history faces once per buyer.

    R2110: api_library, api_watchlist, api_refund and
    api_rating_history had zero product call sites, and the last one
    could not even be reached - its only handle, rating_id, was not
    exposed by any listing-wide face. The rating rows carry it now
    (additive key), so this collector resolves each rated purchase to
    its rating id through api_ratings and reads the history behind it.
    Every value is re-read on each call: nothing is cached. Refund rows
    are the eleven-key provenance envelopes with the resident
    disclaimer stripped so the table stays one row shape."""
    out = {}
    for buyer in sorted(buyers):
        library = am.api_library(buyer)
        refunds = []
        history = []
        for row in library["purchases"]:
            if row["refunded"]:
                env = am.api_refund(row["purchase_id"])
                refunds.append(dict((k, v) for k, v in env.items()
                                    if k != "disclaimer"))
            if row["my_rating"] is None:
                continue
            for rated in am.api_ratings(row["listing_id"])["ratings"]:
                if rated["buyer_id"] == buyer:
                    history.append(
                        am.api_rating_history(rated["rating_id"]))
        out[buyer] = {"library": library,
                      "watchlist": am.api_watchlist(buyer),
                      "refunds": refunds,
                      "rating_history": history}
    return out


def collect(am):
    """Read every settlement face once and return the report payload.

    Seller and buyer ids are derived from the market itself (board
    listing owners and the buyers named on their sales rows), so the
    report never carries a hardcoded participant list."""
    board = am.api_board()
    sellers = sorted({row["dev_account"] for row in board["listings"]})
    buyers = set()
    sales = {}
    for dev in sellers:
        rows = am.api_sales(dev)
        sales[dev] = rows
        for row in rows["sales"]:
            buyers.add(row["buyer_id"])
    report = {
        "market": am.api_market_stats(),
        "market_months": am.api_market_months(),
        "board": board,
        "sellers": {},
        "buyers": {},
    }
    for dev in sellers:
        report["sellers"][dev] = {
            "revenue_months": am.api_revenue_months(dev),
            "sales": sales[dev],
            "profile": am.dev_profile(dev),
        }
    histories = collect_buyer_history(am, buyers)
    for buyer in sorted(buyers):
        report["buyers"][buyer] = {
            "profile": am.api_buyer_profile(buyer),
            "months": am.api_buyer_months(buyer),
            "todo": am.api_buyer_todo(buyer),
            "watch_alerts": am.api_watch_alerts(buyer),
            "history": histories[buyer],
        }
    report["activity"] = am.api_market_feed(limit=FEED_LIMIT)
    report["refunds"] = am.api_refund_register()
    report["dossiers"] = collect_dossiers(am)
    report["attention"] = collect_attention(am, report)
    return report


SEVERITY = {"high": 0, "warn": 1, "info": 2}


def collect_attention(am, report):
    """Derive an ordered operator to-do list from the read faces.

    R2101 turned the settlement faces into a statement; a statement
    still leaves the reader to spot what needs action. Every signal
    below already exists on a face (seller inbox debt, shelf state,
    negative settlement months) but no face aggregates them, so the
    report derives them here - never from a hardcoded roster, and
    never cached: each call re-reads the faces."""
    findings = []

    def add(kind, severity, subject, detail, ref):
        findings.append({"kind": kind, "severity": severity,
                         "subject": subject, "detail": detail,
                         "ref": ref})

    for dev in sorted(report["sellers"]):
        inbox = am.api_seller_inbox(dev)
        if inbox["unanswered_count"] > 0:
            add("rating_debt", "warn", dev,
                "%d unanswered rating(s); oldest %s"
                % (inbox["unanswered_count"],
                   inbox["oldest_unanswered_utc"]),
                inbox["oldest_unanswered_utc"] or "")
        for row in report["sellers"][dev]["revenue_months"]["months"]:
            if row["net"] < 0:
                add("negative_net", "warn", dev,
                    "seller net %d in %s" % (row["net"], row["month"]),
                    row["month"])
        for row in am.api_listing_demand(dev)["rows"]:
            if row["watcher_count"] >= 2 and row["converted_count"] == 0:
                add("unconverted_demand", "warn", dev,
                    "%d watcher(s) on %s with no sale yet"
                    % (row["watcher_count"], row["title"]),
                    row["listing_key"])
    for listing in report["board"]["listings"]:
        supply = am.api_supply(listing["listing_id"])
        if supply["sold_out"]:
            add("sold_out", "high",
                "listing:%d" % supply["listing_id"],
                "%s sold %d of %d units"
                % (listing.get("title") or supply["listing_key"],
                   supply["sold"], supply["supply"]),
                supply["listing_key"])
    for buyer in sorted(report["buyers"]):
        for row in report["buyers"][buyer]["months"]["months"]:
            if row["net"] < 0:
                add("negative_net", "warn", buyer,
                    "buyer net %d in %s" % (row["net"], row["month"]),
                    row["month"])

    findings.sort(key=lambda f: (SEVERITY[f["severity"]], f["kind"],
                                 f["subject"], f["detail"]))
    counts = {}
    for item in findings:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    return {"finding_count": len(findings),
            "severity_counts": dict((k, counts[k])
                                    for k in sorted(counts)),
            "findings": findings}


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def scalar_rows(envelope):
    keys = [k for k in envelope
            if k not in TABLE_KEYS and k not in SKIP_KEYS
            and not isinstance(envelope[k], (list, dict))]
    out = ["<table class=\"kv\">"]
    for key in keys:
        out.append("<tr><th>%s</th><td>%s</td></tr>"
                   % (esc(key), esc(envelope[key])))
    out.append("</table>")
    return "\n".join(out)


def row_table(rows, empty_text="no rows"):
    rows = rows or []
    if not rows:
        return "<p class=\"empty\">%s</p>" % esc(empty_text)
    cols = list(rows[0].keys())
    out = ["<table>", "<tr>"]
    for col in cols:
        out.append("<th>%s</th>" % esc(col))
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for col in cols:
            out.append("<td>%s</td>" % esc(row.get(col)))
        out.append("</tr>")
    out.append("</table>")
    return "\n".join(out)


def month_table(envelope):
    return row_table(envelope.get("months"), "no rows")


ATTENTION_EMPTY = ("no findings - every seller inbox is clear,"
                   " every shelf is in stock, no negative settlement"
                   " month")


def attention_block(attention):
    findings = attention.get("findings") or []
    if not findings:
        return "<p class=\"empty\">%s</p>" % esc(ATTENTION_EMPTY)
    counts = attention.get("severity_counts") or {}
    summary = ", ".join("%s=%s" % (esc(k), esc(counts[k]))
                        for k in sorted(counts))
    out = ["<p>%s finding(s): %s</p>"
           % (esc(attention.get("finding_count")), summary)]
    out.append("<table>")
    out.append("<tr><th>severity</th><th>kind</th><th>subject</th>"
               "<th>detail</th><th>ref</th></tr>")
    for item in findings:
        out.append("<tr>%s</tr>"
                   % "".join("<td>%s</td>" % esc(item.get(key))
                             for key in ("severity", "kind", "subject",
                                         "detail", "ref")))
    out.append("</table>")
    return "\n".join(out)


ACTIVITY_EMPTY = "no market events"
ACTIVITY_COLUMNS = ("event_utc", "kind", "listing", "title", "detail",
                    "value")


def event_value(row):
    """One readable cell for the varying part of an event row.

    The feed's row shape is fixed at thirteen keys with None where a
    field does not apply, so each kind carries its payload in a
    different column. The pinned precedence below turns whichever one
    is set into a single short string, so the section keeps a stable
    six-column table instead of thirteen mostly empty ones."""
    if row.get("amount") is not None:
        return "amount %s" % row.get("amount")
    if row.get("units") is not None:
        return "units %s" % row.get("units")
    if row.get("stars") is not None:
        if row.get("previous_stars") is not None:
            return "stars %s (was %s)" % (row.get("stars"),
                                          row.get("previous_stars"))
        return "stars %s" % row.get("stars")
    if row.get("token_price") is not None:
        return "price %s" % row.get("token_price")
    return ""


def activity_block(activity):
    events = activity.get("events") or []
    total = activity.get("total")
    shown = activity.get("returned", len(events))
    head = "showing %s of %s event(s)" % (esc(shown), esc(total))
    if activity.get("truncated"):
        head = head + " (newest first kept)"
    if not events:
        return ("<p class=\"empty\">%s</p>"
                % esc(ACTIVITY_EMPTY))
    out = ["<p>%s</p>" % head]
    out.append("<table>")
    out.append("<tr>%s</tr>"
               % "".join("<th>%s</th>" % esc(col)
                         for col in ACTIVITY_COLUMNS))
    for row in events:
        cells = (row.get("event_utc"), row.get("kind"),
                 row.get("listing_key"), row.get("title"),
                 row.get("detail"), event_value(row))
        out.append("<tr>%s</tr>"
                   % "".join("<td>%s</td>" % esc(cell) for cell in cells))
    out.append("</table>")
    return "\n".join(out)


REFUND_MONTH_COLUMNS = ("month", "refund_count", "amount", "dev_share",
                        "platform_share")
REFUND_DEV_COLUMNS = ("dev_account", "refund_count", "amount",
                      "dev_share", "platform_share")
REFUND_ROW_COLUMNS = ("refunded_utc", "listing_key", "title",
                      "dev_account", "buyer_id", "amount", "reason")


def refund_block(register):
    """Render the market-wide refund register (R2111, AC-AMRR8).

    The three groupings come from api_refund_register over one row set,
    so the page never merges faces by hand. An older report dict built
    before this key existed renders the honest empty state instead of
    raising."""
    rows = register.get("refunds") or []
    months = register.get("months") or []
    by_dev = register.get("by_dev") or []
    count = register.get("refund_count")
    if count is None:
        count = len(rows)
    head = "%s refund(s) totalling %s token(s) - dev %s / platform %s" % (
        esc(count), esc(register.get("amount")),
        esc(register.get("dev_share")), esc(register.get("platform_share")))
    out = ["<p>%s</p>" % head]
    if not rows:
        out.append("<p class=\"empty\">%s</p>" % esc(REFUND_EMPTY))
        return "\n".join(out)
    for label, columns, data in (
            ("by month", REFUND_MONTH_COLUMNS, months),
            ("by developer", REFUND_DEV_COLUMNS, by_dev),
            ("rows", REFUND_ROW_COLUMNS, rows)):
        out.append("<h3>refunds %s (%d)</h3>" % (esc(label), len(data)))
        out.append("<table>")
        out.append("<tr>%s</tr>"
                   % "".join("<th>%s</th>" % esc(col)
                             for col in columns))
        for row in data:
            out.append("<tr>%s</tr>"
                       % "".join("<td>%s</td>" % esc(row.get(col))
                                 for col in columns))
        out.append("</table>")
    return "\n".join(out)


STYLE = """
:root{--ink:#182033;--muted:#6b7280;--line:#e5e7eb;--bg:#f7f8fa;--accent:#3b5bdb;--ok:#2f9e44}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;color:var(--ink);background:var(--bg);line-height:1.6;padding:0 0 48px}
.wrap{max-width:1000px;margin:0 auto;padding:0 20px}
header{background:linear-gradient(135deg,#1f2b4d,#3b5bdb);color:#fff;padding:32px 0 24px}
header h1{font-size:24px}
header .sub{margin-top:6px;font-size:13px;opacity:.9}
.marker{margin-top:12px;font-size:12px;border:1px solid rgba(255,255,255,.5);border-radius:6px;padding:8px 10px}
h2{font-size:17px;margin:30px 0 10px;padding-left:10px;border-left:4px solid var(--accent)}
h3{font-size:14px;margin:18px 0 8px;color:var(--muted)}
h4{font-size:12px;margin:12px 0 6px;color:var(--muted);letter-spacing:.04em;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px;margin-bottom:14px}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:right}
th{background:#eef1f8;font-weight:600;text-align:center}
table.kv th{width:38%;text-align:left}
table.kv td{text-align:left}
.empty{color:var(--muted);font-size:13px;padding:6px 2px}
footer{margin-top:36px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
"""


def dossier_block(dossiers):
    """One dossier per listing: the full history of a single shelf.

    Each block opens with the effective view row, then the four
    append-only timelines (price, metadata, supply, lifecycle) and the
    two trust faces (ratings, replies) and the per-listing activity
    tail (R2113). Every dynamic string is escaped
    and every sub-table degrades to an honest empty state, so a listing
    with no revisions renders instead of raising."""
    if not dossiers:
        return "<p class=\"empty\">%s</p>" % esc(DOSSIER_EMPTY)
    out = []
    for key in sorted(dossiers, key=lambda k: int(k)):
        block = dossiers[key] or {}
        view = block.get("view") or {}
        title = view.get("title") or view.get("listing_key") or key
        state = "retired" if view.get("delisted") else "live"
        out.append("<h3>#%s %s (%s)</h3>"
                   % (esc(view.get("listing_id", key)), esc(title),
                      esc(state)))
        out.append(scalar_rows(view))
        price = block.get("price_history") or {}
        out.append("<h4>price history (%s revision(s))</h4>"
                   % esc(price.get("revision_count", 0)))
        out.append(row_table(price.get("revisions"), "no price revisions"))
        meta = block.get("metadata_history") or {}
        out.append("<h4>metadata history (%s revision(s))</h4>"
                   % esc(meta.get("revision_count", 0)))
        out.append(row_table(meta.get("revisions"),
                             "no metadata revisions"))
        supply = block.get("supply_history") or {}
        out.append("<h4>supply history (%s restock(s))</h4>"
                   % esc(supply.get("restock_count", 0)))
        out.append(row_table(supply.get("history"), "no restocks"))
        life = block.get("lifecycle") or {}
        out.append("<h4>lifecycle (%s event(s))</h4>"
                   % esc(len(life.get("history") or [])))
        out.append(row_table(life.get("history"), "no lifecycle events"))
        ratings = block.get("ratings") or {}
        out.append("<h4>ratings (%s)</h4>"
                   % esc(ratings.get("rating_count", 0)))
        out.append(row_table(ratings.get("ratings"), "no ratings"))
        replies = block.get("rating_replies") or {}
        out.append("<h4>replies (%s)</h4>"
                   % esc(replies.get("reply_count", 0)))
        out.append(row_table(replies.get("rows"), "no replies"))
        feed = block.get("feed") or {}
        out.append("<h4>recent activity (%s of %s event(s))</h4>"
                   % (esc(feed.get("returned", 0)),
                      esc(feed.get("total", 0))))
        out.append(activity_block(feed))
    return "\n".join(out)


BUYER_HISTORY_EMPTY = ("no purchases, watches, refunds or ratings for"
                       " this buyer yet")


def rating_history_rows(history):
    """Flatten the per-rating history envelopes into one table.

    A rating with no revision is still a fact (its base stamp), so it
    renders as a single "base" row; a revised rating renders one row per
    append-only revision. Every row keeps the same seven columns, which
    is why basis/stamp are projected here instead of nesting the raw
    envelopes."""
    rows = []
    for env in history or []:
        revisions = env.get("revisions") or []
        if not revisions:
            rows.append({"rating_id": env.get("rating_id"),
                         "listing_id": env.get("listing_id"),
                         "basis": "base",
                         "base_stars": env.get("base_stars"),
                         "previous_stars": None,
                         "stars": env.get("base_stars"),
                         "stamp": env.get("rated_utc")})
            continue
        for rev in revisions:
            rows.append({"rating_id": env.get("rating_id"),
                         "listing_id": env.get("listing_id"),
                         "basis": "revision",
                         "base_stars": env.get("base_stars"),
                         "previous_stars": rev.get("previous_stars"),
                         "stars": rev.get("stars"),
                         "stamp": rev.get("revised_utc")})
    rows.sort(key=lambda r: (r["rating_id"],
                             0 if r["basis"] == "base" else 1,
                             str(r["stamp"])))
    return rows


def buyer_history_block(history):
    """The four sub-tables of one buyer's own history.

    Each table degrades to an honest empty state, so a buyer who only
    ever bought (no watches, no refunds, no ratings) still renders."""
    history = history or {}
    library = history.get("library") or {}
    purchases = library.get("purchases") or []
    out = ["<h3>library (%d purchase(s))</h3>" % len(purchases)]
    out.append(row_table(purchases, "no purchases"))
    watches = (history.get("watchlist") or {}).get("watches") or []
    out.append("<h3>watchlist (%d)</h3>" % len(watches))
    out.append(row_table(watches, "no watches"))
    refunds = history.get("refunds") or []
    out.append("<h3>refunds (%d)</h3>" % len(refunds))
    out.append(row_table(refunds, "no refunds"))
    history_rows = rating_history_rows(history.get("rating_history"))
    out.append("<h3>rating history (%d row(s))</h3>" % len(history_rows))
    out.append(row_table(history_rows, "no ratings"))
    return "\n".join(out)


def render_html(report):
    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append("<html lang=\"zh-CN\"><head><meta charset=\"UTF-8\">")
    parts.append("<title>BigDomain API Market - Settlement Ledger</title>")
    parts.append("<style>%s</style></head><body>" % STYLE)
    parts.append("<header><div class=\"wrap\">")
    parts.append("<h1>BigDomain API Market - Settlement Ledger</h1>")
    parts.append("<div class=\"sub\">generated by apimarket_report.py -"
                 " purely derived from the read faces</div>")
    parts.append("<div class=\"marker\">%s</div>" % esc(MARKER))
    parts.append("</div></header><div class=\"wrap\">")

    parts.append("<h2>Market totals</h2>")
    parts.append(scalar_rows(report["market"]))

    parts.append("<h2>Market month timeline</h2>")
    parts.append(month_table(report["market_months"]))

    parts.append("<h2>Attention</h2>")
    # backward-compatible: a report dict built by an older caller (the
    # R2101 suite's synthetic escape fixture) carries no attention
    # block, so the page degrades to the honest empty state.
    parts.append(attention_block(report.get("attention") or {}))

    parts.append("<h2>Public activity</h2>")
    # same degrade rule for the R2108 activity block: an older report
    # dict renders the honest empty state instead of raising.
    parts.append(activity_block(report.get("activity") or {}))

    parts.append("<h2>Refund register</h2>")
    # same degrade rule for the R2111 register: an older report dict
    # renders the honest empty state instead of raising.
    parts.append(refund_block(report.get("refunds") or {}))

    parts.append("<h2>Listings</h2>")
    parts.append(row_table(report["board"].get("listings"),
                           "no live listings"))

    parts.append("<h2>Listing dossiers</h2>")
    # same degrade rule as the attention/activity blocks: an older
    # report dict carries no dossier key, so the page renders the
    # honest empty state instead of raising.
    parts.append(dossier_block(report.get("dossiers") or {}))

    parts.append("<h2>Sellers</h2>")
    for dev in sorted(report["sellers"]):
        block = report["sellers"][dev]
        parts.append("<h3>%s</h3>" % esc(dev))
        parts.append(scalar_rows(block["profile"]))
        parts.append(month_table(block["revenue_months"]))
        rows = block["sales"].get("sales") or []
        parts.append("<h3>%s - sales rows (%d)</h3>"
                     % (esc(dev), len(rows)))
        parts.append(row_table(rows, "no sales"))

    parts.append("<h2>Buyers</h2>")
    for buyer in sorted(report["buyers"]):
        block = report["buyers"][buyer]
        parts.append("<h3>%s</h3>" % esc(buyer))
        parts.append(scalar_rows(block["profile"]))
        parts.append(month_table(block["months"]))
        # R2106 resident workbench: a buyer block built by an older
        # caller carries neither key, so the page degrades to the
        # honest empty state instead of raising.
        todo = block.get("todo") or {}
        pending = todo.get("pending") or []
        parts.append("<h3>%s - rating debt (%d)</h3>"
                     % (esc(buyer), len(pending)))
        parts.append(row_table(pending, "no pending ratings"))
        alerts = (block.get("watch_alerts") or {}).get("alerts") or []
        parts.append("<h3>%s - watch alerts (%d)</h3>"
                     % (esc(buyer), len(alerts)))
        parts.append(row_table(alerts, "no watch alerts"))
        # R2110 buyer history: a block built by an older caller carries
        # no history key, so the four tables degrade to honest empties.
        parts.append("<h3>%s - buyer history</h3>" % esc(buyer))
        parts.append(buyer_history_block(block.get("history")))

    parts.append("<footer>%s</footer>" % esc(report["market"].get(
        "disclaimer") or DISCLAIMER))
    parts.append("</div></body></html>")
    return "\n".join(parts) + "\n"


def api_report_payload(report):
    """Wrap an already collected report in the versioned JSON envelope.

    The payload is a pure projection of the same collect() dict the
    HTML renderer consumes, so the two artifacts can never disagree."""
    return {"schema_version": REPORT_SCHEMA,
            "report": report,
            "attention": report.get("attention") or {}}


def write_report_json(path, report):
    """Write the machine-readable report atomically.

    Serialization happens in full before anything touches disk, and the
    file is published with temp+os.replace, so a failure leaves no
    half-written artifact behind."""
    payload = json.dumps(api_report_payload(report), sort_keys=True,
                         indent=1, ensure_ascii=True) + "\n"
    target = os.path.abspath(path)
    if not path or os.path.isdir(target):
        raise ValueError("--json-out needs a file path, got: %r" % (path,))
    out_dir = os.path.dirname(target)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    tmp = target + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
        os.replace(tmp, target)
    except Exception:
        if os.path.isfile(tmp):
            os.remove(tmp)
        raise
    return len(payload)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="apimarket_report.py",
        description="Render the BigDomain API market settlement ledger"
                    " as a self-contained HTML report (read faces only).")
    parser.add_argument("--db", required=True,
                        help="path to the ledger sqlite file")
    parser.add_argument("--out", required=True,
                        help="path of the HTML report to write")
    parser.add_argument("--seed", action="store_true",
                        help="seed the deterministic demo market first")
    parser.add_argument("--attention-out", default=None,
                        help="optional path for the attention findings"
                             " as machine-readable JSON (ASCII escaped)")
    parser.add_argument("--json-out", default=None,
                        help="optional path for the whole report as a"
                             " versioned machine-readable JSON payload"
                             " (ascii escaped, atomic write)")
    return parser


def write_attention_json(path, attention):
    payload = json.dumps(attention, sort_keys=True, indent=1,
                         ensure_ascii=True) + "\n"
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    return len(payload)


def main(argv=None):
    args = build_parser().parse_args(argv)
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = build_stack(args.db)
        if args.seed:
            seed_demo(am, led, dk)
        report = collect(am)
        page = render_html(report)
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(page)
        digest = hashlib.sha256(page.encode("utf-8")).hexdigest()
        print("report written: %s (%d bytes, sha256 %s)"
              % (args.out, len(page.encode("utf-8")), digest[:16]))
        attention = report["attention"]
        print("attention findings: %d (severity %s)"
              % (attention["finding_count"],
                 json.dumps(attention["severity_counts"],
                            sort_keys=True)))
        if args.attention_out:
            size = write_attention_json(args.attention_out, attention)
            print("attention json written: %s (%d bytes)"
                  % (args.attention_out, size))
        if args.json_out is not None:
            try:
                size = write_report_json(args.json_out, report)
            except (OSError, ValueError) as exc:
                sys.stderr.write("json-out failed: %s\n" % exc)
                return 2
            print("report json written: %s (%d bytes, schema %d)"
                  % (args.json_out, size, REPORT_SCHEMA))
        return 0
    finally:
        if am is not None:
            am.close()
        if dk is not None:
            dk.close()
        if mtr is not None:
            mtr.close()
        if led is not None:
            led.close()


if __name__ == "__main__":
    sys.exit(main())