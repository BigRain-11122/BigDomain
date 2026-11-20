"""Suite for the corpus card: the tree-gate reading gets one live consumer.

ONE criterion AC-FDC3 with four arms, pre-registered in the R3128 backlog row
BEFORE this file and the code it grades.

R3128 measured the hole: the corpus (files / readable / bytes that the flags
face already pays to read, ~4219 files / 508.1MB) was derived in exactly one
place and printed on ONE closeout stdout line. Of 2307 shipped versions of the
CEO face exactly one ever carried a corpus key, and the live one carries none -
so the reading's only durable trace was prose in the state log.

The adjudication from the same window stands and is graded here: an unread
count is a READING, not a gate. The card prints it and borrows no verdict word
from either judge.

Usage: python test_frontdoor_corpus_card.py
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
ROW = "frontdoor-corpus-card"

sys.path.insert(0, HERE)
import frontdoor  # noqa: E402  (the page module, import-time journey)

RESULTS = []


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def card_slice(text):
    start = text.index("def corpus_card(")
    end = text.index("\ndef _export_freshness(", start)
    return text[start:end]


def main():
    bad = []

    # ---- a: a published block renders files / readable / mb. --------------
    clean = {"corpus": {"files": 4219, "readable": 4219, "bytes": 508066256,
                        "mb": 508.1}}
    a_html = frontdoor.corpus_card(clean)
    for needle in ("CORPUS files=4219", "readable=4219", "mb=508.1"):
        if needle not in a_html:
            bad.append("clean-missing-" + needle.replace(" ", "_"))
    if "unread=" in a_html:
        bad.append("clean-invents-unread")

    # ---- b: an unread count prints, and it borrows no verdict word. ------
    dirty = {"corpus": {"files": 3, "readable": 2, "bytes": 10, "mb": 0.0,
                        "unread": 1}}
    b_html = frontdoor.corpus_card(dirty)
    if "unread=1" not in b_html:
        bad.append("unread-not-printed")
    for word in ("class=fail", "class=pass", "FRESH", "FLAG", "PASS",
                 "DRIFT", "ALERT"):
        if word in b_html:
            bad.append("unread-borrows-" + word.replace("=", "_"))

    # ---- c: an absent block is named, and it is never a zero. ------------
    for empty in (None, {}, {"corpus": None}, {"corpus": {}}):
        c_html = frontdoor.corpus_card(empty)
        if "absent" not in c_html:
            bad.append("absent-not-named")
        if "files=0" in c_html or "mb=0" in c_html:
            bad.append("absent-fabricates-zero")

    # ---- d: pure consumption - same input twice, no count of its own. ----
    if frontdoor.corpus_card(clean) != a_html:
        bad.append("not-deterministic")
    moved = {"corpus": {"files": 4300, "readable": 4300, "bytes": 600000000,
                        "mb": 600.0}}
    if frontdoor.corpus_card(moved) == a_html:
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
    if "__SD30_CORPUS__" not in text:
        bad.append("placeholder-missing")
    if "sd30_corpus = corpus_card(" not in text:
        bad.append("render-not-wired")
    if 'sd30_corpus = ""' not in text:
        bad.append("absent-branch-not-wired")
    try:
        slice_text = card_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad.append("card-not-ascii")
        slice_text = ""
    # the card must not re-walk the tree or re-count anything
    for needle in ("os.walk", "listdir", "scandir", "open(", "census",
                   "check_against_baseline"):
        if needle in slice_text:
            bad.append("card-re-counts-" + needle.replace("(", ""))
    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)

    # live page: the card is rendered from the live face's own block
    with io.open(EXPORT, "rb") as handle:
        live = json.loads(handle.read().decode("utf-8-sig"))
    want = frontdoor.corpus_card((live.get("ceo_face") or {}))
    page = frontdoor.render().decode("utf-8")
    if want not in page:
        bad.append("live-card-not-on-page")

    report("AC-FDC3", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
