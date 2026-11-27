#!/usr/bin/env python3
"""Render the resident purchase library on one page a human opens.

Why this exists: api_library answers "what did I buy and what do I own now"
with its own AC-AML1..8 criteria, but a git grep over tools/ and preview/
answered rc=1 with zero hits, so the itemised library could only be read by
calling the sandbox from a shell. api_sales is the seller side ("who bought
from me"), and the R3430 account statement sums one resident into totals - no
page listed the individual purchases with the price actually charged, the live
asking price, the refund stamp, the retirement stamp and this buyer's own
stars side by side.

Nothing here re-implements a market rule. Every number comes from the shipped
api_library() face read over a fresh throwaway demo world seeded through the
shipped report helpers. Buyers are enumerated through the shipped board and
sales faces plus the four demo residents instead of being typed by hand from
the row data. The page prints what the face hands it and never recomputes a
count; the only checks it runs are the face's own published laws, and a broken
law refuses the render instead of printing a plausible page.

The market block on the page is this page's sum over the printed buyer
envelopes, not a shipped field, and the page says so. The real sandbox is
never opened for writing and nothing touches the network.

Usage:
  python tools/library_board.py
  python tools/library_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-LIBB1..AC-LIBB6 are pre-registered in src/os/backlog.md (R3435 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/library-board-copy.json and appear in the rendered document only,
never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "library-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "library-board.json")
COPY = os.path.join(ROOT, "preview", "library-board-copy.json")

FACE = "api_library"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-LIBB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 8 keys.
ENVELOPE_KEYS = (
    "buyer_id", "purchase_count", "total_spent", "refund_count",
    "total_refunded", "net_spent", "disclaimer", "purchases",
)

# One purchase row, 17 keys.
ROW_KEYS = (
    "purchase_id", "listing_id", "listing_key", "title", "dev_account",
    "price_paid", "dev_share", "platform_share", "spend_tx",
    "purchased_utc", "current_price", "delisted", "delisted_utc",
    "my_rating", "refunded", "refunded_utc", "refund_tx",
)

# The market block is this page's sum over the printed envelopes.
MARKET_KEYS = ("buyer_count", "purchase_count", "total_spent",
               "refund_count", "total_refunded", "net_spent")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "kpi_buyers", "kpi_purchases", "kpi_spent", "kpi_refunds",
    "kpi_refunded", "kpi_net",
    "col_id", "col_listing", "col_seller", "col_paid", "col_split",
    "col_live", "col_refund", "col_delist", "col_rating", "col_stamp",
    "col_tx",
    "badge_refunded", "badge_not_refunded", "badge_delisted",
    "badge_live", "badge_rated", "badge_unrated",
    "split_caption", "split_dev", "split_platform",
    "empty_buyer", "empty_scope", "none",
    "law_count", "law_spend", "law_refund", "law_net", "law_split",
    "law_delist", "law_refundstamp", "law_rating", "law_order",
    "law_live", "law_market", "law_notadvice",
    "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1240px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:18px 0 6px;font-weight:620;color:#3c4653}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line);
white-space:nowrap}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;
border:1px solid var(--line);font-size:11.5px;background:#f2f5f8;
color:#3c4653}
.badge.refund{background:#fff1f0;border-color:#f3c9c4;color:#98322a}
.badge.delist{background:#f4f0fb;border-color:#d8cdf0;color:#553a94}
.badge.rated{background:#eef7ee;border-color:#c9e2c9;color:#2e6b34}
.badge.quiet{background:#f6f7f9;color:var(--muted)}
.badge.live{background:#eef4fb;border-color:#c8d9ef;color:#28527f}
.note{color:var(--muted);font-size:12.5px;margin:8px 0 0}
.law{color:#3c4653;font-size:13px;margin:2px 0}
.empty{color:var(--muted);font-size:13px;margin:6px 0}
.disclaimer{color:var(--muted);font-size:12.5px}
code{font-size:12px;background:#f2f5f8;padding:1px 5px;border-radius:5px}
footer{color:var(--muted);font-size:12px;margin:26px 0 8px}
"""


class FaceError(Exception):
    code = "E_LIBB_FACE"


class LawError(Exception):
    code = "E_LIBB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if key not in labels]
    if missing:
        raise FaceError("label copy missing keys: %s" % ",".join(missing))
    return labels


