"""Per-category monthly watch-flow board (R3450).

WHY THIS PAGE EXISTS (measured at R3450, not assumed):
api_category_watch_months shipped the market's attention by CATEGORY on a
monthly axis - watches and unwatches booked in the month of the event, a
running live count per category, the busy month and the month-over-month
change - but a search over tools/, preview/ and src/os answered rc=1 for its
name. The whole-market and per-seller watch axes already had pages, and the
buyer side had its own timeline, so a rush into one bucket read exactly like a
flat market once the per-buyer lines were added up by hand.
This page opens the axis the face already carries; it adds no table, no
reading and no business semantics.

LAWS THE PAGE ITSELF REFUSES TO BREAK (AC-CWMB3, fixed in this round's window
before the first render; the src/os/backlog.md R3450 PIN row landed with the
driver and says so):
  - month_count == len(months)
  - the month rows are one contiguous grid, so a month with no event still
    carries an honest zero row
  - per row: the cell watches sum to watch_count, the cell unwatches sum to
    unwatch_count, net_count == watch_count - unwatch_count, category_count ==
    the number of cells and active_count == the sum of cell live counts
  - per cell: net_count == watch_count - unwatch_count and no live count is
    negative; replaying every category cell across the grid reproduces the
    landed live count exactly, so a later unwatch never rewrites a month
  - cells are ordered by category ascending with the uncategorized bucket last
  - envelope totals equal the row sums, envelope net equals watch minus
    unwatch, and live_watch_count equals the last row's live total
  - category_count is the number of distinct categories across the window
  - peak_month names the FIRST row carrying the maximum positive watch count
    and is None when nothing was watched
  - month_over_month_change is the last row watch count minus the previous
    one, and None when the window holds fewer than two months

Every number on the page comes from the shipped face. Chinese labels live in
preview/category-watch-months-board-copy.json so this driver stays ASCII.
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

OUT_HTML = os.path.join(ROOT, "preview", "category-watch-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-watch-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-watch-months-board-copy.json")

FACE = "api_category_watch_months"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "envelope", "disclaimer", "report",
    "sources", "sizes",
)

ENVELOPE_KEYS = (
    "month_count", "first_month", "last_month", "watch_count",
    "unwatch_count", "net_count", "live_watch_count", "category_count",
    "buyer_count", "listing_count", "peak_month", "peak_watch_count",
    "month_over_month_change", "months", "disclaimer",
)

MONTH_KEYS = ("month", "watch_count", "unwatch_count", "net_count",
              "active_count", "category_count", "categories")

CELL_KEYS = ("category", "watch_count", "unwatch_count", "net_count",
             "active_count", "buyer_count", "listing_count")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_months", "sec_cats", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_watch", "kpi_unwatch",
    "kpi_net", "kpi_live", "kpi_cats", "kpi_buyers", "kpi_listings",
    "kpi_peak", "kpi_peak_count", "kpi_change",
    "col_month", "col_watch", "col_unwatch", "col_net", "col_active",
    "col_cats", "col_buyers", "col_listings", "col_bar",
    "col_category", "col_scope",
    "badge_live", "badge_zero", "badge_closed", "uncategorized",
    "empty", "none", "bar_caption",
    "law_grid", "law_cells", "law_carry", "law_order", "law_sums",
    "law_live", "law_cats", "law_peak", "law_change", "law_zero",
    "law_bar", "law_notadvice",
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

# One pinned clock drives every write so the month buckets reproduce.
STAMP = {"value": "2026-11-01T00:00:00Z"}


class FaceError(Exception):
    code = "E_CWMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_CWMB_LAW"


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
    """One landed category timeline, every row by door.

    The factory world carries three listings and zero watch rows, so four
    listings are published through the shipped publish_api door under the
    pinned clock and every watch and unwatch below is made through the shipped
    watch_api / unwatch_api doors. Two categories gain and lose attention
    across six months, one factory shelf with no category supplies the
    uncategorized bucket, August carries no event at all, and the last month
    swaps one tools watch for another so its net is an honest zero.
    """
    STAMP["value"] = "2026-06-01T00:00:00Z"
    am.publish_api("usr:dana", "data-lens", "Data Lens",
                   "row counts for one table",
                   {"endpoint": "/rows/count", "rows": 1200}, 12, True,
                   category="data")
    am.publish_api("usr:dana", "data-digest", "Data Digest",
                   "weekly digest of new rows",
                   {"endpoint": "/rows/digest", "rows": 40}, 9, True,
                   category="data")
    am.publish_api("usr:frank", "tools-forge", "Tools Forge",
                   "batch rename helper",
                   {"endpoint": "/tools/rename", "batch": 200}, 7, True,
                   category="tools")
    am.publish_api("usr:frank", "tools-mint", "Tools Mint",
                   "csv to json converter",
                   {"endpoint": "/tools/mint", "batch": 100}, 5, True,
                   category="tools")

    board = am.api_board() or {}
    ids = {}
    for row in board.get("listings") or []:
        ids[str(row["listing_key"])] = int(row["listing_id"])
    needed = ("data-lens", "data-digest", "tools-forge", "tools-mint",
              "risk-scan")
    for key in needed:
        if key not in ids:
            raise FaceError("shipped board lost %s" % key)
    data_lens = ids["data-lens"]
    data_digest = ids["data-digest"]
    tools_forge = ids["tools-forge"]
    tools_mint = ids["tools-mint"]
    risk = ids["risk-scan"]

    STAMP["value"] = "2026-06-10T00:00:00Z"
    am.watch_api("usr:bob", data_lens)
    am.watch_api("usr:carol", tools_forge)
    STAMP["value"] = "2026-07-08T00:00:00Z"
    am.watch_api("usr:dave", data_lens)
    am.watch_api("usr:bob", risk)
    STAMP["value"] = "2026-09-04T00:00:00Z"
    am.unwatch_api("usr:bob", data_lens)
    am.watch_api("usr:carol", tools_mint)
    am.unwatch_api("usr:bob", risk)
    STAMP["value"] = "2026-10-06T00:00:00Z"
    am.watch_api("usr:erin", data_digest)
    STAMP["value"] = "2026-11-03T00:00:00Z"
    am.unwatch_api("usr:carol", tools_forge)
    am.watch_api("usr:dave", tools_forge)


def read_world():
    tmp_root = tempfile.mkdtemp(prefix="cwmb-")
    led = mtr = dk = am = None
    orig_now = A._now_utc
    try:
        led, mtr, dk, am = R.build_stack(os.path.join(tmp_root, "cwmb.db"))
        R.seed_demo(am, led, dk)
        A._now_utc = _clock
        build_world(am)
        envelope = dict(am.api_category_watch_months())
        empty = dict(am.api_category_watch_months(
            include_uncategorized=False))
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
    missing = [key for key in ENVELOPE_KEYS if key not in envelope]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    return envelope, empty


def _month_index(label):
    return int(label[:4]) * 12 + int(label[5:7])


def _category_order(cells):
    names = [cell["category"] for cell in cells]
    keyed = sorted([name for name in names if name is not None])
    expected = keyed + ([None] if None in names else [])
    if names != expected:
        return False
    return True


def check_laws(envelope, no_uncat):
    """AC-CWMB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(rows):
        problems.append("month_count %r != %d rows"
                        % (envelope.get("month_count"), len(rows)))
    previous = None
    row_watch = 0
    row_unwatch = 0
    categories = set()
    running = {}
    last_active = 0
    for row in rows:
        month = row["month"]
        if previous is not None and _month_index(month) - \
                _month_index(previous) != 1:
            problems.append("rows not contiguous at %s" % month)
        previous = month
        cells = row.get("categories") or []
        if not _category_order(cells):
            problems.append("row %s cells not ordered" % month)
        cell_watch = 0
        cell_unwatch = 0
        if int(row.get("category_count", -1)) != len(cells):
            problems.append("row %s category_count %r != %d cells"
                            % (month, row.get("category_count"), len(cells)))
        for cell in cells:
            category = cell["category"]
            categories.add(category)
            watch = int(cell["watch_count"])
            unwatch = int(cell["unwatch_count"])
            net = int(cell["net_count"])
            if net != watch - unwatch:
                problems.append("cell %s/%s net %d != %d - %d"
                                % (month, category, net, watch, unwatch))
            running[category] = running.get(category, 0) + net
            if running[category] < 0:
                problems.append("cell %s/%s drives live negative"
                                % (month, category))
            if int(cell["active_count"]) != running[category]:
                problems.append("cell %s/%s active %r != replay %d"
                                % (month, category, cell["active_count"],
                                   running[category]))
            if int(cell["buyer_count"]) < 0 or int(cell["listing_count"]) < 0:
                problems.append("cell %s/%s negative count"
                                % (month, category))
            cell_watch += watch
            cell_unwatch += unwatch
        if cell_watch != int(row["watch_count"]):
            problems.append("row %s watch %r != cell sum %d"
                            % (month, row["watch_count"], cell_watch))
        if cell_unwatch != int(row["unwatch_count"]):
            problems.append("row %s unwatch %r != cell sum %d"
                            % (month, row["unwatch_count"], cell_unwatch))
        if int(row["net_count"]) != cell_watch - cell_unwatch:
            problems.append("row %s net %r != %d - %d"
                            % (month, row["net_count"], cell_watch,
                               cell_unwatch))
        # A row lists only the categories that carried an event that month,
        # while its live total covers every category booked so far.
        if int(row["active_count"]) != sum(running.values()):
            problems.append("row %s active %r != replay total %d"
                            % (month, row["active_count"],
                               sum(running.values())))
        row_watch += cell_watch
        row_unwatch += cell_unwatch
        last_active = int(row["active_count"])
    if int(envelope.get("watch_count", -1)) != row_watch:
        problems.append("watch total %r != row sum %d"
                        % (envelope.get("watch_count"), row_watch))
    if int(envelope.get("unwatch_count", -1)) != row_unwatch:
        problems.append("unwatch total %r != row sum %d"
                        % (envelope.get("unwatch_count"), row_unwatch))
    if int(envelope.get("net_count", 0)) != row_watch - row_unwatch:
        problems.append("net %r != %d - %d"
                        % (envelope.get("net_count"), row_watch,
                           row_unwatch))
    if int(envelope.get("live_watch_count", -1)) != last_active:
        problems.append("live %r != last row active %d"
                        % (envelope.get("live_watch_count"), last_active))
    if int(envelope.get("category_count", -1)) != len(categories):
        problems.append("category total %r != %d distinct"
                        % (envelope.get("category_count"), len(categories)))
    peak_month = None
    peak_count = None
    for row in rows:
        watch = int(row["watch_count"])
        if watch <= 0:
            continue
        if peak_count is None or watch > peak_count:
            peak_month = row["month"]
            peak_count = watch
    if envelope.get("peak_month") != peak_month:
        problems.append("peak month %r != %r"
                        % (envelope.get("peak_month"), peak_month))
    if envelope.get("peak_watch_count") != peak_count:
        problems.append("peak count %r != %r"
                        % (envelope.get("peak_watch_count"), peak_count))
    change = None
    if len(rows) >= 2:
        change = int(rows[-1]["watch_count"]) - int(rows[-2]["watch_count"])
    if envelope.get("month_over_month_change") != change:
        problems.append("change %r != %r"
                        % (envelope.get("month_over_month_change"), change))
    first = rows[0]["month"] if rows else None
    last = rows[-1]["month"] if rows else None
    if envelope.get("first_month") != first:
        problems.append("first month %r != %r"
                        % (envelope.get("first_month"), first))
    if envelope.get("last_month") != last:
        problems.append("last month %r != %r" % (envelope.get("last_month"),
                                                 last))
    if int(envelope.get("buyer_count", -1)) < 0:
        problems.append("negative buyer count")
    if int(envelope.get("listing_count", -1)) < 0:
        problems.append("negative listing count")
    uncat_watch = 0
    uncat_unwatch = 0
    for row in rows:
        for cell in row.get("categories") or []:
            if cell["category"] is None:
                uncat_watch += int(cell["watch_count"])
                uncat_unwatch += int(cell["unwatch_count"])
    for row in no_uncat.get("months") or []:
        for cell in row.get("categories") or []:
            if cell["category"] is None:
                problems.append("flag-off probe still carries the bucket at %s"
                                % row["month"])
    if int(no_uncat.get("watch_count", -1)) != row_watch - uncat_watch:
        problems.append("flag-off watch %r != %d - %d"
                        % (no_uncat.get("watch_count"), row_watch,
                           uncat_watch))
    if int(no_uncat.get("unwatch_count", -1)) != row_unwatch - uncat_unwatch:
        problems.append("flag-off unwatch %r != %d - %d"
                        % (no_uncat.get("unwatch_count"), row_unwatch,
                           uncat_unwatch))
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
        (labels["kpi_first"], envelope.get("first_month")),
        (labels["kpi_last"], envelope.get("last_month")),
        (labels["kpi_watch"], envelope.get("watch_count")),
        (labels["kpi_unwatch"], envelope.get("unwatch_count")),
        (labels["kpi_net"], envelope.get("net_count")),
        (labels["kpi_live"], envelope.get("live_watch_count")),
        (labels["kpi_cats"], envelope.get("category_count")),
        (labels["kpi_buyers"], envelope.get("buyer_count")),
        (labels["kpi_listings"], envelope.get("listing_count")),
        (labels["kpi_peak"], envelope.get("peak_month")),
        (labels["kpi_peak_count"], envelope.get("peak_watch_count")),
        (labels["kpi_change"], envelope.get("month_over_month_change")),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(text(value, dash)))
                   for name, value in items)


