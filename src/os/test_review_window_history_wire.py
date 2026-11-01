"""review_window_history_wire suite (R2359).

Criteria AC-RWHW1..AC-RWHW6 were pinned inside the R2345 seed row of
state/queue/tech.md BEFORE this guard existed.

What this proves: R2345 shipped a reader that treats the declarations list as
a history and refuses one that rewinds, but nothing consumed it -
`review_window_wire.declared_window` asked `review_window_decl.resolve` only,
and that resolver compares the last row against the top-level window while
being blind to the ORDER of the rows. So `exempt_review` could age every
accepted entry against a window taken from a list whose own declared_by goes
backwards, and no reading named it.

This suite pins the wire that closes the seam: the history is asked FIRST and
a rewind refuses before any window is handed back; a DRIFT or UNPINNED
history keeps the resolver's own code and its own words; a legal
moved-but-monotonic list is a REPORT, not a refusal, and its moves are named;
and a refusal writes nothing.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import exempt_review as ER  # noqa: E402
import review_window_decl as RWD  # noqa: E402
import review_window_history as RWH  # noqa: E402
import review_window_wire as RWW  # noqa: E402

EXPECTED_CRITERIA = 6
WIRE = os.path.join(BASE, "review_window_wire.py")
MODULE = os.path.join(BASE, "exempt_review.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-history-wire"
WIRED_EXPECT = '"test_review_window_history_wire.py"), 6),'

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


def row(window, declared_by, reason="pinned window"):
    return {"window": window, "declared_by": declared_by, "reason": reason}


def body(window, rows, reason=None):
    return {
        "window": window,
        "declared_by": rows[-1]["declared_by"],
        "reason": reason or "pinned so it can only move through a new row",
        "declarations": rows,
    }


def make_world(payload=None, raw=None, entries=None, no_window=False):
    """A temp root: state/review_window.json and a small exempt set."""
    if entries is None:
        entries = [{"queue": "tech", "identity": "recent-one",
                    "declared": "R2295", "reason": "accepted as it stands"}]
    world = tempfile.mkdtemp(prefix="bigdomain-rwhw-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    with io.open(os.path.join(inner, "prefix_exempt.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"exemptions": entries}, indent=2))
    if not no_window:
        text = raw if raw is not None else json.dumps(payload, indent=2)
        with io.open(os.path.join(world, "state", "review_window.json"), "w",
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


def run_cli(module, root, extra=None):
    cmd = [sys.executable, module, "--root", root]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def refusal(callable_):
    try:
        callable_()
    except RWW.ReviewWindowWireError as exc:
        return exc.code, exc.detail
    return None, None


def main():
    worlds = []
    try:
        # ---- AC-RWHW1: the history is asked FIRST and a rewind refuses ----
        world = make_world(body(20, [row(20, "R2300")]))
        worlds.append(world)
        saved = RWH.history

        def rewinding(root):
            raise RWH.ReviewWindowHistoryError(
                "E_RWH_REWIND",
                "declaration 1 declared_by=R2300 is earlier than declaration "
                "0 declared_by=R2400 (window 20 -> 10)")

        try:
            RWH.history = rewinding
            code, detail = refusal(lambda: RWW.declared_window(world, "R2359"))
            code_report, _ = refusal(lambda: RWW.window_report(world, "R2359"))
        finally:
            RWH.history = saved
        source = io.open(WIRE, "r", encoding="ascii").read()
        imported = ("review_window_history.history(" in source
                    and "import review_window_history" in source)
        check(code == "E_RWHW_DECL_HISTORY" == code_report
              and "E_RWH_REWIND" in detail
              and "R2300" in detail and "R2400" in detail
              and imported and "declared_by\"] <" not in source,
              "AC-RWHW1 declared_window asks review_window_history.history "
              "first (a patched history flows straight through) and refuses "
              "E_RWHW_DECL_HISTORY carrying the history's own code and both "
              "rounds before any window is handed back")

        # ---- AC-RWHW2: DRIFT keeps the resolver's own words ----
        agree = body(20, [row(20, "R2300")])
        drift = body(10, [row(20, "R2300")])
        agree_world = make_world(agree)
        drift_world = make_world(drift)
        worlds.extend([agree_world, drift_world])
        differing = [key for key in ("window", "declared_by", "reason",
                                     "declarations")
                     if json.dumps(agree[key]) != json.dumps(drift[key])]
        ok_window = RWW.declared_window(agree_world, "R2359")
        code_drift, detail_drift = refusal(
            lambda: RWW.declared_window(drift_world, "R2359"))
        try:
            RWD.resolve(drift_world, None, "R2359")
            resolver_detail = None
        except RWD.ReviewWindowError as exc:
            resolver_detail = exc.detail
        check(code_drift == "E_RWW_DRIFT"
              and differing == ["window"]
              and resolver_detail is not None
              and detail_drift == resolver_detail
              and ok_window == 20,
              "AC-RWHW2 a DRIFT history carries the resolver's own DRIFT "
              "detail through the wire unchanged (measured against the "
              "resolver exception itself, on two fixtures that differ by "
              "exactly the top-level window)")

        # ---- AC-RWHW3: UNPINNED keeps its old code and its old words ----
        unpinned = make_world(no_window=True)
        worlds.append(unpinned)
        code_unpinned, detail_unpinned = refusal(
            lambda: RWW.declared_window(unpinned, "R2359"))
        try:
            RWD.resolve(unpinned, None, "R2359")
            absent_detail = None
        except RWD.ReviewWindowError as exc:
            absent_detail = (exc.code, exc.detail)
        cli_code, cli_out = run_cli(
            MODULE, unpinned, ["--round", "R2359",
                               "--window-from-declaration"])
        check(code_unpinned == "E_RWW_UNPINNED"
              and absent_detail is not None
              and absent_detail[0] == "E_RWD_UNPINNED"
              and detail_unpinned == absent_detail[1]
              and cli_code == 2 and "E_RWW_UNPINNED" in cli_out
              and "entries=0" in cli_out
              and "verdict=WINDOW-REFUSED" in cli_out,
              "AC-RWHW3 an UNPINNED history keeps the existing E_RWW_UNPINNED "
              "pathway byte-identical (same code, the resolver's own detail, "
              "zero counts and WINDOW-REFUSED), so the guard adds a refusal "
              "without changing the meaning of the absent case")

        # ---- AC-RWHW4: a legal move is a report, not a refusal ----
        moved = make_world(body(20, [row(10, "R2300"), row(20, "R2310")]))
        worlds.append(moved)
        report = RWW.window_report(moved, "R2359")
        report_again = RWW.window_report(moved, "R2359")
        live = ER.audit(moved, "R2359",
                        window_source=ER.SOURCE_DECLARATION)
        check(report["verdict"] == "MOVED" and report["window"] == 20
              and report["history"] == "MOVED"
              and len(report["moves"]) == 1
              and report["moves"][0]["from"] == 10
              and report["moves"][0]["to"] == 20
              and report["moves"][0]["to_round"] == "R2310"
              and json.dumps(report, sort_keys=True)
              == json.dumps(report_again, sort_keys=True)
              and live["window"] == 20,
              "AC-RWHW4 a moved-but-monotonic history still hands the last "
              "row's window out (exempt_review ages against it) and names "
              "every move in the wire report, so a legal move is never turned "
              "into a refusal")

        # ---- AC-RWHW5: CLI codes, pinned keys, byte-stable, pure read ----
        clean = make_world(body(20, [row(20, "R2300")]))
        drift_cli = make_world(drift)
        bad = make_world(raw="{not json")
        worlds.extend([clean, drift_cli, bad])
        before = digest_tree(drift_cli)
        first = run_cli(WIRE, clean, ["--check", "--round", "R2359",
                                      "--json"])
        second = run_cli(WIRE, clean, ["--check", "--round", "R2359",
                                       "--json"])
        code_moved, out_moved = run_cli(WIRE, moved, ["--check", "--json"])
        code_drift_cli, out_drift_cli = run_cli(WIRE, drift_cli,
                                                ["--check", "--json"])
        after = digest_tree(drift_cli)
        code_bad, out_bad = run_cli(WIRE, bad, ["--check"])
        code_flag, _ = run_cli(WIRE, clean, ["--check", "--nope"])
        keys = tuple(json.loads(first[1]).keys())
        check(first[0] == 0 and first == second
              and keys == RWW.REPORT_KEYS
              and code_moved == 0
              and json.loads(out_moved)["verdict"] == "MOVED"
              and code_drift_cli == 2 and "E_RWW_DRIFT" in out_drift_cli
              and code_bad == 3 and "E_RWW_UNREADABLE" in out_bad
              and code_flag == 5 and before == after,
              "AC-RWHW5 the wire CLI exits 0/2/3/5 with a byte-stable --json "
              "over the pinned REPORT_KEYS, and a refusal leaves the "
              "declaration bytes untouched")

        # ---- AC-RWHW6: purity, imported law, wiring, live reading ----
        ascii_ok = True
        try:
            io.open(WIRE, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "import time", "import datetime", "requests", "urlopen")
        text = io.open(WIRE, "r", encoding="ascii").read()
        no_network = not any(token in text for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner
        patched_moves = [
            {"index": 1, "from": 5, "to": 10, "from_round": "R2300",
             "to_round": "R2305"},
            {"index": 2, "from": 10, "to": 20, "from_round": "R2305",
             "to_round": "R2310"},
        ]

        def moved_history(root):
            return {"verdict": "MOVED", "declarations": 3, "rows": [],
                    "moves": patched_moves, "rewind": None, "window": 20,
                    "declared_by": "R2310", "resolver": "AGREES"}

        try:
            RWH.history = moved_history
            patched = RWW.window_report(clean, "R2359")
        finally:
            RWH.history = saved
        live_wire = RWW.window_report(REPO, "R2359")
        print("LIVE %s" % RWW.one_line(live_wire), flush=True)
        check(ascii_ok and no_network and wired
              and patched["verdict"] == "MOVED"
              and len(patched["moves"]) == 2
              and patched["moves"][1]["to_round"] == "R2310"
              and live_wire["verdict"] in RWW.VERDICTS
              and live_wire["window"] >= 1,
              "AC-RWHW6 pure ASCII, stdlib only, zero network, no clock, the "
              "history law imported rather than restated (a patched history "
              "moves the report), wired as %s(%d), live reading taken"
              % (LABEL, EXPECTED_CRITERIA))
    finally:
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