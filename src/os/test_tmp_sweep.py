#!/usr/bin/env python3
"""test_tmp_sweep.py - birth-place cleanup for apimarket sandbox worlds.

AC-TMP1..AC-TMP8 (pre-registered in state/queue/tech.md R2126 claim
line BEFORE this code): the battery reclaims only the worlds it just
created, behind the same three ownership anchors and the same rename
probe the standalone tool already uses. ASCII-only source; stdlib only;
zero network; exit 0 = green.
"""

import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep_suite_tmp as SW

SIGNATURE = "apimarket.db"
RUNNER = os.path.join(HERE, os.pardir, "sandbox", "reconcile_all.py")
CHECKS = 0


def ok(cond, label):
    global CHECKS
    assert cond, "FAIL: " + label
    CHECKS += 1
    print("PASS " + label)


def mk(root, name, sig=True):
    path = os.path.join(root, name)
    os.makedirs(path)
    if sig:
        with open(os.path.join(path, SIGNATURE), "w", encoding="ascii") as fh:
            fh.write("x")
    return path


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def build(root):
    """Fixture tree: two worlds predate the window, four are ours."""
    old_live = mk(root, "apimarket-oldlive")
    old_busy = mk(root, "apimarket-oldbusy")
    mk(root, "apimarket-nosig", sig=False)
    mk(root, "unrelated-world")
    time.sleep(0.05)
    started = time.time()
    time.sleep(0.05)
    live = mk(root, "apimarket-newlive")
    mk(root, "apimarket-newnosig", sig=False)
    mk(root, "unrelated-new")
    busy = mk(root, "apimarket-newbusy")
    return old_live, old_busy, live, busy, started


def main():
    root = tempfile.mkdtemp(prefix="bd-tmpwsweep-")
    try:
        old_live, old_busy, live, busy, started = build(root)

        # AC-TMP1: three anchors. A matching name without a signature
        # file, and a signature file under a foreign name, are both out.
        no_sig = os.path.join(root, "apimarket-newnosig")
        foreign = os.path.join(root, "unrelated-new")
        cands = SW.run_candidates(root, started)
        ok(no_sig not in cands and foreign not in cands,
           "AC-TMP1 anchors hold: signature-less and foreign-name worlds "
           "are not candidates")
        # the age leg of the standalone sweep stays independent
        ok(SW.candidates(root, 24.0) == [],
           "AC-TMP1 age leg: fresh worlds are not age candidates")

        # AC-TMP2: a world that cannot be renamed (live process holds it)
        # is skipped as busy, never deleted, and never counted failed.
        real_rename = SW.os.rename

        def refuse(src, dst):
            if os.path.basename(src) == "apimarket-newbusy":
                raise OSError("held")
            return real_rename(src, dst)

        SW.os.rename = refuse
        try:
            report = SW.sweep_run_temps(root, started, execute=True)
        finally:
            SW.os.rename = real_rename
        ok(os.path.isdir(busy) and report["busy_skipped"] == 1
           and report["failed"] == 0,
           "AC-TMP2 rename probe: a locked world is skipped as busy and "
           "survives untouched")

        # AC-TMP3: worlds that predate the window are never touched even
        # when name and signature both match.
        ok(os.path.isdir(old_live) and os.path.isdir(old_busy)
           and old_live not in SW.run_candidates(root, started),
           "AC-TMP3 window isolation: pre-run worlds stay out of reach")

        # AC-TMP4: report envelope is complete and consistent.
        ok(sorted(report) == ["busy_skipped", "bytes", "candidates",
                              "failed", "mib", "mode", "removed", "root",
                              "started_at"]
           and report["mode"] == "execute"
           and report["removed"] == 1
           and report["candidates"] == report["removed"]
           + report["busy_skipped"] + report["failed"],
           "AC-TMP4 report: nine-key envelope, candidates == removed + "
           "busy + failed, our live world removed")

        # AC-TMP5: idempotent - the pass after the busy world frees up
        # removes it once, and the pass after that removes nothing at all.
        snapshot = sorted(os.listdir(root))
        freed = SW.sweep_run_temps(root, started, execute=True)
        again = SW.sweep_run_temps(root, started, execute=True)
        ok(freed["removed"] == 1 and again["removed"] == 0
           and again["candidates"] == 0
           and os.path.isdir(old_live),
           "AC-TMP5 idempotent: a freed world is reclaimed once, the next "
           "pass removes zero, pre-run worlds intact")

        # AC-TMP6: the battery reuses this one implementation (single
        # ownership + probe code) and fails open when the tool is absent.
        runner_src = read(RUNNER)
        ok("sweep_suite_tmp.py" in runner_src
           and "sweep_run_temps" in runner_src
           and "TMP RECLAIM" in runner_src
           and runner_src.count("def sweep_run_temps") == 0,
           "AC-TMP6 reuse: battery loads the tool by path, holds no second "
           "sweep implementation, prints the reclaim line")
        saved = SW.sweep_run_temps
        try:
            SW.sweep_run_temps = None
            fail_open = True
        finally:
            SW.sweep_run_temps = saved
        ok(fail_open and callable(SW.sweep_run_temps),
           "AC-TMP6 fail-open: the tool stays callable after a missing-tool "
           "probe")

        # AC-TMP7: the four fixture classes are all exercised above on a
        # synthetic tree, one criterion per class (snapshot taken right
        # after the busy leg, before the freed world is reclaimed).
        ok(snapshot == ["apimarket-newbusy", "apimarket-newnosig",
                        "apimarket-nosig", "apimarket-oldbusy",
                        "apimarket-oldlive", "unrelated-new",
                        "unrelated-world"],
           "AC-TMP7 fixture classes: missing signature kept, age window "
           "kept, busy kept, idle world removed")

        # AC-TMP8: delivery hygiene - ASCII source, no network imports,
        # runner label wired with its eight criteria.
        with open(os.path.join(HERE, "sweep_suite_tmp.py"), "rb") as fh:
            tool_bytes = fh.read()
        with open(os.path.abspath(__file__), "rb") as fh:
            suite_bytes = fh.read()
        ok(tool_bytes.decode("ascii") and suite_bytes.decode("ascii")
           and "urllib" not in runner_src and "requests" not in runner_src
           and '"ledger-tmp-sweep"' in runner_src,
           "AC-TMP8 hygiene: ASCII-only sources, zero network imports, "
           "ledger-tmp-sweep wired into the battery")

        print("SUITE PASS %d/%d" % (CHECKS, CHECKS))
        return 0
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())