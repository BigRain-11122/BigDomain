"""Suite for the claims card: the published census readings get a live consumer
on the only face that keeps being rendered after the loop stops.

THREE criteria, AC-FDC17..19, pre-registered in the R3230 PIN row of
src/os/backlog.md BEFORE the card existed. AC-FDC20 was added the same round,
after landing this card proved that a data value quoting a placeholder literal
was substituted a second time (three claims cards on one page).

R3230 measured the hole (probe qa/probe-R3230.log): R3229 published all seven
census readings into docs/status-export.json, and src/sandbox/frontdoor.py
carried ZERO site that read the `claims` key - so claimed / captured /
contradicted / uncaptured / historic / rows / present were invisible to the
CEO page while the terminal printed them once per round.

The card is a pure consumption face: it reads the block, it never re-censuses,
never stats a file, and it must not print the `rows=<n>` token the census
counts (measured: the live page already carries 15 such tokens from shipped
cards, so the law grades the delta this card adds).

Usage: python test_frontdoor_claims_card.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "frontdoor.py")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "frontdoor-claims-card"

sys.path.insert(0, HERE)
import frontdoor  # noqa: E402  (the page module, import-time journey)

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def live_block():
    try:
        with io.open(EXPORT, "rb") as handle:
            data = json.loads(handle.read().decode("utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data.get("claims")


def function_slice(text):
    start = text.index("def claims_card(")
    end = text.index("\ndef face_age_card(", start)
    return text[start:end]


HEALTHY = {"claimed": 309, "captured": 107, "contradicted": 11,
           "uncaptured": 191, "historic": 7, "rows": 6, "present": True}


def numbers_in(html):
    return re.findall(r"(?:claimed|captured|contradicted|uncaptured|historic|"
                      r"records)=\d+", html)


def main():
    bad = []

    # ---- AC-FDC17 a: a healthy block prints all seven readings. ----------
    a_html = frontdoor.claims_card(dict(HEALTHY))
    for needle in ("claimed=309", "captured=107", "contradicted=11",
                   "uncaptured=191", "historic=7", "records=6"):
        if needle not in a_html:
            bad.append("healthy-missing-" + needle)
    if "conservation holds" not in a_html:
        bad.append("conservation-unnamed")
    # ---- b: non-zero census counts are READINGS, never verdicts. ---------
    if "class=fail" in a_html:
        bad.append("reading-wears-fail")
    if "carry no citation" not in a_html:
        bad.append("uncaptured-unnamed")
    if "contradict the source" not in a_html:
        bad.append("contradicted-unnamed")
    # ---- c: zero counts name no hint at all. -----------------------------
    zero = {"claimed": 0, "captured": 0, "contradicted": 0,
            "uncaptured": 0, "historic": 0, "rows": 0, "present": True}
    c_html = frontdoor.claims_card(dict(zero))
    if "carry no citation" in c_html or "contradict the source" in c_html:
        bad.append("zero-carries-hint")
    if "class=fail" in c_html:
        bad.append("zero-carries-fail")
    # ---- d: a block whose own counts do not add up IS a defect. ----------
    d_block = dict(HEALTHY, captured=100)
    d_html = frontdoor.claims_card(d_block)
    if "conservation broken" not in d_html:
        bad.append("broken-conservation-unnamed")
    if "class=fail" not in d_html:
        bad.append("broken-conservation-not-flagged")
    if "claimed=309" not in d_html:
        bad.append("broken-conservation-hides-numbers")
    # ---- e: derived, not typed; same input twice is byte-identical. ------
    if frontdoor.claims_card(dict(HEALTHY)) != a_html:
        bad.append("not-deterministic")
    e_html = frontdoor.claims_card(dict(HEALTHY, historic=2))
    if "historic=2" not in e_html:
        bad.append("typed-not-derived")
    if e_html == a_html:
        bad.append("input-ignored")

    report("AC-FDC17", bool(bad), ",".join(bad))

    # ---- AC-FDC18: three states, wiring, purity. ------------------------
    bad2 = []
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    if raw[:3] == b"\xef\xbb\xbf":
        bad2.append("module-bom")
    if b"\r\n" in raw:
        bad2.append("module-crlf")
    try:
        text = raw.decode("utf-8")
        text.encode("ascii")
    except (UnicodeDecodeError, UnicodeEncodeError):
        bad2.append("module-not-ascii")
        text = raw.decode("utf-8", "replace")
    if text.count("__SD30_CLAIMS__") != 2:  # one template slot + one mapping
        bad2.append("placeholder-count-%d" % text.count("__SD30_CLAIMS__"))
    if text.count("sd30_claims = claims_card(") != 1:
        bad2.append("render-not-wired-once")
    if 'sd30_claims = ""' not in text:
        bad2.append("absent-branch-not-wired")
    try:
        slice_text = function_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad2.append("card-not-ascii")
        slice_text = ""
    for forbidden in ("check_claims", "json.", "open(", "os."):
        if forbidden in slice_text:
            bad2.append("card-touches-" + forbidden.replace("(", "par")
                        .replace(".", "dot"))

    # a: an absent block is named, never printed as a measured zero.
    for empty in (None, {}):
        n_html = frontdoor.claims_card(empty)
        if "absent" not in n_html:
            bad2.append("absent-unnamed")
        if numbers_in(n_html):
            bad2.append("absent-fabricates-numbers")
    # b: shape defects print no numbers at all.
    defects = (
        dict(HEALTHY, claimed=None),
        dict(HEALTHY, captured="107"),
        dict(HEALTHY, contradicted=True),
        dict(HEALTHY, uncaptured=-1),
        dict(HEALTHY, rows=None),
        dict(HEALTHY, present="yes"),
    )
    for index, block in enumerate(defects):
        m_html = frontdoor.claims_card(dict(block))
        if "malformed" not in m_html:
            bad2.append("defect-%d-unnamed" % index)
        if numbers_in(m_html):
            bad2.append("defect-%d-prints-numbers" % index)
    # c: no ledger to census is named with no counts; a legacy block keeps its
    # numbers and names the gap instead of guessing.
    p_html = frontdoor.claims_card(dict(HEALTHY, present=False))
    if "no ledger" not in p_html:
        bad2.append("absent-ledger-unnamed")
    if numbers_in(p_html):
        bad2.append("absent-ledger-prints-numbers")
    t_html = frontdoor.claims_card(dict(HEALTHY, present=None))
    if "presence unknown" not in t_html:
        bad2.append("legacy-presence-unguessed")
    if "claimed=309" not in t_html:
        bad2.append("legacy-hides-numbers")
    if p_html == t_html:
        bad2.append("presence-ignored")

    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad2.append("registry-rows-%d" % rows)

    # ---- the live page really carries what the file published. -----------
    page = frontdoor.render().decode("utf-8")
    block = live_block()
    if isinstance(block, dict) and block.get("present") is False:
        if "no ledger" not in page:
            bad2.append("live-absent-unnamed")
    elif isinstance(block, dict) and block:
        for key in ("claimed", "captured", "contradicted", "uncaptured",
                    "historic"):
            needle = "%s=%s" % (key, block.get(key))
            if needle not in page:
                bad2.append("live-missing-" + needle.split("=")[0])
        if "records=%s" % block.get("rows") not in page:
            bad2.append("live-missing-records")
    else:
        if "CLAIMS block absent" not in page:
            bad2.append("live-absent-not-named")

    report("AC-FDC18", bool(bad2), ",".join(bad2))

    # ---- AC-FDC19: the card feeds no census and the faces stay separate. --
    bad3 = []
    h_html = frontdoor.claims_card(dict(HEALTHY))
    if re.search(r"rows=\d+", h_html):
        bad3.append("card-prints-census-token")
    if "records=" not in h_html:
        bad3.append("card-hides-the-rows-reading")
    chain_html = frontdoor.chain_card(
        {"present": True, "rows": 6, "broken": 0,
         "path": "state/qa_replacements.jsonl"})
    if "CLAIM" in chain_html.upper():
        bad3.append("chain-card-carries-claims")
    if "CHAIN" in h_html:
        bad3.append("claims-card-carries-chain")
    # The one census token count that must not move is the card's own: the
    # rendered page is the shipped cards' tokens only.
    page3 = frontdoor.render().decode("utf-8")
    outside = page3.replace(frontdoor.claims_card(live_block() or {}), "")
    if len(re.findall(r"rows=\d+", page3)) != \
            len(re.findall(r"rows=\d+", outside)):
        bad3.append("card-moves-page-token-count")
    if len(RESULTS) != 2:
        bad3.append("results-before-this-arm-%d" % len(RESULTS))

    report("AC-FDC19", bool(bad3), ",".join(bad3))

    # ---- AC-FDC20: data may quote a placeholder without being eaten. ------
    # Found by this round's own landing: the state product line named the
    # claims slot token, the old sequential replace loop filled it INSIDE the
    # escaped export prose, and the page carried three claims cards. The fill
    # is one pass now, so replacement text is never rescanned.
    bad4 = []
    filled = frontdoor._fill_template("__A__ __B__",
                                      {"__A__": "__B__", "__B__": "X"})
    if filled != "__B__ X":
        bad4.append("inserted-placeholder-rescanned-%s" % filled)
    if frontdoor._fill_template("__NOPE__", {}) != "__NOPE__":
        bad4.append("unknown-placeholder-eaten")
    if frontdoor._fill_template("plain", {"__A__": "x"}) != "plain":
        bad4.append("plain-text-changed")
    page4 = frontdoor.render().decode("utf-8")
    if page4.count("CLAIMS claimed=") != 1:
        bad4.append("claims-cards-on-page-%d" % page4.count("CLAIMS claimed="))
    if page4.count("CHAIN rows=") != 1:
        bad4.append("chain-cards-on-page-%d" % page4.count("CHAIN rows="))
    with io.open(REGISTRY, encoding="utf-8") as handle:
        found4 = re.search(r'test_frontdoor_claims_card\.py"\)\s*,\s*(\d+)',
                           handle.read())
    declared4 = int(found4.group(1)) if found4 else -1
    if declared4 != 5:
        bad4.append("registry-count-%d" % declared4)

    report("AC-FDC20", bool(bad4), ",".join(bad4))

    # ---- AC-FDC21: the reading states its own age. -------------------------
    # R3231 measured (qa/probe-R3231.log, ARM-C) that this card printed no
    # moment at all: the only age a reader saw came from another card's
    # export_ts, by convention. The stamp now rides inside the block and is
    # graded equal to export_ts by AC-SXF33, so a reader can age the numbers
    # without cross-reading a neighbour. Absence is named, never faked as 0.
    bad5 = []
    stamped = frontdoor.claims_card(dict(HEALTHY,
                                         census_ts="2026-11-22T06:00:00+08:00"))
    if "CLAIMS census taken at 2026-11-22T06:00:00+08:00" not in stamped:
        bad5.append("stamp-not-printed")
    plain5 = frontdoor.claims_card(dict(HEALTHY))
    if "CLAIMS census age unknown" not in plain5:
        bad5.append("absent-stamp-not-named")
    if re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", plain5):
        bad5.append("absent-stamp-invented-a-moment")
    odd5 = frontdoor.claims_card(dict(HEALTHY, census_ts=12345))
    if "CLAIMS census age unknown" not in odd5:
        bad5.append("non-string-stamp-not-named")
    for html5, label5 in ((stamped, "stamped"), (plain5, "plain"), (odd5, "odd")):
        if "class=fail>CLAIMS census" in html5:
            bad5.append("%s-age-is-a-verdict" % label5)
        if html5.count("<p class=kv>CLAIMS census ") != 1:
            bad5.append("%s-age-lines-%d"
                        % (label5, html5.count("<p class=kv>CLAIMS census ")))
    page5 = frontdoor.render().decode("utf-8")
    if page5.count("CLAIMS census ") != 1:
        bad5.append("page-age-lines-%d" % page5.count("CLAIMS census "))
    with io.open(REGISTRY, encoding="utf-8") as handle:
        found5 = re.search(r'test_frontdoor_claims_card\.py"\)\s*,\s*(\d+)',
                           handle.read())
    declared5 = int(found5.group(1)) if found5 else -1
    if declared5 != 5:
        bad5.append("registry-count-%d" % declared5)

    report("AC-FDC21", bool(bad5), ",".join(bad5))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
