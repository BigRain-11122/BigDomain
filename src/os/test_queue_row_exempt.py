"""queue_row_exempt suite (R2276; criteria AC-QRX1..AC-QRX6 were
pre-registered inside the R2253 seed row of state/queue/tech.md BEFORE this
code existed).

What this proves: an accepted exemption is a recorded fact, not a widening of
the gate. The gate itself is imported (queue_row.audit_root), so the marker
law and the two accepted criteria forms stay in one place, and the suite
proves the import by patching the audit and watching the reading move.

The identity law is proven line-independent: the same row keeps its exemption
when lines are inserted above it (the failure mode of a line-number key), and
a REWORDED row loses its exemption and reads as debt again, because an
exemption whose condition no longer matches must never stay quiet.

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

import queue_row as QR  # noqa: E402
import queue_row_exempt as QE  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "queue_row_exempt.py")
SUITE = os.path.join(BASE, "test_queue_row_exempt.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-queue-row-exempt"

HEADER = ("# queue test world\n\n"
          "prose that mentions - [ ] a row law and never becomes a row\n\n")

BARE = ("- [ ] bare row one with no declaration at all\n"
        "- [ ] bare row two with no declaration at all\n")

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


def make_world(tech, main=None, explore=None, decl=None):
    """Build a temp root with the three queue files and an optional file."""
    world = tempfile.mkdtemp(prefix="bigdomain-qrx-")
    state = os.path.join(world, "state", "queue")
    os.makedirs(state)
    bodies = {"tech": tech,
              "main": main if main is not None else HEADER,
              "explore": explore if explore is not None else HEADER}
    for name in bodies:
        path = os.path.join(state, name + ".md")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(bodies[name])
    if decl is not None:
        path = os.path.join(state, "prefix_exempt.json")
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            if isinstance(decl, str):
                handle.write(decl)
            else:
                handle.write(json.dumps(decl, ensure_ascii=False))
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


def refused(fn):
    """Run a reader expected to refuse; return its error code or None."""
    try:
        fn()
    except QE.QueueRowExemptError as exc:
        return exc.code
    return None


def decl_for(pair, declared="R2276", reason="accepted as it stands",
              until=None):
    entry = {"queue": pair[0], "identity": pair[1], "declared": declared,
             "reason": reason}
    if until is not None:
        entry["until"] = until
    return {"exemptions": [entry]}


def ac_qrx1():
    """The declaration has one pinned shape; a missing file never reads clean."""
    world = make_world(HEADER + BARE)
    bad_json = make_world(HEADER + BARE, decl="{not json")
    unknown_top = make_world(HEADER + BARE,
                             decl={"exemptions": [], "extra": 1})
    unknown_key = make_world(
        HEADER + BARE,
        decl={"exemptions": [{"queue": "tech", "identity": "bare",
                              "declared": "R2276", "reason": "x",
                              "colour": "red"}]})
    dup = make_world(
        HEADER + BARE,
        decl={"exemptions": [
            {"queue": "tech", "identity": "bare", "declared": "R2276",
             "reason": "first"},
            {"queue": "tech", "identity": "bare", "declared": "R2276",
             "reason": "second"}]})
    try:
        unpinned = QE.audit(world, 2276)
        cli = run_cli(["--check", "--round", "R2276", "--root", world])
        codes = (refused(lambda: QE.audit(bad_json, 2276)),
                 refused(lambda: QE.audit(unknown_top, 2276)),
                 refused(lambda: QE.audit(unknown_key, 2276)),
                 refused(lambda: QE.audit(dup, 2276)))
    finally:
        for path in (world, bad_json, unknown_top, unknown_key, dup):
            drop_world(path)
    ok = (unpinned["declaration"] == "UNPINNED"
          and unpinned["entries"] == 0
          and unpinned["exempt_today"] == 0
          and unpinned["violation_count"] == 2
          and unpinned["still_debt"] == 2
          and unpinned["verdict"] == "EXEMPT-DEBT"
          and cli[0] == 2 and "UNPINNED" in cli[1]
          and codes == ("E_QRX_BAD_DECL", "E_QRX_BAD_DECL",
                        "E_QRX_BAD_DECL", "E_QRX_DUP"))
    if not ok:
        print("  measured: %r %r %r" % (unpinned, cli, codes), flush=True)
    check(ok, "AC-QRX1 pinned shape, UNPINNED honest, bad declarations refused")


def ac_qrx2():
    """Identity is the row, not its line: inserting lines changes nothing."""
    pair = ("tech", QE.identity_of(
        "- [ ] bare row one with no declaration at all"))
    decl = decl_for(pair)
    above = make_world(HEADER + BARE, decl=decl)
    moved = make_world(HEADER + "- [ ] a new row inserted above\n\n"
                       + BARE, decl=decl)
    reworded = make_world(HEADER
                          + "- [ ] bare row one REWORDED and different\n"
                          + "- [ ] bare row two with no declaration at all\n",
                          decl=decl)
    try:
        first = QE.audit(above, 2276)
        second = QE.audit(moved, 2276)
        third = QE.audit(reworded, 2276)
        second_exempt = None
        for row in second["rows"]:
            if row["status"] == "EXEMPT":
                second_exempt = row
        before = digest_tree(moved)
        QE.audit(moved, 2276)
        after = digest_tree(moved)
    finally:
        for path in (above, moved, reworded):
            drop_world(path)
    ok = (first["exempt_today"] == 1 and first["still_debt"] == 1
          and second["exempt_today"] == 1 and second["still_debt"] == 2
          # the exempt row moved down the file and is still the same row
          and first["rows"][0]["line"] == 5
          and second_exempt is not None
          and second_exempt["line"] == 7
          and second_exempt["identity"] == pair[1]
          and second_exempt["status"] == "EXEMPT"
          # the reworded row no longer matches: it is debt and the entry is
          # reported as unmatched instead of quietly exempting something else
          and third["exempt_today"] == 0 and third["still_debt"] == 2
          and third["unmatched_count"] == 1
          and third["unmatched"][0]["identity"] == pair[1]
          and before == after)
    if not ok:
        print("  measured: %r %r %r" % (first, second, third), flush=True)
    check(ok, "AC-QRX2 identity stable under line shifts, reword reopens debt")


def ac_qrx3():
    """A dated reason is mandatory: no reason, no date, no exemption."""
    pair = ("tech", QE.identity_of(
        "- [ ] bare row one with no declaration at all"))
    no_reason = make_world(HEADER + BARE, decl={
        "exemptions": [{"queue": pair[0], "identity": pair[1],
                        "declared": "R2276", "reason": "   "}]})
    no_date = make_world(HEADER + BARE, decl={
        "exemptions": [{"queue": pair[0], "identity": pair[1],
                        "declared": "Rxx", "reason": "why"}]})
    bad_until = make_world(HEADER + BARE, decl=decl_for(pair, "R2280",
                                                       until="R2270"))
    no_queue = make_world(HEADER + BARE, decl={
        "exemptions": [{"identity": pair[1], "declared": "R2276",
                        "reason": "why"}]})
    no_identity = make_world(HEADER + BARE, decl={
        "exemptions": [{"queue": "tech", "identity": "  ",
                        "declared": "R2276", "reason": "why"}]})
    try:
        codes = (refused(lambda: QE.audit(no_reason, 2276)),
                 refused(lambda: QE.audit(no_date, 2276)),
                 refused(lambda: QE.audit(bad_until, 2276)),
                 refused(lambda: QE.audit(no_queue, 2276)),
                 refused(lambda: QE.audit(no_identity, 2276)))
    finally:
        for path in (no_reason, no_date, bad_until, no_queue, no_identity):
            drop_world(path)
    ok = codes == ("E_QRX_BAD_REASON", "E_QRX_BAD_DATE", "E_QRX_BAD_DATE",
                   "E_QRX_BAD_DECL", "E_QRX_BAD_IDENTITY")
    if not ok:
        print("  measured: %r" % (codes,), flush=True)
    check(ok, "AC-QRX3 reason, declared round and until validated")


def ac_qrx4():
    """An expired exemption reads as debt again, naming the until round."""
    pair = ("tech", QE.identity_of(
        "- [ ] bare row one with no declaration at all"))
    world = make_world(HEADER + BARE, decl=decl_for(pair, "R2270",
                                                    until="R2270"))
    inside = make_world(HEADER + BARE, decl=decl_for(pair, "R2270",
                                                    until="R2276"))
    try:
        expired = QE.audit(world, 2276)
        cli = run_cli(["--check", "--round", "R2276", "--root", world])
        at_edge = QE.audit(inside, 2276)
    finally:
        drop_world(world)
        drop_world(inside)
    ok = (expired["exempt_expired"] == 1
          and expired["exempt_today"] == 0
          and expired["still_debt"] == 2
          and expired["verdict"] == "EXEMPT-DEBT"
          and expired["rows"][0]["status"] == "EXPIRED"
          and expired["rows"][0]["until"] == "R2270"
          and cli[0] == 2 and "expired=1" in cli[1]
          and "R2270" in cli[1]
          # the until round is inclusive: R2276 still holds at round R2276
          and at_edge["exempt_today"] == 1 and at_edge["still_debt"] == 1)
    if not ok:
        print("  measured: %r %r %r" % (expired, cli, at_edge), flush=True)
    check(ok, "AC-QRX4 expired exemption reads as debt, until named")


def ac_qrx5():
    """The gate is imported, counts reconcile, and both rows cannot share one."""
    world = make_world(HEADER + BARE,
                       decl=decl_for(("tech", QE.identity_of(
                           "- [ ] bare row one with no declaration at all"))))
    twin = make_world(
        HEADER + "- [ ] row about `docker-compose` one\n"
        + "- [ ] row about `docker-compose` two\n",
        decl=decl_for(("tech", "docker-compose")))
    imported = QE.QR is QR
    saved = QR.audit_root
    try:
        def fake(_root):
            return {"queues": [], "open_rows": 1, "done_rows": 0,
                    "gated_rows": 0, "claimable_rows": 1, "prefixed_rows": 0,
                    "violation_count": 1, "missing": [],
                    "violations": [{"file": "state/queue/tech.md", "line": 5,
                                    "prefix": None,
                                    "excerpt": "- [ ] patched row `zz-probe`"}],
                    "verdict": "GATE-DEBT"}
        QR.audit_root = fake
        patched = QE.audit(world, 2276)
    finally:
        QR.audit_root = saved
    try:
        live = QE.audit(world, 2276)
        ambiguous = refused(lambda: QE.audit(twin, 2276))
    finally:
        drop_world(world)
        drop_world(twin)
    with io.open(MODULE, "r", encoding="ascii") as handle:
        text = handle.read()
    no_second_gate = ("Criteria prefix" not in text
                      and "GATED_MARKERS" not in text)
    exact = QE.identity_of("- [ ] bare row one with no declaration at all")
    ok = (imported and no_second_gate
          # a patched audit flows straight through: the report follows it, and
          # the live entry no longer matches anything so it is unmatched and
          # the patched row is honest debt rather than silently exempted
          and patched["violation_count"] == 1
          and patched["unmatched_count"] == 1
          and patched["unmatched"][0]["identity"] == exact
          and patched["rows"][0]["identity"] == "zz-probe"
          and patched["rows"][0]["status"] == "DEBT"
          and patched["still_debt"] == 1
          # and the counts reconcile on the real reading
          and live["violation_count"] == 2
          and live["violation_count"] == live["exempt_today"] + live["still_debt"]
          and ambiguous == "E_QRX_AMBIGUOUS")
    if not ok:
        print("  measured: imported=%r gate=%r %r %r %r"
              % (imported, no_second_gate, patched, live, ambiguous),
              flush=True)
    check(ok, "AC-QRX5 gate imported, counts reconcile, ambiguity refused")


def ac_qrx6():
    """Purity, ASCII, no network, no clock, wired, and a real live reading."""
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen", "time.time",
               "datetime")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_queue_row_exempt.py" in wiring) \
        and ('"test_queue_row_exempt.py"), 6)' in wiring)
    live = run_cli(["--check", "--round", "R2276"])
    live_ok = False
    if live[0] in (0, 2):
        report = QE.audit(REPO, 2276)
        inside = [row for row in report["rows"]
                  if row["file"].startswith("state/queue/")]
        live_ok = bool(inside) and all(row["line"] > 0 for row in inside)
        for row in inside:
            path = os.path.join(REPO, row["file"].replace("/", os.sep))
            with io.open(path, "r", encoding="utf-8") as handle:
                lines = handle.read().split("\n")
            if not (0 < row["line"] <= len(lines)
                    and lines[row["line"] - 1].startswith("- [ ]")):
                live_ok = False
    ok = ascii_only and no_net and wired and live_ok
    if not ok:
        print("  measured: ascii=%r net=%r wired=%r live=%r %r"
              % (ascii_only, no_net, wired, live_ok, live), flush=True)
    check(ok, "AC-QRX6 pure ASCII, no clock, no network, wired, live real")


def main():
    print("queue_row_exempt suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_qrx1()
    ac_qrx2()
    ac_qrx3()
    ac_qrx4()
    ac_qrx5()
    ac_qrx6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())