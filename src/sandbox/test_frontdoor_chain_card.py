"""Suite for the chain card: the published replacement-chain reading gets a
live consumer on the only face that keeps being rendered after the loop stops.

FOUR criteria, AC-FDC13..16. AC-FDC13/14 were pre-registered in the R3223
backlog PIN row, AC-FDC15/16 in the R3224 row, each BEFORE the code it grades.

R3223 measured the hole: R3222 published `chain {rows, broken, path}` into
docs/status-export.json, and src/sandbox/frontdoor.py named it nowhere - zero
placeholder, zero call site - so a broken replacement chain and a chain that
never existed looked alike on the CEO card. This suite proves the card is now a
pure consumption face: it prints what the data file says, it never re-reads the
ledger or re-derives `broken`, and an absent block prints a named absence
instead of a fabricated `rows=0`.

R3224 measured the second hole: a world with NO ledger and a world with an
EMPTY ledger published the identical block (probe qa/probe-R3224.log), so the
card printed `rows=0` for something that was never measured. AC-FDC15 grades
the three states the block now distinguishes; AC-FDC16 grades that the new bit
is read from the block and never measured inside the card.

Usage: python test_frontdoor_chain_card.py
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
    if isinstance(block, dict) and block.get("present") is False:
        # R3224: an absent ledger publishes a named absence, so requiring
        # `rows=` here would demand a fabricated number.
        if "does not exist" not in page:
            bad2.append("live-absent-unnamed")
        if "CHAIN rows=" in page:
            bad2.append("live-absent-fabricates-rows")
    elif isinstance(block, dict) and block:
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

    # ---- AC-FDC15 (R3224): three states, not two. ------------------------
    # p: an absent ledger is named and prints no counts at all - "nothing to
    # measure" must not wear the clothes of a measurement.
    bad3 = []
    p_block = {"present": False, "rows": 0, "broken": 0,
               "path": "state/qa_replacements.jsonl"}
    p_html = frontdoor.chain_card(p_block)
    if "does not exist" not in p_html:
        bad3.append("absent-ledger-unnamed")
    if "rows=" in p_html or "broken=" in p_html:
        bad3.append("absent-ledger-prints-numbers")
    # q: present-but-empty IS a measurement, and it says which one.
    q_block = dict(p_block, present=True)
    q_html = frontdoor.chain_card(q_block)
    for needle in ("rows=0", "present", "measured empty"):
        if needle not in q_html:
            bad3.append("empty-missing-" + needle.replace(" ", "-"))
    if "class=fail" in q_html:
        bad3.append("empty-carries-alert")
    # r: the broken alert survives the new state.
    r_block = {"present": True, "rows": 2, "broken": 1,
               "path": "state/qa_replacements.jsonl"}
    r_html = frontdoor.chain_card(r_block)
    if "class=fail" not in r_html or "broken=1" not in r_html:
        bad3.append("broken-alert-lost")
    # s: a present that is not a boolean is a shape defect, and prints nothing.
    for value in ("yes", 1, None):
        s_html = frontdoor.chain_card(dict(q_block, present=value))
        if "malformed" not in s_html:
            bad3.append("present-%r-unnamed" % (value,))
        if "rows=" in s_html or "broken=" in s_html:
            bad3.append("present-%r-prints-numbers" % (value,))
    # t: a legacy block keeps its numbers and names the gap instead of guessing.
    t_block = {"rows": 3, "broken": 0, "path": "state/qa_replacements.jsonl"}
    t_html = frontdoor.chain_card(t_block)
    for needle in ("rows=3", "presence unknown"):
        if needle not in t_html:
            bad3.append("legacy-missing-" + needle.replace(" ", "-"))
    # u: derived, not typed; and the presence really moves the output.
    if frontdoor.chain_card(p_block) != p_html:
        bad3.append("not-deterministic")
    if p_html == q_html:
        bad3.append("presence-ignored")
    report("AC-FDC15", bool(bad3), ",".join(bad3))

    # ---- AC-FDC16 (R3224): the new bit is READ, never measured here. -----
    bad4 = []
    with io.open(MODULE, "rb") as handle:
        text4 = handle.read().decode("utf-8", "replace")
    body4 = function_slice(text4)
    for forbidden in ("os.", "stat(", "isfile", "getmtime"):
        if forbidden in body4:
            bad4.append("card-reads-the-world-" + forbidden.replace("(", "par")
                        .replace(".", "dot"))
    page4 = frontdoor.render().decode("utf-8")
    block4 = live_block()
    if isinstance(block4, dict) and block4.get("present") is False:
        if "does not exist" not in page4:
            bad4.append("live-absent-ledger-unnamed")
        if "CHAIN rows=" in page4:
            bad4.append("live-absent-ledger-prints-numbers")
    elif isinstance(block4, dict) and block4:
        if "rows=%s" % block4.get("rows") not in page4:
            bad4.append("live-missing-rows")
    # Declared criteria count must move with this file, or the census cannot
    # see a criterion added without a registry bump.
    with io.open(REGISTRY, encoding="utf-8") as handle:
        reg_text = handle.read()
    found = re.search(r'test_frontdoor_chain_card\.py"\)\s*,\s*(\d+)', reg_text)
    declared = int(found.group(1)) if found else -1
    if declared != 4:
        bad4.append("registry-count-%d" % declared)
    if len(RESULTS) != 3:
        bad4.append("results-before-this-arm-%d" % len(RESULTS))
    report("AC-FDC16", bool(bad4), ",".join(bad4))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
