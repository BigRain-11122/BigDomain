#!/usr/bin/env python3
"""Render the seller duty queue on one page a human opens.

Why this exists: api_seller_inbox answers unanswered ratings,
api_seller_questions unanswered questions, api_claims the claim queue a
seller has to filter by hand, and the R2137 disputed state lived only inside
one claim thread - so a seller holding N listings had to open four faces and
merge them by hand to answer "what do I owe right now, and how long has the
oldest one waited". api_seller_todo is that merged queue with its own
AC-AMTD1..8 law, but a git grep over tools/ and preview/ answered zero hits:
no page could be opened.

Nothing here re-implements a market rule. Every number comes from the shipped
api_seller_todo() face read over a fresh throwaway demo world seeded through
the shipped report helpers and the driver's shipped-door duty fixture. Sellers
are enumerated through the shipped board face instead of being typed by hand.
The page prints what the face hands it and never recomputes a count; the only
checks it runs are the face's own published laws, and a broken law refuses the
render instead of printing a plausible page.

A rating row carries no detail (the star value lives on its own face), so the
detail column prints a dash there - never the word None. A seller with no debt
prints a named quiet sentence rather than an empty table, and its two "oldest"
cells print dashes because the face publishes None.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/seller_todo_board.py
  python tools/seller_todo_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-STDB1..AC-STDB6 are pre-registered in src/os/backlog.md (R3433 PIN)
BEFORE this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-todo-board-copy.json and appear in the rendered document only,
never in this file.
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-todo-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-todo-board.json")
COPY = os.path.join(ROOT, "preview", "seller-todo-board-copy.json")

FACE = "api_seller_todo"
BOARD_FACE = "api_board"

# Pinned payload keys (AC-STDB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "board_face", "scope", "seller_count",
    "sellers", "disclaimer", "report", "sources", "sizes",
)

# The shipped envelope, 11 keys.
ENVELOPE_KEYS = (
    "dev_account", "total_count", "rating_count", "question_count",
    "claim_open_count", "claim_disputed_count", "listing_count",
    "oldest_utc", "oldest_kind", "rows", "disclaimer",
)

# One duty row, 8 keys.
ROW_KEYS = (
    "kind", "ref_id", "listing_id", "listing_key", "listing_title",
    "counterparty", "since_utc", "detail",
)

# The four families and their pinned order (AC-AMTD2).
KIND_RANK = {"rating": 0, "question": 1, "claim_open": 2,
             "claim_disputed": 3}

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "foot", "sec_sellers", "sec_law",
    "sec_disc", "sec_rep",
    "kpi_total", "kpi_rating", "kpi_question", "kpi_claim_open",
    "kpi_claim_disputed", "kpi_listings", "kpi_oldest",
    "col_seller", "col_total", "col_rating", "col_question",
    "col_claim_open", "col_claim_disputed", "col_listings", "col_oldest",
    "col_oldest_kind", "col_kind", "col_ref", "col_listing",
    "col_counterparty", "col_since", "col_detail",
    "label_rating", "label_question", "label_claim_open",
    "label_claim_disputed",
    "empty_scope", "none", "empty_detail",
    "law_count", "law_partition", "law_listings", "law_oldest", "law_order",
    "law_family", "law_detail", "law_scope", "law_notadvice",
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
.badge.rating{border-color:#b9c6d8;color:#3d5268}
.badge.question{border-color:#b6cdb9;color:#3f6a4c}
.badge.claim-open{border-color:#e0c898;color:#7a5f28}
.badge.claim-disputed{border-color:#dcb0b0;color:#8a4242}
.law{font-size:13px;margin:6px 0}
.empty{color:var(--muted);font-size:13px}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""

DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face or the label copy refused."""

    code = "E_STDB_FACE"


