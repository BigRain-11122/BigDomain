"""review_window_wire_argument_guard suite (R2371).

Criteria AC-RWAG1..AC-RWAG6 were pinned inside the R2359 seed row of
state/queue/tech.md BEFORE this guard existed.

What this proves: R2345 shipped review_window_history (the declarations list
read as a HISTORY) and R2359 wired it into the DECLARED path, so
`exempt_review --window-from-declaration` refuses a list whose declared_by
rewinds. The ARGUMENT path never asked: `exempt_review --window N` took the
number, aged every entry and returned, so an explicit window silently
overrode a list that is not a history at all.

This suite pins the guard that closes that seam: the rewind law is IMPORTED
(and its code is carried from the wire's own mapping, so the argument path
refuses with the declared path's E_RWHW_DECL_HISTORY), the refusal happens
before any entry is aged with zero counts, and every other outcome -
monotonic, UNPINNED, DRIFT, unreadable - leaves the explicit window's reading
byte-identical, because the guard adds a refusal and nothing else.

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
import review_window_history as RWH  # noqa: E402
import review_window_wire_argument_guard as RWAG  # noqa: E402

EXPECTED_CRITERIA = 6
GUARD = os.path.join(BASE, "review_window_wire_argument_guard.py")
MODULE = os.path.join(BASE, "exempt_review.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-wire-argument-guard"
WIRED_EXPECT = '"test_review_window_wire_argument_guard.py"), 6),'

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


def make_world(payload=None, raw=None, entries=None, no_window=False):
    """A temp root: state/review_window.json plus one exempt entry."""
    if entries is None:
        entries = [{"queue": "tech", "identity": "recent-one",
                    "declared": "R2295", "reason": "accepted as it stands"}]
    world = tempfile.mkdtemp(prefix="bigdomain-rwag-")
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
    cmd = [sys.executable, module]
    if root is not None:
        cmd.extend(["--root", root])
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    worlds = []
    saved_history = RWH.history
    saved_guard = RWAG.guard
    try:
        # ---- AC-RWAG1: the rewind is imported and carried, never restated --
        clean_world = make_world(body(20, [row(20, "R2300")]))
        rewind_world = make_world(body(20, [row(20, "R2400"),
                                            row(10, "R2300")]))
        worlds.extend([clean_world, rewind_world])

        def rewinding(root):
            raise RWH.ReviewWindowHistoryError(
                "E_RWH_REWIND",
                "declaration 1 declared_by=R2300 is earlier than "
                "declaration 0 declared_by=R2400 (window 20 -> 10)")

        RWH.history = rewinding
        try:
            code = None
            detail = None
            try:
                RWAG.guard(clean_world)
            except RWAG.ReviewWindowArgumentGuardError as exc:
                code, detail = exc.code, exc.detail
            audit_code = None
            try:
                ER.audit(clean_world, "R2359", window=20)
            except RWAG.ReviewWindowArgumentGuardError as exc:
                audit_code = exc.code
        finally:
            RWH.history = saved_history
        source = io.open(GUARD, "r", encoding="ascii").read()
        # The module imports the law under its own alias, so the proof is the
        # import line plus the CALL through that alias - asserted against the
        # style this file actually uses, not a full-name call it never makes.
        imported = ("import review_window_history" in source
                    and "RWH.history(" in source
                    and "carry_history_code(" in source)
        # A patched history must move THIS face, which only holds if the law
        # is asked at call time rather than copied into the file.
        real_code, real_out = run_cli(MODULE, rewind_world,
                                      ["--round", "R2359", "--window", "20"])
        check(code == "E_RWHW_DECL_HISTORY"
              and audit_code == "E_RWHW_DECL_HISTORY"
              and "E_RWH_REWIND" in detail
              and "R2400" in detail and "R2300" in detail
              and imported and "declared_by\"] <" not in source
              and real_code == 2
              and "REFUSE E_RWHW_DECL_HISTORY" in real_out,
              "AC-RWAG1 the argument path asks review_window_history first "
              "and refuses the declared path's own E_RWHW_DECL_HISTORY "
              "naming both rounds - on a patched history AND on a real "
              "rewinding declaration file, with the law imported not restated")

        # ---- AC-RWAG2: a monotonic list keeps its reading byte-identical --
        fresh = [{"queue": "tech", "identity": "fresh-one",
                  "declared": "R2350", "reason": "accepted as it stands"}]
        moved_world = make_world(body(20, [row(10, "R2300"),
                                           row(20, "R2310")]), entries=fresh)
        monotone_world = make_world(body(20, [row(20, "R2300")]))
        worlds.extend([moved_world, monotone_world])
        guarded = ER.audit(moved_world, "R2359", window=20)
        RWAG.guard = lambda root: {"verdict": "ARGUMENT-CLEAN"}
        try:
            unguarded = ER.audit(moved_world, "R2359", window=20)
        finally:
            RWAG.guard = saved_guard
        code_m, out_m = run_cli(MODULE, moved_world,
                                ["--round", "R2359", "--window", "20"])
        check(json.dumps(guarded, sort_keys=True) == json.dumps(unguarded,
                                                               sort_keys=True)
              and tuple(guarded.keys()) == ER.REPORT_KEYS
              and guarded["window"] == 20
              and len(guarded["entries"]) == len(unguarded["entries"]) == 1
              and code_m == 0
              and out_m.splitlines()[0] == ER.one_line(unguarded),
              "AC-RWAG2 a lone-argument reading on a monotonic declaration "
              "stays byte-identical (same report keys, same rows, same "
              "window, same printed line), so the guard adds a refusal and "
              "nothing else")

        # ---- AC-RWAG3: UNPINNED keeps today's reading exactly ---------------
        unpinned = make_world(no_window=True, entries=fresh)
        worlds.append(unpinned)
        guarded_un = ER.audit(unpinned, "R2359", window=20)
        RWAG.guard = lambda root: {"verdict": "ARGUMENT-CLEAN"}
        try:
            unguarded_un = ER.audit(unpinned, "R2359", window=20)
        finally:
            RWAG.guard = saved_guard
        code_u, out_u = run_cli(MODULE, unpinned,
                                ["--round", "R2359", "--window", "20"])
        guard_un = RWAG.reading(unpinned)
        check(json.dumps(guarded_un, sort_keys=True)
              == json.dumps(unguarded_un, sort_keys=True)
              and guarded_un["window"] == 20
              and guarded_un["declaration"] == "PINNED"
              and guard_un["verdict"] == "ARGUMENT-CLEAN"
              and guard_un["history"] == "UNPINNED"
              and guard_un["window"] is None
              and code_u == 0 and "REVIEW-CLEAN" in out_u,
              "AC-RWAG3 an UNPINNED window declaration keeps the argument "
              "path's reading byte-identical and exits 0 with the caller's "
              "window intact, while the guard's own line says history=UNPINNED "
              "- because an explicit window is the caller's and not the "
              "declaration's")

        # ---- AC-RWAG4: the refusal lands before any entry is aged ----------
        before = digest_tree(rewind_world)
        audit_code4 = None
        try:
            ER.audit(rewind_world, "R2359", window=20)
        except RWAG.ReviewWindowArgumentGuardError as exc:
            audit_code4 = exc.code
        code_r, out_r = run_cli(MODULE, rewind_world,
                                ["--round", "R2359", "--window", "20"])
        after = digest_tree(rewind_world)
        check(audit_code4 == "E_RWHW_DECL_HISTORY"
              and code_r == 2
              and "verdict=WINDOW-REFUSED" in out_r
              and "entries=0" in out_r and "stale=0" in out_r
              and "source=argument" in out_r
              and before == after,
              "AC-RWAG4 the refusal happens before any entry is aged - zero "
              "counts and WINDOW-REFUSED on the CLI, with the declaration "
              "bytes untouched (whole-tree digest identical before and after)")

        # ---- AC-RWAG5: guard CLI codes, pinned keys, byte-stable ----------
        bad = make_world(raw="{not json")
        worlds.append(bad)
        first = run_cli(GUARD, clean_world, ["--check", "--json"])
        second = run_cli(GUARD, clean_world, ["--check", "--json"])
        code_rw, out_rw = run_cli(GUARD, rewind_world, ["--check"])
        code_bad, out_bad = run_cli(GUARD, bad, ["--check"])
        code_flag, _ = run_cli(GUARD, clean_world, ["--check", "--nope"])
        keys = tuple(json.loads(first[1]).keys())
        code_stale, _ = run_cli(MODULE, monotone_world,
                                ["--round", "R2359", "--window", "20"])
        check(first[0] == 0 and first == second
              and keys == RWAG.REPORT_KEYS
              and json.loads(first[1])["verdict"] == "ARGUMENT-CLEAN"
              and code_rw == 2 and "E_RWHW_DECL_HISTORY" in out_rw
              and code_bad == 2 and "ARGUMENT-UNKNOWN" in out_bad
              and code_flag == 5
              and code_stale == 2,
              "AC-RWAG5 the guard CLI exits 0/2/5 with a byte-stable --json "
              "over the pinned REPORT_KEYS, an unreadable list reads "
              "ARGUMENT-UNKNOWN (never a silent pass), and the exempt_review "
              "codes for the argument path are unchanged (clean 0, stale 2)")

        # ---- AC-RWAG6: purity, wiring, and a patched history moves it -----
        ascii_ok = True
        try:
            io.open(GUARD, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "import time", "import datetime", "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner

        def moved_history(root):
            return {"verdict": "MOVED", "declarations": 3, "rows": [],
                    "moves": [{"index": 1, "from": 10, "to": 20,
                               "from_round": "R2300", "to_round": "R2310"},
                              {"index": 2, "from": 20, "to": 30,
                               "from_round": "R2310", "to_round": "R2320"}],
                    "rewind": None, "window": 30, "declared_by": "R2320",
                    "resolver": "AGREES"}

        RWH.history = moved_history
        try:
            patched = RWAG.reading(clean_world)
        finally:
            RWH.history = saved_history
        live = RWAG.reading(REPO)
        print("LIVE %s" % RWAG.one_line(live), flush=True)
        check(ascii_ok and no_network and wired
              and patched["verdict"] == "ARGUMENT-CLEAN"
              and patched["history"] == "MOVED"
              and len(patched["moves"]) == 2
              and patched["window"] == 30
              and live["verdict"] in RWAG.VERDICTS
              and live["history"] in RWH.VERDICTS,
              "AC-RWAG6 pure ASCII, stdlib only, zero network, no clock, the "
              "history law imported rather than restated (a patched history "
              "moves this report), wired as %s(%d), live reading taken"
              % (LABEL, EXPECTED_CRITERIA))
    finally:
        RWH.history = saved_history
        RWAG.guard = saved_guard
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