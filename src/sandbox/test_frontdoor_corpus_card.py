"""Suite for the corpus card: the tree-gate reading gets one live consumer.

SIX criteria, each pre-registered on the src/os/backlog.md board BEFORE this
file and the code it grades: AC-FDC3 (four arms, R3128), AC-FDC4 (five arms,
R3132), AC-FDC5 (R3133: an over-count is named, not rendered), AC-FDC6
(R3134: the third number is derived from the two on the line, not trusted),
AC-FDC7 (R3135: the fourth number is derived from bytes, never copied) and
AC-FDC8 (R3136: the first two are printed as the integers the line computes
with, and a `files` that cannot be an integer is named instead of rendered).

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

    # ---- AC-FDC4: a malformed block is a named defect, not a reading. ----
    # R3132 pre-registered this criterion on the board before the card changed:
    # the writer refuses a readable-less block, but the card used to print
    # `readable=none` (or a bare `x`) for any dict carrying `files`, which
    # reads as a measurement. Three shipped subscript stores touch the corpus
    # key, so the reader cannot rely on "one writer" and must judge shape.
    malformed = []
    for label, payload_ in (
            ("bare", {"corpus": {"files": 5, "bytes": 100, "mb": 0.0}}),
            ("unparseable", {"corpus": {"files": 5, "readable": "x",
                                        "bytes": 100, "mb": 0.0}}),
            ("null", {"corpus": {"files": 5, "readable": None,
                                 "bytes": 100, "mb": 0.0}})):
        html = frontdoor.corpus_card(payload_)
        if "malformed" not in html:
            malformed.append(label + "-not-named")
        for token in ("readable=", "files="):
            if token in html:
                malformed.append(label + "-prints-" + token.replace("=", ""))
        if "absent" in html:
            malformed.append(label + "-reads-as-absent")
    # negative control: a four-key block renders exactly as it did before
    if frontdoor.corpus_card(clean) != a_html:
        malformed.append("shaped-block-changed")
    # absent stays absent, and never reads as a shape defect
    for empty in (None, {}, {"corpus": None}, {"corpus": {}}):
        html = frontdoor.corpus_card(empty)
        if "absent" not in html or "malformed" in html:
            malformed.append("absent-branch-changed")
    # end to end: the writer refuses the bare block, so no key reaches the card
    sys.path.insert(0, os.path.join(REPO, "src", "os"))
    import export_round as ER
    refused = ER.corpus_block({"files": 5, "bytes": 100})
    if refused is not None:
        malformed.append("writer-now-publishes-bare")
    end_html = frontdoor.corpus_card({"corpus": refused})
    if "absent" not in end_html or "malformed" in end_html:
        malformed.append("end-to-end-not-absent")
    report("AC-FDC4", bool(malformed), ",".join(malformed))

    # ---- AC-FDC5: an over-count is a named defect, not a reading. ----
    # R3133 pre-registered this on the board before the card changed: the
    # census derives files and readable from ONE enumeration (one scandir, one
    # increment inside the names loop), so readable > files cannot come from
    # the supply path - a card that printed it would show unread=-2, a negative
    # count that reads like a measurement. Legal disagreement (fewer readable
    # than files) still prints its unread reading, which is the control.
    over = []
    html = frontdoor.corpus_card({"corpus": {"files": 5, "readable": 7,
                                             "bytes": 100, "mb": 0.0,
                                             "unread": -2}})
    if "readable exceeds files" not in html:
        over.append("over-count-not-named")
    for token in ("files=", "readable=", "unread="):
        if token in html:
            over.append("prints-" + token.replace("=", ""))
    legal = frontdoor.corpus_card({"corpus": {"files": 5, "readable": 3,
                                              "bytes": 100, "mb": 0.0,
                                              "unread": 2}})
    if "unread=2" not in legal or "readable exceeds files" in legal:
        over.append("legal-unread-changed")
    if ER.corpus_block({"files": 5, "readable": 7, "bytes": 100}) is not None:
        over.append("writer-now-publishes-over-count")
    report("AC-FDC5", bool(over), ",".join(over))

    # ---- AC-FDC6: the third number is derived, not trusted. ----
    # R3134 pre-registered this on the board before the card changed: the card
    # printed any stored `unread` value, so a hand-made block like
    # files=5 readable=5 unread=9 rendered three numbers that contradict each
    # other on one line. Measured: 10 published blocks, none carrying the key
    # (the counts agree on every one), one shipped store deriving it from the
    # same two integers - so a disagreeing key is a shape defect, and an absent
    # key over a real gap is stated from the two numbers the line already
    # prints. The legal arm (3/2 with unread=1) stays byte for byte.
    third = []
    for label, bad_block in (
            ("contradictory", {"files": 5, "readable": 5, "bytes": 10,
                               "mb": 0.0, "unread": 9}),
            ("unparseable", {"files": 5, "readable": 4, "bytes": 10,
                             "mb": 0.0, "unread": "x"})):
        html = frontdoor.corpus_card({"corpus": bad_block})
        if "unread disagrees with files-readable" not in html:
            third.append(label + "-not-named")
        for token in ("files=", "readable=", "unread="):
            if token in html:
                third.append(label + "-prints-" + token.replace("=", ""))
    legal_html = frontdoor.corpus_card({"corpus": {"files": 3, "readable": 2,
                                                   "bytes": 10, "mb": 0.0,
                                                   "unread": 1}})
    if "CORPUS files=3 readable=2 mb=0.0 unread=1" not in legal_html:
        third.append("legal-unread-changed")
    if "malformed" in legal_html:
        third.append("legal-read-as-defect")
    # a gap with no key is stated from the two numbers on the same line
    gap_html = frontdoor.corpus_card({"corpus": {"files": 5, "readable": 3,
                                                 "bytes": 10, "mb": 0.0}})
    if "unread=2" not in gap_html or "malformed" in gap_html:
        third.append("absent-key-gap-not-stated")
    # an unverifiable `files` means the difference cannot be cross-checked, so
    # the third number is not printed at all
    blind_html = frontdoor.corpus_card({"corpus": {"files": "x", "readable": 4,
                                                   "bytes": 10, "mb": 0.0,
                                                   "unread": 1}})
    if "unread=" in blind_html:
        third.append("unverifiable-files-printed-unread")
    report("AC-FDC6", bool(third), ",".join(third))

    # ---- AC-FDC7: the fourth number is derived, not trusted. -------------
    # R3135 pre-registered this on the board before the card changed: the card
    # printed whatever `mb` the face carried, so a hand-made block like
    # bytes=508066256 mb=0.0 rendered two numbers contradicting each other on
    # one line, and a block with no bytes still printed the face's mb. Measured:
    # 10 published blocks, every one stating mb equal to round(bytes/1e6,1), and
    # the only shipped corpus writer derives it from an integer total without
    # ever reading an input mb. Derived, the pair agrees by construction; a
    # disagreeing or unparseable key is a shape defect with no numbers, and a
    # block that states no bytes cannot be cross-checked at all.
    fourth = []
    for label, bad_block in (
            ("forged", {"files": 5, "readable": 5, "bytes": 508066256,
                        "mb": 0.0}),
            ("unparseable", {"files": 5, "readable": 5, "bytes": 508066256,
                             "mb": "lots"})):
        html = frontdoor.corpus_card({"corpus": bad_block})
        if "mb disagrees with bytes" not in html:
            fourth.append(label + "-not-named")
        for token in ("files=", "readable=", "mb="):
            if token in html:
                fourth.append(label + "-prints-" + token.replace("=", ""))
    legal_html = frontdoor.corpus_card({"corpus": {"files": 3, "readable": 2,
                                                   "bytes": 10, "mb": 0.0,
                                                   "unread": 1}})
    if "CORPUS files=3 readable=2 mb=0.0 unread=1" not in legal_html:
        fourth.append("legal-line-changed")
    if "malformed" in legal_html:
        fourth.append("legal-read-as-defect")
    # a block that states no bytes cannot be cross-checked, so it prints no
    # numbers instead of the face's mb
    nobytes_html = frontdoor.corpus_card({"corpus": {"files": 5,
                                                     "readable": 5,
                                                     "mb": 12.5}})
    if "bytes missing" not in nobytes_html:
        fourth.append("no-bytes-not-named")
    for token in ("files=", "readable=", "mb="):
        if token in nobytes_html:
            fourth.append("no-bytes-prints-" + token.replace("=", ""))
    # a block that states bytes but no mb is stated from the bytes it prints
    derived_html = frontdoor.corpus_card({"corpus": {"files": 5, "readable": 5,
                                                     "bytes": 508066256}})
    if "mb=508.1" not in derived_html:
        fourth.append("absent-key-not-derived")
    if "malformed" in derived_html:
        fourth.append("absent-key-read-as-defect")
    report("AC-FDC7", bool(fourth), ",".join(fourth))

    # ---- AC-FDC8: the first two numbers are the ones the line computes with. --
    # R3136 pre-registered this on the board before the card changed: `files`
    # is the denominator of every number on the line and `readable` is the
    # subtrahend of the third, yet both were printed verbatim from the face -
    # `files=x` read as a measurement with the third number silently dropped,
    # `readable=4.9` printed 4.9 while the gap used 4, and `files='007'` printed
    # 007 while the comparison used 7. Measured: across 12 published blocks the
    # three count keys are int 12/12 and mb is the only float, the card has
    # exactly ONE `files=` print path, and the writer already int()s the value.
    first = []
    for label, blind_block in (
            ("unparseable", {"files": "x", "readable": 4, "bytes": 10,
                             "mb": 0.0}),
            ("null", {"files": None, "readable": 4, "bytes": 10, "mb": 0.0})):
        html = frontdoor.corpus_card({"corpus": blind_block})
        if "files missing" not in html:
            first.append(label + "-not-named")
        for token in ("files=", "readable=", "mb=", "unread="):
            if token in html:
                first.append(label + "-prints-" + token.replace("=", ""))
        if "absent" in html:
            first.append(label + "-reads-as-absent")
    # negative control: the shaped block renders exactly as it did before
    if frontdoor.corpus_card(clean) != a_html:
        first.append("shaped-block-changed")
    # a float readable is printed as the integer the gap was derived from
    float_html = frontdoor.corpus_card({"corpus": {"files": 5,
                                                   "readable": 4.9,
                                                   "bytes": 10, "mb": 0.0}})
    if "CORPUS files=5 readable=4 mb=0.0 unread=1" not in float_html:
        first.append("float-readable-not-derived")
    if "malformed" in float_html or "4.9" in float_html:
        first.append("float-readable-leaked")
    # a numeric-string files is printed in its integer form, not its raw form
    text_html = frontdoor.corpus_card({"corpus": {"files": "007",
                                                  "readable": 7,
                                                  "bytes": 10, "mb": 0.0}})
    if "CORPUS files=7 readable=7 mb=0.0" not in text_html:
        first.append("string-files-not-derived")
    if "007" in text_html or "malformed" in text_html:
        first.append("string-files-leaked")
    report("AC-FDC8", bool(first), ",".join(first))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
