"""QA evidence-directory mtime probe (BigDomain P2 tech-queue item
"suite_matrix discovery-face live mtime normalization window",
R1727; seed = R1709 tie-break coverage, claim row in
state/queue/tech.md registers AC-LN1..AC-LN8 BEFORE this code).

What this tool answers: after a tracked-relation rebuild (git clone /
git checkout / sync tooling) the qa/ evidence files may all land on
one flattened mtime. R1709 pinned the discovery tie-break semantics
with synthetic same-mtime fixtures; this probe makes the live
empirical window mechanically re-runnable on ANY real state:

    python qa_mtime_probe.py                 # live qa/ reading
    python qa_mtime_probe.py --dir PATH      # any evidence dir
    python qa_mtime_probe.py --selftest      # sandbox fixtures

The discovery face itself is imported live from src/sandbox/
suite_matrix.py (single source of truth, reference never copy); this
probe only reads directories and never writes inside any qa/ dir.
Pre-registered decision rule (AC-LN4):
  * distinct_mtime == 1 (all files one mtime) -> NORMALIZED-FULL,
    winner must equal the name-ascending minimum among eligible
    files (R1709 fixture cross-verification) and the window closes;
  * winner's mtime group holds >= 2 eligible files -> TIE-EXERCISED,
    live tie-break assertion must pass (fixture-live cross-check),
    window stays open awaiting a fully normalized state (honest);
  * otherwise -> NO-LIVE-TIE, honest reading, window stays open
    (lawful negative, probe re-runnable after any future rebuild);
  * zero eligible evidence -> NO-ELIGIBLE-EVIDENCE, refusal exit 3
    (runner_profile AC-RP2 exactly-one family).
Exit codes: 0 all assertions pass; 2 any assertion fails
(fail-closed); 3 no eligible evidence (refusal, not a failure).

Evidence: qa/suite-matrix-livemtime-R1727.log (three sections:
selftest + live qa/ + real git-worktree checkout rebuild).
"""

import argparse
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))   # .../src/os
SRC = os.path.dirname(BASE)                          # .../src
ROOT = os.path.dirname(SRC)                          # repo root
SANDBOX = os.path.join(SRC, "sandbox")
sys.path.insert(0, SANDBOX)
import suite_matrix as SM  # discovery face, single source of truth

NET_IMPORTS = ("urllib", "requests", "socket", "http", "ftplib",
               "xmlrpc", "smtplib", "asyncio")
CALLS = 3
SELF_PATH = os.path.abspath(__file__)


def _candidate_names(qa_dir):
    """Same candidate face as default_evidence: *.log except the
    self-evidence suite-matrix-* prefix (skip family preserved)."""
    names = [n for n in os.listdir(qa_dir)
             if n.endswith(".log") and not n.startswith("suite-matrix-")]
    return sorted(names)


def probe(qa_dir):
    """Read-only probe of one evidence directory. Returns a report
    dict plus an ok flag (calls_identical). Zero writes, zero
    fabrication: every number is measured or honestly absent."""
    all_files = [n for n in os.listdir(qa_dir)
                 if os.path.isfile(os.path.join(qa_dir, n))]
    groups = {}
    for name in all_files:
        key = os.path.getmtime(os.path.join(qa_dir, name))
        groups.setdefault(key, []).append(name)
    distinct = len(groups)
    largest = max((len(v) for v in groups.values()), default=0)
    candidates = _candidate_names(qa_dir)

    saved = SM.QA_DIR
    SM.QA_DIR = qa_dir
    try:
        winners = [SM.default_evidence() for _ in range(CALLS)]
    finally:
        SM.QA_DIR = saved
    winner = winners[0]
    identical = all(w == winner for w in winners)

    report = {
        "dir": qa_dir,
        "file_count": len(all_files),
        "candidate_count": len(candidates),
        "distinct_mtime": distinct,
        "largest_tie_group": largest,
        "winner": winner,
        "winner_calls_identical": identical,
        "tie_peers": 0,
        "verdict": None,
        "expected_winner": None,
    }
    if winner is None:
        report["verdict"] = "NO-ELIGIBLE-EVIDENCE"
        return report, identical

    winner_name = os.path.basename(winner)
    wkey = os.path.getmtime(winner)
    eligible = []
    for name in groups.get(wkey, []):
        if (name.endswith(".log")
                and not name.startswith("suite-matrix-")
                and SM._evidence_eligible(os.path.join(qa_dir, name))):
            eligible.append(name)
    report["tie_peers"] = len(eligible) - 1
    if distinct == 1:
        report["verdict"] = "NORMALIZED-FULL"
        report["expected_winner"] = min(eligible) if eligible else None
    elif report["tie_peers"] >= 1:
        report["verdict"] = "TIE-EXERCISED"
        report["expected_winner"] = min(eligible)
    else:
        report["verdict"] = "NO-LIVE-TIE"
    return report, identical


