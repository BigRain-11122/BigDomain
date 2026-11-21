"""round_evidence suite (R2255; criteria AC-RQE1..AC-RQE6 were pinned in
state/queue/tech.md as the R2248-c seed row BEFORE this code existed).)

What this proves: a round claims "SUITE PASS" in its own log item and the
file that proves it lives in qa/ under a round-suffixed name; the link was
only prose until now. This suite pins the three narrowings that keep the
reading honest - only an item's OWN round label counts (a body mention of
an older round invents no obligation), a round token in a file name must
not be a fragment of a longer number, and a claim exists only through the
pinned markers. The missing-evidence report carries the round and its
markers, an empty log is an honest EMPTY rather than a pass, an absent or
unparseable state.json fails closed with zero fabricated rounds, and the
whole reader is a pure read wired as its own reconcile label.

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

import round_evidence as RE  # noqa: E402

EXPECTED_CRITERIA = 8
MODULE = os.path.join(BASE, "round_evidence.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-round-evidence"
WIRED_EXPECT = '"test_round_evidence.py"), 8),'

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


def make_world(items, files=None, raw_state=None):
    """Build a temp root: src/os/state.json plus an optional qa/ tree."""
    world = tempfile.mkdtemp(prefix="bigdomain-rqe-")
    inner = os.path.join(world, "src", "os")
    os.makedirs(inner)
    target = os.path.join(inner, "state.json")
    if raw_state is None:
        body = json.dumps({"tick": 1, "log": list(items)})
    else:
        body = raw_state
    with io.open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(body)
    qa = os.path.join(world, "qa")
    os.makedirs(qa)
    for name in (files or []):
        with io.open(os.path.join(qa, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write("evidence body\n")
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


def ac_rqe1():
    """Only an item's own round label counts; a body mention invents nothing."""
    items = [
        "2026-10-29 R2300 (five-silence scan clean; the R2168 rule applied)",
        "R2300 tokens: local=~1k api=0 api_reason=test",
        "2026-10-29 R2301 (another item naming R2300 in the body)",
        "carry-forward rolling line R2302 (fold R593): prose without an "
        "owning label",
    ]
    rounds = RE.extract_rounds({"log": items})
    ok = ([row["round"] for row in rounds] == [2300, 2301]
          and rounds[0]["items"] == 2
          and rounds[1]["items"] == 1
          and RE.item_round(items[0]) == 2300
          and RE.item_round(items[1]) == 2300
          and RE.item_round(items[3]) is None)
    check(ok, "AC-RQE1 own round label extracted, body mentions ignored")


def ac_rqe2():
    """File mapping is a whole token, never a fragment of a longer number."""
    world = make_world(["2026-10-29 R2300 (x)"],
                       ["queue-row-R2300-a.log", "reconcile-all-R2300.log",
                        "notes-R23001.log", "unrelated.log"])
    try:
        mapping = RE.map_files(os.path.join(world, "qa"))
    finally:
        drop_world(world)
    ok = (sorted(mapping.keys()) == [2300, 23001]
          and sorted(mapping[2300]) == ["queue-row-R2300-a.log",
                                        "reconcile-all-R2300.log"]
          and mapping.get(23001) == ["notes-R23001.log"]
          and RE.file_round("queue-row-R2300-a.log") == 2300
          and RE.file_round("notes-R23001.log") == 23001
          and RE.file_round("unrelated.log") is None)
    if not ok:
        print("  measured: %r" % (mapping,), flush=True)
    check(ok, "AC-RQE2 whole round token mapped, fragments refused")


def ac_rqe3():
    """Claim detection is through the pinned markers only."""
    items = [
        "2026-10-29 R2300 SUITE PASS 6/6 double-run",
        "2026-10-29 R2301 RUNNER PASS 431/431 suites",
        "2026-10-29 R2302 the suite ran and everything looked fine",
    ]
    rounds = RE.extract_rounds({"log": items})
    by_round = dict((row["round"], row) for row in rounds)
    ok = (by_round[2300]["claims"] is True
          and by_round[2300]["markers"] == ["SUITE PASS"]
          and by_round[2301]["markers"] == ["RUNNER PASS"]
          and by_round[2302]["claims"] is False
          and by_round[2302]["markers"] == []
          and RE.CLAIM_MARKERS == ("SUITE PASS", "RUNNER PASS"))
    check(ok, "AC-RQE3 pinned claim markers, prose is not a claim")


