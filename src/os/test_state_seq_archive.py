"""state_seq archive-fold suite (R2586; criteria AC-SEQAF1..AC-SEQAF6 were
pinned in state/queue/tech.md as the R2586 seed row BEFORE this code).

What this proves: `state_seq` decides "stamped but never logged", but a fold
moves a round's log items out of the live log and into
`logs/state-log-archive-*.md`. A folded round was logged, so it must not read
as residue for ever - the R2586 battery measured exactly that on R2575 and the
residue reader handed it back as untriaged, failing AC-RTR6.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

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

import state_seq as SS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "state_seq.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-seq-archive"

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


def make_world(items, tick=1, queue=None, archive=None, archive_name=None):
    """Temp root: src/os/state.json, optional state/queue/ and logs/archive."""
    world = tempfile.mkdtemp(prefix="bigdomain-seqaf-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    body = json.dumps({"tick": tick, "log": list(items)})
    with io.open(os.path.join(inner, "state.json"), "w", encoding="utf-8",
                 newline="\n") as handle:
        handle.write(body)
    if queue is not None:
        qdir = os.path.join(world, "state", "queue")
        os.makedirs(qdir)
        for name, text in queue.items():
            with io.open(os.path.join(qdir, name), "w", encoding="utf-8",
                         newline="\n") as handle:
                handle.write(text)
    if archive is not None:
        ldir = os.path.join(world, "logs")
        os.makedirs(ldir)
        name = archive_name or "state-log-archive-2026-11.md"
        path = os.path.join(ldir, name)
        if archive is True:
            os.makedirs(path)
        else:
            with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(archive)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


DONE = "- [x] [done 2026-11-08 R%d] a closed row\n"


def ac_seqaf1():
    """Archived labels use the SAME owning-label law as the live log."""
    world = make_world(
        ["R2576 live item"],
        archive=("2026-11-08 R2575 PRODUCT window on the debt gate head, and "
                 "the body mentions the R2168 mixed-tree rule\n"))
    try:
        labels = SS.archived_labels(world)
        ok = 2575 in labels and 2168 not in labels and labels.count(2575) == 1
        print("  measured: archived=%r" % (labels,), flush=True)
        check(ok, "AC-SEQAF1 archive labels read through the owning-label law")
    finally:
        drop_world(world)


def ac_seqaf2():
    """A folded round whose queue row closed is no longer queue_only."""
    live = ["R2576 live item"]
    archive = "2026-11-08 R2575 PRODUCT window, complete block\n"
    folded = make_world(live, queue={"tech.md": DONE % 2575}, archive=archive)
    plain = make_world(live, queue={"tech.md": DONE % 2575})
    try:
        a = SS.audit(folded)
        b = SS.audit(plain)
        ok = (2575 not in a["queue_only"] and 2575 in b["queue_only"]
              and a["verdict"] == b["verdict"] == "SEQUENCE-OK")
        print("  measured: folded=%r plain=%r verdict=%s/%s"
              % (a["queue_only"], b["queue_only"], a["verdict"], b["verdict"]),
              flush=True)
        check(ok, "AC-SEQAF2 a folded round is no longer stamped-never-logged")
    finally:
        drop_world(folded)
        drop_world(plain)


def ac_seqaf3():
    """A round with no log item anywhere is STILL queue_only."""
    world = make_world(
        ["R2576 live item"],
        queue={"tech.md": DONE % 2576 + DONE % 2165},
        archive="2026-11-08 R2575 PRODUCT window, complete block\n")
    try:
        report = SS.audit(world)
        ok = 2165 in report["queue_only"] and 2576 not in report["queue_only"]
        print("  measured: queue_only=%r" % (report["queue_only"],),
              flush=True)
        check(ok, "AC-SEQAF3 unlogged-anywhere round still reads queue_only")
    finally:
        drop_world(world)


def ac_seqaf4():
    """The sequence checks still read the LIVE log; an archive changes none."""
    broken = ["R900 a", "R902 b", "R900 c", "R903 d"]
    world_plain = make_world(broken, queue={"tech.md": DONE % 900})
    world_arch = make_world(broken, queue={"tech.md": DONE % 900},
                            archive="R905 archived\nR906 archived\n")
    try:
        a = SS.audit(world_plain)
        b = SS.audit(world_arch)
        ok = (a["gaps"] == b["gaps"] and a["repeats"] == b["repeats"]
              and a["backwards"] == b["backwards"]
              and a["verdict"] == b["verdict"] == "SEQUENCE-BROKEN"
              and b["repeats"] and b["gaps"] and b["backwards"])
        print("  measured: gaps=%r repeats=%d backwards=%r verdict=%s"
              % (b["gaps"], len(b["repeats"]), b["backwards"], b["verdict"]),
              flush=True)
        check(ok, "AC-SEQAF4 sequence checks still read the live log alone")
    finally:
        drop_world(world_plain)
        drop_world(world_arch)


def ac_seqaf5():
    """No logs/ reads zero labels; an unreadable archive fails closed."""
    world = make_world(["R2576 live item"], queue={"tech.md": DONE % 2575})
    broken = make_world(["R2576 live item"], queue={"tech.md": DONE % 2575},
                        archive=True)
    try:
        empty = SS.archived_labels(world)
        report = SS.audit(world)
        quiet = empty == [] and report["queue_only"] == [2575]
        code = None
        detail = ""
        try:
            SS.archived_labels(broken)
        except SS.StateSeqError as exc:
            code = exc.code
            detail = exc.detail
        ok = quiet and code == "E_SEQAF_BAD_ARCHIVE" and detail
        print("  measured: empty=%r quiet=%r code=%r named=%r"
              % (empty, quiet, code, bool(detail)), flush=True)
        check(ok, "AC-SEQAF5 missing dir is zero, unreadable file fails closed")
    finally:
        drop_world(world)
        drop_world(broken)


def ac_seqaf6():
    """Purity, wiring, and a live reading whose residue verdict is measured."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    no_clock = ("import time" not in source and "datetime" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) and ("test_state_seq_archive.py" in
                                            runner)
    listed = set(SS.archived_labels(REPO))
    live = SS.audit(REPO)
    unlogged = [number for number in live["queue_only"]
                if number not in listed]
    consistent = unlogged == list(live["queue_only"])
    ok = (ascii_only and no_net and no_clock and wired and bool(listed)
          and 2575 in listed and consistent)
    if not ok:
        print("  measured: ascii=%r net=%r clock=%r wired=%r listed=%d "
              "queue_only=%r" % (ascii_only, no_net, no_clock, wired,
                                 len(listed), live["queue_only"]),
              flush=True)
    check(ok, "AC-SEQAF6 pure, wired, and the live residue is measured")


def main():
    print("state_seq archive-fold suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    for face in (ac_seqaf1, ac_seqaf2, ac_seqaf3, ac_seqaf4, ac_seqaf5,
                 ac_seqaf6):
        face()
    passed = 0
    total = 0
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES,
             EXPECTED_CRITERIA), flush=True)
    return 0 if FAILS == 0 and PASSES == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())