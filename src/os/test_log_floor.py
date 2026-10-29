"""log_floor suite (R2265; criteria AC-LFL1..AC-LFL6 were pinned in
state/queue/tech.md as the R2263 seed row BEFORE this code existed).

What this proves: `queue_only_reconcile` splits its residue against a floor the
caller supplies, and its live reading derived that floor from the log's own
smallest label - blind at the window bottom edge. This suite pins the
declaration: one pinned shape with a missing file read as UNPINNED rather than
a fabricated pass, a floor newer than the live log's oldest label refused, a
floor predating its own declaration refused, a silent forward bump reported as
DRIFT with both rounds named, the CLI codes and the byte-stable JSON, and the
module's purity, wiring and live reading.

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

import log_floor as LF  # noqa: E402
import state_seq as SS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "log_floor.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-log-floor"
WIRED_EXPECT = '"test_log_floor.py"), 6),'

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


def make_world(items, declaration=None, tick=1, raw_state=None,
               raw_declaration=None):
    """Build a temp root: src/os/state.json plus an optional log_floor.json."""
    world = tempfile.mkdtemp(prefix="bigdomain-lfl-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    target = os.path.join(inner, "state.json")
    body = raw_state if raw_state is not None else json.dumps(
        {"tick": tick, "log": list(items)})
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    if declaration is not None or raw_declaration is not None:
        sdir = os.path.join(world, "state")
        os.makedirs(sdir)
        dpath = os.path.join(sdir, "log_floor.json")
        payload = (raw_declaration if raw_declaration is not None
                   else json.dumps(declaration))
        with io.open(dpath, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
    return world


def declaration(floor="R100", declared_by="R120", rows=None,
                reason="a dated floor"):
    if rows is None:
        rows = [{"floor": floor, "declared_by": declared_by,
                 "reason": reason}]
    return {"floor": floor, "declared_by": declared_by,
            "reason": reason, "declarations": rows}


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    for base, _dirs, files in os.walk(world):
        for name in sorted(files):
            full = os.path.join(base, name)
            with open(full, "rb") as handle:
                data = handle.read()
            rel = os.path.relpath(full, world).replace("\\", "/")
            parts.append("%s %s" % (rel, hashlib.sha256(data).hexdigest()))
    return "|".join(sorted(parts))


def run_cli(world, extra=None):
    argv = [sys.executable, MODULE, "--check"]
    if extra is not None:
        argv.extend(extra)
    argv.extend(["--root", world])
    proc = subprocess.run(argv, cwd=REPO, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    worlds = []
    try:
        # ---- AC-LFL1: one pinned shape; a missing file reads UNPINNED ----
        world = make_world(["2026-10-29 R100 (a logged item)"])
        worlds.append(world)
        unpinned = LF.audit(world)
        code, out = run_cli(world)
        missing_is_unpinned = (unpinned["verdict"] == "UNPINNED"
                               and unpinned["floor"] is None
                               and code == 2 and "UNPINNED" in out)
        pinned = make_world(["2026-10-29 R100 (a logged item)"],
                            declaration=declaration())
        worlds.append(pinned)
        good = LF.audit(pinned)
        shape_ok = (good["verdict"] == "PINNED" and good["floor"] == 100
                    and good["declared"] == 100
                    and good["declared_by"] == 120)
        bad_shapes = 0
        for bad in ({}, {"floor": "R100"}, {"floor": "R100",
                                           "declared_by": "R120",
                                           "reason": "",
                                           "declarations": [{}]},
                    {"floor": "R100", "declared_by": "R120",
                     "reason": "x", "declarations": []}):
            broken = make_world(["2026-10-29 R100 (a logged item)"],
                                raw_declaration=json.dumps(bad))
            worlds.append(broken)
            try:
                LF.audit(broken)
            except LF.LogFloorError as exc:
                bad_shapes += 1 if exc.code == "E_LFL_BAD_SHAPE" else 0
        check(missing_is_unpinned and shape_ok and bad_shapes == 4,
              "AC-LFL1 one pinned shape; a missing file is UNPINNED at exit 2, "
              "four malformed files are refused")

        # ---- AC-LFL2: a floor newer than the live log's oldest label ----
        ahead = make_world(["2026-10-29 R100 (a logged item)"],
                           declaration=declaration(floor="R200",
                                                   declared_by="R220"))
        worlds.append(ahead)
        code_ahead, out_ahead = run_cli(ahead)
        no_verdict = ("VERDICT" not in out_ahead and "PINNED" not in out_ahead
                      and "UNPINNED" not in out_ahead)
        edge = make_world(["2026-10-29 R100 (a logged item)"],
                          declaration=declaration(floor="R100",
                                                  declared_by="R120"))
        worlds.append(edge)
        at_edge = LF.audit(edge)["verdict"] == "PINNED"
        check(code_ahead == 2 and "E_LFL_FLOOR_AHEAD" in out_ahead
              and no_verdict and at_edge,
              "AC-LFL2 a floor newer than the oldest live label is refused "
              "before any verdict; a floor equal to it is PINNED")

        # ---- AC-LFL3: a floor cannot predate its own declaration ----
        # Kept below the oldest live label so this leg exercises only the
        # declaration-order rule and not the floor-ahead rule.
        order = make_world(["2026-10-29 R100 (a logged item)"],
                           declaration=declaration(floor="R50",
                                                   declared_by="R40"))
        worlds.append(order)
        code_order, out_order = run_cli(order)
        check(code_order == 2 and "E_LFL_DECL_ORDER" in out_order,
              "AC-LFL3 a declared round earlier than the floor it declares is "
              "refused (E_LFL_DECL_ORDER)")

        # ---- AC-LFL4: a silent forward bump is DRIFT, both rounds named ----
        # The oldest live label is R200 here, above the effective floor, so
        # this leg exercises only the declaration-mismatch rule.
        bumped = make_world(
            ["2026-10-29 R200 (a logged item)"],
            declaration=declaration(
                floor="R130", declared_by="R140",
                rows=[{"floor": "R100", "declared_by": "R120",
                       "reason": "the only real declaration"}]))
        worlds.append(bumped)
        report = LF.audit(bumped)
        text = LF.render(report)
        code_bump, out_bump = run_cli(bumped)
        drift_ok = (report["verdict"] == "DRIFT"
                    and report["floor"] == 130 and report["declared"] == 100
                    and "forward" in text
                    and "floor=R130" in text and "declared=R100" in text
                    and code_bump == 2 and "DRIFT" in out_bump)
        match = make_world(
            ["2026-10-29 R200 (a logged item)"],
            declaration=declaration(
                floor="R120", declared_by="R140",
                rows=[{"floor": "R100", "declared_by": "R120",
                       "reason": "first"},
                      {"floor": "R120", "declared_by": "R140",
                       "reason": "second, declared"}]))
        worlds.append(match)
        matched = LF.audit(match)
        matched_ok = (matched["verdict"] == "PINNED"
                      and matched["declared"] == 120
                      and matched["declarations"] == 2)
        check(drift_ok and matched_ok,
              "AC-LFL4 a forward bump with no new declaration row is DRIFT "
              "naming both rounds; a declared move is PINNED")

        # ---- AC-LFL5: CLI codes and the byte-stable pinned JSON ----
        clean = make_world(["2026-10-29 R100 (a logged item)"],
                           declaration=declaration())
        worlds.append(clean)
        before = digest_tree(clean)
        code_clean, _ = run_cli(clean)
        code_json, out_a = run_cli(clean, ["--json"])
        _code_b, out_b = run_cli(clean, ["--json"])
        after = digest_tree(clean)
        code_flag, _ = run_cli(clean, ["--nope"])
        broken = make_world([], raw_state="{not json",
                            declaration=declaration())
        worlds.append(broken)
        code_bad, out_bad = run_cli(broken)
        try:
            parsed = json.loads(out_a)
            keys = tuple(parsed.keys())
        except ValueError:
            keys = ()
        byte_stable = (out_a == out_b and out_a.endswith("\n")
                       and not out_a.endswith("\n\n"))
        check(code_clean == 0 and code_json == 0 and code_flag == 2
              and code_bad == 3 and "E_LFL_UNREADABLE" in out_bad
              and keys == LF.REPORT_KEYS and byte_stable and before == after,
              "AC-LFL5 CLI exits 0/0/2/3 as pinned, --json is byte-stable "
              "over the seven keys, and the reading writes nothing")

        # ---- AC-LFL6: purity, no second label law, wiring, live reading ----
        ascii_ok = True
        try:
            with io.open(MODULE, "rb") as handle:
                handle.read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        source = io.open(MODULE, "r", encoding="ascii").read()
        forbidden = ("import socket", "import urllib", "import http",
                     "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        saved = SS.extract_labels
        try:
            SS.extract_labels = lambda state: [500]
            patched = LF.audit(clean)["oldest_label"]
        finally:
            SS.extract_labels = saved
        imported = patched == 500 and "finditer" not in source
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner

        live = LF.audit(REPO)
        live_ok = live["verdict"] in LF.VERDICTS
        print("LIVE %s" % LF.one_line(live), flush=True)
        check(ascii_ok and no_network and imported and wired and live_ok,
              "AC-LFL6 pure ASCII, stdlib only, the label law read through "
              "state_seq, wired as %s(%d), live reading issued"
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