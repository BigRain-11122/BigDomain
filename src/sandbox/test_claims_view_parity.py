"""Suite for one claims judgement, two faces - criteria AC-CVP1..3.

Pinned in the R3233 PIN row of src/os/backlog.md BEFORE this code existed.

R3233 measured (qa/probe-R3233.log) that the same `claims` block in
docs/status-export.json was derived twice: once for the static page a reader
opens by path (tools/deliverable_index.py:claims_band) and once for the card
the live hub serves (src/sandbox/frontdoor.py:claims_card). Each carried its
own key tuple and its own validation:

  * ZERO shipped file named both faces, so nothing could compare them;
  * they already disagreed on a real shape - a block whose `present` was a
    string was refused by the card and printed as six numbers by the band;
  * a hand-drifted number in the landed page stayed silent under --check
    (rc=0, VERDICT PASS 16/16) while a drifted census_ts was caught.

AC-CVP1  same block, both faces: same shape verdict, same six readings.
AC-CVP2  ONE derivation: patching the shared judgement moves BOTH faces
         (a negative control - if either face kept its own parsing it would
         not move).
AC-CVP3  wiring and hygiene: ASCII/LF, zero I/O in the shared module, one
         call per face, registry declares three criteria.

Usage: python test_claims_view_parity.py
Exit: 0 = SUITE PASS, 2 = FAIL.
"""

import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SANDBOX = HERE
OSDIR = os.path.join(REPO, "src", "os")
TOOLS = os.path.join(REPO, "tools")
EXPORT = os.path.join(REPO, "docs", "status-export.json")
REGISTRY = os.path.join(HERE, "reconcile_all.py")
SHARED = os.path.join(HERE, "claims_view.py")
DIX = os.path.join(TOOLS, "deliverable_index.py")
CARD_MODULE = os.path.join(HERE, "frontdoor.py")
ROW = "claims-view-parity"

for path in (SANDBOX, OSDIR, TOOLS):
    if path not in sys.path:
        sys.path.insert(0, path)

import frontdoor  # noqa: E402
import claims_view  # noqa: E402

RESULTS = []
NUM_RE = re.compile(r"(?:claimed|captured|contradicted|uncaptured|historic|"
                    r"records)=(\d+)")
ORDER = ("claimed", "captured", "contradicted", "uncaptured", "historic",
         "records")


def report(name, bad, detail=""):
    RESULTS.append((name, not bad))
    print("%s %s%s" % ("FAIL" if bad else "PASS", name,
                       ("  " + detail) if detail else ""))
    return bad


def load_dix():
    spec = importlib.util.spec_from_file_location("dix_under_test", DIX)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def readings(text):
    found = NUM_RE.findall(text)
    if len(found) != 6:
        return None
    return dict(zip(ORDER, found))


def face_state(text):
    if "malformed" in text:
        return "malformed"
    if "absent" in text or "no claims block" in text:
        return "absent"
    if "no ledger" in text or "nothing to census" in text:
        return "empty"
    if readings(text):
        return "reading"
    return "unknown"


def live_block():
    try:
        with io.open(EXPORT, "rb") as handle:
            blob = json.loads(handle.read().decode("utf-8-sig"))
    except (OSError, ValueError):
        return None
    return blob.get("claims")


STAMP = "2026-11-22T07:00:00+08:00"
HEALTHY = {"claimed": 309, "captured": 107, "contradicted": 11,
           "uncaptured": 191, "historic": 7, "rows": 6, "present": True,
           "census_ts": STAMP}
ZERO = {"claimed": 0, "captured": 0, "contradicted": 0, "uncaptured": 0,
        "historic": 0, "rows": 0, "present": True, "census_ts": STAMP}


def shapes():
    return [
        ("healthy", dict(HEALTHY)),
        ("zero", dict(ZERO)),
        ("absent-none", None),
        ("absent-empty", {}),
        ("present-false", dict(HEALTHY, present=False)),
        ("legacy-no-present", dict(HEALTHY, present=None)),
        ("no-stamp", dict(HEALTHY)),
        ("key-missing", dict((k, v) for k, v in HEALTHY.items() if k != "rows")),
        ("key-string", dict(HEALTHY, captured="107")),
        ("key-bool", dict(HEALTHY, contradicted=True)),
        ("key-negative", dict(HEALTHY, uncaptured=-1)),
        ("present-string", dict(HEALTHY, present="yes")),
        ("broken-conservation", dict(HEALTHY, captured=100)),
    ]


