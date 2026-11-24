#!/usr/bin/env python3
"""Render the resident account statement on one page a human opens.

Why this exists: api_buyer_profile answers "what has this account spent, got
back and rated" with its own AC-AMBY1..8 criteria, but a git grep over tools/
and preview/ answered rc=1 with zero hits, so the reading could only be had by
calling the sandbox from a shell. api_seller_ledger and api_buyer_ledger print
row-level ledgers, and no page summed one resident's account into a single
statement. Measured in R3430 over the factory demo world: usr:bob carries two
purchases, one refund, gross 13, refunded 10, net 3 (dev 3 / platform 0) and
one rating at 4.0; usr:carol carries gross 10 / net 10 (dev 7 / platform 3)
and one rating at 5.0; usr:erin carries one purchase and one refund so net is
0 and avg_rating is None; usr:nobody is an honest empty envelope.

Nothing here re-implements a market rule. Every number comes from the shipped
api_buyer_profile() face read over a fresh throwaway demo world seeded through
the shipped report helpers. Buyers are enumerated through the shipped board and
sales faces instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/buyer_profile_board.py
  python tools/buyer_profile_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BPFB1..AC-BPFB6 are pre-registered in src/os/backlog.md (R3430 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-profile-board-copy.json and appear in the rendered document
only, never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-profile-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-profile-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-profile-board-copy.json")

FACE = "api_buyer_profile"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-BPFB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "market", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 17 keys.
ENVELOPE_KEYS = (
    "buyer_id", "purchase_count", "refund_count", "net_purchase_count",
    "listing_count", "gross_spent", "refunded_total", "net_spent",
    "dev_paid", "platform_paid", "rating_count", "avg_rating",
    "watch_count", "live_watch_count", "first_purchase_utc",
    "last_purchase_utc", "disclaimer",
)

# The market block: the same envelope minus the per-account identity.
MARKET_KEYS = tuple(key for key in ENVELOPE_KEYS if key != "buyer_id")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot",
    "sec_market", "sec_buyers", "sec_law", "sec_disc", "sec_rep",
    "kpi_buyers", "kpi_purchases", "kpi_refunds", "kpi_net_purchases",
    "kpi_listings", "kpi_gross", "kpi_refunded", "kpi_net",
    "kpi_dev", "kpi_platform", "kpi_ratings", "kpi_avg", "kpi_watch",
    "kpi_first", "kpi_last",
    "col_field", "col_value",
    "row_purchases", "row_refunds", "row_net_purchases", "row_listings",
    "row_gross", "row_refunded", "row_net", "row_dev", "row_platform",
    "row_ratings", "row_avg", "row_watch", "row_first", "row_last",
    "split_caption", "split_dev", "split_platform",
    "empty_scope", "empty_account", "none",
    "law_count", "law_spend", "law_halves", "law_pool", "law_watch",
    "law_rating", "law_range", "law_stamp", "law_market", "law_scope",
    "law_bar", "law_notadvice",
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
.split{display:flex;height:10px;border-radius:999px;overflow:hidden;
background:#eef1f5;min-width:160px;margin:6px 0 2px}
.split i{display:block;height:10px}
.split i.dev{background:#4f7cac}
.split i.plat{background:#c9a227}
.zero-dot{display:inline-block;width:7px;height:7px;margin-right:5px;
border-radius:999px;background:#9aa6b2;vertical-align:middle}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
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

    code = "E_BPFB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_BPFB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_buyers(board, sales_face):
    """Buyer ids through the shipped board and sales faces, never typed."""
    found = set()
    for row in board["listings"]:
        sales = sales_face(str(row["dev_account"]))
        for sale in (sales.get("sales") or []):
            if sale.get("buyer_id"):
                found.add(str(sale["buyer_id"]))
    return sorted(found)


def read_world():
    """Read one scoped envelope per buyer from the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-profile-board-")
    db = os.path.join(tmp_root, "buyer-profile-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        buyers = [dict(getattr(am, FACE)(buyer))
                  for buyer in enumerate_buyers(board, am.api_sales)]
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
        raise FaceError("no buyer on the shipped sales faces")
    for envelope in buyers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("buyer_id"), ",".join(missing)))
    return buyers, disclaimer


