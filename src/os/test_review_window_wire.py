"""review_window_wire suite (R2327; criteria AC-RWW1..AC-RWW6 were pinned in
state/queue/tech.md as the R2305 seed row BEFORE this code existed).

What this proves: R2305 pinned and dated the window a review is judged
against, but nothing consumed it - exempt_review still took --window as a
per-call argument whose only default lived in the CLI, so the declaration
could read PINNED while every actual age reading used another number. This
suite pins the wiring that closes the seam: the window comes from
review_window_decl.resolve through review_window_wire and is never
re-derived, an UNPINNED / DRIFT / refused declaration refuses the review
before any entry is aged, an explicit --window plus --window-from-declaration
is refused as two sources of truth, and for the same pinned window the
FRESH/STALE rows are byte-identical to the literal reading.

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
import review_window_wire as RWW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "exempt_review.py")
WIRE = os.path.join(BASE, "review_window_wire.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-wire"
WIRED_EXPECT = '"test_review_window_wire.py"), 6),'

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


def entry(queue, identity, declared, reason="accepted as it stands",
          until=None):
    row = {"queue": queue, "identity": identity, "declared": declared,
           "reason": reason}
    if until is not None:
        row["until"] = until
    return row


def window_body(window=20, declared_by="R2300", rows=None, top=None):
    if rows is None:
        rows = [{"window": window, "declared_by": declared_by,
                 "reason": "first pinned window"}]
    return {"window": window if top is None else top,
            "declared_by": declared_by,
            "reason": "pinned so it can only move through a new row",
            "declarations": rows}


def make_world(entries=None, window=None, raw_window=None, no_window=False):
    """A temp root: state/queue/prefix_exempt.json and state/review_window.json."""
    if entries is None:
        entries = [
            entry("tech", "old-one", "R2270"),
            entry("tech", "recent-one", "R2295"),
        ]
    world = tempfile.mkdtemp(prefix="bigdomain-rww-")
    inner = os.path.join(world, "state", "queue")
    os.makedirs(inner)
    with io.open(os.path.join(inner, "prefix_exempt.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"exemptions": entries}, indent=2))
    if not no_window:
        payload = (raw_window if raw_window is not None
                   else json.dumps(window_body() if window is None
                                   else window))
        with io.open(os.path.join(world, "state", "review_window.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
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


def run_cli(root, extra=None):
    cmd = [sys.executable, MODULE, "--root", root]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    worlds = []
    try:
        # ---- AC-RWW1: the window comes from the resolver, never re-derived ----
        world = make_world()
        worlds.append(world)
        saved = RWD.resolve
        try:
            RWD.resolve = lambda root, caller_window=None, round_text=None: {
                "window": 1000, "declared": 1000, "declared_by": "R2300",
                "reason": "patched", "round": round_text, "declarations": 1,
                "caller": caller_window, "verdict": "AGREES"}
            patched = RWW.declared_window(world, "R2327")
            through = ER.audit(world, "R2327",
                               window_source=ER.SOURCE_DECLARATION)
        finally:
            RWD.resolve = saved
        wire_source = io.open(WIRE, "r", encoding="ascii").read()
        imported = ("review_window_decl.resolve(" in wire_source
                    and "declarations[" not in wire_source
                    and "min(" not in wire_source)
        real = RWW.declared_window(world, "R2327")
        check(patched == 1000 and through["window"] == 1000
              and real == 20 and imported,
              "AC-RWW1 the window is imported from review_window_decl.resolve "
              "(a patched verdict flows straight through exempt_review) and is "
              "never re-derived from the declarations rows")

        # ---- AC-RWW2: a declaration that is not PINNED refuses, zero counts ----
        unpinned = make_world(no_window=True)
        worlds.append(unpinned)
        code_unpinned, out_unpinned = run_cli(
            unpinned, ["--round", "R2327", "--window-from-declaration"])
        drift = make_world(window={
            "window": 20, "declared_by": "R2300",
            "reason": "pinned window",
            "declarations": [{"window": 10, "declared_by": "R2300",
                              "reason": "moved without a new row"}]})
        worlds.append(drift)
        code_drift, out_drift = run_cli(
            drift, ["--round", "R2327", "--window-from-declaration"])
        check(code_unpinned == 2 and code_drift == 2
              and "E_RWW_UNPINNED" in out_unpinned
              and "E_RWW_DRIFT" in out_drift
              and "entries=0" in out_unpinned and "entries=0" in out_drift
              and "WINDOW-REFUSED" in out_unpinned
              and "EXEMPT REVIEW round=R2327 window=100" not in out_unpinned,
              "AC-RWW2 an UNPINNED or DRIFT declaration refuses at exit 2 with "
              "zero counts and its own code, never the CLI default window")

        # ---- AC-RWW3: one source of truth ----
        code_both, out_both = run_cli(
            world, ["--round", "R2327", "--window", "20",
                    "--window-from-declaration"])
        check(code_both == 5 and "E_RWW_BOTH" in out_both
              and "--window" in out_both
              and "--window-from-declaration" in out_both,
              "AC-RWW3 --window with --window-from-declaration is refused "
              "naming both rather than resolved by precedence")

        # ---- AC-RWW4: same pinned window, byte-identical rows ----
        code_lit, out_lit = run_cli(
            world, ["--round", "R2327", "--window", "20", "--json"])
        code_decl, out_decl = run_cli(
            world, ["--round", "R2327", "--window-from-declaration", "--json"])
        lit = json.loads(out_lit)
        decl = json.loads(out_decl)
        check(code_lit == code_decl == 2
              and lit["window"] == decl["window"] == 20
              and json.dumps(lit["entries"], sort_keys=True)
              == json.dumps(decl["entries"], sort_keys=True)
              and json.dumps(lit["stale"], sort_keys=True)
              == json.dumps(decl["stale"], sort_keys=True)
              and lit["stale_count"] == decl["stale_count"] == 2
              and decl["window_source"] == ER.SOURCE_DECLARATION
              and lit["window_source"] == ER.SOURCE_ARGUMENT,
              "AC-RWW4 for the same world the FRESH/STALE rows are "
              "byte-identical whether the pinned number is passed explicitly "
              "or read from the declaration, and the window is the pinned one")

        # ---- AC-RWW5: CLI codes, byte-stable pinned JSON, pure read ----
        clean = make_world(entries=[entry("tech", "recent-one", "R2326")])
        worlds.append(clean)
        code_clean, out_clean = run_cli(
            clean, ["--round", "R2327", "--window-from-declaration", "--json"])
        before = digest_tree(clean)
        first = run_cli(clean, ["--round", "R2327",
                                "--window-from-declaration", "--json"])
        second = run_cli(clean, ["--round", "R2327",
                                 "--window-from-declaration", "--json"])
        after = digest_tree(clean)
        bad = make_world(raw_window="{not json")
        worlds.append(bad)
        code_bad, out_bad = run_cli(
            bad, ["--round", "R2327", "--window-from-declaration"])
        code_flag, _out_flag = run_cli(clean, ["--round", "R2327", "--nope"])
        keys = tuple(json.loads(first[1]).keys())
        check(code_clean == 0 and "REVIEW-CLEAN" in out_clean
              and first == second and first[1] == out_clean
              and keys == ER.REPORT_KEYS and before == after
              and code_bad == 2 and "E_RWW_UNREADABLE" in out_bad
              and code_flag == 5,
              "AC-RWW5 CLI exits 0/2/5 with a byte-stable --json over the "
              "pinned keys (window source included), and the reading writes "
              "nothing")

        # ---- AC-RWW6: purity, wiring, live reading ----
        ascii_ok = True
        try:
            io.open(MODULE, "rb").read().decode("ascii")
            io.open(WIRE, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "import time", "import datetime", "requests", "urlopen")
        combined = (io.open(MODULE, "r", encoding="ascii").read()
                    + io.open(WIRE, "r", encoding="ascii").read())
        no_network = not any(token in combined for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner
        live = ER.audit(REPO, "R2327", window_source=ER.SOURCE_DECLARATION)
        print("LIVE %s" % ER.one_line(live), flush=True)
        check(ascii_ok and no_network and wired
              and live["window_source"] == ER.SOURCE_DECLARATION
              and live["verdict"] in ER.VERDICTS,
              "AC-RWW6 pure ASCII, stdlib only, zero network, no clock, "
              "wired as %s(%d), live reading taken through the declaration"
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