def main():
    dix = load_dix()

    # ---- AC-CVP1: same block, both faces -> same state, same numbers. ----
    bad = []
    for name, block in shapes():
        card = frontdoor.claims_card(block)
        band = dix.claims_band(block)
        c_state, b_state = face_state(card), face_state(band)
        if c_state != b_state:
            bad.append("%s-state-card=%s-band=%s" % (name, c_state, b_state))
            continue
        c_nums, b_nums = readings(card), readings(band)
        if c_nums != b_nums:
            bad.append("%s-numbers-card=%s-band=%s" % (name, c_nums, b_nums))
        if c_state == "reading" and c_nums is None:
            bad.append("%s-reading-without-numbers" % name)
    live = live_block()
    if isinstance(live, dict) and live:
        c_live = readings(frontdoor.claims_card(live))
        b_live = readings(dix.claims_band(live))
        if c_live != b_live:
            bad.append("live-numbers-card=%s-band=%s" % (c_live, b_live))
        if c_live is None:
            bad.append("live-carries-no-readings")
    report("AC-CVP1", bool(bad), ",".join(bad))

    # ---- AC-CVP2: one derivation - patching it moves both faces. --------
    bad2 = []
    original = claims_view.claims_view
    try:
        # a) a shape BOTH refuse now becomes a reading on both surfaces,
        #    because the judgement they read was replaced.
        forged = {"state": claims_view.READING, "bad": [],
                  "counts": dict(HEALTHY, captured=999), "present": True,
                  "stamp": STAMP}
        claims_view.claims_view = lambda block: forged
        c_f = frontdoor.claims_card({"present": "yes"})
        b_f = dix.claims_band({"present": "yes"})
        if readings(c_f) != readings(b_f):
            bad2.append("forged-reading-split")
        if "captured=999" not in c_f or "captured=999" not in b_f:
            bad2.append("forged-reading-did-not-move-both")

        # b) an absent judgement silences both, with no numbers invented.
        claims_view.claims_view = lambda block: {
            "state": claims_view.ABSENT, "bad": [], "counts": {},
            "present": None, "stamp": None}
        c_a = frontdoor.claims_card(dict(HEALTHY))
        b_a = dix.claims_band(dict(HEALTHY))
        if face_state(c_a) != "absent" or face_state(b_a) != "absent":
            bad2.append("absent-judgement-not-followed")
        if readings(c_a) or readings(b_a):
            bad2.append("absent-judgement-invented-numbers")

        # c) a malformed verdict names the same offending field on both.
        claims_view.claims_view = lambda block: {
            "state": claims_view.MALFORMED, "bad": ["rows"], "counts": {},
            "present": None, "stamp": None}
        c_m = frontdoor.claims_card(dict(HEALTHY))
        b_m = dix.claims_band(dict(HEALTHY))
        if "rows" not in c_m or "rows" not in b_m:
            bad2.append("malformed-field-not-named")
        if face_state(c_m) != "malformed" or face_state(b_m) != "malformed":
            bad2.append("malformed-judgement-not-followed")
    finally:
        claims_view.claims_view = original

    # d) with the real judgement back, the same shape they disagreed on now
    #    agrees - the drift the probe found is closed, not papered over.
    if face_state(frontdoor.claims_card(dict(HEALTHY, present="yes"))) != \
            face_state(dix.claims_band(dict(HEALTHY, present="yes"))):
        bad2.append("present-string-still-split")

    report("AC-CVP2", bool(bad2), ",".join(bad2))

    # ---- AC-CVP3: wiring and hygiene. ------------------------------------
    bad3 = []
    for path, label in ((SHARED, "shared"), (DIX, "tool"), (CARD_MODULE, "card")):
        with io.open(path, "rb") as handle:
            raw = handle.read()
        if raw[:3] == b"\xef\xbb\xbf":
            bad3.append("%s-bom" % label)
        if b"\r\n" in raw:
            bad3.append("%s-crlf" % label)
        try:
            text = raw.decode("utf-8")
            text.encode("ascii")
        except (UnicodeDecodeError, UnicodeEncodeError):
            bad3.append("%s-not-ascii" % label)
            text = raw.decode("utf-8", "replace")
        if label == "shared":
            for forbidden in ("open(", "os.", "json.", "socket", "urllib",
                              "subprocess", "requests"):
                if forbidden in text:
                    bad3.append("shared-touches-" + forbidden.replace(
                        "(", "par").replace(".", "dot"))
            for required in ("def claims_view(", "ABSENT", "EMPTY",
                             "MALFORMED", "READING"):
                if required not in text:
                    bad3.append("shared-missing-%s" % required.split("(")[0])
        elif label == "tool":
            if text.count("claims_view.claims_view(") != 1:
                bad3.append("tool-calls-%d"
                            % text.count("claims_view.claims_view("))
        else:
            if text.count("claims_view_mod.claims_view(") != 1:
                bad3.append("card-calls-%d"
                            % text.count("claims_view_mod.claims_view("))

    with io.open(REGISTRY, encoding="utf-8") as handle:
        registry = handle.read()
    if registry.count('"' + ROW + '"') != 1:
        bad3.append("registry-rows-%d" % registry.count('"' + ROW + '"'))
    found = re.search(r'test_claims_view_parity\.py"\)\s*,\s*(\d+)', registry)
    declared = int(found.group(1)) if found else -1
    if declared != 3:
        bad3.append("registry-count-%d" % declared)
    if len(RESULTS) != 2:
        bad3.append("results-before-this-arm-%d" % len(RESULTS))

    report("AC-CVP3", bool(bad3), ",".join(bad3))

    failed = [name for name, ok in RESULTS if not ok]
    if failed:
        print("SUITE FAIL %d/%d failed=%s" % (len(failed), len(RESULTS),
                                              ",".join(failed)))
        return 2
    print("SUITE PASS %d/%d" % (len(RESULTS), len(RESULTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
