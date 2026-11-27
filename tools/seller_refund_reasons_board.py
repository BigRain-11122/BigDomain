#!/usr/bin/env python3
"""Render the seller-side refund cause reading into one page a human can open.

Why this exists: api_seller_refund_reasons answers "what are my refunds
actually caused by, and how heavy is that against the market" with its own
AC-SRR1..8 criteria, but a git grep over tools/ and preview/ answered rc=1
with zero hits, so the reading could only be had by calling the sandbox from a
shell. The market-wide reason board (R3407) and the seller monthly board
(R3421) answer other questions; neither tells one seller which cause is
carrying the load and how its refund rate and refunded share sit against the
market benchmark the face already ships.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_refund_reasons() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_refund_reasons_board.py
  python tools/seller_refund_reasons_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SRRB1..AC-SRRB6 are pre-registered in src/os/backlog.md (R3424 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-refund-reasons-board-copy.json and appear in the rendered
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-refund-reasons-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-refund-reasons-board.json")
COPY = os.path.join(ROOT, "preview", "seller-refund-reasons-board-copy.json")

FACE = "api_seller_refund_reasons"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_seller_refund_reasons"

# Pinned payload keys (AC-SRRB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "market", "sellers", "disclaimer", "report", "sources",
    "sizes",
)

# The shipped envelope, 17 keys, identical on both scopes.
ENVELOPE_KEYS = (
    "scope", "dev_account", "purchase_count", "refund_count", "refund_rate",
    "refunded_total", "labeled_count", "unlabeled_count", "reason_count",
    "top_reason", "top_reason_count", "top_reason_share",
    "reason_herfindahl", "market_refund_rate", "market_refund_share",
    "rows", "disclaimer",
)

ROW_KEYS = (
    "reason", "refund_count", "refunded", "dev_share", "platform_share",
    "share", "avg_amount", "listing_count",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_market", "sec_sellers",
    "sec_law", "sec_disc", "sec_rep",
    "kpi_purchases", "kpi_refunds", "kpi_rate", "kpi_refunded",
    "kpi_reasons", "kpi_labeled", "kpi_unlabeled", "kpi_top", "kpi_hhi",
    "kpi_market_rate", "kpi_market_share",
    "col_reason", "col_count", "col_refunded", "col_dev", "col_platform",
    "col_share", "col_avg", "col_listings", "col_bar",
    "unlabeled", "top_none", "none",
    "law_legs", "law_share", "law_avg", "law_rate", "law_count", "law_top",
    "law_hhi", "law_order", "law_scope", "law_bar", "law_notadvice",
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
.bar i{display:block;height:9px;border-radius:999px;background:#a8677b}
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

    code = "E_SRRB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_SRRB_LAW"


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
    tmp_root = tempfile.mkdtemp(prefix="seller-refund-reasons-board-")
    db = os.path.join(tmp_root, "seller-refund-reasons-board.db")
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
        for row in envelope["rows"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("reason"), ",".join(missing)))
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    return market, sellers, disclaimer


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _want_herfindahl(rows, refund_count):
    if not refund_count:
        return None
    total = 0.0
    for row in rows:
        total += (float(row["refund_count"]) / refund_count) ** 2
    return round(total * 10000, 2)


def _envelope_problems(envelope, label):
    """AC-SRRB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["rows"]
    count = int(envelope["refund_count"])
    if count != sum(int(row["refund_count"]) for row in rows):
        problems.append("%s refund_count != sum of rows" % label)
    if int(envelope["refunded_total"]) != sum(
            int(row["refunded"]) for row in rows):
        problems.append("%s refunded_total != sum of rows" % label)
    if int(envelope["labeled_count"]) + int(envelope["unlabeled_count"]) != count:
        problems.append("%s labeled+unlabeled != refund_count" % label)
    if int(envelope["reason_count"]) != len(rows):
        problems.append("%s reason_count != rows" % label)
    purchases = int(envelope["purchase_count"])
    want_rate = (round(float(count) / purchases, 4) if purchases else None)
    if not _close(envelope["refund_rate"], want_rate):
        problems.append("%s refund_rate %r != %r"
                        % (label, envelope["refund_rate"], want_rate))
    if not _close(envelope["reason_herfindahl"],
                  _want_herfindahl(rows, count)):
        problems.append("%s reason_herfindahl %r"
                        % (label, envelope["reason_herfindahl"]))

    for row in rows:
        tag = "%s/%s" % (label, row["reason"])
        if int(row["dev_share"]) + int(row["platform_share"]) != int(
                row["refunded"]):
            problems.append("%s legs != refunded" % tag)
        want_share = (round(float(row["refund_count"]) / count, 4)
                      if count else None)
        if not _close(row["share"], want_share):
            problems.append("%s share %r != %r"
                            % (tag, row["share"], want_share))
        want_avg = (round(float(row["refunded"]) / int(row["refund_count"]), 2)
                    if int(row["refund_count"]) else None)
        if not _close(row["avg_amount"], want_avg):
            problems.append("%s avg %r != %r"
                            % (tag, row["avg_amount"], want_avg))

    labeled = [row for row in rows if row["reason"] is not None]
    labeled_count = sum(int(row["refund_count"]) for row in labeled)
    if labeled:
        best = sorted(labeled, key=lambda row: (
            -int(row["refund_count"]), -int(row["refunded"]),
            row["reason"]))[0]
        if envelope["top_reason"] != best["reason"]:
            problems.append("%s top_reason %r != %r"
                            % (label, envelope["top_reason"], best["reason"]))
        if int(envelope["top_reason_count"] or -1) != int(
                best["refund_count"]):
            problems.append("%s top_reason_count" % label)
        want_top_share = (round(float(best["refund_count"]) / labeled_count, 4)
                          if labeled_count else None)
        if not _close(envelope["top_reason_share"], want_top_share):
            problems.append("%s top_reason_share %r != %r"
                            % (label, envelope["top_reason_share"],
                               want_top_share))
    else:
        for key in ("top_reason", "top_reason_count", "top_reason_share"):
            if envelope[key] is not None:
                problems.append("%s %s %r with no labeled bucket"
                                % (label, key, envelope[key]))

    def order(row):
        return (1 if row["reason"] is None else 0,
                -int(row["refund_count"]), -int(row["refunded"]),
                row["reason"] or "")
    if [order(row) for row in rows] != sorted(order(row) for row in rows):
        problems.append("%s rows are not in the face's own order" % label)
    return problems


