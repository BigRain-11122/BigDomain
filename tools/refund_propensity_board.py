#!/usr/bin/env python3
"""Render the per-buyer refund propensity reading (with its market baseline)
into one page a human can open.

Why this exists: api_buyer_refund_propensity answers "how heavy is my refund
behaviour, normalised by how much I actually bought, and how does it compare
with the market" with its own AC-RFP1..8 criteria, but git grep over tools/
and preview/ found no reader at all, so the reading could only be had by
calling the sandbox from a shell. A raw refund_count is not comparable across
residents; a rate with no baseline is not comparable either.

Nothing here re-implements a market rule. Every number comes from the shipped
api_buyer_refund_propensity() face read over a fresh throwaway demo world
seeded through the shipped report helpers. Buyers are enumerated through the
shipped board, sales and ratings faces instead of being typed by hand. The
page prints what the face hands it and never recomputes a total; the only
checks it runs are the face's own published laws, and a broken law refuses the
render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/refund_propensity_board.py
  python tools/refund_propensity_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BRFPB1..AC-BRFPB6 are pre-registered in src/os/backlog.md (R3419 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/refund-propensity-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "refund-propensity-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "refund-propensity-board.json")
COPY = os.path.join(ROOT, "preview", "refund-propensity-board-copy.json")

FACE = "api_buyer_refund_propensity"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_sales"
RATINGS_FACE = "api_ratings"

# Pinned payload keys (AC-BRFPB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "market", "smoothing_strength", "disclaimer", "report",
    "sources", "sizes",
)

BUYER_KEYS = (
    "buyer_id", "purchase_count", "refund_count",
    "non_refunded_purchase_count", "gross_spent", "refunded_tokens",
    "net_spent", "refund_rate", "refund_amount_rate", "market_purchase_count",
    "market_refund_count", "market_refund_rate", "refund_rate_delta",
    "smoothing_strength", "smoothed_refund_rate", "disclaimer",
)

MARKET_KEYS = ("purchase_count", "refund_count", "refund_rate")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_buyers", "sec_market", "sec_extremes",
    "sec_law", "sec_disc", "sec_rep", "col_buyer", "col_purchases",
    "col_refunds", "col_nonrefund", "col_gross", "col_refunded", "col_net",
    "col_rate", "col_amount_rate", "col_delta", "col_smoothed", "col_bar",
    "kpi_buyers", "kpi_market_purchases", "kpi_market_refunds",
    "kpi_market_rate", "kpi_smoothing", "none", "dir_above", "dir_below",
    "extremes_above", "extremes_below", "extremes_none", "law_bound",
    "law_nonrefund", "law_net", "law_rate", "law_market", "law_delta",
    "law_smooth", "law_bar", "law_notadvice", "rep", "cmd",
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
td.neg{color:#b42318}
tr.above td.delta{color:#b42318}
tr.below td.delta{color:#067647}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:120px}
.bar i{display:block;height:9px;border-radius:999px;background:#7b8fa8}
.bar u{position:absolute;top:-3px;width:2px;height:15px;background:#c9a227}
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


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_RFPB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_RFPB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_buyers(am, board):
    """Buyer ids through the shipped sales and ratings faces, never typed."""
    seen = set()
    devs = sorted(set(str(row["dev_account"]) for row in board["listings"]))
    for dev in devs:
        sales = getattr(am, SOURCE_FACE)(dev)
        for row in sales.get("sales") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    for listing in board["listings"]:
        rated = getattr(am, RATINGS_FACE)(listing["listing_id"])
        for row in rated.get("ratings") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    return sorted(seen)


def read_world():
    """Read one propensity block per buyer the shipped faces enumerate."""
    tmp_root = tempfile.mkdtemp(prefix="refund-propensity-board-")
    db = os.path.join(tmp_root, "refund-propensity-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        buyers = [dict(getattr(am, FACE)(buyer))
                  for buyer in enumerate_buyers(am, board)]
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
    if not buyers:
        raise FaceError("no buyer enumerated through the shipped faces")
    for block in buyers:
        missing = [key for key in BUYER_KEYS if key not in block]
        if missing:
            raise FaceError("buyer keys missing on %r: %s"
                            % (block.get("buyer_id"), ",".join(missing)))
    market = {"purchase_count": int(buyers[0]["market_purchase_count"]),
              "refund_count": int(buyers[0]["market_refund_count"]),
              "refund_rate": buyers[0]["market_refund_rate"]}
    return buyers, market, int(buyers[0]["smoothing_strength"]), disclaimer


def check_laws(blocks, market, strength):
    """AC-BRFPB3 read at the source: refuse rather than print."""
    problems = []
    if strength <= 0:
        problems.append("smoothing strength %r is not positive" % (strength,))
    market_rate = market["refund_rate"]
    if market["purchase_count"]:
        want = float(market["refund_count"]) / market["purchase_count"]
        if market_rate is None or abs(float(market_rate) - want) > 1e-9:
            problems.append("market rate %r != %d/%d"
                            % (market_rate, market["refund_count"],
                               market["purchase_count"]))
    elif market_rate is not None:
        problems.append("market rate %r on an empty market" % (market_rate,))
    for block in blocks:
        name = str(block["buyer_id"])
        purchases = int(block["purchase_count"])
        refunds = int(block["refund_count"])
        gross = int(block["gross_spent"])
        refunded = int(block["refunded_tokens"])
        if refunds > purchases:
            problems.append("%s refunds %d > purchases %d"
                            % (name, refunds, purchases))
        if int(block["non_refunded_purchase_count"]) != purchases - refunds:
            problems.append("%s non_refunded=%s"
                            % (name, block["non_refunded_purchase_count"]))
        if int(block["net_spent"]) != gross - refunded:
            problems.append("%s net_spent=%s expected=%d"
                            % (name, block["net_spent"], gross - refunded))
        if int(block["market_purchase_count"]) != market["purchase_count"]:
            problems.append("%s market_purchase_count=%s world=%d"
                            % (name, block["market_purchase_count"],
                               market["purchase_count"]))
        if int(block["market_refund_count"]) != market["refund_count"]:
            problems.append("%s market_refund_count=%s world=%d"
                            % (name, block["market_refund_count"],
                               market["refund_count"]))
        if int(block["smoothing_strength"]) != strength:
            problems.append("%s smoothing_strength=%s world=%d"
                            % (name, block["smoothing_strength"], strength))
        rate = block["refund_rate"]
        if purchases:
            want = float(refunds) / purchases
            if rate is None or abs(float(rate) - want) > 1e-9:
                problems.append("%s refund_rate %r != %d/%d"
                                % (name, rate, refunds, purchases))
        elif rate is not None:
            problems.append("%s refund_rate %r on zero purchases"
                            % (name, rate))
        amount_rate = block["refund_amount_rate"]
        if gross:
            want = float(refunded) / gross
            if amount_rate is None or abs(float(amount_rate) - want) > 1e-9:
                problems.append("%s refund_amount_rate %r != %d/%d"
                                % (name, amount_rate, refunded, gross))
        elif amount_rate is not None:
            problems.append("%s refund_amount_rate %r on zero gross"
                            % (name, amount_rate))
        delta = block["refund_rate_delta"]
        if rate is None or market_rate is None:
            if delta is not None:
                problems.append("%s delta %r with a missing side" % (name,
                                                                     delta))
        elif delta is None or abs(float(delta) - (float(rate)
                                                 - float(market_rate))) > 1e-9:
            problems.append("%s delta %r expected=%r"
                            % (name, delta, float(rate) - float(market_rate)))
        smoothed = block["smoothed_refund_rate"]
        if purchases and market_rate is not None:
            want = ((refunds + strength * float(market_rate))
                    / (purchases + strength))
            if smoothed is None or abs(float(smoothed) - want) > 1e-9:
                problems.append("%s smoothed %r expected %r"
                                % (name, smoothed, want))
        elif smoothed is not None:
            problems.append("%s smoothed %r with a missing denominator"
                            % (name, smoothed))
    return problems


def pct(value):
    """Percent text for a 0..1 rate; the single dash for an absent side."""
    if value is None:
        return None
    return "%.1f%%" % (float(value) * 100.0)


def pp(value):
    """Percentage points, signed, for a rate difference."""
    if value is None:
        return None
    return "%+.1fpp" % (float(value) * 100.0)


def bar_share(value, peak):
    if value is None or not peak:
        return 0.0
    return max(0.0, min(100.0, float(value) / float(peak) * 100.0))


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def extremes(blocks):
    graded = [block for block in blocks
              if block["refund_rate_delta"] is not None]
    if not graded:
        return None, None
    high = max(graded, key=lambda b: float(b["refund_rate_delta"]))
    low = min(graded, key=lambda b: float(b["refund_rate_delta"]))
    return high, low


def kpi_html(blocks, market, strength, labels, e):
    items = [
        (labels["kpi_buyers"], fmt(len(blocks), labels["none"])),
        (labels["kpi_market_purchases"],
         fmt(market["purchase_count"], labels["none"])),
        (labels["kpi_market_refunds"],
         fmt(market["refund_count"], labels["none"])),
        (labels["kpi_market_rate"],
         fmt(pct(market["refund_rate"]), labels["none"])),
        (labels["kpi_smoothing"], fmt(strength, labels["none"])),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def build_html(blocks, market, strength, labels, now, disclaimer):
    e = html.escape
    peak = max([float(b["refund_rate"]) for b in blocks
                if b["refund_rate"] is not None] or [0.0])
    market_width = bar_share(market["refund_rate"], peak)

    head = (labels["col_buyer"], labels["col_purchases"],
            labels["col_refunds"], labels["col_nonrefund"], labels["col_gross"],
            labels["col_refunded"], labels["col_net"], labels["col_rate"],
            labels["col_amount_rate"], labels["col_delta"],
            labels["col_smoothed"], labels["col_bar"])
    right = {labels["col_purchases"], labels["col_refunds"],
             labels["col_nonrefund"], labels["col_gross"],
             labels["col_refunded"], labels["col_net"], labels["col_rate"],
             labels["col_amount_rate"], labels["col_delta"],
             labels["col_smoothed"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)

    body = []
    for block in blocks:
        delta = block["refund_rate_delta"]
        row_class = (" above" if delta is not None and delta > 0
                     else " below" if delta is not None and delta < 0 else "")
        delta_text = fmt(pp(delta), labels["none"])
        if delta is not None and delta > 0:
            delta_text = "%s %s" % (delta_text, labels["dir_above"])
        elif delta is not None and delta < 0:
            delta_text = "%s %s" % (delta_text, labels["dir_below"])
        width = bar_share(block["refund_rate"], peak)
        bar = ('<div class=bar><i style="width:%.1f%%"></i>'
               '<u style="left:%.1f%%"></u></div>'
               % (width, market_width))
        plain = [
            ("", block["buyer_id"]),
            ("n", fmt(block["purchase_count"], labels["none"])),
            ("n", fmt(block["refund_count"], labels["none"])),
            ("n", fmt(block["non_refunded_purchase_count"], labels["none"])),
            ("n", fmt(block["gross_spent"], labels["none"])),
            ("n", fmt(block["refunded_tokens"], labels["none"])),
            ("n", fmt(block["net_spent"], labels["none"])),
            ("n", fmt(pct(block["refund_rate"]), labels["none"])),
            ("n", fmt(pct(block["refund_amount_rate"]), labels["none"])),
            ("n delta", delta_text),
            ("n", fmt(pct(block["smoothed_refund_rate"]), labels["none"])),
        ]
        tds = []
        for klass, value in plain:
            neg = " neg" if str(value).startswith("-") else ""
            tds.append('<td class="%s%s">%s</td>'
                       % (klass, neg, e(str(value))))
        tds.append("<td class=bar-cell>%s</td>" % bar)
        body.append('<tr class="buyer%s" data-buyer="%s">%s</tr>'
                    % (row_class, e(str(block["buyer_id"])), "".join(tds)))
    table = "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))

    high, low = extremes(blocks)
    if high is None:
        extremes_html = '<p class=empty>%s</p>' % e(labels["extremes_none"])
    else:
        def line(title, block):
            return ('<p class=law>%s: <b>%s</b> &middot; %s &middot; %s</p>'
                    % (e(title), e(str(block["buyer_id"])),
                       e(fmt(pct(block["refund_rate"]), labels["none"])),
                       e(fmt(pp(block["refund_rate_delta"]),
                             labels["none"]))))
        extremes_html = (line(labels["extremes_above"], high)
                         + line(labels["extremes_below"], low))

    market_html = (
        '<p class=law>%s: <b>%s</b></p>'
        '<p class=law>%s: <b>%s</b> / <b>%s</b> = <b>%s</b></p>'
        '<p class=law>%s: <b>%s</b></p>'
        % (e(labels["kpi_market_purchases"]),
           e(fmt(market["purchase_count"], labels["none"])),
           e(labels["kpi_market_refunds"]),
           e(fmt(market["refund_count"], labels["none"])),
           e(fmt(market["purchase_count"], labels["none"])),
           e(fmt(pct(market["refund_rate"]), labels["none"])),
           e(labels["kpi_smoothing"]), e(fmt(strength, labels["none"]))))

    laws = [labels["law_bound"], labels["law_nonrefund"], labels["law_net"],
            labels["law_rate"], labels["law_market"], labels["law_delta"],
            labels["law_smooth"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/refund_propensity_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_buyers"]),
           kpi_html(blocks, market, strength, labels, e), table,
           e(labels["sec_market"]), market_html,
           e(labels["sec_extremes"]), extremes_html,
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]), e(now))
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
    """AC-PWC66 (R3588): landing this pair and re-deriving the CEO face are ONE run.

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
        print("REFUND-PROPENSITY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        blocks, market, strength, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(blocks, market, strength)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(blocks, market, strength, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "source_face": SOURCE_FACE,
        "buyer_count": len(blocks),
        "buyers": blocks,
        "market": market,
        "smoothing_strength": strength,
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
    print("REFUND-PROPENSITY %s bytes=%d buyers=%d market_rate=%s face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"], pct(market["refund_rate"]), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
