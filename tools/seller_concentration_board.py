#!/usr/bin/env python3
"""Render the buyer concentration of net revenue into one browsable page.

Why this exists: api_seller_concentration shipped with its own AC-SBC criteria
and answers the seller's existential question - how many residents is my net
revenue hanging on, how much of it rides on the single biggest one, and what
happens if that one leaves - but the R3409 reader re-measure found ZERO readers
under tools/ and preview/, so the answer could only be read by calling the
sandbox from a shell. api_repeat_purchase counts events, api_seller_quality
grades stars and api_market_daily totals a day; none of them shows the money
weight distribution that this face has always computed.

Nothing here re-implements a market rule. Every number on the page comes from
src/sandbox/ledger/apimarket.py api_seller_concentration() read over a fresh
throwaway demo world seeded through the shipped report helpers; the page prints
the ladder and the totals it is handed and never recomputes one. The only
arithmetic added here is the visual width of a bar (a share over the page's own
total, printed as a width), which the page states as a width, not as a rate.

The real sandbox is never opened for writing.

Usage:
  python tools/seller_concentration_board.py
  python tools/seller_concentration_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face or the label copy is missing.

AC-BCB1..AC-BCB6 are pre-registered in src/os/backlog.md (R3409 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-concentration-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-concentration.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-concentration.json")
COPY = os.path.join(ROOT, "preview", "seller-concentration-copy.json")

FACE = "api_seller_concentration"

# Pinned envelope keys (AC-BCB1). A missing one is a contract break rather than
# a silent blank on the page.
PINNED_KEYS = (
    "dev_account", "scope", "purchase_count", "refund_count", "buyer_count",
    "refunded_buyers", "gross_revenue", "refunded_tokens", "net_revenue",
    "top1_share", "top3_share", "herfindahl", "pareto_buyer_count",
    "market_herfindahl", "buyers", "disclaimer",
)

ROW_KEYS = (
    "buyer_id", "purchase_count", "refund_count", "net_purchase_count",
    "gross_revenue", "refunded_tokens", "net_revenue", "share",
    "cumulative_share", "rank",
)

# Pinned payload keys (AC-BCB1): the envelope plus provenance and the two
# blocks the --check gate reads.
PAYLOAD_KEYS = (
    "generated_utc", "face", "dev_account", "scope", "purchase_count",
    "refund_count", "buyer_count", "refunded_buyers", "gross_revenue",
    "refunded_tokens", "net_revenue", "top1_share", "top3_share", "herfindahl",
    "pareto_buyer_count", "market_herfindahl", "buyers", "disclaimer",
    "report", "sources", "sizes",
)

COPY_KEYS = (
    "title", "sub", "gen", "src",
    "kpi_purchases", "kpi_refunds", "kpi_buyers", "kpi_refunded_buyers",
    "kpi_gross", "kpi_refunded", "kpi_net", "kpi_top1", "kpi_top3",
    "kpi_hhi", "kpi_pareto",
    "sec_scale", "scale_low", "scale_mid", "scale_high", "scale_mark",
    "sec_buyers", "sec_named", "sec_laws", "sec_disc", "sec_rep",
    "col_rank", "col_buyer", "col_purchases", "col_refunds", "col_netcount",
    "col_gross", "col_refunded", "col_net", "col_share", "col_cum",
    "law1", "law2", "law3", "law4", "law5", "law6", "law7",
    "named_pareto", "named_top1", "none", "aigc", "cmd",
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
td.n{text-align:right;font-variant-numeric:tabular-nums}
td.s{text-align:center;color:var(--muted)}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 110px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.track{background:#eef1f5;border-radius:4px;height:10px;min-width:60px}
.fill{background:#3d5a80;height:10px;border-radius:4px;min-width:0}
.scale{position:relative;height:12px;background:#eef1f5;border-radius:6px;
margin:26px 0 6px}
.scale .mark{position:absolute;top:-4px;width:2px;height:20px;background:#b23b3b}
.scale-legend{display:flex;justify-content:space-between;font-size:12px;
color:var(--muted)}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.weak{font-size:14px}
.weak b{font-variant-numeric:tabular-nums}
ol.laws{margin:0;padding-left:20px;font-size:13px;color:#2b3138}
ol.laws li{margin-bottom:4px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""


DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, or the label copy, is missing."""

    code = "E_BCB_FACE"


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
    tmp_root = tempfile.mkdtemp(prefix="seller-concentration-")
    db = os.path.join(tmp_root, "seller-concentration.db")
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
    if not isinstance(env.get("buyers"), list):
        raise FaceError("buyers is not a list: %r" % (env.get("buyers"),))
    for row in env["buyers"]:
        row_missing = [key for key in ROW_KEYS if key not in row]
        if row_missing:
            raise FaceError("row keys missing: %s" % ",".join(row_missing))
    return env


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def pct(value):
    """Share as a percentage with one decimal, None kept honest."""
    if value is None:
        return None
    return round(float(value) * 100.0, 1)


