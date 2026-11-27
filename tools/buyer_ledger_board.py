#!/usr/bin/env python3
"""Render the buyer wallet statement (one statement per buyer) into one page.

Why this exists: api_buyer_ledger answers the question a buyer asks right
after a refund - "did the money actually come back into my wallet, and which
entry brought it" - with its own AC-AMLGB1..8 criteria, but git grep over
tools/ and preview/ found no reader at all, so the wallet could only be read
by calling the sandbox from a shell. The seller side already had a statement
page; the buyer side had none.

Nothing here re-implements a market rule. Every number comes from the shipped
api_buyer_ledger() face read over a fresh throwaway demo world seeded through
the shipped report helpers. Buyers are enumerated through the shipped board,
sales and ratings faces instead of being typed by hand. The page prints the
envelope it is handed and never recomputes a total; the only checks it runs
are the face's own published laws, and a broken law refuses the render instead
of printing a plausible page.

A refund credit is marked on the statement because that is the row a buyer is
looking for; the marker is read from the shipped ref prefix, never inferred
from an amount. An empty statement is proved by the suite handing the renderer
its own envelope; nothing synthetic is added to the landed page.

The real sandbox is never opened for writing.

Usage:
  python tools/buyer_ledger_board.py
  python tools/buyer_ledger_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-BLB1..AC-BLB6 are pre-registered in src/os/backlog.md (R3415 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/buyer-ledger-board-copy.json and appear in the rendered document only,
never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "buyer-ledger-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "buyer-ledger-board.json")
COPY = os.path.join(ROOT, "preview", "buyer-ledger-board-copy.json")

FACE = "api_buyer_ledger"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_sales"
RATINGS_FACE = "api_ratings"
REFUND_PREFIX = "apimarket:refund:"

# Pinned payload keys (AC-BLB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "buyer_count",
    "buyers", "disclaimer", "report", "sources", "sizes",
)

BUYER_KEYS = ("balance", "balance_known", "buyer_id", "credit_total",
              "debit_total", "disclaimer", "entries", "entry_count", "limit",
              "net")

ENTRY_KEYS = ("action", "amount", "direction", "memo", "ref", "ref_type",
              "source_ai", "ts_utc", "tx_id", "type")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_buyers", "sec_law", "sec_disc",
    "sec_rep", "col_ts", "col_type", "col_action", "col_dir", "col_amount",
    "col_ref", "col_memo", "col_ai", "col_tx", "kpi_balance", "kpi_known",
    "kpi_entries", "kpi_credit", "kpi_debit", "kpi_net", "kpi_limit",
    "none", "no_entries", "dir_credit", "dir_debit", "ai_yes", "refund_tag",
    "law_balance", "law_count", "law_order", "law_empty", "law_dir",
    "law_refund", "law_notadvice", "rep", "cmd",
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
tr.refund td{background:#fdf8ea}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;
border:1px solid #e3cf8a;background:#fdf8ea;font-size:11.5px;color:#7a5c00}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.kpi div{flex:1 1 108px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi b.neg{color:#b42318}
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

    code = "E_BLB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_BLB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def enumerate_buyers(am, board):
    """Buyer ids through the shipped sales and ratings faces, never typed."""
    seen = set()
    devs = sorted(set(str(row["dev_account"]) for row in board["listings"]))
    for dev in devs:
        sales = getattr(am, SOURCE_FACE)(dev)
        for row in sales.get("sales") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    for listing in board["listings"]:
        rated = getattr(am, RATINGS_FACE)(listing["listing_id"])
        for row in rated.get("ratings") or []:
            if row.get("buyer_id"):
                seen.add(str(row["buyer_id"]))
    return sorted(seen)


def read_buyers():
    """Read one statement per buyer the shipped faces enumerate."""
    tmp_root = tempfile.mkdtemp(prefix="buyer-ledger-board-")
    db = os.path.join(tmp_root, "buyer-ledger-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        buyers = [dict(getattr(am, FACE)(buyer))
                  for buyer in enumerate_buyers(am, board)]
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
    if not buyers:
        raise FaceError("no buyer enumerated through the shipped faces")
    for block in buyers:
        missing = [key for key in BUYER_KEYS if key not in block]
        if missing:
            raise FaceError("buyer keys missing on %r: %s"
                            % (block.get("buyer_id"), ",".join(missing)))
        if not isinstance(block["entries"], list):
            raise FaceError("entries is not a list on %r"
                            % (block.get("buyer_id"),))
        for row in block["entries"]:
            miss = [key for key in ENTRY_KEYS if key not in row]
            if miss:
                raise FaceError("entry keys missing: %s" % ",".join(miss))
    return buyers, disclaimer


def check_laws(blocks):
    """AC-BLB3 read at the source: refuse rather than print."""
    problems = []
    for block in blocks:
        name = str(block["buyer_id"])
        entries = block["entries"]
        if int(block["entry_count"]) != len(entries):
            problems.append("%s entry_count=%s entries=%d"
                            % (name, block["entry_count"], len(entries)))
        credit = sum(int(row["amount"]) for row in entries
                     if row["direction"] == "credit")
        debit = sum(int(row["amount"]) for row in entries
                    if row["direction"] == "debit")
        if credit != int(block["credit_total"]):
            problems.append("%s credit_total=%s sum=%d"
                            % (name, block["credit_total"], credit))
        if debit != int(block["debit_total"]):
            problems.append("%s debit_total=%s sum=%d"
                            % (name, block["debit_total"], debit))
        if int(block["net"]) != credit - debit:
            problems.append("%s net=%s expected=%d"
                            % (name, block["net"], credit - debit))
        if block["balance_known"] and int(block["balance"]) != int(block["net"]):
            problems.append("%s balance=%s net=%s"
                            % (name, block["balance"], block["net"]))
        for row in entries:
            if int(row["amount"]) < 0:
                problems.append("%s negative amount %r"
                                % (name, row["tx_id"]))
            if row["direction"] not in ("credit", "debit"):
                problems.append("%s bad direction %r"
                                % (name, row["direction"]))
        stamps = [str(row["ts_utc"] or "") for row in entries]
        if stamps != sorted(stamps, reverse=True):
            problems.append("%s entries not newest-first: %r"
                            % (name, stamps))
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    return str(value)


def kpi_html(block, labels, e):
    items = [
        (labels["kpi_balance"], fmt(block["balance"], labels["none"])),
        (labels["kpi_known"], str(bool(block["balance_known"])).lower()),
        (labels["kpi_entries"], fmt(block["entry_count"], labels["none"])),
        (labels["kpi_credit"], fmt(block["credit_total"], labels["none"])),
        (labels["kpi_debit"], fmt(block["debit_total"], labels["none"])),
        (labels["kpi_net"], fmt(block["net"], labels["none"])),
        (labels["kpi_limit"], fmt(block["limit"], labels["none"])),
    ]
    return "".join(
        '<div><span>%s</span><b%s>%s</b></div>'
        % (e(k), ' class="neg"' if v.startswith("-") else "", e(v))
        for k, v in items)


def is_refund(row):
    return str(row.get("ref") or "").startswith(REFUND_PREFIX)


def entry_cells(row, labels):
    direction = (labels["dir_credit"] if row["direction"] == "credit"
                 else labels["dir_debit"])
    return (fmt(row["ts_utc"], labels["none"]),
            fmt(row["type"], labels["none"]),
            fmt(row["action"], labels["none"]), direction,
            fmt(row["amount"], labels["none"]),
            fmt(row["ref"], labels["none"]),
            fmt(row["memo"], labels["none"]),
            labels["ai_yes"] if row["source_ai"] else "",
            fmt(row["tx_id"], labels["none"]))


def build_html(blocks, labels, now, disclaimer):
    e = html.escape
    head = (labels["col_ts"], labels["col_type"], labels["col_action"],
            labels["col_dir"], labels["col_amount"], labels["col_ref"],
            labels["col_memo"], labels["col_ai"], labels["col_tx"])
    head_html = "".join(
        '<th class=n>%s</th>' % e(cell) if cell == labels["col_amount"]
        else "<th>%s</th>" % e(cell) for cell in head)

    sections = []
    for block in blocks:
        rows = block["entries"]
        if rows:
            body = []
            for row in rows:
                cells = entry_cells(row, labels)
                # The refund marker rides inside the ref cell of its own row,
                # so the column count never moves.
                tag = ('<span class=tag>%s</span> ' % e(labels["refund_tag"])
                       if is_refund(row) else "")
                tds = []
                for idx, cell in enumerate(cells[1:], start=1):
                    if idx == 4:
                        tds.append('<td class="n%s">%s</td>'
                                   % (" neg" if cell.startswith("-") else "",
                                      e(cell)))
                    elif idx == 5:
                        tds.append("<td>%s%s</td>" % (tag, e(cell)))
                    else:
                        tds.append("<td>%s</td>" % e(cell))
                body.append(
                    '<tr class="entry%s" data-tx="%s"><td>%s</td>%s</tr>'
                    % (" refund" if is_refund(row) else "",
                       e(str(row["tx_id"])), e(cells[0]), "".join(tds)))
            table = ("<table><tr>%s</tr>%s</table>"
                     % (head_html, "".join(body)))
        else:
            table = '<p class=empty>%s</p>' % e(labels["no_entries"])
        sections.append(
            '<div class=buyer id="buyer-%s"><h2>%s</h2>'
            '<div class=kpi>%s</div><div class=card>%s</div></div>'
            % (e(str(block["buyer_id"])), e(str(block["buyer_id"])),
               kpi_html(block, labels, e), table))

    laws = [labels["law_balance"], labels["law_count"], labels["law_order"],
            labels["law_empty"], labels["law_dir"], labels["law_refund"],
            labels["law_notadvice"]]
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
        "\u672c\u9875\u7531 tools/buyer_ledger_board.py "
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
    """AC-PWC40 (R3562): landing this pair and re-deriving the CEO face are ONE run.

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
        sys.stderr.write("E_NO_APIMARKET: src/sandbox/ledger/apimarket.py "
                         "missing\n")
        return 3

    if args.check:
        fails = check_sizes(args.out, args.json) + check_sources(args.json)
        print("BUYER-LEDGER CHECK %s fails=%d html=%dB json=%dB"
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

    face = _refresh_face(args.out, args.json)

    print("BUYER-LEDGER %s bytes=%d buyers=%d entries=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["buyer_count"],
             sum(len(b["entries"]) for b in blocks), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
