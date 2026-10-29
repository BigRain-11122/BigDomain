"""state_seq suite (R2257; criteria AC-SEQ1..AC-SEQ6 were pinned in
state/queue/tech.md as the R2248-d seed row BEFORE this code existed).

What this proves: the tick climbs every window and every window writes a log
item labelled with its own round, but the two were never compared, so a
skipped round, a reused label or a label that goes backwards was invisible.
This suite pins the reading - the tick is an int read or a fail-closed
refusal, only an item's OWN label counts (the round_evidence law, imported
not re-implemented), gaps are measured only inside the known span, repeats
and backwards are separate readings, and the CLI codes and purity hold.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
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

import state_seq as SS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "state_seq.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-state-seq"
WIRED_EXPECT = '"test_state_seq.py"), 6),'

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
    world = tempfile.mkdtemp(prefix="bigdomain-seq-")
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
            try:
                with io.open(full, "rb") as handle:
                    body = handle.read()
            except (IOError, OSError):
                body = b"<unreadable>"
            parts.append((full, len(body), body))
    return parts


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + list(args),
                          cwd=BASE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def ac_seq1():
    """Tick is read as an int with a lead, or refused with exit 3."""
    world = make_world(["2026-10-29 R2250 first",
                        "2026-10-29 R2251 second"], tick=2253)
    try:
        report = SS.audit(world)
        rc_good = run_cli(["--check", "--root", world])[0]
        lead_ok = report["tick"] == 2253 and report["tick_lead"] == 2

        bad_tick = make_world([], tick="2253")
        fabricated = None
        raised = False
        try:
            rc_bad, body_bad = run_cli(["--check", "--root", bad_tick])
            try:
                fabricated = SS.audit(bad_tick)
            except SS.StateSeqError:
                raised = True
        finally:
            drop_world(bad_tick)

        broken = make_world([], raw_state="{not json")
        try:
            rc_broken = run_cli(["--check", "--root", broken])[0]
        finally:
            drop_world(broken)
    finally:
        drop_world(world)
    ok = (lead_ok and report["verdict"] == "SEQUENCE-OK" and rc_good == 0
          and rc_bad == 3 and "E_SEQ_BAD_STATE" in body_bad
          and raised and fabricated is None
          and rc_broken == 3)
    if not ok:
        print("  measured: lead=%r verdict=%r good=%r bad=%r broken=%r"
              % (lead_ok, report["verdict"], rc_good, rc_bad, rc_broken),
              flush=True)
    check(ok, "AC-SEQ1 tick read as int with tick_lead, bad tick fails closed")


def ac_seq2():
    """Only an item's own label counts; body mentions invent nothing."""
    world = make_world([
        "2026-10-29 R2100 first, unlike the R1900 mixed-tree rule",
        "2026-10-29 R2101 second (the R1888 precedent again)",
        "R2102 tokens: local=~1k api=0",
        "a note with no label at all, R9999 in the middle of a sentence",
    ], tick=2103)
    try:
        report = SS.audit(world)
    finally:
        drop_world(world)
    ok = (report["labels"] == [2100, 2101, 2102]
          and report["distinct"] == 3
          and report["smallest"] == 2100
          and report["largest"] == 2102)
    if not ok:
        print("  measured labels=%r" % (report["labels"],), flush=True)
    check(ok, "AC-SEQ2 only the item's own label counts, log order kept")


def ac_seq3():
    """Gaps are named inside the known span and drop the verdict."""
    world = make_world(["2026-10-29 R2200 a",
                        "2026-10-29 R2201 b",
                        "2026-10-29 R2204 c"], tick=2205)
    try:
        report = SS.audit(world)
        rc = run_cli(["--check", "--root", world])[0]
        body = run_cli(["--check", "--root", world])[1]
    finally:
        drop_world(world)
    # Nothing is reported before the first or after the last label.
    ok = (report["gaps"] == [2202, 2203]
          and report["verdict"] == "SEQUENCE-BROKEN"
          and rc == 2 and "GAP R2202" in body and "GAP R2203" in body
          and "GAP R2199" not in body and "GAP R2205" not in body)
    if not ok:
        print("  measured gaps=%r verdict=%r rc=%r"
              % (report["gaps"], report["verdict"], rc), flush=True)
    check(ok, "AC-SEQ3 gaps named inside the span, verdict off OK")


