#!/usr/bin/env python3
"""Render the seller quality scorecard into one browsable page.

Why this exists: api_seller_quality shipped with its own AC-AMQL criteria and
answers the question a seller asks after the first few ratings - what shape is
my reputation, which live shelf drags it down, and what share of ratings has a
reply - but git grep -F over tools/ and preview/ finds ZERO readers, so the
only way to read it was to call the sandbox from a shell. dev_profile carries a
cross-listing average with no shape, api_seller_inbox carries the unanswered
rows only, and api_ratings opens one listing at a time.

Nothing here re-implements a market rule. Every number on the page comes from
src/sandbox/ledger/apimarket.py api_seller_quality() read over a fresh
throwaway demo world seeded through the shipped report helpers; the page prints
the buckets and rows it is handed and never recomputes one. The only arithmetic
added here is the visual width of a bar (count over the panel's own total),
which is stated on the page as a width, not as a rating.

The real sandbox is never opened for writing.

Usage:
  python tools/seller_quality_scorecard.py
  python tools/seller_quality_scorecard.py --check
Exit codes: 0 rendered or verified, 2 a landed size or recorded input moved,
            3 the shipped face or the label copy is missing.

AC-SQS1..AC-SQS6 are pre-registered in src/os/backlog.md (R3401 PIN) BEFORE
this file existed.

ASCII source, stdlib only, no network. Chinese labels live in
preview/seller-quality-scorecard-copy.json and appear in the rendered document
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

OUT_HTML = os.path.join(ROOT, "preview", "seller-quality-scorecard.html")
OUT_JSON = os.path.join(ROOT, "preview", "seller-quality-scorecard.json")
COPY = os.path.join(ROOT, "preview", "seller-quality-scorecard-copy.json")

FACE = "api_seller_quality"

# Pinned envelope keys (AC-SQS1). A missing one is a contract break rather than
# a silent blank on the page.
PINNED_KEYS = (
    "dev_account", "seller_count", "listing_count", "rating_count",
    "reply_count", "unanswered_count", "reply_coverage", "rating_avg",
    "star_distribution", "low_rated_count", "rows", "disclaimer",
)

# Pinned payload keys (AC-SQS1): the envelope plus the page-side weakest-live
# callout, the provenance block and the two blocks the --check gate reads.
PAYLOAD_KEYS = (
    "generated_utc", "face", "seller_count", "listing_count", "rating_count",
    "reply_count", "unanswered_count", "reply_coverage", "rating_avg",
    "star_distribution", "low_rated_count", "rows", "weakest", "disclaimer",
    "report", "sources", "sizes",
)

ROW_KEYS = (
    "listing_id", "listing_key", "title", "retired", "rating_count",
    "rating_avg", "unanswered_count", "reply_count", "lowest_stars",
    "star_distribution",
)

STARS = ("1", "2", "3", "4", "5")

COPY_KEYS = (
    "title", "sub", "gen", "src", "kpi_sellers", "kpi_listings", "kpi_ratings",
    "kpi_avg", "kpi_replied", "kpi_unanswered", "kpi_coverage", "kpi_low",
    "sec_stars", "sec_rows", "sec_weak", "sec_disc", "sec_rep",
    "col_listing", "col_state", "col_ratings", "col_avg", "col_lowest",
    "col_replied", "col_unanswered", "star_1", "star_2", "star_3", "star_4",
    "star_5", "state_live", "state_retired", "none", "weak_none", "aigc",
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
.meta{color:var(--muted);font-size:13px;margin-bottom:16px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin-bottom:14px;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;font-size:12px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpi{display:flex;gap:12px;flex-wrap:wrap}
.kpi div{flex:1 1 110px;border:1px solid var(--line);border-radius:8px;
padding:10px 12px;background:#fff}
.kpi b{display:block;font-size:19px;font-variant-numeric:tabular-nums}
.kpi span{color:var(--muted);font-size:12.5px}
.bars{display:flex;flex-direction:column;gap:6px}
.bar{display:grid;grid-template-columns:64px 1fr 56px;align-items:center;
gap:8px;font-size:12.5px}
.bar .track{background:#eef1f5;border-radius:4px;height:14px}
.bar .fill{background:#3d5a80;height:14px;border-radius:4px;min-width:0}
.bar b{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.disclaimer{border-left:3px solid #c9a227;background:#fdf8ea;padding:10px 14px;
font-size:13px}
.badge{display:inline-block;margin-right:8px;padding:2px 8px;
border:1px solid var(--line);border-radius:999px;font-size:12px;
color:var(--muted)}
.weak{font-size:14px}
.weak b{font-variant-numeric:tabular-nums}
footer{color:var(--muted);font-size:12px;margin:20px 0 8px}
code{font-size:12.5px;background:#f2f4f7;padding:1px 5px;border-radius:4px}
"""


