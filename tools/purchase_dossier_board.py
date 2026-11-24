#!/usr/bin/env python3
"""Render the single-purchase dossier board into one browsable page.

Why this exists: api_purchase_dossier answers what actually happened to one
purchase - the listing, both parties, the money and its two-leg split, the
refund block, the rating block and the claim block, all behind one party gate -
with its own AC-AMPD criteria. But git grep over tools/ and preview/ found no
page reader at all, so a support ticket or a settlement dispute still had to be
assembled by hand from four faces inside a shell.

Nothing here re-implements a market rule. Purchases are enumerated from the
shipped api_board()/api_sales() faces and every number comes from the shipped
api_purchase_dossier() face read over a fresh throwaway demo world seeded
through the shipped report helpers. The page prints the envelopes it is handed
and never recomputes a count, a split or a state; the only checks it runs are
the face's own published laws, and a broken law refuses the render instead of
printing a plausible page.

A purchase with no refund, no rating or no claim answers an honest nested
absence: the page states the absence instead of inventing a row.

The real sandbox is never opened for writing.

Usage:
  python tools/purchase_dossier_board.py
  python tools/purchase_dossier_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-AMPDB1..AC-AMPDB6 are pre-registered in src/os/backlog.md (R3418 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/purchase-dossier-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "purchase-dossier-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "purchase-dossier-board.json")
COPY = os.path.join(ROOT, "preview", "purchase-dossier-board-copy.json")

FACE = "api_purchase_dossier"
BOARD_FACE = "api_board"
SOURCE_FACE = "api_sales"

# Pinned payload keys (AC-AMPDB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "source_face", "purchase_count",
    "purchases", "disclaimer", "report", "sources", "sizes",
)

PURCHASE_KEYS = (
    "purchase_id", "listing_id", "listing_key", "title", "category",
    "buyer_id", "dev_account", "viewer_role", "price_paid", "dev_share",
    "platform_share", "spend_tx", "purchased_utc", "current_price",
    "delisted", "delisted_utc", "refund", "rating", "claim",
    "ticket_state", "disclaimer",
)

REFUND_KEYS = (
    "refund_id", "amount", "dev_share", "platform_share", "refund_tx",
    "refunded_utc", "reason",
)

RATING_KEYS = ("rating_id", "stars", "revision_count", "revised_utc")

CLAIM_KEYS = (
    "claim_id", "claim_text", "opened_utc", "status", "refund_id",
    "refunded_utc", "response_id", "response_text", "responded_utc",
    "withdrawn_utc",
)

TICKET_STATES = ("refunded", "withdrawn", "answered", "open", "rated",
                 "settled")

CLAIM_STATES = ("open", "answered", "withdrawn", "refunded")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_summary", "sec_detail", "sec_law",
    "sec_disc", "sec_rep", "col_pid", "col_title", "col_buyer",
    "col_seller", "col_price", "col_refund", "col_rating", "col_state",
    "col_delisted", "kpi_price", "kpi_dev", "kpi_plat", "kpi_current",
    "kpi_refund", "kpi_rating", "kpi_state", "kpi_delisted", "none",
    "yes", "no", "no_purchases", "no_refund", "no_rating", "no_claim",
    "blk_refund", "blk_rating", "blk_claim", "field_listing",
    "field_category", "field_buyer", "field_seller", "field_role",
    "field_purchased", "field_spend_tx", "field_current_price",
    "field_delisted", "field_delisted_utc", "law_split", "law_refund",
    "law_state", "law_party", "law_pure", "law_absence", "law_notadvice",
    "bar_note", "rep", "cmd",
)

CSS = """
:root{--ink:#1b1f24;--muted:#66707a;--line:#dfe4ea;--bg:#f7f8fa}
*{box-sizing:border-box}
body{margin:0;padding:24px;background:var(--bg);color:var(--ink);
font:15px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1180px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px;font-weight:650}
h2{font-size:16px;margin:22px 0 8px;font-weight:620}
h3{font-size:13.5px;margin:0 0 6px;font-weight:620;color:var(--muted)}
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
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
.purchase{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:16px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_APDB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_APDB_LAW"


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


def read_purchases():
    """Read one dossier per purchase the shipped faces enumerate."""
    tmp_root = tempfile.mkdtemp(prefix="purchase-dossier-board-")
    db = os.path.join(tmp_root, "purchase-dossier-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        seen = {}
        for dev in sorted(set(str(row["dev_account"])
                              for row in board["listings"])):
            for row in (dict(getattr(am, SOURCE_FACE)(dev)).get("sales")
                        or []):
                pid = row.get("purchase_id")
                buyer = row.get("buyer_id")
                if pid is not None and buyer:
                    seen[int(pid)] = str(buyer)
        blocks = [dict(getattr(am, FACE)(pid, seen[pid]))
                  for pid in sorted(seen)]
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
        pid = block.get("purchase_id")
        missing = [key for key in PURCHASE_KEYS if key not in block]
        if missing:
            raise FaceError("purchase keys missing on %r: %s"
                            % (pid, ",".join(missing)))
        for name, keys in (("refund", REFUND_KEYS), ("rating", RATING_KEYS),
                           ("claim", CLAIM_KEYS)):
            nested = block[name]
            if nested is None:
                continue
            miss = [key for key in keys if key not in nested]
            if miss:
                raise FaceError("%s keys missing on %r: %s"
                                % (name, pid, ",".join(miss)))
    return blocks, disclaimer


def expected_ticket_state(block):
    """The face's pinned precedence, read off the three nested blocks."""
    claim = block["claim"]
    if block["refund"] is not None:
        return "refunded"
    if claim is not None and claim.get("status") == "withdrawn":
        return "withdrawn"
    if claim is not None and claim.get("status") == "answered":
        return "answered"
    if claim is not None and claim.get("status") == "open":
        return "open"
    if block["rating"] is not None:
        return "rated"
    return "settled"


def check_laws(blocks):
    """AC-AMPDB3 read at the source: refuse rather than print."""
    problems = []
    previous = 0
    for block in blocks:
        pid = int(block["purchase_id"])
        name = str(pid)
        if pid <= previous:
            problems.append("%s purchase_id not ascending" % name)
        previous = pid
        paid = int(block["price_paid"])
        if paid != int(block["dev_share"]) + int(block["platform_share"]):
            problems.append("%s split is not the two legs" % name)
        refund = block["refund"]
        if refund is not None:
            amount = int(refund["amount"])
            if amount != paid:
                problems.append("%s refund amount != price_paid" % name)
            if amount != (int(refund["dev_share"])
                          + int(refund["platform_share"])):
                problems.append("%s refund split is not the two legs" % name)
        rating = block["rating"]
        if rating is not None and int(rating["revision_count"]) < 0:
            problems.append("%s negative revision count" % name)
        claim = block["claim"]
        if claim is not None and claim.get("status") not in CLAIM_STATES:
            problems.append("%s bad claim status %r"
                            % (name, claim.get("status")))
        state = block["ticket_state"]
        if state not in TICKET_STATES:
            problems.append("%s bad ticket_state %r" % (name, state))
        elif state != expected_ticket_state(block):
            problems.append("%s ticket_state %r != recomputed %r"
                            % (name, state, expected_ticket_state(block)))
        stamped = block["delisted_utc"] is not None
        if bool(block["delisted"]) != stamped:
            problems.append("%s delisted and its stamp disagree" % name)
        purchased = str(block["purchased_utc"])
        if (len(purchased) != 20 or purchased[10] != "T"
                or not purchased.endswith("Z")):
            problems.append("%s bad purchased_utc %r" % (name, purchased))
    return problems


def fmt(value, none_text):
    if value is None:
        return none_text
    return str(value)


def kpi_html(block, labels, e):
    refund = block["refund"]
    rating = block["rating"]
    items = [
        (labels["kpi_price"], fmt(block["price_paid"], labels["none"])),
        (labels["kpi_dev"], fmt(block["dev_share"], labels["none"])),
        (labels["kpi_plat"], fmt(block["platform_share"], labels["none"])),
        (labels["kpi_current"], fmt(block["current_price"], labels["none"])),
        (labels["kpi_refund"],
         fmt(refund["amount"] if refund else None, labels["none"])),
        (labels["kpi_rating"],
         fmt(rating["stars"] if rating else None, labels["none"])),
        (labels["kpi_state"], fmt(block["ticket_state"], labels["none"])),
        (labels["kpi_delisted"],
         labels["yes"] if block["delisted"] else labels["no"]),
    ]
    return "".join("<div><span>%s</span><b>%s</b></div>" % (e(k), e(v))
                   for k, v in items)


def field_rows(block, labels):
    return [
        (labels["field_listing"],
         "%s (#%s)" % (fmt(block["listing_key"], labels["none"]),
                       fmt(block["listing_id"], labels["none"]))),
        (labels["field_category"], fmt(block["category"], labels["none"])),
        (labels["field_buyer"], fmt(block["buyer_id"], labels["none"])),
        (labels["field_seller"], fmt(block["dev_account"], labels["none"])),
        (labels["field_role"], fmt(block["viewer_role"], labels["none"])),
        (labels["field_purchased"], fmt(block["purchased_utc"],
                                        labels["none"])),
        (labels["field_spend_tx"], fmt(block["spend_tx"], labels["none"])),
        (labels["field_current_price"],
         fmt(block["current_price"], labels["none"])),
        (labels["field_delisted"],
         labels["yes"] if block["delisted"] else labels["no"]),
        (labels["field_delisted_utc"], fmt(block["delisted_utc"],
                                            labels["none"])),
    ]


def nested_table(rows, labels):
    body = "".join("<tr><th>%s</th><td>%s</td></tr>"
                   % (html.escape(str(k)), html.escape(fmt(v, labels["none"])))
                   for k, v in rows)
    return "<table>%s</table>" % body


def summary_cells(block, labels):
    refund = block["refund"]
    rating = block["rating"]
    return (
        str(block["purchase_id"]),
        fmt(block["title"], labels["none"]),
        fmt(block["buyer_id"], labels["none"]),
        fmt(block["dev_account"], labels["none"]),
        fmt(block["price_paid"], labels["none"]),
        fmt(refund["amount"] if refund else None, labels["none"]),
        fmt(rating["stars"] if rating else None, labels["none"]),
        fmt(block["ticket_state"], labels["none"]),
        labels["yes"] if block["delisted"] else labels["no"],
    )


def build_html(blocks, labels, now, disclaimer):
    e = html.escape
    head = (labels["col_pid"], labels["col_title"], labels["col_buyer"],
            labels["col_seller"], labels["col_price"], labels["col_refund"],
            labels["col_rating"], labels["col_state"], labels["col_delisted"])
    head_html = "".join(
        ('<th>%s</th>' if index < 2 else '<th class=n>%s</th>') % e(cell)
        for index, cell in enumerate(head))

    if blocks:
        body = "".join(
            '<tr class="purchase"><td class=n>%s</td><td>%s</td>'
            '<td>%s</td><td>%s</td>%s</tr>'
            % (e(cells[0]), e(cells[1]), e(cells[2]), e(cells[3]),
               "".join('<td class=n>%s</td>' % e(cell)
                       for cell in cells[4:]))
            for cells in (summary_cells(block, labels) for block in blocks))
        summary = "<table><tr>%s</tr>%s</table>" % (head_html, body)
    else:
        summary = '<p class=empty>%s</p>' % e(labels["no_purchases"])

    details = []
    for block in blocks:
        refund = block["refund"]
        rating = block["rating"]
        claim = block["claim"]
        refund_html = (nested_table([(key, refund[key])
                                     for key in REFUND_KEYS], labels)
                       if refund is not None
                       else '<p class=empty>%s</p>' % e(labels["no_refund"]))
        rating_html = (nested_table([(key, rating[key])
                                     for key in RATING_KEYS], labels)
                       if rating is not None
                       else '<p class=empty>%s</p>' % e(labels["no_rating"]))
        claim_html = (nested_table([(key, claim[key])
                                    for key in CLAIM_KEYS], labels)
                      if claim is not None
                      else '<p class=empty>%s</p>' % e(labels["no_claim"]))
        details.append(
            '<div class=purchase id="purchase-%s"><h2>#%s %s</h2>'
            '<div class=kpi>%s</div>'
            '<div class=card>%s</div>'
            '<div class=card><h3>%s</h3>%s</div>'
            '<div class=card><h3>%s</h3>%s</div>'
            '<div class=card><h3>%s</h3>%s</div></div>'
            % (e(str(block["purchase_id"])), e(str(block["purchase_id"])),
               e(fmt(block["title"], labels["none"])),
               kpi_html(block, labels, e),
               nested_table(field_rows(block, labels), labels),
               e(labels["blk_refund"]), refund_html,
               e(labels["blk_rating"]), rating_html,
               e(labels["blk_claim"]), claim_html))

    laws = [labels["law_split"], labels["law_refund"], labels["law_state"],
            labels["law_party"], labels["law_pure"], labels["law_absence"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)

    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<p class=empty>%s</p>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/purchase_dossier_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_summary"]),
           summary, e(labels["sec_detail"]), "".join(details),
           e(labels["bar_note"]), e(labels["sec_law"]), law_html,
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
        print("PURCHASE-DOSSIER CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        blocks, disclaimer = read_purchases()
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
        "purchase_count": len(blocks),
        "purchases": blocks,
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

    print("PURCHASE-DOSSIER %s bytes=%d purchases=%d refunds=%d"
          " ratings=%d claims=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["purchase_count"],
             sum(1 for b in blocks if b["refund"] is not None),
             sum(1 for b in blocks if b["rating"] is not None),
             sum(1 for b in blocks if b["claim"] is not None)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
