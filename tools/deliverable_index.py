#!/usr/bin/env python3
"""Render the CEO deliverable-index block into preview/index.html.

Editorial claims live in preview/deliverable-index.json. Every number inside
the rendered block (byte sizes, page titles, verdicts, timestamps) is derived
from disk at render time, so the walkthrough page cannot drift from the
artifacts it points at. The block is idempotent: rendering twice produces
byte-identical output, which is what --check measures.

Never writes to src/. Never touches the network.

Usage:
    python tools/deliverable_index.py          # render in place
    python tools/deliverable_index.py --check  # verify the landed block
"""

import hashlib
import html
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(REPO, "preview")
INDEX = os.path.join(PREVIEW, "index.html")
REGISTRY = os.path.join(PREVIEW, "deliverable-index.json")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
FREEZE = os.path.join(REPO, "state", "apimarket-face-freeze.json")
HIST_TAG_RE = re.compile(r'<span class="tag hist">\u5386\u53f2\u5feb\u7167\u00b7schema ')
HIST_OPEN = '<span class="tag hist">\u5386\u53f2\u5feb\u7167\u00b7schema '

# R3233: the claims census has ONE judgement, and this page is one of its two
# renderers. The other is src/sandbox/frontdoor.py's card. Probed before this
# change (qa/probe-R3233.log): the two faces carried separate key tuples and
# separate validation, already disagreed on a block whose `present` was a
# string, and a hand-drifted number in this page stayed silent under --check.
SANDBOX = os.path.join(REPO, "src", "sandbox")
if SANDBOX not in sys.path:
    sys.path.insert(0, SANDBOX)
import claims_view  # noqa: E402  (one derivation, shared with the live card)

