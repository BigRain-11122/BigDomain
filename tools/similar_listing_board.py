#!/usr/bin/env python3
"""Render the similar-listing neighbour board into one browsable page.

Why this exists: api_similar_listings shipped with its own AC-AMSI criteria and
answers the buyer's most natural follow-up after opening one listing - "what
else is like this one" - but git grep -F over tools/ and preview/ finds no
reader at all, so the only way to get that answer was to call the sandbox from a
shell. api_board enumerates what is on the shelf and api_listing_position ranks
one listing against its bucket; neither of them lists the neighbours a head
recruits, nor the order the market itself pinned for them.

Nothing here re-implements a market rule. The ids come from the shipped
api_board() face and every number on the page comes from the shipped
api_similar_listings() face read over a fresh throwaway demo world seeded
through the shipped report helpers. The page prints the envelopes it is handed
and never recomputes a neighbour order, a delta or a rating; the only checks it
runs are the face's own published laws, and a broken law refuses the render
instead of printing a plausible page.

The real sandbox is never opened for writing.

Usage:
  python tools/similar_listing_board.py
  python tools/similar_listing_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SNB1..AC-SNB6 are pre-registered in src/os/backlog.md (R3404 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/similar-listing-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "similar-listing-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "similar-listing-board.json")
COPY = os.path.join(ROOT, "preview", "similar-listing-board-copy.json")

FACE = "api_similar_listings"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-SNB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "listing_count", "pair_count",
    "heads", "disclaimer", "report", "sources", "sizes",
)

ROW_KEYS = ("listing_id", "dev_account", "listing_key", "title",
            "current_price", "price_delta", "abs_price_delta", "rating_count",
            "rating_avg", "net_sales", "live", "delisted_utc")

ENV_KEYS = ("listing_id", "category", "live", "delisted_utc", "current_price",
            "include_delisted", "limit", "total", "returned", "truncated",
            "rows")

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_listings", "kpi_pairs", "kpi_empty",
    "kpi_avg", "kpi_buckets", "aigc", "sec_heads", "sec_law", "sec_disc",
    "sec_rep", "col_neighbour", "col_price", "col_delta", "col_absdelta",
    "col_rating", "col_sales", "col_status", "cat_uncat", "live_yes",
    "live_no", "head_label", "none", "law_order", "law_delta", "law_scope",
    "law_unrated", "neighbours_for", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:14px;margin:14px 0 6px;font-weight:600;color:var(--muted)}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 110px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.headline{font-size:13.5px;color:var(--muted);margin:0 0 6px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_SNB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_SNB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_board():
    """Enumerate listing ids and titles from the shipped board, then neighbours."""
    tmp_root = tempfile.mkdtemp(prefix="similar-listing-board-")
    db = os.path.join(tmp_root, "similar-listing-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        heads = []
        for row in board["listings"]:
            listing_id = int(row["listing_id"])
            env = getattr(am, FACE)(listing_id)
            head = dict(env)
            # The neighbour envelope does not carry the head's own title; the
            # board does, so the page takes it from there instead of typing it.
            head["title"] = row["title"]
            heads.append(head)
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
    if not heads:
        raise FaceError("board enumerated zero listings")
    for head in heads:
        for key in ENV_KEYS:
            if key not in head:
                raise FaceError("neighbour keys missing: %s" % key)
        if not isinstance(head["rows"], list):
            raise FaceError("rows is not a list on listing %s"
                            % head["listing_id"])
        for rival in head["rows"]:
            miss = [k for k in ROW_KEYS if k not in rival]
            if miss:
                raise FaceError("row keys missing: %s" % ",".join(miss))
    return heads, disclaimer


def check_laws(heads):
    """AC-SNB3 / AC-SNB4 read at the source: refuse rather than print."""
    problems = []
    for head in heads:
        rows = head["rows"]
        head_id = int(head["listing_id"])
        head_price = int(head["current_price"])
        if int(head["returned"]) != len(rows):
            problems.append("listing %s returned=%s rows=%d"
                            % (head_id, head["returned"], len(rows)))
        if int(head["total"]) < int(head["returned"]):
            problems.append("listing %s total=%s returned=%s"
                            % (head_id, head["total"], head["returned"]))
        truncated = bool(head["truncated"])
        if truncated != (int(head["returned"]) < int(head["total"])):
            problems.append("listing %s truncated=%s with total=%s returned=%s"
                            % (head_id, truncated, head["total"],
                               head["returned"]))
        order = []
        for rival in rows:
            if int(rival["listing_id"]) == head_id:
                problems.append("listing %s appears in its own neighbours"
                                % head_id)
            delta = int(rival["current_price"]) - head_price
            if int(rival["price_delta"]) != delta:
                problems.append("listing %s neighbour %s delta=%s expected=%d"
                                % (head_id, rival["listing_id"],
                                   rival["price_delta"], delta))
            if int(rival["abs_price_delta"]) != abs(delta):
                problems.append("listing %s neighbour %s abs=%s expected=%d"
                                % (head_id, rival["listing_id"],
                                   rival["abs_price_delta"], abs(delta)))
            # The neighbour envelope carries no category of its own, so bucket
            # scope is graded by the suite through api_listing_position on each
            # neighbour instead of guessed from a missing key here.
            order.append((abs(int(rival["price_delta"])),
                          int(rival["current_price"]),
                          int(rival["listing_id"])))
        if order != sorted(order):
            problems.append("listing %s neighbour order=%r" % (head_id, order))
        if len(order) != len(set(order)):
            problems.append("listing %s neighbour order repeats" % head_id)
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def rating_text(row, none_text):
    """An unrated neighbour prints the no-value mark, never the 0.0 stand-in."""
    if int(row.get("rating_count") or 0) == 0:
        return none_text
    return fmt(row.get("rating_avg"), none_text)


def cat_name(head, labels):
    if head["category"] is None:
        return labels["cat_uncat"]
    return str(head["category"])


def build_html(heads, labels, now, disclaimer):
    e = html.escape
    none = labels["none"]
    pairs = sum(len(head["rows"]) for head in heads)
    empty = sum(1 for head in heads if not head["rows"])
    avg = (float(pairs) / len(heads)) if heads else 0.0
    buckets = len(set(head["category"] for head in heads))
    kpi = [
        (labels["kpi_listings"], fmt(len(heads), none)),
        (labels["kpi_pairs"], fmt(pairs, none)),
        (labels["kpi_empty"], fmt(empty, none)),
        (labels["kpi_avg"], fmt(round(avg, 2), none)),
        (labels["kpi_buckets"], fmt(buckets, none)),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                       for k, v in kpi)

    blocks = []
    for head in heads:
        rows_html = []
        for rival in head["rows"]:
            status = labels["live_yes"] if rival["live"] else labels["live_no"]
            rows_html.append(
                '<tr><td>%s &middot; %s</td><td class=n>%s</td>'
                '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
                '<td class=n>%s</td><td>%s</td></tr>'
                % (e(str(rival["listing_id"])), e(str(rival["title"])),
                   e(fmt(rival["current_price"], none)),
                   e(fmt(rival["price_delta"], none)),
                   e(fmt(rival["abs_price_delta"], none)),
                   e(rating_text(rival, none)),
                   e(fmt(rival["net_sales"], none)), e(status)))
        head_status = labels["live_yes"] if head["live"] else labels["live_no"]
        blocks.append(
            "<h3>%s %s &middot; %s</h3>"
            "<p class=headline>%s %s &middot; %s &middot; %s %s</p>"
            "<table><tr><th>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th>%s</th></tr>%s</table>"
            % (e(labels["neighbours_for"]), e(str(head["listing_id"])),
               e(str(head["title"])),
               e(labels["head_label"]), e(head_status),
               e(cat_name(head, labels)), e(labels["kpi_pairs"]),
               e(fmt(head["returned"], none)),
               e(labels["col_neighbour"]), e(labels["col_price"]),
               e(labels["col_delta"]), e(labels["col_absdelta"]),
               e(labels["col_rating"]), e(labels["col_sales"]),
               e(labels["col_status"]), "".join(rows_html)))

    laws = [labels["law_order"], labels["law_delta"], labels["law_scope"],
            labels["law_unrated"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/similar_listing_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_heads"]), "".join(blocks),
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
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
        print("SIMILAR CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        heads, disclaimer = read_board()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(heads)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(heads, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "listing_count": len(heads),
        "pair_count": sum(len(head["rows"]) for head in heads),
        "heads": heads,
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

    print("SIMILAR %s bytes=%d heads=%d pairs=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["listing_count"], payload["pair_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
