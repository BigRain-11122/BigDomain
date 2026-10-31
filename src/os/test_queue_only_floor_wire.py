"""queue_only_floor_wire suite (R2269; criteria AC-QFW1..AC-QFW6 were pinned
in state/queue/tech.md as the R2266 seed row BEFORE this code existed).

What this proves: R2265 pinned the log-window floor in state/log_floor.json and
R2266 shipped the resolver that knows it, but the splitter still took its floor
as a caller literal - so the declaration could read PINNED while every actual
split used another number. This suite pins the wiring that closes the seam at
the source: the floor comes from the resolver and is never re-derived from the
log, a declaration that is not PINNED refuses the split instead of defaulting,
an explicit --floor plus --floor-from-declaration is refused as two sources of
truth, and for the same resolved floor the classification is unchanged.

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

import queue_floor_decl as QFD  # noqa: E402
import queue_only_reconcile as QOR  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_only_reconcile.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-only-floor-wire"
WIRED_EXPECT = '"test_queue_only_floor_wire.py"), 6),'

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
    if rows is None:
        rows = [{"floor": floor, "declared_by": declared_by,
                 "reason": "first explicit declaration"}]
    return {"floor": floor, "declared_by": declared_by,
            "reason": "declared so it can only move through a new row",
            "declarations": rows}


def make_world(items=None, stamp_rows=None, declaration_body=None,
               raw_declaration=None):
    """A temp root: src/os/state.json, state/queue/*.md, state/log_floor.json."""
    if items is None:
        items = [
            "2026-10-30 R100 (a logged item)",
            "2026-10-30 R101 (a logged item)",
        ]
    if stamp_rows is None:
        stamp_rows = [
            "- [x] [done 2026-10-30 R100] landed",
            "- [x] [done 2026-10-30 R101] landed",
            "- [x] [done 2026-10-30 R099] aged out below the floor",
        ]
    world = tempfile.mkdtemp(prefix="bigdomain-qfw-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    with io.open(os.path.join(inner, "state.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"tick": 101, "log": list(items)}))
    qdir = os.path.join(world, "state", "queue")
    os.makedirs(qdir)
    with io.open(os.path.join(qdir, "tech.md"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(stamp_rows) + "\n")
    payload = (raw_declaration if raw_declaration is not None
               else json.dumps(declaration_body if declaration_body is not None
                               else declaration()))
    with io.open(os.path.join(world, "state", "log_floor.json"), "w",
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
    cmd = [sys.executable, MODULE, "--check", "--root", root]
    if extra:
        cmd.extend(extra)
    proc = subprocess.run(cmd, capture_output=True, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    worlds = []
    try:
        # ---- AC-QFW1: the floor comes from the resolver, not the log ----
        world = make_world()
        worlds.append(world)
        saved = QFD.resolve
        try:
            QFD.resolve = lambda root, caller_floor=None: {
                "floor": 1000, "declared": 1000, "declared_by": 1200,
                "caller": None, "oldest_label": 900, "declarations": 1,
                "verdict": "AGREES"}
            patched = QOR.declared_floor(world)
        finally:
            QFD.resolve = saved
        source = io.open(MODULE, "r", encoding="ascii").read()
        imported = ("queue_floor_decl.resolve(" in source
                    and "min(" not in source.split("def audit")[0]
                    and "smallest" not in source)
        real = QOR.declared_floor(world)
        check(patched == 1000 and real == 100 and imported,
              "AC-QFW1 the declared floor is obtained through "
              "queue_floor_decl.resolve (a patched verdict flows through) and "
              "is never re-derived from the log")

        # ---- AC-QFW2: a declaration that is not PINNED refuses the split ----
        # An honest UNPINNED is a missing declaration file (an unparseable one
        # is a different refusal, pinned by AC-QFW5 at exit 3).
        unpinned = make_world()
        worlds.append(unpinned)
        os.remove(os.path.join(unpinned, "state", "log_floor.json"))
        code_unpinned, out_unpinned = run_cli(unpinned,
                                             ["--floor-from-declaration"])
        drift = make_world(declaration_body=declaration(
            floor="R100", declared_by="R120",
            rows=[{"floor": "R050", "declared_by": "R120",
                   "reason": "moved without a row"}]))
        worlds.append(drift)
        code_drift, out_drift = run_cli(drift, ["--floor-from-declaration"])
        check(code_unpinned == 2 and code_drift == 2
              and "E_QFW_NOT_PINNED" in out_unpinned
              and "E_QFW_NOT_PINNED" in out_drift
              and "QUEUE ONLY" not in out_unpinned
              and "QUEUE ONLY" not in out_drift,
              "AC-QFW2 an UNPINNED or DRIFT declaration refuses the split "
              "with exit 2 and no counts, never a default floor")

        # ---- AC-QFW3: one source of truth, and at least one ----
        code_both, out_both = run_cli(
            world, ["--floor", "R100", "--floor-from-declaration"])
        code_none, out_none = run_cli(world, [])
        check(code_both == 2 and code_none == 2
              and "E_QFW_BOTH" in out_both
              and "--floor" in out_both and "--floor-from-declaration" in out_both
              and "E_QOC_BAD_FLOOR" in out_none,
              "AC-QFW3 --floor with --floor-from-declaration is refused "
              "naming both, and neither is refused so no silent derived floor "
              "survives")

        # ---- AC-QFW4: same floor, byte-identical classification ----
        code_lit, out_lit = run_cli(world, ["--floor", "R100", "--json"])
        code_decl, out_decl = run_cli(world,
                                      ["--floor-from-declaration", "--json"])
        report = json.loads(out_decl)
        check(out_lit == out_decl and code_lit == code_decl == 0
              and report["floor"] == 100 and report["logged"] == 2
              and report["folded"] == 1 and report["never_logged"] == 0
              and report["verdict"] == "RECONCILED",
              "AC-QFW4 the declared floor and the same literal floor produce "
              "byte-identical LOGGED/FOLDED/NEVER-LOGGED counts")

        # ---- AC-QFW5: CLI codes, byte-stable pinned JSON, pure read ----
        before = digest_tree(world)
        code_a, out_a = run_cli(world, ["--floor-from-declaration", "--json"])
        code_b, out_b = run_cli(world, ["--floor-from-declaration", "--json"])
        after = digest_tree(world)
        residue = make_world(stamp_rows=[
            "- [x] [done 2026-10-30 R100] landed",
            "- [x] [done 2026-10-30 R150] never logged",
        ])
        worlds.append(residue)
        code_residue, _out_residue = run_cli(residue,
                                             ["--floor-from-declaration"])
        bad = make_world(raw_declaration="{not json")
        worlds.append(bad)
        code_bad, out_bad = run_cli(bad, ["--floor-from-declaration"])
        code_flag, _ = run_cli(world, ["--nope"])
        keys = tuple(json.loads(out_a).keys())
        check(code_a == 0 and code_b == 0 and out_a == out_b
              and keys == QOR.REPORT_KEYS and before == after
              and code_residue == 2 and code_bad == 3
              and "E_QFW_UNREADABLE" in out_bad and code_flag == 2,
              "AC-QFW5 CLI exits 0/2/3 as pinned, --json is byte-stable over "
              "the nine report keys, and the split writes nothing")

        # ---- AC-QFW6: purity, wiring, live reading ----
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
        live = QOR.audit(REPO, QOR.declared_floor(REPO))
        print("LIVE %s" % QOR.one_line(live), flush=True)
        check(ascii_ok and no_network and wired
              and live["verdict"] in QOR.VERDICTS,
              "AC-QFW6 pure ASCII, stdlib only, zero network, wired as "
              "%s(%d), live reading taken through the declared floor"
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