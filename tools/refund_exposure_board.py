#!/usr/bin/env python3
"""Render the seller refund exposure into one browsable page.

Why this exists: api_refund_exposure answers the two questions an
operator and a seller both ask - "how much of my balance is already
spoken for by refunds I may have to pay back, and which seller would
break a refund today" - with its own AC-RPX1..8 criteria, but git grep
over tools/ and preview/ found no reader at all, so the exposure could
only be read by calling the sandbox from a shell. The other boards show
balances, revenue months, concentration or the daily calendar; none of
them shows the liability standing against a seller's balance.

Nothing here re-implements a market rule. Every number comes from the
shipped api_refund_exposure() face read over a fresh throwaway demo
world seeded through the shipped report helpers. The page prints the
envelope it is handed and never recomputes a total; the only checks it
runs are the face's own published laws, and a broken law refuses the
render instead of printing a plausible page.

A zero at-risk world is a real reading, so the page prints an explicit
"no seller would break a refund today" sentence instead of an empty
section. A shortfall-bearing world is proved by the suite handing the
renderer its own envelope; nothing synthetic is added to the landed page.

The real sandbox is never opened for writing.

Usage:
  python tools/refund_exposure_board.py
  python tools/refund_exposure_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-REX1..AC-REX6 are pre-registered in src/os/backlog.md (R3412 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/refund-exposure-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "refund-exposure.html")
OUT_JSON = os.path.join(ROOT, "preview", "refund-exposure.json")
COPY = os.path.join(ROOT, "preview", "refund-exposure-copy.json")

FACE = "api_refund_exposure"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-REX1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "seller_count", "exposure",
    "disclaimer", "report", "sources", "sizes",
)

ENVELOPE_KEYS = ("dev_account", "seller_count", "total_liability",
                 "total_shortfall", "at_risk_count", "disclaimer", "rows")

ROW_KEYS = ("dev_account", "listing_count", "open_purchases",
            "refunded_purchases", "refundable_liability", "balance",
            "balance_known", "shortfall", "covered")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_ladder", "sec_risk", "sec_law",
    "sec_disc", "sec_rep", "col_seller", "col_listings", "col_open",
    "col_refunded", "col_liability", "col_bar", "col_balance", "col_known",
    "col_shortfall", "col_covered", "kpi_sellers", "kpi_liability",
    "kpi_shortfall", "kpi_atrisk", "none", "yes", "no", "risk_none",
    "risk_row", "bar_note", "law_liability", "law_sum", "law_shortfall",
    "law_zero", "law_retired", "law_unknown", "law_notadvice", "rep",
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

    code = "E_REX_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_REX_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_exposure():
    """Read the whole exposure envelope over a throwaway demo world."""
    tmp_root = tempfile.mkdtemp(prefix="refund-exposure-board-")
    db = os.path.join(tmp_root, "refund-exposure-board.db")
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
    if not isinstance(envelope["rows"], list):
        raise FaceError("rows is not a list")
    for row in envelope["rows"]:
        miss = [key for key in ROW_KEYS if key not in row]
        if miss:
            raise FaceError("row keys missing on %r: %s"
                            % (row.get("dev_account"), ",".join(miss)))
    return envelope


def check_laws(envelope):
    """AC-REX3 read at the source: refuse rather than print."""
    rows = envelope["rows"]
    problems = []
    if int(envelope["seller_count"]) != len(rows):
        problems.append("seller_count=%s rows=%d"
                        % (envelope["seller_count"], len(rows)))
    if int(envelope["total_liability"]) != sum(
            int(row["refundable_liability"]) for row in rows):
        problems.append("total_liability=%s sum=%d"
                        % (envelope["total_liability"],
                           sum(int(row["refundable_liability"])
                               for row in rows)))
    if int(envelope["total_shortfall"]) != sum(
            int(row["shortfall"]) for row in rows):
        problems.append("total_shortfall=%s sum=%d"
                        % (envelope["total_shortfall"],
                           sum(int(row["shortfall"]) for row in rows)))
    if int(envelope["at_risk_count"]) != sum(
            1 for row in rows if int(row["shortfall"]) > 0):
        problems.append("at_risk_count=%s counted=%d"
                        % (envelope["at_risk_count"],
                           sum(1 for row in rows
                               if int(row["shortfall"]) > 0)))
    owners = [str(row["dev_account"]) for row in rows]
    if owners != sorted(owners):
        problems.append("rows not ascending by dev_account: %r" % (owners,))
    for row in rows:
        name = str(row["dev_account"])
        for key in ("listing_count", "open_purchases", "refunded_purchases",
                    "refundable_liability", "shortfall"):
            if int(row[key]) < 0:
                problems.append("%s %s=%s" % (name, key, row[key]))
        expected = int(row["refundable_liability"]) - int(row["balance"])
        if expected < 0:
            expected = 0
        if int(row["shortfall"]) != expected:
            problems.append("%s shortfall=%s expected=%d"
                            % (name, row["shortfall"], expected))
        if bool(row["covered"]) != (int(row["shortfall"]) == 0):
            problems.append("%s covered=%r shortfall=%s"
                            % (name, row["covered"], row["shortfall"]))
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(envelope, labels, e):
    items = [
        (labels["kpi_sellers"], fmt(envelope["seller_count"], labels["none"])),
        (labels["kpi_liability"],
         fmt(envelope["total_liability"], labels["none"])),
        (labels["kpi_shortfall"],
         fmt(envelope["total_shortfall"], labels["none"])),
        (labels["kpi_atrisk"], fmt(envelope["at_risk_count"], labels["none"])),
    ]
    return "".join(
        '<div><span>%s</span><b%s>%s</b></div>'
        % (e(k), ' class="neg"' if v.startswith("-") else "", e(v))
        for k, v in items)


def ladder_rows(envelope, labels):
    rows = envelope["rows"]
    top = max([int(row["refundable_liability"]) for row in rows] or [0])
    out = []
    for row in rows:
        liability = int(row["refundable_liability"])
        width = 0 if top <= 0 else int(round(liability * 100.0 / top))
        out.append((
            str(row["dev_account"]),
            fmt(row["listing_count"], labels["none"]),
            fmt(row["open_purchases"], labels["none"]),
            fmt(row["refunded_purchases"], labels["none"]),
            fmt(liability, labels["none"]),
            width,
            fmt(row["balance"], labels["none"]),
            labels["yes"] if row["balance_known"] else labels["no"],
            fmt(row["shortfall"], labels["none"]),
            labels["yes"] if row["covered"] else labels["no"],
        ))
    return out


def risk_html(envelope, labels, e):
    at_risk = [row for row in envelope["rows"]
               if int(row["shortfall"]) > 0]
    if not at_risk:
        return '<p class="empty risk-empty">%s</p>' % e(labels["risk_none"])
    items = "".join(
        '<p class="risk-row" data-seller="%s">%s</p>'
        % (e(str(row["dev_account"])),
           e(labels["risk_row"].replace("{seller}", str(row["dev_account"]))
             .replace("{shortfall}", str(row["shortfall"]))
             .replace("{liability}", str(row["refundable_liability"]))))
        for row in at_risk)
    return items


def build_html(envelope, labels, now, disclaimer):
    e = html.escape
    head = (labels["col_seller"], labels["col_listings"], labels["col_open"],
            labels["col_refunded"], labels["col_liability"],
            labels["col_bar"], labels["col_balance"], labels["col_known"],
            labels["col_shortfall"], labels["col_covered"])
    head_html = "".join("<th>%s</th>" % e(cell) for cell in head)
    body = []
    for cells in ladder_rows(envelope, labels):
        bars = '<div class="bar"><i style="width:%d%%"></i></div>' % cells[5]
        body.append(
            '<tr class="seller" data-seller="%s"><td>%s</td>'
            "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td>%s</td><td class=n>%s</td>"
            "<td>%s</td><td class=n>%s</td><td>%s</td></tr>"
            % (e(cells[0]), e(cells[0]), e(cells[1]), e(cells[2]),
               e(cells[3]), e(cells[4]), bars, e(cells[6]), e(cells[7]),
               e(cells[8]), e(cells[9])))
    table = ("<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))
             if body else '<p class="empty">%s</p>' % e(labels["none"]))

    laws = [labels["law_liability"], labels["law_sum"],
            labels["law_shortfall"], labels["law_zero"],
            labels["law_retired"], labels["law_unknown"],
            labels["law_notadvice"]]
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
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/refund_exposure_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html(envelope, labels, e),
           e(labels["sec_ladder"]), table, e(labels["bar_note"]),
           e(labels["sec_risk"]), risk_html(envelope, labels, e),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
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
        print("REFUND-EXPOSURE CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        envelope = read_exposure()
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
        "seller_count": int(len(envelope["rows"])),
        "exposure": envelope,
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

    print("REFUND-EXPOSURE %s bytes=%d sellers=%d liability=%s at_risk=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"], envelope["total_liability"],
             envelope["at_risk_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
