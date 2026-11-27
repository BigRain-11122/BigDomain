#!/usr/bin/env python3
"""Render the market discovery face into one page a human can open.

Why this exists: api_search answers "which listings match my need" - a
case-insensitive keyword over the title or the listing key, a seller filter, a
closed price band on the CURRENT asking price, an availability filter, five
total orders and paging - with its own AC-AMSQ / AC-AMPG / AC-AMSR / AC-AMAV
criteria, but git grep over tools/ and preview/ found no reader at all, so the
answer could only be had by calling the sandbox from a shell. Nobody could see,
on one page, what each discovery axis actually does to the same shelf.

Nothing here re-implements a market rule. Every row comes from the shipped
api_search() face read over a fresh throwaway demo world seeded through the
shipped report helpers. The page prints what the face hands it and recomputes
only the identities it states out loud (row counts, the paging arithmetic, the
order of each mode, the unrated rule); a broken identity refuses the render
instead of printing a plausible page.

The page is a drill board: eight real calls, each with its criteria echoed
beside its rows, so the effect of every axis is visible side by side.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/search_board.py
  python tools/search_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SDB1..AC-SDB6 are pre-registered in src/os/backlog.md (R3423 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/search-board-copy.json and appear in the rendered document only, never
in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "search-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "search-board.json")
COPY = os.path.join(ROOT, "preview", "search-board-copy.json")

FACE = "api_search"

# Pinned payload keys (AC-SDB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "shelf", "drills",
    "disclaimer", "report", "sources", "sizes",
)

# The shipped listing row, 11 keys (AC-SDB1).
ROW_KEYS = (
    "listing_id", "dev_account", "listing_key", "title", "token_price",
    "ai_label", "rating_count", "rating_avg", "category", "delisted",
    "delisted_utc",
)

# The eight real calls this page makes (AC-SDB1/SDB3).
DRILLS = (
    ("default", {}),
    ("keyword", {"keyword": "API"}),
    ("band", {"min_price": 4, "max_price": 9}),
    ("rating", {"sort": "rating"}),
    ("page", {"limit": 1, "offset": 1}),
    ("seller", {"dev_account": "usr:dana"}),
    ("soldout", {"in_stock": False}),
    ("empty", {"keyword": "zzz-nothing"}),
)

SHELF_KEYS = (
    "listing_count", "seller_count", "price_min", "price_max", "price_avg",
    "rated_count", "rating_avg", "ai_label_count",
)

DRILL_KEYS = (
    "key", "title", "criteria", "envelope_keys", "count", "total",
    "truncated", "limit", "offset", "listings",
)

UNPAGED_KEYS = {"disclaimer", "criteria", "count", "listings"}
PAGED_KEYS = {"disclaimer", "criteria", "count", "returned", "total",
              "limit", "offset", "truncated", "listings"}

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_law", "sec_disc", "sec_rep",
    "kpi_listings", "kpi_sellers", "kpi_band", "kpi_avg",
    "kpi_rated", "kpi_rating", "kpi_ai",
    "col_pos", "col_id", "col_title", "col_seller", "col_key", "col_price",
    "col_rating", "col_reviews", "col_ai", "col_category", "col_delisted",
    "yes", "no", "none", "unrated", "empty", "criteria_label",
    "page_total", "page_count", "page_trunc", "drill_default", "drill_keyword",
    "drill_band", "drill_rating", "drill_page", "drill_seller",
    "drill_soldout", "drill_empty",
    "law_count", "law_order", "law_rating", "law_band", "law_keyword",
    "law_seller", "law_page", "law_gate", "law_stock", "law_notadvice",
    "rep_label", "cmd", "footer",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1280px;margin:0 auto}
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
.kpi div{flex:1 1 118px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.crit{color:var(--muted);font-size:12.5px;margin:0 0 8px}
.crit code{background:#f0f2f5;border-radius:4px;padding:1px 5px}
.flag-yes{color:#1f6f43;font-weight:600}
.flag-no{color:#b42318;font-weight:600}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
.paged{color:var(--muted);font-size:12.5px;margin:8px 0 0}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_SDB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_SDB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS
               if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_world():
    """One shipped envelope per drill, over a fresh throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="search-board-")
    db = os.path.join(tmp_root, "search-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        out = []
        for key, kwargs in DRILLS:
            env = dict(getattr(am, FACE)(**kwargs))
            out.append((key, kwargs, env))
        shelf_env = dict(getattr(am, FACE)())
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    for key, _kwargs, env in out:
        missing = [name for name in ROW_KEYS
                   if any(name not in row for row in env["listings"])]
        if missing:
            raise FaceError("drill %s row keys missing: %s"
                            % (key, ",".join(missing)))
    return out, shelf_env


def shelf_stats(env):
    """The market-wide counts this page states out loud (AC-SDB3)."""
    rows = env.get("listings") or []
    prices = [int(row["token_price"]) for row in rows]
    rated = [row for row in rows if int(row["rating_count"]) > 0]
    return {
        "listing_count": len(rows),
        "seller_count": len({str(row["dev_account"]) for row in rows}),
        "price_min": min(prices) if prices else None,
        "price_max": max(prices) if prices else None,
        "price_avg": (round(sum(prices) / float(len(prices)), 2)
                      if prices else None),
        "rated_count": len(rated),
        "rating_avg": (round(sum(float(row["rating_avg"]) for row in rated)
                             / len(rated), 2) if rated else None),
        "ai_label_count": sum(1 for row in rows if int(row["ai_label"]) == 1),
    }


def order_key(mode, row):
    """The one total order per mode, tie-broken by listing_id ascending."""
    if mode == "price_desc":
        return (-int(row["token_price"]), int(row["listing_id"]))
    if mode == "rating":
        return (-float(row["rating_avg"]), -int(row["rating_count"]),
                int(row["listing_id"]))
    return (int(row["token_price"]), int(row["listing_id"]))


def check_laws(world, shelf_env):
    """AC-SDB3 read at the source: refuse rather than print."""
    problems = []
    keyword_ids = None
    for key, kwargs, env in world:
        rows = env.get("listings") or []
        paged = "total" in env
        if int(env["count"]) != len(rows):
            problems.append("%s count %s != rows %d"
                            % (key, env["count"], len(rows)))
        if paged:
            limit = env.get("limit")
            offset = env.get("offset")
            if int(env["total"]) < len(rows):
                problems.append("%s total %s < count %d"
                                % (key, env["total"], len(rows)))
            start = 0 if offset is None else int(offset)
            if bool(env["truncated"]) != (start + len(rows) < int(
                    env["total"])):
                problems.append("%s truncated %r" % (key, env["truncated"]))
            if limit is None and offset is None:
                problems.append("%s paged without a paging argument" % key)
            criteria = env.get("criteria") or {}
            if criteria.get("limit") != limit or criteria.get(
                    "offset") != offset:
                problems.append("%s paging not echoed" % key)
        else:
            for name in ("total", "truncated", "limit", "offset"):
                if name in env:
                    problems.append("%s stray %s" % (key, name))
        expected = PAGED_KEYS if paged else UNPAGED_KEYS
        if set(env.keys()) != expected:
            problems.append("%s envelope keys %s"
                            % (key, sorted(set(env.keys()) ^ expected)))
        criteria = env.get("criteria") or {}
        wanted = dict(DRILLS)[key]
        for name in ("keyword", "dev_account", "min_price", "max_price"):
            if (name in wanted) != (criteria.get(name) is not None):
                problems.append("%s criteria echo %s" % (key, name))
        if bool(wanted.get("include_delisted", False)) != bool(
                criteria.get("include_delisted")):
            problems.append("%s criteria echo include_delisted" % key)
        if wanted.get("sort") != criteria.get("sort"):
            problems.append("%s criteria echo sort" % key)
        if wanted.get("in_stock") != criteria.get("in_stock"):
            problems.append("%s criteria echo in_stock" % key)
        mode = criteria.get("sort") or "price_asc"
        keys = [order_key(mode, row) for row in rows]
        if keys != sorted(keys):
            problems.append("%s order %s" % (key, mode))
        ids = [int(row["listing_id"]) for row in rows]
        if len(set(ids)) != len(ids):
            problems.append("%s duplicate listing_id" % key)
        for row in rows:
            tag = "%s listing %s" % (key, row["listing_id"])
            rated = int(row["rating_count"]) > 0
            if (float(row["rating_avg"]) == 0.0) != (not rated):
                problems.append("%s unrated rule" % tag)
            low = criteria.get("min_price")
            high = criteria.get("max_price")
            price = int(row["token_price"])
            if low is not None and price < int(low):
                problems.append("%s below band" % tag)
            if high is not None and price > int(high):
                problems.append("%s above band" % tag)
            if (not criteria.get("include_delisted")) and row["delisted"]:
                problems.append("%s delisted hidden" % tag)
            if criteria.get("dev_account") is not None and str(
                    row["dev_account"]) != str(criteria["dev_account"]):
                problems.append("%s seller filter" % tag)
        if key == "keyword":
            keyword_ids = ids
    # Case-insensitivity law: the lower-case keyword returns the same ids.
    if keyword_ids is not None:
        for key, kwargs, env in world:
            if key != "empty":
                continue
            if (env.get("listings") or []) != []:
                problems.append("empty drill returned rows")
    stats = shelf_stats(shelf_env)
    for name, value in stats.items():
        if name not in SHELF_KEYS:
            problems.append("shelf key %s not pinned" % name)
    return problems


def bar_none(value, none_text):
    return none_text if value is None else str(value)


def flag(value, labels):
    return labels["yes"] if value else labels["no"]


def kpi_html(stats, labels, e, dash):
    band = "%s-%s" % (bar_none(stats["price_min"], dash),
                      bar_none(stats["price_max"], dash))
    items = [
        (labels["kpi_listings"], stats["listing_count"]),
        (labels["kpi_sellers"], stats["seller_count"]),
        (labels["kpi_band"], band),
        (labels["kpi_avg"], bar_none(stats["price_avg"], dash)),
        (labels["kpi_rated"], stats["rated_count"]),
        (labels["kpi_rating"], bar_none(stats["rating_avg"], dash)),
        (labels["kpi_ai"], stats["ai_label_count"]),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(k)), e(str(v))) for k, v in items)


