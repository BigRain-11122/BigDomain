#!/usr/bin/env python3
"""Render the per-category monthly asking-price band into one page.

Why this exists: api_category_price_months answers "what did each category's
asking price look like at the end of every UTC month - the band, the quartiles,
the median, and how far the median moved" with its own AC-CPM criteria, but a
search over tools/, preview/ and src/os answered rc=1 with zero hits. The
market already had two snapshot price faces (one distribution, one min/max
bucket band) and a time axis that only answered turnover, so nobody could see
on one page that a category's median moved from month to month.

Nothing here re-implements a market rule. Every number comes from the shipped
face read over a fresh throwaway demo world seeded through the shipped report
helpers. The page prints what the face hands it; the only thing it computes is
the width of each bar, and the page says out loud that the bar marks where the
median sits inside that month's band and is not a share. A broken identity
refuses the render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/category_price_months_board.py
  python tools/category_price_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-CPMB1..AC-CPMB6 are pre-registered in src/os/backlog.md (R3439 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/category-price-months-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "category-price-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-price-months-board.json")
COPY = os.path.join(ROOT, "preview", "category-price-months-board-copy.json")

FACE = "api_category_price_months"

# Pinned payload keys (AC-CPMB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "month_count", "first_month",
    "last_month", "listing_count", "category_count", "months", "disclaimer",
    "report", "sources", "sizes",
)

# The shipped 12-key month row and 5-key category cell.
ROW_KEYS = (
    "month", "as_of", "live_listing_count", "category_count", "min_price",
    "max_price", "p25_price", "p50_price", "p75_price", "mean_price",
    "p50_change", "categories",
)
CELL_KEYS = ("category", "live_listing_count", "min_price", "max_price",
             "p50_price")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_months", "sec_law", "sec_disc", "sec_rep",
    "kpi_months", "kpi_first", "kpi_last", "kpi_listings", "kpi_categories",
    "kpi_live", "kpi_cats", "kpi_min", "kpi_max", "kpi_p25", "kpi_p50",
    "kpi_p75", "kpi_mean", "kpi_change",
    "col_category", "col_live", "col_min", "col_max", "col_p50", "col_bar",
    "badge_uncategorized", "empty", "none", "bar_caption", "as_of",
    "law_count", "law_sampling", "law_window", "law_median", "law_order",
    "law_change", "law_bar", "law_scope", "law_notadvice", "rep", "cmd",
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
.bar{position:relative;height:10px;min-width:120px;border:1px solid var(--line);
border-radius:999px;background:#f2f4f7}
.bar i{position:absolute;top:-3px;width:3px;height:16px;background:#3c4653}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.cap{color:var(--muted);font-size:12px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_CPMB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_CPMB_LAW"


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
    """The shipped monthly band over a throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="cpmb-")
    db = os.path.join(tmp_root, "cpmb.db")
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


def check_laws(envelope):
    """AC-CPMB3 read at the source: refuse rather than print."""
    problems = []
    months = envelope.get("months") or []
    months_seen = [row["month"] for row in months]
    if months_seen != sorted(months_seen):
        problems.append("months not ascending")
    if months and envelope.get("first_month") != months[0]["month"]:
        problems.append("first_month does not match the first row")
    if months and envelope.get("last_month") != months[-1]["month"]:
        problems.append("last_month does not match the last row")
    if int(envelope.get("month_count", -1)) != len(months):
        problems.append("month_count %s != %d rows"
                        % (envelope.get("month_count"), len(months)))
    previous_median = None
    for row in months:
        tag = "month %s" % row["month"]
        cells = row.get("categories") or []
        if int(row["category_count"]) != len(cells):
            problems.append("%s category_count %s != %d cells"
                            % (tag, row["category_count"], len(cells)))
        named = [cell["category"] for cell in cells if cell["category"] is not None]
        if named != sorted(named):
            problems.append("%s categories not ascending" % tag)
        if any(cell["category"] is None for cell in cells) \
                and cells and cells[-1]["category"] is not None:
            problems.append("%s uncategorized bucket not last" % tag)
        live = sum(int(cell["live_listing_count"]) for cell in cells)
        if live != int(row["live_listing_count"]):
            problems.append("%s live %s != sum of cells %d"
                            % (tag, row["live_listing_count"], live))
        prices = [int(cell["min_price"]) for cell in cells]
        tops = [int(cell["max_price"]) for cell in cells]
        if prices and row["min_price"] != min(prices):
            problems.append("%s min_price %r != cell minimum %d"
                            % (tag, row["min_price"], min(prices)))
        if tops and row["max_price"] != max(tops):
            problems.append("%s max_price %r != cell maximum %d"
                            % (tag, row["max_price"], max(tops)))
        trio = (row["p25_price"], row["p50_price"], row["p75_price"])
        if None not in trio and not (trio[0] <= trio[1] <= trio[2]):
            problems.append("%s quartiles not ordered %r" % (tag, trio))
        median = row["p50_price"]
        if median is None and previous_median is not None:
            pass
        change = row["p50_change"]
        if change is None:
            pass
        elif median is None or previous_median is None:
            problems.append("%s change %r without both medians" % (tag, change))
        elif float(change) != float(median) - float(previous_median):
            problems.append("%s change %r != %r-%r"
                            % (tag, change, median, previous_median))
        if median is not None:
            previous_median = median
        else:
            previous_median = None
    return problems


