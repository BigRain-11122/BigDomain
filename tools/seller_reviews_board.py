#!/usr/bin/env python3
"""Render the seller review-status reading on one page a human opens.

Why this exists: api_seller_reviews answers "which of my listings are waiting,
which were refused and why, and how many times did I resubmit" with its own
AC-AMRC6 law, but the operator holds api_review_queue and the outside reader
holds api_public_listings while the seller had no page of his own; a git grep
over tools/ and preview/ answered zero hits. Measured in R3431 over the factory
demo world: usr:dana carries two listings, both pending at review cycle 1 with
a null reason and a null reviewed stamp; usr:frank is an honest empty envelope.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_reviews() face read over a fresh throwaway demo world seeded through
the shipped report helpers. Sellers are enumerated through the shipped board
face instead of being typed by hand. The page prints what the face hands it and
never recomputes a total; the only checks it runs are the face's own published
laws, and a broken law refuses the render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_reviews_board.py
  python tools/seller_reviews_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-SVRB1..AC-SVRB6 are pre-registered in src/os/backlog.md (R3431 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-reviews-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-reviews-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-reviews-board.json")
COPY = os.path.join(ROOT, "preview", "seller-reviews-board-copy.json")

FACE = "api_seller_reviews"
BOARD_FACE = "api_board"
STATES = ("pending", "approved", "refused")

# Pinned payload keys (AC-SVRB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 8 keys.
ENVELOPE_KEYS = (
    "dev_account", "listing_count", "pending_count", "approved_count",
    "refused_count", "resubmit_count", "disclaimer", "rows",
)

# One listing row, 10 keys.
ROW_KEYS = (
    "listing_id", "listing_key", "title", "token_price", "delisted",
    "review_cycle", "review_state", "review_reason", "reviewed_utc",
    "resubmit_count",
)

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_sellers", "sec_law",
    "sec_disc", "sec_rep",
    "kpi_listings", "kpi_pending", "kpi_approved", "kpi_refused",
    "kpi_resubmits",
    "col_id", "col_key", "col_title", "col_price", "col_shelf",
    "col_cycle", "col_state", "col_reason", "col_reviewed", "col_resubmits",
    "badge_pending", "badge_approved", "badge_refused",
    "label_live", "label_delisted", "empty_scope", "none",
    "law_count", "law_states", "law_reason", "law_stamp", "law_order",
    "law_scope", "law_reason_scope", "law_notadvice", "law_resubmit",
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
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.badge.pending{border-color:#c8b48f;color:#7a5f28}
.badge.approved{border-color:#a9c6b0;color:#3f6a4c}
.badge.refused{border-color:#dcb0b0;color:#8a4242}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
.note{color:var(--muted);font-size:12.5px;margin:6px 0 0}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_SVRB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_SVRB_LAW"


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
    """Read one scoped envelope per seller from the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="seller-reviews-board-")
    db = os.path.join(tmp_root, "seller-reviews-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        board = getattr(am, BOARD_FACE)()
        sellers = [dict(getattr(am, FACE)(seller))
                   for seller in enumerate_sellers(board)]
        disclaimer = sellers[0]["disclaimer"] if sellers else None
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    if not sellers:
        raise FaceError("no seller on the shipped board face")
    for envelope in sellers:
        missing = [key for key in ENVELOPE_KEYS if key not in envelope]
        if missing:
            raise FaceError("envelope keys missing on %r: %s"
                            % (envelope.get("dev_account"), ",".join(missing)))
        for row in envelope["rows"]:
            missing = [key for key in ROW_KEYS if key not in row]
            if missing:
                raise FaceError("row keys missing on %r: %s"
                                % (row.get("listing_id"), ",".join(missing)))
    return sellers, disclaimer


def _envelope_problems(envelope, label):
    """AC-SVRB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["rows"]
    if int(envelope["listing_count"]) != len(rows):
        problems.append("%s listing_count %r != rows %d"
                        % (label, envelope["listing_count"], len(rows)))
    for state in STATES:
        want = sum(1 for row in rows if row["review_state"] == state)
        key = "%s_count" % state
        if int(envelope[key]) != want:
            problems.append("%s %s %r != %d"
                            % (label, key, envelope[key], want))
    want_resub = sum(int(row["resubmit_count"]) for row in rows)
    if int(envelope["resubmit_count"]) != want_resub:
        problems.append("%s resubmit_count %r != row sum %d"
                        % (label, envelope["resubmit_count"], want_resub))
    ids = [int(row["listing_id"]) for row in rows]
    if ids != sorted(ids):
        problems.append("%s rows are not ordered by listing_id" % label)
    if len(ids) != len(set(ids)):
        problems.append("%s carries one listing_id twice" % label)
    for row in rows:
        state = row["review_state"]
        name = "%s/%s" % (label, row["listing_id"])
        if state not in STATES:
            problems.append("%s review_state %r is not a known state"
                            % (name, state))
            continue
        if (row["review_reason"] is None) != (state != "refused"):
            problems.append("%s reason must be set exactly when refused"
                            % name)
        if (row["reviewed_utc"] is None) != (state == "pending"):
            problems.append("%s reviewed stamp must be set exactly when"
                            " not pending" % name)
        if state == "pending" and row["review_reason"] is not None:
            problems.append("%s pending row carries a reason" % name)
        if int(row["review_cycle"]) < 1:
            problems.append("%s review_cycle %r < 1"
                            % (name, row["review_cycle"]))
        if int(row["resubmit_count"]) < 0:
            problems.append("%s resubmit_count %r < 0"
                            % (name, row["resubmit_count"]))
        if not str(row["listing_key"] or "").strip():
            problems.append("%s carries an empty listing_key" % name)
        if not str(row["title"] or "").strip():
            problems.append("%s carries an empty title" % name)
        if not isinstance(row["delisted"], bool):
            problems.append("%s delisted %r is not a boolean"
                            % (name, row["delisted"]))
    return problems


def check_laws(sellers):
    problems = []
    for block in sellers:
        name = str(block["dev_account"])
        problems.extend(_envelope_problems(block, name))
        if not name.startswith("usr:"):
            problems.append("%s is not a seller account" % name)
    if sellers and sellers[0]["disclaimer"] != sellers[-1]["disclaimer"]:
        problems.append("sellers disagree on the disclaimer")
    return problems


def fmt(value, none_text):
    if value is None or value == "":
        return none_text
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def kpi_html(envelope, labels, e, dash):
    items = [
        (labels["kpi_listings"], fmt(envelope["listing_count"], dash)),
        (labels["kpi_pending"], fmt(envelope["pending_count"], dash)),
        (labels["kpi_approved"], fmt(envelope["approved_count"], dash)),
        (labels["kpi_refused"], fmt(envelope["refused_count"], dash)),
        (labels["kpi_resubmits"], fmt(envelope["resubmit_count"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def summary_table(sellers, labels, e, dash):
    head = (labels["sec_sellers"], labels["kpi_listings"],
            labels["kpi_pending"], labels["kpi_approved"],
            labels["kpi_refused"], labels["kpi_resubmits"])
    head_html = "<th>%s</th>" % e(head[0]) + "".join(
        '<th class=n>%s</th>' % e(cell) for cell in head[1:])
    body = []
    for block in sellers:
        cells = (fmt(block["listing_count"], dash),
                 fmt(block["pending_count"], dash),
                 fmt(block["approved_count"], dash),
                 fmt(block["refused_count"], dash),
                 fmt(block["resubmit_count"], dash))
        body.append('<tr data-seller="%s"><td><code>%s</code></td>%s</tr>'
                    % (e(str(block["dev_account"])),
                       e(str(block["dev_account"])),
                       "".join('<td class=n>%s</td>' % e(str(cell))
                               for cell in cells)))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def rows_table(envelope, labels, e, dash):
    head = (labels["col_id"], labels["col_key"], labels["col_title"],
            labels["col_price"], labels["col_shelf"], labels["col_cycle"],
            labels["col_state"], labels["col_reason"], labels["col_reviewed"],
            labels["col_resubmits"])
    left = (labels["col_id"], labels["col_key"], labels["col_title"],
            labels["col_state"], labels["col_reason"], labels["col_reviewed"])
    head_html = "".join(
        ("<th>%s</th>" % e(cell)) if cell in left
        else ('<th class=n>%s</th>' % e(cell)) for cell in head)
    body = []
    for row in envelope["rows"]:
        state = str(row["review_state"])
        badge = '<span class="badge %s">%s</span>' % (
            e(state), e(labels["badge_" + state]))
        shelf = (labels["label_delisted"] if row["delisted"]
                 else labels["label_live"])
        cells_left = (
            fmt(row["listing_id"], dash), fmt(row["listing_key"], dash),
            fmt(row["title"], dash), badge,
            fmt(row["review_reason"], dash), fmt(row["reviewed_utc"], dash),
        )
        cells_right = (
            fmt(row["token_price"], dash), fmt(shelf, dash),
            fmt(row["review_cycle"], dash), fmt(row["resubmit_count"], dash),
        )
        tds = "".join("<td>%s</td>" % cell for cell in cells_left)
        tds += "".join('<td class=n>%s</td>' % e(str(cell))
                       for cell in cells_right)
        body.append('<tr data-state="%s" data-listing="%s">%s</tr>'
                    % (e(state), e(str(row["listing_id"])), tds))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["sec_sellers"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash)))


def build_html(sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_states"], labels["law_reason"],
            labels["law_stamp"], labels["law_order"], labels["law_scope"],
            labels["law_reason_scope"], labels["law_resubmit"],
            labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    sections = "".join(
        '<div class=card data-seller="%s">%s</div>'
        % (e(str(block["dev_account"])),
           seller_section(block, labels, e, dash))
        for block in sellers)
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n%s\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>%s</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), e(labels["sec_sellers"]),
           summary_table(sellers, labels, e, dash),
           e(labels["sec_sellers"]),
           sections or ('<div class=card data-seller-empty="1"><p class=empty>'
                        '%s</p></div>' % e(labels["empty_scope"])),
           e(labels["sec_law"]), law_html, e(labels["sec_disc"]),
           DISCLAIMER_SLOT, e(labels["aigc"]), e(labels["sec_rep"]),
           e(labels["cmd"]), e(labels["foot"]))
    )
    return doc.replace(DISCLAIMER_SLOT, e(disclaimer or ""))


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
        print("SELLER-REVIEWS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        sellers, disclaimer = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(sellers)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    now = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ")
    doc = build_html(sellers, labels, now, disclaimer)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "board_face": BOARD_FACE,
        "scope": "seller",
        "seller_count": len(sellers),
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

    print("SELLER-REVIEWS %s bytes=%d sellers=%d listings=%d pending=%d"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"],
             sum(int(b["listing_count"]) for b in sellers),
             sum(int(b["pending_count"]) for b in sellers)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