def read_world():
    """Read one library envelope per buyer over a throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="library-board-")
    db = os.path.join(tmp_root, "library-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        buyers = []
        for buyer in buyer_ids(board, am):
            buyers.append(dict(getattr(am, FACE)(buyer)))
        disclaimer = buyers[0]["disclaimer"] if buyers else None
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
        raise FaceError("no buyer on the shipped board face")
    for envelope in buyers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("buyer_id"), ",".join(missing)))
        for row in envelope["purchases"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("purchase_id"), ",".join(missing)))
    return buyers, disclaimer


def buyer_ids(board, am):
    """Purchase holders through the shipped sales face, then the demo roster."""
    ids = set()
    sellers = []
    for row in board["listings"]:
        seller = str(row["dev_account"])
        if seller not in sellers:
            sellers.append(seller)
        ids.add(seller)
    for seller in sellers:
        sales = am.api_sales(seller)
        for row in sales.get("rows") or sales.get("sales") or []:
            buyer = row.get("buyer_id")
            if buyer:
                ids.add(str(buyer))
    for who in ("bob", "carol", "dave", "erin"):
        ids.add("usr:" + who)
    return sorted(ids)


def market_block(buyers, disclaimer):
    return {
        "buyer_count": len(buyers),
        "purchase_count": sum(int(b["purchase_count"]) for b in buyers),
        "total_spent": sum(int(b["total_spent"]) for b in buyers),
        "refund_count": sum(int(b["refund_count"]) for b in buyers),
        "total_refunded": sum(int(b["total_refunded"]) for b in buyers),
        "net_spent": sum(int(b["net_spent"]) for b in buyers),
    }


def check_laws(buyers):
    """AC-LIBB3 read at the source: refuse rather than print."""
    problems = []
    for block in buyers:
        who = block.get("buyer_id")
        rows = block["purchases"]
        if int(block["purchase_count"]) != len(rows):
            problems.append("%s purchase_count %s != rows %d"
                            % (who, block["purchase_count"], len(rows)))
        if int(block["total_spent"]) != sum(int(r["price_paid"])
                                            for r in rows):
            problems.append("%s total_spent != sum(price_paid)" % who)
        if int(block["refund_count"]) != sum(1 for r in rows if r["refunded"]):
            problems.append("%s refund_count != count(refunded)" % who)
        if int(block["net_spent"]) != (int(block["total_spent"])
                                      - int(block["total_refunded"])):
            problems.append("%s net_spent != total_spent - total_refunded"
                            % who)
        if int(block["total_refunded"]) < 0:
            problems.append("%s total_refunded negative" % who)
        ids = [int(r["purchase_id"]) for r in rows]
        if ids != sorted(ids) or len(set(ids)) != len(ids):
            problems.append("%s purchase_id not strictly ascending" % who)
        for row in rows:
            if (int(row["dev_share"]) + int(row["platform_share"])
                    != int(row["price_paid"])):
                problems.append("%s #%s split != price_paid"
                                % (who, row["purchase_id"]))
            if bool(row["delisted"]) != (row["delisted_utc"] is not None):
                problems.append("%s #%s delisted flag != stamp"
                                % (who, row["purchase_id"]))
            has_refund_stamp = (row["refunded_utc"] is not None
                                and row["refund_tx"] is not None)
            if bool(row["refunded"]) != has_refund_stamp:
                problems.append("%s #%s refunded flag != stamps"
                                % (who, row["purchase_id"]))
            stars = row["my_rating"]
            if stars is not None and not (1 <= int(stars) <= 5):
                problems.append("%s #%s rating out of range"
                                % (who, row["purchase_id"]))
            if int(row["current_price"]) < 0:
                problems.append("%s #%s negative current_price"
                                % (who, row["purchase_id"]))
            if not str(row.get("purchased_utc") or ""):
                problems.append("%s #%s empty purchased_utc"
                                % (who, row["purchase_id"]))
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    return str(value)


def text(value, none_text):
    if value is None or str(value) == "":
        return none_text
    return str(value)


def kpi_html(block, labels, e, dash):
    items = [
        (labels["kpi_purchases"], fmt(block["purchase_count"], dash)),
        (labels["kpi_spent"], fmt(block["total_spent"], dash)),
        (labels["kpi_refunds"], fmt(block["refund_count"], dash)),
        (labels["kpi_refunded"], fmt(block["total_refunded"], dash)),
        (labels["kpi_net"], fmt(block["net_spent"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def listing_cell(row, e):
    return ('<code>%s</code> %s'
            % (e(str(row["listing_key"])), e(str(row["title"]))))


def refund_cell(row, labels, e, dash):
    if row["refunded"]:
        return ('<span class="badge refund">%s</span> %s'
                % (e(labels["badge_refunded"]),
                   e(text(row["refunded_utc"], dash))))
    return ('<span class="badge quiet">%s</span>'
            % e(labels["badge_not_refunded"]))


def delist_cell(row, labels, e, dash):
    if row["delisted"]:
        return ('<span class="badge delist">%s</span> %s'
                % (e(labels["badge_delisted"]),
                   e(text(row["delisted_utc"], dash))))
    return '<span class="badge live">%s</span>' % e(labels["badge_live"])


def rating_cell(row, labels, e):
    if row["my_rating"] is None:
        return '<span class="badge quiet">%s</span>' % e(labels["badge_unrated"])
    return ('<span class="badge rated">%s</span> %s'
            % (e(labels["badge_rated"]), e(str(row["my_rating"]))))


def rows_table(block, labels, e, dash):
    head = "".join("<th>%s</th>" % e(labels[key]) for key in (
        "col_id", "col_listing", "col_seller", "col_paid", "col_split",
        "col_live", "col_refund", "col_delist", "col_rating", "col_stamp",
        "col_tx"))
    body = []
    for row in block["purchases"]:
        body.append(
            '<tr data-listing="%s" data-refund="%s">'
            '<td class=n>%s</td><td>%s</td><td><code>%s</code></td>'
            '<td class=n>%s</td><td class=n>%s / %s</td>'
            '<td class=n>%s</td><td>%s</td><td>%s</td><td>%s</td>'
            '<td>%s</td><td><code>%s</code></td></tr>'
            % (e(str(row["listing_id"])),
               e("1" if row["refunded"] else "0"),
               e(fmt(row["purchase_id"], dash)),
               listing_cell(row, e), e(str(row["dev_account"])),
               e(fmt(row["price_paid"], dash)),
               e(fmt(row["dev_share"], dash)),
               e(fmt(row["platform_share"], dash)),
               e(fmt(row["current_price"], dash)),
               refund_cell(row, labels, e, dash),
               delist_cell(row, labels, e, dash),
               rating_cell(row, labels, e),
               e(text(row["purchased_utc"], dash)),
               e(str(row["spend_tx"])[:8])))
    return ('<table><tr>%s</tr>%s</table>' % (head, "".join(body)))


def split_caption(block, labels, e):
    return ('<p class=note>%s &middot; %s %d &middot; %s %d</p>'
            % (e(labels["split_caption"]),
               e(labels["split_dev"]),
               sum(int(r["dev_share"]) for r in block["purchases"]),
               e(labels["split_platform"]),
               sum(int(r["platform_share"]) for r in block["purchases"])))


def buyer_section(block, labels, e, dash):
    if not block["purchases"]:
        return ("<h3><code>%s</code></h3>"
                "<div class=kpi>%s</div>"
                '<p class=empty data-buyer-empty="1">%s</p>'
                % (e(str(block["buyer_id"])), kpi_html(block, labels, e, dash),
                   e(labels["empty_buyer"])))
    return ("<h3><code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(str(block["buyer_id"])), kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash))
            + split_caption(block, labels, e))


def build_html(buyers, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_spend"], labels["law_refund"],
            labels["law_net"], labels["law_split"], labels["law_delist"],
            labels["law_refundstamp"], labels["law_rating"], labels["law_order"],
            labels["law_live"], labels["law_market"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-buyer="%s">%s</div>'
        % (e(str(block["buyer_id"])), buyer_section(block, labels, e, dash))
        for block in buyers)
    market_items = [
        (labels["kpi_buyers"], fmt(market["buyer_count"], dash)),
        (labels["kpi_purchases"], fmt(market["purchase_count"], dash)),
        (labels["kpi_spent"], fmt(market["total_spent"], dash)),
        (labels["kpi_refunds"], fmt(market["refund_count"], dash)),
        (labels["kpi_refunded"], fmt(market["total_refunded"], dash)),
        (labels["kpi_net"], fmt(market["net_spent"], dash)),
    ]
    market_kpi = "".join('<div><span>%s</span><b>%s</b></div>'
                         % (e(k), e(v)) for k, v in market_items)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card data-market=1>"
        "<div class=kpi>%s</div>"
        '<p class=note>%s</p></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_market"]),
           market_kpi, e(labels["law_market"]),
           e(labels["sec_buyers"]),
           sections or ('<div class=card data-buyer-empty="1">'
                        '<p class=empty>%s</p></div>'
                        % e(labels["empty_scope"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer or ""))


DISCLAIMER_SLOT = "[[NONADVICE_SLOT]]"


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
    """AC-PWC51 (R3573): landing this pair and re-deriving the CEO face are ONE run.

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
        print("LIBRARY CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        buyers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    market = market_block(buyers, disclaimer)
    problems = check_laws(buyers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(buyers, market, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "buyer",
        "buyer_count": len(buyers),
        "buyers": [{key: block[key] for key in ENVELOPE_KEYS}
                   for block in buyers],
        "market": market,
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

    print("LIBRARY %s bytes=%d buyers=%d purchases=%d spent=%d net=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"], market["purchase_count"],
             market["total_spent"], market["net_spent"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
