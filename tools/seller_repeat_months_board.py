#!/usr/bin/env python3
"""Render the seller monthly returning-buyer reading on one page a human opens.

Why this exists: api_seller_repeat_months answers "was this month carried by
regulars or by newcomers" with its own AC-SRB1..8 criteria, but a git grep
over tools/ and preview/ answered rc=1 with zero hits, so the reading could
only be had by calling the sandbox from a shell. api_repeat_purchase answers
the lifetime question only and api_market_buyer_cohort reads new versus
returning at MARKET scope, so one seller's month axis had no page. Measured in
R3429: usr:dana carries one month (2026-09) with two purchases, two buyers,
zero returning buyers and a 0.0 repeat rate; usr:frank is an honest empty
envelope.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_repeat_months() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_repeat_months_board.py
  python tools/seller_repeat_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-RPTB1..AC-RPTB6 are pre-registered in src/os/backlog.md (R3429 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-repeat-months-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-repeat-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-repeat-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-repeat-months-board-copy.json")

FACE = "api_seller_repeat_months"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-RPTB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 18 keys.
ENVELOPE_KEYS = (
    "scope", "dev_account", "buyer_count", "repeat_buyer_count",
    "repeat_rate", "purchase_count", "gross", "new_gross",
    "returning_gross", "month_count", "active_month_count", "first_month",
    "last_month", "peak_month", "peak_returning_buyer_count",
    "latest_month_returning_share", "disclaimer", "months",
)

# One month row, 11 keys.
ROW_KEYS = (
    "month", "purchase_count", "gross", "buyer_count", "new_buyer_count",
    "returning_buyer_count", "returning_share", "new_purchase_count",
    "returning_purchase_count", "new_gross", "returning_gross",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_sellers", "sec_law",
    "sec_disc", "sec_rep",
    "kpi_months", "kpi_active", "kpi_buyers", "kpi_repeat", "kpi_rate",
    "kpi_purchases", "kpi_gross", "kpi_new_gross", "kpi_returning_gross",
    "kpi_peak", "kpi_peak_count", "kpi_latest",
    "col_month", "col_purchases", "col_gross", "col_buyers",
    "col_new_buyers", "col_returning_buyers", "col_share",
    "col_new_purchases", "col_returning_purchases", "col_new_gross",
    "col_returning_gross", "col_bar",
    "badge_peak", "badge_new", "badge_quiet", "empty_scope", "none",
    "label_single", "label_zero",
    "law_count", "law_grid", "law_sum", "law_share", "law_newmonth",
    "law_peak", "law_scope", "law_bar", "law_zero", "law_notadvice",
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
.zero-dot{display:inline-block;width:7px;height:7px;margin-right:5px;
border-radius:999px;background:#9aa6b2;vertical-align:middle}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.peak{border-color:#9fb8c3;color:#3f6473}
.badge.new{border-color:#b7c6a9;color:#4b6338}
.badge.quiet{border-color:#d8dde3;color:#7b848e}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
.note{color:var(--muted);font-size:12.5px;margin:6px 0 0}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_RPTB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_RPTB_LAW"


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
    """Read one scoped envelope per seller from the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="seller-repeat-months-board-")
    db = os.path.join(tmp_root, "seller-repeat-months-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        sellers = [dict(getattr(am, FACE)(seller))
                   for seller in enumerate_sellers(board)]
        disclaimer = sellers[0]["disclaimer"] if sellers else None
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    for envelope in sellers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("dev_account"), ",".join(missing)))
        for row in envelope["months"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("month"), ",".join(missing)))
    return sellers, disclaimer


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _want_share(returning, buyers):
    if not buyers:
        return None
    return float(returning) / float(buyers)


def _next_month(month):
    year, mon = int(month[:4]), int(month[5:7])
    if mon == 12:
        return "%04d-01" % (year + 1)
    return "%04d-%02d" % (year, mon + 1)


