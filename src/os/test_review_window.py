"""review_window_decl suite (R2305; criteria AC-RWD1..AC-RWD6 were
pre-registered inside the R2292 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the window a review is judged against is now a dated
declaration instead of a per-call argument. One pinned shape and nothing
else, a future declaration refused before it is used, a window that moved
without a declaration row read as DRIFT with both rounds named, no window
handed back for any unreadable or drifting state, and a caller-supplied
window compared rather than trusted.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

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

import review_window_decl as RW  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "review_window_decl.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window"

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


def declaration(window=100, declared_by="R2305", reason="declared for the suite",
                rows=None):
    """A well-shaped declaration, with the rows defaulting to one matching."""
    if rows is None:
        rows = [{"window": window, "declared_by": declared_by,
                 "reason": "first row"}]
    return {
        "window": window,
        "declared_by": declared_by,
        "reason": reason,
        "declarations": rows,
    }


def make_world(body, raw=None):
    """A temp root carrying state/review_window.json (raw text wins)."""
    world = tempfile.mkdtemp(prefix="bigdomain-rwd-")
    state = os.path.join(world, "state")
    os.makedirs(state)
    if raw is not None:
        with io.open(os.path.join(state, "review_window.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            handle.write(raw)
    elif body is not None:
        with io.open(os.path.join(state, "review_window.json"), "w",
                     encoding="utf-8", newline="\n") as handle:
            json.dump(body, handle, indent=2, sort_keys=False)
            handle.write("\n")
    return world


def tree_digest(world):
    """Every file under the world with its size and bytes."""
    out = []
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            with io.open(path, "rb") as handle:
                data = handle.read()
            out.append((os.path.relpath(path, world), len(data),
                        hash(data)))
        for name in sorted(dirs):
            out.append((os.path.relpath(os.path.join(root, name), world),
                        -1, 0))
    return sorted(out)


def run_cli(world, args=None):
    """Run the module as a child interpreter against one world."""
    argv = [sys.executable, MODULE, "--check", "--root", world]
    if args:
        argv.extend(args)
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def raised_code(body, raw=None, window=None, round_text=None):
    """Resolve one world and return the raised code, or None."""
    world = make_world(body, raw)
    try:
        RW.resolve(world, window, round_text)
        return None
    except RW.ReviewWindowError as exc:
        return exc.code
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rwd1():
    """AC-RWD1: one pinned shape, and every refusal carries its own code."""
    good = declaration()
    missing_key = declaration()
    del missing_key["reason"]
    no_rows = declaration()
    no_rows["declarations"] = []
    row_missing = declaration(rows=[{"window": 100, "declared_by": "R2305"}])
    cases = []
    # unpinned is its own state, never a fabricated pass
    cases.append(("unpinned", raised_code(None), "E_RWD_UNPINNED"))
    # shape refusals
    cases.append(("missing key", raised_code(missing_key), "E_RWD_BAD_SHAPE"))
    cases.append(("empty rows", raised_code(no_rows), "E_RWD_BAD_SHAPE"))
    cases.append(("row missing key", raised_code(row_missing),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("empty reason", raised_code(declaration(reason="   ")),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("str window", raised_code(declaration(window="100")),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("bool window", raised_code(declaration(window=True)),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("zero window", raised_code(declaration(window=0)),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("negative window", raised_code(declaration(window=-5)),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("bad round", raised_code(declaration(declared_by="Rx")),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("not an object", raised_code(None, raw="[1, 2]"),
                  "E_RWD_BAD_SHAPE"))
    cases.append(("not json", raised_code(None, raw="{not json"),
                  "E_RWD_UNREADABLE"))
    # consistency, judged BEFORE the declaration is used
    cases.append(("future declaration",
                  raised_code(good, round_text="R2300"), "E_RWD_DECL_FUTURE"))
    own_order = declaration(declared_by="R2300", rows=[
        {"window": 100, "declared_by": "R2305", "reason": "later row"}])
    cases.append(("declared_by before its row",
                  raised_code(own_order), "E_RWD_REFUSED"))
    codes = set(code for _, code, _ in cases)
    ok = all(measured == expected for _, measured, expected in cases)
    ok = ok and len(codes) == 5
    if not ok:
        for name, measured, expected in cases:
            if measured != expected:
                print("  measured %s: %r != %r"
                      % (name, measured, expected), flush=True)
    check(ok, "AC-RWD1 one pinned shape, five distinct refusal codes")


def ac_rwd2():
    """AC-RWD2: a caller window is compared, never quietly preferred."""
    world = make_world(declaration(window=100))
    try:
        same = RW.resolve(world, 100)
        other = RW.resolve(world, 50)
        silent = RW.resolve(world, None)
        rendered = RW.render(other)
        ok = (same["verdict"] == "AGREES" and same["caller"] == 100
              and other["verdict"] == "DISAGREES" and other["caller"] == 50
              and other["window"] == 100
              and silent["verdict"] == "AGREES" and silent["caller"] is None
              and "DISAGREES caller=50 declared=100" in rendered)
        if not ok:
            print("  measured: same=%r other=%r silent=%r rendered=%r"
                  % (same["verdict"], other, silent["verdict"], rendered),
                  flush=True)
        check(ok, "AC-RWD2 disagreement names both windows")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_rwd3():
    """AC-RWD3: a bump with no new declaration row is DRIFT, both rounds named."""
    bumped = declaration(window=120, declared_by="R2306", rows=[
        {"window": 100, "declared_by": "R2305", "reason": "the only row"}])
    # a silent bump with the SAME declaring round: the top-level window moved
    # but the last row still says 100, which is the quiet edit DRIFT exists for
    drifted_same_round = declaration(window=120, rows=[
        {"window": 100, "declared_by": "R2305", "reason": "the only row"}])
    world = make_world(bumped)
    same_round = make_world(drifted_same_round)
    try:
        raised = None
        detail = ""
        try:
            RW.resolve(world)
        except RW.ReviewWindowError as exc:
            raised = exc.code
            detail = exc.detail
        raised2 = None
        try:
            RW.resolve(same_round)
        except RW.ReviewWindowError as exc:
            raised2 = exc.code
        ok = (raised == "E_RWD_DRIFT" and raised2 == "E_RWD_DRIFT"
              and "120" in detail and "100" in detail
              and "R2306" in detail and "R2305" in detail
              and "forward" in detail)
        if not ok:
            print("  measured: raised=%r same=%r detail=%r"
                  % (raised, raised2, detail), flush=True)
        check(ok, "AC-RWD3 drift names both windows and both rounds")
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(same_round, ignore_errors=True)


def ac_rwd4():
    """AC-RWD4: no window is handed back, nothing is written, no clock read."""
    unpinned = make_world(None)
    drift = make_world(declaration(window=120, rows=[
        {"window": 100, "declared_by": "R2305", "reason": "the only row"}]))
    good = make_world(declaration())
    bad = make_world(declaration(window="100"))
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_clock = ("import time" not in source and "datetime" not in source
                and "time.time" not in source)
    results = []
    try:
        before_unpinned = tree_digest(unpinned)
        before_drift = tree_digest(drift)
        before_good = tree_digest(good)
        before_bad = tree_digest(bad)
        for world in (unpinned, drift, bad):
            try:
                value = RW.resolve(world, 100)
                results.append(value)
            except RW.ReviewWindowError as exc:
                results.append(exc.code)
        resolved = RW.resolve(good, 100)
        unchanged = (before_unpinned == tree_digest(unpinned)
                     and before_drift == tree_digest(drift)
                     and before_good == tree_digest(good)
                     and before_bad == tree_digest(bad))
        ok = (results == ["E_RWD_UNPINNED", "E_RWD_DRIFT", "E_RWD_BAD_SHAPE"]
              and resolved["window"] == 100
              and unchanged and no_clock)
        if not ok:
            print("  measured: results=%r window=%r writes=%r clock=%r"
                  % (results, resolved["window"], unchanged, no_clock),
                  flush=True)
        check(ok, "AC-RWD4 refuse rather than default, zero writes, no clock")
    finally:
        for world in (unpinned, drift, good, bad):
            shutil.rmtree(world, ignore_errors=True)


def ac_rwd5():
    """AC-RWD5: CLI exits 0/2/2/3/5 with byte-stable --json over pinned keys."""
    good = make_world(declaration())
    unpinned = make_world(None)
    broken = make_world(None, raw="{not json")
    drifted = make_world(declaration(window=120, rows=[
        {"window": 100, "declared_by": "R2305", "reason": "the only row"}]))
    try:
        code_pinned = run_cli(good, ["--window", "100"])[0]
        code_disagree = run_cli(good, ["--window", "50"])[0]
        code_round = run_cli(good, ["--round", "R2305"])[0]
        code_unpinned = run_cli(unpinned)[0]
        code_drift = run_cli(drifted)[0]
        code_unreadable = run_cli(broken)[0]
        code_flags = run_cli(good, ["--nope"])[0]
        code_no_value = run_cli(good, ["--window"])[0]
        code_missing_check = subprocess.run(
            [sys.executable, MODULE, "--root", good],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
        first = run_cli(good, ["--json"])[1]
        second = run_cli(good, ["--json"])[1]
        parsed = json.loads(first)
        pinned = tuple(parsed.keys()) == RW.REPORT_KEYS
        ok = (code_pinned == 0 and code_disagree == 2 and code_round == 0
              and code_unpinned == 2 and code_drift == 2
              and code_unreadable == 3 and code_flags == 5
              and code_no_value == 5 and code_missing_check == 5
              and first == second and pinned
              and parsed["window"] == 100)
        if not ok:
            print("  measured: codes=%r stable=%r pinned=%r"
                  % ((code_pinned, code_disagree, code_round, code_unpinned,
                      code_drift, code_unreadable, code_flags, code_no_value,
                      code_missing_check), first == second, pinned),
                  flush=True)
        check(ok, "AC-RWD5 CLI codes and byte-stable pinned json")
    finally:
        for world in (good, unpinned, broken, drifted):
            shutil.rmtree(world, ignore_errors=True)


def ac_rwd6():
    """AC-RWD6: pure ASCII, stdlib only, wired, and the live reading agrees."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = ("socket" not in source and "urllib" not in source
              and "http" not in source)
    stdlib_only = True
    for line in source.splitlines():
        text = line.strip()
        if text.startswith("import ") and " " not in text[7:]:
            name = text[7:].strip()
            if name not in ("json", "os", "sys"):
                stdlib_only = False
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = RW.resolve(REPO, 100, "R2305")
    rendered = RW.render(live)
    ok = (ascii_only and no_net and stdlib_only and wired
          and live["window"] == 100 and live["verdict"] == "AGREES"
          and live["declarations"] >= 1
          and "REVIEW WINDOW window=100" in rendered)
    if not ok:
        print("  measured: ascii=%r net=%r stdlib=%r wired=%r live=%r"
              % (ascii_only, no_net, stdlib_only, wired, live), flush=True)
    check(ok, "AC-RWD6 pure source, wired, live declaration pinned")


def main():
    print("review_window_decl suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rwd1()
    ac_rwd2()
    ac_rwd3()
    ac_rwd4()
    ac_rwd5()
    ac_rwd6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())