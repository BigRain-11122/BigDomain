#!/usr/bin/env python3
"""Render the monthly buyer cohort (new versus returning) into one page.

Why this exists: api_market_buyer_cohort answers the question an operator
asks every month - "of the buyers who paid this month, how many are first
timers and how many came back" - with its own AC-MBC1..8 criteria, but git
grep over tools/ and preview/ found no reader at all, so the cohort could
only be read by calling the sandbox from a shell. The daily calendar shows
money, the concentration ladder shows who matters, the revenue months show
a seller's own months; none of them separates a first-time buyer from a
resident who returned in the same month.

Nothing here re-implements a market rule. Every number comes from the
shipped api_market_buyer_cohort() face read over a fresh throwaway demo
world seeded through the shipped report helpers. The page prints the
envelope it is handed and never recomputes a total; the only checks it runs
are the face's own published laws, and a broken law refuses the render
instead of printing a plausible page.

A world with zero returning buyers is a real reading, so the page prints an
explicit "nobody came back this month" sentence instead of a silent zero.
An empty world is proved by the suite handing the renderer its own envelope;
nothing synthetic is added to the landed page.

The real sandbox is never opened for writing.

Usage:
  python tools/buyer_cohort_board.py
  python tools/buyer_cohort_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-MBCB1..AC-MBCB6 are pre-registered in src/os/backlog.md (R3413 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-cohort-copy.json and appear in the rendered document only,
never in this file.
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_DIR = os.path.join(ROOT, "src", "sandbox", "ledger")
sys.path.insert(0, LEDGER_DIR)

import apimarket_report as R  # noqa: E402

OUT_HTML = os.path.join(ROOT, "preview", "buyer-cohort.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-cohort.json")
COPY = os.path.join(ROOT, "preview", "buyer-cohort-copy.json")

FACE = "api_market_buyer_cohort"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-MBCB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "month_count", "cohort",
    "disclaimer", "report", "sources", "sizes",
)

ENVELOPE_KEYS = (
    "month_count", "purchase_count", "gross", "buyer_count",
    "repeat_buyer_count", "repeat_rate", "returning_purchase_count",
    "first_month", "last_month", "disclaimer", "months",
)

ROW_KEYS = (
    "month", "purchase_count", "gross", "buyer_count", "new_buyer_count",
    "returning_buyer_count", "new_purchase_count",
    "returning_purchase_count", "avg_purchases_per_buyer",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_months", "sec_split", "sec_law",
    "sec_disc", "sec_rep", "col_month", "col_purchases", "col_gross",
    "col_buyers", "col_new", "col_returning", "col_newpurch", "col_retpurch",
    "col_avg", "col_bar", "kpi_months", "kpi_purchases", "kpi_gross",
    "kpi_buyers", "kpi_repeat", "kpi_rate", "kpi_retpurch", "none", "yes",
    "no", "repeat_none", "empty", "bar_note", "split_row", "law_new",
    "law_refund", "law_repeat", "law_norecompute", "law_notadvice", "rep",
    "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1080px;margin:0 auto}
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
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi b.neg{color:#b42318}
.kpi span{color:var(--muted);font-size:12.5px}
.bar{height:7px;background:#eef1f5;border-radius:4px;min-width:90px}
.bar i{display:block;height:7px;background:#3b6ea5;border-radius:4px}
.bar i.ret{background:#c9a227}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.note{color:var(--muted);font-size:12.5px;margin-top:8px}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_MBCB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_MBCB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_cohort():
    """Read the whole cohort envelope over a throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-cohort-board-")
    db = os.path.join(tmp_root, "buyer-cohort-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        envelope = dict(getattr(am, FACE)())
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    missing = [key for key in ENVELOPE_KEYS if key not in envelope]
    if missing:
        raise FaceError("envelope keys missing: %s" % ",".join(missing))
    if not isinstance(envelope["months"], list):
        raise FaceError("months is not a list")
    for row in envelope["months"]:
        miss = [key for key in ROW_KEYS if key not in row]
        if miss:
            raise FaceError("row keys missing on %r: %s"
                            % (row.get("month"), ",".join(miss)))
    return envelope


def check_laws(envelope):
    """AC-MBCB3 read at the source: refuse rather than print."""
    rows = envelope["months"]
    problems = []
    if int(envelope["month_count"]) != len(rows):
        problems.append("month_count=%s rows=%d"
                        % (envelope["month_count"], len(rows)))
    if int(envelope["purchase_count"]) != sum(
            int(row["purchase_count"]) for row in rows):
        problems.append("purchase_count=%s sum=%d"
                        % (envelope["purchase_count"],
                           sum(int(row["purchase_count"]) for row in rows)))
    if int(envelope["gross"]) != sum(int(row["gross"]) for row in rows):
        problems.append("gross=%s sum=%d"
                        % (envelope["gross"],
                           sum(int(row["gross"]) for row in rows)))
    if int(envelope["returning_purchase_count"]) != sum(
            int(row["returning_purchase_count"]) for row in rows):
        problems.append("returning_purchase_count=%s sum=%d"
                        % (envelope["returning_purchase_count"],
                           sum(int(row["returning_purchase_count"])
                               for row in rows)))
    months = [str(row["month"]) for row in rows]
    if months != sorted(months):
        problems.append("months not ascending: %r" % (months,))
    for name in months:
        if not re.match(r"^\d{4}-\d{2}$", name):
            problems.append("month shape %r" % (name,))
    expected_first = months[0] if months else None
    expected_last = months[-1] if months else None
    if envelope["first_month"] != expected_first:
        problems.append("first_month=%r expected=%r"
                        % (envelope["first_month"], expected_first))
    if envelope["last_month"] != expected_last:
        problems.append("last_month=%r expected=%r"
                        % (envelope["last_month"], expected_last))
    for row in rows:
        tag = str(row["month"])
        if int(row["buyer_count"]) != (int(row["new_buyer_count"])
                                       + int(row["returning_buyer_count"])):
            problems.append("%s buyer partition" % tag)
        if int(row["purchase_count"]) != (
                int(row["new_purchase_count"])
                + int(row["returning_purchase_count"])):
            problems.append("%s purchase partition" % tag)
        for key in ("purchase_count", "gross", "buyer_count",
                    "new_buyer_count", "returning_buyer_count",
                    "new_purchase_count", "returning_purchase_count"):
            if int(row[key]) < 0:
                problems.append("%s %s=%s" % (tag, key, row[key]))
        buyers = int(row["buyer_count"])
        avg = row["avg_purchases_per_buyer"]
        if buyers == 0:
            if avg is not None:
                problems.append("%s avg on empty month=%r" % (tag, avg))
        else:
            want = int(row["purchase_count"]) / float(buyers)
            if avg is None or abs(float(avg) - want) > 1e-9:
                problems.append("%s avg=%r expected=%r" % (tag, avg, want))
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(envelope, labels, e):
    rate = envelope["repeat_rate"]
    rate_text = fmt(round(float(rate) * 100.0, 1), labels["none"]) \
        if rate is not None else labels["none"]
    items = [
        (labels["kpi_months"], fmt(envelope["month_count"], labels["none"])),
        (labels["kpi_purchases"],
         fmt(envelope["purchase_count"], labels["none"])),
        (labels["kpi_gross"], fmt(envelope["gross"], labels["none"])),
        (labels["kpi_buyers"], fmt(envelope["buyer_count"], labels["none"])),
        (labels["kpi_repeat"],
         fmt(envelope["repeat_buyer_count"], labels["none"])),
        (labels["kpi_rate"], rate_text),
        (labels["kpi_retpurch"],
         fmt(envelope["returning_purchase_count"], labels["none"])),
    ]
    return "".join(
        '<div><span>%s</span><b%s>%s</b></div>'
        % (e(k), ' class="neg"' if v.startswith("-") else "", e(v))
        for k, v in items)


def split_html(envelope, labels, e):
    """One stacked bar per month: new purchases versus returning ones."""
    rows = envelope["months"]
    if not rows:
        return '<p class="empty">%s</p>' % e(labels["empty"])
    out = []
    for row in rows:
        total = int(row["purchase_count"])
        new = int(row["new_purchase_count"])
        ret = int(row["returning_purchase_count"])
        new_w = 0 if total <= 0 else int(round(new * 100.0 / total))
        ret_w = 0 if total <= 0 else 100 - new_w
        out.append(
            '<p class="split" data-month="%s">%s</p>'
            '<div class="bar"><i style="width:%d%%"></i>'
            '<i class="ret" style="width:%d%%"></i></div>'
            % (e(str(row["month"])),
               e(labels["split_row"].replace("{month}", str(row["month"]))
                 .replace("{new}", str(new)).replace("{ret}", str(ret))
                 .replace("{total}", str(total))),
               new_w, ret_w))
    return "".join(out)


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    head = (labels["col_month"], labels["col_purchases"], labels["col_gross"],
            labels["col_buyers"], labels["col_new"], labels["col_returning"],
            labels["col_newpurch"], labels["col_retpurch"], labels["col_avg"])
    head_html = "".join("<th>%s</th>" % e(cell) for cell in head)
    body = []
    for row in envelope["months"]:
        avg = row["avg_purchases_per_buyer"]
        avg_text = labels["none"] if avg is None else ("%.2f" % float(avg))
        body.append(
            '<tr class="month" data-month="%s"><td>%s</td>'
            "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td></tr>"
            % (e(str(row["month"])), e(str(row["month"])),
               e(str(row["purchase_count"])), e(str(row["gross"])),
               e(str(row["buyer_count"])), e(str(row["new_buyer_count"])),
               e(str(row["returning_buyer_count"])),
               e(str(row["new_purchase_count"])),
               e(str(row["returning_purchase_count"])), e(avg_text)))
    table = ("<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))
             if body else '<p class="empty">%s</p>' % e(labels["empty"]))

    repeat_note = ""
    if int(envelope["repeat_buyer_count"]) == 0:
        repeat_note = '<p class="empty repeat-empty">%s</p>' % e(
            labels["repeat_none"])
    else:
        rate = envelope["repeat_rate"]
        rate_text = labels["none"] if rate is None else str(
            round(float(rate) * 100.0, 1))
        repeat_note = '<p class="note">%s: %s</p>' % (
            e(labels["kpi_rate"]), e(rate_text))

    laws = [labels["law_new"], labels["law_refund"], labels["law_repeat"],
            labels["law_norecompute"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<div class=kpi>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s"
        '<p class=note>%s</p></div>\n'
        "<h2>%s</h2>\n<div class=card>%s%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/buyer_cohort_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html(envelope, labels, e),
           e(labels["sec_months"]), table, e(labels["bar_note"]),
           e(labels["sec_split"]), split_html(envelope, labels, e),
           repeat_note, e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(now))
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
        print("BUYER-COHORT CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope = read_cohort()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(envelope)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(envelope, labels, now, envelope["disclaimer"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "month_count": int(len(envelope["months"])),
        "cohort": envelope,
        "disclaimer": envelope["disclaimer"],
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

    print("BUYER-COHORT %s bytes=%d months=%d purchases=%s buyers=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["month_count"], envelope["purchase_count"],
             envelope["buyer_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
