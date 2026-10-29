"""queue_floor_decl suite (R2266; criteria AC-FDL1..AC-FDL6 were pinned in
state/queue/tech.md as the R2265 seed row BEFORE this code existed).

What this proves: R2265 made the queue-only floor a dated declaration, but
nothing consumed it - `queue_only_reconcile --floor R<n>` still takes a caller
literal, so the pinned file could read PINNED while every split used another
number. This suite pins the resolver: the verdict is log_floor's (imported, not
re-derived), a refusal hands back no floor and carries its own code, a supplied
floor is compared rather than trusted, the reading writes nothing and reads no
clock, the CLI codes and the byte-stable JSON, and the module's purity, wiring
and live reading.

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
import queue_floor_decl as QFD  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_floor_decl.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-floor-decl"
WIRED_EXPECT = '"test_queue_floor_decl.py"), 6),'

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


def declaration(floor="R100", declared_by="R120", rows=None):
    """One pinned declaration body with a single recorded row by default."""
    if rows is None:
        rows = [{"floor": floor, "declared_by": declared_by,
                 "reason": "first explicit declaration"}]
    return {"floor": floor, "declared_by": declared_by,
            "reason": "declared so it can only move through a new row",
            "declarations": rows}


def make_world(items, declaration_body=None, raw_state=None,
               raw_declaration=None):
    """Build a temp root: src/os/state.json plus state/log_floor.json."""
    world = tempfile.mkdtemp(prefix="bigdomain-fdl-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    body = (raw_state if raw_state is not None
            else json.dumps({"tick": 1, "log": list(items)}))
    with io.open(os.path.join(inner, "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    sdir = os.path.join(world, "state")
    os.makedirs(sdir)
    payload = (raw_declaration if raw_declaration is not None
               else json.dumps(declaration_body if declaration_body is not None
                               else declaration()))
    with io.open(os.path.join(sdir, "log_floor.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(root):
    """Digest every file under root so a read that writes is visible."""
    digest = hashlib.sha256()
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, root).encode("utf-8"))
            with io.open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def run_cli(root, extra=None):
    cmd = [sys.executable, MODULE, "--check", "--root", root]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def raises(func):
    """Return the error code of a refusal, or None when it did not refuse."""
    try:
        result = func()
    except QFD.FloorDeclError as exc:
        return exc.code
    except Exception as exc:  # noqa: BLE001 - disclosed: any other raise counts
        return "UNEXPECTED:%s" % type(exc).__name__
    return "RETURNED:%r" % (result,)


def main():
    worlds = []
    try:
        # ---- AC-FDL1: the verdict is log_floor's, imported ----
        world = make_world(["2026-10-29 R100 (a logged item)"])
        worlds.append(world)
        saved_audit = LF.audit
        try:
            LF.audit = lambda root: {
                "floor": 1000, "declared": 1000, "declared_by": 1200,
                "reason": "sentinel", "oldest_label": 900,
                "declarations": 1, "verdict": "PINNED"}
            sentinel = QFD.resolve(world)
        finally:
            LF.audit = saved_audit
        source = io.open(MODULE, "r", encoding="ascii").read()
        imported = (sentinel["floor"] == 1000
                    and sentinel["declared_by"] == 1200
                    and "log_floor.audit(" in source
                    and "def shape(" not in source
                    and 'declarations"][' not in source)
        real = QFD.resolve(world)
        check(imported and real["floor"] == 100,
              "AC-FDL1 the floor comes from log_floor.audit (a patched verdict "
              "flows straight through) and the shape is never re-derived")

        # ---- AC-FDL2: a refusal yields no floor, each with its own code ----
        codes = []
        try:
            LF.audit = lambda root: {
                "floor": None, "declared": None, "declared_by": None,
                "reason": "no state/log_floor.json", "oldest_label": None,
                "declarations": 0, "verdict": "UNPINNED"}
            codes.append(raises(lambda: QFD.resolve(world)))
            LF.audit = lambda root: {
                "floor": 130, "declared": 100, "declared_by": 140,
                "reason": "drift", "oldest_label": 200,
                "declarations": 2, "verdict": "DRIFT"}

            def boom(root):
                raise LF.LogFloorError("E_LFL_FLOOR_AHEAD", "floor=R300")
            codes.append(raises(lambda: QFD.resolve(world)))
            LF.audit = boom
            codes.append(raises(lambda: QFD.resolve(world)))

            def unreadable(root):
                raise LF.LogFloorError("E_LFL_UNREADABLE", "not JSON")
            LF.audit = unreadable
            codes.append(raises(lambda: QFD.resolve(world)))
        finally:
            LF.audit = saved_audit
        check(codes == ["E_FDL_UNPINNED", "E_FDL_DRIFT", "E_FDL_REFUSED",
                        "E_FDL_UNREADABLE"],
              "AC-FDL2 UNPINNED, DRIFT, a consistency refusal and unreadable "
              "input each refuse with their own code and hand back no floor")

        # ---- AC-FDL3: a supplied floor is compared, not trusted ----
        agree = QFD.resolve(world, "R100")
        agree_numeric = QFD.resolve(world, "100")
        differ = QFD.resolve(world, "R150")
        text = QFD.render(differ)
        check(agree["verdict"] == "AGREES"
              and agree_numeric["verdict"] == "AGREES"
              and differ["verdict"] == "DISAGREES"
              and differ["caller"] == 150 and differ["floor"] == 100
              and "caller=R150" in text and "declared=R100" in text,
              "AC-FDL3 a caller floor equal to the declared one reads AGREES, "
              "a different one reads DISAGREES naming both rounds")

        # ---- AC-FDL4: writes nothing, reads no clock ----
        before = digest_tree(world)
        QFD.resolve(world)
        QFD.resolve(world, "R100")
        after = digest_tree(world)
        no_clock = ("import time" not in source
                    and "import datetime" not in source
                    and "time.time" not in source
                    and "date.today" not in source)
        repo_before = digest_tree(os.path.join(REPO, "state"))
        QFD.resolve(REPO)
        repo_after = digest_tree(os.path.join(REPO, "state"))
        check(before == after and repo_before == repo_after and no_clock,
              "AC-FDL4 the resolver writes nothing (both the temp world and "
              "the live state/ tree digest identically) and reads no clock")

        # ---- AC-FDL5: CLI codes and the byte-stable pinned JSON ----
        code_clean, _ = run_cli(world)
        code_equal, _ = run_cli(world, ["--floor", "R100"])
        code_diff, out_diff = run_cli(world, ["--floor", "R150"])
        code_flag, _ = run_cli(world, ["--nope"])
        code_json, out_a = run_cli(world, ["--json"])
        _code_b, out_b = run_cli(world, ["--json"])
        unpinned = make_world(["2026-10-29 R100 (a logged item)"],
                              raw_declaration="{not json")
        worlds.append(unpinned)
        code_bad, out_bad = run_cli(unpinned)
        try:
            keys = tuple(json.loads(out_a).keys())
        except ValueError:
            keys = ()
        byte_stable = (out_a == out_b and out_a.endswith("\n")
                       and not out_a.endswith("\n\n"))
        check(code_clean == 0 and code_equal == 0 and code_diff == 2
              and code_flag == 2 and code_json == 0 and code_bad == 3
              and "E_FDL_UNREADABLE" in out_bad and "DISAGREES" in out_diff
              and keys == QFD.REPORT_KEYS and byte_stable,
              "AC-FDL5 CLI exits 0/0/2/2/0/3 as pinned, --json is byte-stable "
              "over the seven keys")

        # ---- AC-FDL6: purity, wiring and the live reading ----
        ascii_ok = True
        try:
            io.open(MODULE, "rb").read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner
        live = QFD.resolve(REPO)
        print("LIVE %s" % QFD.one_line(live), flush=True)
        live_ok = live["verdict"] in QFD.VERDICTS
        check(ascii_ok and no_network and wired and live_ok,
              "AC-FDL6 pure ASCII, stdlib only, zero network, wired as "
              "%s(%d), live reading issued" % (LABEL, EXPECTED_CRITERIA))
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