def category_name(value, labels, e):
    if value is None:
        return e(labels["uncategorized"])
    return e(str(value))


def cell_token(value):
    """A stable attribute token, so an absent category never prints None."""
    return "uncategorized" if value is None else str(value)


def cell_table(row, labels, e, dash, peak):
    cells = row.get("categories") or []
    if not cells:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name not in (labels["col_category"],)
                      else "", e(name))
                   for name in (labels["col_category"], labels["col_watch"],
                                labels["col_unwatch"], labels["col_net"],
                                labels["col_active"], labels["col_buyers"],
                                labels["col_listings"], labels["col_bar"]))
    body = []
    for cell in cells:
        watch = int(cell["watch_count"])
        if not peak or watch <= 0:
            bar = e(dash)
        else:
            pos = max(0.0, min(100.0, watch / float(peak) * 100.0))
            bar = '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos
        body.append(
            '<tr data-category="%s"><td>%s</td>%s<td>%s</td></tr>'
            % (e(cell_token(cell["category"])),
               category_name(cell["category"], labels, e),
               "".join('<td class="n">%s</td>' % e(text(cell[key], dash))
                       for key in ("watch_count", "unwatch_count",
                                   "net_count", "active_count",
                                   "buyer_count", "listing_count")),
               bar))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def month_card(row, labels, e, dash, peak):
    watch = int(row["watch_count"])
    unwatch = int(row["unwatch_count"])
    if watch == 0 and unwatch == 0:
        badge = '<span class="badge">%s</span>' % e(labels["badge_zero"])
        quiet = True
    elif int(row["active_count"]) > 0:
        badge = '<span class="badge on">%s</span>' % e(labels["badge_live"])
        quiet = False
    else:
        badge = '<span class="badge off">%s</span>' % e(labels["badge_closed"])
        quiet = False
    cells = row.get("categories") or []
    table = cell_table(row, labels, e, dash, peak)
    return (
        '<div class=card data-month="%s"%s>\n<h3>%s %s</h3>\n'
        "<div class=kpi>"
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        '<div><span>%s</span><b>%s</b></div>'
        "</div>\n%s\n</div>\n"
        % (e(str(row["month"])), ' class="quiet-row"' if quiet else "",
           e(str(row["month"])), badge,
           e(labels["col_watch"]), e(text(row["watch_count"], dash)),
           e(labels["col_unwatch"]), e(text(row["unwatch_count"], dash)),
           e(labels["col_net"]), e(text(row["net_count"], dash)),
           e(labels["col_active"]), e(text(row["active_count"], dash)),
           e(labels["col_cats"]), e(text(len(cells), dash)),
           table))


