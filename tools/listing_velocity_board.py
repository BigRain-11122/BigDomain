#!/usr/bin/env python3
"""Render the shelf-to-sale velocity reading into one page a human can open.

Why this exists: api_listing_velocity answers "how long did this shelf sit
before it sold, and how does that compare with the market" with its own
AC-LV1..8 criteria, but git grep over tools/ and preview/ found no reader at
all, so the reading could only be had by calling the sandbox from a shell. A
seller cannot tell a high price from a bad description from a dead category
without it.

Nothing here re-implements a market rule. Every number comes from the shipped
api_listing_velocity() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/listing_velocity_board.py
  python tools/listing_velocity_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-LVB1..AC-LVB6 are pre-registered in src/os/backlog.md (R3420 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/listing-velocity-board-copy.json and appear in the rendered document
only, never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "listing-velocity-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "listing-velocity-board.json")
COPY = os.path.join(ROOT, "preview", "listing-velocity-board-copy.json")

FACE = "api_listing_velocity"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_listing_velocity"

# Pinned payload keys (AC-LVB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "scope",
    "listing_count", "sold_count", "unsold_count", "avg_seconds",
    "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "rows", "sellers", "disclaimer", "report", "sources", "sizes",
)

ROW_KEYS = (
    "listing_id", "listing_key", "title", "category", "delisted",
    "current_price", "shelf_opened_utc", "first_sale_utc", "elapsed_seconds",
    "category_avg_seconds", "unsold",
)

SELLER_KEYS = (
    "dev_account", "listing_count", "sold_count", "unsold_count",
    "avg_seconds", "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "disclaimer",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_market", "sec_rows", "sec_sellers",
    "sec_law", "sec_disc", "sec_rep", "kpi_listings", "kpi_sold",
    "kpi_unsold", "kpi_avg", "kpi_median", "kpi_fastest", "kpi_slowest",
    "kpi_market", "col_title", "col_category", "col_price", "col_delisted",
    "col_shelf", "col_first_sale", "col_elapsed", "col_cat_avg",
    "col_state", "col_bar", "col_seller", "col_sold", "col_unsold",
    "state_sold", "state_unsold", "yes", "no", "none", "unit_day",
    "unit_hour", "unit_minute", "law_elapsed", "law_unsold", "law_avg",
    "law_extremes", "law_market", "law_category", "law_bar",
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
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.unsold td.state{color:#b42318}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:110px}
.bar i{display:block;height:9px;border-radius:999px;background:#7b8fa8}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"
FMT = "%Y-%m-%dT%H:%M:%SZ"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_LVB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_LVB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_sellers(am, board):
    """Seller ids through the shipped board face, never typed."""
    return sorted(set(str(row["dev_account"]) for row in board["listings"]))


def read_world():
    """Read the market envelope plus one scoped envelope per seller."""
    tmp_root = tempfile.mkdtemp(prefix="listing-velocity-board-")
    db = os.path.join(tmp_root, "listing-velocity-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        market = dict(getattr(am, FACE)())
        sellers = [dict(getattr(am, FACE)(seller))
                   for seller in enumerate_sellers(am, board)]
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
    if not market.get("rows"):
        raise FaceError("no listing row on the market envelope")
    for row in market["rows"]:
        missing = [key for key in ROW_KEYS if key not in row]
        if missing:
            raise FaceError("row keys missing on %r: %s"
                            % (row.get("listing_id"), ",".join(missing)))
    for block in sellers:
        missing = [key for key in SELLER_KEYS if key not in block]
        if missing:
            raise FaceError("seller keys missing on %r: %s"
                            % (block.get("dev_account"), ",".join(missing)))
    return market, sellers, disclaimer


def _secs(earlier, later):
    import datetime
    start = datetime.datetime.strptime(str(earlier), FMT)
    end = datetime.datetime.strptime(str(later), FMT)
    return int((end - start).total_seconds())


def _mean(values):
    if not values:
        return None
    return float(sum(values)) / len(values)


def _median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (float(ordered[mid - 1]) + float(ordered[mid])) / 2.0


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _aggregate_problems(rows, block, label):
    """Recompute one envelope's mean and median from its own rows."""
    problems = []
    elapsed = [int(row["elapsed_seconds"]) for row in rows
               if not row["unsold"]]
    if not _close(block["avg_seconds"], _mean(elapsed)):
        problems.append("%s avg %r != %r"
                        % (label, block["avg_seconds"], _mean(elapsed)))
    want = None
    if elapsed:
        ordered = sorted(elapsed)
        mid = len(ordered) // 2
        want = (float(ordered[mid]) if len(ordered) % 2
                else (float(ordered[mid - 1]) + float(ordered[mid])) / 2.0)
    if not _close(block["median_seconds"], want):
        problems.append("%s median %r != %r"
                        % (label, block["median_seconds"], want))
    return problems, elapsed


