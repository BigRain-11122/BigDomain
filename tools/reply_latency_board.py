#!/usr/bin/env python3
"""Render the rating reply latency reading into one page a human can open.

Why this exists: api_rating_reply_latency answers "how long did a rating sit
before the seller answered it, and what is still owed" with its own AC-RRL1..8
criteria, but a git grep over tools/ and preview/ answered rc=1 with zero hits,
so the reading could only be had by calling the sandbox from a shell. The seller
quality scorecard (R3401) reads the star shape and the seller monthly rating
page reads a month histogram; neither shows the waiting time or the unanswered
queue. Measured in R3425: two ratings exist in the demo world, zero are
answered, so the honest page shows a coverage of 0.0 and two owed rows.

Nothing here re-implements a market rule. Every number comes from the shipped
api_rating_reply_latency() face read over a fresh throwaway demo world seeded
through the shipped report helpers. Sellers are enumerated through the shipped
board face instead of being typed by hand. The page prints what the face hands
it and never recomputes a total; the only checks it runs are the face's own
published laws, and a broken law refuses the render instead of printing a
plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/reply_latency_board.py
  python tools/reply_latency_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-RRLB1..AC-RRLB6 are pre-registered in src/os/backlog.md (R3425 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/reply-latency-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "reply-latency-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "reply-latency-board.json")
COPY = os.path.join(ROOT, "preview", "reply-latency-board-copy.json")

FACE = "api_rating_reply_latency"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_rating_reply_latency"
STAMP_FMT = "%Y-%m-%dT%H:%M:%SZ"

# Pinned payload keys (AC-RRLB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "scope",
    "seller_count", "market", "sellers", "disclaimer", "report", "sources",
    "sizes",
)

# The shipped envelope, 13 keys, identical on both scopes.
ENVELOPE_KEYS = (
    "dev_account", "rating_count", "replied_count", "unreplied_count",
    "reply_coverage", "avg_seconds", "median_seconds", "fastest_seconds",
    "slowest_seconds", "latest_reply_utc", "oldest_unreplied_utc",
    "rows", "disclaimer",
)

ROW_KEYS = (
    "rating_id", "listing_id", "listing_key", "title", "dev_account",
    "buyer_id", "stars", "rated_utc", "replied", "reply_id", "replied_utc",
    "reply_text", "latency_seconds",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_market", "sec_sellers",
    "sec_law", "sec_disc", "sec_rep",
    "kpi_ratings", "kpi_replied", "kpi_unreplied", "kpi_coverage", "kpi_avg",
    "kpi_median", "kpi_fastest", "kpi_slowest", "kpi_latest", "kpi_oldest",
    "kpi_market_coverage",
    "col_rating", "col_listing", "col_title", "col_buyer", "col_stars",
    "col_rated", "col_replied", "col_replied_utc", "col_latency",
    "col_text", "col_bar",
    "badge_replied", "badge_pending", "empty_scope", "none",
    "law_count", "law_split", "law_coverage", "law_avg", "law_median",
    "law_extremes", "law_stamps", "law_row", "law_order", "law_scope",
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
.bar{position:relative;height:9px;background:#eef1f5;border-radius:999px;
min-width:110px}
.bar i{display:block;height:9px;border-radius:999px;background:#4f7cac}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.owed{border-color:#c3a0a8;color:#8c4a5c}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_RRLB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_RRLB_LAW"


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
    tmp_root = tempfile.mkdtemp(prefix="reply-latency-board-")
    db = os.path.join(tmp_root, "reply-latency-board.db")
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
                                % (row.get("rating_id"), ",".join(missing)))
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    return market, sellers, disclaimer


def _close(left, right):
    if left is None or right is None:
        return left is None and right is None
    return abs(float(left) - float(right)) <= 1e-9


def elapsed(rated, replied):
    """The face's own latency: two stored stamps, never a wall clock."""
    if replied is None:
        return None
    start = datetime.datetime.strptime(str(rated), STAMP_FMT)
    end = datetime.datetime.strptime(str(replied), STAMP_FMT)
    return int((end - start).total_seconds())