def text(value, none_text):
    return none_text if value is None else str(value)


def bar_html(row, none_text):
    low, high = row["min_price"], row["max_price"]
    median = row["p50_price"]
    if None in (low, high, median) or int(high) <= int(low):
        return none_text
    pos = (float(median) - float(low)) / (float(high) - float(low)) * 100.0
    pos = max(0.0, min(100.0, pos))
    return '<div class="bar"><i style="left:%.1f%%"></i></div>' % pos


def kpi_html(row, labels, e, dash):
    items = [
        (labels["kpi_live"], row["live_listing_count"]),
        (labels["kpi_cats"], row["category_count"]),
        (labels["kpi_min"], text(row["min_price"], dash)),
        (labels["kpi_p25"], text(row["p25_price"], dash)),
        (labels["kpi_p50"], text(row["p50_price"], dash)),
        (labels["kpi_p75"], text(row["p75_price"], dash)),
        (labels["kpi_max"], text(row["max_price"], dash)),
        (labels["kpi_mean"], text(row["mean_price"], dash)),
        (labels["kpi_change"], text(row["p50_change"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(name)), e(str(value))) for name, value in items)


def cells_table(row, labels, e, dash):
    head = "".join("<th%s>%s</th>"
                   % (' class="n"' if name != labels["col_category"] else "",
                      e(name))
                   for name in (labels["col_category"], labels["col_live"],
                                labels["col_min"], labels["col_max"],
                                labels["col_p50"], labels["col_bar"]))
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
            '<td class="n">%s</td><td class="n">%s</td><td>%s</td></tr>'
            % (key, label, e(str(cell["live_listing_count"])),
               e(text(cell["min_price"], dash)),
               e(text(cell["max_price"], dash)),
               e(text(cell["p50_price"], dash)),
               bar_html(cell, dash)))
    return "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
        head, "".join(body))


def month_section(row, labels, e, dash):
    return (
        '<div class=card data-month="%s">\n'
        "<h3>%s &middot; %s %s</h3>\n"
        "<div class=kpi>%s</div>\n"
        "%s\n</div>\n"
        % (e(str(row["month"])), e(str(row["month"])),
           e(labels["as_of"]), e(text(row["as_of"], dash)),
           kpi_html(row, labels, e, dash), cells_table(row, labels, e, dash))
    )


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    months = envelope.get("months") or []
    laws = [labels["law_count"], labels["law_sampling"],
            labels["law_window"], labels["law_median"], labels["law_order"],
            labels["law_change"], labels["law_bar"], labels["law_scope"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    head_kpi = "".join(
        "<div><span>%s</span><b>%s</b></div>" % (e(labels[key]), e(value))
        for key, value in (
            ("kpi_months", text(envelope.get("month_count"), dash)),
            ("kpi_first", text(envelope.get("first_month"), dash)),
            ("kpi_last", text(envelope.get("last_month"), dash)),
            ("kpi_listings", text(envelope.get("listing_count"), dash)),
            ("kpi_categories", text(envelope.get("category_count"), dash)),
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
        '<div class=card data-market="1"><div class=kpi>%s</div>\n'
        "<p class=cap>%s</p></div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; %s</footer>\n"
        "</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), head_kpi,
           e(labels["bar_caption"]), e(labels["sec_months"]), sections,
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
        print("CATEGORY-PRICE-MONTHS CHECK %s fails=%d html=%dB json=%dB"
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
        "listing_count": envelope["listing_count"],
        "category_count": envelope["category_count"],
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

    print("CATEGORY-PRICE-MONTHS %s bytes=%d months=%d listings=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["month_count"], payload["listing_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
