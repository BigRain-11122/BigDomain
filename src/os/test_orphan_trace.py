"""orphan_trace suite (R2323; criteria AC-OTR1..AC-OTR6 were pre-registered
inside the R2302 seed row of state/queue/tech.md:379 BEFORE this code
existed).

What this proves: ORPHAN stops being a dead end. The orphan list, the round and
the leg-to-round pairing are asked of evidence_variants (never re-derived), so
patching that reading moves this reader; every leg carrying a RUNNER line is
named with its own runner token, its own VERDICT token and its digest, and the
standing-in leg is the first such leg in NAME order rather than an arbitrary
pick; a round whose legs carry no runner line reads NO-TRACE; an empty orphan
list reads NO-ORPHAN at exit 0; and a leg that cannot be decoded refuses the
whole reading instead of being counted as an empty leg.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
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

import evidence_variants as EV  # noqa: E402
import orphan_trace as OT  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "orphan_trace.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-orphan-trace"

GREEN = "RUNNER PASS 340/340 suites green\nSECTION matrix PASS\nVERDICT PASS\n"
NO_VERDICT = "RUNNER FAIL (2 failed assertions)\n"
SILENT = "SUITE PASS 6/6\n"

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


def make_world(files):
    """A temp root with one qa directory; a bytes body is written verbatim."""
    world = tempfile.mkdtemp(prefix="bigdomain-otr-")
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name, body in files:
        target = os.path.join(qa, name)
        if isinstance(body, bytes):
            with io.open(target, "wb") as handle:
                handle.write(body)
            continue
        with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return world


def tree_digest(world):
    """Every file under the world with size and digest, plus directories."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(dirs):
            rel = os.path.relpath(os.path.join(root, name), world)
            out.append("D:%s" % rel)
        for name in sorted(files):
            path = os.path.join(root, name)
            with io.open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()[:16]
            rel = os.path.relpath(path, world)
            out.append("%s:%d:%s" % (rel, os.path.getsize(path), digest))
    return "|".join(sorted(out))


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_cli(world, extra=()):
    argv = [sys.executable, MODULE, "--trace", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_otr1():
    """AC-OTR1: orphans, rounds and leg pairing come from evidence_variants."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_scan = ("listdir" not in source and "os.walk" not in source
                      and "glob" not in source)
    world = make_world([("reconcile-all-R1500b.log", GREEN)])
    synthetic = {
        "dir": "qa",
        "variants": [
            {"name": "reconcile-all-R1700a.log", "round": "R1700",
             "suffix": "a", "canonical": "reconcile-all-R1700.log",
             "kind": "other", "status": "ORPHAN", "digest": "0" * 64,
             "canonical_digest": None},
            {"name": "reconcile-all-R1700b.log", "round": "R1700",
             "suffix": "b", "canonical": "reconcile-all-R1700.log",
             "kind": "other", "status": "ORPHAN", "digest": "1" * 64,
             "canonical_digest": None},
            {"name": "reconcile-all-R1800-2.log", "round": "R1800",
             "suffix": "-2", "canonical": "reconcile-all-R1800.log",
             "kind": "other", "status": "DISTINCT", "digest": "2" * 64,
             "canonical_digest": "3" * 64},
        ],
        "counts": {"variants": 3, "duplicate": 0, "distinct": 1,
                   "orphan": 2, "retry": 0},
        "verdict": "UNRESOLVED",
    }
    saved = EV.variants
    try:
        live = OT.traces(world)
        EV.variants = lambda root, directory="qa": synthetic
        # Two of the synthetic legs do not exist on disk, so the reading must
        # refuse rather than invent an empty leg - which is itself proof that
        # the pairing came from EV and not from a scan of this directory.
        refused = None
        try:
            OT.traces(world)
        except OT.OrphanTraceError as exc:
            refused = exc.code
        EV.variants = lambda root, directory="qa": {
            "dir": "qa", "variants": [], "counts": {},
            "verdict": "RESOLVED"}
        patched = OT.traces(world)
        ok = (no_second_scan
              and live["counts"]["rounds"] == 1
              and live["rounds"][0]["round"] == "R1500"
              and refused in (OT.E_OTR_UNREADABLE, OT.E_OTR_UNDECODABLE)
              and patched["counts"]["rounds"] == 0
              and patched["verdict"] == "NO-ORPHAN")
        if not ok:
            print("  measured: no_second_scan=%r live=%r refused=%r "
                  "patched=%r" % (no_second_scan, live, refused, patched),
                  flush=True)
        check(ok, "AC-OTR1 orphans and rounds imported from evidence_variants")
    finally:
        EV.variants = saved
        shutil.rmtree(world, ignore_errors=True)


def ac_otr2():
    """AC-OTR2: every runner-carrying leg named, standing-in first by name."""
    world = make_world([("reconcile-all-R1501a.log", SILENT),
                        ("reconcile-all-R1501b.log", NO_VERDICT),
                        ("reconcile-all-R1501c.log", GREEN)])
    try:
        report = OT.traces(world)
        item = report["rounds"][0]
        legs = dict((leg["name"], leg) for leg in item["legs"])
        code = run_cli(world)[0]
        ok = (item["round"] == "R1501"
              and item["status"] == "TRACE-EXISTS"
              and item["standing_in"] == "reconcile-all-R1501b.log"
              and [leg["name"] for leg in item["legs"]]
              == ["reconcile-all-R1501a.log", "reconcile-all-R1501b.log",
                  "reconcile-all-R1501c.log"]
              and legs["reconcile-all-R1501a.log"]["runner"] is None
              and legs["reconcile-all-R1501b.log"]["runner"] == "FAIL"
              and legs["reconcile-all-R1501b.log"]["verdict"] is None
              and legs["reconcile-all-R1501c.log"]["runner"] == "PASS"
              and legs["reconcile-all-R1501c.log"]["verdict"] == "PASS"
              and legs["reconcile-all-R1501c.log"]["digest"] == sha256(GREEN)
              and report["counts"]["trace_exists"] == 1
              and report["counts"]["no_trace"] == 0
              and report["verdict"] == "TRACE-FOUND"
              and code == 0)
        if not ok:
            print("  measured: item=%r code=%r" % (item, code), flush=True)
        check(ok, "AC-OTR2 every runner leg named, first in name order stands")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_otr3():
    """AC-OTR3: no runner line anywhere reads NO-TRACE; empty reads NO-ORPHAN."""
    quiet = make_world([("reconcile-all-R1502a.log", SILENT),
                        ("reconcile-all-R1502b.log", "SECTION matrix PASS\n")])
    empty = make_world([("reconcile-all-R1503.log", GREEN)])
    try:
        report = OT.traces(quiet)
        item = report["rounds"][0]
        clean = OT.traces(empty)
        ok = (item["status"] == "NO-TRACE"
              and item["standing_in"] is None
              and report["counts"]["no_trace"] == 1
              and report["verdict"] == "TRACE-MISSING"
              and run_cli(quiet)[0] == 2
              and clean["counts"]["rounds"] == 0
              and clean["counts"]["legs"] == 0
              and clean["verdict"] == "NO-ORPHAN"
              and run_cli(empty)[0] == 0)
        if not ok:
            print("  measured: item=%r report=%r clean=%r"
                  % (item, report, clean), flush=True)
        check(ok, "AC-OTR3 NO-TRACE named, empty orphan list is NO-ORPHAN")
    finally:
        shutil.rmtree(quiet, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)


def ac_otr4():
    """AC-OTR4: an undecodable leg refuses instead of counting as no verdict."""
    world = make_world([("reconcile-all-R1504a.log", GREEN)])
    broken = make_world([("reconcile-all-R1505a.log", GREEN),
                         ("reconcile-all-R1505b.log", b"\xff\xff\xff\xff")])
    try:
        raised = None
        try:
            OT.traces(broken)
        except OT.OrphanTraceError as exc:
            raised = exc.code
        code, out = run_cli(broken)
        ok = (raised == "E_OTR_UNDECODABLE"
              and code == 3
              and "E_OTR_UNDECODABLE" in out
              and OT.traces(world)["verdict"] == "TRACE-FOUND")
        if not ok:
            print("  measured: raised=%r code=%r out=%r"
                  % (raised, code, out), flush=True)
        check(ok, "AC-OTR4 undecodable leg refuses with its own code")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(broken, ignore_errors=True)


def ac_otr5():
    """AC-OTR5: CLI 0/2/3/5, byte-stable --json over pinned keys, read-only."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    clean = make_world([("reconcile-all-R1506a.log", GREEN)])
    missing = make_world([("reconcile-all-R1507a.log", SILENT)])
    try:
        before = tree_digest(missing)
        first = run_cli(missing, ["--json"])[1]
        second = run_cli(missing, ["--json"])[1]
        OT.traces(missing)
        after = tree_digest(missing)
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == OT.REPORT_KEYS
        counts_pinned = tuple(parsed["counts"].keys()) == OT.COUNT_KEYS
        row_pinned = tuple(parsed["rounds"][0].keys()) == OT.ROUND_KEYS
        leg_pinned = (tuple(parsed["rounds"][0]["legs"][0].keys())
                      == OT.LEG_KEYS)
        absent = os.path.join(clean, "nowhere")
        rendered = OT.render(OT.traces(missing))
        ok = (no_clock and before == after
              and run_cli(clean)[0] == 0
              and run_cli(missing)[0] == 2
              and run_cli(absent)[0] == 3
              and run_cli(clean, ["--nope"])[0] == 5
              and run_cli(clean, ["--root"])[0] == 5
              and first == second
              and pinned and counts_pinned and row_pinned and leg_pinned
              and parsed["verdict"] == "TRACE-MISSING"
              and "ORPHAN TRACE" in rendered
              and "status=NO-TRACE" in rendered)
        if not ok:
            print("  measured: no_clock=%r writes=%r stable=%r pinned=%r "
                  "render=%r" % (no_clock, before == after, first == second,
                                 (pinned, counts_pinned, row_pinned,
                                  leg_pinned), rendered), flush=True)
        check(ok, "AC-OTR5 CLI codes, byte-stable json, pinned keys")
    finally:
        shutil.rmtree(clean, ignore_errors=True)
        shutil.rmtree(missing, ignore_errors=True)


def ac_otr6():
    """AC-OTR6: pure source, stdlib only, wired, live pile resolved."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = OT.traces(REPO)
    counts = live["counts"]
    ok = (ascii_only and no_net and wired
          and live["dir"] == "qa"
          and counts["rounds"] >= 1
          and counts["legs"] >= counts["rounds"]
          and counts["trace_exists"] + counts["no_trace"] == counts["rounds"]
          and live["verdict"] in ("NO-ORPHAN", "TRACE-FOUND",
                                  "TRACE-MISSING")
          and all(item["standing_in"] in
                  [leg["name"] for leg in item["legs"]]
                  for item in live["rounds"]
                  if item["status"] == "TRACE-EXISTS"))
    if not ok:
        print("  measured: ascii=%r net=%r wired=%r live=%r"
              % (ascii_only, no_net, wired, live), flush=True)
    check(ok, "AC-OTR6 pure source, wired, live orphan pile resolved")


def main():
    print("orphan_trace suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_otr1()
    ac_otr2()
    ac_otr3()
    ac_otr4()
    ac_otr5()
    ac_otr6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())