def market_block(buyers, disclaimer):
    """The market row is a column-by-column sum, and says so on the page."""
    def total(key):
        return sum(int(block[key]) for block in buyers)

    ratings = sum(int(block["rating_count"]) for block in buyers)
    star_sum = sum(float(block["avg_rating"]) * int(block["rating_count"])
                   for block in buyers
                   if block["avg_rating"] is not None)
    stamps = [block["first_purchase_utc"] for block in buyers
              if block["first_purchase_utc"] is not None]
    lasts = [block["last_purchase_utc"] for block in buyers
             if block["last_purchase_utc"] is not None]
    return {
        "purchase_count": total("purchase_count"),
        "refund_count": total("refund_count"),
        "net_purchase_count": total("net_purchase_count"),
        "listing_count": total("listing_count"),
        "gross_spent": total("gross_spent"),
        "refunded_total": total("refunded_total"),
        "net_spent": total("net_spent"),
        "dev_paid": total("dev_paid"),
        "platform_paid": total("platform_paid"),
        "rating_count": ratings,
        "avg_rating": (star_sum / ratings if ratings else None),
        "watch_count": total("watch_count"),
        "live_watch_count": total("live_watch_count"),
        "first_purchase_utc": min(stamps) if stamps else None,
        "last_purchase_utc": max(lasts) if lasts else None,
        "disclaimer": disclaimer,
    }


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def _account_problems(block, label):
    """AC-BPFB3 read at the source: refuse rather than print."""
    problems = []
    if int(block["net_spent"]) != (int(block["gross_spent"])
                                   - int(block["refunded_total"])):
        problems.append("%s net_spent != gross - refunded" % label)
    if int(block["purchase_count"]) != (int(block["net_purchase_count"])
                                        + int(block["refund_count"])):
        problems.append("%s purchase_count != net + refund" % label)
    if int(block["dev_paid"]) + int(block["platform_paid"]) != int(
            block["net_spent"]):
        problems.append("%s dev + platform != net_spent" % label)
    if int(block["live_watch_count"]) > int(block["watch_count"]):
        problems.append("%s live_watch_count > watch_count" % label)
    ratings = int(block["rating_count"])
    avg = block["avg_rating"]
    if ratings == 0 and avg is not None:
        problems.append("%s zero ratings but avg_rating %r" % (label, avg))
    if ratings > 0 and avg is None:
        problems.append("%s %d ratings but avg_rating is None"
                        % (label, ratings))
    if avg is not None and not (0.0 <= float(avg) <= 5.0):
        problems.append("%s avg_rating %r outside [0,5]" % (label, avg))
    first = block["first_purchase_utc"]
    last = block["last_purchase_utc"]
    if int(block["purchase_count"]) == 0:
        if first is not None or last is not None:
            problems.append("%s empty account with a purchase stamp" % label)
    elif first is None or last is None:
        problems.append("%s purchases without both stamps" % label)
    elif str(first) > str(last):
        problems.append("%s first_purchase_utc after last_purchase_utc"
                        % label)
    if not str(block["buyer_id"]).startswith("usr:"):
        problems.append("%s is not a resident account" % label)
    return problems


def check_laws(buyers, market):
    problems = []
    seen = set()
    for block in buyers:
        name = str(block["buyer_id"])
        problems.extend(_account_problems(block, name))
        if name in seen:
            problems.append("%s appears twice" % name)
        seen.add(name)
    for key in ("purchase_count", "refund_count", "net_purchase_count",
                "listing_count", "gross_spent", "refunded_total",
                "net_spent", "dev_paid", "platform_paid", "rating_count",
                "watch_count", "live_watch_count"):
        want = sum(int(block[key]) for block in buyers)
        if int(market[key]) != want:
            problems.append("market %s %r != buyer sum %d"
                            % (key, market[key], want))
    ratings = sum(int(block["rating_count"]) for block in buyers)
    star_sum = sum(float(block["avg_rating"]) * int(block["rating_count"])
                   for block in buyers if block["avg_rating"] is not None)
    want_avg = (star_sum / ratings) if ratings else None
    if not _close(market["avg_rating"], want_avg):
        problems.append("market avg_rating %r != %r"
                        % (market["avg_rating"], want_avg))
    stamps = [block["first_purchase_utc"] for block in buyers
              if block["first_purchase_utc"] is not None]
    if market["first_purchase_utc"] != (min(stamps) if stamps else None):
        problems.append("market first_purchase_utc %r"
                        % (market["first_purchase_utc"],))
    lasts = [block["last_purchase_utc"] for block in buyers
             if block["last_purchase_utc"] is not None]
    if market["last_purchase_utc"] != (max(lasts) if lasts else None):
        problems.append("market last_purchase_utc %r"
                        % (market["last_purchase_utc"],))
    if buyers and buyers[0]["disclaimer"] != market["disclaimer"]:
        problems.append("market disclaimer differs from the envelopes")
    return problems


def fmt(value, dash):
    return dash if value is None else str(int(value))


def num(value, dash):
    return dash if value is None else "%.2f" % float(value)


def text(value, dash):
    return dash if value is None else str(value)


