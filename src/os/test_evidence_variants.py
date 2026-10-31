"""evidence_variants suite (R2302; criteria AC-EVR1..AC-EVR6 were
pre-registered inside the R2288 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: a variant leg that the history reports as IGNORED becomes a
classified fact. The round and the suffix are asked of followup_history's own
name law (never a second regex), the canonical leg is looked up on disk, and
the DUPLICATE/DISTINCT split is decided by CONTENT digest rather than by name -
so `-2` that differs reads DISTINCT with both digests named, and a variant with
no canonical round reads ORPHAN instead of vanishing.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, BASE)

import evidence_variants as EV  # noqa: E402
import followup_history as FH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "evidence_variants.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-evidence-variants"

GREEN = "RUNNER PASS 4/4 suites green\nSECTION matrix PASS\nVERDICT PASS\n"
RED = "SUITE FAIL 2/4\nRUNNER FAIL\n"

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
    """A temp root with one qa directory; body None makes a directory."""
    world = tempfile.mkdtemp(prefix="bigdomain-evr-")
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name, body in files:
        target = os.path.join(qa, name)
        if body is None:
            os.makedirs(target)
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
    argv = [sys.executable, MODULE, "--variants", "--root", world]
    argv.extend(extra)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_evr1():
    """AC-EVR1: round and suffix come from the shared law, never a second regex."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    statements = [line.strip() for line in source.splitlines()]
    # "import retry_naming" must not be mistaken for a regex import here.
    no_regex = ("import re" not in statements and "re.compile" not in source
                and "\\d" not in source)
    world = make_world([("reconcile-all-R1400.log", GREEN),
                        ("reconcile-all-R1400-2.log", GREEN)])
    patched_world = make_world([("variant-R1400.log", GREEN),
                                ("variant-R1400-b.log", GREEN)])
    saved = FH.NAME_RE
    try:
        live = EV.variants(world)
        # Patch the ONE law: the scope prefix and the round both move with it,
        # which is only possible if this reader asks rather than restates.
        FH.NAME_RE = re.compile(r"^variant-(R(\d+))\.log$")
        moved_scope = EV.variants(patched_world)
        stale_scope = [row["name"] for row in EV.variants(world)["variants"]]
        refused = None
        try:
            EV.classify(os.path.join(world, "qa"), "reconcile-all-R1400-2.log")
        except EV.EvidenceVariantsError as exc:
            refused = exc.code
        ok = (no_regex
              and len(live["variants"]) == 1
              and live["variants"][0]["round"] == "R1400"
              and live["variants"][0]["suffix"] == "-2"
              and EV.canonical_prefix() == "variant-"
              and len(moved_scope["variants"]) == 1
              and moved_scope["variants"][0]["round"] == "R1400"
              and moved_scope["variants"][0]["suffix"] == "-b"
              and stale_scope == []
              and refused == "E_EVR_BAD_NAME")
        if not ok:
            print("  measured: no_regex=%r live=%r moved=%r stale=%r "
                  "refused=%r"
                  % (no_regex, live["variants"], moved_scope["variants"],
                     stale_scope, refused), flush=True)
        check(ok, "AC-EVR1 round and suffix derived from the shared name law")
    finally:
        FH.NAME_RE = saved
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(patched_world, ignore_errors=True)


def ac_evr2():
    """AC-EVR2: a variant with no canonical round reads ORPHAN, never dropped."""
    orphan_only = make_world([("reconcile-all-R2136c.log", GREEN)])
    empty = make_world([])
    try:
        report = EV.variants(orphan_only)
        row = report["variants"][0]
        clean = EV.variants(empty)
        code = run_cli(orphan_only)[0]
        ok = (len(report["variants"]) == 1
              and row["status"] == "ORPHAN"
              and row["round"] == "R2136"
              and row["suffix"] == "c"
              and row["canonical"] == "reconcile-all-R2136.log"
              and row["canonical_digest"] is None
              and row["digest"] == sha256(GREEN)
              and report["counts"]["orphan"] == 1
              and report["verdict"] == "UNRESOLVED"
              and code == 2
              and clean["counts"]["variants"] == 0
              and clean["verdict"] == "RESOLVED"
              and run_cli(empty)[0] == 0)
        if not ok:
            print("  measured: row=%r report=%r code=%r clean=%r"
                  % (row, report, code, clean), flush=True)
        check(ok, "AC-EVR2 ORPHAN named, never dropped silently")
    finally:
        shutil.rmtree(orphan_only, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)