def ac_seq4():
    """Repeats and backwards are separate readings, both with detail.

    A round writes several items in a row by design (narrative, ledger,
    self-heal note), so a contiguous block is NOT a repeat; only a label
    that comes back after another round intervened is one. This criterion
    was corrected at R2257 after the live reading flagged 15 of 15 rounds
    under the first wording - disclosed in the criteria row.
    """
    world = make_world(["2026-10-29 R2300 a",
                        "2026-10-29 R2301 b",
                        "2026-10-29 R2301 c",
                        "2026-10-29 R2301 d",
                        "2026-10-29 R2300 e"], tick=2302)
    try:
        report = SS.audit(world)
        rc = run_cli(["--check", "--root", world])[0]
        body = run_cli(["--check", "--root", world])[1]
    finally:
        drop_world(world)
    ok = (report["repeats"] == [{"round": 2300, "count": 2}]
          and report["backwards"] == [{"index": 4, "round": 2300,
                                       "previous": 2301}]
          and report["gaps"] == []
          and report["verdict"] == "SEQUENCE-BROKEN" and rc == 2
          and "REPEAT R2300 count=2" in body
          and "REPEAT R2301" not in body
          and "BACKWARDS index=4 R2300 after R2301" in body)
    if not ok:
        print("  measured repeats=%r backwards=%r gaps=%r"
              % (report["repeats"], report["backwards"], report["gaps"]),
              flush=True)
    check(ok, "AC-SEQ4 repeats and backwards reported separately")


def ac_seq5():
    """CLI codes: 0 clean/EMPTY, 2 broken or bad flags, 3 bad state."""
    good = make_world(["2026-10-29 R2400 a", "2026-10-29 R2401 b"],
                      tick=2402,
                      queue={"tech.md": "- [x] [done 2026-10-29 R2400] x\n"
                                        "- [ ] still open\n"})
    empty = make_world([], tick=5)
    broken = make_world(["2026-10-29 R2410 a", "2026-10-29 R2412 b"],
                        tick=2413)
    try:
        rc_good, body_good = run_cli(["--check", "--root", good])
        rc_empty, body_empty = run_cli(["--check", "--root", empty])
        rc_broken, _body = run_cli(["--check", "--root", broken])
        rc_unknown, _b2 = run_cli(["--check", "--root", good, "--bogus"])
        rc_missing_arg, _b3 = run_cli(["--root", good])
        report = SS.audit(good)
    finally:
        for world in (good, empty, broken):
            drop_world(world)
    ok = (rc_good == 0 and "SEQUENCE-OK" in body_good
          and rc_empty == 0 and "EMPTY" in body_empty
          and rc_broken == 2 and rc_unknown == 2 and rc_missing_arg == 2
          and report["queue_done"] == 1 and report["queue_only"] == [])
    if not ok:
        print("  measured good=%r empty=%r broken=%r unknown=%r missing=%r "
              "queue_done=%r queue_only=%r"
              % (rc_good, rc_empty, rc_broken, rc_unknown, rc_missing_arg,
                 report["queue_done"], report["queue_only"]), flush=True)
    check(ok, "AC-SEQ5 CLI codes 0/2/3 and the queue stamp counted")


def ac_seq6():
    """Purity: no write, ASCII source, no network import, wired in."""
    world = make_world(["2026-10-29 R2500 SUITE PASS 6/6",
                        "2026-10-29 R2501 b"], tick=2502,
                       queue={"tech.md": "- [x] [done 2026-10-29 R2501] x\n"
                                        "- [x] [done 2026-10-29 R2490] y\n"})
    before = digest_tree(world)
    try:
        run_cli(["--check", "--root", world])
        run_cli(["--check", "--root", world, "--json"])
        after = digest_tree(world)
        report = SS.audit(world)
    finally:
        drop_world(world)
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    ascii_only = True
    try:
        raw.decode("ascii")
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("ascii", "replace")
    blocked = ("import socket", "import urllib", "import http",
               "import requests", "import asyncio", "urlopen")
    no_net = not any(token in text for token in blocked)
    with io.open(RUNNER, "r", encoding="utf-8") as handle:
        wiring = handle.read()
    wired = (LABEL in wiring) and ("test_state_seq.py" in wiring) \
        and (WIRED_EXPECT in wiring)
    first = run_cli(["--check", "--root", REPO, "--json"])
    second = run_cli(["--check", "--root", REPO, "--json"])
    pinned = list(json.loads(first[1]).keys())
    ok = (before == after and ascii_only and no_net and wired
          and first == second and pinned == list(SS.REPORT_KEYS)
          and report["queue_only"] == [2490])
    if not ok:
        print("  measured: write=%r ascii=%r net=%r wired=%r json=%r "
              "queue_only=%r"
              % (before == after, ascii_only, no_net, wired,
                 pinned == list(SS.REPORT_KEYS), report["queue_only"]),
              flush=True)
    check(ok, "AC-SEQ6 pure read, ASCII source, no network, wired, "
              "byte-stable json, queue_only named")


def main():
    print("state_seq suite (expected criteria %d)" % EXPECTED_CRITERIA,
          flush=True)
    ac_seq1()
    ac_seq2()
    ac_seq3()
    ac_seq4()
    ac_seq5()
    ac_seq6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())