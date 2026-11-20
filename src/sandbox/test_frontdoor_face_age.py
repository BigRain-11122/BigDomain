"""Suite for the export-face age card: the age gate gets its live consumer.

ONE criterion AC-FDC2 with six arms, pre-registered in the R3115 backlog row
BEFORE this file and the code it grades.

R3115 measured the hole: src/os/export_freshness.py (the 24h age gate, AC-EXP1..6
shipped at R2250) had ZERO production consumers - its twelve non-oneoff hits were
test suites, sibling gate modules' prose, and the suite runner, while closeout.py,
export_round.py and scan_five_still.py named it not at all. Meanwhile the CEO
card printed export_ts as a bare string in a KPI box: a dead loop and a live loop
look the same on the only face that keeps being rendered after the loop stops.
The same sample also held two stamps written in the FUTURE, which an
upper-bound-only gate reads as FRESH forever.

This suite proves the card consumes the shipped reading (no second parser, no
new verdict word) and names the lower bound instead of printing it green.

Usage: python test_frontdoor_face_age.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import datetime
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MODULE = os.path.join(HERE, "frontdoor.py")
OS_DIR = os.path.join(REPO, "src", "os")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
ROW = "frontdoor-face-age"

sys.path.insert(0, HERE)
sys.path.insert(0, OS_DIR)
import frontdoor  # noqa: E402  (the page module, import-time journey)
import export_freshness as EF  # noqa: E402

RESULTS = []
NOW = datetime.datetime(2026, 11, 21, 12, 0, 0,
                        tzinfo=datetime.timezone.utc)


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def world(hours_from_now, drop_ts=False, raw_ts=None):
    """One private export world; returns the path to its face document."""
    folder = tempfile.mkdtemp(prefix="bigdomain-fdc2-")
    body = {
        "export_ts": "not-a-time",
        "ceo_face": {
            "current": "window in flight",
            "latest_artifact": "qa/some-evidence.log",
            "next_milestone": "next window within the gate",
            "next_milestone_due": "also-not-a-time",
        },
    }
    if not drop_ts:
        stamp = (NOW + datetime.timedelta(hours=hours_from_now)).isoformat()
        body["export_ts"] = raw_ts if raw_ts is not None else stamp
        # A due stamp 24h out keeps the milestone window inside its gate, so
        # every arm here grades the AGE axis alone (AC-EXP3 keeps the window).
        body["ceo_face"]["next_milestone_due"] = (
            NOW + datetime.timedelta(hours=24)).isoformat()
    else:
        del body["export_ts"]
    path = os.path.join(folder, "status-export.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(body, ensure_ascii=False, indent=2))
    return path


def card_for(hours_from_now, **kwargs):
    """The card rendered over the SHIPPED gate's reading of a private world."""
    path = world(hours_from_now, **kwargs)
    try:
        reading = EF.assess(path, NOW)
    except EF.ExportFreshnessError as exc:
        reading = {"error": "%s: %s" % (exc.code, exc.detail)}
    return frontdoor.face_age_card(reading), reading


def card_slice(text):
    start = text.index("def face_age_card(")
    end = text.index("\ndef render(", start)
    return text[start:end]


def main():
    bad = []

    # ---- a: a fresh face renders age, gate and the shipped verdict. -------
    a_html, a_reading = card_for(-1.0)
    if "age=1.00h" not in a_html:
        bad.append("fresh-age-missing")
    if "gate=24h" not in a_html:
        bad.append("fresh-gate-missing")
    if "verdict=FRESH" not in a_html:
        bad.append("fresh-verdict-missing")
    if "class=fail" in a_html:
        bad.append("fresh-carries-alert")
    if a_reading.get("verdict") != "FRESH":
        bad.append("gate-disagrees-on-fresh")

    # ---- b: the upper bound still fires, and it fires as a failed row. ----
    b_html, b_reading = card_for(-30.0)
    if b_reading.get("verdict") != "STALE-FACE":
        bad.append("gate-missed-stale")
    for needle in ("verdict=STALE-FACE", "class=fail", "E_EXP_STALE_FACE"):
        if needle not in b_html:
            bad.append("stale-missing-" + needle)

    # ---- c: the lower bound the gate cannot see is named here. ------------
    c_html, c_reading = card_for(8.0)
    if c_reading.get("verdict") != "FRESH":
        bad.append("gate-unexpected-on-future")
    if "age=-8.00h" not in c_html:
        bad.append("future-age-not-negative")
    if "future_stamp" not in c_html or "class=fail" not in c_html:
        bad.append("future-stamp-not-named")

    # ---- d: derived, not typed - same input twice, a 2h move moves age. ---
    if frontdoor.face_age_card(a_reading) != a_html:
        bad.append("not-deterministic")
    d_html, d_reading = card_for(-3.0)
    if "age=3.00h" not in d_html or d_html == a_html:
        bad.append("age-not-derived")

    # ---- e: a face without a usable stamp is refused, never green. --------
    e_html, e_reading = card_for(0.0, drop_ts=True)
    if "error" not in e_reading:
        bad.append("missing-stamp-not-refused")
    if "unreadable" not in e_html:
        bad.append("refusal-not-named")
    if "verdict=FRESH" in e_html:
        bad.append("refusal-claims-fresh")
    f_html, _ = card_for(0.0, raw_ts="2026-11-21T04:00:00")
    if "unreadable" not in f_html:
        bad.append("naive-stamp-not-refused")
    empty_html = frontdoor.face_age_card(None)
    if "absent" not in empty_html or "verdict=FRESH" in empty_html:
        bad.append("absent-not-named")

    # ---- f: the live page carries the live reading; source stays honest. --
    live = EF.assess(EXPORT, datetime.datetime.now(datetime.timezone.utc))
    page = frontdoor.render().decode("utf-8")
    if "FACE age=" not in page:
        bad.append("live-face-line-absent")
    if ("verdict=%s" % live["verdict"]) not in page:
        bad.append("live-verdict-not-rendered")
    match = re.search(r"age=(-?\d+\.\d+)h", page)
    if not match:
        bad.append("live-age-not-parsed")
    else:
        printed = float(match.group(1))
        if abs(printed - live["age_hours"]) > 0.1:
            bad.append("live-age-%s-vs-%s" % (printed, live["age_hours"]))

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
    if "__SD30_AGE__" not in text:
        bad.append("placeholder-missing")
    if "sd30_age = face_age_card(" not in text:
        bad.append("render-not-wired")
    if "sd30_age = \"\"" not in text:
        bad.append("absent-branch-not-wired")
    try:
        slice_text = card_slice(text)
        slice_text.encode("ascii")
    except (ValueError, UnicodeEncodeError):
        bad.append("card-not-ascii")
        slice_text = ""
    for needle in ("assess(", "fromisoformat", "timedelta"):
        if needle in slice_text:
            bad.append("card-re-derives-" + needle)
    with io.open(REGISTRY, encoding="utf-8") as handle:
        rows = handle.read().count('"' + ROW + '"')
    if rows != 1:
        bad.append("registry-rows-%d" % rows)

    report("AC-FDC2", bool(bad), ",".join(bad))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
