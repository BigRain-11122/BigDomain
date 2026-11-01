"""review_window_history suite (R2345; criteria AC-RWH1..AC-RWH6 were pinned
inside the R2327 tech seed row of state/queue/tech.md BEFORE this code
existed).

What this proves: the declarations list is now read as a history instead of
being collapsed into its last row. The parsed rows come from the resolver
own shape law and the resolver own reading is asked, so the two readers
cannot disagree about the same file; a list that rewinds in time refuses
naming both rows and both rounds; every window move is named with from/to and
both declaring rounds in file order, while a list with no move reads
EMPTY-HISTORY rather than CLEAN.

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

import review_window_decl as RWD  # noqa: E402
import review_window_history as RWH  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "review_window_history.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-review-window-history"

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


def row(window, declared_by, reason="row reason"):
    return {"window": window, "declared_by": declared_by, "reason": reason}


def world(rows, window=None, declared_by=None, reason="world reason"):
    """A temporary repo root holding one state/review_window.json."""
    root = tempfile.mkdtemp(prefix="rwh-")
    os.makedirs(os.path.join(root, "state"))
    payload = {
        "window": rows[-1]["window"] if window is None else window,
        "declared_by": rows[-1]["declared_by"] if declared_by is None else declared_by,
        "reason": reason,
        "declarations": rows,
    }
    with io.open(os.path.join(root, "state", "review_window.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, indent=2))
    return root


def run_cli(root, extra=None):
    args = [sys.executable, MODULE, "--check", "--root", root]
    if extra:
        args.extend(extra)
    proc = subprocess.run(args, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, cwd=REPO)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def snapshot(root):
    """Every path plus its size and mtime under the world root."""
    found = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found.append((os.path.relpath(path, root), stat.st_size,
                          int(stat.st_mtime)))
    return sorted(found)


def ac_rwh1():
    """The rows come from the resolver shape law, and a patched law flows."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    no_second_law = ("RWD.shape(" in source
                     and "DECLARATION_KEYS" not in source
                     and "def shape(" not in source
                     and "re.compile" not in source)

    root = world([row(10, "R2305")])
    original = RWD.shape
    # The shape contract hands declared_by back as an INT (parse_round), so a
    # doctored reading must respect that contract or it is testing nothing.
    doctored = [{"window": 10, "declared_by": 2305, "reason": "patched row"},
                {"window": 20, "declared_by": 2306, "reason": "patched row"}]

    def patched(raw, origin):
        parsed = original(raw, origin)
        parsed["window"] = 20
        parsed["declared_by"] = 2306
        parsed["declarations"] = [dict(item) for item in doctored]
        return parsed

    RWD.shape = patched
    try:
        report = RWH.history(root)
    finally:
        RWD.shape = original
    flowed = (report["verdict"] == "MOVED" and len(report["moves"]) == 1
              and report["declarations"] == 2)
    if not (no_second_law and flowed):
        print("  measured: no_second_law=%r flowed=%r report=%r"
              % (no_second_law, flowed, report), flush=True)
    check(no_second_law and flowed,
          "AC-RWH1 rows come from RWD.shape and a patched shape flows through")


def ac_rwh2():
    """A rewind refuses naming both rows and both rounds."""
    root = world([row(10, "R2400"), row(20, "R2300")],
                 window=20, declared_by="R2400")
    code = None
    detail = ""
    try:
        RWH.history(root)
    except RWH.ReviewWindowHistoryError as exc:
        code = exc.code
        detail = exc.detail
    refused = (code == "E_RWH_REWIND"
               and "R2400" in detail and "R2300" in detail
               and "0" in detail and "1" in detail)
    rc, body = run_cli(root)
    cli = rc == 2 and "E_RWH_REWIND" in body
    if not (refused and cli):
        print("  measured: code=%r detail=%r rc=%r body=%r"
              % (code, detail, rc, body), flush=True)
    check(refused and cli,
          "AC-RWH2 a declared_by rewind refuses naming both rows and rounds")


def ac_rwh3():
    """Every move is named in file order; no move reads EMPTY-HISTORY."""
    root = world([row(10, "R2305"), row(20, "R2306"), row(30, "R2307")])
    report = RWH.history(root)
    named = (report["verdict"] == "MOVED" and len(report["moves"]) == 2)
    if named:
        first, second = report["moves"]
        named = (first["from"] == 10 and first["to"] == 20
                 and first["from_round"] == "R2305"
                 and first["to_round"] == "R2306"
                 and first["index"] == 1
                 and second["from"] == 20 and second["to"] == 30
                 and second["from_round"] == "R2306"
                 and second["to_round"] == "R2307"
                 and second["index"] == 2)
    rendered = RWH.render(report) if named else ""
    in_order = rendered.find("MOVE 1 from=10") < rendered.find("MOVE 2 from=20")

    flat = RWH.history(world([row(100, "R2305")]))
    honest = (flat["verdict"] == "EMPTY-HISTORY"
              and flat["verdict"] != "CLEAN" and not flat["moves"])
    rc, body = run_cli(world([row(100, "R2305")]))
    zero = rc == 0 and "EMPTY-HISTORY" in body
    if not (named and in_order and honest and zero):
        print("  measured: named=%r in_order=%r honest=%r zero=%r"
              % (named, in_order, honest, zero), flush=True)
    check(named and in_order and honest and zero,
          "AC-RWH3 moves named in file order, no move reads EMPTY-HISTORY")


