#!/usr/bin/env python3
"""Render the seller monthly rating reading into one page a human can open.

Why this exists: api_seller_rating_months answers "is my rating intake and my
star level moving month over month" with its own AC-SRT1..8 criteria, but a
git grep over tools/ and preview/ answered rc=1 with zero hits, so the reading
could only be had by calling the sandbox from a shell. The reply latency board
(R3425) reads the waiting time and the owed queue, and the seller quality
scorecard (R3401) reads the lifetime star shape; neither shows the month axis
with the five bucket histogram beside it. Measured in R3427: the demo world
carries one month (2026-09) with two ratings, 5 stars and 4 stars, a pooled
average of 4.5, and zero replies.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_rating_months() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_rating_months_board.py
  python tools/seller_rating_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SRMB1..AC-SRMB6 are pre-registered in src/os/backlog.md (R3427 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-rating-months-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-rating-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-rating-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-rating-months-board-copy.json")

FACE = "api_seller_rating_months"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-SRMB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "market", "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 20 keys, identical on both scopes.
ENVELOPE_KEYS = (
    "scope", "dev_account", "month_count", "active_month_count",
    "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "low_star_count", "replied_count", "reply_coverage",
    "peak_month", "peak_rating_count", "first_month", "last_month",
    "latest_month_rating_count", "months", "market_avg_stars", "disclaimer",
)

# One month row, 14 keys.
ROW_KEYS = (
    "month", "rating_count", "buyer_count", "star_sum", "avg_stars",
    "five_star_count", "four_star_count", "three_star_count",
    "two_star_count", "one_star_count", "low_star_count", "replied_count",
    "reply_coverage", "running_rating",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_market", "sec_sellers",
    "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_active", "kpi_ratings", "kpi_buyers", "kpi_avg",
    "kpi_five", "kpi_low", "kpi_replied", "kpi_coverage", "kpi_peak",
    "kpi_latest", "kpi_market_avg",
    "col_month", "col_ratings", "col_buyers", "col_avg", "col_five",
    "col_four", "col_three", "col_two", "col_one", "col_low",
    "col_replied", "col_coverage", "col_running", "col_bar",
    "badge_peak", "empty_scope", "none",
    "law_count", "law_grid", "law_pooled", "law_hist", "law_lowstar",
    "law_coverage", "law_peak", "law_running", "law_distinct", "law_scope",
    "law_bar", "law_notadvice",
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
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:110px}
.bar i{display:block;height:9px;border-radius:999px;background:#4f7cac}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.peak{border-color:#9fb8c3;color:#3f6473}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_SRMB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_SRMB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_sellers(board):
    """Seller ids through the shipped board face, never typed."""
    return sorted(set(str(row["dev_account"]) for row in board["listings"]))


def read_world():
    """Read the market envelope plus one scoped envelope per seller."""
    tmp_root = tempfile.mkdtemp(prefix="seller-rating-months-board-")
    db = os.path.join(tmp_root, "seller-rating-months-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        market = dict(getattr(am, FACE)())
        sellers = [dict(getattr(am, FACE)(seller))
                   for seller in enumerate_sellers(board)]
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
    for envelope in [market] + sellers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("dev_account"), ",".join(missing)))
        for row in envelope["months"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("month"), ",".join(missing)))
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    return market, sellers, disclaimer


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _want_avg(star_sum, count):
    if not count:
        return None
    return round(float(star_sum) / float(count), 2)


def _want_coverage(replied, count):
    if not count:
        return None
    return round(float(replied) / float(count), 4)


def _envelope_problems(envelope, label):
    """AC-SRMB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["months"]
    count = int(envelope["rating_count"])
    if int(envelope["month_count"]) != len(rows):
        problems.append("%s month_count != months" % label)
    active = sum(1 for row in rows if int(row["rating_count"]) > 0)
    if int(envelope["active_month_count"]) != active:
        problems.append("%s active_month_count %r != %d"
                        % (label, envelope["active_month_count"], active))
    row_ratings = sum(int(row["rating_count"]) for row in rows)
    if count != row_ratings:
        problems.append("%s rating_count %r != row sum %d"
                        % (label, envelope["rating_count"], row_ratings))
    running = 0
    for row in rows:
        running += int(row["rating_count"])
        if int(row["running_rating"]) != running:
            problems.append("%s running_rating %r != %d on %s"
                            % (label, row["running_rating"], running,
                               row["month"]))
    if rows and int(rows[-1]["running_rating"]) != count:
        problems.append("%s last running_rating != rating_count" % label)
    row_star_sum = sum(int(row["star_sum"]) for row in rows)
    if int(envelope["star_sum"]) != row_star_sum:
        problems.append("%s star_sum %r != row sum %d"
                        % (label, envelope["star_sum"], row_star_sum))
    if not _close(envelope["avg_stars"], _want_avg(row_star_sum, count)):
        problems.append("%s avg_stars %r != %r"
                        % (label, envelope["avg_stars"],
                           _want_avg(row_star_sum, count)))
    for column in ("five_star_count", "low_star_count", "replied_count"):
        want = sum(int(row[column]) for row in rows)
        if int(envelope[column]) != want:
            problems.append("%s %s %r != row sum %d"
                            % (label, column, envelope[column], want))
    if not _close(envelope["reply_coverage"],
                  _want_coverage(int(envelope["replied_count"]), count)):
        problems.append("%s reply_coverage %r != %r"
                        % (label, envelope["reply_coverage"],
                           _want_coverage(int(envelope["replied_count"]),
                                          count)))
    peak_month = None
    peak_count = None
    for row in rows:
        value = int(row["rating_count"])
        if value > 0 and (peak_count is None or value > peak_count):
            peak_month = row["month"]
            peak_count = value
    if envelope["peak_month"] != peak_month:
        problems.append("%s peak_month %r != %r"
                        % (label, envelope["peak_month"], peak_month))
    if envelope["peak_rating_count"] != peak_count:
        problems.append("%s peak_rating_count %r != %r"
                        % (label, envelope["peak_rating_count"], peak_count))
    want_first = rows[0]["month"] if rows else None
    want_last = rows[-1]["month"] if rows else None
    if envelope["first_month"] != want_first:
        problems.append("%s first_month %r != %r"
                        % (label, envelope["first_month"], want_first))
    if envelope["last_month"] != want_last:
        problems.append("%s last_month %r != %r"
                        % (label, envelope["last_month"], want_last))
    want_latest = int(rows[-1]["rating_count"]) if rows else 0
    if int(envelope["latest_month_rating_count"]) != want_latest:
        problems.append("%s latest_month_rating_count %r != %d"
                        % (label, envelope["latest_month_rating_count"],
                           want_latest))
    previous = None
    for row in rows:
        month = str(row["month"])
        if len(month) != 7 or month[4] != "-":
            problems.append("%s month %r is not YYYY-MM" % (label, month))
        elif previous is not None and month <= previous:
            problems.append("%s month %r not ascending after %r"
                            % (label, month, previous))
        previous = month
        row_count = int(row["rating_count"])
        buckets = sum(int(row[key]) for key in (
            "five_star_count", "four_star_count", "three_star_count",
            "two_star_count", "one_star_count"))
        if buckets != row_count:
            problems.append("%s %s buckets %d != rating_count %d"
                            % (label, month, buckets, row_count))
        want_low = int(row["two_star_count"]) + int(row["one_star_count"])
        if int(row["low_star_count"]) != want_low:
            problems.append("%s %s low_star_count %r != %d"
                            % (label, month, row["low_star_count"], want_low))
        if not _close(row["avg_stars"],
                      _want_avg(int(row["star_sum"]), row_count)):
            problems.append("%s %s avg_stars %r != %r"
                            % (label, month, row["avg_stars"],
                               _want_avg(int(row["star_sum"]), row_count)))
        if not _close(row["reply_coverage"],
                      _want_coverage(int(row["replied_count"]), row_count)):
            problems.append("%s %s reply_coverage %r != %r"
                            % (label, month, row["reply_coverage"],
                               _want_coverage(int(row["replied_count"]),
                                              row_count)))
    return problems