class LawError(Exception):
    """Named refusal: a law the face publishes does not hold in this world."""

    code = "E_STDB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def seed_duty(am):
    """Add the duty families the factory demo world never carries.

    The demo world leaves dana two unanswered ratings and frank nothing, so a
    question, an open claim and an answered-then-restated claim (the R2137
    disputed state) would only ever be proved by a probe. These rows are
    written through the shipped doors (ask, purchase, claim, respond, note)
    under a pinned clock, so the page proves those families on landed rows.
    The fixture is a world builder, never a data source: every number on the
    page is still read back from api_seller_todo().
    """
    board = am.api_board()
    by_key = {str(row["listing_key"]): int(row["listing_id"])
              for row in board["listings"]}
    d1 = by_key["risk-scan"]
    d2 = by_key["macro-feed"]
    clock = R.Clock()
    orig = R.A._now_utc
    R.A._now_utc = clock.now_utc
    try:
        clock.value = "2026-11-02T00:00:00Z"
        am.ask_question("usr:bob", d1, "does the scan cover options?")
        clock.value = "2026-11-03T00:00:00Z"
        buy = am.purchase_api("usr:carol", d2, "ref-carol-feed")
        am.open_claim("usr:carol", buy["purchase_id"],
                      "feed returns stale rows")
        clock.value = "2026-11-04T00:00:00Z"
        buy2 = am.purchase_api("usr:dave", d2, "ref-dave-feed")
        claim = am.open_claim("usr:dave", buy2["purchase_id"],
                              "feed stopped overnight")
        clock.value = "2026-11-05T00:00:00Z"
        am.respond_claim("usr:dana", claim["claim_id"],
                         "restarted the feeder")
        clock.value = "2026-11-06T00:00:00Z"
        am.add_claim_note("usr:dave", claim["claim_id"],
                          "still stale this morning")
    finally:
        R.A._now_utc = orig


def enumerate_sellers(board):
    """Seller ids through the shipped board face, never typed."""
    return sorted(set(str(row["dev_account"]) for row in board["listings"]))


def read_world():
    """Read one duty envelope per seller from the shipped face."""
    tmp_root = tempfile.mkdtemp(prefix="seller-todo-board-")
    db = os.path.join(tmp_root, "seller-todo-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        seed_duty(am)
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
                                % (row.get("ref_id"), ",".join(missing)))
    return sellers, disclaimer


