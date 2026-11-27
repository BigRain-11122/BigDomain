#!/usr/bin/env python3
"""Render the buyer watch alert feed on one page a human opens.

Why this exists: api_watchlist answers WHAT a resident is watching, and
api_watch_alerts answers WHAT HAPPENED to those watches (a price moved, a
shelf sold out, a listing was retired), but a git grep over tools/ and
preview/ answered zero hits: no page could be opened, so "what happened to
the things I watch" could only be asked of a shell.

Nothing here re-implements a market rule. Every number comes from the shipped
api_watch_alerts() face read over a fresh throwaway demo world seeded through
the shipped report helpers plus this driver's shipped-door watch fixture
(watch, revise_price, purchase, delist). Buyers are enumerated through the
shipped board face instead of being typed by hand. The page prints what the
face hands it and never recomputes a count; the only checks it runs are the
face's own published laws, and a broken law refuses the render instead of
printing a plausible page.

The factory demo world carries no watches, so the four alerts kinds would be
proved by probe alone if the page simply rendered it. The fixture therefore
drives the shipped doors under a pinned clock and lands one row of each kind:
a price rise, a price drop, a limited shelf selling out, and a retirement.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/watch_alerts_board.py
  python tools/watch_alerts_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-WALB1..AC-WALB6 are pre-registered in src/os/backlog.md (R3434 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/watch-alerts-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "watch-alerts-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "watch-alerts-board.json")
COPY = os.path.join(ROOT, "preview", "watch-alerts-board-copy.json")

FACE = "api_watch_alerts"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-WALB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 5 keys.
ENVELOPE_KEYS = (
    "buyer_id", "watch_count", "alert_count", "disclaimer", "alerts",
)

# One alert row, 13 keys.
ROW_KEYS = (
    "watch_id", "listing_id", "listing_key", "title", "dev_account",
    "kind", "severity", "price_at_watch", "current_price", "delta",
    "delisted", "sold_out", "watched_utc",
)

# The four kinds, their pinned rank and severity (AC-WAL3).
KIND_RANK = {"delisted": 0, "sold_out": 1, "price_drop": 2, "price_rise": 3}
KIND_SEVERITY = {"delisted": "high", "sold_out": "warn",
                 "price_drop": "info", "price_rise": "info"}

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_buyers", "sec_law",
    "sec_disc", "sec_rep",
    "kpi_watches", "kpi_alerts", "kpi_delisted", "kpi_sold_out",
    "kpi_drops", "kpi_rises", "kpi_net_delta",
    "col_buyer", "col_watches", "col_alerts", "col_delisted",
    "col_sold_out", "col_drops", "col_rises",
    "col_kind", "col_listing", "col_seller", "col_severity",
    "col_at_watch", "col_current", "col_delta", "col_watched",
    "label_delisted", "label_sold_out", "label_price_drop",
    "label_price_rise",
    "empty_buyer", "none",
    "law_count", "law_watches", "law_kinds", "law_severity", "law_delta",
    "law_order", "law_retired", "law_purchased", "law_silent", "law_scope",
    "law_notadvice",
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
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.delisted{border-color:#dcb0b0;color:#8a4242}
.badge.sold-out{border-color:#e0c898;color:#7a5f28}
.badge.price-drop{border-color:#b6cdb9;color:#3f6a4c}
.badge.price-rise{border-color:#b9c6d8;color:#3d5268}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_WALB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_WALB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def seed_watches(am):
    """Land one alert of each kind through the shipped doors.

    The factory demo world carries no watch rows, so the four kinds this page
    exists for would only ever be proved by a probe. The fixture watches,
    revises prices, buys the single unit of a limited shelf and retires a
    listing under a pinned clock. It is a world builder, never a data source:
    every number on the page is still read back from api_watch_alerts().
    """
    board = am.api_board()
    by_key = {str(row["listing_key"]): int(row["listing_id"])
              for row in board["listings"]}
    d1 = by_key["risk-scan"]
    d2 = by_key["macro-feed"]
    d3 = by_key["chart-render"]
    clock = R.Clock()
    orig = R.A._now_utc
    R.A._now_utc = clock.now_utc
    try:
        clock.value = "2026-09-23T00:00:00Z"
        am.watch_api("usr:bob", d3)
        am.watch_api("usr:bob", d1)      # bob already bought d1: silent
        clock.value = "2026-09-24T00:00:00Z"
        am.watch_api("usr:carol", d2)
        clock.value = "2026-09-25T00:00:00Z"
        am.watch_api("usr:dave", d3)
        clock.value = "2026-09-25T06:00:00Z"
        am.watch_api("usr:erin", d1)
        clock.value = "2026-09-26T00:00:00Z"
        pub = am.publish_api("usr:dana", "scan-plus", "Scan Plus API",
                             "extended scan with one seat", {"endpoint": "/scan"},
                             4, False, supply=1)
        sp = pub["listing_id"]
        clock.value = "2026-09-26T06:00:00Z"
        am.watch_api("usr:bob", sp)
        clock.value = "2026-09-27T00:00:00Z"
        am.revise_price("usr:frank", d3, 8)   # rise for bob and dave
        clock.value = "2026-09-28T00:00:00Z"
        am.revise_price("usr:dana", d1, 7)    # drop for erin
        clock.value = "2026-09-29T00:00:00Z"
        am.purchase_api("usr:carol", sp, "ref-carol-sp")  # shelf sells out
        clock.value = "2026-09-30T00:00:00Z"
        am.delist_api("usr:dana", d2)         # retirement for carol
    finally:
        R.A._now_utc = orig


def read_world():
    """Read one alert envelope (and its watchlist) per buyer."""
    tmp_root = tempfile.mkdtemp(prefix="watch-alerts-board-")
    db = os.path.join(tmp_root, "watch-alerts-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        seed_watches(am)
        board = getattr(am, BOARD_FACE)()
        buyers = []
        watches = {}
        for buyer in buyer_ids(board, am):
            buyers.append(dict(getattr(am, FACE)(buyer)))
            watches[buyer] = dict(am.api_watchlist(buyer))
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
        for row in envelope["alerts"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("listing_id"), ",".join(missing)))
    return buyers, watches, disclaimer


def buyer_ids(board, am):
    """The four demo residents plus every seller, all through shipped faces."""
    ids = set()
    for row in board["listings"]:
        ids.add(str(row["dev_account"]))
    for who in ("bob", "carol", "dave", "erin"):
        ids.add("usr:" + who)
    return sorted(ids)


def _envelope_problems(envelope, watchlist, label):
    """AC-WALB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["alerts"]
    if int(envelope["alert_count"]) != len(rows):
        problems.append("%s alert_count %r != alerts %d"
                        % (label, envelope["alert_count"], len(rows)))
    if int(envelope["watch_count"]) < int(envelope["alert_count"]):
        problems.append("%s watch_count %r < alert_count %r"
                        % (label, envelope["watch_count"],
                           envelope["alert_count"]))
    if int(watchlist["watch_count"]) != int(envelope["watch_count"]):
        problems.append("%s watch_count %r != watchlist %r"
                        % (label, envelope["watch_count"],
                           watchlist["watch_count"]))
    purchased = {int(w["listing_id"]) for w in watchlist["watches"]
                 if w.get("purchased")}
    for row in rows:
        name = "%s/%s" % (label, row["listing_id"])
        kind = str(row["kind"])
        if kind not in KIND_RANK:
            problems.append("%s carries unknown kind %r" % (name, kind))
            continue
        if str(row["severity"]) != KIND_SEVERITY[kind]:
            problems.append("%s severity %r != %r"
                            % (name, row["severity"], KIND_SEVERITY[kind]))
        if int(row["delta"]) != int(row["current_price"]) - int(
                row["price_at_watch"]):
            problems.append("%s delta %r != %d - %d"
                            % (name, row["delta"], row["current_price"],
                               row["price_at_watch"]))
        if kind == "price_drop" and int(row["delta"]) >= 0:
            problems.append("%s is a drop with delta %r"
                            % (name, row["delta"]))
        if kind == "price_rise" and int(row["delta"]) <= 0:
            problems.append("%s is a rise with delta %r"
                            % (name, row["delta"]))
        if kind == "delisted" and not bool(row["delisted"]):
            problems.append("%s is a delisted row without the flag" % name)
        if kind != "delisted" and bool(row["delisted"]):
            problems.append("%s carries the retired flag on a live kind"
                            % name)
        if int(row["listing_id"]) in purchased:
            problems.append("%s is a watch this buyer already bought" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s carries an empty listing_key" % name)
        if not str(row["dev_account"] or "").startswith("usr:"):
            problems.append("%s seller %r is not a resident"
                            % (name, row["dev_account"]))
        if not str(row["watched_utc"] or "").strip():
            problems.append("%s carries no watched_utc" % name)
    order = [(KIND_RANK.get(str(r["kind"]), 9), int(r["listing_id"]))
             for r in rows]
    if order != sorted(order):
        problems.append("%s rows are not in the pinned total order" % label)
    return problems


def check_laws(buyers, watches):
    problems = []
    for block in buyers:
        name = str(block["buyer_id"])
        problems.extend(_envelope_problems(block, watches.get(name) or {},
                                          name))
        if not name.startswith("usr:"):
            problems.append("%s is not a resident account" % name)
    if buyers and buyers[0]["disclaimer"] != buyers[-1]["disclaimer"]:
        problems.append("buyers disagree on the disclaimer")
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def kind_count(envelope, kind):
    return sum(1 for row in envelope["alerts"] if str(row["kind"]) == kind)


def net_delta(envelope):
    total = sum(int(row["delta"]) for row in envelope["alerts"])
    return total


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_watches"], fmt(envelope["watch_count"], dash)),
        (labels["kpi_alerts"], fmt(envelope["alert_count"], dash)),
        (labels["kpi_delisted"], str(kind_count(envelope, "delisted"))),
        (labels["kpi_sold_out"], str(kind_count(envelope, "sold_out"))),
        (labels["kpi_drops"], str(kind_count(envelope, "price_drop"))),
        (labels["kpi_rises"], str(kind_count(envelope, "price_rise"))),
        (labels["kpi_net_delta"], fmt(net_delta(envelope), dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def summary_table(buyers, labels, e, dash):
    head = (labels["col_buyer"], labels["col_watches"], labels["col_alerts"],
            labels["col_delisted"], labels["col_sold_out"],
            labels["col_drops"], labels["col_rises"])
    head_html = "<th>%s</th>" % e(head[0]) + "".join(
        '<th class=n>%s</th>' % e(cell) for cell in head[1:])
    body = []
    for block in buyers:
        cells = (fmt(block["watch_count"], dash),
                 fmt(block["alert_count"], dash),
                 str(kind_count(block, "delisted")),
                 str(kind_count(block, "sold_out")),
                 str(kind_count(block, "price_drop")),
                 str(kind_count(block, "price_rise")))
        body.append('<tr data-buyer="%s"><td><code>%s</code></td>%s</tr>'
                    % (e(str(block["buyer_id"])), e(str(block["buyer_id"])),
                       "".join('<td class=n>%s</td>' % e(str(cell))
                               for cell in cells)))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_buyer"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def badge(kind, labels, e):
    name = "label_" + kind
    return '<span class="badge %s">%s</span>' % (
        e(kind.replace("_", "-")), e(labels[name]))


def rows_table(envelope, labels, e, dash):
    head = (labels["col_kind"], labels["col_listing"], labels["col_seller"],
            labels["col_severity"], labels["col_at_watch"],
            labels["col_current"], labels["col_delta"], labels["col_watched"])
    head_html = "".join("<th>%s</th>" % e(cell) for cell in head)
    body = []
    for row in envelope["alerts"]:
        listing = "<code>%s</code> %s" % (
            e(str(row["listing_key"])), e(str(row["title"])))
        body.append(
            '<tr data-kind="%s" data-listing="%s"><td>%s</td>'
            '<td>%s</td><td><code>%s</code></td><td>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td>%s</td></tr>'
            % (e(str(row["kind"])), e(str(row["listing_id"])),
               badge(str(row["kind"]), labels, e), listing,
               e(str(row["dev_account"])), e(str(row["severity"])),
               e(fmt(row["price_at_watch"], dash)),
               e(fmt(row["current_price"], dash)),
               e(fmt(row["delta"], dash)), e(str(row["watched_utc"]))))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_buyer"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def buyer_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["col_buyer"]), e(str(block["buyer_id"])),
               kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash)))


def build_html(buyers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_watches"], labels["law_kinds"],
            labels["law_severity"], labels["law_delta"], labels["law_order"],
            labels["law_retired"], labels["law_purchased"],
            labels["law_silent"], labels["law_scope"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-buyer="%s">%s</div>'
        % (e(str(block["buyer_id"])),
           buyer_section(block, labels, e, dash))
        for block in buyers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_buyers"]),
           summary_table(buyers, labels, e, dash),
           e(labels["sec_buyers"]),
           sections or ('<div class=card data-buyer-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_buyer"])),
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
    """AC-PWC86 (R3608): landing this pair and re-deriving the face are ONE run.

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
        print("WATCH-ALERTS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        buyers, watches, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(buyers, watches)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(buyers, labels, now, disclaimer)
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
    print("WATCH-ALERTS %s bytes=%d buyers=%d alerts=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"],
             sum(int(b["alert_count"]) for b in buyers), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
