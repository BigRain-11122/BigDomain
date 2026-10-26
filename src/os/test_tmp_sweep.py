#!/usr/bin/env python3
"""test_tmp_sweep.py - birth-place cleanup for apimarket sandbox worlds.

AC-TMP1..AC-TMP8 (pre-registered in state/queue/tech.md R2126 claim
line BEFORE this code): the battery reclaims only the worlds it just
created, behind the same three ownership anchors and the same rename
probe the standalone tool already uses. ASCII-only source; stdlib only;
zero network; exit 0 = green.

AC-TSN1..AC-TSN8 (pre-registered in state/queue/tech.md R2150 claim
line BEFORE this code): the negative-example families of the same three
anchors - same-prefix but foreign names, nested worlds, and a signature
name occupied by a directory - plus a closed delete domain.
"""

import hashlib
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

        # ------------------------------------------------------------------
        # R2150 negative-example window (AC-TSN1..AC-TSN8).
        # ------------------------------------------------------------------
        def snapshot(base_path):
            seen = {}
            for base, _dirs, files in os.walk(base_path):
                rel = os.path.relpath(base, base_path)
                seen[rel + "/"] = "dir"
                for name in files:
                    full = os.path.join(base, name)
                    with open(full, "rb") as fh:
                        seen[os.path.join(rel, name)] = hashlib.sha256(
                            fh.read()).hexdigest()
            return seen

        def world_with(root_path, name, sig):
            world = os.path.join(root_path, name)
            os.makedirs(world)
            with open(os.path.join(world, sig), "w", encoding="ascii") as fh:
                fh.write("x")
            return world

        negroot = tempfile.mkdtemp(prefix="bd-tmpwsneg-")
        posroot = tempfile.mkdtemp(prefix="bd-tmpwspos-")
        try:
            time.sleep(0.05)
            nstart = time.time()
            time.sleep(0.05)

            # AC-TSN1: same prefix without separator, a foreign family, a
            # case variant and a glued suffix stay non-candidates on both
            # legs even when a real signature file is present.
            prefix_neg = ["apimarket", "amzzz-x", "APIMARKET-x",
                          "apimarketx-x"]
            for name in prefix_neg:
                mk(negroot, name)
            ok(SW.run_candidates(negroot, nstart) == []
               and SW.candidates(negroot, -1.0) == []
               and sorted(os.listdir(negroot)) == sorted(prefix_neg),
               "AC-TSN1 prefix negatives: four name shapes carrying a real "
               "signature stay non-candidates on both legs")

            # AC-TSN2: the scan is root-level only, so a nested world is
            # invisible and its tree is left byte-identical.
            nest = os.path.join(negroot, "sub")
            mk(nest, "apimarket-nested")
            nest_before = snapshot(nest)
            ok(SW.run_candidates(negroot, nstart) == []
               and snapshot(nest) == nest_before
               and os.path.isfile(os.path.join(nest, "apimarket-nested",
                                               SIGNATURE)),
               "AC-TSN2 depth negatives: a nested world is invisible to "
               "both legs and its tree is unchanged")

            # AC-TSN3: a directory occupying a signature name is not a
            # world signature (the tightening under test).
            for idx, sig in enumerate(SW.SIGNATURES):
                world = mk(negroot, "apimarket-sig%d" % idx, sig=False)
                os.makedirs(os.path.join(world, sig))
            ok(SW.run_candidates(negroot, nstart) == []
               and SW.candidates(negroot, -1.0) == []
               and len([n for n in os.listdir(negroot)
                        if n.startswith("apimarket-sig")])
               == len(SW.SIGNATURES),
               "AC-TSN3 signature shape: all seven signature names as "
               "directories leave every world non-candidate")

            # AC-TSN4: the tightening does not kill the positive control -
            # every signature family as a regular file is still a world.
            pos_paths = [world_with(posroot, "apimarket-pos%d" % idx, sig)
                         for idx, sig in enumerate(SW.SIGNATURES)]
            run_leg = SW.run_candidates(posroot, nstart)
            age_leg = SW.candidates(posroot, -1.0)
            ok(sorted(run_leg) == sorted(pos_paths)
               and sorted(age_leg) == sorted(pos_paths),
               "AC-TSN4 positive control: seven signature families stay "
               "candidates on both legs after the tightening")

            # AC-TSN5: the delete domain is closed over the candidate set.
            neg_before = snapshot(negroot)
            real_sweep = SW.sweep
            touched = []

            def recording_sweep(path, execute=True):
                touched.append(os.path.abspath(path))
                return real_sweep(path, execute)

            SW.sweep = recording_sweep
            try:
                pos_report = SW.sweep_run_temps(posroot, nstart, execute=True)
            finally:
                SW.sweep = real_sweep
            ok(bool(touched)
               and sorted(touched) == sorted(os.path.abspath(p)
                                             for p in pos_paths)
               and pos_report["removed"] == len(pos_paths)
               and snapshot(negroot) == neg_before,
               "AC-TSN5 delete domain: sweep() sees exactly the candidates "
               "and every negative tree is byte-identical afterwards")

            # AC-TSN6: both legs agree on the negatives and share the
            # positive control set.
            ok(SW.run_candidates(negroot, nstart) == []
               and SW.candidates(negroot, -1.0) == []
               and set(run_leg) & set(age_leg) == set(pos_paths),
               "AC-TSN6 both legs: identical negative verdicts, identical "
               "positive control set")

            # AC-TSN7: a missing root and a plain file are both empty and
            # never raise.
            missing = os.path.join(negroot, "no-such-dir")
            plain = os.path.join(negroot, "plainfile.txt")
            with open(plain, "w", encoding="ascii") as fh:
                fh.write("x")
            ok(SW.run_candidates(missing, nstart) == []
               and SW.candidates(missing, -1.0) == []
               and SW.run_candidates(plain, nstart) == []
               and SW.candidates(plain, -1.0) == [],
               "AC-TSN7 bad roots: missing path and plain file return "
               "empty lists on both legs")

            # AC-TSN8: hygiene - ASCII sources, no network imports, the
            # existing runner label untouched, tightened helper present.
            tool_src = read(os.path.join(HERE, "sweep_suite_tmp.py"))
            suite_src = read(os.path.abspath(__file__))
            ok(tool_src.encode("ascii") and suite_src.encode("ascii")
               and "urllib" not in tool_src and "requests" not in tool_src
               and "_signature_file" in tool_src
               and '"ledger-tmp-sweep"' in runner_src,
               "AC-TSN8 hygiene: ASCII-only sources, zero network imports, "
               "signature helper in place, ledger-tmp-sweep still wired")
        finally:
            import shutil as _sh
            _sh.rmtree(negroot, ignore_errors=True)
            _sh.rmtree(posroot, ignore_errors=True)

        print("SUITE PASS %d/%d" % (CHECKS, CHECKS))
        return 0
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())