def render(report):
    lines = []
    lines.append("dir: " + str(report["dir"]))
    lines.append("files: %d (candidates %d)"
                 % (report["file_count"], report["candidate_count"]))
    lines.append("distinct_mtime: %d" % report["distinct_mtime"])
    lines.append("largest_tie_group: %d" % report["largest_tie_group"])
    lines.append("winner: %s" % report["winner"])
    lines.append("winner_calls_identical: %s (%d/%d)"
                 % (report["winner_calls_identical"], CALLS, CALLS))
    lines.append("tie_peers: %d" % report["tie_peers"])
    lines.append("verdict: %s" % report["verdict"])
    return lines


def _assertions(report):
    """AC-LN5 fail-closed assertion set. Returns (ok, notes)."""
    notes = []
    if not report["winner_calls_identical"]:
        notes.append("FAIL determinism: %d consecutive calls differ"
                     % CALLS)
        return False, notes
    verdict = report["verdict"]
    if verdict == "NO-ELIGIBLE-EVIDENCE":
        notes.append("no eligible evidence in probed dir")
        return True, notes
    if verdict in ("NORMALIZED-FULL", "TIE-EXERCISED"):
        got = os.path.basename(report["winner"])
        want = report["expected_winner"]
        if got != want:
            notes.append("FAIL tie-break: winner %s != name-asc min %s"
                         % (got, want))
            return False, notes
        notes.append("tie-break assert PASS: winner==name-asc min "
                     "among eligible@winner-mtime (%s)" % want)
    else:
        notes.append("no live tie at winner mtime: tie-break not "
                     "exercised this state (honest reading)")
    return True, notes