def check_laws(market, sellers):
    problems = _envelope_problems(market, "market")
    if market["scope"] != "market" or market["dev_account"] is not None:
        problems.append("market envelope is not the market scope")
    for key in ("market_refund_rate", "market_refund_share"):
        if market[key] is not None:
            problems.append("market %s must be None" % key)
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if block["scope"] != "seller":
            problems.append("%s scope is not seller" % name)
        if not _close(block["market_refund_rate"], market["refund_rate"]):
            problems.append("%s market_refund_rate %r != market %r"
                            % (name, block["market_refund_rate"],
                               market["refund_rate"]))
        want_share = (round(float(block["refunded_total"])
                            / float(market["refunded_total"]), 4)
                      if int(market["refunded_total"]) else None)
        if not _close(block["market_refund_share"], want_share):
            problems.append("%s market_refund_share %r != %r"
                            % (name, block["market_refund_share"], want_share))
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def reason_text(reason, labels):
    if reason is None:
        return labels["unlabeled"]
    return str(reason)


def top_text(envelope, labels):
    if envelope["top_reason"] is None:
        return labels["top_none"]
    share = envelope["top_reason_share"]
    if share is None:
        return str(envelope["top_reason"])
    return "%s (%s)" % (envelope["top_reason"], fmt(share, labels["none"]))


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_purchases"], fmt(envelope["purchase_count"], dash)),
        (labels["kpi_refunds"], fmt(envelope["refund_count"], dash)),
        (labels["kpi_rate"], fmt(envelope["refund_rate"], dash)),
        (labels["kpi_refunded"], fmt(envelope["refunded_total"], dash)),
        (labels["kpi_reasons"], fmt(envelope["reason_count"], dash)),
        (labels["kpi_labeled"], fmt(envelope["labeled_count"], dash)),
        (labels["kpi_unlabeled"], fmt(envelope["unlabeled_count"], dash)),
        (labels["kpi_top"], top_text(envelope, labels)),
        (labels["kpi_hhi"], fmt(envelope["reason_herfindahl"], dash)),
    ]
    if envelope["scope"] == "seller":
        items.append((labels["kpi_market_rate"],
                      fmt(envelope["market_refund_rate"], dash)))
        items.append((labels["kpi_market_share"],
                      fmt(envelope["market_refund_share"], dash)))
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def rows_table(envelope, labels, e, dash):
    head = (labels["col_reason"], labels["col_count"], labels["col_refunded"],
            labels["col_dev"], labels["col_platform"], labels["col_share"],
            labels["col_avg"], labels["col_listings"], labels["col_bar"])
    right = {labels["col_count"], labels["col_refunded"], labels["col_dev"],
             labels["col_platform"], labels["col_share"], labels["col_avg"],
             labels["col_listings"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    peak = max([float(row["share"] or 0) for row in envelope["rows"]] or [0.0])
    body = []
    for row in envelope["rows"]:
        share = row["share"]
        if share is None or not peak:
            bar = '<span class=empty>%s</span>' % e(dash)
        else:
            width = max(0.0, min(100.0, float(share) / peak * 100.0))
            bar = ('<div class=bar><i style="width:%.1f%%"></i></div>' % width)
        cells = [
            ("", reason_text(row["reason"], labels)),
            ("n", fmt(row["refund_count"], dash)),
            ("n", fmt(row["refunded"], dash)),
            ("n", fmt(row["dev_share"], dash)),
            ("n", fmt(row["platform_share"], dash)),
            ("n", fmt(share, dash)),
            ("n", fmt(row["avg_amount"], dash)),
            ("n", fmt(row["listing_count"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr class="%s" data-reason="%s">%s</tr>'
                    % ("unlabeled" if row["reason"] is None else "labeled",
                       e(reason_text(row["reason"], labels)), tds))
    if not body:
        return ('<p class=empty>%s</p>' % e(labels["top_none"]))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash)))


def build_html(market, sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_legs"], labels["law_share"], labels["law_avg"],
            labels["law_rate"], labels["law_count"], labels["law_top"],
            labels["law_hhi"], labels["law_order"], labels["law_scope"],
            labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])), seller_section(block, labels, e, dash))
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
           rows_table(market, labels, e, dash), e(labels["sec_sellers"]),
           sections, e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
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
    """AC-PWC84 (R3606): landing this pair and re-deriving the face are ONE run.

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
        print("SELLER-REFUND-REASONS CHECK %s fails=%d html=%dB json=%dB"
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
        "scope": market["scope"],
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

    face = _refresh_face(args.out, args.json)
    print("SELLER-REFUND-REASONS %s bytes=%d sellers=%d refunds=%d reasons=%d"
          " face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"], payload["market"]["refund_count"],
             payload["market"]["reason_count"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
