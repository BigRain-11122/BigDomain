"""queue_only_reconcile suite (R2263; criteria AC-QOC1..AC-QOC6 were pinned in
state/queue/tech.md as the R2257 seed row BEFORE this code existed).

What this proves: `state_seq` reports a residue of done-stamped rounds that
carry no log item, but the residue alone cannot tell a round that aged out of
the log window from one that was never logged at all. This suite pins the
split - the stamp and label law is state_seq's (imported, patched to prove it),
the three classes are exhaustive and sum to the stamp count, the floor is
mandatory and explicit, the reader writes nothing and fails closed on
unreadable input, the CLI codes and the byte-stable JSON hold, and the module
is pure ASCII, stdlib only, and wired into the battery.

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

import queue_only_reconcile as QO  # noqa: E402
import state_seq as SS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_only_reconcile.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-only"
WIRED_EXPECT = '"test_queue_only_reconcile.py"), 6),'

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


def make_world(items, tick=1, queue=None, raw_state=None):
    """Build a temp root: src/os/state.json plus an optional state/queue/."""
    world = tempfile.mkdtemp(prefix="bigdomain-qoc-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    target = os.path.join(inner, "state.json")
    if raw_state is None:
        body = json.dumps({"tick": tick, "log": list(items)})
    else:
        body = raw_state
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    if queue is not None:
        qdir = os.path.join(world, "state", "queue")
        os.makedirs(qdir)
        for name, text in queue.items():
            with io.open(os.path.join(qdir, name), "w", encoding="utf-8",
                         newline="\n") as handle:
                handle.write(text)
    return world


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


def stamp_row(round_no):
    return "- [x] [done 2026-10-29 R%d] a delivered row\n" % round_no


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
        # ---- AC-QOC1: the stamp and label law is state_seq's, imported ----
        world = make_world(["2026-10-29 R100 (a logged item)"],
                           queue={"main.md": stamp_row(90) + stamp_row(120)})
        worlds.append(world)
        source = io.open(MODULE, "r", encoding="ascii").read()
        saved_stamps = SS.queue_done_rounds
        saved_labels = SS.extract_labels
        try:
            SS.queue_done_rounds = lambda root: [5, 9]
            SS.extract_labels = lambda state: [5]
            report = QO.audit(world, 1)
            reused = (report["stamps"] == 2 and report["logged"] == 1
                      and report["never_logged_rounds"] == [9])
        finally:
            SS.queue_done_rounds = saved_stamps
            SS.extract_labels = saved_labels
        no_second_regex = ("DONE_STAMP_RE" not in source
                           and "finditer" not in source
                           and "\\[done" not in source)
        check(reused and no_second_regex,
              "AC-QOC1 stamps and labels read through state_seq, no second "
              "implementation")

        # ---- AC-QOC2: three classes, exhaustive, sum to the stamp count ----
        world = make_world(["2026-10-29 R200 (a logged item)",
                            "R200 tokens: local=0 api=0 api_reason=test"],
                           queue={"main.md": (stamp_row(190) + stamp_row(200)
                                             + stamp_row(220))})
        worlds.append(world)
        mixed = QO.audit(world, 195)
        exhaustive = (mixed["stamps"] == 3
                      and mixed["logged"] == 1
                      and mixed["folded"] == 1
                      and mixed["folded_rounds"] == [190]
                      and mixed["never_logged"] == 1
                      and mixed["never_logged_rounds"] == [220]
                      and (mixed["logged"] + mixed["folded"]
                           + mixed["never_logged"]) == mixed["stamps"]
                      and mixed["verdict"] == "RESIDUE")
        deep = QO.audit(world, 250)
        all_folded = (deep["never_logged"] == 0
                      and deep["folded"] == 2
                      and deep["verdict"] == "RECONCILED")
        edge = QO.audit(world, 220)
        at_floor = (edge["never_logged_rounds"] == [220]
                    and edge["folded_rounds"] == [190])
        check(exhaustive and all_folded and at_floor,
              "AC-QOC2 LOGGED/FOLDED/NEVER-LOGGED are exhaustive, sum to the "
              "stamp count, and the floor boundary is at-or-above")

        # ---- AC-QOC3: the floor is mandatory and explicit ----
        refused = []
        for bad in (None, "", "abc", "R", "-3"):
            try:
                QO.parse_floor(bad)
            except QO.QueueOnlyError as exc:
                refused.append(exc.code == "E_QOC_BAD_FLOOR")
        forms = (QO.parse_floor("R95") == 95 and QO.parse_floor("95") == 95
                 and QO.parse_floor(" R007 ") == 7)
        code, out = run_cli(world, [])
        no_floor_cli = (code == 2 and "E_QOC_BAD_FLOOR" in out)
        code_bad, out_bad = run_cli(world, ["--floor", "abc"])
        bad_floor_cli = (code_bad == 2 and "E_QOC_BAD_FLOOR" in out_bad)
        check(len(refused) == 5 and all(refused) and forms
              and no_floor_cli and bad_floor_cli,
              "AC-QOC3 the floor is mandatory, integer-only, and refused "
              "before any read")

        # ---- AC-QOC4: a reading only, and it fails closed ----
        before = digest_tree(world)
        QO.audit(world, 195)
        code, _out = run_cli(world, ["--floor", "195", "--json"])
        after = digest_tree(world)
        zero_writes = before == after

        broken = make_world([], raw_state="{not json")
        worlds.append(broken)
        code_bad, out_bad = run_cli(broken, ["--floor", "195"])
        fails_closed = (code_bad == 3 and "E_QOC_UNREADABLE" in out_bad
                        and "RECONCILED" not in out_bad
                        and "RESIDUE" not in out_bad)

        empty_world = make_world(["2026-10-29 R5 (only item)"])
        worlds.append(empty_world)
        empty = QO.audit(empty_world, 1)
        honest_empty = (empty["stamps"] == 0 and empty["verdict"] == "EMPTY"
                        and empty["max_stamp"] is None)
        check(zero_writes and fails_closed and honest_empty,
              "AC-QOC4 zero writes, unreadable input fails closed, empty "
              "queues read honestly empty")

        # ---- AC-QOC5: CLI codes and the byte-stable JSON ----
        clean = make_world(["2026-10-29 R100 (a logged item)"],
                           queue={"main.md": stamp_row(100)})
        worlds.append(clean)
        code_clean, _ = run_cli(clean, ["--floor", "50"])
        code_residue, _ = run_cli(world, ["--floor", "195"])
        code_flag, _ = run_cli(clean, ["--floor", "50", "--nope"])
        code_json, out_a = run_cli(world, ["--floor", "195", "--json"])
        _code_b, out_b = run_cli(world, ["--floor", "195", "--json"])
        try:
            parsed = json.loads(out_a)
            keys = tuple(parsed.keys())
        except ValueError:
            keys = ()
        byte_stable = (out_a == out_b
                       and out_a.endswith("\n")
                       and not out_a.endswith("\n\n"))
        check(code_clean == 0 and code_residue == 2 and code_flag == 2
              and code_json == 2 and keys == QO.REPORT_KEYS and byte_stable,
              "AC-QOC5 CLI exits 0/2/2/2/3 as pinned and --json carries the "
              "nine pinned keys byte-stably")

        # ---- AC-QOC6: purity, wiring, and the live reading ----
        ascii_ok = True
        try:
            with io.open(MODULE, "rb") as handle:
                handle.read().decode("ascii")
        except (UnicodeDecodeError, IOError):
            ascii_ok = False
        forbidden = ("import socket", "import urllib", "import http",
                     "requests", "urlopen")
        no_network = not any(token in source for token in forbidden)
        runner = io.open(RUNNER, "r", encoding="utf-8").read()
        wired = WIRED_EXPECT in runner and LABEL in runner

        live = QO.audit(REPO, _live_floor())
        live_ok = (live["verdict"] in QO.VERDICTS
                   and (live["logged"] + live["folded"] + live["never_logged"])
                   == live["stamps"])
        print("LIVE %s" % QO.one_line(live), flush=True)
        check(ascii_ok and no_network and wired and live_ok,
              "AC-QOC6 pure ASCII, stdlib only, wired as %s(%d), live reading "
              "reconciled" % (LABEL, EXPECTED_CRITERIA))
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


def _live_floor():
    """The live log window floor: the oldest round the log still carries.

    The residue this module splits only means something against the real log
    window, so the live reading derives its floor from the log itself rather
    than inventing a constant: no labels reads as 1 (nothing has aged out).
    """
    try:
        state = SS.load_state(REPO)
        labels = SS.extract_labels(state)
    except SS.StateSeqError:
        return 1
    return min(labels) if labels else 1


if __name__ == "__main__":
    sys.exit(main())