def ac_evr3():
    """AC-EVR3: DUPLICATE/DISTINCT by content digest, both digests named."""
    world = make_world([("reconcile-all-R1401.log", GREEN),
                        ("reconcile-all-R1401-2.log", GREEN),
                        ("reconcile-all-R1401-3.log", RED),
                        ("reconcile-all-R1401-zzz.log", GREEN),
                        ("reconcile-all-R1401-retry.log", RED)])
    try:
        report = EV.variants(world)
        rows = dict((row["suffix"], row) for row in report["variants"])
        green_digest = sha256(GREEN)
        red_digest = sha256(RED)
        # The SAME content under two different suffix names proves the split
        # is content-keyed: only "-3" and "-retry" differ from the canonical.
        ok = (len(rows) == 4
              and rows["-2"]["status"] == "DUPLICATE"
              and rows["-zzz"]["status"] == "DUPLICATE"
              and rows["-2"]["digest"] == green_digest
              and rows["-2"]["canonical_digest"] == green_digest
              and rows["-3"]["status"] == "DISTINCT"
              and rows["-3"]["digest"] == red_digest
              and rows["-3"]["canonical_digest"] == green_digest
              and rows["-retry"]["status"] == "DISTINCT"
              and rows["-retry"]["kind"] == "retry"
              and rows["-2"]["kind"] == "other"
              and report["counts"]["duplicate"] == 2
              and report["counts"]["distinct"] == 2
              and report["counts"]["retry"] == 1
              and report["verdict"] == "UNRESOLVED")
        if not ok:
            print("  measured: rows=%r counts=%r"
                  % (rows, report["counts"]), flush=True)
        check(ok, "AC-EVR3 duplicate matched by digest, DISTINCT names both")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_evr4():
    """AC-EVR4: zero writes, no clock, an unreadable variant fails closed."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    world = make_world([("reconcile-all-R1402.log", GREEN),
                        ("reconcile-all-R1402-2.log", GREEN)])
    broken = make_world([("reconcile-all-R1403.log", GREEN),
                         ("reconcile-all-R1403-2.log", None)])
    try:
        before = tree_digest(world)
        EV.variants(world)
        after = tree_digest(world)
        raised = None
        try:
            EV.variants(broken)
        except EV.EvidenceVariantsError as exc:
            raised = exc.code
        code = run_cli(broken)[0]
        ok = (no_clock and before == after
              and raised == "E_EVR_UNREADABLE"
              and code == 3)
        if not ok:
            print("  measured: no_clock=%r writes=%r raised=%r code=%r"
                  % (no_clock, before == after, raised, code), flush=True)
        check(ok, "AC-EVR4 read-only, no clock, unreadable fails closed")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(broken, ignore_errors=True)


def ac_evr5():
    """AC-EVR5: CLI 0/2/5, byte-stable --json over pinned keys, 3 on absence."""
    resolved = make_world([("reconcile-all-R1404.log", GREEN),
                           ("reconcile-all-R1404-2.log", GREEN)])
    unresolved = make_world([("reconcile-all-R1404.log", GREEN),
                             ("reconcile-all-R1404-2.log", RED)])
    try:
        code_ok = run_cli(resolved)[0]
        code_bad = run_cli(unresolved)[0]
        code_flags = run_cli(resolved, ["--nope"])[0]
        code_absent = run_cli(os.path.join(resolved, "nowhere"))[0]
        first = run_cli(unresolved, ["--json"])[1]
        second = run_cli(unresolved, ["--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == EV.REPORT_KEYS
        counts_pinned = tuple(parsed["counts"].keys()) == EV.COUNT_KEYS
        row_pinned = tuple(parsed["variants"][0].keys()) == EV.VARIANT_KEYS
        rendered = EV.render(EV.variants(resolved))
        ok = (code_ok == 0 and code_bad == 2 and code_flags == 5
              and code_absent == 3
              and first == second
              and pinned and counts_pinned and row_pinned
              and parsed["verdict"] == "UNRESOLVED"
              and "EVIDENCE VARIANTS" in rendered
              and "RESOLVED" in rendered)
        if not ok:
            print("  measured: codes=%r stable=%r pinned=%r/%r/%r rendered=%r"
                  % ((code_ok, code_bad, code_flags, code_absent),
                     first == second, pinned, counts_pinned, row_pinned,
                     rendered), flush=True)
        check(ok, "AC-EVR5 CLI codes, byte-stable json, pinned keys")
    finally:
        shutil.rmtree(resolved, ignore_errors=True)
        shutil.rmtree(unresolved, ignore_errors=True)


def ac_evr6():
    """AC-EVR6: pure source, stdlib only, wired, live callable."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = EV.variants(REPO)
    ok = (ascii_only and no_net and wired
          and live["dir"] == "qa"
          and live["counts"]["variants"] == len(live["variants"]) > 0
          and (live["counts"]["duplicate"] + live["counts"]["distinct"]
               + live["counts"]["orphan"]) == live["counts"]["variants"]
          and live["counts"]["retry"] >= 4
          and live["verdict"] in ("RESOLVED", "UNRESOLVED"))
    if not ok:
        print("  measured: ascii=%r net=%r wired=%r live=%r"
              % (ascii_only, no_net, wired, live["counts"]), flush=True)
    check(ok, "AC-EVR6 pure source, wired, live pile classified")


def main():
    print("evidence_variants suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_evr1()
    ac_evr2()
    ac_evr3()
    ac_evr4()
    ac_evr5()
    ac_evr6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())