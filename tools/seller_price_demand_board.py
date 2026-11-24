#!/usr/bin/env python3
"""Render whether a seller actually moved the price when interest rose.

Why this exists: api_seller_price_demand_months answers, on the month axis,
"when attention arrived, did anyone reprice" - it joins the revision leg, the
watch leg, the unwatch leg and the question leg, each booked in the UTC month
of its own immutable stamp. The market already had three separate timelines
(api_seller_price_cadence_months for repricing, api_seller_watch_months for
attention, api_seller_question_months for pre-sale questions) and no page that
put them side by side, so a search over tools/, preview/ and src/os answered
rc=1 for the face and the seller's own operating question could only be read
by calling the sandbox from a shell.

Nothing here re-implements a market rule. Every number comes from the shipped
face read over a throwaway demo world whose rows are created through the
shipped doors (publish, reprice, watch, unwatch, ask) under a pinned clock -
the shipped factory world carries no revision, no watch and no question at
all, so an empty shape would have proved nothing. The page prints what the
face hands it and never recomputes a total; a broken identity refuses the
render instead of printing a plausible page.

The response law is printed as the face states it: a response month needs a
revision AND demand, a demand month needs a positive watch delta or a
question, and the rate is the dash rather than a fabricated zero when no
demand exists.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_price_demand_board.py
  python tools/seller_price_demand_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SPDB1..AC-SPDB6 were fixed in this round's window before the first render,
and the src/os/backlog.md R3444 PIN row landed before any driver code.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-price-demand-board-copy.json and appear in the rendered
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

import apimarket as A  # noqa: E402
import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "seller-price-demand-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-price-demand-board.json")
COPY = os.path.join(ROOT, "preview", "seller-price-demand-board-copy.json")

FACE = "api_seller_price_demand_months"

# Pinned payload keys (AC-SPDB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "sellers", "disclaimer",
    "report", "sources", "sizes",
)

# The shipped 22-key envelope.
ENVELOPE_KEYS = (
    "dev_account", "scope", "month_count", "active_month_count",
    "revision_count", "up_count", "down_count", "watch_count",
    "unwatch_count", "watch_net_count", "question_count",
    "response_month_count", "demand_month_count", "response_rate",
    "peak_revision_month", "peak_revision_count", "market_response_rate",
    "latest_month_revision_count", "first_month", "last_month", "months",
    "disclaimer",
)

# The shipped 10-key month row.
ROW_KEYS = (
    "month", "revision_count", "up_count", "down_count", "net_count",
    "watch_count", "unwatch_count", "watch_net_count", "question_count",
    "running_revision",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_sellers", "sec_law", "sec_disc", "sec_rep",
    "scope_market", "scope_seller", "dash_scope",
    "kpi_months", "kpi_active", "kpi_revisions", "kpi_up", "kpi_down",
    "kpi_watches", "kpi_unwatches", "kpi_net_watch", "kpi_questions",
    "kpi_response", "kpi_demand", "kpi_rate", "kpi_peak", "kpi_bench",
    "col_month", "col_rev", "col_up", "col_down", "col_net",
    "col_watch", "col_unwatch", "col_watch_net", "col_question",
    "col_run", "col_state", "col_bar",
    "badge_demand", "badge_response", "badge_quiet", "empty", "none",
    "bar_caption", "peak_label",
    "law_sum", "law_split", "law_watch_net", "law_running", "law_grid",
    "law_demand", "law_rate", "law_peak", "law_bench", "law_partition",
    "law_bar", "law_empty", "law_notadvice",
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
.badge.on{border-color:#9ad1a7;background:#eef9f1;color:#1f6b33}
.badge.off{border-color:#e4b9b9;background:#fdf1f1;color:#8a2323}
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

# One pinned clock drives every write so the month buckets reproduce.
STAMP = {"value": "2026-09-05T00:00:00Z"}


class FaceError(Exception):
    code = "E_SPDB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_SPDB_LAW"


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


def _clock():
    return STAMP["value"]


def build_world(am):
    """Three months of the same story, every row through a shipped door.

    2026-09: dana reprices her own shelf up and bob watches it and asks a
    question, so September is a demand month AND a response month.
    2026-10: carol watches frank's shelf and nobody reprices, so October is
    a demand month with no response.
    2026-11: bob unwatches dana's shelf and frank reprices his down, so
    November carries a revision but no demand - the unwatch drain is
    honestly not demand.
    """
    board = am.api_public_listings() or {}
    by_key = {}
    for row in board.get("listings") or []:
        by_key[str(row["listing_key"])] = row
    if "risk-scan" not in by_key or "chart-render" not in by_key:
        raise FaceError("shipped board lost risk-scan or chart-render")
    dana_shelf = int(by_key["risk-scan"]["listing_id"])
    frank_shelf = int(by_key["chart-render"]["listing_id"])
    dana = str(by_key["risk-scan"]["dev_account"])
    frank = str(by_key["chart-render"]["dev_account"])

    STAMP["value"] = "2026-09-05T00:00:00Z"
    am.revise_price(dana, dana_shelf, int(by_key["risk-scan"]["token_price"]) + 2)
    STAMP["value"] = "2026-09-06T00:00:00Z"
    am.watch_api("usr:bob", dana_shelf)
    STAMP["value"] = "2026-09-07T00:00:00Z"
    am.ask_question("usr:bob", dana_shelf, "does it cover tools")
    STAMP["value"] = "2026-10-04T00:00:00Z"
    am.watch_api("usr:carol", frank_shelf)
    STAMP["value"] = "2026-11-03T00:00:00Z"
    am.unwatch_api("usr:bob", dana_shelf)
    STAMP["value"] = "2026-11-09T00:00:00Z"
    am.revise_price(frank, frank_shelf,
                    max(1, int(by_key["chart-render"]["token_price"]) - 1))
    return sorted({dana, frank})


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="spdb-")
    db = os.path.join(tmp_root, "spdb.db")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        sellers = build_world(am)
        market = dict(am.api_seller_price_demand_months())
        scoped = [{"seller": name,
                   "envelope": dict(am.api_seller_price_demand_months(name))}
                  for name in sellers]
        empty_scope = dict(am.api_seller_price_demand_months("usr:ghost"))
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        A._now_utc = orig_now
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    missing = [key for key in ENVELOPE_KEYS if key not in market]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    return market, scoped, empty_scope


def _next_month(label):
    year, month = int(label[:4]), int(label[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return "%04d-%02d" % (year, month)


def _envelope_problems(tag, envelope, problems, market_rate):
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("%s month_count %s != %d rows"
                        % (tag, envelope.get("month_count"), len(rows)))
    if rows:
        if envelope.get("first_month") != rows[0]["month"]:
            problems.append("%s first_month does not match the first row" % tag)
        if envelope.get("last_month") != rows[-1]["month"]:
            problems.append("%s last_month does not match the last row" % tag)
    previous = None
    running = []
    sums = {"revision_count": 0, "up_count": 0, "down_count": 0,
            "watch_count": 0, "unwatch_count": 0, "watch_net_count": 0,
            "question_count": 0}
    demand = 0
    response = 0
    for row in rows:
        missing = [key for key in ROW_KEYS if key not in row]
        if missing:
            problems.append("%s month %r keys missing: %s"
                            % (tag, row.get("month"), ",".join(missing)))
            continue
        label = "%s month %s" % (tag, row["month"])
        if previous is not None and _next_month(previous) != row["month"]:
            problems.append("%s is not the month after %s" % (label, previous))
        previous = row["month"]
        for key in sums:
            sums[key] += int(row[key])
        if int(row["up_count"]) + int(row["down_count"]) != int(
                row["revision_count"]):
            problems.append("%s up+down %d != revisions %s"
                            % (label, int(row["up_count"])
                               + int(row["down_count"]),
                               row["revision_count"]))
        if int(row["net_count"]) != int(row["up_count"]) - int(
                row["down_count"]):
            problems.append("%s net_count %s != up-down %d"
                            % (label, row["net_count"],
                               int(row["up_count"]) - int(row["down_count"])))
        if int(row["watch_net_count"]) != int(row["watch_count"]) - int(
                row["unwatch_count"]):
            problems.append("%s watch_net %s != watch-unwatch %d"
                            % (label, row["watch_net_count"],
                               int(row["watch_count"])
                               - int(row["unwatch_count"])))
        has_demand = int(row["watch_net_count"]) > 0 or int(
            row["question_count"]) > 0
        if has_demand:
            demand += 1
            if int(row["revision_count"]) > 0:
                response += 1
        running.append(int(row["running_revision"]))
    for key in sums:
        if sums[key] != int(envelope.get(key, -2)):
            problems.append("%s %s %s != %d summed over months"
                            % (tag, key, envelope.get(key), sums[key]))
    if running:
        if running != sorted(running):
            problems.append("%s running_revision is not monotone" % tag)
        if running[-1] != int(envelope.get("revision_count", -1)):
            problems.append("%s last running %d != revisions %s"
                            % (tag, running[-1], envelope.get("revision_count")))
    if demand != int(envelope.get("demand_month_count", -1)):
        problems.append("%s demand months %d != envelope %s"
                        % (tag, demand, envelope.get("demand_month_count")))
    if response != int(envelope.get("response_month_count", -1)):
        problems.append("%s response months %d != envelope %s"
                        % (tag, response, envelope.get("response_month_count")))
    if response > demand:
        problems.append("%s response months %d above demand months %d"
                        % (tag, response, demand))
    rate = envelope.get("response_rate")
    if demand == 0:
        if rate is not None:
            problems.append("%s answers a rate with zero demand months" % tag)
    else:
        want = round(response / float(demand), 4)
        if rate is None or abs(float(rate) - want) > 1e-12:
            problems.append("%s rate %r != response/demand %r"
                            % (tag, rate, want))
    active = sum(1 for row in rows if int(row["revision_count"]) > 0)
    if active != int(envelope.get("active_month_count", -1)):
        problems.append("%s active months %d != envelope %s"
                        % (tag, active, envelope.get("active_month_count")))
    if rows:
        if envelope.get("latest_month_revision_count") != rows[-1][
                "revision_count"]:
            problems.append("%s latest_month_revision_count %r != last row %r"
                            % (tag, envelope.get("latest_month_revision_count"),
                               rows[-1]["revision_count"]))
        peaks = [(row["month"], int(row["revision_count"])) for row in rows
                 if int(row["revision_count"]) > 0]
        if peaks:
            best = max(count for _, count in peaks)
            first = [month for month, count in peaks if count == best][0]
            if envelope.get("peak_revision_month") != first:
                problems.append("%s peak month %r != earliest max %r"
                                % (tag, envelope.get("peak_revision_month"),
                                   first))
            if int(envelope.get("peak_revision_count") or -1) != best:
                problems.append("%s peak count %r != %d"
                                % (tag, envelope.get("peak_revision_count"),
                                   best))
        elif envelope.get("peak_revision_month") is not None:
            problems.append("%s names a peak month on a flat grid" % tag)
    if envelope.get("scope") == "market":
        if envelope.get("market_response_rate") is not None:
            problems.append("%s market scope benchmarks itself with %r"
                            % (tag, envelope.get("market_response_rate")))
    else:
        if envelope.get("market_response_rate") != market_rate:
            problems.append("%s seller benchmark %r != market rate %r"
                            % (tag, envelope.get("market_response_rate"),
                               market_rate))
    return problems


def check_laws(market, scoped, empty_scope):
    """AC-SPDB3 read at the source: refuse rather than print."""
    problems = []
    if market.get("scope") != "market":
        problems.append("market envelope scope %r" % market.get("scope"))
    rate = market.get("response_rate")
    problems = _envelope_problems("market", market, problems, rate)
    totals = {"revision_count": 0, "up_count": 0, "down_count": 0,
              "watch_count": 0, "unwatch_count": 0, "watch_net_count": 0,
              "question_count": 0}
    for item in scoped:
        tag = "seller %s" % item["seller"]
        envelope = item["envelope"]
        if envelope.get("scope") != "seller":
            problems.append("%s scope %r" % (tag, envelope.get("scope")))
        if envelope.get("dev_account") != item["seller"]:
            problems.append("%s dev_account %r" % (tag,
                                                   envelope.get("dev_account")))
        problems = _envelope_problems(tag, envelope, problems, rate)
        for key in totals:
            totals[key] += int(envelope.get(key, 0))
    for key in totals:
        if totals[key] != int(market.get(key, -2)):
            problems.append("seller %s %d != market %s"
                            % (key, totals[key], market.get(key)))
    if int(empty_scope.get("month_count", -1)) != 0:
        problems.append("empty scope answers %r months"
                        % empty_scope.get("month_count"))
    if empty_scope.get("response_rate") is not None:
        problems.append("empty scope fabricates a rate")
    if empty_scope.get("market_response_rate") != rate:
        problems.append("empty scope lost the market benchmark")
    return problems


def text(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.4f" % value).rstrip("0").rstrip(".")
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_months"], envelope.get("month_count")),
        (labels["kpi_active"], envelope.get("active_month_count")),
        (labels["kpi_revisions"], envelope.get("revision_count")),
        (labels["kpi_up"], envelope.get("up_count")),
        (labels["kpi_down"], envelope.get("down_count")),
        (labels["kpi_watches"], envelope.get("watch_count")),
        (labels["kpi_unwatches"], envelope.get("unwatch_count")),
        (labels["kpi_net_watch"], envelope.get("watch_net_count")),
        (labels["kpi_questions"], envelope.get("question_count")),
        (labels["kpi_response"], envelope.get("response_month_count")),
        (labels["kpi_demand"], envelope.get("demand_month_count")),
        (labels["kpi_rate"], envelope.get("response_rate")),
        (labels["kpi_peak"], envelope.get("peak_revision_month")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def month_table(envelope, labels, e, dash):
    rows = envelope.get("months") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = envelope.get("peak_revision_count")
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_month"] else "",
                      e(name))
                   for name in (labels["col_month"], labels["col_rev"],
                                labels["col_up"], labels["col_down"],
                                labels["col_net"], labels["col_watch"],
                                labels["col_unwatch"], labels["col_watch_net"],
                                labels["col_question"], labels["col_run"],
                                labels["col_state"], labels["col_bar"]))
    body = []
    for row in rows:
        demand = int(row["watch_net_count"]) > 0 or int(
            row["question_count"]) > 0
        response = demand and int(row["revision_count"]) > 0
        if response:
            state = '<span class="badge on">%s</span>' % e(
                labels["badge_response"])
        elif demand:
            state = '<span class="badge off">%s</span>' % e(
                labels["badge_demand"])
        else:
            state = '<span class="badge">%s</span>' % e(labels["badge_quiet"])
        revisions = int(row["revision_count"])
        if not peak or revisions <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, revisions / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-month="%s"%s><td>%s</td>%s<td>%s</td><td>%s</td></tr>'
            % (e(str(row["month"])),
               ' class="quiet-row"' if not demand else "",
               e(str(row["month"])),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("revision_count", "up_count", "down_count",
                                   "net_count", "watch_count", "unwatch_count",
                                   "watch_net_count", "question_count",
                                   "running_revision")),
               state, bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def scope_card(envelope, labels, e, dash, heading, tag):
    bench = envelope.get("market_response_rate")
    badge = ""
    if bench is not None:
        badge = ' <span class=badge>%s %s</span>' % (
            e(labels["kpi_bench"]), e(text(bench, dash)))
    peak = envelope.get("peak_revision_month")
    peak_html = ""
    if peak:
        peak_html = ' <span class=badge>%s %s</span>' % (
            e(labels["peak_label"]), e(str(peak)))
    return (
        '<div class=card data-scope="%s">\n<h3>%s%s%s</h3>\n'
        "<div class=kpi>%s</div>\n%s\n</div>\n"
        % (e(tag), e(heading), peak_html, badge,
           kpi_html(envelope, labels, e, dash),
           month_table(envelope, labels, e, dash))
    )


def build_html(market, scoped, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_sum"], labels["law_split"], labels["law_watch_net"],
            labels["law_running"], labels["law_grid"], labels["law_demand"],
            labels["law_rate"], labels["law_peak"], labels["law_bench"],
            labels["law_partition"], labels["law_bar"], labels["law_empty"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    seller_cards = "".join(
        scope_card(item["envelope"], labels, e, dash,
                   "%s %s" % (labels["scope_seller"], item["seller"]),
                   item["seller"])
        for item in scoped)
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
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]),
           scope_card(market, labels, e, dash, labels["scope_market"],
                      "market"),
           e(labels["sec_sellers"]), seller_cards,
           e(labels["sec_law"]), law_html, e(labels["bar_caption"]),
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
    if sorted(doc.keys()) != sorted(PAYLOAD_KEYS):
        fails.append("payload keys %r" % sorted(doc.keys()))
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


def trim_envelope(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    doc["months"] = [{key: row[key] for key in ROW_KEYS}
                     for row in envelope.get("months") or []]
    return doc


def payload_of(market, scoped, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "market": trim_envelope(market),
        "sellers": [{"seller": item["seller"],
                     "envelope": trim_envelope(item["envelope"])}
                    for item in scoped],
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
        print("PRICE-DEMAND CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, scoped, empty_scope = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, scoped, empty_scope)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = market.get("disclaimer")
    doc = build_html(market, scoped, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(market, scoped, args.out, disclaimer, now)
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

    print("PRICE-DEMAND %s bytes=%d months=%d revisions=%d demand=%d "
          "response=%d rate=%r sellers=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             market["month_count"], market["revision_count"],
             market["demand_month_count"], market["response_month_count"],
             market["response_rate"], len(payload["sellers"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