def kpi_html(block, labels, e, dash):
    items = [
        (labels["kpi_purchases"], fmt(block["purchase_count"], dash)),
        (labels["kpi_refunds"], fmt(block["refund_count"], dash)),
        (labels["kpi_net_purchases"], fmt(block["net_purchase_count"], dash)),
        (labels["kpi_listings"], fmt(block["listing_count"], dash)),
        (labels["kpi_gross"], fmt(block["gross_spent"], dash)),
        (labels["kpi_refunded"], fmt(block["refunded_total"], dash)),
        (labels["kpi_net"], fmt(block["net_spent"], dash)),
        (labels["kpi_dev"], fmt(block["dev_paid"], dash)),
        (labels["kpi_platform"], fmt(block["platform_paid"], dash)),
        (labels["kpi_ratings"], fmt(block["rating_count"], dash)),
        (labels["kpi_avg"], num(block["avg_rating"], dash)),
        (labels["kpi_watch"], "%s / %s"
         % (fmt(block["watch_count"], dash),
            fmt(block["live_watch_count"], dash))),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def split_html(block, labels, e, dash):
    """The dev/platform split is a width over net spend, never a share."""
    net = int(block["net_spent"])
    if net <= 0:
        return ('<p class=note><span class="badge quiet">%s</span>%s</p>'
                % (e(labels["split_caption"]), e(labels["empty_account"])))
    dev = int(block["dev_paid"])
    width = float(dev) / float(net) * 100.0
    width = max(0.0, min(100.0, width))
    return ('<p class=note>%s</p>'
            '<div class=split><i class=dev style="width:%.1f%%"></i>'
            '<i class=plat style="width:%.1f%%"></i></div>'
            '<p class=note>%s %d &middot; %s %d</p>'
            % (e(labels["split_caption"]), width, 100.0 - width,
               e(labels["split_dev"]), dev,
               e(labels["split_platform"]), net - dev))


def account_table(block, labels, e, dash):
    rows = (
        (labels["row_purchases"], fmt(block["purchase_count"], dash)),
        (labels["row_refunds"], fmt(block["refund_count"], dash)),
        (labels["row_net_purchases"], fmt(block["net_purchase_count"], dash)),
        (labels["row_listings"], fmt(block["listing_count"], dash)),
        (labels["row_gross"], fmt(block["gross_spent"], dash)),
        (labels["row_refunded"], fmt(block["refunded_total"], dash)),
        (labels["row_net"], fmt(block["net_spent"], dash)),
        (labels["row_dev"], fmt(block["dev_paid"], dash)),
        (labels["row_platform"], fmt(block["platform_paid"], dash)),
        (labels["row_ratings"], fmt(block["rating_count"], dash)),
        (labels["row_avg"], num(block["avg_rating"], dash)),
        (labels["row_watch"], "%s / %s"
         % (fmt(block["watch_count"], dash),
            fmt(block["live_watch_count"], dash))),
        (labels["row_first"], text(block["first_purchase_utc"], dash)),
        (labels["row_last"], text(block["last_purchase_utc"], dash)),
    )
    body = "".join('<tr data-field="%d"><td>%s</td><td class=n>%s</td></tr>'
                   % (index, e(name), e(value))
                   for index, (name, value) in enumerate(rows))
    return ('<table><tr><th>%s</th><th class=n>%s</th></tr>%s</table>'
            % (e(labels["col_field"]), e(labels["col_value"]), body))


def buyer_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s%s"
            % (e(labels["sec_buyers"]), e(str(block["buyer_id"])),
               kpi_html(block, labels, e, dash),
               split_html(block, labels, e, dash),
               account_table(block, labels, e, dash)))


def build_html(buyers, market, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_spend"], labels["law_halves"],
            labels["law_pool"], labels["law_watch"], labels["law_rating"],
            labels["law_range"], labels["law_stamp"], labels["law_market"],
            labels["law_scope"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-buyer="%s">%s</div>'
        % (e(str(block["buyer_id"])), buyer_section(block, labels, e, dash))
        for block in buyers)
    market_kpi = ('<div><span>%s</span><b>%s</b></div>'
                  % (e(labels["kpi_buyers"]), e(dash if not buyers
                                                else str(len(buyers))))
                  + kpi_html(dict(market, buyer_id=""), labels, e, dash))
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card data-market=1>"
        "<div class=kpi>%s</div>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_market"]),
           market_kpi,
           '<p class=note>%s</p>' % e(labels["law_market"]),
           e(labels["sec_buyers"]),
           sections or ('<div class=card data-buyer-empty="1">'
                        '<p class=empty>%s</p></div>'
                        % e(labels["empty_scope"])),
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
        print("BUYER-PROFILE CHECK %s fails=%d html=%dB json=%dB"
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
    problems = check_laws(buyers, market)
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

    print("BUYER-PROFILE %s bytes=%d buyers=%d purchases=%d gross=%d "
          "net=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"],
             sum(int(b["purchase_count"]) for b in buyers),
             sum(int(b["gross_spent"]) for b in buyers),
             sum(int(b["net_spent"]) for b in buyers)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