def check_laws(market, sellers):
    """AC-LVB3 read at the source: refuse rather than print."""
    problems = []
    rows = market["rows"]
    if int(market["listing_count"]) != len(rows):
        problems.append("listing_count %s != rows %d"
                        % (market["listing_count"], len(rows)))
    if int(market["sold_count"]) + int(market["unsold_count"]) != len(rows):
        problems.append("sold+unsold != listings")
    for row in rows:
        name = "listing %s" % row["listing_id"]
        if row["unsold"]:
            for key in ("elapsed_seconds", "first_sale_utc",
                        "shelf_opened_utc"):
                if row[key] is not None:
                    problems.append("%s unsold %s=%r" % (name, key, row[key]))
            continue
        if row["elapsed_seconds"] is None or row["first_sale_utc"] is None \
                or row["shelf_opened_utc"] is None:
            problems.append("%s sold row with a missing stamp" % name)
            continue
        want = max(0, _secs(row["shelf_opened_utc"], row["first_sale_utc"]))
        if int(row["elapsed_seconds"]) != want:
            problems.append("%s elapsed %s != %d"
                            % (name, row["elapsed_seconds"], want))
        if int(row["elapsed_seconds"]) < 0:
            problems.append("%s negative elapsed" % name)

    agg_problems, elapsed = _aggregate_problems(rows, market, "market")
    problems.extend(agg_problems)
    if elapsed:
        fastest = min(elapsed)
        slowest = max(elapsed)
        if int(market["fastest_seconds"]) != fastest:
            problems.append("fastest_seconds %s != %d"
                            % (market["fastest_seconds"], fastest))
        if int(market["slowest_seconds"]) != slowest:
            problems.append("slowest_seconds %s != %d"
                            % (market["slowest_seconds"], slowest))
        want_fast = min(row["listing_id"] for row in rows
                        if not row["unsold"]
                        and int(row["elapsed_seconds"]) == fastest)
        want_slow = min(row["listing_id"] for row in rows
                        if not row["unsold"]
                        and int(row["elapsed_seconds"]) == slowest)
        if market["fastest_listing_id"] != want_fast:
            problems.append("fastest_listing_id %s != %s"
                            % (market["fastest_listing_id"], want_fast))
        if market["slowest_listing_id"] != want_slow:
            problems.append("slowest_listing_id %s != %s"
                            % (market["slowest_listing_id"], want_slow))
    else:
        for key in ("avg_seconds", "median_seconds", "fastest_seconds",
                    "slowest_seconds", "fastest_listing_id",
                    "slowest_listing_id"):
            if market[key] is not None:
                problems.append("market %s %r on a world with no sale"
                                % (key, market[key]))

    # market_avg_seconds pools every sold row in the whole market, so on the
    # unscoped read it must equal the scoped average.
    market_pool = [int(row["elapsed_seconds"]) for row in rows
                   if not row["unsold"]]
    if not _close(market["market_avg_seconds"], _mean(market_pool)):
        problems.append("market_avg_seconds %r != pooled %r"
                        % (market["market_avg_seconds"],
                           _mean(market_pool)))

    # category_avg_seconds is the pooled mean inside one effective bucket.
    buckets = {}
    for row in rows:
        if row["elapsed_seconds"] is None:
            continue
        buckets.setdefault(row["category"], []).append(
            int(row["elapsed_seconds"]))
    for row in rows:
        want = _mean(buckets.get(row["category"], []))
        if not _close(row["category_avg_seconds"], want):
            problems.append("listing %s category_avg %r != %r"
                            % (row["listing_id"], row["category_avg_seconds"],
                               want))

    # Row order: unsold last, then elapsed ascending, then id ascending.
    def key(item):
        return (item["unsold"],
                0 if item["elapsed_seconds"] is None
                else int(item["elapsed_seconds"]), item["listing_id"])
    if [key(row) for row in rows] != sorted(key(row) for row in rows):
        problems.append("rows are not in the face's own order")

    for block in sellers:
        name = str(block["dev_account"])
        own = block["rows"]
        if int(block["listing_count"]) != len(own):
            problems.append("%s listing_count %s != rows %d"
                            % (name, block["listing_count"], len(own)))
        if int(block["sold_count"]) + int(block["unsold_count"]) != len(own):
            problems.append("%s sold+unsold != listings" % name)
        if not _close(block["market_avg_seconds"], market["avg_seconds"]):
            problems.append("%s market_avg %r != market %r"
                            % (name, block["market_avg_seconds"],
                               market["avg_seconds"]))
        own_problems, own_elapsed = _aggregate_problems(own, block, name)
        problems.extend(own_problems)
        if own_elapsed:
            if int(block["fastest_seconds"]) != min(own_elapsed):
                problems.append("%s fastest" % name)
            if int(block["slowest_seconds"]) != max(own_elapsed):
                problems.append("%s slowest" % name)
        else:
            for field in ("avg_seconds", "median_seconds", "fastest_seconds",
                          "slowest_seconds", "fastest_listing_id",
                          "slowest_listing_id"):
                if block[field] is not None:
                    problems.append("%s %s %r with no sold row"
                                    % (name, field, block[field]))
    return problems


