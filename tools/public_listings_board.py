#!/usr/bin/env python3
"""Render the public shelf compliance face into one page a human can open.

Why this exists: api_public_listings answers "what does the outside reader see
on the shelf right now - the review state, the registered provider identity,
the AIGC label and the price" with its own AC-AMPI4 criteria, but git grep
over tools/ and preview/ found no reader at all, so the reading could only be
had by calling the sandbox from a shell. Nobody could see, on one page, that
the shelf is fully pending and that not one listing is disclosed.

Nothing here re-implements a market rule. Every number comes from the shipped
api_public_listings() face read over a fresh throwaway demo world seeded
through the shipped report helpers. The page prints what the face hands it and
recomputes only the two published identities (the disclosure flag and the
review-state precedence) plus its own stated counts; a broken identity refuses
the render instead of printing a plausible page.

The real sandbox is never opened for writing and nothing touches the network.

Usage:
  python tools/public_listings_board.py
  python tools/public_listings_board.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face, a law, or the label copy refused.

AC-PLB1..AC-PLB6 are pre-registered in src/os/backlog.md (R3422 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/public-listings-board-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "public-listings-board.html")
OUT_JSON = os.path.join(ROOT, "preview", "public-listings-board.json")
COPY = os.path.join(ROOT, "preview", "public-listings-board-copy.json")

FACE = "api_public_listings"
QUEUE_FACE = "api_review_queue"

# Pinned payload keys (AC-PLB1).
PAYLOAD_KEYS = (
    "generated_utc", "face", "source_face", "listing_count",
    "review_pending_count", "disclosure_ok_count", "ai_label_count",
    "disclosed_and_labeled", "seller_count", "shelf_total", "top_price",
    "listings", "disclaimer", "report", "sources", "sizes",
)

# The shipped listing row, 13 keys (AC-PLB1).
LISTING_KEYS = (
    "listing_id", "dev_account", "listing_key", "title", "token_price",
    "ai_label", "listed_utc", "provider_name", "credit_code",
    "disclosure_ok", "review_state", "review_reason", "reviewed_utc",
)

STATES = ("pending", "approved", "refused")

COPY_KEYS = (
    "title", "sub", "gen", "aigc", "sec_listings", "sec_law", "sec_disc",
    "sec_rep", "kpi_listings", "kpi_pending", "kpi_disclosed", "kpi_labeled",
    "kpi_both", "kpi_sellers", "kpi_shelf", "kpi_top", "col_pos", "col_id",
    "col_seller", "col_key", "col_title", "col_price", "col_listed",
    "col_review", "col_reason", "col_reviewed", "col_disclosure", "col_label",
    "col_provider", "col_credit", "yes", "no", "none", "pending", "approved",
    "refused", "empty", "law_count", "law_pending", "law_disclosure",
    "law_label", "law_both", "law_reason", "law_order", "law_cross",
    "law_notready", "law_notadvice", "rep", "cmd",
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
.flag-no{color:#b42318;font-weight:600}
.flag-yes{color:#1f6f43;font-weight:600}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.law{font-size:13px;margin:6px 0}
.empty{color:#b42318}
footer{color:var(--muted);font-size:12px;margin:18px 0 0}
"""

DISCLAIMER_SLOT = "__DISCLAIMER_SLOT__"


class FaceError(Exception):
    code = "E_PLB_FACE"

    def __init__(self, message, code=None):
        super(FaceError, self).__init__(message)
        if code:
            self.code = code


class LawError(Exception):
    code = "E_PLB_LAW"


def read_copy():
    if not os.path.exists(COPY):
        raise FaceError("label copy missing: %s" % COPY)
    with open(COPY, "r", encoding="utf-8") as fh:
        labels = json.load(fh)
    missing = [key for key in COPY_KEYS if not str(labels.get(key, "")).strip()]
    if missing:
        raise FaceError("label copy keys missing: %s" % ",".join(missing))
    return labels


def read_world():
    """One shipped public-shelf envelope plus the queue face it must agree with."""
    tmp_root = tempfile.mkdtemp(prefix="public-listings-board-")
    db = os.path.join(tmp_root, "public-listings-board.db")
    led = mtr = dk = am = None
    try:
        led, mtr, dk, am = R.build_stack(db)
        R.seed_demo(am, led, dk)
        env = dict(getattr(am, FACE)())
        queue = dict(getattr(am, QUEUE_FACE)())
    except AttributeError as exc:
        raise FaceError("%s: %s" % (FACE, exc)) from exc
    finally:
        for obj in (am, dk, mtr, led):
            if obj is not None:
                try:
                    obj.close()
                except Exception:
                    pass
    missing = [key for key in LISTING_KEYS
               if any(key not in row for row in env["listings"])]
    if missing:
        raise FaceError("listing keys missing: %s" % ",".join(missing))
    return env, queue