def ac_rqe4():
    """A claiming round with no file is reported with its round and markers."""
    world = make_world([
        "2026-10-29 R2300 SUITE PASS 6/6",
        "2026-10-29 R2301 SUITE PASS 8/8",
        "2026-10-29 R2302 no claim here",
    ], ["suite-R2300-a.log"])
    try:
        report = RE.audit(world)
        code = run_cli(["--check", "--root", world])[0]
    finally:
        drop_world(world)
    ok = (report["verdict"] == "EVIDENCE-MISSING"
          and report["claiming_rounds"] == 2
          and report["with_files"] == 1
          and report["missing_count"] == 1
          and report["missing"] == [{"round": 2301,
                                     "markers": ["SUITE PASS"]}]
          and code == 2)
    if not ok:
        print("  measured: %r code=%r" % (report, code), flush=True)
    check(ok, "AC-RQE4 missing evidence reported, exit 2")


def ac_rqe5():
    """An empty log is EMPTY, and an absent or broken state fails closed."""
    empty = make_world([])
    broken = make_world([], raw_state="{not json")
    absent = tempfile.mkdtemp(prefix="bigdomain-rqe-")
    try:
        empty_report = RE.audit(empty)
        empty_code = run_cli(["--check", "--root", empty])[0]
        broken_code, broken_out, _ = run_cli(["--check", "--root", broken])
        absent_code, absent_out, _ = run_cli(["--check", "--root", absent])
    finally:
        drop_world(empty)
        drop_world(broken)
        drop_world(absent)
    ok = (empty_report["rounds"] == []
          and empty_report["verdict"] == "EMPTY"
          and empty_report["missing_count"] == 0
          and empty_code == 0
          and broken_code == 3 and "E_RQE_BAD_STATE" in broken_out
          and absent_code == 3 and "E_RQE_BAD_STATE" in absent_out)
    check(ok, "AC-RQE5 honest empty, absent and broken state exit 3")


def ac_rqe6():
    """Purity: no write, ASCII source, no network import, wired in."""
    world = make_world(["2026-10-29 R2300 SUITE PASS 6/6"],
                       ["suite-R2300-a.log"])
    before = digest_tree(world)
    try:
        run_cli(["--check", "--root", world])
        run_cli(["--check", "--root", world, "--json"])
        after = digest_tree(world)
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
    wired = (LABEL in wiring) and ("test_round_evidence.py" in wiring) \
        and (WIRED_EXPECT in wiring)
    first = run_cli(["--check", "--root", REPO, "--json"])
    second = run_cli(["--check", "--root", REPO, "--json"])
    pinned = list(json.loads(first[1]).keys())
    ok = (before == after and ascii_only and no_net and wired
          and first == second and pinned == list(RE.REPORT_KEYS))
    if not ok:
        print("  measured: write=%r ascii=%r net=%r wired=%r json=%r"
              % (before == after, ascii_only, no_net, wired,
                 pinned == list(RE.REPORT_KEYS)), flush=True)
    check(ok, "AC-RQE6 pure read, ASCII source, no network, wired, "
              "byte-stable json")


