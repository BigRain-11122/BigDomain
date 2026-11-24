#!/usr/bin/env python3
"""Render what one purchase is actually worth into one page.

Why this exists: api_market_ticket_size answers "how big is one order, what
does the band look like, and what changes when refunded tickets are counted
or left out" with its own AC-MTM criteria, and api_market_ticket_size_months
answers the same question on a calendar month. A search over tools/, preview/
and src/os answered rc=1 for both, so the market already had lifetime sale
counts (api_market_stats), monthly revenue (api_revenue_months) and price
bands (api_category_price_months) but no page that answered how large a single
ticket is, whether this month's tickets are richer than last month's, whether
refunds are inside the average, and how wide one seller's own band sits.

Nothing here re-implements a market rule. Every number comes from the shipped
faces read over a fresh throwaway demo world; the page prints what the faces
hand it and never recomputes a total. The only thing it draws is the width of
one marker showing where a month's p90 sits between that scope's own floor and
ceiling, and the page says out loud that the bar is a position, not a share. A
broken identity refuses the render instead of printing a plausible page.

Both refund conventions are shown side by side on purpose: the default face
leaves refunded sales out of the average, and reading only one of the two
numbers is how a "ticket size" turns into a half-truth.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/ticket_size_board.py
  python tools/ticket_size_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-TSZB1..AC-TSZB6 were fixed in this round's window before the first render,
and the src/os/backlog.md R3443 PIN row landed before any driver code.

ASCII source, stdlib only, no network. Chinese labels live in
preview/ticket-size-board-copy.json and appear in the rendered document only,
never in this file.
"""
import argparse
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

OUT_HTML = os.path.join(ROOT, "preview", "ticket-size-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "ticket-size-board.json")
COPY = os.path.join(ROOT, "preview", "ticket-size-board-copy.json")

FACE = "api_market_ticket_size"
FACE_MONTHS = "api_market_ticket_size_months"

# Pinned payload keys (AC-TSZB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "faces", "scope", "market_lifetime",
    "market_lifetime_refunded", "sellers", "months", "disclaimer", "report",
    "sources", "sizes",
)

# The shipped 19-key lifetime envelope.
LIFE_KEYS = (
    "scope", "dev_account", "include_refunded", "sale_count",
    "refunded_sale_count", "gross_tokens", "refunded_tokens",
    "net_gross_tokens", "mean_ticket", "p25_ticket", "p50_ticket",
    "p75_ticket", "p90_ticket", "min_ticket", "max_ticket", "spread",
    "category_count", "categories", "disclaimer",
)

# The shipped 10-key category row.
CAT_KEYS = (
    "category", "sale_count", "refunded_sale_count", "gross_tokens",
    "net_gross_tokens", "refunded_tokens", "mean_ticket", "p50_ticket",
    "min_ticket", "max_ticket",
)

# The shipped 17-key monthly envelope.
MONTH_ENV_KEYS = (
    "scope", "sale_count", "refunded_sale_count", "gross_tokens",
    "mean_ticket", "median_ticket", "p90_ticket", "min_ticket", "max_ticket",
    "month_count", "first_month", "last_month", "peak_month",
    "peak_median_ticket", "latest_month_median_ticket", "disclaimer", "months",
)

