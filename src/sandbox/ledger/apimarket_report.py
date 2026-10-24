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

Faces consumed (read-only): api_market_stats, api_market_months,
api_revenue_months, api_buyer_profile, api_buyer_months, api_board,
api_sales.

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
    for buyer in sorted(buyers):
        report["buyers"][buyer] = {
            "profile": am.api_buyer_profile(buyer),
            "months": am.api_buyer_months(buyer),
        }
    return report


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
table{width:100%;border-collapse:collapse;background:#fff;font-size:13px;margin-bottom:14px}
th,td{border:1px solid var(--line);padding:6px 8px;text-align:right}
th{background:#eef1f8;font-weight:600;text-align:center}
table.kv th{width:38%;text-align:left}
table.kv td{text-align:left}
.empty{color:var(--muted);font-size:13px;padding:6px 2px}
footer{margin-top:36px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
"""


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

    parts.append("<h2>Listings</h2>")
    parts.append(row_table(report["board"].get("listings"),
                           "no live listings"))

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

    parts.append("<footer>%s</footer>" % esc(report["market"].get(
        "disclaimer") or DISCLAIMER))
    parts.append("</div></body></html>")
    return "\n".join(parts) + "\n"


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
    return parser


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