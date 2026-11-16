"""suite_output_audit suite (R2845; criteria AC-SOA1..AC-SOA6 were pinned in
the R2845 row of src/os/backlog.md BEFORE this file existed).

What this proves: the census answers "can this suite emit the battery row?" by
reading SOURCE literals, which is wrong in both directions - a suite that
builds its row in a helper reads non_law, and a law literal on a branch that
never runs reads law. tools/suite_output_audit.py answers the same question
from the suite's real stdout through the runner's own invocation.

  - the law and the invocation are imported from the runner, never re-written;
  - four probe suites in a private world classify at output level as measured;
  - two runs of the same world read the same numbers;
  - the audit leaves the world's bytes and mtimes untouched (bytecode off);
  - a per-family bound is honoured and printed;
  - the registry declares this suite at six criteria.

Stdlib only, ASCII source, zero network, no clock. Exit 0 = all green.
"""

import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
ROOT = os.path.dirname(SRC)

EXPECTED_CRITERIA = 6
TOOL = os.path.join(ROOT, "tools", "suite_output_audit.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-suite-output-audit"

PASSES = 0
FAILS = 0

PROBES = {
    "probe_law.py": ('print("SUITE PASS 2/2")\n', 'print("PASS a")\nprint("PASS b")\n'),
    "probe_nostatus.py": ('print("SUITE 2/2")\n', 'print("PASS a")\n'),
    "probe_nostatus2.py": ('print("SUITE 3/3")\n', 'print("PASS a")\n'),
    "probe_nonumbers.py": ('print("SUITE PASS")\n', 'print("PASS a")\n'),
    "probe_other.py": ('print("SUITE civic: 3 criteria, 3 pass, 0 fail")\n',
                       'print("PASS a")\n'),
}


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def world(second_nostatus=False):
    """A private tree: shipped runner/census/audit + stub registry + probes.

    The pinned AC-SOA2 world carries exactly four probes (one per family); the
    second no_status probe exists only for the AC-SOA5 bound, so it is added on
    request rather than always, and no pinned number was restated to fit.
    """
    folder = tempfile.mkdtemp(prefix="soa-")
    tools = os.path.join(folder, "tools")
    sandbox = os.path.join(folder, "src", "sandbox")
    qa = os.path.join(folder, "qa")
    for path in (tools, sandbox, qa):
        os.makedirs(path)
    for name in ("battery_shard.py", "suite_closing_row_census.py",
                 "suite_output_audit.py", "suite_run_evidence.py", "qa_log.py"):
        src = os.path.join(ROOT, "tools", name)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(tools, name))
    rows = []
    probes = dict(PROBES)
    if not second_nostatus:
        del probes["probe_nostatus2.py"]
    for name in sorted(probes):
        body = PROBES[name][0] + PROBES[name][1]
        with io.open(os.path.join(sandbox, name), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write("# probe\n" + body)
        rows.append((name[:-3], name, 2))
    stub = (
        "BASE = %r\n"
        "SUITE_TIMEOUT_S = 60\n"
        "SUITE_TIMEOUT_OVERRIDES = {}\n"
        "SUITES = %r\n" % (sandbox, rows)
    )
    with io.open(os.path.join(sandbox, "reconcile_all.py"), "w",
                 encoding="utf-8", newline="\n") as handle:
        handle.write(stub)
    return folder


def cleanup(folder):
    shutil.rmtree(folder, ignore_errors=True)


def fingerprint(folder):
    rows = []
    for base, dirs, files in os.walk(folder):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(base, name)
            with io.open(path, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            rows.append((os.path.relpath(path, folder), digest,
                         os.stat(path).st_mtime_ns))
    return rows


def audit(folder, extra):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, os.path.join(folder, "tools", "suite_output_audit.py"),
         "--root", folder] + extra,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", env=env, timeout=180)
    return proc.returncode, proc.stdout or ""


FOUR = ["--family", "law_direct", "--family", "no_status",
        "--family", "no_numbers", "--family", "other"]


def ac_soa1():
    text = io.open(TOOL, encoding="utf-8").read()
    no_own_law = re.search(r"re\.compile\([^)]*SUITE", text) is None
    uses_law = "SUITE_LINE" in text and "runner.run_one(" in text
    ok = no_own_law and uses_law
    if not ok:
        print("  measured: own_law=%r uses_law=%r" % (not no_own_law, uses_law),
              flush=True)
    check(ok, "AC-SOA1 law and invocation come from the runner, not a copy")


def ac_soa2():
    folder = world()
    try:
        code, out = audit(folder, FOUR)
        ok = (code == 0 and "law_emit=1 non_law=3" in out
              and "law=yes" in out and "row=none" not in out.split("law=no")[1])
        if not ok:
            print("  measured rc=%d out=%r" % (code, out[-600:]), flush=True)
        check(ok, "AC-SOA2 private world reads law_emit=1 non_law=3 with rows")
    finally:
        cleanup(folder)


def ac_soa3():
    folder = world()
    try:
        _, one = audit(folder, FOUR)
        _, two = audit(folder, FOUR)
        totals = [ln for ln in one.splitlines() if ln.startswith("AUDIT TOTAL")]
        totals2 = [ln for ln in two.splitlines() if ln.startswith("AUDIT TOTAL")]
        ok = len(totals) == 1 and totals == totals2
        if not ok:
            print("  measured one=%r two=%r" % (totals, totals2), flush=True)
        check(ok, "AC-SOA3 two runs of one world read identical totals")
    finally:
        cleanup(folder)


def ac_soa4():
    folder = world()
    try:
        before = fingerprint(folder)
        audit(folder, FOUR)
        after = fingerprint(folder)
        changed = [row[0] for row in before if row not in after]
        added = [row[0] for row in after if row not in before]
        ok = before == after
        if not ok:
            print("  measured changed=%r added=%r" % (changed, added), flush=True)
        check(ok, "AC-SOA4 audit leaves the world bytes and mtimes untouched")
    finally:
        cleanup(folder)


def ac_soa5():
    folder = world(second_nostatus=True)
    try:
        code, out = audit(folder, ["--family", "no_status",
                                  "--per-family-limit", "1"])
        head = "AUDIT family=no_status total=2 selected=1 law_emit=0 non_law=1 red=0"
        ok = code == 0 and head in out
        if not ok:
            print("  measured rc=%d head_missing=%r" % (code, head), flush=True)
        check(ok, "AC-SOA5 a per-family bound is honoured and printed")
    finally:
        cleanup(folder)


def ac_soa6():
    folder = world()
    try:
        _, out = audit(folder, FOUR)
        noted = "AUDIT note=OUTPUT-LEVEL" in out
    finally:
        cleanup(folder)
    runner_text = io.open(RUNNER, encoding="utf-8").read()
    pattern = re.compile(
        r"\(" + '"' + LABEL + '"' + r",\s*\n\s*os\.path\.join\([^)]*\),\s*"
        r"(\d+)\)")
    match = pattern.search(runner_text)
    declared = int(match.group(1)) if match else -1
    ok = noted and declared == EXPECTED_CRITERIA
    if not ok:
        print("  measured noted=%r declared=%r" % (noted, declared), flush=True)
    check(ok, "AC-SOA6 boundary printed and the registry declares %d criteria"
          % EXPECTED_CRITERIA)


def main():
    print("suite output audit suite (expected criteria %d)"
          % EXPECTED_CRITERIA, flush=True)
    ac_soa1()
    ac_soa2()
    ac_soa3()
    ac_soa4()
    ac_soa5()
    ac_soa6()
    verdict = "SUITE PASS" if FAILS == 0 else "SUITE FAIL"
    print("%s %d/%d" % (verdict, PASSES, PASSES + FAILS), flush=True)
    if (PASSES + FAILS) != EXPECTED_CRITERIA:
        print("SUITE FAIL criteria count %d != %d"
              % (PASSES + FAILS, EXPECTED_CRITERIA), flush=True)
        return 1
    return 0 if FAILS == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