def fmt_duration(seconds, labels, none_text):
    """Day/hour text for an elapsed reading; the dash for an absent side."""
    if seconds is None:
        return none_text
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    parts = []
    if days:
        parts.append("%d%s" % (days, labels["unit_day"]))
    if hours:
        parts.append("%d%s" % (hours, labels["unit_hour"]))
    if not parts:
        parts.append("%d%s" % (minutes, labels["unit_minute"]))
    return "".join(parts)


def bar_share(value, peak):
    if value is None or not peak:
        return 0.0
    return max(0.0, min(100.0, float(value) / float(peak) * 100.0))


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(market, labels, e, dash):
    items = [
        (labels["kpi_listings"], fmt(market["listing_count"], dash)),
        (labels["kpi_sold"], fmt(market["sold_count"], dash)),
        (labels["kpi_unsold"], fmt(market["unsold_count"], dash)),
        (labels["kpi_avg"],
         fmt_duration(market["avg_seconds"], labels, dash)),
        (labels["kpi_median"],
         fmt_duration(market["median_seconds"], labels, dash)),
        (labels["kpi_fastest"],
         fmt_duration(market["fastest_seconds"], labels, dash)),
        (labels["kpi_slowest"],
         fmt_duration(market["slowest_seconds"], labels, dash)),
        (labels["kpi_market"],
         fmt_duration(market["market_avg_seconds"], labels, dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def rows_table(market, labels, e, dash):
    head = (labels["col_title"], labels["col_category"], labels["col_price"],
            labels["col_delisted"], labels["col_shelf"],
            labels["col_first_sale"], labels["col_elapsed"],
            labels["col_cat_avg"], labels["col_state"], labels["col_bar"])
    right = {labels["col_price"], labels["col_elapsed"], labels["col_cat_avg"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    peak = max([int(row["elapsed_seconds"]) for row in market["rows"]
                if row["elapsed_seconds"] is not None] or [0])
    body = []
    for row in market["rows"]:
        state = labels["state_unsold"] if row["unsold"] else labels["state_sold"]
        delisted = labels["yes"] if row["delisted"] else labels["no"]
        if row["unsold"]:
            bar = '<span class=empty>%s</span>' % e(dash)
        else:
            bar = ('<div class=bar><i style="width:%.1f%%"></i></div>'
                   % bar_share(row["elapsed_seconds"], peak))
        cells = [
            ("", fmt(row["title"], dash)),
            ("", fmt(row["category"], dash)),
            ("n", fmt(row["current_price"], dash)),
            ("", delisted),
            ("", fmt(row["shelf_opened_utc"], dash)),
            ("", fmt(row["first_sale_utc"], dash)),
            ("n", fmt_duration(row["elapsed_seconds"], labels, dash)),
            ("n", fmt_duration(row["category_avg_seconds"], labels, dash)),
            ("state", state),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr class="%s" data-listing="%s">%s</tr>'
                    % ("unsold" if row["unsold"] else "sold",
                       e(str(row["listing_id"])), tds))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def sellers_table(sellers, labels, e, dash):
    head = (labels["col_seller"], labels["kpi_listings"], labels["col_sold"],
            labels["col_unsold"], labels["kpi_avg"], labels["kpi_median"],
            labels["kpi_fastest"], labels["kpi_slowest"], labels["kpi_market"])
    right = set(head[1:])
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    body = []
    for block in sellers:
        cells = [
            ("", fmt(block["dev_account"], dash)),
            ("n", fmt(block["listing_count"], dash)),
            ("n", fmt(block["sold_count"], dash)),
            ("n", fmt(block["unsold_count"], dash)),
            ("n", fmt_duration(block["avg_seconds"], labels, dash)),
            ("n", fmt_duration(block["median_seconds"], labels, dash)),
            ("n", fmt_duration(block["fastest_seconds"], labels, dash)),
            ("n", fmt_duration(block["slowest_seconds"], labels, dash)),
            ("n", fmt_duration(block["market_avg_seconds"], labels, dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        body.append('<tr class="seller" data-seller="%s">%s</tr>'
                    % (e(str(block["dev_account"])), tds))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def build_html(market, sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_elapsed"], labels["law_unsold"], labels["law_avg"],
            labels["law_extremes"], labels["law_market"], labels["law_category"],
            labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/listing_velocity_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_market"]),
           kpi_html(market, labels, e, dash), e(labels["sec_rows"]),
           rows_table(market, labels, e, dash), e(labels["sec_sellers"]),
           sellers_table(sellers, labels, e, dash), e(labels["sec_law"]),
           law_html, e(labels["sec_disc"]), DISCLAIMER_SLOT,
           e(labels["aigc"]), e(labels["sec_rep"]), e(labels["cmd"]),
           e(now))
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
    """AC-PWC57 (R3579): landing this pair and re-deriving the CEO face are ONE run.

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
        print("LISTING-VELOCITY CHECK %s fails=%d html=%dB json=%dB"
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

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(market, sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "source_face": SOURCE_FACE,
        "scope": "market",
        "listing_count": market["listing_count"],
        "sold_count": market["sold_count"],
        "unsold_count": market["unsold_count"],
        "avg_seconds": market["avg_seconds"],
        "median_seconds": market["median_seconds"],
        "fastest_seconds": market["fastest_seconds"],
        "slowest_seconds": market["slowest_seconds"],
        "fastest_listing_id": market["fastest_listing_id"],
        "slowest_listing_id": market["slowest_listing_id"],
        "market_avg_seconds": market["market_avg_seconds"],
        "rows": market["rows"],
        "sellers": [{key: block[key] for key in SELLER_KEYS}
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
    print("LISTING-VELOCITY %s bytes=%d rows=%d sold=%d unsold=%d avg=%s "
          "face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             len(payload["rows"]), payload["sold_count"],
             payload["unsold_count"],
             fmt_duration(payload["avg_seconds"], labels, "-"), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
