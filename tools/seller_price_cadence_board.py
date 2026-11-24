#!/usr/bin/env python3
"""Render the monthly repricing cadence into one page.

Why this exists: api_seller_price_cadence_months answers "how often did this
shop reprice, how many moves went up and how many down, how large were the
steps in absolute percent, and was this month quieter than the last" with its
own AC-SPC criteria, but a search over tools/, preview/ and src/os answered
rc=1 with zero hits. The market already had two lifetime repricing faces
(api_price_volatility and api_price_step_distribution), both whole-history
scalars, so a seller that repriced twelve times in one month and then went
silent for a quarter read exactly like one that adjusted once a month for a
year.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_price_cadence_months() face read over a fresh throwaway demo world
whose repricing rows were made through the shipped publish_api and
revise_price doors under a fixed clock - no sqlite rewrite, no typed ids, no
padded rows. The page prints what the face hands it and never recomputes a
total; the only thing it draws is the width of one marker showing where a
month average sits between zero and that scope's largest month average, and
the page says out loud that the bar is a position, not a share. A broken
identity refuses the render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_price_cadence_board.py
  python tools/seller_price_cadence_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SPCB1..AC-SPCB6 were fixed in this round's window before the first render;
the src/os/backlog.md R3442 PIN row was filed at closeout and says so on its
face instead of pretending it landed first.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-price-cadence-board-copy.json and appear in the rendered
document only, never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-price-cadence-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-price-cadence-board.json")
COPY = os.path.join(ROOT, "preview", "seller-price-cadence-board-copy.json")

FACE = "api_seller_price_cadence_months"

# Pinned payload keys (AC-SPCB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "listing_count",
    "seller_count", "avg_abs_step_pct", "peak_month", "peak_revision_count",
    "first_month", "last_month", "latest_month_revision_count",
    "market_avg_abs_step_pct", "months", "sellers", "disclaimer", "report",
    "sources", "sizes",
)

# The shipped 9-key month row.
ROW_KEYS = (
    "month", "revision_count", "up_count", "down_count", "net_count",
    "listing_count", "seller_count", "avg_abs_step_pct",
    "running_revision",
)

# One seller scope keeps every envelope key the market envelope carries.
SCOPE_KEYS = (
    "dev_account", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "listing_count",
    "seller_count", "avg_abs_step_pct", "peak_month", "peak_revision_count",
    "first_month", "last_month", "latest_month_revision_count",
    "market_avg_abs_step_pct", "months",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_sellers", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_active", "kpi_revisions", "kpi_up", "kpi_down",
    "kpi_listings", "kpi_sellers", "kpi_avg", "kpi_peak", "kpi_latest",
    "kpi_bench",
    "scope_market", "scope_seller", "dash_scope",
    "col_month", "col_rev", "col_up", "col_down", "col_net", "col_lists",
    "col_sellers", "col_avg", "col_run", "col_bar",
    "empty", "none", "bar_caption",
    "law_count", "law_step", "law_window", "law_running", "law_pool",
    "law_peak", "law_scope", "law_distinct", "law_nosame", "law_bar",
    "law_notadvice",
    "rep", "cmd",
)

PAYLOAD = {"kind": "backtest", "calls": 100, "docs": "api/v1"}

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
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
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
.quiet{color:var(--muted);font-size:12.5px}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_SPCB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_SPCB_LAW"


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


def seed_world(am):
    """Make the repricing rows through the shipped doors under a fixed clock.

    The shipped demo world carries no price revision at all, so every step on
    the page is a landed row created by publish_api plus revise_price:

      2026-09  dana  cadence-alpha  10 -> 12   (+20.00)
               dana  cadence-beta    4 ->  5   (+25.00)
               frank cadence-gamma   8 ->  6   (-25.00)
      2026-10  (nothing - the honest zero row inside the window)
      2026-11  dana  cadence-alpha  12 ->  9   (-25.00)
               frank cadence-gamma   6 ->  9   (+50.00)
               frank cadence-delta   4 ->  5   (+25.00)
    """
    import apimarket as A

    clock = R.Clock()
    orig_now = A._now_utc
    A._now_utc = clock.now_utc
    try:
        clock.value = "2026-08-20T10:00:00Z"
        alpha = am.publish_api("usr:dana", "cadence-alpha", "Cadence Alpha",
                               "repricing demo payload alpha", PAYLOAD, 10,
                               False, category="data")["listing_id"]
        beta = am.publish_api("usr:dana", "cadence-beta", "Cadence Beta",
                              "repricing demo payload beta", PAYLOAD, 4,
                              True, category="data")["listing_id"]
        gamma = am.publish_api("usr:frank", "cadence-gamma", "Cadence Gamma",
                               "repricing demo payload gamma", PAYLOAD, 8,
                               False, category="tools")["listing_id"]
        delta = am.publish_api("usr:frank", "cadence-delta", "Cadence Delta",
                               "repricing demo payload delta", PAYLOAD, 4,
                               False, category="tools")["listing_id"]
        clock.value = "2026-09-05T09:00:00Z"
        am.revise_price("usr:dana", alpha, 12)
        clock.value = "2026-09-12T09:00:00Z"
        am.revise_price("usr:dana", beta, 5)
        clock.value = "2026-09-19T09:00:00Z"
        am.revise_price("usr:frank", gamma, 6)
        clock.value = "2026-11-03T09:00:00Z"
        am.revise_price("usr:dana", alpha, 9)
        clock.value = "2026-11-10T09:00:00Z"
        am.revise_price("usr:frank", gamma, 9)
        clock.value = "2026-11-17T09:00:00Z"
        am.revise_price("usr:frank", delta, 5)
    finally:
        A._now_utc = orig_now


def read_world():
    """The market envelope plus one scoped envelope per published seller."""
    tmp_root = tempfile.mkdtemp(prefix="spcb-")
    db = os.path.join(tmp_root, "spcb.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        seed_world(am)
        market = dict(getattr(am, FACE)())
        sellers = sorted({row["dev_account"]
                          for row in (am.api_public_listings() or {})
                          .get("listings") or []})
        scopes = [dict(getattr(am, FACE)(seller)) for seller in sellers]
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for scope in [market] + scopes:
        for row in scope.get("months") or []:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("month"), ",".join(missing)))
    return market, scopes


def _next_month(label):
    year, month = int(label[:4]), int(label[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return "%04d-%02d" % (year, month)


def check_laws(market, scopes):
    """AC-SPCB3 read at the source: refuse rather than print."""
    problems = []
    every = [("market", market)] + [
        (scope.get("dev_account"), scope) for scope in scopes]
    pooled = market.get("avg_abs_step_pct")
    for name, envelope in every:
        months = envelope.get("months") or []
        tag = "scope %s" % name
        if int(envelope.get("month_count", -1)) != len(months):
            problems.append("%s month_count %s != %d rows"
                            % (tag, envelope.get("month_count"), len(months)))
        if months:
            if envelope.get("first_month") != months[0]["month"]:
                problems.append("%s first_month does not match the first row"
                                % tag)
            if envelope.get("last_month") != months[-1]["month"]:
                problems.append("%s last_month does not match the last row"
                                % tag)
        previous = None
        revisions = 0
        up = 0
        down = 0
        lists_sum = 0
        lists_max = 0
        avgs = []
        for row in months:
            row_tag = "%s month %s" % (tag, row["month"])
            if previous is not None and _next_month(previous) != row["month"]:
                problems.append("%s is not the month after %s"
                                % (row_tag, previous))
            previous = row["month"]
            count = int(row["revision_count"])
            row_up = int(row["up_count"])
            row_down = int(row["down_count"])
            if row_up + row_down != count:
                problems.append("%s up+down %d != revision_count %d"
                                % (row_tag, row_up + row_down, count))
            if int(row["net_count"]) != row_up - row_down:
                problems.append("%s net_count %s != up-down"
                                % (row_tag, row["net_count"]))
            if count == 0:
                if row["avg_abs_step_pct"] is not None:
                    problems.append("%s zero month carries an average"
                                    % row_tag)
                if row["listing_count"] != 0 or row["seller_count"] != 0:
                    problems.append("%s zero month carries a distinct count"
                                    % row_tag)
            else:
                if row["avg_abs_step_pct"] is None:
                    problems.append("%s counts steps without an average"
                                    % row_tag)
                else:
                    avgs.append(float(row["avg_abs_step_pct"]))
            if count and int(row["listing_count"]) < 1:
                problems.append("%s steps without a listing" % row_tag)
            if count and int(row["seller_count"]) < 1:
                problems.append("%s steps without a seller" % row_tag)
            revisions += count
            up += row_up
            down += row_down
            lists_sum += int(row["listing_count"])
            lists_max = max(lists_max, int(row["listing_count"]))
        if months:
            running = [int(row["running_revision"]) for row in months]
            if running != sorted(running):
                problems.append("%s running_revision not monotone" % tag)
            if running[-1] != int(envelope.get("revision_count", -1)):
                problems.append("%s last running %d != revision_count %s"
                                % (tag, running[-1],
                                   envelope.get("revision_count")))
        if revisions != int(envelope.get("revision_count", -1)):
            problems.append("%s revision_count %s != %d summed"
                            % (tag, envelope.get("revision_count"),
                               revisions))
        if up != int(envelope.get("up_count", -1)):
            problems.append("%s up_count %s != %d summed"
                            % (tag, envelope.get("up_count"), up))
        if down != int(envelope.get("down_count", -1)):
            problems.append("%s down_count %s != %d summed"
                            % (tag, envelope.get("down_count"), down))
        if months:
            distinct = int(envelope.get("listing_count", -1))
            if not (lists_max <= distinct <= lists_sum):
                problems.append("%s listing_count %d outside [%d,%d]"
                                % (tag, distinct, lists_max, lists_sum))
            if int(envelope.get("active_month_count", -1)) != \
                    len([row for row in months
                         if int(row["revision_count"]) > 0]):
                problems.append("%s active_month_count %s"
                                % (tag, envelope.get("active_month_count")))
            if envelope.get("latest_month_revision_count") != \
                    months[-1]["revision_count"]:
                problems.append("%s latest_month_revision_count" % tag)
            best = max(int(row["revision_count"]) for row in months)
            if best > 0:
                first = [row["month"] for row in months
                         if int(row["revision_count"]) == best][0]
                if envelope.get("peak_month") != first:
                    problems.append("%s peak_month %r != earliest max %r"
                                    % (tag, envelope.get("peak_month"), first))
                if int(envelope.get("peak_revision_count", -1)) != best:
                    problems.append("%s peak_revision_count %s != %d"
                                    % (tag, envelope.get("peak_revision_count"),
                                       best))
            elif envelope.get("peak_month") is not None:
                problems.append("%s peak_month set on an all-zero scope" % tag)
                # Pooled mean is never a mean of monthly means: it must sit
                # inside the monthly range it pools.
            avg = envelope.get("avg_abs_step_pct")
            if avgs:
                if avg is None or not (min(avgs) - 0.005 <= float(avg)
                                       <= max(avgs) + 0.005):
                    problems.append("%s pooled average %r outside [%r,%r]"
                                    % (tag, avg, min(avgs), max(avgs)))
            elif avg is not None:
                problems.append("%s answers an average with zero steps" % tag)
        if envelope.get("scope") == "market":
            if envelope.get("market_avg_abs_step_pct") is not None:
                problems.append("%s market scope benchmarks itself" % tag)
        else:
            if envelope.get("market_avg_abs_step_pct") != pooled:
                problems.append("%s market benchmark %r != market %r"
                                % (tag, envelope.get("market_avg_abs_step_pct"),
                                   pooled))
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


def bar_html(row, top, none_text):
    avg = row["avg_abs_step_pct"]
    if avg is None or not top:
        return none_text
    pos = float(avg) / float(top) * 100.0
    pos = max(0.0, min(100.0, pos))
    return '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos


def scope_kpi(envelope, labels, e, dash):
    items = [
        (labels["kpi_months"], text(envelope.get("month_count"), dash)),
        (labels["kpi_active"], text(envelope.get("active_month_count"), dash)),
        (labels["kpi_revisions"], text(envelope.get("revision_count"), dash)),
        (labels["kpi_up"], text(envelope.get("up_count"), dash)),
        (labels["kpi_down"], text(envelope.get("down_count"), dash)),
        (labels["kpi_listings"], text(envelope.get("listing_count"), dash)),
        (labels["kpi_sellers"], text(envelope.get("seller_count"), dash)),
        (labels["kpi_avg"], text(envelope.get("avg_abs_step_pct"), dash)),
        (labels["kpi_peak"],
         "%s / %s" % (text(envelope.get("peak_month"), dash),
                      text(envelope.get("peak_revision_count"), dash))),
        (labels["kpi_latest"],
         text(envelope.get("latest_month_revision_count"), dash)),
        (labels["kpi_bench"],
         text(envelope.get("market_avg_abs_step_pct"), dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(str(value))) for name, value in items)


def month_table(envelope, labels, e, dash):
    months = envelope.get("months") or []
    top = max([float(row["avg_abs_step_pct"])
               for row in months
               if row["avg_abs_step_pct"] is not None] or [0.0])
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_rev"],
                                labels["col_up"], labels["col_down"],
                                labels["col_net"], labels["col_lists"],
                                labels["col_sellers"], labels["col_avg"],
                                labels["col_run"], labels["col_bar"]))
    body = []
    for row in months:
        quiet = int(row["revision_count"]) == 0
        cells = (
            (text(row["revision_count"], dash), ""),
            (text(row["up_count"], dash), ""),
            (text(row["down_count"], dash), ""),
            (text(row["net_count"], dash), ""),
            (text(row["listing_count"], dash), ""),
            (text(row["seller_count"], dash), ""),
            (text(row["avg_abs_step_pct"], dash), ""),
            (text(row["running_revision"], dash), ""),
        )
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td></tr>'
            % (e(str(row["month"])),
               ' class="quiet-row"' if quiet else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(value)
                       for value, _ in cells),
               bar_html(row, top, e(dash))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading):
    months = envelope.get("months") or []
    body = (month_table(envelope, labels, e, dash) if months
            else "<p class=empty>%s</p>" % e(labels["empty"]))
    return (
        '<div class=card data-scope="%s">\n'
        "<h3>%s</h3>\n<div class=kpi>%s</div>\n"
        '<p class=cap>%s</p>\n%s\n</div>\n'
        % (e(str(envelope.get("dev_account") or "market")), e(heading),
           scope_kpi(envelope, labels, e, dash), e(labels["bar_caption"]),
           body)
    )


def build_html(market, scopes, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_step"], labels["law_window"],
            labels["law_running"], labels["law_pool"], labels["law_peak"],
            labels["law_scope"], labels["law_distinct"], labels["law_nosame"],
            labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    seller_cards = "".join(
        scope_card(scope, labels, e, dash, labels["scope_seller"])
        for scope in scopes)
    if not seller_cards:
        seller_cards = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE),
           e(labels["sec_market"]),
           scope_card(market, labels, e, dash, labels["scope_market"]),
           e(labels["sec_sellers"]), seller_cards,
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


def payload_of(market, scopes, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "month_count": market["month_count"],
        "active_month_count": market["active_month_count"],
        "revision_count": market["revision_count"],
        "up_count": market["up_count"],
        "down_count": market["down_count"],
        "listing_count": market["listing_count"],
        "seller_count": market["seller_count"],
        "avg_abs_step_pct": market["avg_abs_step_pct"],
        "peak_month": market["peak_month"],
        "peak_revision_count": market["peak_revision_count"],
        "first_month": market["first_month"],
        "last_month": market["last_month"],
        "latest_month_revision_count":
            market["latest_month_revision_count"],
        "market_avg_abs_step_pct": market["market_avg_abs_step_pct"],
        "months": [{key: row[key] for key in ROW_KEYS}
                   for row in market.get("months") or []],
        "sellers": [{key: scope[key] for key in SCOPE_KEYS
                     if key != "months"} | {
                        "months": [{key: row[key] for key in ROW_KEYS}
                                   for row in scope.get("months") or []]}
                    for scope in scopes],
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
        print("REPRICING-CADENCE CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, scopes = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, scopes)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = market.get("disclaimer")
    doc = build_html(market, scopes, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(market, scopes, args.out, disclaimer, now)
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

    print("REPRICING-CADENCE %s bytes=%d months=%d revisions=%d sellers=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["month_count"], payload["revision_count"],
             len(payload["sellers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
