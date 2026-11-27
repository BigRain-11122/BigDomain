#!/usr/bin/env python3
"""Render the seller-side monthly refund reading into one page a human can open.

Why this exists: api_seller_refund_months answers "how much money came back
this month, who paid it, and is my refund pressure heavier than the market"
with its own AC-SRFM1..AC-SRFM8 criteria, but git grep over tools/ and
preview/ found no reader at all, so the reading could only be had by calling
the sandbox from a shell. A seller could not tell a quiet month from a month
whose refunds ate the whole gross without it.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_refund_months() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_refund_months_board.py
  python tools/seller_refund_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SRFMB1..AC-SRFMB6 are pre-registered in src/os/backlog.md (R3421 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-refund-months-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-refund-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-refund-months-board.json")
COPY = os.path.join(ROOT, "preview", "seller-refund-months-board-copy.json")

FACE = "api_seller_refund_months"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_seller_refund_months"

# Pinned payload keys (AC-SRFMB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped seller envelope, 27 keys (AC-SRFMB1).
SELLER_KEYS = (
    "dev_account", "scope", "month_count", "active_month_count",
    "refund_count", "refunded", "gross", "net", "refund_rate",
    "dev_refunded", "platform_refunded", "listing_count", "buyer_count",
    "seller_count", "avg_refund_amount", "same_month_count",
    "largest_refund", "peak_month", "peak_refund_count", "first_month",
    "last_month", "latest_month_refund_count", "latest_month_refunded",
    "latest_month_refund_rate", "market_refund_rate", "disclaimer", "months",
)

# The shipped month row, 14 keys (AC-SRFMB1).
MONTH_KEYS = (
    "month", "refund_count", "refunded", "gross", "net", "refund_rate",
    "dev_refunded", "platform_refunded", "listing_count", "buyer_count",
    "seller_count", "avg_refund_amount", "same_month_count",
    "running_refund_count",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_sellers", "sec_law", "sec_disc",
    "sec_rep", "kpi_months", "kpi_active", "kpi_refunds", "kpi_refunded",
    "kpi_dev", "kpi_platform", "kpi_avg", "kpi_same_month", "kpi_largest",
    "kpi_peak", "kpi_net", "kpi_market", "col_month", "col_refunds",
    "col_refunded", "col_dev", "col_platform", "col_gross", "col_net",
    "col_rate", "col_avg", "col_buyers", "col_listings", "col_running",
    "col_bar", "none", "yes", "no", "law_net", "law_legs", "law_rate",
    "law_zero", "law_running", "law_sums", "law_peak", "law_scope",
    "law_bar", "law_notadvice", "rep", "cmd",
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
tr.refund-only td.state{color:#b42318}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:110px}
.bar i{display:block;height:9px;border-radius:999px;background:#a8766f}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.seller-head{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.seller-head b{font-size:16px}
.empty{color:#b42318}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_SRFM_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_SRFM_LAW"


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
    """Read one scoped envelope per seller plus the market lifetime rate."""
    tmp_root = tempfile.mkdtemp(prefix="seller-refund-months-board-")
    db = os.path.join(tmp_root, "seller-refund-months-board.db")
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
    if not sellers:
        raise FaceError("no seller on the board face")
    for block in sellers:
        missing = [key for key in SELLER_KEYS if key not in block]
        if missing:
            raise FaceError("seller keys missing on %r: %s"
                            % (block.get("dev_account"), ",".join(missing)))
        for row in block["months"]:
            missing = [key for key in MONTH_KEYS if key not in row]
            if missing:
                raise FaceError("month keys missing on %r/%r: %s"
                                % (block.get("dev_account"),
                                   row.get("month"), ",".join(missing)))
    return market, sellers, disclaimer


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _next_month(month):
    year, mon = str(month).split("-")
    year = int(year)
    mon = int(mon) + 1
    if mon > 12:
        year += 1
        mon = 1
    return "%04d-%02d" % (year, mon)


def check_laws(market, sellers):
    """AC-SRFMB3 read at the source: refuse rather than print."""
    problems = []
    market_rate = market["refund_rate"]
    for block in sellers:
        name = str(block["dev_account"])
        months = block["months"]
        if block["scope"] != "seller":
            problems.append("%s scope %r" % (name, block["scope"]))
        if int(block["month_count"]) != len(months):
            problems.append("%s month_count %s != months %d"
                            % (name, block["month_count"], len(months)))
        active = sum(1 for row in months
                     if int(row["refund_count"]) > 0 or int(row["gross"]) > 0)
        if int(block["active_month_count"]) != active:
            problems.append("%s active_month_count %s != %d"
                            % (name, block["active_month_count"], active))
        if not _close(block["market_refund_rate"], market_rate):
            problems.append("%s market_refund_rate %r != market %r"
                            % (name, block["market_refund_rate"],
                               market_rate))
        running = 0
        previous = None
        totals = {"refund_count": 0, "refunded": 0, "gross": 0,
                  "dev_refunded": 0, "platform_refunded": 0,
                  "same_month_count": 0}
        for row in months:
            tag = "%s/%s" % (name, row["month"])
            if previous is not None and row["month"] != _next_month(previous):
                problems.append("%s month grid is not contiguous" % tag)
            previous = row["month"]
            if int(row["net"]) != int(row["gross"]) - int(row["refunded"]):
                problems.append("%s net %s != gross-refunded" % (tag, row["net"]))
            if int(row["refunded"]) != (int(row["dev_refunded"])
                                       + int(row["platform_refunded"])):
                problems.append("%s refunded != dev+platform" % tag)
            count = int(row["refund_count"])
            want_avg = None
            if count:
                want_avg = round(float(row["refunded"]) / count, 2)
            if not _close(row["avg_refund_amount"], want_avg):
                problems.append("%s avg_refund_amount %r != %r"
                                % (tag, row["avg_refund_amount"], want_avg))
            want_rate = None
            if int(row["gross"]) > 0:
                want_rate = round(float(row["refunded"]) / int(row["gross"]), 2)
            if not _close(row["refund_rate"], want_rate):
                problems.append("%s refund_rate %r != %r"
                                % (tag, row["refund_rate"], want_rate))
            running += count
            if int(row["running_refund_count"]) != running:
                problems.append("%s running_refund_count %s != %d"
                                % (tag, row["running_refund_count"], running))
            if int(row["same_month_count"]) > count:
                problems.append("%s same_month_count %s > refund_count %d"
                                % (tag, row["same_month_count"], count))
            for key in totals:
                totals[key] += int(row[key])
        for key in sorted(totals):
            if int(block[key]) != totals[key]:
                problems.append("%s %s %s != month sum %d"
                                % (name, key, block[key], totals[key]))
        if int(block["net"]) != int(block["gross"]) - int(block["refunded"]):
            problems.append("%s net %s != gross-refunded" % (name, block["net"]))
        want_rate = None
        if int(block["gross"]) > 0:
            want_rate = round(float(block["refunded"]) / int(block["gross"]), 2)
        if not _close(block["refund_rate"], want_rate):
            problems.append("%s refund_rate %r != %r"
                            % (name, block["refund_rate"], want_rate))
        want_avg = None
        if int(block["refund_count"]):
            want_avg = round(float(block["refunded"])
                             / int(block["refund_count"]), 2)
        if not _close(block["avg_refund_amount"], want_avg):
            problems.append("%s avg_refund_amount %r != %r"
                            % (name, block["avg_refund_amount"], want_avg))
        if months:
            if block["first_month"] != months[0]["month"]:
                problems.append("%s first_month" % name)
            if block["last_month"] != months[-1]["month"]:
                problems.append("%s last_month" % name)
            if not _close(block["latest_month_refund_count"],
                          months[-1]["refund_count"]):
                problems.append("%s latest_month_refund_count" % name)
            if not _close(block["latest_month_refunded"],
                          months[-1]["refunded"]):
                problems.append("%s latest_month_refunded" % name)
            if not _close(block["latest_month_refund_rate"],
                          months[-1]["refund_rate"]):
                problems.append("%s latest_month_refund_rate" % name)
        if int(block["refund_count"]) == 0:
            for key in ("largest_refund", "peak_month", "peak_refund_count"):
                if block[key] is not None:
                    problems.append("%s %s %r with zero refunds"
                                    % (name, key, block[key]))
        else:
            if block["largest_refund"] is None:
                problems.append("%s largest_refund missing" % name)
            elif int(block["largest_refund"]) > int(block["refunded"]):
                problems.append("%s largest_refund %s > refunded"
                                % (name, block["largest_refund"]))
            peaks = [int(row["refund_count"]) for row in months
                     if int(row["refund_count"]) > 0]
            if block["peak_month"] is None or block["peak_refund_count"] is None:
                problems.append("%s peak missing" % name)
            else:
                if int(block["peak_refund_count"]) != max(peaks):
                    problems.append("%s peak_refund_count %s != %d"
                                    % (name, block["peak_refund_count"],
                                       max(peaks)))
                hit = [row for row in months
                       if row["month"] == block["peak_month"]]
                if not hit:
                    problems.append("%s peak_month %r not a month row"
                                    % (name, block["peak_month"]))
                elif int(hit[0]["refund_count"]) != int(block["peak_refund_count"]):
                    problems.append("%s peak_month %r count mismatch"
                                    % (name, block["peak_month"]))
    return problems


def bar_share(value, peak):
    if value is None or not peak:
        return 0.0
    return max(0.0, min(100.0, float(value) / float(peak) * 100.0))


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def money(value, none_text):
    """Signed integer money, the minus sign kept for a negative net."""
    if value is None:
        return none_text
    return "%d" % int(value)


def rate(value, none_text):
    if value is None:
        return none_text
    return "%.2f" % float(value)


def kpi_html(block, labels, e, dash):
    items = [
        (labels["kpi_months"], fmt(block["month_count"], dash)),
        (labels["kpi_active"], fmt(block["active_month_count"], dash)),
        (labels["kpi_refunds"], fmt(block["refund_count"], dash)),
        (labels["kpi_refunded"], money(block["refunded"], dash)),
        (labels["kpi_dev"], money(block["dev_refunded"], dash)),
        (labels["kpi_platform"], money(block["platform_refunded"], dash)),
        (labels["kpi_avg"], rate(block["avg_refund_amount"], dash)),
        (labels["kpi_same_month"], fmt(block["same_month_count"], dash)),
        (labels["kpi_largest"], money(block["largest_refund"], dash)),
        (labels["kpi_peak"], fmt(block["peak_month"], dash)),
        (labels["kpi_net"], money(block["net"], dash)),
        (labels["kpi_market"], rate(block["market_refund_rate"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def months_table(block, labels, e, dash):
    head = (labels["col_month"], labels["col_refunds"],
            labels["col_refunded"], labels["col_dev"],
            labels["col_platform"], labels["col_gross"], labels["col_net"],
            labels["col_rate"], labels["col_avg"], labels["col_buyers"],
            labels["col_listings"], labels["col_running"],
            labels["col_bar"])
    right = set(head[1:12])
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    peak = max([int(row["refunded"]) for row in block["months"]] or [0])
    body = []
    for row in block["months"]:
        klass = "refund-only" if int(row["gross"]) == 0 \
            and int(row["refund_count"]) > 0 else ""
        cells = [
            ("", str(row["month"])),
            ("n", fmt(row["refund_count"], dash)),
            ("n", money(row["refunded"], dash)),
            ("n", money(row["dev_refunded"], dash)),
            ("n", money(row["platform_refunded"], dash)),
            ("n", money(row["gross"], dash)),
            ("n", money(row["net"], dash)),
            ("n", rate(row["refund_rate"], dash)),
            ("n", rate(row["avg_refund_amount"], dash)),
            ("n", fmt(row["buyer_count"], dash)),
            ("n", fmt(row["listing_count"], dash)),
            ("n", fmt(row["running_refund_count"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (cell_class, e(str(value)))
                      for cell_class, value in cells)
        tds += ('<td class=bar-cell><div class=bar><i style="width:%.1f%%">'
                '</i></div></td>' % bar_share(row["refunded"], peak))
        body.append('<tr class="%s" data-month="%s">%s</tr>'
                    % (klass, e(str(row["month"])), tds))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def build_html(sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_net"], labels["law_legs"], labels["law_rate"],
            labels["law_zero"], labels["law_running"], labels["law_sums"],
            labels["law_peak"], labels["law_scope"], labels["law_bar"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = []
    for block in sellers:
        sections.append(
            '<h2 data-seller="%s"><span class=seller-head><b>%s</b>'
            '<span>%s</span></span></h2>\n'
            "<div class=card><div class=kpi>%s</div>%s</div>\n"
            % (e(str(block["dev_account"])), e(str(block["dev_account"])),
               e(labels["sec_sellers"]),
               kpi_html(block, labels, e, dash),
               months_table(block, labels, e, dash)))
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "%s"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/seller_refund_months_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), "".join(sections),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(now))
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
    """AC-PWC73 (R3595): landing this pair and re-deriving the CEO face are ONE run.

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
        print("SELLER-REFUND-MONTHS CHECK %s fails=%d html=%dB json=%dB"
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
    doc = build_html(sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "source_face": SOURCE_FACE,
        "scope": "seller",
        "seller_count": len(sellers),
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

    print("SELLER-REFUND-MONTHS %s bytes=%d sellers=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(sellers), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