def derived(env):
    """The counts this page states out loud, recomputed from the rows."""
    rows = env.get("listings") or []
    prices = [int(row["token_price"]) for row in rows]
    return {
        "ai_label_count": sum(1 for row in rows if int(row["ai_label"]) == 1),
        "disclosed_and_labeled": sum(
            1 for row in rows
            if bool(row["disclosure_ok"]) and int(row["ai_label"]) == 1),
        "seller_count": len({str(row["dev_account"]) for row in rows}),
        "shelf_total": sum(prices),
        "top_price": max(prices) if prices else None,
    }


def check_laws(env, queue):
    """AC-PLB3 read at the source: refuse rather than print."""
    problems = []
    rows = env.get("listings") or []
    if int(env["listing_count"]) != len(rows):
        problems.append("listing_count %s != rows %d"
                        % (env["listing_count"], len(rows)))
    pending = [row for row in rows if row["review_state"] == "pending"]
    if int(env["review_pending_count"]) != len(pending):
        problems.append("review_pending_count %s != pending rows %d"
                        % (env["review_pending_count"], len(pending)))
    disclosed = [row for row in rows if row["disclosure_ok"]]
    if int(env["disclosure_ok_count"]) != len(disclosed):
        problems.append("disclosure_ok_count %s != disclosed rows %d"
                        % (env["disclosure_ok_count"], len(disclosed)))
    if int(queue.get("pending_count", -1)) != int(env["review_pending_count"]):
        problems.append("cross-face pending %s != queue %s"
                        % (env["review_pending_count"],
                           queue.get("pending_count")))
    previous = None
    for row in rows:
        tag = "listing %s" % row["listing_id"]
        lid = int(row["listing_id"])
        if previous is not None and lid <= previous:
            problems.append("%s listing_id not strictly ascending" % tag)
        previous = lid
        if row["review_state"] not in STATES:
            problems.append("%s review_state %r" % (tag, row["review_state"]))
        identity = (row["provider_name"] is not None
                    and row["credit_code"] is not None)
        if bool(row["disclosure_ok"]) != identity:
            problems.append("%s disclosure_ok %r != identity %r"
                            % (tag, row["disclosure_ok"], identity))
        if row["review_state"] == "refused":
            if not str(row["review_reason"] or "").strip():
                problems.append("%s refused without a reason" % tag)
        elif row["review_reason"] is not None:
            problems.append("%s review_reason on %s"
                            % (tag, row["review_state"]))
        if row["review_state"] == "pending":
            if row["reviewed_utc"] is not None:
                problems.append("%s reviewed_utc on pending" % tag)
        elif row["reviewed_utc"] is None:
            problems.append("%s reviewed_utc missing on %s"
                            % (tag, row["review_state"]))
    return problems


def bar_none(value, none_text):
    return none_text if value is None else str(value)


def flag(value, labels):
    return labels["yes"] if value else labels["no"]


def state_text(state, labels):
    return labels.get(state, state)


def kpi_html(env, stats, labels, e, dash):
    items = [
        (labels["kpi_listings"], env["listing_count"]),
        (labels["kpi_pending"], env["review_pending_count"]),
        (labels["kpi_disclosed"], env["disclosure_ok_count"]),
        (labels["kpi_labeled"], stats["ai_label_count"]),
        (labels["kpi_both"], stats["disclosed_and_labeled"]),
        (labels["kpi_sellers"], stats["seller_count"]),
        (labels["kpi_shelf"], stats["shelf_total"]),
        (labels["kpi_top"], bar_none(stats["top_price"], dash)),
    ]
    return "".join('<div><span>%s</span><b>%s</b></div>'
                   % (e(str(k)), e(str(v))) for k, v in items)


