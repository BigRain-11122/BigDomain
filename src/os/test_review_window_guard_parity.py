"""review_window_guard_parity suite (R2381).

Criteria AC-RWGP1..AC-RWGP6 were pinned inside the R2371 seed row of
state/queue/tech.md BEFORE the parity module existed.

What this proves: the same declarations list is read by two faces -
review_window_wire.window_report (the DECLARED path) and
review_window_wire_argument_guard.reading (the ARGUMENT path) - and each was
proved only on its own fixtures, so a future edit to either law could split
the two paths in silence. This suite pins one reading that hands the same file
to both faces and says AGREES or names the first split.

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

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "review_window_guard_parity.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-guard-parity"
WIRED_EXPECT = '"test_review_window_guard_parity.py"), 6),'
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
    world = tempfile.mkdtemp(prefix="bigdomain-rwgp-")
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
        code = RWGP.main(argv)
    return code, buf.getvalue()


def main():
    worlds = []
    saved_report = RWW.window_report
    saved_reading = RWAG.reading
    try:
        clean = make_world(body(20, [row(20, "R2300")]))
        rewind = make_world(body(20, [row(20, "R2400"), row(10, "R2300")]))
        unpinned = make_world(no_window=True)
        bad = make_world(raw="{not json")
        worlds.extend([clean, rewind, unpinned, bad])

        # ---- AC-RWGP1: both faces IMPORTED; patching either moves it -------
        baseline = RWGP.check(clean)

        def rewind_report(root, round_text):
            raise RWW.ReviewWindowWireError(REWIND, "E_RWH_REWIND R2400 R2300")

        RWW.window_report = rewind_report
        try:
            patched_declared = RWGP.check(clean)
        finally:
            RWW.window_report = saved_report

        RWAG.reading = lambda root: {
            "verdict": "ARGUMENT-REFUSED", "code": REWIND,
            "history": "E_RWH_REWIND"}
        try:
            patched_argument = RWGP.check(clean)
        finally:
            RWAG.reading = saved_reading

        source = io.open(MODULE, "r", encoding="ascii").read()
        imported = ("import review_window_wire as RWW" in source
                    and "import review_window_wire_argument_guard as RWAG"
                    in source
                    and "RWW.window_report(" in source
                    and "RWAG.reading(" in source)
        no_second_parser = ("json.load" not in source
                            and '"declarations"' not in source
                            and "declared_by" not in source)
        check(baseline["verdict"] == "PARITY-AGREES"
              and patched_declared["verdict"] == "PARITY-DISAGREES"
              and patched_argument["verdict"] == "PARITY-DISAGREES"
              and imported and no_second_parser,
              "AC-RWGP1 both faces are imported and asked at call time "
              "(patching window_report moves the verdict, patching reading "
              "moves it too) and this module carries no second declarations "
              "reader, no row parser and no declared_by comparison")

        # ---- AC-RWGP2: a rewinding list agrees on the carried code --------
        found = RWGP.check(rewind)
        code_d, _ = run_main(["--check", "--root", rewind])
        check(found["verdict"] == "PARITY-AGREES"
              and found["rewind"] is True
              and found["declared_code"] == REWIND
              and found["argument_code"] == REWIND
              and found["agrees"] is True
              and code_d == 0,
              "AC-RWGP2 a rewinding declaration reads PARITY-AGREES with BOTH "
              "faces naming the carried %s, and the CLI exits 0" % REWIND)

        # ---- AC-RWGP3: monotonic / unpinned are different questions --------
        moved = make_world(body(20, [row(10, "R2300"), row(20, "R2310")]))
        worlds.append(moved)
        moved_report = RWGP.check(moved)
        unpinned_report = RWGP.check(unpinned)
        clean_report = RWGP.check(clean)
        argument_word = RWAG.reading(clean).get("history")
        check(moved_report["verdict"] == "PARITY-AGREES"
              and moved_report["declared_window"] == 20
              and moved_report["argument"] == "ARGUMENT-CLEAN"
              and moved_report["argument_history"] == "MOVED"
              and clean_report["verdict"] == "PARITY-AGREES"
              and clean_report["declared_window"] == 20
              and argument_word == "EMPTY-HISTORY"
              and unpinned_report["verdict"] == "PARITY-AGREES"
              and unpinned_report["declared_code"] == "E_RWW_UNPINNED"
              and unpinned_report["argument"] == "ARGUMENT-CLEAN",
              "AC-RWGP3 a monotonic list (and an UNPINNED one the argument "
              "path deliberately ignores) reads PARITY-AGREES with the "
              "declared window carried from the wire and the argument guard's "
              "own history word beside it - two different questions, not a "
              "disagreement")

        # ---- AC-RWGP4: a patched divergence is named, nothing is written ---
        before = digest_tree(clean)

        def clean_reading(root):
            return {"verdict": "ARGUMENT-CLEAN", "history": "MOVED", "code": None}

        RWW.window_report = rewind_report
        RWAG.reading = clean_reading
        try:
            split = RWGP.check(clean)
        finally:
            RWW.window_report = saved_report
            RWAG.reading = saved_reading
        after = digest_tree(clean)
        RWAG.reading = lambda root: {
            "verdict": "ARGUMENT-REFUSED", "code": REWIND,
            "history": "E_RWH_REWIND"}
        try:
            split_other = RWGP.check(clean)
        finally:
            RWAG.reading = saved_reading
        check(split["verdict"] == "PARITY-DISAGREES"
              and split["agrees"] is False
              and split["declared_code"] == REWIND
              and split["argument_code"] is None
              and split_other["verdict"] == "PARITY-DISAGREES"
              and split_other["argument_code"] == REWIND
              and split_other["declared_code"] is None
              and before == after,
              "AC-RWGP4 a patched divergence on EITHER side reads "
              "PARITY-DISAGREES naming both codes, and the tree digest is "
              "identical before and after - the parity writes nothing")

        # ---- AC-RWGP5: CLI codes, pinned keys, byte-stable -----------------
        json_one = run_main(["--check", "--root", clean, "--json"])
        json_two = run_main(["--check", "--root", clean, "--json"])
        RWAG.reading = clean_reading
        RWW.window_report = rewind_report
        try:
            code_split, out_split = run_main(["--check", "--root", clean])
        finally:
            RWW.window_report = saved_report
            RWAG.reading = saved_reading
        code_root, out_root = run_main(["--check", "--root",
                                        os.path.join(clean, "nope")])
        code_flag, _ = run_main(["--check", "--nope"])
        keys = tuple(json.loads(json_one[1]).keys())
        check(json_one[0] == 0 and json_one == json_two
              and keys == RWGP.PARITY_KEYS
              and json.loads(json_one[1])["verdict"] == "PARITY-AGREES"
              and code_split == 2
              and "verdict=PARITY-DISAGREES" in out_split
              and code_root == 3 and "E_RWGP_ROOT" in out_root
              and code_flag == 5,
              "AC-RWGP5 the CLI exits 0 (agree) / 2 (disagree) / 3 (missing "
              "root) / 5 (bad flags) with a byte-stable --json over the "
              "pinned PARITY_KEYS and one trailing LF")

        # ---- AC-RWGP6: purity, wiring, and a real live reading -------------
        ascii_ok = True
        try:
            io.open(MODULE, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "import time", "import datetime", "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner
        live = RWGP.check(REPO)
        print("LIVE %s" % RWGP.one_line(live), flush=True)
        check(ascii_ok and no_network and wired
              and live["verdict"] in RWGP.VERDICTS
              and live["agrees"] is (live["verdict"] == "PARITY-AGREES"),
              "AC-RWGP6 pure ASCII, stdlib only, zero network, no clock, "
              "read-only, wired as %s(%d), with the live tree reading taken"
              % (LABEL, EXPECTED_CRITERIA))
    finally:
        RWW.window_report = saved_report
        RWAG.reading = saved_reading
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