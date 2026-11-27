#!/usr/bin/env python3
"""Render the category-by-month refund timeline into one browsable page.

Why this exists: api_category_refund_months shipped with its own AC-CRM
criteria and answers the question a seller asks before committing to a line of
business - is THIS category's refund load abnormal THIS month - but git grep -F
over tools/ and preview/ finds ZERO readers, so the only way to read it was to
call the sandbox from a shell. api_category_demand sums a category over its
whole life, api_market_months sums the whole market per month and
api_refund_register lists refunds one by one; none of them is a category x month
refund timeline.

Nothing here re-implements a market rule. Every number on the page comes from
src/sandbox/ledger/apimarket.py api_category_refund_months() read over a fresh
throwaway demo world seeded through the shipped report helpers; the page prints
the buckets, the category rows and their month rows it is handed and never
recomputes one. The only arithmetic added here is the visual percentage shown
next to a rate (the face's own fraction times 100), which is stated on the page
as a display conversion, not as a rate the face does not publish.

The real sandbox is never opened for writing.

Usage:
  python tools/category_refund_months.py
  python tools/category_refund_months.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face or the label copy is missing.

AC-CRF1..AC-CRF6 are pre-registered in src/os/backlog.md (R3402 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/category-refund-months-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "category-refund-months.html")
OUT_JSON = os.path.join(ROOT, "preview", "category-refund-months.json")
COPY = os.path.join(ROOT, "preview", "category-refund-months-copy.json")

FACE = "api_category_refund_months"

# Pinned envelope keys (AC-CRF1). A missing one is a contract break rather
# than a silent blank on the page.
PINNED_KEYS = (
    "include_uncategorized", "category_count", "month_count", "trade_count",
    "gross", "refund_count", "refunded", "net", "refund_rate",
    "worst_refund_month", "worst_refund_rate", "top_refund_month",
    "categories", "disclaimer",
)

# Pinned payload keys (AC-CRF1): the envelope plus the two blocks the --check
# gate reads and the page's own provenance line.
PAYLOAD_KEYS = (
    "generated_utc", "face", "include_uncategorized", "category_count",
    "month_count", "trade_count", "gross", "refund_count", "refunded", "net",
    "refund_rate", "worst_refund_month", "worst_refund_rate",
    "top_refund_month", "categories", "disclaimer", "report", "sources",
    "sizes",
)

CATEGORY_KEYS = (
    "category", "gross", "refund_count", "refunded", "net", "refund_rate",
    "trade_count", "months",
)

MONTH_KEYS = ("month", "gross", "refund_count", "refunded", "net",
              "refund_rate")

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_categories", "kpi_months", "kpi_trades",
    "kpi_gross", "kpi_refunded", "kpi_net", "kpi_rate", "kpi_refunds",
    "sec_categories", "sec_months", "sec_law", "sec_disc", "sec_rep",
    "col_category", "col_gross", "col_refunded", "col_net", "col_rate",
    "col_refunds", "col_trades", "col_month", "cat_uncat", "none", "aigc",
    "law_cash", "law_undefined", "law_top", "law_worst", "law_unit",
    "rep", "cmd",
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
tr.net td.neg{color:#a4373a;font-weight:600}
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
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""


DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, or the label copy, is missing."""

    code = "E_CRF_FACE"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_face():
    """Build the demo world in a private dir and read the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="category-refund-months-")
    db = os.path.join(tmp_root, "category-refund-months.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        env = getattr(am, FACE)()
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    missing = [key for key in PINNED_KEYS if key not in env]
    if missing:
        raise FaceError("pinned keys missing: %s" % ",".join(missing))
    rows = env.get("categories")
    if not isinstance(rows, list):
        raise FaceError("categories is not a list: %r" % (rows,))
    for row in rows:
        miss = [k for k in CATEGORY_KEYS if k not in row]
        if miss:
            raise FaceError("category row keys missing: %s" % ",".join(miss))
        for month in row["months"]:
            miss = [k for k in MONTH_KEYS if k not in month]
            if miss:
                raise FaceError("month row keys missing: %s" % ",".join(miss))
    return env


def ordered(env):
    """AC-CRF4 read at the source: months ascend and uncategorized is last."""
    for row in env["categories"]:
        names = [m["month"] for m in row["months"]]
        if names != sorted(names):
            return "months not ascending in %r" % (names,)
    cats = [row["category"] for row in env["categories"]]
    named = [c for c in cats if c is not None]
    if named != sorted(named):
        return "categories not ascending: %r" % (cats,)
    if None in cats and cats[-1] is not None:
        return "uncategorized bucket is not last: %r" % (cats,)
    return ""


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def pct(value):
    """Display only: the face's own fraction times 100, rounded to 1 dp."""
    if value is None:
        return None
    return round(float(value) * 100.0, 1)


def cat_name(row, labels):
    if row["category"] is None:
        return labels["cat_uncat"]
    return str(row["category"])


