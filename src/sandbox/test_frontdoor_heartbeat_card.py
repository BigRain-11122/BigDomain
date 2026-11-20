"""Suite for the heartbeat card: the published reading gets its live consumer.

ONE criterion AC-FDC1 with six arms, pre-registered in the R3114 backlog row
BEFORE this file and the code it grades.

R3114 measured the hole: 22 shipped readers of the export's `heartbeat` block
key exist, all of them the writer (src/os/export_round.py), its checker or its
test, and the key tuple the CEO card validated against did not name the block
at all - so a FLAG verdict was published into a document nobody rendered. This
suite proves the card is now a pure consumption face: it renders what the data
says, it never re-derives a verdict, and an absent block prints an honest
absence line instead of a green one.

Usage: python test_frontdoor_heartbeat_card.py
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
ROW = "frontdoor-heartbeat-card"

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
    face = data.get("ceo_face")
    return (face or {}).get("heartbeat") if isinstance(face, dict) else None


def function_slice(text):
    start = text.index("def heartbeat_card(")
    end = text.index("\ndef render(", start)
    return text[start:end]


def main():
    bad = []

    # ---- a: a PASS block renders all four values, with no alert row. -------
    a_face = {"tick": 12, "state_tick": 12, "lag": 0,
              "verdict": "PASS", "reason": "fresh"}
    a_html = frontdoor.heartbeat_card(a_face)
    for needle in ("tick=12", "state_tick=12", "lag=0", "verdict=PASS"):
        if needle not in a_html:
            bad.append("pass-missing-" + needle)
    if "class=fail" in a_html:
        bad.append("pass-carries-alert")

    # ---- b: the SAME function renders a FLAG block as a failed row. --------
    b_face = {"tick": 10, "state_tick": 12, "lag": 2,
              "verdict": "FLAG", "reason": "heartbeat_row_debt"}
    b_html = frontdoor.heartbeat_card(b_face)
    for needle in ("class=fail", "reason=heartbeat_row_debt",
                   "verdict=FLAG", "lag=2"):
        if needle not in b_html:
            bad.append("flag-missing-" + needle)

    # ---- c: an absent block is named, never printed green. ----------------
    for empty in (None, {}):
        c_html = frontdoor.heartbeat_card(empty)
        if "absent" not in c_html:
            bad.append("absent-unnamed")
        if "verdict=PASS" in c_html:
            bad.append("absent-claims-pass")

    # ---- d: derived, not typed - same input twice, a new tick changes it ---
    if frontdoor.heartbeat_card(a_face) != a_html:
        bad.append("not-deterministic")
    d_face = dict(a_face)
    d_face["tick"] = 13
    if "tick=13" not in frontdoor.heartbeat_card(d_face):
        bad.append("typed-not-derived")
    if frontdoor.heartbeat_card(d_face) == a_html:
        bad.append("input-ignored")

    # ---- e: the live page really carries the block it published ------------
    page = frontdoor.render().decode("utf-8")
    block = live_block()
    if isinstance(block, dict) and block:
        verdict = str(block.get("verdict"))
        if ("verdict=%s" % verdict) not in page:
            bad.append("live-verdict-not-rendered")
        if ("tick=%s" % block.get("tick")) not in page:
            bad.append("live-tick-not-rendered")
        if verdict != "PASS" and "class=fail" not in page:
            bad.append("live-flag-not-alerted")
    else:
        if "HB block absent" not in page:
            bad.append("live-absent-not-named")

    # ---- f: the module stays pure ASCII and the card is wired + registered -
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
    if "__SD30_HB__" not in text:
        bad.append("placeholder-missing")
    if "sd30_hb = heartbeat_card(" not in text:
        bad.append("render-not-wired")
    try:
        slice_text = function_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad.append("card-not-ascii")
        slice_text = ""
    if slice_text and "heartbeat.verify" in slice_text:
        bad.append("card-re-derives-verdict")
    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)

    report("AC-FDC1", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
