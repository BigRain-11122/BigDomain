"""Suite for the chain card: the published replacement-chain reading gets a
live consumer on the only face that keeps being rendered after the loop stops.

TWO criteria, AC-FDC13 and AC-FDC14, pre-registered in the R3223 backlog PIN
row BEFORE this file and the code it grades.

R3223 measured the hole: R3222 published `chain {rows, broken, path}` into
docs/status-export.json, and src/sandbox/frontdoor.py named it nowhere - zero
placeholder, zero call site - so a broken replacement chain and a chain that
never existed looked alike on the CEO card. This suite proves the card is now a
pure consumption face: it prints what the data file says, it never re-reads the
ledger or re-derives `broken`, and an absent block prints a named absence
instead of a fabricated `rows=0`.

Usage: python test_frontdoor_chain_card.py
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
ROW = "frontdoor-chain-card"

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
    return data.get("chain")


def function_slice(text):
    start = text.index("def chain_card(")
    end = text.index("\ndef face_age_card(", start)
    return text[start:end]


def main():
    bad = []

    # ---- AC-FDC13 a: a healthy block prints all three values, no alert. ---
    a_block = {"rows": 3, "broken": 0, "path": "state/qa_replacements.jsonl"}
    a_html = frontdoor.chain_card(a_block)
    for needle in ("rows=3", "broken=0", "path=state/qa_replacements.jsonl"):
        if needle not in a_html:
            bad.append("healthy-missing-" + needle)
    if "class=fail" in a_html:
        bad.append("healthy-carries-alert")

    # ---- b: the SAME function renders broken=1 as a failed row. -----------
    b_block = {"rows": 2, "broken": 1, "path": "state/qa_replacements.jsonl"}
    b_html = frontdoor.chain_card(b_block)
    for needle in ("class=fail", "broken=1", "rows=2"):
        if needle not in b_html:
            bad.append("broken-missing-" + needle)

    # ---- c: an absent block is named, never printed as rows=0. -----------
    for empty in (None, {}):
        c_html = frontdoor.chain_card(empty)
        if "absent" not in c_html:
            bad.append("absent-unnamed")
        if "rows=0" in c_html:
            bad.append("absent-fabricates-zero")

    # ---- d: shape defects print no numbers at all. -----------------------
    defects = (
        {"broken": 0, "path": "p"},                       # rows missing
        {"rows": "3", "broken": 0, "path": "p"},           # rows not int
        {"rows": 3, "broken": True, "path": "p"},          # bool counts
        {"rows": 3, "broken": 0},                          # path missing
        {"rows": 3, "broken": 0, "path": "  "},            # path blank
    )
    for index, block in enumerate(defects):
        d_html = frontdoor.chain_card(block)
        if "malformed" not in d_html:
            bad.append("defect-%d-unnamed" % index)
        if "rows=" in d_html or "broken=" in d_html:
            bad.append("defect-%d-prints-numbers" % index)

    # ---- e: derived, not typed; same input twice is byte-identical. ------
    if frontdoor.chain_card(a_block) != a_html:
        bad.append("not-deterministic")
    e_block = dict(a_block)
    e_block["broken"] = 4
    e_html = frontdoor.chain_card(e_block)
    if "broken=4" not in e_html:
        bad.append("typed-not-derived")
    if e_html == a_html:
        bad.append("input-ignored")

    report("AC-FDC13", bool(bad), ",".join(bad))

    # ---- AC-FDC14: wiring, purity and registration. ----------------------
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
    if "__SD30_CHAIN__" not in text:
        bad2.append("placeholder-missing")
    if text.count("sd30_chain = chain_card(") != 1:
        bad2.append("render-not-wired-once")
    # Measured this window: without the absent-branch reset, a corrupt export
    # file leaves sd30_chain undefined and the placeholder map raises NameError
    # instead of rendering the honest-failure line.
    if 'sd30_chain = ""' not in text:
        bad2.append("absent-branch-not-wired")
    try:
        slice_text = function_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad2.append("card-not-ascii")
        slice_text = ""
    for forbidden in ("check_ledger", "json.", "open("):
        if forbidden in slice_text:
            bad2.append("card-touches-" + forbidden.replace(".", "dot"))
    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad2.append("registry-rows-%d" % rows)

    # ---- the live page really carries what the file published. -----------
    page = frontdoor.render().decode("utf-8")
    block = live_block()
    if isinstance(block, dict) and block:
        for needle in ("rows=%s" % block.get("rows"),
                       "broken=%s" % block.get("broken"),
                       "path=%s" % block.get("path")):
            if needle not in page:
                bad2.append("live-missing-" + needle)
        if str(block.get("broken")) not in ("0", "None") \
                and "class=fail" not in page:
            bad2.append("live-broken-not-alerted")
    else:
        if "CHAIN block absent" not in page:
            bad2.append("live-absent-not-named")

    report("AC-FDC14", bool(bad2), ",".join(bad2))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
