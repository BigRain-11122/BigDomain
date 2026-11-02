"""review_window_guard_parity_blind_agreement suite (R2387).

Criteria AC-RWGB1..AC-RWGB6 were pinned inside the R2381 seed row of
state/queue/tech.md BEFORE the module existed.

What this proves: the parity reads PARITY-AGREES when BOTH faces agree there is
no rewind - including when neither face could read the declaration at all, which
is the reading that would hide the law it guards. This suite pins the added
distinction (PARITY-UNKNOWN naming both codes) AND pins that every informed
reading keeps the parity's own eight fields byte for byte.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import review_window_wire as RWW  # noqa: E402
import review_window_wire_argument_guard as RWAG  # noqa: E402
import review_window_guard_parity as RWGP  # noqa: E402
import review_window_guard_parity_blind_agreement as RWGB  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "review_window_guard_parity_blind_agreement.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-guard-parity-blind-agreement"
WIRED_EXPECT = '"test_review_window_guard_parity_blind_agreement.py"), 6),'
REWIND = "E_RWHW_DECL_HISTORY"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def row(window, declared_by):
    return {"window": window, "declared_by": declared_by,
            "reason": "pinned window"}


def body(window, rows):
    return {
        "window": window,
        "declared_by": rows[-1]["declared_by"],
        "reason": "pinned so it can only move through a new row",
        "declarations": rows,
    }


def make_world(payload=None, raw=None, no_window=False):
    world = tempfile.mkdtemp(prefix="bigdomain-rwgb-")
    if not no_window:
        inner = os.path.join(world, "state")
        os.makedirs(inner)
        text = raw if raw is not None else json.dumps(payload, indent=2)
        with io.open(os.path.join(inner, "review_window.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(root):
    digest = hashlib.sha256()
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            with io.open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def run_main(argv):
    """Call main() in-process so a patched face can move the CLI answer."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = RWGB.main(argv)
    return code, buf.getvalue()


def base_fields(found):
    """The parity's own eight fields, in its own order."""
    return dict((key, found.get(key)) for key in RWGP.PARITY_KEYS)