def build_html(env, labels, now):
    e = html.escape
    none = labels["none"]
    kpi = [
        (labels["kpi_categories"], fmt(env["category_count"], none)),
        (labels["kpi_months"], fmt(env["month_count"], none)),
        (labels["kpi_trades"], fmt(env["trade_count"], none)),
        (labels["kpi_gross"], fmt(env["gross"], none)),
        (labels["kpi_refunded"], fmt(env["refunded"], none)),
        (labels["kpi_net"], fmt(env["net"], none)),
        (labels["kpi_rate"], fmt(pct(env["refund_rate"]), none)),
        (labels["kpi_refunds"], fmt(env["refund_count"], none)),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                       for k, v in kpi)

    cat_rows = []
    for row in env["categories"]:
        neg = int(row["net"]) < 0
        cat_rows.append(
            '<tr class=net><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class="n%s">%s</td><td class=n>%s</td><td class=n>%s</td>'
            "<td class=n>%s</td></tr>"
            % (e(cat_name(row, labels)),
               e(fmt(row["gross"], none)),
               e(fmt(row["refunded"], none)),
               " neg" if neg else "",
               e(fmt(row["net"], none)),
               e(fmt(pct(row["refund_rate"]), none)),
               e(fmt(row["refund_count"], none)),
               e(fmt(row["trade_count"], none))))
    cats_table = (
        "<table><tr><th>%s</th><th class=n>%s</th><th class=n>%s</th>"
        "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
        "<th class=n>%s</th></tr>%s</table>"
        % (e(labels["col_category"]), e(labels["col_gross"]),
           e(labels["col_refunded"]), e(labels["col_net"]),
           e(labels["col_rate"]), e(labels["col_refunds"]),
           e(labels["col_trades"]), "".join(cat_rows)))

    blocks = []
    for row in env["categories"]:
        month_rows = []
        for month in row["months"]:
            neg = int(month["net"]) < 0
            # A refund-only month has gross 0, so the face reports its rate as
            # None; the page prints the no-value mark and the standing law
            # sentence says why, instead of printing a fake 0%.
            month_rows.append(
                '<tr class=net><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
                '<td class="n%s">%s</td><td class=n>%s</td><td class=n>%s</td>'
                "</tr>"
                % (e(str(month["month"])),
                   e(fmt(month["gross"], none)),
                   e(fmt(month["refunded"], none)),
                   " neg" if neg else "",
                   e(fmt(month["net"], none)),
                   e(fmt(pct(month["refund_rate"]), none)),
                   e(fmt(month["refund_count"], none))))
        blocks.append(
            "<h3>%s</h3><table><tr><th>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th></tr>%s</table>"
            % (e(cat_name(row, labels)), e(labels["col_month"]),
               e(labels["col_gross"]), e(labels["col_refunded"]),
               e(labels["col_net"]), e(labels["col_rate"]),
               e(labels["col_refunds"]), "".join(month_rows)))
    months_html = "".join(blocks) if blocks else "<p>%s</p>" % e(
        labels["kpi_months"] + ": " + fmt(env["month_count"], none))

    law = [
        "%s: %s" % (e(labels["law_cash"]), e(labels["law_unit"])),
        "%s: %s" % (e(labels["law_undefined"]), e(labels["law_unit"])),
        "%s: <b>%s</b> &middot; %s" % (
            e(labels["law_top"]),
            e(fmt(env["top_refund_month"], none)),
            e(fmt(env["refunded"], none))),
        "%s: <b>%s</b> &middot; %s" % (
            e(labels["law_worst"]),
            e(fmt(env["worst_refund_month"], none)),
            e(fmt(pct(env["worst_refund_rate"]), none))),
    ]
    law_html = "".join('<p class=law>%s</p>' % line for line in law)

    head = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        "<p style=\"margin-top:10px\"><span class=badge>%s</span></p></div>\n"
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/category_refund_months.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_categories"]), cats_table,
           e(labels["sec_months"]), months_html,
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT,
           e(labels["aigc"]), e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
    return head.replace(DISCLAIMER_SLOT, e(env["disclaimer"]))


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
    """AC-PWC48 (R3570): landing this pair and re-deriving the CEO face are ONE run.

    The one definition lives in src/os/board_face_landing.py, so no second
    writer is kept here. ROOT is passed explicitly, so a private world derives
    that world's face. Refusals are named, never raised: both halves are
    already on disk when this runs, so the caller's exit code stays its own.
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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("REFUND CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json) else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        env = read_face()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problem = ordered(env)
    if problem:
        sys.stderr.write("E_CRF_ORDER: %s\n" % problem)
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, labels, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "include_uncategorized": env["include_uncategorized"],
        "category_count": env["category_count"],
        "month_count": env["month_count"],
        "trade_count": env["trade_count"],
        "gross": env["gross"],
        "refund_count": env["refund_count"],
        "refunded": env["refunded"],
        "net": env["net"],
        "refund_rate": env["refund_rate"],
        "worst_refund_month": env["worst_refund_month"],
        "worst_refund_rate": env["worst_refund_rate"],
        "top_refund_month": env["top_refund_month"],
        "categories": env["categories"],
        "disclaimer": env["disclaimer"],
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

    print("REFUND %s bytes=%d categories=%d months=%d trades=%d gross=%s "
          "refunded=%s net=%s face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["category_count"], env["month_count"], env["trade_count"],
             fmt(env["gross"], "-"), fmt(env["refunded"], "-"),
             fmt(env["net"], "-"), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
