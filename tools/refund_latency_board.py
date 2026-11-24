#!/usr/bin/env python3
"""Render the market refund latency reading into one page a human can open.

Why this exists: api_refund_latency answers "how long did the money take to
come back" with its own AC-RFLT1..8 criteria and a six-band partition, five
aggregates over refunded rows only, two named crossings and a contiguous
monthly leg - but no page under tools/ or preview/ ever called it. The refund
family already has four money answers (propensity, register, exposure,
category_refund_months); the time axis had no door, so a slow settlement, a
backlogged after-sales desk and a healthy refund read identically from outside.

Nothing here re-implements a market rule. Every number comes from the shipped
api_refund_latency() face read over a fresh throwaway demo world seeded through
the shipped report helpers. The page prints what the face hands it and never
recomputes a total; the only checks it runs are the face's own published laws,
and a broken law refuses the render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/refund_latency_board.py
  python tools/refund_latency_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-RFLB1..AC-RFLB6 are pre-registered in src/os/backlog.md (R3440 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/refund-latency-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "refund-latency-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "refund-latency-board.json")
COPY = os.path.join(ROOT, "preview", "refund-latency-board-copy.json")

FACE = "api_refund_latency"

PAYLOAD_KEYS = (
    "generated_utc", "face", "scope", "band_count", "month_count", "envelope",
    "bands", "months", "disclaimer", "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "purchase_count", "refund_count", "unrefunded_count", "refund_rate",
    "avg_refund_seconds", "median_refund_seconds", "p90_refund_seconds",
    "fastest_seconds", "slowest_seconds", "same_day_count", "over_week_count",
    "month_count", "bands", "months", "disclaimer",
)

BAND_KEYS = ("band", "lower_seconds", "upper_seconds", "refund_count",
             "refunded")
MONTH_KEYS = ("month", "refund_count", "median_refund_seconds",
              "avg_refund_seconds", "slowest_seconds")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_kpi", "sec_bands",
    "sec_months", "sec_law", "sec_disc", "sec_rep",
    "kpi_purchases", "kpi_refunds", "kpi_unrefunded", "kpi_rate",
    "kpi_avg", "kpi_median", "kpi_p90", "kpi_fastest", "kpi_slowest",
    "kpi_sameday", "kpi_week", "kpi_months",
    "col_band", "col_lower", "col_upper", "col_count", "col_refunded",
    "col_bar", "col_month", "col_median", "col_avg", "col_slowest",
    "bar_caption", "none", "empty", "band_all",
    "law_derive", "law_bands", "law_null", "law_median", "law_order",
    "law_months", "law_crossings", "law_bar", "law_scope", "law_notadvice",
    "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1120px;margin:0 auto}
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
.kpi div{flex:1 1 112px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:18px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:110px}
.bar i{display:block;height:9px;border-radius:999px;background:#5b7fa8}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
caption{caption-side:top;text-align:left;color:var(--muted);font-size:12px;
padding-bottom:6px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_RFLB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_RFLB_LAW"


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
    tmp_root = tempfile.mkdtemp(prefix="refund-latency-board-")
    db = os.path.join(tmp_root, "refund-latency-board.db")
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
    missing = [key for key in ENVELOPE_KEYS if key not in envelope]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    for row in envelope["bands"]:
        missing = [key for key in BAND_KEYS if key not in row]
        if missing:
            raise FaceError("band keys missing: %s" % ",".join(missing))
    for row in envelope["months"]:
        missing = [key for key in MONTH_KEYS if key not in row]
        if missing:
            raise FaceError("month keys missing: %s" % ",".join(missing))
    return envelope


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def check_laws(envelope):
    """AC-RFLB3 read at the source: refuse rather than print."""
    problems = []
    purchases = int(envelope["purchase_count"])
    refunds = int(envelope["refund_count"])
    unrefunded = int(envelope["unrefunded_count"])
    if refunds != purchases - unrefunded:
        problems.append("refund_count != purchases - unrefunded")
    want_rate = round(float(refunds) / purchases, 4) if purchases else None
    if not _close(envelope["refund_rate"], want_rate):
        problems.append("refund_rate %r != %r"
                        % (envelope["refund_rate"], want_rate))
    bands = envelope["bands"]
    if sum(int(row["refund_count"]) for row in bands) != refunds:
        problems.append("band counts do not sum to refund_count")
    if bands:
        if int(bands[0]["lower_seconds"]) != 0:
            problems.append("first band does not start at zero")
        if bands[-1]["upper_seconds"] is not None:
            problems.append("last band has an upper bound")
        for prev, cur in zip(bands, bands[1:]):
            if prev["upper_seconds"] != cur["lower_seconds"]:
                problems.append("bands %r and %r do not meet"
                                % (prev["band"], cur["band"]))
        for row in bands:
            if row["upper_seconds"] is not None and \
                    int(row["upper_seconds"]) <= int(row["lower_seconds"]):
                problems.append("band %r is not a half-open interval"
                                % row["band"])
            if int(row["refunded"]) < 0:
                problems.append("band %r refunded is negative" % row["band"])
    months = envelope["months"]
    if int(envelope["month_count"]) != len(months):
        problems.append("month_count != months")
    if sum(int(row["refund_count"]) for row in months) != refunds:
        problems.append("month counts do not sum to refund_count")
    for prev, cur in zip(months, months[1:]):
        if _month_index(cur["month"]) != _month_index(prev["month"]) + 1:
            problems.append("months %r and %r are not contiguous"
                            % (prev["month"], cur["month"]))
    for row in months:
        stats = (row["median_refund_seconds"], row["avg_refund_seconds"],
                 row["slowest_seconds"])
        if int(row["refund_count"]) == 0:
            if any(value is not None for value in stats):
                problems.append("empty month %r carries statistics"
                                % row["month"])
        elif any(value is None for value in stats):
            problems.append("month %r is missing a statistic" % row["month"])
        else:
            if float(row["median_refund_seconds"]) > \
                    float(row["slowest_seconds"]):
                problems.append("month %r median exceeds slowest"
                                % row["month"])
    chain = [envelope["fastest_seconds"], envelope["median_refund_seconds"],
             envelope["p90_refund_seconds"], envelope["slowest_seconds"]]
    if refunds == 0:
        if any(value is not None for value in chain):
            problems.append("aggregates with no refund")
    else:
        if any(value is None for value in chain):
            problems.append("aggregate missing with refunds")
        elif not (float(chain[0]) <= float(chain[1]) <= float(chain[2]) <=
                  float(chain[3])):
            problems.append("fastest/median/p90/slowest out of order")
    for key in ("same_day_count", "over_week_count"):
        if int(envelope[key]) > refunds or int(envelope[key]) < 0:
            problems.append("%s outside 0..refund_count" % key)
    return problems


def _month_index(text):
    year, month = str(text).split("-")
    return int(year) * 12 + int(month)


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_purchases"], fmt(envelope["purchase_count"], dash)),
        (labels["kpi_refunds"], fmt(envelope["refund_count"], dash)),
        (labels["kpi_unrefunded"], fmt(envelope["unrefunded_count"], dash)),
        (labels["kpi_rate"], fmt(envelope["refund_rate"], dash)),
        (labels["kpi_avg"], fmt(envelope["avg_refund_seconds"], dash)),
        (labels["kpi_median"], fmt(envelope["median_refund_seconds"], dash)),
        (labels["kpi_p90"], fmt(envelope["p90_refund_seconds"], dash)),
        (labels["kpi_fastest"], fmt(envelope["fastest_seconds"], dash)),
        (labels["kpi_slowest"], fmt(envelope["slowest_seconds"], dash)),
        (labels["kpi_sameday"], fmt(envelope["same_day_count"], dash)),
        (labels["kpi_week"], fmt(envelope["over_week_count"], dash)),
        (labels["kpi_months"], fmt(envelope["month_count"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def bands_table(envelope, labels, e, dash):
    head = (labels["col_band"], labels["col_lower"], labels["col_upper"],
            labels["col_count"], labels["col_refunded"], labels["col_bar"])
    peak = max([int(row["refund_count"]) for row in envelope["bands"]] or [0])
    body = []
    for row in envelope["bands"]:
        count = int(row["refund_count"])
        if not peak:
            bar = '<span class=empty>%s</span>' % e(dash)
        else:
            width = max(0.0, min(100.0, float(count) / peak * 100.0))
            bar = '<div class=bar><i style="width:%.1f%%"></i></div>' % width
        cells = [
            ("", row["band"]),
            ("n", fmt(row["lower_seconds"], dash)),
            ("n", fmt(row["upper_seconds"], dash)
             if row["upper_seconds"] is not None else labels["band_all"]),
            ("n", fmt(count, dash)),
            ("n", fmt(row["refunded"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr data-band="%s">%s</tr>' % (e(str(row["band"])), tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty"])
    head_html = "".join('<th class=n>%s</th>' % e(cell)
                        if cell != labels["col_band"] and cell != labels["col_bar"]
                        else "<th>%s</th>" % e(cell) for cell in head)
    return ('<table><caption>%s</caption><tr>%s</tr>%s</table>'
            % (e(labels["bar_caption"]), head_html, "".join(body)))


def months_table(envelope, labels, e, dash):
    head = (labels["col_month"], labels["col_count"], labels["col_median"],
            labels["col_avg"], labels["col_slowest"], labels["col_bar"])
    peak = max([value for value in
                [row["median_refund_seconds"] for row in envelope["months"]]
                if value is not None] or [0])
    body = []
    for row in envelope["months"]:
        median = row["median_refund_seconds"]
        if median is None or not peak:
            bar = '<span class=empty>%s</span>' % e(dash)
        else:
            width = max(0.0, min(100.0, float(median) / float(peak) * 100.0))
            bar = '<div class=bar><i style="width:%.1f%%"></i></div>' % width
        cells = [
            ("", row["month"]),
            ("n", fmt(row["refund_count"], dash)),
            ("n", fmt(median, dash)),
            ("n", fmt(row["avg_refund_seconds"], dash)),
            ("n", fmt(row["slowest_seconds"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr data-month="%s">%s</tr>'
                    % (e(str(row["month"])), tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty"])
    head_html = "".join('<th class=n>%s</th>' % e(cell)
                        if cell not in (labels["col_month"], labels["col_bar"])
                        else "<th>%s</th>" % e(cell) for cell in head)
    return ('<table><caption>%s</caption><tr>%s</tr>%s</table>'
            % (e(labels["bar_caption"]), head_html, "".join(body)))


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_derive"], labels["law_bands"], labels["law_null"],
            labels["law_median"], labels["law_order"], labels["law_months"],
            labels["law_crossings"], labels["law_bar"], labels["law_scope"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    empty_sentence = ""
    if not int(envelope.get("refund_count") or 0):
        empty_sentence = '<p class=empty>%s</p>' % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card><div class=kpi>%s</div>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_kpi"]),
           kpi_html(envelope, labels, e, dash), empty_sentence,
           e(labels["sec_bands"]), bands_table(envelope, labels, e, dash),
           e(labels["sec_months"]), months_table(envelope, labels, e, dash),
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
        print("REFUND-LATENCY CHECK %s fails=%d html=%dB json=%dB"
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
    doc = build_html(envelope, labels, now, envelope["disclaimer"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "scope": "market",
        "band_count": len(envelope["bands"]),
        "month_count": len(envelope["months"]),
        "envelope": {key: envelope[key] for key in ENVELOPE_KEYS},
        "bands": [{key: row[key] for key in BAND_KEYS}
                  for row in envelope["bands"]],
        "months": [{key: row[key] for key in MONTH_KEYS}
                   for row in envelope["months"]],
        "disclaimer": envelope["disclaimer"],
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

    print("REFUND-LATENCY %s bytes=%d purchases=%d refunds=%d bands=%d "
          "months=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["envelope"]["purchase_count"],
             payload["envelope"]["refund_count"], payload["band_count"],
             payload["month_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