DISCLAIMER_SLOT = "@@DISCLAIMER@@"


class FaceError(Exception):
    """Named refusal: the shipped face, or the label copy, is missing."""

    code = "E_SQS_FACE"


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
    tmp_root = tempfile.mkdtemp(prefix="seller-quality-scorecard-")
    db = os.path.join(tmp_root, "seller-quality-scorecard.db")
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
    if not isinstance(env.get("rows"), list):
        raise FaceError("rows is not a list: %r" % (env.get("rows"),))
    return env


def ordered(env):
    """AC-SQS4 read at the source: the row set must not arrive unsorted."""
    ids = [int(row["listing_id"]) for row in env["rows"]]
    return ids == sorted(ids)


def weakest_live(env):
    """The page-side callout: the lowest-rated live shelf that has ratings.

    A retired shelf is excluded by the face's own rule (a shelf nobody can buy
    no longer costs a buyer anything), and a tie names nobody rather than
    picking one arbitrarily.
    """
    rows = [r for r in env["rows"]
            if not r["retired"] and int(r["rating_count"]) > 0]
    if not rows:
        return None
    best = min(float(r["rating_avg"]) for r in rows)
    tied = [r for r in rows if float(r["rating_avg"]) == best]
    if len(tied) != 1:
        return None
    row = tied[0]
    return {"listing_id": row["listing_id"], "title": row["title"],
            "rating_avg": row["rating_avg"],
            "rating_count": row["rating_count"]}


def fmt(value, none_text):
    if value is None:
        return none_text
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value)


def pct(value):
    if value is None:
        return None
    return round(float(value) * 100.0, 1)