TOOLS = os.path.join(REPO, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import buyer_route  # noqa: E402  (R3286: one closure of hop labels and order)
BEGIN = "<!-- BD-DELIVERABLE-INDEX:BEGIN -->"
END = "<!-- BD-DELIVERABLE-INDEX:END -->"
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
LINK_RE = re.compile(r'href="([^"]+)"')
CLAIMS_DIV_RE = re.compile(r'<div class="note" id="claims-census">(.*?)</div>', re.S)

# R3301: the three named-absence phrases are ONE author. They used to be typed
# in the renderer and again in the criterion, so naming the source document in
# the page (AC-COO8 requires it) left AC-CVL2 grading a sentence that no longer
# existed. Both readers take the words from here.
CENSUS_ABSENT = "no claims block in docs/status-export.json"
CENSUS_EMPTY = "nothing to census in docs/status-export.json (present=false)"
CENSUS_MALFORMED = "block in docs/status-export.json is malformed ("
# R3300 (AC-COO8): a copy of the export's time of day is what made this page's
# byte count swing on every --apply.
CLOCK_COPY_RE = re.compile(r"\d{2}:\d{2}:\d{2}")
BYTES_COPY_RE = re.compile(r"\d+B\b")
MARKERS = ["AIGC", "msgSecCheck", "\u6295\u987e", "19.9"]
COMPLIANCE = [
    "AIGC \u6807\u8bc6",
    "msgSecCheck \u524d\u7f6e\u95f8",
    "\u975e\u6295\u987e",
]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def load_registry():
    data = json.loads(read(REGISTRY))
    return data.get("faces", [])


def facts(entry):
    """Derive every displayed value from the artifact itself."""
    html_path = os.path.join(PREVIEW, entry["html"])
    json_path = os.path.splitext(html_path)[0] + ".json"
    text = read(html_path)
    m = TITLE_RE.search(text)
    title = html.unescape(m.group(1).strip()) if m else "(no title)"
    verdict, stamp = "n/a", ""
    if os.path.exists(json_path):
        try:
            blob = json.loads(read(json_path))
        except ValueError:
            blob = {}
        if isinstance(blob, dict):
            verdict = blob.get("verdict") or "n/a"
            stamp = blob.get("generated_utc") or ""
    if not stamp:
        import datetime
        stamp = "%sZ" % datetime.datetime.fromtimestamp(
            os.path.getmtime(html_path), datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S")
    defects = []
    if "%s" in title:
        defects.append("title placeholder not filled")
    return {
        "id": entry["id"],
        "html": entry["html"],
        "claim": entry["claim"],
        "blocker": entry["blocker"],
        "bytes": os.path.getsize(html_path),
        "json_bytes": os.path.getsize(json_path) if os.path.exists(json_path) else 0,
        "title": title,
        "verdict": str(verdict),
        "stamp": stamp,
        "defects": defects,
    }


def newest_artifact():
    """Derive the newest preview artifact pair by mtime (R2775).

    The registry is editorial and covers only the *-report.html family, so a
    face shipped under another filename family (first-yuan.html, journey-19.9
    .html) is invisible in the ledger table and the CEO entry page silently
    stopped carrying the window's newest artifact. This scans every preview
    *.json by mtime instead of trusting a name convention, and it never
    renders a blank recent-artifact line while artifacts exist (R2751 K1).
    """
    best = None
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".json"):
            continue
        stem = os.path.splitext(name)[0]
        # An artifact pair is X.html + X.json. The editorial registry
        # (deliverable-index.json) is not an artifact and carries no sibling
        # page, so it can never become the newest "shipped" face.
        if not os.path.exists(os.path.join(PREVIEW, stem + ".html")):
            continue
        if stem in BOARD_PAGES:
            continue
        path = os.path.join(PREVIEW, name)
        try:
            mtime = os.path.getmtime(path)
            nbytes = os.path.getsize(path)
        except OSError:
            continue
        if best is None or mtime > best[1]:
            best = (name, mtime, nbytes)
    if best is None:
        return {"json": "", "bytes": 0, "stamp": "", "empty": True}
    import datetime
    stamp = datetime.datetime.fromtimestamp(best[1]).strftime("%Y-%m-%dT%H:%M:%S")
    # R3296 (AC-DIX21): the row names the json, but the page a reader opens is
    # the sibling html - and a self-verify command prints the HTML byte count.
    # Both numbers live here so the band can quote the one the command reports.
    html_name = os.path.splitext(best[0])[0] + ".html"
    try:
        html_bytes = os.path.getsize(os.path.join(PREVIEW, html_name))
    except OSError:
        html_bytes = 0
    return {"json": best[0], "bytes": best[2], "stamp": stamp,
            "html": html_name, "html_bytes": html_bytes, "empty": False}


# R3298 (AC-DIX23): this binding used to be ONE global producer constant, so the
# command was only truthful while the apimarket pair happened to be newest. The
# day first-yuan-chain took the band the row degraded to a named absence - and a
# stamp alone would have been worse, because the printed command would have run
# the wrong producer (37201B instead of this pair's 4403B). The producer is now
# read from a per-pair table, and a producer whose only read-only flag is
# `--check` gets a check command carrying a named caveat: it proves the recipe
# still reproduces these bytes, not that the numbers are live.
PAIR_PRODUCERS = {
    "apimarket-report.json": "src/os/preview_apimarket_current.py",
    "first-yuan-chain.json": "tools/first_yuan_chain.py",
    # R3354: the shard report pair was regenerated by this owner but had no
    # recorded producer, so AC-DIX21/AC-DIX23 could only read a named absence.
    "battery-shard-report.json": "tools/battery_shard_report.py",
    # R3399: the market hourly activity page is a single-writer product (one
    # render, one json, no back-hop block), so it names its producer rather
    # than a recipe.
    "market-hour-heatmap.json": "tools/market_hour_heatmap.py",
    # R3400: same shape as the line above - one render, one json, no back-hop
    # block - so the asking-price distribution page names its producer.
    "market-price-percentiles.json": "tools/market_price_percentiles.py",
    # R3401: same shape again - one render, one json, no back-hop block - so
    # the seller quality scorecard names its producer rather than a recipe.
    "seller-quality-scorecard.json": "tools/seller_quality_scorecard.py",
    # R3402: same single-writer shape - one render, one json, no back-hop block
    # - so the category x month refund timeline names its producer.
    "category-refund-months.json": "tools/category_refund_months.py",
    # R3403: same single-writer shape again - one render, one json, no back-hop
    # block - so the category competitive-standing board names its producer.
    "listing-position-board.json": "tools/listing_position_board.py",
    # R3404: same single-writer shape again - one render, one json, no back-hop
    # block - so the similar-listing neighbour board names its producer.
    "similar-listing-board.json": "tools/similar_listing_board.py",
    # R3407: same single-writer shape - one render, one json, no back-hop block
    # - so the refund reason distribution page names its producer.
    "refund-reasons.json": "tools/refund_reasons_board.py",
    # R3408: same single-writer shape again - one render, one json, no back-hop
    # block - so the daily calendar settlement sheet names its producer.
    "market-daily.json": "tools/market_daily_board.py",
    # R3409: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer concentration ladder names its producer.
    "seller-concentration.json": "tools/seller_concentration_board.py",
    # R3410: same single-writer shape - one render, one json, no back-hop block
    # - so the seller month revenue page names its producer.
    "seller-revenue-board.json": "tools/seller_revenue_board.py",
    # R3411: same single-writer shape again - one render, one json, no back-hop
    # block - so the seller ledger statement page names its producer.
    "seller-ledger-board.json": "tools/seller_ledger_board.py",
    # R3412: same single-writer shape - one render, one json, no back-hop block
    # - so the seller refund exposure page names its producer.
    "refund-exposure.json": "tools/refund_exposure_board.py",
    # R3413: same single-writer shape - one render, one json, no back-hop block
    # - so the monthly buyer cohort page names its producer.
    "buyer-cohort.json": "tools/buyer_cohort_board.py",
    # R3414: same single-writer shape - one render, one json, no back-hop block
    # - so the monthly seller cohort page names its producer.
    "seller-cohort.json": "tools/seller_cohort_board.py",
    # R3415: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer wallet statement page names its producer.
    "buyer-ledger-board.json": "tools/buyer_ledger_board.py",
    "buyer-months-board.json": "tools/buyer_months_board.py",
    # R3417: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer monthly refund statement names its producer.
    "buyer-refund-months-board.json": "tools/buyer_refund_months_board.py",
    # R3418: same single-writer shape - one render, one json, no back-hop block
    # - so the whole-purchase dossier page names its producer.
    "purchase-dossier-board.json": "tools/purchase_dossier_board.py",
    # R3419: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer refund propensity page names its producer.
    "refund-propensity-board.json": "tools/refund_propensity_board.py",
    # R3420: same single-writer shape - one render, one json, no back-hop block
    # - so the shelf-to-sale velocity page names its producer.
    "listing-velocity-board.json": "tools/listing_velocity_board.py",
    # R3421: same single-writer shape - one render, one json, no back-hop block
    # - so the seller monthly refund page names its producer.
    "seller-refund-months-board.json": "tools/seller_refund_months_board.py",
    # R3424: same single-writer shape - one render, one json, no back-hop block
    # - so the seller refund cause page names its producer.
    "seller-refund-reasons-board.json": "tools/seller_refund_reasons_board.py",
    "public-listings-board.json": "tools/public_listings_board.py",
    # R3423: same single-writer shape - one render, one json, no back-hop block
    # - so the market discovery drill page names its producer.
    "search-board.json": "tools/search_board.py",
    # R3425: same single-writer shape - one render, one json, no back-hop block
    # - so the rating reply latency page names its producer.
    "reply-latency-board.json": "tools/reply_latency_board.py",
    # R3427: same single-writer shape - one render, one json, no back-hop block
    # - so the seller monthly rating page names its producer.
    "seller-rating-months-board.json": "tools/seller_rating_months_board.py",
    # R3428: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer concentration page names its producer.
    "buyer-concentration-board.json": "tools/buyer_concentration_board.py",
    # R3429: same single-writer shape - one render, one json, no back-hop block
    # - so the seller monthly returning-buyer page names its producer.
    "seller-repeat-months-board.json": "tools/seller_repeat_months_board.py",
    # R3430: same single-writer shape - one render, one json, no back-hop block
    # - so the resident account statement names its producer.
    "buyer-profile-board.json": "tools/buyer_profile_board.py",
    # R3432: same single-writer shape - one render, one json, no back-hop block
    # - so the seller shelf supply page names its producer.
    "seller-supply-board.json": "tools/seller_supply_board.py",
    # R3433: same single-writer shape - one render, one json, no back-hop block
    # - so the seller duty queue page names its producer.
    "seller-todo-board.json": "tools/seller_todo_board.py",
    # R3434: same single-writer shape - one render, one json, no back-hop block
    # - so the buyer watch alert page names its producer.
    "watch-alerts-board.json": "tools/watch_alerts_board.py",
    # R3435: the resident purchase library is a single-writer product (one
    # render, one json, no back-hop block), so it names its producer.
    "library-board.json": "tools/library_board.py",
}
# R3392 (AC-DIX21 recipe arm). One pair on this page cannot be reproduced by ONE
# command, and until now the law had only two answers - name a producer or print
# a named absence - so the pair either reddened the page or stayed unreproducible
# in silence. Measured in R3391/R3392: preview/ugc-gate-report.html is a
# TWO-WRITER product (tools/ugc_gate_report.py renders the body; tools/face_backhop.py
# injects the back-hop block and patches the recorded sizes), so the landed bytes
# are the product of a declared two-step recipe. R3392 also measured that running
# that renderer FIRST in the closeout ring does not dodge the question: the
# injector's size patch is the last write, so this pair is the newest one and the
# entry page must answer for it.
#
# The recipe is therefore DECLARED - both writers named here - and graded by
# running BOTH and requiring the pair's bytes to come back identical. No producer
# is invented, no criterion is loosened: a pair with neither a producer nor a
# recipe still prints the named absence, and a recipe that stops reproducing its
# pair reddens this page instead of hiding behind a printed number.
PAIR_RECIPES = {
    "ugc-gate-report.json": ("tools/ugc_gate_report.py",
                             "tools/face_backhop.py", ["--write"]),
    # R3395: same shape measured on the monthly ledger pair - the renderer
    # writes 9878B with no back-hop block and tools/face_backhop.py patches
    # the page afterwards (9878B, different sha16), so one command cannot
    # reproduce the landed bytes.
    "apimarket-monthly-faces.json": (
        "src/sandbox/ledger/monthly_faces_preview.py",
        "tools/face_backhop.py", ["--write"]),
}
RECIPE_CAVEAT = ("\u4e24\u6b65\u914d\u65b9\uff08\u6e32\u67d3+\u56de\u6ce8\uff09"
                 "\uff1a\u5b83\u8bc1\u8fd9\u5bf9\u5b57\u8282\u4ecd\u80fd\u88ab"
                 "\u4e24\u4f4d\u5199\u8005\u590d\u73b0\uff0c"
                 "\u4e0d\u8bc1\u9875\u5185\u6570\u5b57\u662f\u5b9e\u51b5")
SELF_VERIFY_FLAGS = ("--dry-run", "--stamp")
CHECK_CAVEAT = (
    "\u53ea\u8bc1\u8fd9\u4efd\u914d\u65b9\u8fd8\u80fd\u9020\u51fa\u540c\u4e00"
    "\u4efd\u5b57\u8282\uff0c\u4e0d\u8bc1\u9875\u5185\u6570\u5b57\u662f\u5b9e\u51b5")


def recipe_for(json_name):
    """The declared two-step recipe for THIS pair, or None.

    R3392: a recipe names both shipped writers (renderer, injector) so the law
    can grade the landed bytes without pretending one command made them.
    """
    return PAIR_RECIPES.get(json_name or "")


def producer_for(new):
    """(rel_path, why_not) - the producer recorded for THIS pair, never a global."""
    rel = PAIR_PRODUCERS.get(new.get("json") or "")
    if not rel:
        return None, ("no producer is recorded for %s"
                      % (new.get("json") or "this pair"))
    return rel, None


def newest_rendered_on(new):
    """The date the newest json says its page was rendered on, or None."""
    if not new.get("json"):
        return None
    try:
        doc = json.loads(read(os.path.join(PREVIEW, new["json"])))
    except (OSError, ValueError):
        return None
    value = doc.get("rendered_on") if isinstance(doc, dict) else None
    return value if isinstance(value, str) and value else None


def self_verify(new):
    """(command, mode, why_not) for the one command that reproduces the newest pair.

    R3296 (AC-DIX21): the index lists this pair as the newest deliverable and
    the reader still has to guess what to run. R3298 (AC-DIX23): the producer is
    the one the PAIR is recorded against, and two modes are told apart instead
    of one being assumed - a producer that declares `--dry-run`/`--stamp` and a
    json that records `rendered_on` gets the byte-counting dry run (mode
    'dry', the row may promise a number); a producer whose only read-only flag
    is `--check` gets that (mode 'check', the row quotes the recipe caveat,
    because re-deriving the bytes proves the recipe, not the readings).
    """
    if new.get("empty"):
        return None, None, "no artifact pair on disk"
    recipe = recipe_for(new.get("json") or "")
    if recipe is not None:
        render, inject, inject_args = recipe
        return ("python %s && python %s %s"
                % (render, inject, " ".join(inject_args))), "recipe", None
    rel, why_not = producer_for(new)
    if rel is None:
        return None, None, why_not
    path = os.path.join(REPO, *rel.split("/"))
    try:
        source = read(path)
    except OSError:
        return None, None, "producer %s is not on disk" % rel
    stamp = newest_rendered_on(new)
    if stamp and all(('"%s"' % f) in source for f in SELF_VERIFY_FLAGS):
        return ("python %s --dry-run --stamp %s" % (rel, stamp)), "dry", None
    if '"--check"' in source:
        return ("python %s --check" % rel), "check", None
    missing = [f for f in SELF_VERIFY_FLAGS if ('"%s"' % f) not in source]
    if missing:
        return None, None, ("producer no longer declares %s" % ",".join(missing))
    return None, None, "producer %s declares no read-only verify flag" % rel


# R3297 (AC-DIX22): two CEO pages answered "which pair is newest" with two
# different pairs - this band ranks by raw mtime, docs/status-export.json ranks
# by commit content time. A read-only probe measured the split as STRUCTURAL
# (31 of 40 pairs sat at a different position while every pair was committed
# and clean), not the dirty-tree corner the board first guessed. Merging on one
# law was measured too: the shared newest pair carries no rendered_on, so the
# self-verify command this band ships would degrade to a named absence the day
# it switched. Both laws stay; this band now states its own law and QUOTES the
# export face's answer, taken from the export face's own derivation.
def _export_round():
    src = os.path.join(REPO, "src", "os")
    if src not in sys.path:
        sys.path.insert(0, src)
    import importlib
    return importlib.import_module("export_round")


def export_law(new):
    """(view, why_not): the newest pair the EXPORT face would publish.

    view carries both file names, both byte counts and the clock word that
    derivation reports ('commit' when the winning half is committed and clean,
    'mtime' when it is dirty or the tree carries no git), plus same=True when
    both laws name the same json. Never a copy of the rule: the row comes from
    export_round.newest_artifact(), the single definition that face uses.
    """
    try:
        er = _export_round()
    except Exception as exc:   # report, never fabricate a pair
        return None, "shared derivation unavailable (%s)" % exc
    try:
        pair, _skipped, _board = er.newest_artifact(REPO)
    except Exception as exc:
        return None, "shared derivation raised %s" % exc
    if pair is None:
        return None, "the export face derives no pair"
    view = {
        "html": pair[1],
        "json": pair[2],
        "html_bytes": pair[3],
        "json_bytes": pair[4],
        "clock": pair[5],
        "same": os.path.basename(pair[2]) == (new.get("json") or ""),
    }
    return view, None


LAW_NOTE_RE = re.compile(
    r'<div class="note" data-law="(diff|same|none|static)">(.*?)</div>', re.S)


CLOCK_WORD_WIDTH = 6


def CLOCK_PAD(word):
    """Fixed-width clock word (R3298).

    The note's byte length used to depend on whether the pair ranked by
    'mtime' (5) or 'commit' (6), so preview/index.html changed size whenever
    the newest pair flipped between dirty and clean - and every face that
    embeds the entry page's byte count (data-back-bytes) went E_STALE with it.
    Padding to one width stops the entry page's size from depending on that
    state; HTML collapses the extra space, so the rendered sentence is
    unchanged.
    """
    return (word or "").ljust(CLOCK_WORD_WIDTH)


# R3393 (AC-BYI1..AC-BYI5, pinned in src/os/backlog.md BEFORE this code): the
# same class of defect CLOCK_PAD exists for, one level deeper. Every face that
# matches the catch-all back-hop rule carries `data-back-bytes` = THE SIZE OF
# THIS PAGE, and this page quotes the size of every face - so page size and
# face bytes were each other's input. Measured in R3392: at the instant the
# newest pair flipped, the entry page reddened its own recipe arm
# (`pair-bytes-reproduced=False`) and only a second ring pass converged it.
# A number whose WIDTH varies with its value feeds that loop; padding it to one
# width inside the HTML source (whitespace collapses, the rendered sentence and
# the exact value are unchanged) takes the width out of the page's size.
BYTES_WIDTH = 9


def BYTES_PAD(count):
    """Fixed-width byte count, e.g. '    28799B' (see BYTES_WIDTH)."""
    return ("%" + str(BYTES_WIDTH) + "dB") % count


def newest_line(new):
    """The one derived line AC-DIX8 compares against a fresh read."""
    if new["empty"]:
        return "preview/ carries no json artifact yet - stated, not blank."
    # R3296: both sizes, because the self-verify command prints the html byte
    # count while this band used to quote only the json's.
    return "%s \u00b7 json=%s \u00b7 html=%s \u00b7 %s" % (
        new["json"], BYTES_PAD(new["bytes"]),
        BYTES_PAD(new.get("html_bytes", 0)), new["stamp"])


def render_newest(new):
    out = []
    out.append("<h2>\u6700\u65b0\u5b9e\u7269\uff08\u76d8\u4e0a mtime \u6d3e\u751f\uff0c\u7981\u5199\u6b7b\uff09</h2>")
    out.append('<div class="note">%s</div>' % html.escape(newest_line(new)))
    command, mode, why_not = self_verify(new)
    if command and mode == "dry":
        out.append(
            '<div class="note">\u81ea\u5df1\u9a8c\u4e00\u904d\uff08\u547d\u4ee4'
            '\u53c2\u6570\u73b0\u8bfb\u81ea\u4ea7\u51fa\u5668\u4e0e\u8be5\u5bf9'
            '\u6587\u4ef6\uff0c\u975e\u624b\u5199\uff09\uff1a'
            '<code>%s</code>\uff0d\u5b83\u4f1a\u62a5\u51fa\u540c\u4e00\u4e2a '
            '<b>%s</b> \u5e76\u4e14\u4e0d\u5199\u4efb\u4f55\u5b57\u8282\u3002</div>'
            % (html.escape(command), BYTES_PAD(new.get("html_bytes", 0))))
    elif command and mode == "recipe":
        # R3392: the pair is a declared two-step product, so the row prints BOTH
        # writers instead of one command it cannot honestly claim.
        out.append(
            '<div class="note">\u81ea\u5df1\u9a8c\u4e00\u904d\uff08\u4e24\u6b65'
            '\u914d\u65b9\u73b0\u8bfb\u81ea\u914d\u5bf9\u8868\uff0c\u975e\u624b'
            '\u5199\uff09\uff1a<code>%s</code>'
            '\uff0d\u5b83%s\uff1b\u8dd1\u5b83\u4f1a\u91cd\u5199\u8fd9\u4e24'
            '\u4f4d\u5199\u8005\u7684\u4ea7\u7269\uff08\u5e42\u7b49\uff1a'
            '\u5b57\u8282\u5e94\u9010\u5bf9\u56de\u6765\uff09\u3002</div>'
            % (html.escape(command), html.escape(RECIPE_CAVEAT)))
    elif command:
        # R3298 (AC-DIX23): a check-mode producer re-derives and compares bytes;
        # the row must not let that read as proof of the numbers themselves.
        out.append(
            '<div class="note">\u81ea\u5df1\u9a8c\u4e00\u904d\uff08\u547d\u4ee4'
            '\u4e0e\u4ea7\u51fa\u5668\u73b0\u8bfb\u81ea\u914d\u5bf9\u8868\uff0c'
            '\u975e\u624b\u5199\uff09\uff1a<code>%s</code>'
            '\uff0d\u5b83%s\uff1b'
            '\u8dd1\u5b83\u4e0d\u5199\u4efb\u4f55\u5b57\u8282\u3002</div>'
            % (html.escape(command), html.escape(CHECK_CAVEAT)))
    else:
        out.append('<div class="note">\u65e0\u81ea\u9a8c\u547d\u4ee4\uff1a%s'
                   '\uff08\u5982\u5b9e\u547d\u540d\uff0c\u4e0d\u7f16\u9020\uff09</div>'
                   % html.escape(why_not))
    # AC-DIX22 (R3301, exit 2): the note is now FULLY STATIC. R3297/R3300 shipped
    # three answer-shaped branches (diff/same/none) and R3300 measured the
    # consequence: the export face's own answer to "which pair is newest" flips
    # with the last write, so any page that copies that answer - even as one
    # boolean - cannot be a fixed point, and closeout_order --write stayed rc=2.
    # The disagreement is still measured, but it is READ (closeout_order --plan
    # prints one LAW row) instead of copied here.
    out.append(
        '<div class="note" data-law="static">\u672c\u5e26\u6309\u6587\u4ef6 '
        'mtime \u6392\u540d\uff1b<code>docs/status-export.json</code> '
        '\u6309\u63d0\u4ea4\u5185\u5bb9\u65f6\u949f\u6392\u540d\u3002\u5bfc'
        '\u51fa\u9762\u9009\u51fa\u7684\u90a3\u4e00\u5bf9\u4e0e\u4e24\u4e2a'
        '\u5b57\u8282\u6570\u5199\u5728\u90a3\u4efd\u6587\u6863\u91cc\uff0c'
        '\u672c\u9875\u4e0d\u590d\u5236\uff08\u590d\u5236\u4f1a\u8ba9\u672c'
        '\u9875\u5b57\u8282\u968f\u5bfc\u51fa\u9762\u91cd\u5199\u800c\u53d8'
        '\uff09\u3002\u4e24\u6cd5\u6b64\u523b\u662f\u5426\u610f\u89c1\u4e0d'
        '\u540c\uff0c\u7531 <code>python tools/closeout_order.py --plan</code> '
        '\u7684 LAW \u884c\u53ea\u8bfb\u5370\u51fa\u3002</div>')
    out.append('<div class="note">%s</div>' % html.escape(NEWEST_SNAPSHOT))
    return "\n".join(out)


GATE_PAGES = ("index", "deliverable-index")

# AC-DIX16 (pinned 2026-11-15 R2804 before this code): the BOARD pages re-render on every
# closeout and are not product faces, but they were winning the "newest artifact" race and
# stealing the band from the artifact the window actually shipped - which reddened this page
# one render later, and reddened the export face (AC-EXPW1) after that. Boards are CEO-openable
# and stay in the pairs band; they are simply not "the newest thing the line produced".
BOARD_PAGES = ("face-sweep", "ceo-blockers")

# AC-DIX15 (pinned 2026-11-15 R2804 before this code): the newest band quotes a byte count
# and an mtime that belong to whatever rendered that face LAST. Re-rendering that face in the
# same closeout changes both, which is why this page read AC-DIX3/AC-DIX8 red the moment the
# sweep board was refreshed after it. The band must therefore LABEL those two numbers a
# snapshot, and its live assertion must be the artifact NAME - the fact a reader needs is
# "which face is newest", never "how many bytes it had at 23:10".
NEWEST_SNAPSHOT = ("Snapshot: the size and stamp above were measured when this page was rendered; "
                   "a later re-render of that face changes them. The live fact this band asserts "
                   "is which artifact is newest, not its byte count.")


def artifact_pairs():
    """Every shipped preview face (X.html, paired or not), newest first (R2777).

    R2775's band carries only the single newest pair, so a face that shipped
    two windows ago is unreachable from the CEO entry page once a newer one
    lands (measured: ceo-blockers, face-sweep and city-observatory all read
    zero links in index.html). This derives the FULL list from the directory
    instead of a name convention: a face exists when its html is on disk, and
    the gate page plus the editorial registry are never product faces.
    """
    pairs = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        stem = name[:-5]
        if stem in GATE_PAGES:
            continue
        json_name = stem + ".json"
        hpath = os.path.join(PREVIEW, name)
        jpath = os.path.join(PREVIEW, json_name)
        # AC-DIX17 (pinned 2026-11-17 R2883 before this code): the universe is
        # every html FACE, not every pair. A page whose json sibling is absent
        # is still on disk and still CEO-openable; skipping it here made the
        # entry page's own claim ("every shipped face stays reachable") false
        # for two measured faces without reddening any criterion.
        paired = os.path.exists(jpath)
        if not os.path.exists(hpath):
            continue
        try:
            nbytes = os.path.getsize(hpath)
            mtime = os.path.getmtime(hpath)
        except OSError:
            continue
        pairs.append({"stem": stem, "html": name,
                      "json": json_name if paired else "",
                      "paired": paired, "bytes": nbytes, "mtime": mtime})
    pairs.sort(key=lambda p: (-p["mtime"], p["stem"]))
    return pairs


def frozen_hist():
    """stem -> declared schema (None = no sibling) for every frozen face.

    R3291 (AC-DIX20): a reader can see from the entry page that a link is a
    historical snapshot before clicking it. The list is derived from the freeze
    manifest, so a face frozen or released there appears or disappears here -
    never a second written-down list of names.
    """
    try:
        doc = json.loads(read(FREEZE))
    except (OSError, ValueError):
        return {}
    rows = doc.get("faces")
    if not isinstance(rows, list):
        return {}
    out = {}
    for row in rows:
        html_name = row.get("html")
        if not isinstance(html_name, str):
            continue
        stem = os.path.splitext(os.path.basename(html_name))[0]
        value = row.get("schema_version")
        out[stem] = None if value is None else int(value)
    return out


def hist_tag(schema):
    return '%s%s</span>' % (HIST_OPEN, "\u672a\u77e5" if schema is None else schema)


def render_pairs(pairs):
    """The all-pairs band, derived row by row (never a written-down list)."""
    hist = frozen_hist()
    out = ["<h2>\u5168\u90e8\u5df2\u4e0a\u7ebf\u9762\uff08\u76d8\u4e0a pair \u6d3e\u751f\u00b7\u70b9\u5f00\u5373\u770b\uff09</h2>"]
    if not pairs:
        out.append('<div class="note">preview/ \u76ee\u524d\u6ca1\u6709 '
                   "html+json \u6210\u5bf9\u9762\u2014\u2014\u5b9e\u8bdd\u76f4\u8bf4\uff0c"
                   "\u4e0d\u7559\u7a7a\u884c\u3002</div>")
        return "\n".join(out)
    out.append('<div class="note">\u672c\u5757\u9762\u6570=%d\uff0c\u9010\u6761\u76f4\u63a5'
               "\u4ece <code>preview/</code> \u626b\u63cf\u5f97\u51fa\uff1a"
               "\u9762\u540d\u00b7\u5b57\u8282\u00b7\u65f6\u95f4\u6233\u5747\u5b9e\u8bfb\u3002</div>"
               % len(pairs))
    out.append("<ul>")
    for p in pairs:
        import datetime
        stamp = datetime.datetime.fromtimestamp(p["mtime"]).strftime("%Y-%m-%d %H:%M")
        paired = p.get("paired", True)
        label = ("json=%s" % p["json"]) if paired else "json=missing"
        tag = (" " + hist_tag(hist[p["stem"]])) if p["stem"] in hist else ""
        out.append(
            '<li><a href="%s">%s</a> <span class="tag">%s</span> '
            '<span class="tag">%s</span> <span class="tag%s">%s</span>%s</li>'
            % (html.escape(p["html"]), html.escape(p["stem"]),
               BYTES_PAD(p["bytes"]),
               html.escape(stamp), "" if paired else " warn",
               html.escape(label), tag)
        )
    out.append("</ul>")
    return "\n".join(out)


def read_claims():
    """Read the export face's claims block at render time, or None if absent."""
    try:
        blob = json.loads(read(EXPORT))
    except (OSError, ValueError):
        return None
    block = blob.get("claims")
    return block if isinstance(block, dict) else None


def claims_readings(view):
    """The exact six readings this page prints, or None when it prints none.

    R3234: the readings line has ONE author. AC-CVL1 compares the landed page
    against this function's output from a fresh view, so the criterion cannot
    restate the format string and quietly agree with itself.
    """
    if view["state"] != claims_view.READING:
        return None
    counts = view["counts"]
    return ("claimed=%d captured=%d contradicted=%d uncaptured=%d "
            "historic=%d records=%d"
            % (counts["claimed"], counts["captured"], counts["contradicted"],
               counts["uncaptured"], counts["historic"], counts["rows"]))


def claims_band(block):
    """Print the census readings and their moment, or a named honest absence.

    This page is a static file a reader opens by path, so it has to say how old
    its own reading is; AC-DIX19 pins the printed moment to the live export.

    R3233: the readings and the shape verdict come from claims_view, the same
    judgement src/sandbox/frontdoor.py's card reads - so the file a reader
    opens and the page the hub serves can no longer say two different worlds.
    Only the prose is per surface. The one behaviour that changed here: a block
    that carries the six readings but no census_ts is now a READING with a
    named missing moment (it used to be called "block malformed"), which is
    what the card already said; the numbers are the export's, the moment is
    not, and no moment is invented.
    """
    view = claims_view.claims_view(block)
    if view["state"] == claims_view.ABSENT:
        return ('<div class="note" id="claims-census">claims census: '
                + CENSUS_ABSENT + '; no moment invented.</div>')
    if view["state"] == claims_view.EMPTY:
        return ('<div class="note" id="claims-census">claims census: '
                + CENSUS_EMPTY + '; no moment invented.</div>')
    if view["state"] == claims_view.MALFORMED:
        return ('<div class="note" id="claims-census">claims census: '
                + CENSUS_MALFORMED + '%s); no moment invented.</div>'
                % ",".join(view["bad"]))
    readings = claims_readings(view)
    ts = view["stamp"]
    if not ts:
        return ('<div class="note" id="claims-census">claims census: %s \u00b7 '
                'docs/status-export.json carries no census_ts; the numbers are '
                'the export\'s and the moment is not - no moment invented.</div>'
                % readings)
    # R3300 (AC-COO8): the exact moment is deliberately NOT copied here. A page
    # that printed the export's full census_ts changed bytes on every --apply,
    # and first-yuan-chain embeds this page's byte count, so the two drag each
    # other round a ring no ordering can close. A day is ten characters wide
    # whatever the time of day, so the edge stops carrying a clock; the exact
    # moment keeps one authority - the export document itself.
    return ('<div class="note" id="claims-census">claims census: %s \u00b7 '
            'census day %s (the day is derived from docs/status-export.json at '
            'render time; the exact moment lives in that document and is not '
            'copied here, so re-rendering is not owed to an --apply - AC-COO8 '
            'refuses a printed moment).</div>'
            % (readings, html.escape(ts[:10])))


def render_body(rows, defects_total, newest, pairs, claims):
    # R3286 (AC-IDX1): the entry page used to list every face flat and never say
    # which page a first-time reader should open first. The walk is the SAME
    # closure the face footers use, measured at render time.
    out = [buyer_route.render_block(buyer_route.FIRST_VISIT), ""]
    out.append(render_newest(newest))
    out.append(render_pairs(pairs))
    out.append("")
    out.append(claims_band(claims))
    out.append("<h2>\u5b9e\u7269\u53f0\u8d26\uff08\u4e00\u9875\u70b9\u8fdb\u6bcf\u4e2a\u5b9e\u6d4b\u9762\uff09</h2>")
    out.append(
        '<div class="note">\u672c\u5757\u7531 <code>tools/deliverable_index.py</code> '
        "\u4ece\u76d8\u4e0a\u6d3e\u751f\uff08\u5c3a\u5bf8\u00b7\u6807\u9898\u00b7verdict\u00b7"
        "\u65f6\u95f4\u6233\u5747\u5b9e\u8bfb\uff0c\u7981\u5199\u6b7b\uff09\u3002"
        "\u9762\u6570=%d \u00b7 \u672a\u586b\u6807\u9898\u5360\u4f4d=%d \u00b7 "
        "\u8bf7\u4ee5 <code>--check</code> \u590d\u6838\u4e00\u81f4\u6027\u3002</div>"
        % (len(rows), defects_total)
    )
    out.append(
        '<div class="disclaimer">\u5e38\u9a7b\u5408\u89c4\u4e09\u9762\uff1a'
        "<b>AIGC \u6807\u8bc6</b>\uff08\u751f\u6210\u5185\u5bb9\u5168\u5448\u73b0\u9762\u6807\u6ce8\uff09\u00b7 "
        "<b>msgSecCheck \u524d\u7f6e\u95f8</b>\uff08\u5185\u5bb9\u5b89\u5168\u672a\u63a5\u7981\u5f00\u95e8\uff09\u00b7 "
        "<b>\u975e\u6295\u987e</b>\uff08\u672c\u5e73\u53f0\u4ea7\u51fa\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff09\u3002</div>"
    )
    out.append("<table>")
    out.append(
        "<tr><th>#</th><th>\u9762</th><th>\u5b9e\u7269\uff08\u70b9\u5f00\u5373\u770b\uff09</th>"
        "<th>\u5b9e\u6d4b\u5224\u636e</th><th>\u5360\u4f4d / \u963b\u585e</th></tr>"
    )
    for i, r in enumerate(rows, 1):
        tag = "ok" if r["verdict"].upper() == "PASS" else "warn"
        cell = (
            '<a href="%s">%s</a><br>'
            '<span class="tag %s">verdict=%s</span> '
            '<span class="tag">%s</span> '
            '<span class="tag">%s</span>'
            % (r["html"], r["html"], tag, html.escape(r["verdict"]),
               BYTES_PAD(r["bytes"]),
               html.escape(r["stamp"]))
        )
        if r["defects"]:
            cell += ' <span class="tag ceo">%s</span>' % html.escape(
                "; ".join(r["defects"]))
        out.append(
            "<tr><td>%d</td><td><b>%s</b><br>%s</td><td>%s</td><td>%s</td>"
            "<td>%s</td></tr>"
            % (
                i,
                html.escape(r["id"]),
                html.escape(r["title"]),
                cell,
                html.escape(r["claim"]),
                html.escape(r["blocker"]),
            )
        )
    out.append("</table>")
    return "\n".join(out)


def render_block():
    rows = [facts(e) for e in load_registry()]
    defects = sum(len(r["defects"]) for r in rows)
    newest = newest_artifact()
    pairs = artifact_pairs()
    claims = read_claims()
    body = render_body(rows, defects, newest, pairs, claims)
    fp = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return (
        "%s\n%s\n<!-- fingerprint %s -->\n%s" % (BEGIN, body, fp, END), fp, rows,
        newest, pairs
    )


def strip_block(text):
    if BEGIN not in text or END not in text:
        return text
    head = text.split(BEGIN)[0]
    tail = text.split(END, 1)[1]
    return head + tail


def get_block(text):
    if BEGIN not in text or END not in text:
        return ""
    return BEGIN + text.split(BEGIN, 1)[1].split(END, 1)[0] + END


def inject(text, block):
    if BEGIN in text and END in text:
        head = text.split(BEGIN)[0]
        tail = text.split(END, 1)[1]
        return head + block + tail
    idx = text.find("<h2>")
    if idx < 0:
        raise SystemExit("index.html has no <h2> anchor to insert the block before")
    return text[:idx] + block + "\n\n  " + text[idx:]


def front_count(text):
    """Count RD1 real fronts with the candidate index.html text in place.

    The gate itself reads preview/ from disk, so the candidate text is scored
    here against the same three shipped conditions instead of being written out.
    """
    sys.path.insert(0, os.path.join(REPO, "src", "sandbox", "benchgate"))
    import bench_gate  # noqa: E402

    def qualifies(body, nbytes):
        markers_ok = all(m in body for m in bench_gate.MARKERS)
        external = [t for t in bench_gate.EXTERNAL_REF_TOKENS if t in body]
        return nbytes >= 4096 and markers_ok and not external

    names = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html") or name == "index.html":
            continue
        path = os.path.join(PREVIEW, name)
        if qualifies(read(path), os.path.getsize(path)):
            names.append(name)
    if qualifies(text, len(text.encode("utf-8"))):
        names.append("index.html")
    return names


def main(argv):
    check = "--check" in argv[1:]
    text = read(INDEX)
    stat_before = (os.path.getsize(INDEX), os.path.getmtime(INDEX))
    block, fp, rows, newest, pairs = render_block()

    checks = []

    def record(code, ok, detail):
        checks.append((code, ok, detail))

    registered = {e["html"] for e in load_registry()}
    on_disk = {n for n in os.listdir(PREVIEW)
               if n.endswith("-report.html")
               and os.path.exists(os.path.join(PREVIEW, os.path.splitext(n)[0] + ".json"))}
    record("AC-DIX1", registered == on_disk,
           "registry=%d disk=%d missing=%s extra=%s"
           % (len(registered), len(on_disk),
              sorted(on_disk - registered), sorted(registered - on_disk)))

    size_rows = [r for r in rows
                 if (("%s</span>" % BYTES_PAD(r["bytes"])) in block
                     and r["html"] in block)]
    record("AC-DIX2", len(size_rows) == len(rows),
           "quoted-sizes=%d of %d, each equal to os.path.getsize" % (len(size_rows), len(rows)))

    landed = get_block(text)
    # AC-DIX15 relaxed the byte-equality of this criterion, not its purpose: the landed band
    # must still name the same newest face the fresh scan names, and must label its size and
    # stamp a snapshot, so a same-closeout re-render of that face cannot redden the page.
    landed_name = (newest["json"] or "") in landed
    label_ok = NEWEST_SNAPSHOT in landed
    record("AC-DIX3", landed_name and label_ok,
           "landed-names-newest=%s snapshot-label=%s fingerprint=%s"
           % (landed_name, label_ok, fp))

    clean = strip_block(text)
    before = set(front_count(clean))
    after = set(front_count(text))
    markers_ok = all(m in text for m in MARKERS)
    scheme_ok = ("http://" not in text) and ("https://" not in text)
    record("AC-DIX4", markers_ok and scheme_ok and before == after and
           os.path.getsize(INDEX) >= 4096,
           "markers=%s scheme_free=%s fronts_before=%d fronts_after=%d bytes=%d"
           % (markers_ok, scheme_ok, len(before), len(after), os.path.getsize(INDEX)))

    links = LINK_RE.findall(block)
    bad = [l for l in links
           if "/" in l or ":" in l or not os.path.exists(os.path.join(PREVIEW, l))]
    record("AC-DIX5", bool(links) and not bad,
           "links=%d relative-and-present=%d bad=%s" % (len(links), len(links) - len(bad), bad))

    have = [c for c in COMPLIANCE if c in block]
    blockers = [r for r in rows if r["blocker"]]
    record("AC-DIX6", len(have) == len(COMPLIANCE) and len(blockers) == len(rows),
           "compliance=%d/%d blocker-named=%d/%d" % (len(have), len(COMPLIANCE),
                                                     len(blockers), len(rows)))

    # AC-IDX1 (pinned 2026-11-22 R3286 in src/os/backlog.md BEFORE this code):
    # the entry page listed every face flat and said nothing about what to open
    # first. Measured before this change: index.html was 39637B with 55 hrefs and
    # no walk; four targets were already linked, so no link target is invented.
    # Scored against the page a reader opens, from the same closure the face
    # footers print - the arms live in buyer_route.first_visit_problems().
    idx_block = get_block(text) if check else block
    idx_problems = buyer_route.first_visit_problems(idx_block)
    record("AC-IDX1", not idx_problems,
           "first-visit=%s" % (idx_problems[:3] or "ok"))

    # R2804: scored against the LANDED page, not the block this run just built. AC-DIX3 used
    # to catch a tampered ledger row only because it compared the whole landed block byte for
    # byte; that comparison is gone (it was the two-page interlock), so the row-level claim has
    # to be made against the file a reader actually opens.
    quoted = [r for r in rows if ("verdict=%s" % html.escape(r["verdict"])) in text]
    record("AC-DIX7", len(quoted) == len(rows),
           "verdicts-quoted=%d/%d defect-rows=%d"
           % (len(quoted), len(rows), sum(1 for r in rows if r["defects"])))

    # AC-DIX8 (pinned 2026-11-15 R2775 before this code was written): the
    # newest-artifact band must equal a FRESH mtime scan of preview/*.json, so
    # the entry page cannot keep pointing at last window's face after a new
    # one lands, and it may never read as a blank line while artifacts exist.
    fresh = newest_artifact()
    want = newest_line(fresh)
    # The criterion must score the LANDED document, not the block this run just
    # built: comparing the fresh derivation against the fresh render is a
    # self-matching test that passes on any bytes (R2760/R2761 class, caught
    # here by control c2 of tmp/negctl_dix8_R2775.py).
    landed_block = get_block(text) if check else block
    # AC-DIX15 (R2804): the NAME is the live fact. The byte count and stamp are a snapshot of
    # whichever render came last, so they are asserted as labelled, never as equal.
    landed_names_fresh = (fresh["json"] or "") in landed_block
    record("AC-DIX8", landed_names_fresh and (NEWEST_SNAPSHOT in landed_block),
           "newest=%s bytes=%d names_fresh=%s snapshot_label=%s"
           % (fresh["json"] or "(none)", fresh["bytes"], landed_names_fresh,
              NEWEST_SNAPSHOT in landed_block))

    # AC-DIX9..AC-DIX14 (pinned 2026-11-15 R2777 in src/os/backlog.md BEFORE
    # this code): the all-pairs band must list every shipped face on disk, so
    # a page landed two windows ago stays reachable from the CEO entry page.
    fresh_pairs = artifact_pairs()
    listed = [p for p in pairs
              if ('href="%s"' % html.escape(p["html"])) in landed_block]
    record("AC-DIX9", len(pairs) == len(fresh_pairs) and len(listed) == len(pairs),
           "band-rows=%d fresh-scan=%d listed-in-landed=%d"
           % (len(pairs), len(fresh_pairs), len(listed)))

    missing = [p["html"] for p in pairs
               if not os.path.exists(os.path.join(PREVIEW, p["html"]))
               or (p["paired"] and not os.path.exists(os.path.join(PREVIEW, p["json"])))]
    record("AC-DIX10", not missing, "pairs=%d missing-targets=%s"
           % (len(pairs), missing))

    if check:
        record("AC-DIX11", (os.path.getsize(INDEX), os.path.getmtime(INDEX)) == stat_before,
               "check-left-size+mtime-unchanged=%s"
               % ((os.path.getsize(INDEX), os.path.getmtime(INDEX)) == stat_before))
    else:
        record("AC-DIX11", True, "writer mode: this run is the intended author")

    band_text = render_pairs(pairs)
    record("AC-DIX12", ("http://" not in band_text) and ("https://" not in band_text),
           "band-offline=%s rows=%d"
           % (("http://" not in band_text) and ("https://" not in band_text),
              len(pairs)))

    wrong = [p["html"] for p in pairs
             if (("%s</span>" % BYTES_PAD(p["bytes"])) not in band_text)]
    record("AC-DIX13", not wrong, "self-referential-bytes-wrong=%s" % wrong)

    gate = [p["stem"] for p in pairs if p["stem"] in GATE_PAGES]
    record("AC-DIX14", not gate, "gate-pages-listed=%s" % gate)

    # AC-DIX17 (pinned 2026-11-17 R2883 before this code): the universe is
    # re-measured from RAW html names, never through artifact_pairs(), so an
    # html-only face cannot fall off the CEO entry page unnoticed - an unpaired
    # face must be listed and labelled, not quietly dropped.
    raw_faces = sorted(n for n in os.listdir(PREVIEW)
                       if n.endswith(".html")
                       and os.path.splitext(n)[0] not in GATE_PAGES)
    unlisted = [n for n in raw_faces
                if ('href="%s"' % html.escape(n)) not in landed_block]
    unlabelled = []
    for p in pairs:
        if p["paired"]:
            continue
        at = landed_block.find('href="%s"' % html.escape(p["html"]))
        if at < 0 or "json=missing" not in landed_block[at:at + 400]:
            unlabelled.append(p["html"])
    record("AC-DIX17", not unlisted and not unlabelled,
           "html-faces=%d unlisted=%s unlabelled-incomplete=%s"
           % (len(raw_faces), unlisted, unlabelled))

    # AC-DIX19 (pinned 2026-11-22 R3232 before this code; renumbered from the
    # R3232 plan's AC-DIX18 because this suite already used that label for a
    # control name): this page is a static file, so the moment it prints has to
    # be the export's current moment. A page left behind by an --apply must
    # redden rather than keep a quiet old stamp.
    live_claims = read_claims()
    live_ts = None
    if isinstance(live_claims, dict) and isinstance(live_claims.get("census_ts"), str):
        live_ts = live_claims["census_ts"] or None
    if live_ts:
        printed = ("census day %s" % html.escape(live_ts[:10])) in landed_block
        record("AC-DIX19", printed,
               "export-census-day=%s printed-in-%s=%s"
               % (live_ts[:10], "landed" if check else "block", printed))
    else:
        named = "no moment invented" in landed_block
        record("AC-DIX19", named,
               "export-claims=none named-absence-in-page=%s" % named)

    # AC-CVL1/AC-CVL2 (pinned 2026-11-22 R3234 BEFORE this code): AC-DIX19 pins
    # the moment this static page prints and never the six numbers beside it.
    # Measured (qa/probe-R3234.log): hand-editing contradicted=11 -> 999 left
    # --check at rc=0, and so did moving the export block without a re-render.
    # The readings line is now compared, value by value, against the same
    # claims_readings() the page renders from - one author, not two.
    live_view = claims_view.claims_view(live_claims)
    census = CLAIMS_DIV_RE.search(landed_block)
    div_text = census.group(1) if census else ""

    # AC-COO8 (pinned 2026-11-22 R3300 in src/os/backlog.md BEFORE this code):
    # the entry page must not carry the export's time of day at all, and must
    # name the document that does. The day is what keeps AC-DIX19 gradeable
    # without letting a clock ride into this file's bytes. A page with no
    # claims block still has to keep the no-clock promise.
    no_clock = CLOCK_COPY_RE.search(div_text) is None
    source_named = "docs/status-export.json" in div_text
    if live_ts:
        day_named = ("census day %s" % html.escape(live_ts[:10])) in div_text
        record("AC-COO8", no_clock and source_named and day_named,
               "clock-copy=%s source-named=%s day=%s"
               % (not no_clock, source_named, day_named))
    else:
        fell_back = "no moment invented" in div_text
        record("AC-COO8", no_clock and source_named and fell_back,
               "clock-copy=%s source-named=%s named-absence=%s"
               % (not no_clock, source_named, fell_back))

    want_readings = claims_readings(live_view)
    if want_readings is not None:
        printed_readings = want_readings in div_text
        record("AC-CVL1", printed_readings,
               "live-readings=%r printed=%s" % (want_readings, printed_readings))
    else:
        absence = {claims_view.ABSENT: CENSUS_ABSENT,
                   claims_view.EMPTY: CENSUS_EMPTY,
                   claims_view.MALFORMED: CENSUS_MALFORMED}[live_view["state"]]
        named = (absence in div_text) and ("claimed=" not in div_text)
        record("AC-CVL2", named,
               "live-state=%s named-absence=%s invented-numbers=%s"
               % (live_view["state"], absence in div_text,
                  "claimed=" in div_text))

    # AC-DIX20 (pinned 2026-11-22 R3291 in src/os/backlog.md BEFORE this code):
    # the frozen apimarket faces carry an in-page schema banner, but the entry
    # page still listed all thirteen as ordinary rows, so a reader could not
    # tell a schema-3 snapshot from a current face before clicking. Each frozen
    # row now carries its declared schema, taken from the freeze manifest; a
    # released or newly frozen face changes this page without a second list.
    hist = frozen_hist()
    hist_tagged = []
    for stem, schema in sorted(hist.items()):
        at = landed_block.find('href="%s.html"' % html.escape(stem))
        if at >= 0 and (hist_tag(schema) in landed_block[at:at + 400]):
            hist_tagged.append(stem)
    leaked = []
    for p in pairs:
        if p["stem"] in hist:
            continue
        at = landed_block.find('href="%s"' % html.escape(p["html"]))
        if at >= 0 and (HIST_OPEN in landed_block[at:at + 400]):
            leaked.append(p["stem"])
    printed_tags = len(HIST_TAG_RE.findall(landed_block))
    record("AC-DIX20",
           bool(hist) and len(hist_tagged) == len(hist)
           and printed_tags == len(hist) and not leaked,
           "frozen=%d tagged=%d printed=%d leaked=%s"
           % (len(hist), len(hist_tagged), printed_tags, leaked))

    # AC-DIX21 (pinned 2026-11-22 R3296 in src/os/backlog.md BEFORE this code):
    # this page lists the newest pair and used to leave the reader with no way
    # to check it themselves. The band now prints one command whose module path,
    # flags and stamp are all read from sources; this criterion runs that command
    # ONCE and grades what it reports. Measured before the change
    # (qa/probe-R3296.log): the dry run reports 37201 bytes - the HTML count,
    # not the 59815 the band used to quote alone - and leaves both files byte
    # identical, so the row must quote both numbers for the command to be true.
    # Cost: one extra deterministic render, measured 0.292s (the sweep the
    # closeout already runs; no standing second pass is added to production).
    command, mode, why_not = self_verify(fresh)
    band = landed_block if check else block
    rel = None
    if command is None:
        absence = "\u65e0\u81ea\u9a8c\u547d\u4ee4\uff1a%s" % html.escape(why_not)
        record("AC-DIX21", absence in band,
               "no-command-reason=%r printed-as-named-absence=%s"
               % (why_not, absence in band))
    else:
        recipe = recipe_for(fresh.get("json") or "")
        if recipe is not None:
            rel = recipe[0]
        else:
            rel, _why = producer_for(fresh)
        target = os.path.join(REPO, *rel.split("/"))
        stamp = newest_rendered_on(fresh)
        html_path = os.path.join(PREVIEW, fresh["html"])
        json_path = os.path.join(PREVIEW, fresh["json"])

        def stat_pair(path):
            try:
                return (os.path.getsize(path), os.path.getmtime(path))
            except OSError:
                return None

        def read_pair():
            out = []
            for path in (html_path, json_path):
                try:
                    with open(path, "rb") as fh:
                        out.append(fh.read())
                except OSError:
                    out.append(None)
            return tuple(out)

        printed_once = band.count(html.escape(command)) == 1
        printed_html = ("html=%s" % BYTES_PAD(fresh.get("html_bytes", 0))) in band
        before = (stat_pair(html_path), stat_pair(json_path))
        if mode != "recipe":
            flags = (["--dry-run", "--stamp", stamp] if mode == "dry"
                     else ["--check"])
            proc = subprocess.run(
                [sys.executable, target] + flags,
                cwd=REPO, capture_output=True, text=True)
            after = (stat_pair(html_path), stat_pair(json_path))

        if mode == "recipe":
            # R3392: two declared writers, and the law is BYTE EQUALITY of the
            # pair they land - not a number either of them prints. A recipe that
            # stops reproducing its pair reddens here even though both writers
            # still exit 0.
            render_mod, inject_mod, inject_args = recipe
            mods = [os.path.join(REPO, *rel.split("/"))
                    for rel in (render_mod, inject_mod)]
            before_bytes = read_pair()
            rc_render = subprocess.run([sys.executable, mods[0]],
                                       cwd=REPO, capture_output=True,
                                       text=True).returncode
            rc_inject = subprocess.run([sys.executable, mods[1]] + inject_args,
                                       cwd=REPO, capture_output=True,
                                       text=True).returncode
            after_bytes = read_pair()
            arms = {
                "printed-once": printed_once,
                "both-modules-on-disk": all(os.path.exists(m) for m in mods),
                "rc0-both": rc_render == 0 and rc_inject == 0,
                "pair-bytes-reproduced": (before_bytes == after_bytes
                                          and None not in after_bytes),
                "row-quotes-html": printed_html,
                "caveat-printed": html.escape(RECIPE_CAVEAT) in band,
            }
            record("AC-DIX21", all(arms.values()),
                   "mode=recipe cmd=%r rc=%d/%d html=%dB json=%dB %s"
                   % (command, rc_render, rc_inject, fresh.get("html_bytes", 0),
                      fresh["bytes"],
                      " ".join("%s=%s" % (k, v)
                               for k, v in sorted(arms.items())
                               if not v) or "all-arms-green"))
        elif mode == "dry":
            dry_lines = [ln for ln in (proc.stdout or "").splitlines()
                         if ln.startswith("DRY ")]
            dry = dry_lines[-1] if dry_lines else ""
            m_bytes = re.search(r"bytes=(\d+)", dry)
            m_stamp = re.search(r"stamp=(\d{4}-\d{2}-\d{2})", dry)
            reported = int(m_bytes.group(1)) if m_bytes else -1
            reported_stamp = m_stamp.group(1) if m_stamp else ""
            arms = {
                "printed-once": printed_once,
                "module-on-disk": os.path.exists(target),
                "rc0": proc.returncode == 0,
                "dry-line": bool(dry),
                "bytes-eq-html-eq-row": (reported == fresh.get("html_bytes", 0)
                                         == (os.path.getsize(html_path)
                                            if os.path.exists(html_path)
                                            else -2)),
                "row-quotes-html": printed_html,
                "stamp-eq-page": reported_stamp == stamp,
                "nothing-written": before == after,
            }
            record("AC-DIX21", all(arms.values()),
                   "mode=dry cmd=%r dry=%r html=%dB json=%dB %s"
                   % (command, dry, fresh.get("html_bytes", 0), fresh["bytes"],
                      " ".join("%s=%s" % (k, v)
                               for k, v in sorted(arms.items())
                               if not v) or "all-arms-green"))
        else:
            m_html = re.search(r"html=(\d+)B", proc.stdout or "")
            reported = int(m_html.group(1)) if m_html else -1
            arms = {
                "printed-once": printed_once,
                "module-on-disk": os.path.exists(target),
                "rc0": proc.returncode == 0,
                "nothing-written": before == after,
                "html-eq-row": (reported == fresh.get("html_bytes", 0)
                                == (os.path.getsize(html_path)
                                   if os.path.exists(html_path) else -2)),
                "caveat-printed": html.escape(CHECK_CAVEAT) in band,
                "row-quotes-html": printed_html,
            }
            record("AC-DIX21", all(arms.values()),
                   "mode=check cmd=%r html=%dB json=%dB rc=%d %s"
                   % (command, fresh.get("html_bytes", 0), fresh["bytes"],
                      proc.returncode,
                      " ".join("%s=%s" % (k, v)
                               for k, v in sorted(arms.items())
                               if not v) or "all-arms-green"))

    # AC-DIX23 (pinned 2026-11-22 R3298 in src/os/backlog.md BEFORE this code):
    # the command used to be bound to ONE producer constant, so the day another
    # pair took the band the row either lied (wrong producer) or went silent.
    # This criterion grades the BINDING, not a number: the path printed must be
    # the table's value for this very json, the table must carry more than one
    # producer, an unknown pair must be refused by name, and the mode must be
    # announced in the row (a byte promise for a dry run, the recipe caveat for
    # a check run) - neither may stand in for the other.
    unknown, _umode, why_unknown = self_verify({"json": "no-such-pair.json",
                                                "empty": False})
    if command and mode == "dry":
        promise = (("<b>%s</b>" % BYTES_PAD(fresh.get("html_bytes", 0)))
                   in band)
    elif command and mode == "recipe":
        # R3392: a recipe announces itself as a recipe - it may not borrow the
        # single-command caveat, and its own caveat may not stand in for a
        # byte promise nobody can make.
        promise = (html.escape(RECIPE_CAVEAT) in band
                   and html.escape(CHECK_CAVEAT) not in band)
    elif command:
        promise = html.escape(CHECK_CAVEAT) in band
    else:
        # R3301: with no recorded producer the row is a NAMED ABSENCE, and this
        # arm used to demand the check-run caveat there - a sentence an absence
        # cannot carry, so the arm was red for every pair outside the table.
        # The intent ("neither may stand in for the other") is kept by refusing
        # the opposite: an absence that still prints a promise or caveat.
        promise = (absence in band) and (html.escape(CHECK_CAVEAT) not in band)
    arms = {
        "one-command-or-absence": (band.count(html.escape(command)) == 1
                                   if command else absence in band),
        "per-pair-table": (len(PAIR_PRODUCERS) >= 2
                           and len(set(PAIR_PRODUCERS.values())) >= 2),
        "path-from-table": (command is None
                            or rel == PAIR_PRODUCERS.get(fresh["json"])
                            or rel == (PAIR_RECIPES.get(fresh["json"]) or ("",))[0]),
        "unknown-refused": unknown is None and bool(why_unknown),
        "mode-announced": promise,
    }
    record("AC-DIX23", all(arms.values()),
           "pair=%s producer=%s mode=%s %s"
           % (fresh.get("json") or "-", rel or "-", mode or "-",
              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items())
                       if not v) or "all-arms-green"))

    # AC-DIX22 (pinned 2026-11-22 R3297, rewritten R3301 exit 2): two CEO pages
    # ranked "newest" by two different clocks. Measured (qa/probe-R3297.log): 31
    # of 40 pairs sat at a different position with every pair committed and
    # clean, so the split is structural. R3300 then measured the answer itself
    # flipping with the last write, which makes any copy of it - pair name, byte
    # counts, or one boolean - a non-fixed-point page. This arm now grades a
    # STATIC note: both laws named, the other answer's single source named, the
    # read-only witness named, and no copied value. The fresh derivation is
    # still computed here and printed as gate evidence; it is never rendered.
    law_view, _law_why = export_law(fresh)
    notes = LAW_NOTE_RE.findall(band)
    marks = [mark for mark, _body in notes]
    law_body = notes[0][1] if notes else ""
    arms = {"one-law-note": len(notes) == 1}
    arms["mark-static"] = marks == ["static"]
    arms["own-law-stated"] = ("mtime" in law_body
                              and "\u63d0\u4ea4\u5185\u5bb9" in law_body)
    arms["source-named"] = "docs/status-export.json" in law_body
    arms["witness-named"] = ("closeout_order" in law_body
                             and "--plan" in law_body)
    arms["no-bytes-copied"] = (BYTES_COPY_RE.search(law_body) is None
                               and "preview/" not in law_body)
    arms["no-clock-copied"] = CLOCK_COPY_RE.search(law_body) is None
    record("AC-DIX22", all(arms.values()),
           "law=%s (still derived here, never rendered) %s"
           % ("none" if law_view is None
              else ("same" if law_view["same"] else "diff"),
              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items())
                       if not v) or "all-arms-green"))

    if check:
        for code, ok, detail in checks:
            print("%s %-9s %s" % ("PASS" if ok else "FAIL", code, detail))
        failed = [c for c, ok, _ in checks if not ok]
        print("VERDICT %s %d/%d fingerprint=%s" %
              ("PASS" if not failed else "FAIL", len(checks) - len(failed),
               len(checks), fp))
        print(json.dumps({"passed": len(checks) - len(failed), "total": len(checks),
                          "failed": failed, "fingerprint": fp}, sort_keys=True))
        return 0 if not failed else 2

    new_text = inject(text, block)
    with open(INDEX, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    print("DELIVERABLE INDEX faces=%d defects=%d fingerprint=%s index=%dB" %
          (len(rows), sum(len(r["defects"]) for r in rows), fp,
           os.path.getsize(INDEX)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
