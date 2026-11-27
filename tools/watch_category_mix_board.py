"""Buyer watch-intent category mix board (R3454).

WHY THIS PAGE EXISTS (measured at R3454, not assumed):
api_buyer_watch_category_mix shipped the intent-concentration face - every live
watch resolved to its CURRENT bucket through the single category seam, with the
purchased/open split, the delisted split, the per-row seller axis, share,
cumulative share, rank, top1, top3, herfindahl and the integer-decided pareto
count, plus the market-wide watch count and herfindahl as comparable context -
but a search over tools/, preview/ and src/os answered zero readers for its
name. api_watchlist answers how many rows a buyer watches, api_watch_budget
answers their live state and api_buyer_category_spend answers where the money
went, so "is my attention biased to categories or to sellers" could only be
read by calling the sandbox from a shell. This page opens the axis the face
already carries; it adds no table, no reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-WCMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3454 PIN row landed with the
driver and says so):
  - watch_count equals the row sum and equals purchased_count + open_count
  - per row open_count == watch_count - purchased_count and delisted_count
    never exceeds watch_count
  - per row share == watch_count / total rounded to six places, or None
    (never a fabricated zero) when the scope carries no live watch at all
  - cumulative_share replays monotonically from the first row and lands
    exactly on 1.0 on the last row
  - rank is 1..n and the rows follow the face's total order: -watch_count,
    then -open_count, then the category ascending with the uncategorized
    bucket pinned LAST only among ties
  - herfindahl == sum of the exact shares squared times 10000, rounded to two
    places, and None when the scope is empty
  - pareto_category_count is the smallest k whose cumulative watch count
    reaches 80%, decided on integers (cum * 5 >= total * 4) so a bucket
    landing exactly on 80% is counted, and None when the scope is empty
  - top1_share is the head row's share and top3_share is the rounded sum of
    the first three shares
  - per row seller_count <= watch_count and top_seller_share == the top
    seller's row count / the row watch count; the envelope seller_count is
    the distinct seller count and top_seller_share is that seller's total /
    the scope total
  - market_watch_count >= watch_count and market_herfindahl is computed by
    the same law over every live watch row, so a buyer scope never
    benchmarks itself
  - an empty scope answers watch_count 0, every derived field None and no
    rows

Every number on the page comes from the shipped face. Chinese labels live in
preview/watch-category-mix-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "watch-category-mix-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "watch-category-mix-board.json")
COPY = os.path.join(ROOT, "preview", "watch-category-mix-board-copy.json")

FACE = "api_buyer_watch_category_mix"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "market", "buyers", "disclaimer",
    "report", "sources", "sizes",
)

BUYER_KEYS = (
    "watch_count", "category_count", "purchased_count", "open_count",
    "delisted_count", "seller_count", "top_seller", "top_seller_share",
    "top1_share", "top3_share", "herfindahl", "pareto_category_count",
    "market_watch_count", "market_herfindahl",
)

ROW_KEYS = ("category", "watch_count", "purchased_count", "open_count",
            "delisted_count", "seller_count", "top_seller",
            "top_seller_share", "share", "cumulative_share", "rank")

BUYERS = ("usr:bob", "usr:carol", "usr:dave", "usr:ghost")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "kpi_watches", "kpi_categories", "kpi_purchased", "kpi_open",
    "kpi_delisted", "kpi_sellers", "kpi_top_seller", "kpi_top_share",
    "kpi_top1", "kpi_top3", "kpi_hhi", "kpi_pareto", "kpi_market",
    "market_cap", "col_rank", "col_category", "col_watches", "col_purchased",
    "col_open", "col_delisted", "col_sellers", "col_top_seller",
    "col_top_share", "col_share", "col_cumulative", "col_bar",
    "uncategorized", "empty", "none", "bar_caption",
    "law_sum", "law_open", "law_share", "law_cumulative", "law_order",
    "law_hhi", "law_pareto", "law_top", "law_seller", "law_delisted",
    "law_market", "law_zero", "law_bar", "law_notadvice",
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
.badge.off{border-color:#b9c7e4;background:#f1f4fd;color:#23388a}
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

# One pinned clock drives every write so the story reproduces.
STAMP = {"value": "2026-10-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_WCMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_WCMB_LAW"


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
    """One landed watch roll, every row by door.

    The factory world carries three live shelves and ZERO watch row, so every
    watch, unwatch, purchase and delisting below is made through the shipped
    watch_api, unwatch_api, publish_api, purchase_api and delist_api doors
    under the pinned clock - no sqlite rewrite, no typed ids, no padded rows.
    The story exercises the laws on purpose: four buckets for usr:bob with the
    uncategorized pair riding the tie-break, one purchase inside the busiest
    bucket, one delisted shelf inside the tools bucket, a two-bucket buyer
    whose head bucket lands exactly on 80% at row three of four, a buyer who
    unwatches back to an empty roll and a buyer who never watched at all.
    """
    STAMP["value"] = "2026-10-01T00:00:00Z"
    ids = {}

    def pub(dev, key, title, category):
        ids[key] = am.publish_api(dev, key, title, "demo", {"ep": key},
                                  5, False, supply=5,
                                  category=category)["listing_id"]

    pub("usr:dana", "data-a", "Data A", "data")
    pub("usr:dana", "data-b", "Data B", "data")
    pub("usr:frank", "data-c", "Data C", "data")
    pub("usr:frank", "data-d", "Data D", "data")
    pub("usr:dana", "tools-a", "Tools A", "tools")
    pub("usr:dana", "tools-b", "Tools B", "tools")
    pub("usr:frank", "tools-c", "Tools C", "tools")
    pub("usr:frank", "media-a", "Media A", "media")
    pub("usr:dana", "misc-a", "Misc A", None)
    pub("usr:dana", "misc-b", "Misc B", None)

    STAMP["value"] = "2026-11-02T00:00:00Z"
    for key in ("data-a", "data-b", "data-c", "data-d", "tools-a",
                "tools-b", "tools-c", "media-a", "misc-a", "misc-b"):
        am.watch_api("usr:bob", ids[key])
    for key in ("data-a", "data-c", "tools-b"):
        am.watch_api("usr:carol", ids[key])
    am.watch_api("usr:dave", ids["media-a"])
    am.unwatch_api("usr:dave", ids["media-a"])

    STAMP["value"] = "2026-11-10T00:00:00Z"
    am.purchase_api("usr:bob", ids["data-a"], "wcm-bob-1")
    am.purchase_api("usr:carol", ids["data-a"], "wcm-carol-1")

    STAMP["value"] = "2026-11-15T00:00:00Z"
    am.delist_api("usr:dana", ids["tools-a"])


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="wcm-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "wcm.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        envelopes = {buyer: dict(am.api_buyer_watch_category_mix(buyer))
                     for buyer in BUYERS}
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
    for buyer, envelope in envelopes.items():
        missing = [key for key in BUYER_KEYS if key not in envelope]
        if missing or "rows" not in envelope:
            raise FaceError("envelope keys missing for %s: %s"
                            % (buyer, ",".join(missing)))
    return envelopes


def read_empty():
    """The bare stack answers the honest empty envelope; the page shows it."""
    tmp_root = tempfile.mkdtemp(prefix="wcm-empty-")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "bare.db"))
        envelope = dict(am.api_buyer_watch_category_mix("usr:ghost"))
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    return envelope


def _ratio(part, total, places=6):
    return round(part / float(total), places) if total else None


def _market(envelopes):
    counts = {(envelope["market_watch_count"],
               envelope["market_herfindahl"]) for envelope in
              envelopes.values()}
    if len(counts) != 1:
        raise LawError("market context disagrees across scopes: %r"
                       % sorted(counts, key=str))
    watch, hhi = counts.pop()
    return {"watch_count": watch, "herfindahl": hhi}


def check_laws(envelopes, empty, market):
    """AC-WCMB3 read at the source: refuse rather than print."""
    problems = []
    for buyer, envelope in envelopes.items():
        rows = envelope.get("rows") or []
        total = int(envelope["watch_count"])
        if int(envelope["category_count"]) != len(rows):
            problems.append("%s category_count %r != %d rows"
                            % (buyer, envelope["category_count"], len(rows)))
        purchased = int(envelope["purchased_count"])
        opened = int(envelope["open_count"])
        if total != purchased + opened:
            problems.append("%s total %d != %d + %d"
                            % (buyer, total, purchased, opened))
        sums = {"watch_count": 0, "purchased_count": 0, "open_count": 0,
                "delisted_count": 0}
        sellers = set()
        running = 0
        squares = 0.0
        pareto = None
        previous = None
        for index, row in enumerate(rows, 1):
            watches = int(row["watch_count"])
            sums["watch_count"] += watches
            sums["purchased_count"] += int(row["purchased_count"])
            sums["open_count"] += int(row["open_count"])
            sums["delisted_count"] += int(row["delisted_count"])
            if int(row["open_count"]) != watches - int(row["purchased_count"]):
                problems.append("%s row %r open split broken"
                                % (buyer, row["category"]))
            if int(row["delisted_count"]) > watches:
                problems.append("%s row %r delisted %r > watches %d"
                                % (buyer, row["category"],
                                   row["delisted_count"], watches))
            if int(row["seller_count"]) > watches:
                problems.append("%s row %r sellers %r > watches %d"
                                % (buyer, row["category"],
                                   row["seller_count"], watches))
            if row["share"] != _ratio(watches, total):
                problems.append("%s row %r share %r != %r"
                                % (buyer, row["category"], row["share"],
                                   _ratio(watches, total)))
            # The row share is the row watch count over the scope total; the
            # top seller share is that seller's row count over the row watch
            # count, so it must land on a positive integer count no larger
            # than the row itself.
            share_of_row = float(row["top_seller_share"])
            exact = share_of_row * watches
            if not (0.0 < share_of_row <= 1.0) or \
                    abs(exact - round(exact)) > 1e-4 or not 1 <= round(exact) <= watches:
                problems.append("%s row %r top seller share %r is not a "
                                "count over %d watches"
                                % (buyer, row["category"], share_of_row,
                                   watches))
            if total:
                running += watches
                if row["cumulative_share"] != _ratio(running, total):
                    problems.append("%s row %r cumulative %r != %r"
                                    % (buyer, row["category"],
                                       row["cumulative_share"],
                                       _ratio(running, total)))
                squares += (watches / float(total)) ** 2
                if pareto is None and running * 5 >= total * 4:
                    pareto = index
            else:
                if row["share"] is not None or \
                        row["cumulative_share"] is not None:
                    problems.append("%s empty scope carries a share"
                                    % buyer)
            if int(row["rank"]) != index:
                problems.append("%s row %d rank %r"
                                % (buyer, index, row["rank"]))
            key = (watches, -int(row["open_count"]),
                   1 if row["category"] is None else 0,
                   str(row["category"] or ""))
            if previous is not None and key > previous:
                problems.append("%s rows out of order at %r"
                                % (buyer, row["category"]))
            previous = key
            if row["top_seller"]:
                sellers.add(row["top_seller"])
        for key, value in sums.items():
            if int(envelope[key]) != value:
                problems.append("%s %s %r != row sum %d"
                                % (buyer, key, envelope[key], value))
        if rows and rows[-1]["cumulative_share"] != 1.0:
            problems.append("%s last cumulative %r != 1.0"
                            % (buyer, rows[-1]["cumulative_share"]))
        wanted_hhi = round(squares * 10000, 2) if total else None
        if envelope["herfindahl"] != wanted_hhi:
            problems.append("%s herfindahl %r != %r"
                            % (buyer, envelope["herfindahl"], wanted_hhi))
        if envelope["pareto_category_count"] != pareto:
            problems.append("%s pareto %r != %r"
                            % (buyer, envelope["pareto_category_count"],
                               pareto))
        head = rows[0]["share"] if rows else None
        if envelope["top1_share"] != head:
            problems.append("%s top1 %r != %r"
                            % (buyer, envelope["top1_share"], head))
        top3 = (round(sum(row["share"] for row in rows[:3]), 6)
                if rows else None)
        if envelope["top3_share"] != top3:
            problems.append("%s top3 %r != %r"
                            % (buyer, envelope["top3_share"], top3))
        # The envelope seller count is the distinct sellers over the whole
        # scope, so the rows only bound it: at least one seller and no more
        # than the per-row seller counts added up. The envelope top seller
        # share is that seller's watch total over the scope total, so it must
        # land on a positive integer count no smaller than any single row's
        # top seller count.
        row_seller_sum = sum(int(row["seller_count"]) for row in rows)
        if total and not 1 <= int(envelope["seller_count"]) <= row_seller_sum:
            problems.append("%s seller_count %r outside 1..%d"
                            % (buyer, envelope["seller_count"],
                               row_seller_sum))
        top_share = envelope["top_seller_share"]
        if total:
            exact = float(top_share) * total
            row_max = max([float(row["top_seller_share"])
                           * int(row["watch_count"]) for row in rows] or [0])
            if not (0.0 < float(top_share) <= 1.0) or \
                    abs(exact - round(exact)) > 1e-4 or \
                    not int(envelope["seller_count"]) >= 1 or \
                    round(exact) < round(row_max - 1e-6):
                problems.append("%s top seller share %r is not a count over "
                                "%d watches" % (buyer, top_share, total))
        elif top_share is not None:
            problems.append("%s empty scope carries top seller share %r"
                            % (buyer, top_share))
        if int(envelope["market_watch_count"]) < total:
            problems.append("%s market %r < scope %d"
                            % (buyer, envelope["market_watch_count"], total))
        if envelope["market_herfindahl"] != market["herfindahl"]:
            problems.append("%s market herfindahl %r != %r"
                            % (buyer, envelope["market_herfindahl"],
                               market["herfindahl"]))
    # The bare world must answer the honest empty envelope.
    if empty.get("rows"):
        problems.append("bare world answered %d rows" % len(empty["rows"]))
    for key in ("watch_count", "category_count", "purchased_count",
                "open_count", "delisted_count", "seller_count"):
        if int(empty.get(key, -1)) != 0:
            problems.append("bare %s %r != 0" % (key, empty.get(key)))
    for key in ("top_seller", "top_seller_share", "top1_share", "top3_share",
                "herfindahl", "pareto_category_count"):
        if empty.get(key) is not None:
            problems.append("bare %s %r is not None" % (key, empty.get(key)))
    return problems


def text(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, float):
        return ("%.6f" % value).rstrip("0").rstrip(".")
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_watches"], envelope.get("watch_count")),
        (labels["kpi_categories"], envelope.get("category_count")),
        (labels["kpi_purchased"], envelope.get("purchased_count")),
        (labels["kpi_open"], envelope.get("open_count")),
        (labels["kpi_delisted"], envelope.get("delisted_count")),
        (labels["kpi_sellers"], envelope.get("seller_count")),
        (labels["kpi_top_seller"], envelope.get("top_seller")),
        (labels["kpi_top_share"], envelope.get("top_seller_share")),
        (labels["kpi_top1"], envelope.get("top1_share")),
        (labels["kpi_top3"], envelope.get("top3_share")),
        (labels["kpi_hhi"], envelope.get("herfindahl")),
        (labels["kpi_pareto"], envelope.get("pareto_category_count")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def row_table(envelope, labels, e, dash):
    rows = envelope.get("rows") or []
    if not rows:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    peak = max(int(row["watch_count"]) for row in rows)
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name not in (labels["col_rank"],
                                                   labels["col_category"],
                                                   labels["col_top_seller"])
                      else "", e(name))
                   for name in (labels["col_rank"], labels["col_category"],
                                labels["col_watches"], labels["col_purchased"],
                                labels["col_open"], labels["col_delisted"],
                                labels["col_sellers"], labels["col_top_seller"],
                                labels["col_top_share"], labels["col_share"],
                                labels["col_cumulative"], labels["col_bar"]))
    body = []
    for row in rows:
        watches = int(row["watch_count"])
        category = (row["category"] if row["category"] is not None
                    else labels["uncategorized"])
        quiet = watches == 0
        if not peak:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, watches / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-category="%s"%s><td class="n">%s</td><td>%s</td>%s'
            '<td>%s</td><td>%s</td><td>%s</td></tr>'
            % (e(str(category)), ' class="quiet-row"' if quiet else "",
               e(text(row["rank"], dash)), e(str(category)),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("watch_count", "purchased_count",
                                   "open_count", "delisted_count",
                                   "seller_count")),
               e(str(row["top_seller"] or dash)),
               "".join('<td class="n">%s</td>' % e(text(row[key], dash))
                       for key in ("top_seller_share", "share",
                                   "cumulative_share")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def buyer_card(buyer, envelope, labels, e, dash):
    empty = not envelope.get("rows")
    return ('<div class=card data-buyer="%s"><h3 style="margin:0 0 8px;'
            'font-size:14px">%s</h3><div class=kpi>%s</div>%s'
            '<p class=cap>%s</p></div>'
            % (e(buyer), e(buyer), kpi_html(envelope, labels, e, dash),
               row_table(envelope, labels, e, dash) if not empty
               else "<p class=empty>%s</p>" % e(labels["empty"]),
               e(labels["bar_caption"])))


def build_html(buyers, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_sum"], labels["law_open"], labels["law_share"],
            labels["law_cumulative"], labels["law_order"], labels["law_hhi"],
            labels["law_pareto"], labels["law_top"], labels["law_seller"],
            labels["law_delisted"], labels["law_market"], labels["law_zero"],
            labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    market_html = (
        '<div class=card><div class=kpi>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div></div>'
        '<p class=cap>%s</p></div>'
        % (e(labels["kpi_market"]), e(text(market.get("watch_count"), dash)),
           e(labels["kpi_hhi"]), e(text(market.get("herfindahl"), dash)),
           e(labels["market_cap"])))
    cards = "".join(buyer_card(buyer, envelope, labels, e, dash)
                    for buyer, envelope in buyers)
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
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]), market_html,
           e(labels["sec_buyers"]), cards,
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
    if not os.path.exists(html_path):
        return ["html missing: %s" % html_path]
    if not os.path.exists(json_path):
        return ["json missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    sizes = payload.get("sizes") or {}
    if sizes.get("html") != os.path.getsize(html_path):
        fails.append("json records html %r but disk answers %d"
                     % (sizes.get("html"), os.path.getsize(html_path)))
    if sizes.get("json") != os.path.getsize(json_path):
        fails.append("json records itself as %r but disk answers %d"
                     % (sizes.get("json"), os.path.getsize(json_path)))
    extra = sorted(set(payload) - set(PAYLOAD_KEYS))
    missing = sorted(set(PAYLOAD_KEYS) - set(payload))
    if extra or missing:
        fails.append("payload keys extra=%r missing=%r" % (extra, missing))
    return fails


def check_sources(json_path):
    fails = []
    if not os.path.exists(json_path):
        return ["json missing: %s" % json_path]
    with open(json_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    recorded = payload.get("sources") or {}
    if sorted(recorded) != ["apimarket", "copy", "driver", "report"]:
        fails.append("source keys %r" % sorted(recorded))
        return fails
    live = source_fingerprints()
    for key, value in live.items():
        if recorded.get(key) != value:
            fails.append("source %s moved: %r -> %r"
                         % (key, recorded.get(key), value))
    return fails


def trim_buyer(buyer, envelope):
    doc = {"buyer_id": buyer}
    for key in BUYER_KEYS:
        doc[key] = envelope[key]
    doc["rows"] = [{key: row[key] for key in ROW_KEYS}
                   for row in envelope.get("rows") or []]
    return doc


def payload_of(buyers, market, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "buyers",
        "market": market,
        "buyers": [trim_buyer(buyer, envelope)
                   for buyer, envelope in buyers],
        "disclaimer": disclaimer,
        "report": os.path.relpath(path, ROOT).replace("\\", "/"),
        "sources": source_fingerprints(),
    }


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
    """AC-PWC35 (R3557): landing this pair and re-deriving the CEO face are ONE run.

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
        print("WATCH-CATEGORY-MIX CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelopes = read_world()
        empty = read_empty()
        market = _market(envelopes)
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    try:
        problems = check_laws(envelopes, empty, market)
    except LawError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = envelopes[BUYERS[0]].get("disclaimer")
    buyers = [(buyer, envelopes[buyer]) for buyer in BUYERS]
    doc = build_html(buyers, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(buyers, market, args.out, disclaimer, now)
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

    print("WATCH-CATEGORY-MIX %s bytes=%d buyers=%d market_watches=%d "
          "face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(buyers),
             int(market["watch_count"]), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