def build_html(env, weak, labels, now):
    e = html.escape
    kpi = [
        (labels["kpi_sellers"], fmt(env["seller_count"], labels["none"])),
        (labels["kpi_listings"], fmt(env["listing_count"], labels["none"])),
        (labels["kpi_ratings"], fmt(env["rating_count"], labels["none"])),
        (labels["kpi_avg"], fmt(env["rating_avg"], labels["none"])),
        (labels["kpi_replied"], fmt(env["reply_count"], labels["none"])),
        (labels["kpi_unanswered"], fmt(env["unanswered_count"],
                                        labels["none"])),
        (labels["kpi_coverage"],
         fmt(pct(env["reply_coverage"]), labels["none"])),
        (labels["kpi_low"], fmt(env["low_rated_count"], labels["none"])),
    ]
    kpi_html = "".join("<div><span>%s</span><b>%s</b></div>"
                       % (e(k), e(v)) for k, v in kpi)

    total = sum(int(env["star_distribution"].get(k, 0)) for k in STARS)
    bars = []
    for key in STARS:
        count = int(env["star_distribution"].get(key, 0))
        width = 0.0 if total <= 0 else round(count * 100.0 / total, 1)
        bars.append(
            '<div class=bar data-star="%s"><span>%s</span>'
            '<div class=track><div class=fill style="width:%.1f%%"></div></div>'
            "<b>%d</b></div>"
            % (e(key), e(labels["star_" + key]), width, count))
    stars = '<div class=bars>%s</div>' % "".join(bars)

    row_html = []
    for row in env["rows"]:
        state = (labels["state_retired"] if row["retired"]
                 else labels["state_live"])
        # A shelf nobody rated yet carries rating_avg 0.0 and lowest_stars None
        # in the envelope; printing that 0.0 would read as "rated zero stars",
        # so the row face prints the no-value mark and the count says why.
        unrated = int(row["rating_count"]) == 0
        avg_text = labels["none"] if unrated else fmt(row["rating_avg"],
                                                     labels["none"])
        lowest_text = (labels["none"] if unrated
                       else fmt(row["lowest_stars"], labels["none"]))
        row_html.append(
            "<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td>"
            "<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>"
            % (e(str(row["title"])), e(state),
               e(fmt(row["rating_count"], labels["none"])),
               e(avg_text), e(lowest_text),
               e(fmt(row["reply_count"], labels["none"])),
               e(fmt(row["unanswered_count"], labels["none"]))))
    rows = ("<table><tr><th>%s</th><th>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th><th class=n>%s</th><th class=n>%s</th>"
            "<th class=n>%s</th></tr>%s</table>"
            % (e(labels["col_listing"]), e(labels["col_state"]),
               e(labels["col_ratings"]), e(labels["col_avg"]),
               e(labels["col_lowest"]), e(labels["col_replied"]),
               e(labels["col_unanswered"]), "".join(row_html)))

    if weak is None:
        weak_text = e(labels["weak_none"])
    else:
        weak_text = ("%s &middot; %s / %s"
                     % (e(str(weak["title"])),
                        e(fmt(weak["rating_avg"], labels["none"])),
                        e(fmt(weak["rating_count"], labels["none"]))))

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
        "<h2>%s</h2>\n<div class=card><div class=disclaimer>%s</div>\n"
        "<p style=\"margin-top:10px\"><span class=badge>%s</span></p></div>\n"
        "<h2>%s</h2>\n<div class=card><code>%s</code></div>\n"
        "<footer>BigDomain OSLoop &middot; %s &middot; "
        "\u672c\u9875\u7531 tools/seller_quality_scorecard.py "
        "\u751f\u6210\uff0c\u4e0d\u624b\u6539</footer>\n</main></body></html>\n"
        % (e(labels["title"]), CSS, e(labels["title"]), e(labels["sub"]),
           e(labels["gen"]), e(now), e(FACE), kpi_html,
           e(labels["sec_stars"]), stars,
           e(labels["sec_rows"]), rows,
           e(labels["sec_weak"]), weak_text,
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
    """AC-PWC27 (R3549): landing this pair and re-deriving the CEO face are ONE run.

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
    except Exception as exc:  # a private world may carry no shared writer
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
        print("SELLER CHECK %s fails=%d html=%dB json=%dB"
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
    if not ordered(env):
        sys.stderr.write("E_SQS_ORDER: rows not sorted by listing_id %s\n"
                         % [r["listing_id"] for r in env["rows"]])
        return 3
    weak = weakest_live(env)

    _dt = __import__("datetime")
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    doc = build_html(env, weak, labels, now)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)

    payload = {
        "generated_utc": now,
        "face": FACE,
        "seller_count": env["seller_count"],
        "listing_count": env["listing_count"],
        "rating_count": env["rating_count"],
        "reply_count": env["reply_count"],
        "unanswered_count": env["unanswered_count"],
        "reply_coverage": env["reply_coverage"],
        "rating_avg": env["rating_avg"],
        "star_distribution": env["star_distribution"],
        "low_rated_count": env["low_rated_count"],
        "rows": env["rows"],
        "weakest": weak,
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
    print("SELLER %s bytes=%d sellers=%d listings=%d ratings=%d avg=%s "
          "coverage=%s weak=%s face=%s"
          % (payload["report"], len(doc.encode("utf-8")),
             env["seller_count"], env["listing_count"], env["rating_count"],
             fmt(env["rating_avg"], "-"), fmt(pct(env["reply_coverage"]), "-"),
             (weak or {}).get("listing_id"), face))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
