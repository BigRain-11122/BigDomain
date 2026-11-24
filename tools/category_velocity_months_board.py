#!/usr/bin/env python3
"""Render the per-category monthly sell-through velocity into one page.

Why this exists: api_category_velocity_months answers "how many net sales did
each category book in every UTC month, how long did each sale sit on the shelf,
and is this month slower than the last" with its own AC-CVMT criteria, but a
search over tools/, preview/ and src/os answered rc=1 with zero hits. The market
already had a lifetime velocity face, a supply face and an asking-price face;
none of them put a net sale on a calendar month a reader could open, so a
quarter that quietly went from two sales to zero looked exactly like a healthy
one from outside.

Nothing here re-implements a market rule. Every number comes from the shipped
api_category_velocity_months() face read over a fresh throwaway demo world
seeded through the shipped report helpers. The page prints what the face hands
it and never recomputes a total; the only thing it draws is the width of one
marker showing where the month median sits between that month fastest and
slowest sale, and the page says out loud that the bar is a position, not a
share. A broken identity refuses the render instead of printing a plausible
page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/category_velocity_months_board.py
  python tools/category_velocity_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-CVMB1..AC-CVMB6 are pre-registered in src/os/backlog.md (R3441 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/category-velocity-months-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "category-velocity-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-velocity-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-velocity-months-board-copy.json")

FACE = "api_category_velocity_months"

# Pinned payload keys (AC-CVMB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "month_count", "first_month",
    "last_month", "sale_count", "listing_count", "category_count",
    "peak_month", "peak_sale_count", "month_over_month_change",
    "market_avg_seconds", "market_median_seconds", "months", "disclaimer",
    "report", "sources", "sizes",
)

# The shipped 13-key month row and 5-key category cell.
ROW_KEYS = (
    "month", "as_of", "sale_count", "listing_count", "category_count",
    "avg_seconds", "median_seconds", "fastest_seconds", "slowest_seconds",
    "fastest_listing_id", "slowest_listing_id", "market_avg_seconds",
    "categories",
)
CELL_KEYS = ("category", "sale_count", "listing_count", "avg_seconds",
             "median_seconds")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_months", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_sales", "kpi_listings",
    "kpi_categories", "kpi_peak", "kpi_peak_sales", "kpi_change",
    "kpi_mkt_avg", "kpi_mkt_median",
    "kpi_row_sales", "kpi_row_listings", "kpi_row_cats", "kpi_row_avg",
    "kpi_row_median", "kpi_row_fastest", "kpi_row_slowest",
    "col_category", "col_sales", "col_listings", "col_avg", "col_median",
    "badge_uncategorized", "empty", "none", "bar_caption", "as_of",
    "law_count", "law_sampling", "law_window", "law_net", "law_cats",
    "law_nulls", "law_peak", "law_change", "law_benchmark", "law_bar",
    "law_scope", "law_notadvice",
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
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.bar{position:relative;height:10px;min-width:160px;max-width:420px;
border:1px solid var(--line);border-radius:999px;background:#f2f4f7}
.bar i{position:absolute;top:-3px;width:3px;height:16px;background:#3c4653}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_CVMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_CVMB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_world():
    """The shipped monthly velocity face over a throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="cvmb-")
    db = os.path.join(tmp_root, "cvmb.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        envelope = dict(getattr(am, FACE)())
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for row in envelope.get("months") or []:
        missing = [key for key in ROW_KEYS if key not in row]
        if missing:
            raise FaceError("row keys missing on %r: %s"
                            % (row.get("month"), ",".join(missing)))
        for cell in row.get("categories") or []:
            missing = [key for key in CELL_KEYS if key not in cell]
            if missing:
                raise FaceError("cell keys missing on %r: %s"
                                % (cell.get("category"), ",".join(missing)))
    return envelope


def _next_month(label):
    year, month = int(label[:4]), int(label[5:7])
    month += 1
    if month > 12:
        month = 1
        year += 1
    return "%04d-%02d" % (year, month)


def check_laws(envelope):
    """AC-CVMB3 read at the source: refuse rather than print."""
    problems = []
    months = envelope.get("months") or []
    if int(envelope.get("month_count", -1)) != len(months):
        problems.append("month_count %s != %d rows"
                        % (envelope.get("month_count"), len(months)))
    if months:
        if envelope.get("first_month") != months[0]["month"]:
            problems.append("first_month does not match the first row")
        if envelope.get("last_month") != months[-1]["month"]:
            problems.append("last_month does not match the last row")
    previous = None
    total_sales = 0
    sum_row_listings = 0
    max_row_listings = 0
    categories = set()
    for row in months:
        tag = "month %s" % row["month"]
        if previous is not None and _next_month(previous) != row["month"]:
            problems.append("%s is not the month after %s" % (tag, previous))
        previous = row["month"]
        cells = row.get("categories") or []
        if int(row["category_count"]) != len(cells):
            problems.append("%s category_count %s != %d cells"
                            % (tag, row["category_count"], len(cells)))
        named = [cell["category"] for cell in cells
                 if cell["category"] is not None]
        if named != sorted(named):
            problems.append("%s categories not ascending" % tag)
        if any(cell["category"] is None for cell in cells) \
                and cells and cells[-1]["category"] is not None:
            problems.append("%s uncategorized bucket not last" % tag)
        if sum(int(cell["sale_count"]) for cell in cells) \
                != int(row["sale_count"]):
            problems.append("%s sale_count %s != sum of cells"
                            % (tag, row["sale_count"]))
        if sum(int(cell["listing_count"]) for cell in cells) \
                != int(row["listing_count"]):
            problems.append("%s listing_count %s != sum of cells"
                            % (tag, row["listing_count"]))
        for cell in cells:
            count = int(cell["sale_count"])
            if count == 0 and (cell["avg_seconds"] is not None
                               or cell["median_seconds"] is not None):
                problems.append("%s empty cell carries an aggregate" % tag)
            if count > 0 and cell["median_seconds"] is None:
                problems.append("%s cell counts sales without a median" % tag)
        count = int(row["sale_count"])
        if count == 0:
            if any(row[key] is not None for key in
                   ("avg_seconds", "median_seconds", "fastest_seconds",
                    "slowest_seconds")):
                problems.append("%s zero month carries an aggregate" % tag)
            if row["fastest_listing_id"] is not None \
                    or row["slowest_listing_id"] is not None:
                problems.append("%s zero month carries a listing id" % tag)
        else:
            trio = (row["fastest_seconds"], row["median_seconds"],
                    row["slowest_seconds"])
            if None in trio or not trio[0] <= trio[1] <= trio[2]:
                problems.append("%s fastest/median/slowest not ordered %r"
                                % (tag, trio))
            if row["fastest_listing_id"] is None \
                    or row["slowest_listing_id"] is None:
                problems.append("%s sale without a listing id" % tag)
        if row["market_avg_seconds"] != envelope.get("market_avg_seconds"):
            problems.append("%s market benchmark %r != envelope %r"
                            % (tag, row["market_avg_seconds"],
                               envelope.get("market_avg_seconds")))
        total_sales += count
        sum_row_listings += int(row["listing_count"])
        max_row_listings = max(max_row_listings, int(row["listing_count"]))
        for cell in cells:
            categories.add(cell["category"])
    if total_sales != int(envelope.get("sale_count", -1)):
        problems.append("envelope sale_count %s != %d summed"
                        % (envelope.get("sale_count"), total_sales))
    listings = int(envelope.get("listing_count", -1))
    if months and not (max_row_listings <= listings <= sum_row_listings):
        problems.append("envelope listing_count %d outside [%d,%d]"
                        % (listings, max_row_listings, sum_row_listings))
    expected = len([c for c in categories if c is not None]) \
        + (1 if None in categories else 0)
    if int(envelope.get("category_count", -1)) != expected:
        problems.append("envelope category_count %s != %d distinct"
                        % (envelope.get("category_count"), expected))
    if months:
        best = max(int(row["sale_count"]) for row in months)
        first = [row["month"] for row in months
                 if int(row["sale_count"]) == best][0]
        if int(envelope.get("peak_sale_count", -1)) != best:
            problems.append("peak_sale_count %s != %d"
                            % (envelope.get("peak_sale_count"), best))
        if envelope.get("peak_month") != first:
            problems.append("peak_month %r != earliest max month %r"
                            % (envelope.get("peak_month"), first))
    if len(months) >= 2:
        expected_change = (int(months[-1]["sale_count"])
                           - int(months[-2]["sale_count"]))
        if envelope.get("month_over_month_change") != expected_change:
            problems.append("month_over_month_change %r != %d"
                            % (envelope.get("month_over_month_change"),
                               expected_change))
    elif envelope.get("month_over_month_change") is not None:
        problems.append("month_over_month_change set without two months")
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


def bar_html(row, none_text):
    fastest, median, slowest = (row["fastest_seconds"],
                                row["median_seconds"],
                                row["slowest_seconds"])
    if None in (fastest, median, slowest) or float(slowest) <= float(fastest):
        return none_text
    pos = (float(median) - float(fastest)) \
        / (float(slowest) - float(fastest)) * 100.0
    pos = max(0.0, min(100.0, pos))
    return '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos


def kpi_html(row, labels, e, dash):
    items = [
        (labels["kpi_row_sales"], text(row["sale_count"], dash)),
        (labels["kpi_row_listings"], text(row["listing_count"], dash)),
        (labels["kpi_row_cats"], text(row["category_count"], dash)),
        (labels["kpi_row_avg"], text(row["avg_seconds"], dash)),
        (labels["kpi_row_median"], text(row["median_seconds"], dash)),
        (labels["kpi_row_fastest"],
         "%s / #%s" % (text(row["fastest_seconds"], dash),
                       text(row["fastest_listing_id"], dash))),
        (labels["kpi_row_slowest"],
         "%s / #%s" % (text(row["slowest_seconds"], dash),
                       text(row["slowest_listing_id"], dash))),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(str(value))) for name, value in items)