def _envelope_problems(envelope, label):
    """AC-STDB3 read at the source: refuse rather than print."""
    problems = []
    rows = envelope["rows"]
    if int(envelope["total_count"]) != len(rows):
        problems.append("%s total_count %r != rows %d"
                        % (label, envelope["total_count"], len(rows)))
    tallies = {"rating": 0, "question": 0, "claim_open": 0,
               "claim_disputed": 0}
    for row in rows:
        kind = str(row["kind"])
        if kind not in tallies:
            problems.append("%s carries unknown kind %r" % (label, kind))
            continue
        tallies[kind] += 1
    for kind in tallies:
        if int(envelope[kind + "_count"]) != tallies[kind]:
            problems.append("%s %s_count %r != %d"
                            % (label, kind, envelope[kind + "_count"],
                               tallies[kind]))
    if sum(tallies.values()) != len(rows):
        problems.append("%s families do not partition the rows" % label)
    listings = {int(row["listing_id"]) for row in rows}
    if int(envelope["listing_count"]) != len(listings):
        problems.append("%s listing_count %r != %d distinct listings"
                        % (label, envelope["listing_count"], len(listings)))
    if rows:
        first = rows[0]
        if envelope["oldest_utc"] != first["since_utc"]:
            problems.append("%s oldest_utc %r != first row %r"
                            % (label, envelope["oldest_utc"],
                               first["since_utc"]))
        if envelope["oldest_kind"] != first["kind"]:
            problems.append("%s oldest_kind %r != first row %r"
                            % (label, envelope["oldest_kind"], first["kind"]))
    elif envelope["oldest_utc"] is not None or (
            envelope["oldest_kind"] is not None):
        problems.append("%s empty queue still publishes an oldest" % label)
    order = [(str(row["since_utc"]), KIND_RANK.get(str(row["kind"]), 9),
              int(row["ref_id"])) for row in rows]
    if order != sorted(order):
        problems.append("%s rows are not in the pinned total order" % label)
    for row in rows:
        name = "%s/%s" % (label, row["ref_id"])
        if row["detail"] is None and str(row["kind"]) != "rating":
            problems.append("%s is a %s row with no detail"
                            % (name, row["kind"]))
        if str(row["kind"]) == "rating" and row["detail"] is not None:
            problems.append("%s is a rating row carrying a detail" % name)
        if not str(row["listing_key"] or "").strip():
            problems.append("%s carries an empty listing_key" % name)
        if not str(row["counterparty"] or "").startswith("usr:"):
            problems.append("%s counterparty %r is not a resident"
                            % (name, row["counterparty"]))
        if not str(row["since_utc"] or "").strip():
            problems.append("%s carries no since_utc" % name)
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
        (labels["kpi_total"], fmt(envelope["total_count"], dash)),
        (labels["kpi_rating"], fmt(envelope["rating_count"], dash)),
        (labels["kpi_question"], fmt(envelope["question_count"], dash)),
        (labels["kpi_claim_open"], fmt(envelope["claim_open_count"], dash)),
        (labels["kpi_claim_disputed"],
         fmt(envelope["claim_disputed_count"], dash)),
        (labels["kpi_listings"], fmt(envelope["listing_count"], dash)),
        (labels["kpi_oldest"], fmt(envelope["oldest_utc"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>' % (e(k), e(v))
                   for k, v in items)


def summary_table(sellers, labels, e, dash):
    head = (labels["col_seller"], labels["col_total"], labels["col_rating"],
            labels["col_question"], labels["col_claim_open"],
            labels["col_claim_disputed"], labels["col_listings"],
            labels["col_oldest"], labels["col_oldest_kind"])
    head_html = "<th>%s</th>" % e(head[0]) + "".join(
        '<th class=n>%s</th>' % e(cell) for cell in head[1:])
    body = []
    for block in sellers:
        cells = (fmt(block["total_count"], dash),
                 fmt(block["rating_count"], dash),
                 fmt(block["question_count"], dash),
                 fmt(block["claim_open_count"], dash),
                 fmt(block["claim_disputed_count"], dash),
                 fmt(block["listing_count"], dash),
                 fmt(block["oldest_utc"], dash),
                 fmt(block["oldest_kind"], dash))
        body.append('<tr data-seller="%s"><td><code>%s</code></td>%s</tr>'
                    % (e(str(block["dev_account"])),
                       e(str(block["dev_account"])),
                       "".join('<td class=n>%s</td>' % e(str(cell))
                               for cell in cells)))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def badge(kind, labels, e):
    name = "label_" + kind
    return '<span class="badge %s">%s</span>' % (
        e(kind.replace("_", "-")), e(labels[name]))


def rows_table(envelope, labels, e, dash):
    head = (labels["col_kind"], labels["col_ref"], labels["col_listing"],
            labels["col_counterparty"], labels["col_since"],
            labels["col_detail"])
    head_html = "".join("<th>%s</th>" % e(cell) for cell in head)
    body = []
    for row in envelope["rows"]:
        detail = (dash if row["detail"] is None
                  else fmt(row["detail"], labels["empty_detail"]))
        listing = "<code>%s</code> %s" % (
            e(str(row["listing_key"])), e(str(row["listing_title"])))
        body.append(
            '<tr data-kind="%s" data-ref="%s"><td>%s</td>'
            '<td class=n>%s</td><td>%s</td><td><code>%s</code></td>'
            '<td>%s</td><td>%s</td></tr>'
            % (e(str(row["kind"])), e(str(row["ref_id"])),
               badge(str(row["kind"]), labels, e),
               e(str(row["ref_id"])), listing, e(str(row["counterparty"])),
               e(str(row["since_utc"])), e(str(detail))))
    if not body:
        return '<p class=empty>%s</p>' % e(labels["empty_scope"])
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def seller_section(block, labels, e, dash):
    return ("<h3>%s &middot; <code>%s</code></h3>"
            "<div class=kpi>%s</div>%s"
            % (e(labels["col_seller"]), e(str(block["dev_account"])),
               kpi_html(block, labels, e, dash),
               rows_table(block, labels, e, dash)))


def build_html(sellers, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    laws = [labels["law_count"], labels["law_partition"],
            labels["law_listings"], labels["law_oldest"], labels["law_order"],
            labels["law_family"], labels["law_detail"], labels["law_scope"],
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
    """AC-PWC75 (R3597): landing this pair and re-deriving the CEO face are ONE run.

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
        print("SELLER-TODO CHECK %s fails=%d html=%dB json=%dB"
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

    face = _refresh_face(args.out, args.json)

    print("SELLER-TODO %s bytes=%d sellers=%d duties=%d disputed=%d face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             payload["seller_count"],
             sum(int(b["total_count"]) for b in sellers),
             sum(int(b["claim_disputed_count"]) for b in sellers), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