def _write_valid(path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("RUNNER PASS (3/3 suites green, reconcile controls "
                 "6/6, 12.3s)\n")
        for label in ("alpha", "beta", "gamma"):
            fh.write("PASS suite %s exit=0 pass-lines=1 fail-lines=0 "
                     "criteria=1 1.0s\n" % label)


def _write_invalid(path):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("RUNNER FAIL (2/3 suites green, reconcile controls "
                 "5/6, 9.9s)\n")
        fh.write("FAIL suite broken exit=1 pass-lines=0 fail-lines=2 "
                 "criteria=1 1.0s\n")


def _selftest():
    """AC-LN6 sandbox fixtures: zero live-tree writes, mkdtemp,
    full cleanup. Each case asserts the report fields."""
    tmp = tempfile.mkdtemp(prefix="qa_mtime_probe_st_")
    checks = []

    def check(name, cond):
        checks.append((name, bool(cond)))

    try:
        # Fixture 1: full normalization (AC-TIE1 semantics, 4 files
        # one mtime, ineligible sorts first and must be skipped).
        d1 = os.path.join(tmp, "f1")
        os.makedirs(d1)
        _write_valid(os.path.join(d1, "b-good.log"))
        _write_valid(os.path.join(d1, "c-good.log"))
        _write_valid(os.path.join(d1, "d-good.log"))
        _write_invalid(os.path.join(d1, "a-fail.log"))
        stamp = 1700000000.0
        for n in os.listdir(d1):
            os.utime(os.path.join(d1, n), (stamp, stamp))
        r1, _ = probe(d1)
        check("f1 distinct==1", r1["distinct_mtime"] == 1)
        check("f1 verdict NORMALIZED-FULL",
              r1["verdict"] == "NORMALIZED-FULL")
        check("f1 winner==b-good.log",
              os.path.basename(r1["winner"]) == "b-good.log")
        check("f1 tie_peers==2", r1["tie_peers"] == 2)
        ok1, _ = _assertions(r1)
        check("f1 assertions pass", ok1)

        # Fixture 2: tie group with ineligible name-sorted first
        # (AC-TIE2 semantics: skip in-group, never fall to old group).
        d2 = os.path.join(tmp, "f2")
        os.makedirs(d2)
        _write_valid(os.path.join(d2, "m-old.log"))
        _write_invalid(os.path.join(d2, "a-fail.log"))
        _write_valid(os.path.join(d2, "z-tie.log"))
        os.utime(os.path.join(d2, "m-old.log"),
                 (stamp - 100.0, stamp - 100.0))
        os.utime(os.path.join(d2, "a-fail.log"), (stamp, stamp))
        os.utime(os.path.join(d2, "z-tie.log"), (stamp, stamp))
        r2, _ = probe(d2)
        check("f2 distinct==2", r2["distinct_mtime"] == 2)
        check("f2 winner==z-tie.log (skip a-fail, not m-old)",
              os.path.basename(r2["winner"]) == "z-tie.log")
        check("f2 verdict NO-LIVE-TIE", r2["verdict"] == "NO-LIVE-TIE")
        ok2, _ = _assertions(r2)
        check("f2 assertions pass", ok2)

        # Fixture 3: two eligible tied at the newest mtime ->
        # TIE-EXERCISED, name-ascending minimum wins (live assertion).
        d3 = os.path.join(tmp, "f3")
        os.makedirs(d3)
        _write_valid(os.path.join(d3, "m-old2.log"))
        _write_valid(os.path.join(d3, "s-one.log"))
        _write_valid(os.path.join(d3, "t-two.log"))
        os.utime(os.path.join(d3, "m-old2.log"),
                 (stamp - 100.0, stamp - 100.0))
        for n in ("s-one.log", "t-two.log"):
            os.utime(os.path.join(d3, n), (stamp, stamp))
        r3, _ = probe(d3)
        check("f3 verdict TIE-EXERCISED",
              r3["verdict"] == "TIE-EXERCISED")
        check("f3 winner==s-one.log",
              os.path.basename(r3["winner"]) == "s-one.log")
        check("f3 tie_peers==1", r3["tie_peers"] == 1)
        ok3, _ = _assertions(r3)
        check("f3 assertions pass", ok3)

        # Fixture 4: zero eligible evidence -> refusal verdict.
        d4 = os.path.join(tmp, "f4")
        os.makedirs(d4)
        _write_invalid(os.path.join(d4, "a-bad.log"))
        r4, _ = probe(d4)
        check("f4 verdict NO-ELIGIBLE-EVIDENCE",
              r4["verdict"] == "NO-ELIGIBLE-EVIDENCE")
    finally:
        for sub in os.listdir(tmp):
            full = os.path.join(tmp, sub)
            for n in os.listdir(full):
                os.remove(os.path.join(full, n))
            os.rmdir(full)
        os.rmdir(tmp)

    # Hygiene face (AC-LN7): own source pure ASCII + no network
    # imports on true import lines.
    with open(SELF_PATH, "rb") as fh:
        raw = fh.read()
    bad_bytes = sum(1 for b in raw if b > 127)
    check("hygiene pure-ascii source", bad_bytes == 0)
    net_hits = []
    with open(SELF_PATH, "r", encoding="ascii") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped.startswith("import ") or \
                    stripped.startswith("from "):
                for lib in NET_IMPORTS:
                    if lib + " " in stripped or stripped.endswith(lib):
                        net_hits.append(stripped)
    check("hygiene zero network imports", not net_hits)

    print("SELFTEST %s: %d checks, %d pass, %d fail"
          % ("PASS" if all(ok for _, ok in checks) else "FAIL",
             len(checks), sum(1 for _, ok in checks if ok),
             sum(1 for _, ok in checks if not ok)))
    for name, ok in checks:
        print("  %s %s" % ("PASS" if ok else "FAIL", name))
    return 0 if all(ok for _, ok in checks) else 2


def main():
    parser = argparse.ArgumentParser(
        description="QA evidence-dir mtime probe (R1727, AC-LN1..8)")
    parser.add_argument("--dir", default=os.path.join(ROOT, "qa"),
                        help="evidence dir to probe (default: qa/)")
    parser.add_argument("--selftest", action="store_true",
                        help="run sandbox fixtures then exit")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()

    if not os.path.isdir(args.dir):
        print("E_BAD_DIR: not a directory: %s" % args.dir)
        return 2
    report, _ = probe(args.dir)
    for line in render(report):
        print(line)
    ok, notes = _assertions(report)
    for note in notes:
        print("note: " + note)
    if not ok:
        print("PROBE FAIL: assertions failed (fail-closed)")
        return 2
    if report["verdict"] == "NO-ELIGIBLE-EVIDENCE":
        print("PROBE REFUSED: no eligible evidence (exit 3 family)")
        return 3
    print("PROBE PASS verdict=%s" % report["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