def main():
    worlds = []
    saved_report = RWW.window_report
    saved_reading = RWAG.reading
    saved_parity = RWGP.check
    try:
        clean = make_world(body(20, [row(20, "R2300")]))
        moved = make_world(body(20, [row(10, "R2300"), row(20, "R2310")]))
        rewind = make_world(body(20, [row(20, "R2400"), row(10, "R2300")]))
        unpinned = make_world(no_window=True)
        bad = make_world(raw="{not json")
        unkempt = make_world(raw="{not json either")
        worlds.extend([clean, moved, rewind, unpinned, bad, unkempt])

        def rewind_report(root, round_text):
            raise RWW.ReviewWindowWireError(REWIND, "E_RWH_REWIND R2400 R2300")

        def clean_reading(root):
            return {"verdict": "ARGUMENT-CLEAN", "history": "MOVED",
                    "code": None}

        def refused_reading(root):
            return {"verdict": "ARGUMENT-REFUSED", "code": REWIND,
                    "history": "E_RWH_REWIND"}

        # ---- AC-RWGB1: agreement on ignorance reads PARITY-UNKNOWN --------
        blind = RWGB.check(bad)
        parity_blind = RWGP.check(bad)
        one_side = RWGB.check(unkempt)
        code_unknown, out_unknown = run_main(["--check", "--root", bad])
        check(parity_blind["verdict"] == "PARITY-AGREES"
              and blind["verdict"] == RWGB.VERDICT_UNKNOWN
              and blind["verdict"] != RWGB.VERDICT_AGREES
              and blind["agrees"] is False
              and blind["ignorance"] == RWGB.IGNORANCE_BOTH
              and blind["declared_code"] == "E_RWW_UNREADABLE"
              and blind["argument"] == RWGB.unknown_word()
              and blind["argument_code"] == "E_RWW_UNREADABLE"
              and one_side["verdict"] == RWGB.VERDICT_UNKNOWN
              and code_unknown == 1
              and "verdict=PARITY-UNKNOWN" in out_unknown,
              "AC-RWGB1 a declaration neither face can read reads "
              "PARITY-UNKNOWN naming BOTH codes (the carried "
              "E_RWW_UNREADABLE on each side, the argument side with its own "
              "UNKNOWN word), never AGREES - while the shipped parity still "
              "reads PARITY-AGREES on the same world, so the gap this face "
              "closes is named rather than asserted, and the CLI exits 1")

        # ---- AC-RWGB2: a rewinding list keeps the R2381 reading ------------
        found_rewind = RWGB.check(rewind)
        base_rewind = RWGP.check(rewind)
        code_rewind, _ = run_main(["--check", "--root", rewind])
        check(found_rewind["verdict"] == "PARITY-AGREES"
              and found_rewind["rewind"] is True
              and found_rewind["declared_code"] == REWIND
              and found_rewind["argument_code"] == REWIND
              and found_rewind["agrees"] is True
              and found_rewind["ignorance"] == RWGB.IGNORANCE_NONE
              and base_fields(found_rewind) == base_fields(base_rewind)
              and code_rewind == 0,
              "AC-RWGB2 a rewinding list still reads PARITY-AGREES with BOTH "
              "faces naming the carried %s, all eight parity fields byte for "
              "byte, and the CLI exits 0" % REWIND)

        # ---- AC-RWGB3: informed agreements keep the parity's words ---------
        found_clean = RWGB.check(clean)
        found_moved = RWGB.check(moved)
        found_unpinned = RWGB.check(unpinned)
        check(found_clean["verdict"] == "PARITY-AGREES"
              and found_clean["declared_window"] == 20
              and found_clean["ignorance"] == RWGB.IGNORANCE_NONE
              and base_fields(found_clean) == base_fields(RWGP.check(clean))
              and found_moved["verdict"] == "PARITY-AGREES"
              and found_moved["declared_window"] == 20
              and found_moved["argument_history"] == "MOVED"
              and found_moved["ignorance"] == RWGB.IGNORANCE_NONE
              and base_fields(found_moved) == base_fields(RWGP.check(moved))
              and found_unpinned["verdict"] == "PARITY-AGREES"
              and found_unpinned["declared_code"] == "E_RWW_UNPINNED"
              and found_unpinned["ignorance"] == RWGB.IGNORANCE_NONE
              and base_fields(found_unpinned)
              == base_fields(RWGP.check(unpinned)),
              "AC-RWGB3 a clean monotonic list keeps PARITY-AGREES with the "
              "declared window carried, and an UNPINNED list (a state the "
              "argument path deliberately ignores) is NOT called an "
              "ignorance - every informed reading keeps the parity's eight "
              "fields byte for byte")

        # ---- AC-RWGB4: a real split is named and outranks an ignorance ----
        before = digest_tree(clean)
        RWW.window_report = rewind_report
        RWAG.reading = clean_reading
        try:
            split = RWGB.check(clean)
        finally:
            RWW.window_report = saved_report
            RWAG.reading = saved_reading

        def broken_report(root, round_text):
            raise RuntimeError("declaration reader exploded")

        RWW.window_report = broken_report
        RWAG.reading = refused_reading
        try:
            split_over_ignorance = RWGB.check(clean)
        finally:
            RWW.window_report = saved_report
            RWAG.reading = saved_reading
        after = digest_tree(clean)
        check(split["verdict"] == "PARITY-DISAGREES"
              and split["agrees"] is False
              and split["declared_code"] == REWIND
              and split["argument_code"] is None
              and split["ignorance"] == RWGB.IGNORANCE_NONE
              and split_over_ignorance["verdict"] == "PARITY-DISAGREES"
              and split_over_ignorance["ignorance"]
              == RWGB.IGNORANCE_DECLARED
              and before == after,
              "AC-RWGB4 a genuine split still reads PARITY-DISAGREES naming "
              "both codes, and a split reads DISAGREES even when one side is "
              "ignorant, so the new verdict never swallows a disagreement - "
              "and the tree digest is identical before and after")

        # ---- AC-RWGB5: CLI codes, one new key, byte-stable -----------------
        json_one = run_main(["--check", "--root", clean, "--json"])
        json_two = run_main(["--check", "--root", clean, "--json"])
        json_bad = run_main(["--check", "--root", bad, "--json"])
        RWW.window_report = rewind_report
        RWAG.reading = clean_reading
        try:
            code_split, out_split = run_main(["--check", "--root", clean])
        finally:
            RWW.window_report = saved_report
            RWAG.reading = saved_reading
        code_root, out_root = run_main(["--check", "--root",
                                        os.path.join(clean, "nope")])
        code_flag, _ = run_main(["--check", "--nope"])
        keys = tuple(json.loads(json_one[1]).keys())
        bad_keys = tuple(json.loads(json_bad[1]).keys())
        check(json_one[0] == 0 and json_one == json_two
              and keys == RWGB.REPORT_KEYS == RWGP.PARITY_KEYS + ("ignorance",)
              and bad_keys == RWGB.REPORT_KEYS
              and json.loads(json_one[1])["verdict"] == "PARITY-AGREES"
              and json_bad[0] == 1
              and json_one[1].endswith("}\n") and not json_one[1].endswith("\n\n")
              and code_split == 2 and "verdict=PARITY-DISAGREES" in out_split
              and code_root == 3 and "E_RWGB_ROOT" in out_root
              and code_flag == 5,
              "AC-RWGB5 the CLI exits 0 (agree) / 1 (unknown) / 2 (disagree) "
              "/ 3 (missing root) / 5 (bad flags) with a byte-stable --json "
              "over the eight parity keys plus exactly one new key "
              "'ignorance', in that order and with one trailing LF")

        # ---- AC-RWGB6: purity, delegation, wiring, live reading ------------
        ascii_ok = True
        try:
            io.open(MODULE, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        source = io.open(MODULE, "r", encoding="ascii").read()
        forbidden = ("import socket", "import urllib", "import http",
                     "import time", "import datetime", "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        no_second_parser = ("json.load" not in source
                            and '"declarations"' not in source
                            and "declared_by" not in source)
        delegated = ("import review_window_guard_parity as RWGP" in source
                     and "RWGP.check(" in source)

        def patched_parity(root, round_text=None):
            return {
                "verdict": "PARITY-AGREES",
                "rewind": False,
                "declared": "WINDOW",
                "declared_code": None,
                "declared_window": 99,
                "argument": "ARGUMENT-CLEAN",
                "argument_history": "MOVED",
                "argument_code": None,
                "agrees": True,
            }

        RWGP.check = patched_parity
        try:
            patched_blind = RWGB.check(clean)
        finally:
            RWGP.check = saved_parity

        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner
        live = RWGB.check(REPO)
        print("LIVE %s" % RWGB.one_line(live), flush=True)
        check(ascii_ok and no_network and no_second_parser and delegated
              and patched_blind["declared_window"] == 99
              and wired
              and live["verdict"] in RWGB.VERDICTS
              and live["agrees"] is (live["verdict"] == RWGB.VERDICT_AGREES)
              and live["ignorance"] in (RWGB.IGNORANCE_NONE,
                                        RWGB.IGNORANCE_DECLARED,
                                        RWGB.IGNORANCE_ARGUMENT,
                                        RWGB.IGNORANCE_BOTH),
              "AC-RWGB6 pure ASCII, stdlib only, zero network, no clock, "
              "read-only, the parity imported and asked at call time (a "
              "patched check moves this reading through to its window), wired "
              "as %s(%d), with the live tree reading taken"
              % (LABEL, EXPECTED_CRITERIA))
    finally:
        RWW.window_report = saved_report
        RWAG.reading = saved_reading
        RWGP.check = saved_parity
        for world in worlds:
            drop_world(world)

    total = PASSES + FAILS
    print("SUITE %s %d/%d" % ("PASS" if FAILS == 0 else "FAIL",
                              PASSES, total), flush=True)
    if total != EXPECTED_CRITERIA:
        print("FAIL criteria count %d != %d" % (total, EXPECTED_CRITERIA),
              flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())