def cells_table(row, labels, e, dash):
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_category"] else "",
                      e(name))
                   for name in (labels["col_category"], labels["col_sales"],
                                labels["col_listings"], labels["col_avg"],
                                labels["col_median"]))
    body = []
    for cell in row.get("categories") or []:
        name = cell["category"]
        if name is None:
            label = ('<span class="badge">%s</span>'
                     % e(labels["badge_uncategorized"]))
            key = ""
        else:
            label = e(str(name))
            key = e(str(name))
        body.append(
            '<tr data-category="%s"><td>%s</td>'
            '<td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>'
            % (key, label, e(text(cell["sale_count"], dash)),
               e(text(cell["listing_count"], dash)),
               e(text(cell["avg_seconds"], dash)),
               e(text(cell["median_seconds"], dash))))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def month_section(row, labels, e, dash):
    return (
        '<div class=card data-month="%s">\n'
        "<h3>%s &middot; %s %s</h3>\n"
        "<div class=kpi>%s</div>\n"
        '<p class=cap>%s</p><div class=bar-slot>%s</div>\n'
        "%s\n</div>\n"
        % (e(str(row["month"])), e(str(row["month"])),
           e(labels["as_of"]), e(text(row["as_of"], dash)),
           kpi_html(row, labels, e, dash), e(labels["bar_caption"]),
           bar_html(row, e(dash)), cells_table(row, labels, e, dash))
    )


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    months = envelope.get("months") or []
    laws = [labels["law_count"], labels["law_sampling"],
            labels["law_window"], labels["law_net"], labels["law_cats"],
            labels["law_nulls"], labels["law_peak"], labels["law_change"],
            labels["law_benchmark"], labels["law_bar"], labels["law_scope"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    head_kpi = "".join(
        "<div><span>%s</span><b>%s</b></div>" % (e(labels[key]), e(value))
        for key, value in (
            ("kpi_months", text(envelope.get("month_count"), dash)),
            ("kpi_first", text(envelope.get("first_month"), dash)),
            ("kpi_last", text(envelope.get("last_month"), dash)),
            ("kpi_sales", text(envelope.get("sale_count"), dash)),
            ("kpi_listings", text(envelope.get("listing_count"), dash)),
            ("kpi_categories", text(envelope.get("category_count"), dash)),
            ("kpi_peak", text(envelope.get("peak_month"), dash)),
            ("kpi_peak_sales", text(envelope.get("peak_sale_count"), dash)),
            ("kpi_change",
             text(envelope.get("month_over_month_change"), dash)),
            ("kpi_mkt_avg", text(envelope.get("market_avg_seconds"), dash)),
            ("kpi_mkt_median",
             text(envelope.get("market_median_seconds"), dash)),
        ))
    if months:
        sections = "".join(month_section(row, labels, e, dash)
                           for row in months)
    else:
        sections = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card data-market="1"><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), head_kpi,
           e(labels["sec_months"]), sections,
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
        print("CATEGORY-VELOCITY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelope)
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

    payload = {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "month_count": envelope["month_count"],
        "first_month": envelope["first_month"],
        "last_month": envelope["last_month"],
        "sale_count": envelope["sale_count"],
        "listing_count": envelope["listing_count"],
        "category_count": envelope["category_count"],
        "peak_month": envelope["peak_month"],
        "peak_sale_count": envelope["peak_sale_count"],
        "month_over_month_change": envelope["month_over_month_change"],
        "market_avg_seconds": envelope["market_avg_seconds"],
        "market_median_seconds": envelope["market_median_seconds"],
        "months": [{key: row[key] for key in ROW_KEYS}
                   for row in envelope.get("months") or []],
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

    print("CATEGORY-VELOCITY %s bytes=%d months=%d sales=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["month_count"], payload["sale_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
