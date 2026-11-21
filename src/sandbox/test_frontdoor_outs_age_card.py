"""Suite for the artifact-list age card: the derived age gets one live consumer.

ONE criterion (AC-FDC9), pre-registered on the src/os/backlog.md board BEFORE
this file existed. R3142 shipped the card with the age block and no suite at
all; R3143 measured that gap while it was changing the same card, so the first
arm here is the absence branch it was written for.

The card is a pure consumption face over the block the exporter derives. It
never re-walks preview/ or qa/, never re-stamps a file, and an absent block
prints a named absence rather than a zero, because a fabricated
`oldest_days=0` would read as "everything is fresh" on the face that exists to
warn about staleness.

Usage: python test_frontdoor_outs_age_card.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "frontdoor.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "frontdoor-outs-age-card"

sys.path.insert(0, HERE)
import frontdoor  # noqa: E402  (the page module, import-time journey)

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def card_slice(text):
    start = text.index("def outs_age_card(")
    end = text.index("\ndef ", start + 1)
    return text[start:end]


def main():
    bad = []
    clean = {"outs_age": {"rows": 29, "measurable": 27, "unmeasurable": 2,
                          "oldest_days": 6, "over7": 0, "dup_rows": 0,
                          "distinct": 29, "collapsed": 27}}
    clean_html = frontdoor.outs_age_card(clean)

    # ---- p: an absent block is named and never printed as a zero. --------
    for empty in (None, {}, {"outs_age": None}, {"outs_age": {}}):
        html = frontdoor.outs_age_card(empty)
        if "absent" not in html:
            bad.append("absent-not-named")
        for token in ("rows=0", "oldest_days=0", "over7=0"):
            if token in html:
                bad.append("absent-fabricates-" + token.replace("=", ""))
    # ---- q: a shaped block prints its seven readings and the fold count. --
    for needle in ("OUTS-AGE rows=29", "measurable=27", "unmeasurable=2",
                   "oldest_days=6", "over7=0", "dup_rows=0", "distinct=29"):
        if needle not in clean_html:
            bad.append("clean-missing-" + needle.replace(" ", "_"))
    if "collapsed=27" not in clean_html:
        bad.append("collapsed-not-printed")
    # a face written before the fold existed carries no key: the line stays the
    # seven-reading line it always was, byte for byte, with no fabricated zero
    old = {"outs_age": dict((k, v) for k, v in clean["outs_age"].items()
                            if k != "collapsed")}
    old_html = frontdoor.outs_age_card(old)
    if "collapsed" in old_html:
        bad.append("old-face-invents-collapsed")
    if "OUTS-AGE rows=29" not in old_html:
        bad.append("old-face-line-changed")
    # ---- r: over7 alerts only when it is positive. ------------------------
    stale = {"outs_age": dict(clean["outs_age"], over7=3)}
    stale_html = frontdoor.outs_age_card(stale)
    if "older than seven days" not in stale_html:
        bad.append("over7-not-alerted")
    if "older than seven days" in clean_html:
        bad.append("over7-zero-alerts")
    for word in ("class=fail",):
        if word in clean_html:
            bad.append("clean-borrows-failure-class")

    # ---- s: pure consumption, ASCII source, one registry row, live page. --
    if frontdoor.outs_age_card(clean) != clean_html:
        bad.append("not-deterministic")
    moved = {"outs_age": dict(clean["outs_age"], rows=30, distinct=30)}
    if frontdoor.outs_age_card(moved) == clean_html:
        bad.append("not-derived-from-input")

    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad.append("module-bom")
    if b"\r\n" in raw:
        bad.append("module-crlf")
    try:
        text = raw.decode("utf-8")
        text.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        bad.append("module-not-ascii")
        text = raw.decode("utf-8", "replace")
    if "__SD30_OUTS_AGE__" not in text:
        bad.append("placeholder-missing")
    if "sd30_outs_age = outs_age_card(" not in text:
        bad.append("render-not-wired")
    if 'sd30_outs_age = ""' not in text:
        bad.append("absent-branch-not-wired")
    try:
        slice_text = card_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad.append("card-not-ascii")
        slice_text = ""
    for needle in ("os.walk", "listdir", "scandir", "open("):
        if needle in slice_text:
            bad.append("card-re-counts-" + needle.replace("(", ""))
    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)

    with io.open(EXPORT, "rb") as handle:
        live = json.loads(handle.read().decode("utf-8-sig"))
    want = frontdoor.outs_age_card((live.get("ceo_face") or {}))
    page = frontdoor.render().decode("utf-8")
    if want not in page:
        bad.append("live-card-not-on-page")

    report("AC-FDC9", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