def write_archive(world, lines, name="state-log-archive-2026-11.md"):
    """Add a fold archive under logs/ (the fold's own folder and prefix)."""
    directory = os.path.join(world, "logs")
    if not os.path.isdir(directory):
        os.makedirs(directory)
    path = os.path.join(directory, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")
    return path


def ac_rqe7():
    """The folded rounds are judged too, and the live reading is unchanged."""
    items = ["2026-11-21 R3200 SUITE PASS 6/6"]
    world = make_world(items, ["suite-R3200.log"])
    try:
        # arm a: a folded claim with no file is reported, a quiet fold is not.
        write_archive(world, [
            "2026-09-01 R1255 RUNNER PASS legs=1",
            "2026-09-01 R1256 (narrative only, no claim marker)",
            "2026-09-01 R1256 tokens: local=~1k api=0",
        ])
        live_only = RE.audit(world)
        with_archive = RE.audit(world, include_archive=True)
        missing = [row["round"] for row in with_archive["missing"]]

        # arm b: the union sums items per round across both faces and orders
        # by round number.
        doubled = make_world(items, ["suite-R3200.log"])
        write_archive(doubled, [
            "2026-09-01 R3200 SUITE PASS 6/6",
            "R1255 RUNNER PASS legs=1",
        ])
        union = RE.audit(doubled, include_archive=True)
        row_3200 = [r for r in union["rounds"] if r["round"] == 3200]

        # arm c: the file fragment law holds in the folded face too.
        frag = make_world(items, ["suite-R3200.log", "suite-R22541.log"])
        write_archive(frag, ["R2254 SUITE PASS 1/1"])

        # arm d: an absent logs/ directory reads nothing rather than raising.
        absent = make_world(items, ["suite-R3200.log"])
        no_archive = RE.archive_rounds(absent)

        # arm e: the CLI flag, and its refusals.
        bad_flag = run_cli(["--check", "--root", world, "--bogus"])[0]
        no_check = run_cli(["--root", world, "--archive"])[0]
        code_archive, out_archive, _ = run_cli(
            ["--check", "--root", world, "--archive"])
        code_live, out_live, _ = run_cli(["--check", "--root", world])
        first = run_cli(["--check", "--root", world, "--archive", "--json"])
        second = run_cli(["--check", "--root", world, "--archive", "--json"])
        pinned = list(json.loads(first[1]).keys())

        # arm f: the archive folder and prefix are the fold's, not a copy that
        # may drift; state_seq owns the same two literals.
        with io.open(os.path.join(BASE, "state_seq.py"), "r",
                     encoding="utf-8") as handle:
            source = handle.read()
        agrees = ('ARCHIVE_DIR = ("logs",)' in source
                  and 'ARCHIVE_PREFIX = "state-log-archive-"' in source
                  and RE.ARCHIVE_DIR == ("logs",)
                  and RE.ARCHIVE_PREFIX == "state-log-archive-")

        ok = (live_only["missing_count"] == 0
              and live_only["verdict"] == "EVIDENCE-OK"
              and with_archive["missing_count"] == 1
              and missing == [1255]
              and with_archive["missing"][0]["markers"] == ["RUNNER PASS"]
              and with_archive["claiming_rounds"] == 2
              and [r["round"] for r in union["rounds"]] == [1255, 3200]
              and len(row_3200) == 1 and row_3200[0]["items"] == 2
              and union["log_items"] == 1 + 2
              and [r["round"] for r in RE.audit(frag, include_archive=True)
                   ["missing"]] == [2254]
              and no_archive == []
              and bad_flag == 2 and no_check == 2
              and code_archive == 2 and "MISSING R1255" in out_archive
              and code_live == 0 and "verdict=EVIDENCE-OK" in out_live
              and first == second and pinned == list(RE.REPORT_KEYS)
              and agrees)
        if not ok:
            print("  measured: live=%r archive=%r missing=%r union=%r "
                  "frag=%r noarch=%r cli=%r agrees=%r"
                  % (live_only["missing_count"], with_archive["missing_count"],
                     missing, [r["round"] for r in union["rounds"]],
                     [r["round"] for r in RE.audit(frag,
                                                   include_archive=True)
                      ["missing"]], no_archive,
                     (bad_flag, no_check, code_archive, code_live), agrees),
                  flush=True)
    finally:
        drop_world(world)
        drop_world(doubled)
        drop_world(frag)
        drop_world(absent)
    check(ok, "AC-RQE7 folded claims are judged, live reading byte-identical")


def ac_rqe8():
    """A missing round's own named qa/ files are published; verdict untouched."""
    items = ["2026-11-21 R3200 SUITE PASS 6/6"]
    world = make_world(items, ["suite-R3200.log"])
    try:
        # arm a: the judged universe is the audit's own missing set.
        live_clean = RE.named_evidence(world)
        write_archive(world, [
            "2026-09-01 R1255 RUNNER PASS legs=1 named qa/pass-1254.log",
            "2026-09-01 R1256 SUITE PASS 2/2 named qa/quiet.log",
            "2026-09-01 R1257 SUITE PASS 3/3 named qa/absent.log",
            "2026-09-01 R1258 SUITE PASS 4/4 named tasks.md",
        ])
        qa = os.path.join(world, "qa")
        for name, body in (("pass-1254.log", "SUITE PASS 9/9\n"),
                           ("quiet.log", "nothing claimed here\n")):
            with io.open(os.path.join(qa, name), "w", encoding="utf-8",
                         newline="\n") as handle:
                handle.write(body)
        audit_arch = RE.audit(world, include_archive=True)
        named = RE.named_evidence(world, include_archive=True)
        by_round = dict((row["round"], row) for row in named["named"])

        # arm b/c: pass, no-pass, an absent target and a name outside qa/.
        classified = (by_round.get(1255) == {"round": 1255,
                                             "files": ["pass-1254.log"],
                                             "pass": True}
                      and by_round.get(1256) == {"round": 1256,
                                                 "files": ["quiet.log"],
                                                 "pass": False}
                      and 1257 not in by_round and 1258 not in by_round)

        # arm d: the claim-to-file verdict is never moved by this reading.
        verdict_kept = (audit_arch["verdict"] == "EVIDENCE-MISSING"
                        and named["verdict"] == "NAMED-READING"
                        and [r["round"] for r in audit_arch["missing"]]
                        == [1255, 1256, 1257, 1258]
                        and named["rounds_missing"] == 4)

        # arm e: the CLI flag, its pinned shape and its refusals.
        no_check = run_cli(["--named", "--root", world, "--archive"])[0]
        first = run_cli(["--named", "--root", world, "--archive", "--json"])
        second = run_cli(["--named", "--root", world, "--archive", "--json"])
        pinned = list(json.loads(first[1]).keys())
        bad_flag = run_cli(["--named", "--root", world, "--bogus"])[0]
        broken = make_world([], raw_state="{not json")
        broken_code = run_cli(["--named", "--root", broken])[0]
        drop_world(broken)

        # arm f: the live face reaches all three buckets and obeys the sum law.
        live = RE.named_evidence(REPO, include_archive=True)
        consistent = (live["rounds_missing"] == live["named_on_disk"]
                      + live["no_named"]
                      and live["named_on_disk"] == (live["named_pass"]
                                                    + live["named_no_pass"])
                      and live["rounds_missing"] > 0
                      and live["named_on_disk"] > 0
                      and live["named_pass"] > 0
                      and live["no_named"] > 0)

        ok = (live_clean["rounds_missing"] == 0 and live_clean["named"] == []
              and classified and verdict_kept
              and no_check == 0 and first == second
              and pinned == list(RE.REPORT_NAMED_KEYS) and bad_flag == 2
              and broken_code == 3 and consistent)
        if not ok:
            print("  measured: live_clean=%r named=%r audit=%r classify=%r "
                  "cli=%r pinned=%r consistent=%r"
                  % (live_clean["rounds_missing"], named,
                     audit_arch["verdict"],
                     (by_round.get(1255), by_round.get(1256)),
                     (no_check, bad_flag, broken_code),
                     pinned == list(RE.REPORT_NAMED_KEYS), consistent),
                  flush=True)
    finally:
        drop_world(world)
    check(ok, "AC-RQE8 named evidence published, verdict untouched")


def main():
    print("round_evidence suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_rqe1()
    ac_rqe2()
    ac_rqe3()
    ac_rqe4()
    ac_rqe5()
    ac_rqe6()
    ac_rqe7()
    ac_rqe8()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())