def build_html(env, labels, now):
    e = html.escape
    kpi = [
        (labels["kpi_purchases"], fmt(env["purchase_count"], labels["none"])),
        (labels["kpi_refunds"], fmt(env["refund_count"], labels["none"])),
        (labels["kpi_buyers"], fmt(env["buyer_count"], labels["none"])),
        (labels["kpi_refunded_buyers"],
         fmt(env["refunded_buyers"], labels["none"])),
        (labels["kpi_gross"], fmt(env["gross_revenue"], labels["none"])),
        (labels["kpi_refunded"], fmt(env["refunded_tokens"], labels["none"])),
        (labels["kpi_net"], fmt(env["net_revenue"], labels["none"])),
        (labels["kpi_top1"], fmt(pct(env["top1_share"]), labels["none"])),
        (labels["kpi_top3"], fmt(pct(env["top3_share"]), labels["none"])),
        (labels["kpi_hhi"], fmt(env["herfindahl"], labels["none"])),
        (labels["kpi_pareto"],
         fmt(env["pareto_buyer_count"], labels["none"])),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>"
                       % (e(k), e(v)) for k, v in kpi)

    hhi = env["herfindahl"]
    mark_pct = 0.0 if hhi is None else max(0.0, min(100.0,
                                                  float(hhi) / 100.0))
    scale = ('<div class="scale"><div class="mark" style="left:%.2f%%" '
             'title="%s"></div></div>'
             '<div class=scale-legend><span>%s</span><span>%s</span>'
             '<span>%s</span></div>'
             '<p class=weak>%s <b>%s</b></p>'
             % (mark_pct, e(labels["scale_mark"]), e(labels["scale_low"]),
                e(labels["scale_mid"]), e(labels["scale_high"]),
                e(labels["scale_mark"]), e(fmt(hhi, labels["none"]))))

    row_html = []
    for row in env["buyers"]:
        share = row["share"]
        width = 0.0 if share is None else round(float(share) * 100.0, 2)
        row_html.append(
            '<tr class="buyer"><td class=s>%s</td><td>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
            '<td><div class=track><div class=fill style="width:%.2f%%">'
            '</div></div></td><td class=n>%s</td><td class=n>%s</td></tr>'
            % (e(fmt(row["rank"], labels["none"])), e(str(row["buyer_id"])),
               e(fmt(row["purchase_count"], labels["none"])),
               e(fmt(row["refund_count"], labels["none"])),
               e(fmt(row["net_purchase_count"], labels["none"])),
               e(fmt(row["gross_revenue"], labels["none"])),
               e(fmt(row["refunded_tokens"], labels["none"])),
               e(fmt(row["net_revenue"], labels["none"])), width,
               e(fmt(pct(share), labels["none"])),
               e(fmt(pct(row["cumulative_share"]), labels["none"]))))
    if row_html:
        rows = ("<table><tr><th class=s>%s</th><th>%s</th>"
                "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
                "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
                "<th>%s</th><th class=n>%s</th><th class=n>%s</th></tr>"
                "%s</table>"
                % (e(labels["col_rank"]), e(labels["col_buyer"]),
                   e(labels["col_purchases"]), e(labels["col_refunds"]),
                   e(labels["col_netcount"]), e(labels["col_gross"]),
                   e(labels["col_refunded"]), e(labels["col_net"]),
                   e(labels["col_share"]), e(labels["col_share"]),
                   e(labels["col_cum"]), "".join(row_html)))
    else:
        rows = "<p>%s</p>" % e(labels["none"])

    head_buyer = env["buyers"][0] if env["buyers"] else None
    named = []
    if env["pareto_buyer_count"] is None:
        named.append("%s %s" % (e(labels["named_pareto"]),
                                e(labels["none"])))
    else:
        named.append("%s %s" % (e(labels["named_pareto"]),
                                e(fmt(env["pareto_buyer_count"],
                                      labels["none"]))))
    if head_buyer is None or env["top1_share"] is None:
        named.append("%s %s" % (e(labels["named_top1"]), e(labels["none"])))
    else:
        named.append("%s %s &middot; %s%%"
                     % (e(labels["named_top1"]), e(str(head_buyer["buyer_id"])),
                        e(fmt(pct(env["top1_share"]), labels["none"]))))
    named_html = "<br>".join(named)

    laws = "".join("<li>%s</li>" % e(labels["law%d" % (i + 1)])
                   for i in range(7))

    head = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        '<div class=card><div class=kpi>%s</div></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><p class=weak>%s</p></div>\n"
        "<h2>%s</h2>\n<div class=card><ol class=laws>%s</ol></div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        "<p style=\"margin-top:10px\"><span class=badge>%s</span></p></div>\n"
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/seller_concentration_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_scale"]), scale,
           e(labels["sec_buyers"]), rows,
           e(labels["sec_named"]), named_html,
           e(labels["sec_laws"]), laws,
           e(labels["sec_disc"]), DISCLAIMER_SLOT,
           e(labels["aigc"]), e(labels["sec_rep"]), e(labels["cmd"]), e(now))
    )
    # The disclaimer is the face's own sentence, injected after assembly so its
    # text is never retyped here.
    return head.replace(DISCLAIMER_SLOT, e(env["disclaimer"] or ""))


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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("SELLER-CONCENTRATION CHECK %s fails=%d html=%dB json=%dB"
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

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, labels, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "dev_account": env["dev_account"],
        "scope": env["scope"],
        "purchase_count": env["purchase_count"],
        "refund_count": env["refund_count"],
        "buyer_count": env["buyer_count"],
        "refunded_buyers": env["refunded_buyers"],
        "gross_revenue": env["gross_revenue"],
        "refunded_tokens": env["refunded_tokens"],
        "net_revenue": env["net_revenue"],
        "top1_share": env["top1_share"],
        "top3_share": env["top3_share"],
        "herfindahl": env["herfindahl"],
        "pareto_buyer_count": env["pareto_buyer_count"],
        "market_herfindahl": env["market_herfindahl"],
        "buyers": env["buyers"],
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

    print("SELLER-CONCENTRATION %s bytes=%d buyers=%d net=%s top1=%s hhi=%s "
          "pareto=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["buyer_count"], fmt(env["net_revenue"], "-"),
             fmt(pct(env["top1_share"]), "-"), fmt(env["herfindahl"], "-"),
             fmt(env["pareto_buyer_count"], "-")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