def _envelope_problems(envelope, label):
    """AC-RPTB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["months"]
    if int(envelope["month_count"]) != len(rows):
        problems.append("%s month_count %r != months %d"
                        % (label, envelope["month_count"], len(rows)))
    active = sum(1 for row in rows if int(row["purchase_count"]) > 0)
    if int(envelope["active_month_count"]) != active:
        problems.append("%s active_month_count %r != %d"
                        % (label, envelope["active_month_count"], active))
    sums = {
        "purchase_count": sum(int(row["purchase_count"]) for row in rows),
        "gross": sum(int(row["gross"]) for row in rows),
        "new_gross": sum(int(row["new_gross"]) for row in rows),
        "buyer_count": sum(int(row["new_buyer_count"]) for row in rows),
    }
    for key, want in sums.items():
        if int(envelope[key]) != want:
            problems.append("%s %s %r != row sum %d"
                            % (label, key, envelope[key], want))
    if int(envelope["returning_gross"]) != (int(envelope["gross"])
                                           - int(envelope["new_gross"])):
        problems.append("%s returning_gross != gross - new_gross" % label)
    if not _close(envelope["repeat_rate"],
                  _want_share(int(envelope["repeat_buyer_count"]),
                              int(envelope["buyer_count"]))):
        problems.append("%s repeat_rate %r != %r"
                        % (label, envelope["repeat_rate"],
                           _want_share(int(envelope["repeat_buyer_count"]),
                                       int(envelope["buyer_count"]))))
    want_latest = rows[-1]["returning_share"] if rows else None
    if not _close(envelope["latest_month_returning_share"], want_latest):
        problems.append("%s latest_month_returning_share %r != %r"
                        % (label, envelope["latest_month_returning_share"],
                           want_latest))
    want_first = rows[0]["month"] if rows else None
    want_last = rows[-1]["month"] if rows else None
    if envelope["first_month"] != want_first:
        problems.append("%s first_month %r != %r"
                        % (label, envelope["first_month"], want_first))
    if envelope["last_month"] != want_last:
        problems.append("%s last_month %r != %r"
                        % (label, envelope["last_month"], want_last))
    peak_month = None
    peak_count = None
    for row in rows:
        value = int(row["returning_buyer_count"])
        if value > 0 and (peak_count is None or value > peak_count):
            peak_month = row["month"]
            peak_count = value
    if envelope["peak_month"] != peak_month:
        problems.append("%s peak_month %r != %r"
                        % (label, envelope["peak_month"], peak_month))
    if envelope["peak_returning_buyer_count"] != peak_count:
        problems.append("%s peak_returning_buyer_count %r != %r"
                        % (label, envelope["peak_returning_buyer_count"],
                           peak_count))
    previous = None
    for row in rows:
        month = str(row["month"])
        if len(month) != 7 or month[4] != "-":
            problems.append("%s month %r is not YYYY-MM" % (label, month))
        elif previous is not None and _next_month(previous) != month:
            problems.append("%s month %r is not contiguous after %r"
                            % (label, month, previous))
        previous = month
        buyers = int(row["buyer_count"])
        if int(row["new_buyer_count"]) + int(row["returning_buyer_count"]) \
                != buyers:
            problems.append("%s %s buyer halves != buyer_count"
                            % (label, month))
        if int(row["new_purchase_count"]) + int(
                row["returning_purchase_count"]) != int(row["purchase_count"]):
            problems.append("%s %s purchase halves != purchase_count"
                            % (label, month))
        if int(row["new_gross"]) + int(row["returning_gross"]) != int(
                row["gross"]):
            problems.append("%s %s gross halves != gross" % (label, month))
        if not _close(row["returning_share"],
                      _want_share(int(row["returning_buyer_count"]), buyers)):
            problems.append("%s %s returning_share %r != %r"
                            % (label, month, row["returning_share"],
                               _want_share(int(row["returning_buyer_count"]),
                                           buyers)))
        if int(row["returning_buyer_count"]) > buyers:
            problems.append("%s %s returning > buyers" % (label, month))
    return problems


def check_laws(sellers):
    problems = []
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s is not a seller account" % name)
        if block["scope"] != "seller":
            problems.append("%s scope %r != seller" % (name, block["scope"]))
    if sellers and sellers[0]["disclaimer"] != sellers[-1]["disclaimer"]:
        problems.append("sellers disagree on the disclaimer")
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def pct(value, none_text):
    if value is None:
        return none_text
    return "%.1f%%" % (float(value) * 100.0)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_months"], fmt(envelope["month_count"], dash)),
        (labels["kpi_active"], fmt(envelope["active_month_count"], dash)),
        (labels["kpi_buyers"], fmt(envelope["buyer_count"], dash)),
        (labels["kpi_repeat"], fmt(envelope["repeat_buyer_count"], dash)),
        (labels["kpi_rate"], pct(envelope["repeat_rate"], dash)),
        (labels["kpi_purchases"], fmt(envelope["purchase_count"], dash)),
        (labels["kpi_gross"], fmt(envelope["gross"], dash)),
        (labels["kpi_new_gross"], fmt(envelope["new_gross"], dash)),
        (labels["kpi_returning_gross"],
         fmt(envelope["returning_gross"], dash)),
        (labels["kpi_peak"], fmt(envelope["peak_month"], dash)),
        (labels["kpi_peak_count"],
         fmt(envelope["peak_returning_buyer_count"], dash)),
        (labels["kpi_latest"],
         pct(envelope["latest_month_returning_share"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def months_table(envelope, labels, e, dash):
    head = (labels["col_month"], labels["col_purchases"], labels["col_gross"],
            labels["col_buyers"], labels["col_new_buyers"],
            labels["col_returning_buyers"], labels["col_share"],
            labels["col_new_purchases"], labels["col_returning_purchases"],
            labels["col_new_gross"], labels["col_returning_gross"],
            labels["col_bar"])
    head_html = "".join('<th class=n>%s</th>' % e(cell)
                        if cell != labels["col_month"]
                        else "<th>%s</th>" % e(cell) for cell in head)
    peak = max([int(row["returning_buyer_count"])
                for row in envelope["months"]] or [0])
    body = []
    for row in envelope["months"]:
        share = row["returning_share"]
        purchases = int(row["purchase_count"])
        badges = ""
        if str(row["month"]) == str(envelope["peak_month"]):
            badges += '<span class="badge peak">%s</span>' % e(
                labels["badge_peak"])
        if not purchases:
            badges += '<span class="badge quiet">%s</span>' % e(
                labels["badge_quiet"])
            bar = '<span class=empty>%s</span>' % e(dash)
        elif share is None:
            bar = '<span class=empty>%s</span>' % e(dash)
        elif float(share) <= 0.0:
            badges += '<span class="badge new">%s</span>' % e(
                labels["badge_new"])
            bar = ('<span class=zero-dot></span>'
                   '<span class=empty>%s</span>' % e(labels["label_zero"]))
        else:
            width = float(share) / peak * 100.0 if peak else 0.0
            width = max(0.0, min(100.0, width))
            bar = '<div class=bar><i style="width:%.1f%%"></i></div>' % width
        cells = (
            fmt(row["purchase_count"], dash), fmt(row["gross"], dash),
            fmt(row["buyer_count"], dash), fmt(row["new_buyer_count"], dash),
            fmt(row["returning_buyer_count"], dash), pct(share, dash),
            fmt(row["new_purchase_count"], dash),
            fmt(row["returning_purchase_count"], dash),
            fmt(row["new_gross"], dash), fmt(row["returning_gross"], dash),
        )
        tds = "".join('<td class=n>%s</td>' % e(str(value))
                      for value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr class="%s" data-month="%s"><td>%s%s</td>%s</tr>'
                    % ("active" if purchases else "quiet",
                       e(str(row["month"])), e(str(row["month"])), badges,
                       tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    note = ('<p class=note>%s</p>' % e(labels["label_single"])
            if len(envelope["months"]) <= 1 else "")
    return "<table><tr>%s</tr>%s</table>%s" % (head_html, "".join(body), note)


def seller_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash),
               months_table(block, labels, e, dash)))


def build_html(sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_grid"], labels["law_sum"],
            labels["law_share"], labels["law_newmonth"], labels["law_peak"],
            labels["law_scope"], labels["law_bar"], labels["law_zero"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])),
           seller_section(block, labels, e, dash))
        for block in sellers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_sellers"]),
           sections or ('<div class=card data-seller-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_scope"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer or ""))


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
    """AC-PWC74 (R3596): landing this pair and re-deriving the CEO face are ONE run.

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
        print("SELLER-REPEAT-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        sellers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(sellers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "seller",
        "seller_count": len(sellers),
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

    face = _refresh_face(args.out, args.json)

    print("SELLER-REPEAT-MONTHS %s bytes=%d sellers=%d months=%d "
          "repeat_buyers=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"],
             sum(int(b["month_count"]) for b in sellers),
             sum(int(b["repeat_buyer_count"]) for b in sellers), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