def listings_table(env, labels, e, dash):
    head = (labels["col_pos"], labels["col_id"], labels["col_seller"],
            labels["col_key"], labels["col_title"], labels["col_price"],
            labels["col_listed"], labels["col_review"],
            labels["col_reason"], labels["col_reviewed"],
            labels["col_disclosure"], labels["col_label"],
            labels["col_provider"], labels["col_credit"])
    right = set(head[1:1] + head[3:4] + head[5:6])
    head_html = "".join('<th class=n>%s</th>' % e(cell) if cell in right
                        else "<th>%s</th>" % e(cell) for cell in head)
    body = []
    for position, row in enumerate(env.get("listings") or [], 1):
        disclosed = bool(row["disclosure_ok"])
        labeled = int(row["ai_label"]) == 1
        cells = [
            ("n", str(position)),
            ("n", str(row["listing_id"])),
            ("", str(row["dev_account"])),
            ("", str(row["listing_key"])),
            ("", str(row["title"])),
            ("n", str(row["token_price"])),
            ("", str(row["listed_utc"])),
            ("", state_text(row["review_state"], labels)),
            ("", bar_none(row["review_reason"], dash)),
            ("", bar_none(row["reviewed_utc"], dash)),
            ("flag-%s" % ("yes" if disclosed else "no"),
             flag(disclosed, labels)),
            ("flag-%s" % ("yes" if labeled else "no"), flag(labeled, labels)),
            ("", bar_none(row["provider_name"], dash)),
            ("", bar_none(row["credit_code"], dash)),
        ]
        tds = "".join('<td class="%s">%s</td>' % (klass, e(value))
                      for klass, value in cells)
        body.append('<tr data-listing="%s">%s</tr>' % (e(str(row["listing_id"])),
                                                       tds))
    return "<table><tr>%s</tr>%s</table>" % (head_html, "".join(body))


def build_html(env, labels, now, disclaimer):
    e = html.escape
    dash = labels["none"]
    stats = derived(env)
    laws = [labels["law_count"], labels["law_pending"],
            labels["law_disclosure"], labels["law_label"], labels["law_both"],
            labels["law_reason"], labels["law_order"], labels["law_cross"],
            labels["law_notready"], labels["law_notadvice"]]
    law_html = "".join('<p class=law>%s</p>' % e(line) for line in laws)
    if env.get("listings"):
        table_html = listings_table(env, labels, e, dash)
    else:
        table_html = "<p class=empty>%s</p>" % e(labels["empty"])
    doc = (
        '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style></head><body><main>\n"
        "<h1>%s</h1>\n"
        '<div class=meta>%s &middot; %s %s &middot; <code>%s</code></div>\n'
        "<div class=card><div class=kpi>%s</div></div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card>%s</div>\n"
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        '<p style="margin-top:10px"><span class=badge>%s</span></p></div>\n'
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/public_listings_board.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE),
           kpi_html(env, stats, labels, e, dash),
           e(labels["sec_listings"]), table_html,
           e(labels["sec_law"]), law_html,
           e(labels["sec_disc"]), DISCLAIMER_SLOT, e(labels["aigc"]),
           e(labels["sec_rep"]), e(labels["cmd"]), e(now))
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
    """AC-PWC55 (R3577): landing this pair and re-deriving the CEO face are ONE run.

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
        print("PUBLIC-LISTINGS CHECK %s fails=%d html=%dB json=%dB"
              % ("PASS" if not fails else "FAIL", len(fails),
                 os.path.getsize(args.out) if os.path.exists(args.out) else -1,
                 os.path.getsize(args.json) if os.path.exists(args.json)
                 else -1))
        for item in fails:
            print("  - %s" % item)
        return 0 if not fails else 2

    try:
        labels = read_copy()
        env, queue = read_world()
    except FaceError as exc:
        sys.stderr.write("%s: %s\n" % (exc.code, exc))
        return 3
    problems = check_laws(env, queue)
    if problems:
        for item in problems:
            sys.stderr.write("%s: %s\n" % (LawError.code, item))
        return 3

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, labels, now, env["disclaimer"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    stats = derived(env)
    payload = {
        "generated_utc": now,
        "face": FACE,
        "source_face": FACE,
        "listing_count": env["listing_count"],
        "review_pending_count": env["review_pending_count"],
        "disclosure_ok_count": env["disclosure_ok_count"],
        "ai_label_count": stats["ai_label_count"],
        "disclosed_and_labeled": stats["disclosed_and_labeled"],
        "seller_count": stats["seller_count"],
        "shelf_total": stats["shelf_total"],
        "top_price": stats["top_price"],
        "listings": [{key: row[key] for key in LISTING_KEYS}
                     for row in env["listings"]],
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

    print("PUBLIC-LISTINGS %s bytes=%d listings=%d pending=%d disclosed=%d "
          "face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             len(payload["listings"]), payload["review_pending_count"],
             payload["disclosure_ok_count"], face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
