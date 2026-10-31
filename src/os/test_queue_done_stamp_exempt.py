"""queue_done_stamp_exempt suite (R2280; criteria AC-SEX1..AC-SEX6 were
pre-registered inside the R2278 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: the 380 closed rows the stamp gate reports as debt are now a
named, dated acceptance instead of a permanent red reading - and nothing else.
A missing declaration reads UNPINNED with the full debt (never a pass), a row
identity survives a line shift, an entry needs a real round and a real reason,
an expired entry puts the row back into debt naming its until round, the gate
itself is imported (a patched verdict flows straight through) and the counts
reconcile with ambiguity refused, and a reading writes nothing and reads no
clock while its own reconcile label is wired.

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

import queue_done_stamp as QDS  # noqa: E402
import queue_done_stamp_exempt as SX  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_done_stamp_exempt.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-done-stamp-exempt"

HEADER = ("# queue test world\n\n"
          "prose that mentions - [x] a done row and never becomes a row\n\n")

UNSTAMPED = "- [x] no bracket at all on this closed row\n"
DATE_ONLY = "- [x] [done 2026-10-31] a date but no window\n"
STAMPED = "- [x] [done 2026-10-31 R2270] a resolvable row\n"

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


def make_world(tech, main=None, explore=None, declaration=None, drop=None):
    """Build a temp root with the three queue files and an optional decl."""
    world = tempfile.mkdtemp(prefix="bigdomain-sex-")
    state = os.path.join(world, "state", "queue")
    os.makedirs(state)
    bodies = {"tech": tech,
              "main": main if main is not None else HEADER,
              "explore": explore if explore is not None else HEADER}
    for name in bodies:
        if drop and name in drop:
            continue
        path = os.path.join(state, name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if declaration is not None:
        path = os.path.join(state, "stamp_exempt.json")
        if isinstance(declaration, str):
            body = declaration
        else:
            body = json.dumps(declaration)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    return world


def drop_world(world):
    shutil.rmtree(world, ignore_errors=True)


def digest_tree(world):
    parts = []
    for base, _dirs, files in os.walk(world):
        for leaf in sorted(files):
            path = os.path.join(base, leaf)
            with open(path, "rb") as handle:
                parts.append((os.path.relpath(path, world).replace(os.sep,
                                                                   "/"),
                              len(handle.read())))
    return tuple(sorted(parts))


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          cwd=REPO)
    return (proc.returncode,
            proc.stdout.decode("ascii", "replace"),
            proc.stderr.decode("ascii", "replace"))


def entry(queue, identity, declared="R2280", reason="pre-law row",
          until=None):
    item = {"queue": queue, "identity": identity, "declared": declared,
            "reason": reason}
    if until is not None:
        item["until"] = until
    return item


def ac_sex1():
    """Declaration shape is enforced; a missing declaration reads UNPINNED."""
    world = make_world(UNSTAMPED + DATE_ONLY)
    try:
        report = SX.audit(world, 2280)
        code, out, _err = run_cli(["--check", "--round", "R2280",
                                   "--root", world])
    finally:
        drop_world(world)
    ok = (report["declaration"] == "UNPINNED"
          and report["violation_count"] == 2
          and report["exempt_today"] == 0
          and report["still_debt"] == 2
          and report["verdict"] == "EXEMPT-DEBT"
          and code == 2
          and "declaration=UNPINNED" in out)

    # A malformed declaration, an unknown top key and an unknown entry key
    # are all refused with their own code rather than read as nothing owed.
    tech = UNSTAMPED
    bad_bodies = ["{not json", json.dumps({"exemptions": [], "extra": 1}),
                  json.dumps({"entries": []})]
    codes = []
    for body in bad_bodies:
        world = make_world(tech, declaration=body)
        try:
            code, out, _err = run_cli(["--check", "--round", "R2280",
                                       "--root", world])
        finally:
            drop_world(world)
        codes.append((code, "E_SEX_BAD_DECL" in out))
    world = make_world(
        tech,
        declaration={"exemptions": [dict(entry("tech", "x#12345678"),
                                         bogus=1)]})
    try:
        code, out, _err = run_cli(["--check", "--round", "R2280",
                                   "--root", world])
    finally:
        drop_world(world)
    codes.append((code, "E_SEX_BAD_DECL" in out))
    ok = ok and all(item == (3, True) for item in codes)
    check(ok, "AC-SEX1 declaration shape enforced, missing file reads "
              "UNPINNED with full debt")


def ac_sex2():
    """A row identity is stable under a line shift, and is line-free."""
    identity = SX.identity_of(UNSTAMPED.strip())
    moved = HEADER + "- [x] an unrelated closed row\n" + UNSTAMPED
    world_a = make_world(UNSTAMPED)
    world_b = make_world(moved)
    try:
        report_a = SX.audit(world_a, 2280)
        report_b = SX.audit(world_b, 2280)
    finally:
        drop_world(world_a)
        drop_world(world_b)
    row_a = report_a["rows"][0]
    row_b = [row for row in report_b["rows"]
             if row["identity"] == identity]
    expected_line = moved.split("\n").index(UNSTAMPED.strip()) + 1
    ok = (row_a["identity"] == identity
          and row_a["line"] == 1
          and len(row_b) == 1
          and expected_line != row_a["line"]
          and row_b[0]["line"] == expected_line
          and "#" in identity
          and len(identity.split("#")[1]) == 8
          and SX.identity_of("  " + UNSTAMPED.strip() + "  ") == identity)
    check(ok, "AC-SEX2 identity is a text digest, stable across a line "
              "shift and whitespace")


def ac_sex3():
    """An entry needs a real round, a real reason and a legal optional until."""
    tech = UNSTAMPED
    identity = SX.identity_of(UNSTAMPED.strip())
    good = {"exemptions": [entry("tech", identity,
                                 reason="closed before the stamp law")]}
    world = make_world(tech, declaration=good)
    try:
        report = SX.audit(world, 2280)
    finally:
        drop_world(world)
    ok = (report["declaration"] == "PINNED"
          and report["exempt_today"] == 1
          and report["still_debt"] == 0
          and report["verdict"] == "EXEMPT-CLEAN")

    cases = [
        {"exemptions": [entry("tech", identity, declared="yesterday")]},
        {"exemptions": [entry("tech", identity, reason="   ")]},
        {"exemptions": [entry("tech", identity, until="R2270")]},
        {"exemptions": [entry("tech", identity)] * 2},
        {"exemptions": [entry("nowhere", identity)]},
    ]
    codes = []
    for body in cases:
        world = make_world(tech, declaration=body)
        try:
            code, out, _err = run_cli(["--check", "--round", "R2280",
                                       "--root", world])
        finally:
            drop_world(world)
        codes.append(code)
    ok = ok and codes == [3, 3, 3, 3, 3]
    check(ok, "AC-SEX3 a real round, a real reason and a legal optional "
              "until are required")


def ac_sex4():
    """An expired entry puts the row back into debt, naming its until round."""
    tech = UNSTAMPED
    identity = SX.identity_of(UNSTAMPED.strip())
    body = {"exemptions": [entry("tech", identity, declared="R2270",
                                 until="R2279")]}
    world = make_world(tech, declaration=body)
    try:
        report = SX.audit(world, 2280)
        code, out, _err = run_cli(["--check", "--round", "R2280",
                                   "--root", world])
        still = SX.audit(world, 2279)
    finally:
        drop_world(world)
    ok = (report["exempt_expired"] == 1
          and report["exempt_today"] == 0
          and report["still_debt"] == 1
          and report["verdict"] == "EXEMPT-DEBT"
          and report["rows"][0]["status"] == "EXPIRED"
          and report["rows"][0]["until"] == "R2279"
          and "until=R2279" in SX.render(report)
          and code == 2
          and still["exempt_today"] == 1
          and still["verdict"] == "EXEMPT-CLEAN")
    check(ok, "AC-SEX4 an expired entry reads as debt again and names its "
              "until round")


def ac_sex5():
    """The gate is imported, the counts reconcile, ambiguity is refused."""
    tech = UNSTAMPED + DATE_ONLY + STAMPED
    identity = SX.identity_of(UNSTAMPED.strip())
    body = {"exemptions": [entry("tech", identity)]}
    world = make_world(tech, declaration=body)
    original = QDS.audit_root
    patched_report = {
        "queues": [],
        "done_rows": 1,
        "stamped_rows": 0,
        "ok_rows": 0,
        "unstamped_rows": 1,
        "bad_stamp_rows": 0,
        "date_only_rows": 0,
        "before_seed_rows": 0,
        "violation_count": 1,
        "violations": [{"file": "state/queue/tech.md", "line": 9,
                        "status": "UNSTAMPED", "stamp": None, "round": None,
                        "seed_round": None,
                        "excerpt": UNSTAMPED.strip()}],
        "verdict": "DONE-STAMP-DEBT",
        "missing": [],
    }

    def patched(_root):
        return patched_report

    try:
        live = SX.audit(world, 2280)
        QDS.audit_root = patched
        try:
            flow = SX.audit(world, 2280)
        finally:
            QDS.audit_root = original
        report = SX.audit(world, 2280)
    finally:
        drop_world(world)
    reconciles = (report["violation_count"] == 2
                  and report["exempt_today"] == 1
                  and report["still_debt"] == 1
                  and report["exempt_today"] + report["still_debt"]
                  == report["violation_count"]
                  and live["violation_count"] == 2)
    flowed = (flow["violation_count"] == 1 and flow["rows"][0]["line"] == 9
              and flow["exempt_today"] == 1)

    # Two textually identical rows share one identity, so one entry cannot
    # silently exempt both.
    twin = UNSTAMPED + UNSTAMPED
    twin_identity = SX.identity_of(UNSTAMPED.strip())
    world = make_world(twin, declaration={"exemptions": [entry("tech",
                                                              twin_identity)]})
    try:
        code, out, _err = run_cli(["--check", "--round", "R2280",
                                   "--root", world])
    finally:
        drop_world(world)
    ok = reconciles and flowed and code == 3 and "E_SEX_AMBIGUOUS" in out
    check(ok, "AC-SEX5 the gate is imported, counts reconcile and ambiguity "
              "is refused")


def ac_sex6():
    """A reading writes nothing, reads no clock, and is wired as a label."""
    tech = UNSTAMPED + DATE_ONLY
    world = make_world(tech,
                       declaration={"exemptions": [
                           entry("tech", SX.identity_of(UNSTAMPED.strip()))]})
    try:
        before = digest_tree(world)
        SX.audit(world, 2280)
        SX.render(SX.audit(world, 2280))
        SX.to_json(SX.audit(world, 2280))
        after = digest_tree(world)
    finally:
        drop_world(world)
    with io.open(MODULE, "r", encoding="ascii") as handle:
        source = handle.read()
    no_clock = ("import time" not in source
                and "datetime" not in source
                and "now(" not in source)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        runner = handle.read()
    wired = ('"%s"' % LABEL) in runner and "test_queue_done_stamp_exempt.py" \
        in runner
    check(before == after and no_clock and wired and source.isascii(),
          "AC-SEX6 pure read, no clock, ASCII source and its own reconcile "
          "label")


def main():
    print("SUITE queue-done-stamp-exempt (AC-SEX1..AC-SEX6)", flush=True)
    ac_sex1()
    ac_sex2()
    ac_sex3()
    ac_sex4()
    ac_sex5()
    ac_sex6()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria" % ("PASS" if FAILS == 0 else "FAIL",
                                       PASSES, total), flush=True)
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 1


if __name__ == "__main__":
    sys.exit(main())