def _want_median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _envelope_problems(envelope, label):
    """AC-RRLB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["rows"]
    count = int(envelope["rating_count"])
    answered = [row for row in rows if row["latency_seconds"] is not None]
    pending = [row for row in rows if row["latency_seconds"] is None]
    replied = int(envelope["replied_count"])
    if count != len(rows):
        problems.append("%s rating_count != rows" % label)
    if replied != len(answered):
        problems.append("%s replied_count != answered rows" % label)
    if int(envelope["unreplied_count"]) != count - replied:
        problems.append("%s unreplied_count != count - replied" % label)
    want_coverage = (round(float(replied) / count, 4) if count else None)
    if not _close(envelope["reply_coverage"], want_coverage):
        problems.append("%s reply_coverage %r != %r"
                        % (label, envelope["reply_coverage"], want_coverage))

    latencies = [int(row["latency_seconds"]) for row in answered]
    want_fastest = min(latencies) if latencies else None
    want_slowest = max(latencies) if latencies else None
    want_avg = (float(sum(latencies)) / len(latencies)) if latencies else None
    want_median = _want_median(latencies)
    if not _close(envelope["fastest_seconds"], want_fastest):
        problems.append("%s fastest_seconds %r != %r"
                        % (label, envelope["fastest_seconds"], want_fastest))
    if not _close(envelope["slowest_seconds"], want_slowest):
        problems.append("%s slowest_seconds %r != %r"
                        % (label, envelope["slowest_seconds"], want_slowest))
    if not _close(envelope["avg_seconds"], want_avg):
        problems.append("%s avg_seconds %r != %r"
                        % (label, envelope["avg_seconds"], want_avg))
    if not _close(envelope["median_seconds"], want_median):
        problems.append("%s median_seconds %r != %r"
                        % (label, envelope["median_seconds"], want_median))

    stamps = [str(row["replied_utc"]) for row in answered]
    owed = [str(row["rated_utc"]) for row in pending]
    want_latest = max(stamps) if stamps else None
    want_oldest = min(owed) if owed else None
    if envelope["latest_reply_utc"] != want_latest:
        problems.append("%s latest_reply_utc %r != %r"
                        % (label, envelope["latest_reply_utc"], want_latest))
    if envelope["oldest_unreplied_utc"] != want_oldest:
        problems.append("%s oldest_unreplied_utc %r != %r"
                        % (label, envelope["oldest_unreplied_utc"],
                           want_oldest))

    for row in rows:
        tag = "%s/%s" % (label, row["rating_id"])
        if bool(row["replied"]) != (row["replied_utc"] is not None):
            problems.append("%s replied flag vs stamp" % tag)
        if bool(row["replied"]) != (row["reply_id"] is not None):
            problems.append("%s replied flag vs reply_id" % tag)
        if row["replied"] and row["latency_seconds"] is None:
            problems.append("%s answered row has no latency" % tag)
        if not row["replied"] and row["latency_seconds"] is not None:
            problems.append("%s pending row carries a latency" % tag)
        if row["replied"]:
            want = elapsed(row["rated_utc"], row["replied_utc"])
            if int(row["latency_seconds"]) != want:
                problems.append("%s latency %r != %r"
                                % (tag, row["latency_seconds"], want))

    def order(row):
        if row["latency_seconds"] is not None:
            return (0, -int(row["latency_seconds"]), int(row["rating_id"]))
        return (1, str(row["rated_utc"]), int(row["rating_id"]))
    if [order(row) for row in rows] != sorted(order(row) for row in rows):
        problems.append("%s rows are not in the face's own order" % label)
    return problems


def check_laws(market, sellers):
    problems = _envelope_problems(market, "market")
    if market["dev_account"] is not None:
        problems.append("market envelope carries a dev_account")
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s is not a seller account" % name)
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(envelope, labels, e, dash, market_coverage=None):
    items = [
        (labels["kpi_ratings"], fmt(envelope["rating_count"], dash)),
        (labels["kpi_replied"], fmt(envelope["replied_count"], dash)),
        (labels["kpi_unreplied"], fmt(envelope["unreplied_count"], dash)),
        (labels["kpi_coverage"], fmt(envelope["reply_coverage"], dash)),
        (labels["kpi_avg"], fmt(envelope["avg_seconds"], dash)),
        (labels["kpi_median"], fmt(envelope["median_seconds"], dash)),
        (labels["kpi_fastest"], fmt(envelope["fastest_seconds"], dash)),
        (labels["kpi_slowest"], fmt(envelope["slowest_seconds"], dash)),
        (labels["kpi_latest"], fmt(envelope["latest_reply_utc"], dash)),
        (labels["kpi_oldest"], fmt(envelope["oldest_unreplied_utc"], dash)),
    ]
    if market_coverage is not None:
        items.append((labels["kpi_market_coverage"],
                      fmt(market_coverage, dash)))
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def rows_table(envelope, labels, e, dash):
    head = (labels["col_rating"], labels["col_listing"], labels["col_title"],
            labels["col_buyer"], labels["col_stars"], labels["col_rated"],
            labels["col_replied"], labels["col_replied_utc"],
            labels["col_latency"], labels["col_text"], labels["col_bar"])
    right = {labels["col_rating"], labels["col_stars"],
             labels["col_latency"]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    answered = [row["latency_seconds"] for row in envelope["rows"]
                if row["latency_seconds"] is not None]
    peak = max(int(value) for value in answered) if answered else 0
    body = []
    for row in envelope["rows"]:
        latency = row["latency_seconds"]
        if latency is None:
            bar = '<span class=empty>%s</span>' % e(dash)
            state = ('<span class="badge owed">%s</span>'
                     % e(labels["badge_pending"]))
        else:
            width = (float(int(latency)) / peak * 100.0) if peak else 100.0
            width = max(0.0, min(100.0, width))
            bar = '<div class=bar><i style="width:%.1f%%"></i></div>' % width
            state = ('<span class="badge">%s</span>'
                     % e(labels["badge_replied"]))
        cells = [
            ("n", fmt(row["rating_id"], dash)),
            ("", fmt(row["listing_key"], dash)),
            ("", fmt(row["title"], dash)),
            ("", fmt(row["buyer_id"], dash)),
            ("n", fmt(row["stars"], dash)),
            ("", fmt(row["rated_utc"], dash)),
            ("", state),
            ("", fmt(row["replied_utc"], dash)),
            ("n", fmt(latency, dash)),
            ("", fmt(row["reply_text"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(str(value)))
                      for klass, value in cells)
        tds += "<td class=bar-cell>%s</td>" % bar
        body.append('<tr class="%s" data-rating="%s">%s</tr>'
                    % ("answered" if latency is not None else "pending",
                       e(str(row["rating_id"])), tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, market, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash,
                        market_coverage=market["reply_coverage"]),
               rows_table(block, labels, e, dash)))


def build_html(market, sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_split"], labels["law_coverage"],
            labels["law_avg"], labels["law_median"], labels["law_extremes"],
            labels["law_stamps"], labels["law_row"], labels["law_order"],
            labels["law_scope"], labels["law_bar"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])),
           seller_section(block, market, labels, e, dash))
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
           sections or ('<div class=card data-seller-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_scope"])),
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
    """AC-PWC68 (R3590): landing this pair and re-deriving the CEO face are ONE run.

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
        print("REPLY-LATENCY CHECK %s fails=%d html=%dB json=%dB"
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

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(market, sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "source_face": SOURCE_FACE,
        "scope": "market",
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

    print("REPLY-LATENCY %s bytes=%d sellers=%d ratings=%d replied=%d "
          "owed=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"], payload["market"]["rating_count"],
             payload["market"]["replied_count"],
             payload["market"]["unreplied_count"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
