"""Suite: opsreview gate AC checks (backlog R604, AC-OR1..OR7).

Pre-registered criteria XD1..XD10 live in criteria.json; the gate is
xidudu_ops_compliance_gate.py. This suite exercises the gate logic on
synthetic fixtures (fixtures.json - synthetic texts, NOT copies of the
real spec; the live run against the real spec is captured separately
in qa/opsreview-R604.log).

AC-OR1 compliant fixture -> exit 0, 10 PASS, 0 GAP, 0 FAIL
AC-OR2 v1-like fixture -> exit 1, gaps exactly XD4/XD6/XD7/XD8
AC-OR3 redline fixture -> exit 2 (forbidden patterns detected)
AC-OR4 missing spec path -> exit 3 (SKIP, honest no-crash)
AC-OR5 criteria registry: 10 unique ids XD1..XD10, severities sane
AC-OR6 gate output carries an evidence line per criterion (XDn lines)
AC-OR7 idempotence: two identical runs -> same exit + same SUMMARY
"""

import json
import os
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(BASE, "xidudu_ops_compliance_gate.py")

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
    else:
        FAILS += 1
    print("%s %s" % ("PASS" if ok else "FAIL", label), flush=True)


def run_gate(spec_path, log_path):
    proc = subprocess.run(
        [sys.executable, GATE, "--spec", spec_path, "--log", log_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", timeout=120)
    out = proc.stdout or ""
    if os.path.isfile(log_path):
        with open(log_path, encoding="utf-8") as fh:
            out += "\n" + fh.read()
    return proc.returncode, out


def main():
    with open(os.path.join(BASE, "criteria.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    with open(os.path.join(BASE, "fixtures.json"), encoding="utf-8") as fh:
        fixtures = json.load(fh)
    crits = data["criteria"]
    tmpdir = tempfile.mkdtemp(prefix="opsreview-")

    def write_fixture(name):
        path = os.path.join(tmpdir, name + ".md")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(fixtures[name])
        return path

    # AC-OR5: registry integrity (judged first: the rest depends on it)
    ids = [c["id"] for c in crits]
    expected_ids = ["XD%d" % n for n in range(1, 11)]
    check(len(ids) == 10 and sorted(ids) == sorted(expected_ids)
          and len(set(ids)) == 10
          and all(c.get("on_missing", "GAP") in ("GAP", "FAIL")
                  for c in crits),
          "AC-OR5 registry: 10 criteria, unique ids XD1..XD10, "
          "severities GAP/FAIL only")

    # AC-OR1: compliant fixture -> exit 0, all PASS
    code, out = run_gate(write_fixture("compliant"),
                         os.path.join(tmpdir, "log1.txt"))
    check(code == 0 and "SUMMARY: PASS=10 GAP=0 FAIL=0 criteria=10" in out,
          "AC-OR1 compliant fixture: exit=%d, 10 PASS / 0 GAP / 0 FAIL"
          % code)

    # AC-OR2: v1-like fixture -> exit 1, gaps exactly XD4/XD6/XD7/XD8
    code, out = run_gate(write_fixture("v1_like"),
                         os.path.join(tmpdir, "log2.txt"))
    gap_ids = sorted(set(
        line.split()[1] for line in out.splitlines()
        if line.startswith("GAP XD")))
    check(code == 1 and gap_ids == ["XD4", "XD6", "XD7", "XD8"]
          and "SUMMARY: PASS=6 GAP=4 FAIL=0 criteria=10" in out,
          "AC-OR2 v1-like fixture: exit=%d, gaps=%s"
          % (code, ",".join(gap_ids)))

    # AC-OR3: redline fixture -> exit 2
    code, out = run_gate(write_fixture("redline"),
                         os.path.join(tmpdir, "log3.txt"))
    check(code == 2 and "FAIL XD" in out and "RED_LINE_FAIL" in out,
          "AC-OR3 redline fixture: exit=%d, FAIL lines present" % code)

    # AC-OR4: missing spec path -> exit 3
    code, out = run_gate(os.path.join(tmpdir, "no-such-spec.md"),
                         os.path.join(tmpdir, "log4.txt"))
    check(code == 3 and "SPEC_MISSING" in out,
          "AC-OR4 missing spec: exit=%d, SKIP verdict" % code)

    # AC-OR6: one labeled line per criterion id in gate output
    code, out = run_gate(write_fixture("v1_like"),
                         os.path.join(tmpdir, "log6.txt"))
    missing_labels = [cid for cid in ids
                      if not any(ln.startswith(("PASS %s " % cid,
                                               "GAP %s " % cid,
                                               "FAIL %s " % cid))
                                 for ln in out.splitlines())]
    check(not missing_labels,
          "AC-OR6 every criterion has a labeled result line (%d ids)"
          % len(ids))

    # AC-OR7: idempotence - two identical runs agree (note: out merges
    # stdout and the utf-8 log, so the SUMMARY line appears twice per
    # run; compare deduped sets)
    path = write_fixture("v1_like")
    code_a, out_a = run_gate(path, os.path.join(tmpdir, "log7a.txt"))
    code_b, out_b = run_gate(path, os.path.join(tmpdir, "log7b.txt"))
    sum_a = set(ln for ln in out_a.splitlines()
                if ln.startswith("SUMMARY:"))
    sum_b = set(ln for ln in out_b.splitlines()
                if ln.startswith("SUMMARY:"))
    check(code_a == code_b == 1 and sum_a == sum_b and len(sum_a) == 1,
          "AC-OR7 idempotence: two runs same exit=%d and same SUMMARY"
          % code_a)

    print("suite opsreview: %d/7 green" % PASSES, flush=True)
    return 0 if FAILS == 0 and PASSES == 7 else 1


if __name__ == "__main__":
    sys.exit(main())