# The shipped 8-key month row.
MONTH_ROW_KEYS = (
    "month", "sale_count", "refunded_sale_count", "gross_tokens",
    "mean_ticket", "median_ticket", "p90_ticket", "running_ticket_tokens",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_life", "sec_sellers", "sec_months", "sec_law", "sec_disc", "sec_rep",
    "scope_default", "scope_refunded", "scope_seller", "dash_scope",
    "kpi_sales", "kpi_refunded", "kpi_gross", "kpi_net", "kpi_refund_tokens",
    "kpi_mean", "kpi_p25", "kpi_p50", "kpi_p75", "kpi_p90",
    "kpi_min", "kpi_max", "kpi_spread", "kpi_categories",
    "col_category", "col_sales", "col_refunded", "col_gross", "col_net",
    "col_refund_tokens", "col_mean", "col_p50", "col_min", "col_max",
    "col_month", "col_run", "col_p90", "col_bar",
    "uncategorized", "empty", "none", "bar_caption",
    "law_sum", "law_net", "law_mean", "law_band", "law_two_sides",
    "law_sellers", "law_months", "law_running", "law_grid", "law_peak",
    "law_row_band", "law_bar", "law_notadvice",
    "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:16px 0 8px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 104px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:18px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.bar{position:relative;height:10px;min-width:120px;max-width:240px;
border:1px solid var(--line);border-radius:999px;background:#f2f4f7}
.bar i{position:absolute;top:-3px;width:3px;height:16px;background:#3c4653}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.quiet-row td{color:var(--muted)}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_TSZB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_TSZB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS
               if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_world():
    """Both refund conventions, per seller, plus the monthly envelope."""
    tmp_root = tempfile.mkdtemp(prefix="tszb-")
    db = os.path.join(tmp_root, "tszb.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        plain = dict(am.api_market_ticket_size())
        refunded = dict(am.api_market_ticket_size(include_refunded=True))
        months = dict(am.api_market_ticket_size_months())
        sellers = sorted({row["dev_account"]
                          for row in (am.api_public_listings() or {})
                          .get("listings") or []})
        scoped = []
        for seller in sellers:
            scoped.append({
                "seller": seller,
                "lifetime": dict(am.api_market_ticket_size(
                    seller, include_refunded=True)),
                "lifetime_plain": dict(am.api_market_ticket_size(seller)),
            })
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for name, envelope in (("market", plain), ("market_refunded", refunded)):
        missing = [key for key in LIFE_KEYS if key not in envelope]
        if missing:
            raise FaceError("lifetime keys missing on %s: %s"
                            % (name, ",".join(missing)))
    missing = [key for key in MONTH_ENV_KEYS if key not in months]
    if missing:
        raise FaceError("monthly envelope keys missing: %s"
                        % ",".join(missing))
    return plain, refunded, scoped, months


def _next_month(label):
    year, month = int(label[:4]), int(label[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return "%04d-%02d" % (year, month)


def _band_problems(tag, envelope, problems):
    sales = int(envelope.get("sale_count", -1))
    refunded = int(envelope.get("refunded_sale_count", -1))
    gross = int(envelope.get("gross_tokens", -1))
    refund_tokens = int(envelope.get("refunded_tokens", -1))
    net = int(envelope.get("net_gross_tokens", -1))
    if net != gross - refund_tokens:
        problems.append("%s net_gross %d != gross %d - refunded %d"
                        % (tag, net, gross, refund_tokens))
    if refunded > sales:
        problems.append("%s refunded_sale_count %d > sale_count %d"
                        % (tag, refunded, sales))
    cats = envelope.get("categories") or []
    if int(envelope.get("category_count", -1)) != len(cats):
        problems.append("%s category_count %s != %d rows"
                        % (tag, envelope.get("category_count"), len(cats)))
    for key in ("sale_count", "refunded_sale_count", "gross_tokens"):
        summed = sum(int(row[key]) for row in cats)
        if summed != int(envelope.get(key, -1)):
            problems.append("%s %s %s != %d summed over categories"
                            % (tag, key, envelope.get(key), summed))
    if sales > 0:
        mean = envelope.get("mean_ticket")
        if mean is None or abs(float(mean) - gross / float(sales)) > 1e-9:
            problems.append("%s mean_ticket %r != gross/sales %r"
                            % (tag, mean, gross / float(sales)))
        points = [envelope.get(k) for k in ("min_ticket", "p25_ticket",
                                            "p50_ticket", "p75_ticket",
                                            "p90_ticket", "max_ticket")]
        if any(point is None for point in points):
            problems.append("%s a five-number band is missing on a sold scope"
                            % tag)
        else:
            nums = [float(point) for point in points]
            if nums != sorted(nums):
                problems.append("%s band is not monotone: %r" % (tag, nums))
            if not (nums[0] <= float(mean) <= nums[-1]):
                problems.append("%s mean %r outside [%r,%r]"
                                % (tag, mean, nums[0], nums[-1]))
            if envelope.get("spread") != nums[-1] - nums[0]:
                problems.append("%s spread %r != max-min %r"
                                % (tag, envelope.get("spread"),
                                   nums[-1] - nums[0]))
    else:
        for key in ("mean_ticket", "p25_ticket", "p50_ticket", "p75_ticket",
                    "p90_ticket", "min_ticket", "max_ticket", "spread"):
            if envelope.get(key) is not None:
                problems.append("%s answers %s on a zero-sale scope"
                                % (tag, key))
        if cats:
            problems.append("%s carries categories with zero sales" % tag)
    for row in cats:
        missing = [key for key in CAT_KEYS if key not in row]
        if missing:
            problems.append("%s category row keys missing: %s"
                            % (tag, ",".join(missing)))
    return problems


def check_laws(plain, refunded, scoped, months):
    """AC-TSZB3 read at the source: refuse rather than print."""
    problems = []
    _band_problems("market", plain, problems)
    _band_problems("market_refunded", refunded, problems)
    if plain.get("include_refunded") is not False:
        problems.append("market default envelope says include_refunded=%r"
                        % plain.get("include_refunded"))
    if refunded.get("include_refunded") is not True:
        problems.append("market refunded envelope says include_refunded=%r"
                        % refunded.get("include_refunded"))
    if int(plain.get("gross_tokens", -1)) != int(
            refunded.get("net_gross_tokens", -2)):
        problems.append("plain gross %s != refunded net %s"
                        % (plain.get("gross_tokens"),
                           refunded.get("net_gross_tokens")))
    seller_sales = 0
    seller_gross = 0
    for item in scoped:
        tag = "seller %s" % item["seller"]
        problems = _band_problems(tag, item["lifetime"], problems)
        if item["lifetime"].get("scope") != "seller":
            problems.append("%s scope %r" % (tag, item["lifetime"].get("scope")))
        seller_sales += int(item["lifetime"].get("sale_count", 0))
        seller_gross += int(item["lifetime"].get("gross_tokens", 0))
    if seller_sales != int(refunded.get("sale_count", -1)):
        problems.append("seller sales %d != market refunded sales %s"
                        % (seller_sales, refunded.get("sale_count")))
    if seller_gross != int(refunded.get("gross_tokens", -1)):
        problems.append("seller gross %d != market refunded gross %s"
                        % (seller_gross, refunded.get("gross_tokens")))
    rows = months.get("months") or []
    if int(months.get("month_count", -1)) != len(rows):
        problems.append("month_count %s != %d rows"
                        % (months.get("month_count"), len(rows)))
    if rows:
        if months.get("first_month") != rows[0]["month"]:
            problems.append("first_month does not match the first row")
        if months.get("last_month") != rows[-1]["month"]:
            problems.append("last_month does not match the last row")
    previous = None
    running = []
    totals = {"sale_count": 0, "refunded_sale_count": 0, "gross_tokens": 0}
    for row in rows:
        missing = [key for key in MONTH_ROW_KEYS if key not in row]
        if missing:
            problems.append("month %r keys missing: %s"
                            % (row.get("month"), ",".join(missing)))
            continue
        tag = "month %s" % row["month"]
        if previous is not None and _next_month(previous) != row["month"]:
            problems.append("%s is not the month after %s"
                            % (tag, previous))
        previous = row["month"]
        for key in totals:
            totals[key] += int(row[key])
        sales = int(row["sale_count"])
        if int(row["refunded_sale_count"]) > sales:
            problems.append("%s refunded %s > sales %d"
                            % (tag, row["refunded_sale_count"], sales))
        if sales > 0:
            low = months.get("min_ticket")
            high = months.get("max_ticket")
            for key in ("mean_ticket", "median_ticket", "p90_ticket"):
                if (row[key] is None or low is None or high is None
                        or not (float(low) <= float(row[key])
                                <= float(high))):
                    problems.append("%s %s %r outside envelope [%r,%r]"
                                    % (tag, key, row[key], low, high))
            if (row["median_ticket"] is not None
                    and row["p90_ticket"] is not None
                    and float(row["median_ticket"]) > float(row["p90_ticket"])):
                problems.append("%s median %r above p90 %r"
                                % (tag, row["median_ticket"],
                                   row["p90_ticket"]))
        running.append(int(row["running_ticket_tokens"]))
    if running:
        if running != sorted(running):
            problems.append("running_ticket_tokens is not monotone")
        if running[-1] != int(months.get("gross_tokens", -1)):
            problems.append("last running %d != monthly gross %s"
                            % (running[-1], months.get("gross_tokens")))
    if totals["sale_count"] != int(months.get("sale_count", -1)):
        problems.append("monthly sales %d != envelope %s"
                        % (totals["sale_count"], months.get("sale_count")))
    if totals["gross_tokens"] != int(months.get("gross_tokens", -1)):
        problems.append("monthly gross %d != envelope %s"
                        % (totals["gross_tokens"], months.get("gross_tokens")))
    if totals["refunded_sale_count"] != int(
            months.get("refunded_sale_count", -1)):
        problems.append("monthly refunded %d != envelope %s"
                        % (totals["refunded_sale_count"],
                           months.get("refunded_sale_count")))
    for key in totals:
        if totals[key] != int(refunded.get(key, -2)):
            problems.append("monthly %s %d != lifetime refunded %s"
                            % (key, totals[key], refunded.get(key)))
    if rows:
        medians = [(row["month"], row["median_ticket"]) for row in rows
                   if row["median_ticket"] is not None]
        if medians:
            best = max(float(value) for _, value in medians)
            first = [month for month, value in medians
                     if float(value) == best][0]
            if months.get("peak_month") != first:
                problems.append("peak_month %r != earliest max %r"
                                % (months.get("peak_month"), first))
            if float(months.get("peak_median_ticket") or -1) != best:
                problems.append("peak_median_ticket %r != %r"
                                % (months.get("peak_median_ticket"), best))
        if months.get("latest_month_median_ticket") != rows[-1]["median_ticket"]:
            problems.append("latest_month_median_ticket %r != last row %r"
                            % (months.get("latest_month_median_ticket"),
                               rows[-1]["median_ticket"]))
    return problems


def text(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.2f" % value).rstrip("0").rstrip(".")
    return str(value)


def cat_rows_html(envelope, labels, e, dash):
    rows = envelope.get("categories") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_category"] else "",
                      e(name))
                   for name in (labels["col_category"], labels["col_sales"],
                                labels["col_refunded"], labels["col_gross"],
                                labels["col_net"], labels["col_refund_tokens"],
                                labels["col_mean"], labels["col_p50"],
                                labels["col_min"], labels["col_max"]))
    body = []
    for row in rows:
        name = row["category"] if row["category"] else labels["uncategorized"]
        badge = "" if row["category"] else ' <span class=badge>%s</span>' % e(
            labels["uncategorized"])
        body.append(
            '<tr data-category="%s"><td>%s%s</td>%s</tr>'
            % (e(str(row["category"] or "")), e(str(name)), badge,
               "".join('<td class="n">%s</td>'
                       % e(text(row[key], dash))
                       for key in ("sale_count", "refunded_sale_count",
                                   "gross_tokens", "net_gross_tokens",
                                   "refunded_tokens", "mean_ticket",
                                   "p50_ticket", "min_ticket", "max_ticket"))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def life_kpi(envelope, labels, e, dash):
    items = [
        (labels["kpi_sales"], envelope.get("sale_count")),
        (labels["kpi_refunded"], envelope.get("refunded_sale_count")),
        (labels["kpi_gross"], envelope.get("gross_tokens")),
        (labels["kpi_refund_tokens"], envelope.get("refunded_tokens")),
        (labels["kpi_net"], envelope.get("net_gross_tokens")),
        (labels["kpi_mean"], envelope.get("mean_ticket")),
        (labels["kpi_p25"], envelope.get("p25_ticket")),
        (labels["kpi_p50"], envelope.get("p50_ticket")),
        (labels["kpi_p75"], envelope.get("p75_ticket")),
        (labels["kpi_p90"], envelope.get("p90_ticket")),
        (labels["kpi_min"], envelope.get("min_ticket")),
        (labels["kpi_max"], envelope.get("max_ticket")),
        (labels["kpi_spread"], envelope.get("spread")),
        (labels["kpi_categories"], envelope.get("category_count")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def life_card(envelope, labels, e, dash, heading, scope_tag):
    return (
        '<div class=card data-scope="%s">\n<h3>%s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n</div>\n"
        % (e(scope_tag), e(heading), life_kpi(envelope, labels, e, dash),
           cat_rows_html(envelope, labels, e, dash))
    )


def month_table(months, labels, e, dash):
    rows = months.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    low = months.get("min_ticket")
    high = months.get("max_ticket")
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_sales"],
                                labels["col_refunded"], labels["col_gross"],
                                labels["col_mean"], labels["col_p50"],
                                labels["col_p90"], labels["col_run"],
                                labels["col_bar"]))
    body = []
    for row in rows:
        quiet = int(row["sale_count"]) == 0
        p90 = row["p90_ticket"]
        if p90 is None or low is None or high is None or high <= low:
            bar = e(dash)
        else:
            pos = (float(p90) - low) / (high - low) * 100.0
            pos = max(0.0, min(100.0, pos))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td></tr>'
            % (e(str(row["month"])),
               ' class="quiet-row"' if quiet else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("sale_count", "refunded_sale_count",
                                   "gross_tokens", "mean_ticket",
                                   "median_ticket", "p90_ticket",
                                   "running_ticket_tokens")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def build_html(plain, refunded, scoped, months, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_sum"], labels["law_net"], labels["law_mean"],
            labels["law_band"], labels["law_two_sides"], labels["law_sellers"],
            labels["law_months"], labels["law_running"], labels["law_grid"],
            labels["law_peak"], labels["law_row_band"], labels["law_bar"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    seller_cards = "".join(
        life_card(item["lifetime"], labels, e, dash, labels["scope_seller"],
                  item["seller"])
        for item in scoped)
    if not seller_cards:
        seller_cards = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; '
        "<code>%s</code> + <code>%s</code></div>\n"
        "<h2>%s</h2>\n%s\n%s\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE, FACE_MONTHS,
           e(labels["sec_life"]),
           life_card(plain, labels, e, dash, labels["scope_default"], "plain"),
           life_card(refunded, labels, e, dash, labels["scope_refunded"],
                     "refunded"),
           e(labels["sec_sellers"]), seller_cards,
           e(labels["sec_months"]),
           month_table(months, labels, e, dash), e(labels["bar_caption"]),
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["rep"]), e(now), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(str(disclaimer or "")))


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


def trim_life(envelope):
    doc = {key: envelope[key] for key in LIFE_KEYS if key != "categories"}
    doc["categories"] = [{key: row[key] for key in CAT_KEYS}
                         for row in envelope.get("categories") or []]
    return doc


def payload_of(plain, refunded, scoped, months, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "faces": [FACE, FACE_MONTHS],
        "scope": "market",
        "market_lifetime": trim_life(plain),
        "market_lifetime_refunded": trim_life(refunded),
        "sellers": [{"seller": item["seller"],
                     "lifetime": trim_life(item["lifetime"]),
                     "lifetime_plain": trim_life(item["lifetime_plain"])}
                    for item in scoped],
        "months": {
            "month_count": months["month_count"],
            "first_month": months["first_month"],
            "last_month": months["last_month"],
            "sale_count": months["sale_count"],
            "refunded_sale_count": months["refunded_sale_count"],
            "gross_tokens": months["gross_tokens"],
            "mean_ticket": months["mean_ticket"],
            "median_ticket": months["median_ticket"],
            "p90_ticket": months["p90_ticket"],
            "min_ticket": months["min_ticket"],
            "max_ticket": months["max_ticket"],
            "peak_month": months["peak_month"],
            "peak_median_ticket": months["peak_median_ticket"],
            "latest_month_median_ticket":
                months["latest_month_median_ticket"],
            "rows": [{key: row[key] for key in MONTH_ROW_KEYS}
                     for row in months.get("months") or []],
        },
        "disclaimer": disclaimer,
        "report": os.path.relpath(path, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }


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
        print("TICKET-SIZE CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        plain, refunded, scoped, months = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(plain, refunded, scoped, months)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = plain.get("disclaimer")
    doc = build_html(plain, refunded, scoped, months, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(plain, refunded, scoped, months, args.out,
                         disclaimer, now)
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

    print("TICKET-SIZE %s bytes=%d months=%d sales=%d gross=%d sellers=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             months["month_count"], refunded["sale_count"],
             refunded["gross_tokens"], len(payload["sellers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