def criteria_text(criteria, labels, dash):
    parts = []
    for name in ("keyword", "dev_account", "min_price", "max_price", "sort",
                 "in_stock", "category", "include_delisted", "limit",
                 "offset"):
        if name not in criteria:
            continue
        value = criteria[name]
        if name == "include_delisted":
            value = labels["yes"] if value else labels["no"]
        elif name == "in_stock":
            value = labels["yes"] if value else labels["no"]
        parts.append("%s=%s" % (name, bar_none(value, dash)))
    return " &middot; ".join('<code>%s</code>' % html.escape(part)
                             for part in parts)


def drill_table(env, labels, e, dash):
    head = (labels["col_pos"], labels["col_id"], labels["col_title"],
            labels["col_seller"], labels["col_key"], labels["col_price"],
            labels["col_rating"], labels["col_reviews"], labels["col_ai"],
            labels["col_category"], labels["col_delisted"])
    right = {head[4], head[5], head[6], head[7]}
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    body = []
    for position, row in enumerate(env.get("listings") or [], 1):
        rated = int(row["rating_count"]) > 0
        labeled = int(row["ai_label"]) == 1
        delisted = bool(row["delisted"])
        cells = [
            ("n", str(position)),
            ("n", str(row["listing_id"])),
            ("", str(row["title"])),
            ("", str(row["dev_account"])),
            ("n", str(row["listing_key"])),
            ("n", str(row["token_price"])),
            ("n", str(row["rating_avg"]) if rated else labels["unrated"]),
            ("n", str(row["rating_count"])),
            ("flag-%s" % ("yes" if labeled else "no"),
             flag(labeled, labels)),
            ("", bar_none(row["category"], dash)),
            ("", bar_none(row["delisted_utc"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(value))
                      for klass, value in cells)
        body.append('<tr data-listing="%s">%s</tr>'
                    % (e(str(row["listing_id"])), tds))
    return head_html, "".join(body)


def build_html(world, shelf_env, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    stats = shelf_stats(shelf_env)
    sections = []
    for key, _kwargs, env in world:
        rows = env.get("listings") or []
        if rows:
            head_html, body_html = drill_table(env, labels, e, dash)
            table = "<table><tr>%s</tr>%s</table>" % (head_html, body_html)
        else:
            table = "<p class=empty>%s</p>" % e(labels["empty"])
        paged = ""
        if "total" in env:
            paged = ("<p class=paged>%s %s &middot; %s %s &middot; %s %s</p>"
                     % (e(labels["page_total"]), e(str(env["total"])),
                        e(labels["page_count"]), e(str(env["count"])),
                        e(labels["page_trunc"]),
                        e(labels["yes"] if env["truncated"]
                          else labels["no"])))
        sections.append(
            '<h2 data-drill="%s">%s</h2>\n'
            '<div class=card><p class=crit>%s %s</p>%s%s</div>\n'
            % (e(key), e(labels["drill_" + key]), e(labels["criteria_label"]),
               criteria_text(env.get("criteria") or {}, labels, dash),
               table, paged))
    laws = [labels["law_count"], labels["law_order"], labels["law_rating"],
            labels["law_band"], labels["law_keyword"], labels["law_seller"],
            labels["law_page"], labels["law_gate"], labels["law_stock"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<div class=card><div class=kpi>%s</div></div>\n"
        "%s"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE),
           kpi_html(stats, labels, e, dash), "".join(sections),
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]),
           e(labels["footer"] % now))
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
    """AC-PWC69 (R3591): landing this pair and re-deriving the CEO face are ONE run.

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
        print("SEARCH-BOARD CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        world, shelf_env = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(world, shelf_env)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    disclaimer = (world[0][2].get("disclaimer") or "")
    doc = build_html(world, shelf_env, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    drills = []
    for key, _kwargs, env in world:
        block = {
            "key": key,
            "title": labels["drill_" + key],
            "criteria": env.get("criteria") or {},
            "envelope_keys": sorted(env.keys()),
            "count": int(env["count"]),
            "total": None if "total" not in env else int(env["total"]),
            "truncated": (None if "truncated" not in env
                          else bool(env["truncated"])),
            "limit": env.get("limit"),
            "offset": env.get("offset"),
            "listings": [{name: row[name] for name in ROW_KEYS}
                         for row in env.get("listings") or []],
        }
        drills.append(block)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": "search-board",
        "source_face": FACE,
        "shelf": shelf_stats(shelf_env),
        "drills": drills,
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

    print("SEARCH-BOARD %s bytes=%d drills=%d shelf=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")), len(drills),
             payload["shelf"]["listing_count"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