def check_laws(market, sellers):
    problems = _envelope_problems(market, "market")
    if market["dev_account"] is not None:
        problems.append("market envelope carries a dev_account")
    if market["market_avg_stars"] is not None:
        problems.append("market envelope benchmarks itself: market_avg_stars")
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s is not a seller account" % name)
        if block["scope"] != "seller":
            problems.append("%s scope %r != seller" % (name, block["scope"]))
        if not _close(block["market_avg_stars"], market["avg_stars"]):
            problems.append("%s market_avg_stars %r != pooled market %r"
                            % (name, block["market_avg_stars"],
                               market["avg_stars"]))
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(envelope, labels, e, dash, market_avg=None):
    items = [
        (labels["kpi_months"], fmt(envelope["month_count"], dash)),
        (labels["kpi_active"], fmt(envelope["active_month_count"], dash)),
        (labels["kpi_ratings"], fmt(envelope["rating_count"], dash)),
        (labels["kpi_buyers"], fmt(envelope["buyer_count"], dash)),
        (labels["kpi_avg"], fmt(envelope["avg_stars"], dash)),
        (labels["kpi_five"], fmt(envelope["five_star_count"], dash)),
        (labels["kpi_low"], fmt(envelope["low_star_count"], dash)),
        (labels["kpi_replied"], fmt(envelope["replied_count"], dash)),
        (labels["kpi_coverage"], fmt(envelope["reply_coverage"], dash)),
        (labels["kpi_peak"], fmt(envelope["peak_month"], dash)),
        (labels["kpi_latest"], fmt(envelope["latest_month_rating_count"],
                                   dash)),
    ]
    if market_avg is not None:
        items.append((labels["kpi_market_avg"], fmt(market_avg, dash)))
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def months_table(envelope, labels, e, dash):
    head = (labels["col_month"], labels["col_ratings"], labels["col_buyers"],
            labels["col_avg"], labels["col_five"], labels["col_four"],
            labels["col_three"], labels["col_two"], labels["col_one"],
            labels["col_low"], labels["col_replied"], labels["col_coverage"],
            labels["col_running"], labels["col_bar"])
    right = {labels["col_ratings"], labels["col_buyers"], labels["col_avg"],
             labels["col_five"], labels["col_four"], labels["col_three"],
             labels["col_two"], labels["col_one"], labels["col_low"],
             labels["col_replied"], labels["col_coverage"],
             labels["col_running"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    peak = max([int(row["rating_count"]) for row in envelope["months"]]
               or [0])
    body = []
    for row in envelope["months"]:
        ratings = int(row["rating_count"])
        if not ratings:
            bar = '<span class=empty>%s</span>' % e(dash)
            month_cell = ("<td>%s</td>" % e(str(row["month"])))
        else:
            width = (float(ratings) / peak * 100.0) if peak else 100.0
            width = max(0.0, min(100.0, width))
            bar = '<div class=bar><i style="width:%.1f%%"></i></div>' % width
            if str(row["month"]) == str(envelope["peak_month"]):
                month_cell = ('<td>%s <span class="badge peak">%s</span></td>'
                              % (e(str(row["month"])),
                                 e(labels["badge_peak"])))
            else:
                month_cell = "<td>%s</td>" % e(str(row["month"]))
        cells = [
            ("n", fmt(row["rating_count"], dash)),
            ("n", fmt(row["buyer_count"], dash)),
            ("n", fmt(row["avg_stars"], dash)),
            ("n", fmt(row["five_star_count"], dash)),
            ("n", fmt(row["four_star_count"], dash)),
            ("n", fmt(row["three_star_count"], dash)),
            ("n", fmt(row["two_star_count"], dash)),
            ("n", fmt(row["one_star_count"], dash)),
            ("n", fmt(row["low_star_count"], dash)),
            ("n", fmt(row["replied_count"], dash)),
            ("n", fmt(row["reply_coverage"], dash)),
            ("n", fmt(row["running_rating"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr class="%s" data-month="%s">%s%s</tr>'
                    % ("active" if ratings else "quiet",
                       e(str(row["month"])), month_cell, tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, market, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash,
                        market_avg=market["avg_stars"]),
               months_table(block, labels, e, dash)))


def build_html(market, sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_grid"], labels["law_pooled"],
            labels["law_hist"], labels["law_lowstar"], labels["law_coverage"],
            labels["law_peak"], labels["law_running"], labels["law_distinct"],
            labels["law_scope"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])),
           seller_section(block, market, labels, e, dash))
        for block in sellers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_market"]),
           kpi_html(market, labels, e, dash),
           months_table(market, labels, e, dash), e(labels["sec_sellers"]),
           sections or ('<div class=card data-seller-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_scope"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
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
        print("SELLER-RATING-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        market, sellers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(market, sellers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(market, sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "market",
        "seller_count": len(sellers),
        "market": {key: market[key] for key in ENVELOPE_KEYS},
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

    print("SELLER-RATING-MONTHS %s bytes=%d sellers=%d months=%d ratings=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"], payload["market"]["month_count"],
             payload["market"]["rating_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