def ac_rwh4():
    """Two worlds differ by exactly one row; DRIFT is the resolver own word."""
    rows = [row(10, "R2305"), row(20, "R2306")]
    agreeing = world(rows, window=20, declared_by="R2306")
    drifting = world(rows, window=10, declared_by="R2306")

    live = RWH.history(agreeing)
    resolver_live = RWD.resolve(agreeing)
    agrees = (live["verdict"] == "MOVED" and live["resolver"] == "AGREES"
              and resolver_live["verdict"] == "AGREES")

    resolver_detail = ""
    try:
        RWD.resolve(drifting)
        resolver_drift = False
    except RWD.ReviewWindowError as exc:
        resolver_drift = exc.code == "E_RWD_DRIFT"
        resolver_detail = exc.detail

    history = RWH.history(drifting)
    same_word = (history["verdict"] == "DRIFT"
                 and history["resolver"] == "DRIFT %s" % resolver_detail)
    rc, body = run_cli(drifting)
    cli_agrees = rc == 2 and "DRIFT" in body and resolver_detail.split()[0] in body
    if not (agrees and resolver_drift and same_word and cli_agrees):
        print("  measured: agrees=%r resolver_drift=%r same_word=%r "
              "cli=%r history=%r detail=%r"
              % (agrees, resolver_drift, same_word, cli_agrees, history,
                 resolver_detail), flush=True)
    check(agrees and resolver_drift and same_word and cli_agrees,
          "AC-RWH4 identical DRIFT reading to the resolver on a one-row diff")


def ac_rwh5():
    """CLI 0/2/3/5, a byte-stable --json, and zero writes."""
    moved = world([row(10, "R2305"), row(20, "R2306")])
    before = snapshot(moved)
    rc_zero, _body_zero = run_cli(moved, ["--json"])
    first = run_cli(moved, ["--json"])[1]
    second = run_cli(moved, ["--json"])[1]
    after = snapshot(moved)
    stable = first == second and json.loads(first)["verdict"] == "MOVED"
    untouched = before == after

    rewind_rc = run_cli(world([row(10, "R2400"), row(20, "R2300")],
                              window=20, declared_by="R2400"))[0]
    drift_rc = run_cli(world([row(10, "R2305"), row(20, "R2306")],
                             window=10, declared_by="R2306"))[0]

    bad = tempfile.mkdtemp(prefix="rwh-bad-")
    os.makedirs(os.path.join(bad, "state"))
    with io.open(os.path.join(bad, "state", "review_window.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write("{not json")
    unreadable_rc = run_cli(bad)[0]

    shapeless = world([row(10, "R2305")])
    with io.open(os.path.join(shapeless, "state", "review_window.json"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"window": 10, "declared_by": "R2305",
                                 "reason": "x", "declarations": []},
                                ensure_ascii=True))
    shape_rc = run_cli(shapeless)[0]

    args_rc = subprocess.run([sys.executable, MODULE], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, cwd=REPO).returncode
    flag_rc = run_cli(moved, ["--nope"])[0]

    codes = (rc_zero == 0 and rewind_rc == 2 and drift_rc == 2
             and unreadable_rc == 3 and shape_rc == 3
             and args_rc == 5 and flag_rc == 5)
    if not (codes and stable and untouched):
        print("  measured: zero=%r rewind=%r drift=%r unreadable=%r shape=%r "
              "args=%r flag=%r stable=%r untouched=%r"
              % (rc_zero, rewind_rc, drift_rc, unreadable_rc, shape_rc,
                 args_rc, flag_rc, stable, untouched), flush=True)
    check(codes and stable and untouched,
          "AC-RWH5 exit codes 0/2/3/5, byte-stable --json, zero writes")


def ac_rwh6():
    """Pure source, wired, and the live declaration reads honestly."""
    source = io.open(MODULE, "r", encoding="utf-8").read()
    ascii_only = all(ord(char) < 128 for char in source)
    no_net = not any(token in source for token in
                     ("urllib", "socket", "requests", "http://", "https://"))
    no_clock = not any(token in source for token in
                       ("import time", "import datetime", "time.time"))
    stdlib_only = True
    for line in source.splitlines():
        text = line.strip()
        if text.startswith("import ") and " " not in text[7:]:
            name = text[7:].strip()
            if name not in ("json", "os", "sys", "review_window_decl"):
                stdlib_only = False
    runner = io.open(RUNNER, "r", encoding="utf-8").read()
    wired = ('"%s"' % LABEL in runner) or ("'%s'" % LABEL in runner)
    live = RWH.history(REPO)
    honest = (live["verdict"] in ("MOVED", "EMPTY-HISTORY")
              and live["resolver"] == "AGREES"
              and live["declarations"] >= 1
              and "REVIEW WINDOW HISTORY" in RWH.one_line(live))
    if not (ascii_only and no_net and no_clock and stdlib_only and wired
            and honest):
        print("  measured: ascii=%r net=%r clock=%r stdlib=%r wired=%r live=%r"
              % (ascii_only, no_net, no_clock, stdlib_only, wired, live),
              flush=True)
    check(ascii_only and no_net and no_clock and stdlib_only and wired
          and honest,
          "AC-RWH6 pure source, wired, live declaration reads honestly")


def main():
    print("review_window_history suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rwh1()
    ac_rwh2()
    ac_rwh3()
    ac_rwh4()
    ac_rwh5()
    ac_rwh6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())