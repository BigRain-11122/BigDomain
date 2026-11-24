#!/usr/bin/env python3
"""Render the buyer monthly refund board into one browsable page.

Why this exists: api_buyer_refund_months answers how much money came back to a
resident month by month, which month carried the refunds and whether a refund
landed in the purchase month or in a later one, with its own AC-BRM criteria -
but git grep over tools/ and preview/ found no page reader at all, so the only
way to read it was to call the sandbox from a shell.

Nothing here re-implements a market rule. Buyers are enumerated from the shipped
api_board()/api_sales()/api_ratings() faces and every number comes from the
shipped api_buyer_refund_months() face read over a fresh throwaway demo world
seeded through the shipped report helpers. The page prints the envelopes it is
handed and never recomputes a count, a total or an average; the only checks it
runs are the face's own published laws, and a broken law refuses the render
instead of printing a plausible page.

A buyer with no refund at all answers an honest empty envelope: that page states
the absence instead of inventing a zero month.

The real sandbox is never opened for writing.

Usage:
  python tools/buyer_refund_months_board.py
  python tools/buyer_refund_months_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BRFM1..AC-BRFM6 are pre-registered in src/os/backlog.md (R3417 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-refund-months-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-refund-months-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-refund-months-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-refund-months-board-copy.json")

FACE = "api_buyer_refund_months"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_sales"

# Pinned payload keys (AC-BRFM1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
)

BUYER_KEYS = ("buyer_id", "scope", "month_count", "active_month_count",
              "refund_count", "refunded", "dev_refunded", "platform_refunded",
              "listing_count", "seller_count", "avg_refund_amount",
              "same_month_count", "largest_refund", "peak_month",
              "peak_refund_count", "first_month", "last_month",
              "latest_month_refund_count", "latest_month_refunded", "months",
              "disclaimer")

MONTH_KEYS = ("month", "refund_count", "refunded", "dev_refunded",
              "platform_refunded", "listing_count", "seller_count",
              "avg_refund_amount", "same_month_count", "running_refund_count")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_buyers", "sec_law", "sec_disc",
    "sec_rep", "col_month", "col_refunds", "col_refunded", "col_dev",
    "col_plat", "col_listings", "col_sellers", "col_avg", "col_same",
    "col_running", "col_bar", "kpi_months", "kpi_active", "kpi_refunds",
    "kpi_refunded", "kpi_dev", "kpi_plat", "kpi_avg", "kpi_same",
    "kpi_largest", "kpi_peak", "none", "no_months", "law_booking",
    "law_grid", "law_split", "law_running", "law_pooled", "law_distinct",
    "law_notadvice", "bar_note", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{height:8px;background:#e8ecf1;border-radius:4px;min-width:90px}
.bar i{display:block;height:8px;background:#2f7d5d;border-radius:4px}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
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

    code = "E_BRFM_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_BRFM_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_buyers():
    """Read one envelope per buyer the shipped faces enumerate."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-refund-months-board-")
    db = os.path.join(tmp_root, "buyer-refund-months-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        seen = set()
        for dev in sorted(set(str(row["dev_account"])
                              for row in board["listings"])):
            for row in (dict(getattr(am, SOURCE_FACE)(dev)).get("sales")
                        or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        for listing in board["listings"]:
            for row in (dict(am.api_ratings(listing["listing_id"]))
                        .get("ratings") or []):
                if row.get("buyer_id"):
                    seen.add(str(row["buyer_id"]))
        blocks = [dict(getattr(am, FACE)(buyer)) for buyer in sorted(seen)]
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
    for block in blocks:
        missing = [key for key in BUYER_KEYS if key not in block]
        if missing:
            raise FaceError("buyer keys missing on %r: %s"
                            % (block.get("buyer_id"), ",".join(missing)))
        if not isinstance(block["months"], list):
            raise FaceError("months is not a list on %r"
                            % (block.get("buyer_id"),))
        for row in block["months"]:
            miss = [key for key in MONTH_KEYS if key not in row]
            if miss:
                raise FaceError("month keys missing: %s" % ",".join(miss))
    return blocks, disclaimer


def check_laws(blocks):
    """AC-BRFM3 read at the source: refuse rather than print."""
    problems = []
    for block in blocks:
        name = str(block["buyer_id"])
        months = block["months"]
        if int(block["month_count"]) != len(months):
            problems.append("%s month_count=%s months=%d"
                            % (name, block["month_count"], len(months)))
        active = sum(1 for row in months if int(row["refund_count"]) > 0)
        if int(block["active_month_count"]) != active:
            problems.append("%s active_month_count=%s expected=%d"
                            % (name, block["active_month_count"], active))
        for key in ("refund_count", "refunded", "dev_refunded",
                    "platform_refunded"):
            got = sum(int(row[key]) for row in months)
            if got != int(block[key]):
                problems.append("%s sum(%s)=%d envelope=%s"
                                % (name, key, got, block[key]))
        if (int(block["refunded"]) != int(block["dev_refunded"])
                + int(block["platform_refunded"])):
            problems.append("%s envelope split is not the two legs" % name)
        running = 0
        for row in months:
            if int(row["refunded"]) != (int(row["dev_refunded"])
                                        + int(row["platform_refunded"])):
                problems.append("%s %s split is not the two legs"
                                % (name, row["month"]))
            if int(row["listing_count"]) != int(row["refund_count"]):
                problems.append("%s %s listing_count != refund_count"
                                % (name, row["month"]))
            if int(row["seller_count"]) > int(row["refund_count"]):
                problems.append("%s %s seller_count > refund_count"
                                % (name, row["month"]))
            count = int(row["refund_count"])
            avg = row["avg_refund_amount"]
            if count == 0:
                if avg is not None:
                    problems.append("%s %s zero month has an average"
                                    % (name, row["month"]))
            else:
                if avg is None or round(float(row["refunded"]) / count, 2) != avg:
                    problems.append("%s %s average is not pooled"
                                    % (name, row["month"]))
            if int(row["running_refund_count"]) < running:
                problems.append("%s %s running accumulator fell"
                                % (name, row["month"]))
            running = int(row["running_refund_count"])
        if months and running != int(block["refund_count"]):
            problems.append("%s last running=%d refund_count=%s"
                            % (name, running, block["refund_count"]))
        if int(block["same_month_count"]) > int(block["refund_count"]):
            problems.append("%s same_month_count > refund_count" % name)
        if months:
            if str(block["first_month"]) != str(months[0]["month"]):
                problems.append("%s first_month is not the first row" % name)
            if str(block["last_month"]) != str(months[-1]["month"]):
                problems.append("%s last_month is not the last row" % name)
        names = [str(row["month"]) for row in months]
        if names != sorted(names):
            problems.append("%s months not ascending: %r" % (name, names))
        for row in months:
            month = str(row["month"])
            if len(month) != 7 or month[4] != "-":
                problems.append("%s bad month shape: %r" % (name, month))
        # Peak month is the first active month holding the largest count.
        peak = None
        for row in months:
            if int(row["refund_count"]) > 0 and (
                    peak is None
                    or int(row["refund_count"]) > int(peak["refund_count"])):
                peak = row
        if peak is None:
            if block["peak_month"] is not None:
                problems.append("%s peak_month on an empty envelope" % name)
        elif str(block["peak_month"]) != str(peak["month"]):
            problems.append("%s peak_month=%r expected=%r"
                            % (name, block["peak_month"], peak["month"]))
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    return str(value)


def kpi_html(block, labels, e):
    items = [
        (labels["kpi_months"], fmt(block["month_count"], labels["none"])),
        (labels["kpi_active"], fmt(block["active_month_count"],
                                   labels["none"])),
        (labels["kpi_refunds"], fmt(block["refund_count"], labels["none"])),
        (labels["kpi_refunded"], fmt(block["refunded"], labels["none"])),
        (labels["kpi_dev"], fmt(block["dev_refunded"], labels["none"])),
        (labels["kpi_plat"], fmt(block["platform_refunded"], labels["none"])),
        (labels["kpi_avg"], fmt(block["avg_refund_amount"], labels["none"])),
        (labels["kpi_same"], fmt(block["same_month_count"], labels["none"])),
        (labels["kpi_largest"], fmt(block["largest_refund"], labels["none"])),
        (labels["kpi_peak"], fmt(block["peak_month"], labels["none"])),
    ]
    return "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                   for k, v in items)


def month_cells(row, labels):
    return (str(row["month"]), fmt(row["refund_count"], labels["none"]),
            fmt(row["refunded"], labels["none"]),
            fmt(row["dev_refunded"], labels["none"]),
            fmt(row["platform_refunded"], labels["none"]),
            fmt(row["listing_count"], labels["none"]),
            fmt(row["seller_count"], labels["none"]),
            fmt(row["avg_refund_amount"], labels["none"]),
            fmt(row["same_month_count"], labels["none"]),
            fmt(row["running_refund_count"], labels["none"]))


def refund_bar(row, blocks):
    """A width, not a share: scaled against the largest refunded here."""
    amounts = [int(item["refunded"]) for block in blocks
               for item in block["months"]] or [1]
    scale = max(amounts) or 1
    width = int(round(100.0 * int(row["refunded"]) / float(scale)))
    return ('<div class="bar" title="%s"><i style="width:%d%%"></i></div>'
            % (html.escape(str(row["refunded"])), width))


def build_html(blocks, labels, now, disclaimer):
    e = html.escape
    head = (labels["col_month"], labels["col_refunds"],
            labels["col_refunded"], labels["col_dev"], labels["col_plat"],
            labels["col_listings"], labels["col_sellers"], labels["col_avg"],
            labels["col_same"], labels["col_running"], labels["col_bar"])
    head_html = "".join(
        ('<th>%s</th>' if index == 0 else '<th class=n>%s</th>') % e(cell)
        for index, cell in enumerate(head))

    sections = []
    for block in blocks:
        rows = block["months"]
        if rows:
            body = "".join(
                '<tr class="month"><td>%s</td>%s<td class=n>%s</td></tr>'
                % (e(month_cells(row, labels)[0]),
                   "".join('<td class=n>%s</td>' % e(cell)
                           for cell in month_cells(row, labels)[1:]),
                   refund_bar(row, blocks))
                for row in rows)
            table = ("<table><tr>%s</tr>%s</table>" % (head_html, body))
        else:
            table = '<p class=empty>%s</p>' % e(labels["no_months"])
        sections.append(
            '<div class=buyer id="buyer-%s"><h2>%s</h2>'
            '<div class=kpi>%s</div><div class=card>%s'
            '<p class=empty>%s</p></div></div>'
            % (e(str(block["buyer_id"])), e(str(block["buyer_id"])),
               kpi_html(block, labels, e), table, e(labels["bar_note"])))

    laws = [labels["law_booking"], labels["law_grid"], labels["law_split"],
            labels["law_running"], labels["law_pooled"],
            labels["law_distinct"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/buyer_refund_months_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_buyers"]),
           "".join(sections), e(labels["sec_law"]), law_html,
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
        print("BUYER-REFUND-MONTHS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        blocks, disclaimer = read_buyers()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(blocks)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(blocks, labels, now, disclaimer)
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

    print("BUYER-REFUND-MONTHS %s bytes=%d buyers=%d months=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"],
             sum(len(b["months"]) for b in blocks)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