def category_summary(envelope, labels, e, dash):
    """Sums of the face's own cells, never a new reading."""
    totals = {}
    for row in envelope.get("months") or []:
        for cell in row.get("categories") or []:
            slot = totals.setdefault(cell["category"], {
                "watch": 0, "unwatch": 0, "live": 0})
            slot["watch"] += int(cell["watch_count"])
            slot["unwatch"] += int(cell["unwatch_count"])
            slot["live"] = int(cell["active_count"])
    if not totals:
        return "<p class=empty>%s</p>" % e(labels["empty"])
    names = sorted([name for name in totals if name is not None])
    if None in totals:
        names.append(None)
    head = "".join('<th%s>%s</th>'
                   % (' class="n"' if name != labels["col_scope"] else "",
                      e(name))
                   for name in (labels["col_scope"], labels["col_watch"],
                                labels["col_unwatch"], labels["col_net"],
                                labels["col_active"]))
    body = []
    for name in names:
        slot = totals[name]
        net = slot["watch"] - slot["unwatch"]
        body.append('<tr data-category="%s"><td>%s</td>%s</tr>'
                    % (e(cell_token(name)), category_name(name, labels, e),
                       "".join('<td class="n">%s</td>'
                               % e(text(value, dash))
                               for value in (slot["watch"],
                                             slot["unwatch"], net,
                                             slot["live"]))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_grid"], labels["law_cells"], labels["law_carry"],
            labels["law_order"], labels["law_sums"], labels["law_live"],
            labels["law_cats"], labels["law_peak"], labels["law_change"],
            labels["law_zero"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    peak = envelope.get("peak_watch_count") or 0
    months = "".join(month_card(row, labels, e, dash, peak)
                     for row in envelope.get("months") or [])
    if not months:
        months = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s\n<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), FACE,
           e(labels["sec_market"]), kpi_html(envelope, labels, e, dash),
           e(labels["sec_months"]), months,
           e(labels["sec_cats"]),
           category_summary(envelope, labels, e, dash),
           e(labels["bar_caption"]),
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


def trim_envelope(envelope):
    doc = {key: envelope[key] for key in ENVELOPE_KEYS if key != "months"}
    months = []
    for row in envelope.get("months") or []:
        item = {key: row[key] for key in MONTH_KEYS if key != "categories"}
        item["categories"] = [{key: cell[key] for key in CELL_KEYS}
                              for cell in row.get("categories") or []]
        months.append(item)
    doc["months"] = months
    return doc


def payload_of(envelope, path, disclaimer, now):
    return {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "envelope": trim_envelope(envelope),
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
    """AC-PWC50 (R3572): landing this pair and re-deriving the CEO face are ONE run.

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
        print("CATEGORY-WATCH-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope, empty = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelope, empty)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = envelope.get("disclaimer")
    doc = build_html(envelope, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = payload_of(envelope, args.out, disclaimer, now)
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

    print("CATEGORY-WATCH-MONTHS %s bytes=%d months=%d watch=%d live=%d "
          "cats=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             int(envelope["month_count"]), int(envelope["watch_count"]),
             int(envelope["live_watch_count"]),
             int(envelope["category_count"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))