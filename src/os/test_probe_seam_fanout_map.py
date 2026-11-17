"""AC-PSFM1..AC-PSFM6 suite for tools/probe_seam_fanout_map.py (R2870).

The six criteria were pinned in state/queue/tech.md at R2870 BEFORE this file
existed. R2867 shipped the map to make R2866's 2**depth fan-out enumerable and
gave it no suite of its own, so a miscount, a cycle that recursed instead of
refusing, or a write smuggled into a read-only tool would have been read by a
human or by nobody.

  AC-PSFM1  a doubled parent call reads CALLS 2 (the shape R2866 measured)
  AC-PSFM2  a single parent call reads CALLS 1 (the shape a fix must reach)
  AC-PSFM3  a cycle reads depth -1 rather than recursing (pinned refusal)
  AC-PSFM4  the live tree partitions: zero unreadable entries, FANOUT_LAYERS
           equals the count of rows at CALLS >= 2, every decided row carries
           an int depth >= 0 and int calls >= 0
  AC-PSFM5  the CLI is a pure read: two runs byte-identical, --evidence writes
           exactly the stdout text, and the trailing EVIDENCE line names the
           same bytes and line count
  AC-PSFM6  hygiene: ASCII source, stdlib only, no clock, no network import,
           and the suite is wired into the runner

Every private world lives in a temporary directory and FOM.OS_DIR is restored
in a finally; no shipped source file is written.

Measured limit, declared rather than hidden: the map resolves a parent link
only when the alias RHS names the MODULE (_BASE_X_ENTRY = mod.func). A chain
written through an "import ... as" short name (_BASE_X_ENTRY = M.func) reads
depth 1, because the alias table is keyed by module file name. This window
found that by building the cycle fixture that way first, so the fixture now
uses the shipped shape; a cycle written with short aliases would read depth 1
instead of -1. The refusal is proved for the shipped shape, not for every
possible spelling.

Pure ASCII, stdlib only, no clock, zero network.
"""

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)

import probe_seam_fanout_map as FOM  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(TOOLS, "probe_seam_fanout_map.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
WIRED_LABEL = '"os-probe-seam-fanout-map",'
WIRED_SUITE = '"test_probe_seam_fanout_map.py"), 6),'

CHECKS = []
FAILS = []

ROOT_BODY = (
    "def module_alias_entry(name, text, scope, line, tables=None, root=None,\n"
    "                       src_path=None):\n"
    "    return {\"state\": \"ok\"}\n"
)

DOUBLE_BODY = (
    "import aaa_root as P\n"
    "\n"
    "_BASE_P_ENTRY = aaa_root.module_alias_entry\n"
    "\n"
    "\n"
    "def module_alias_entry(name, text, scope, line, tables=None, root=None,\n"
    "                       src_path=None):\n"
    "    base = _BASE_P_ENTRY(name, text, scope, line, tables, root, src_path)\n"
    "    got = _BASE_P_ENTRY(name, text, scope, line, tables, root, src_path)\n"
    "    return got\n"
)

SINGLE_BODY = (
    "import aaa_root as P\n"
    "\n"
    "_BASE_P_ENTRY = aaa_root.module_alias_entry\n"
    "\n"
    "\n"
    "def module_alias_entry(name, text, scope, line, tables=None, root=None,\n"
    "                       src_path=None):\n"
    "    return _BASE_P_ENTRY(name, text, scope, line, tables, root, src_path)\n"
)

CYCLE_A = (
    "import aaa_cycle_b as Q\n"
    "\n"
    "_BASE_Q_ENTRY = aaa_cycle_b.module_alias_entry\n"
    "\n"
    "\n"
    "def module_alias_entry(name, text, scope, line, tables=None, root=None,\n"
    "                       src_path=None):\n"
    "    return _BASE_Q_ENTRY(name, text, scope, line, tables, root, src_path)\n"
)

CYCLE_B = (
    "import aaa_cycle_a as R\n"
    "\n"
    "_BASE_R_ENTRY = aaa_cycle_a.module_alias_entry\n"
    "\n"
    "\n"
    "def module_alias_entry(name, text, scope, line, tables=None, root=None,\n"
    "                       src_path=None):\n"
    "    return _BASE_R_ENTRY(name, text, scope, line, tables, root, src_path)\n"
)


def check(ok, label):
    if ok:
        CHECKS.append(label)
        print("PASS " + label)
    else:
        FAILS.append(label)
        print("FAIL " + label)
    return ok


def write_world(work, files):
    for name in sorted(files):
        path = os.path.join(work, name)
        with open(path, "w", encoding="ascii", newline="\n") as handle:
            handle.write(files[name])


def scan_world(work):
    """Read a private world by pointing the tool's OS_DIR at it."""
    saved = FOM.OS_DIR
    FOM.OS_DIR = work
    try:
        rows = FOM.chain_depth(FOM.scan(), FOM.alias_table())
    finally:
        FOM.OS_DIR = saved
    return dict((row["module"], row) for row in rows)


def capture(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = FOM.main(argv)
    if rc != 0:
        raise RuntimeError("E_PSF_RC")
    return buffer.getvalue()


def ac_psf1():
    work = tempfile.mkdtemp(prefix="psf-double-")
    try:
        write_world(work, {"aaa_root.py": ROOT_BODY,
                           "bbb_double.py": DOUBLE_BODY})
        rows = scan_world(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    row = rows.get("bbb_double") or {}
    return check(row.get("calls") == 2 and row.get("depth") == 1,
                 "AC-PSFM1 a doubled parent call reads CALLS 2 depth 1 (%r/%r)"
                 % (row.get("calls"), row.get("depth")))


def ac_psf2():
    work = tempfile.mkdtemp(prefix="psf-single-")
    try:
        write_world(work, {"aaa_root.py": ROOT_BODY,
                           "ccc_single.py": SINGLE_BODY})
        rows = scan_world(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    row = rows.get("ccc_single") or {}
    return check(row.get("calls") == 1 and row.get("depth") == 1,
                 "AC-PSFM2 a single parent call reads CALLS 1 depth 1 (%r/%r)"
                 % (row.get("calls"), row.get("depth")))


def ac_psf3():
    work = tempfile.mkdtemp(prefix="psf-cycle-")
    try:
        write_world(work, {"aaa_cycle_a.py": CYCLE_A,
                           "aaa_cycle_b.py": CYCLE_B})
        rows = scan_world(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    a = (rows.get("aaa_cycle_a") or {}).get("depth")
    b = (rows.get("aaa_cycle_b") or {}).get("depth")
    return check(a == -1 and b == -1,
                 "AC-PSFM3 a cycle reads depth -1 rather than recursing (%r/%r)"
                 % (a, b))


def ac_psf4():
    rows = FOM.chain_depth(FOM.scan(), FOM.alias_table())
    unreadable = [row for row in rows if row["state"] == "unreadable"]
    ok = check(not unreadable and len(rows) >= 15,
               "AC-PSFM4 the live tree is readable (%d entries, %d unreadable)"
               % (len(rows), len(unreadable)))
    decided = [row for row in rows if row["state"] in ("ok", "root")]
    bad = [row["module"] for row in decided
           if not isinstance(row["depth"], int) or row["depth"] < 0
           or not isinstance(row["calls"], int) or row["calls"] < 0]
    ok = check(not bad,
               "AC-PSFM4 every decided row carries an int depth >= 0 and int "
               "calls >= 0 (%d bad)" % len(bad)) and ok
    chain = [row for row in decided if row["state"] == "ok"]
    ok = check(chain and all(row["depth"] >= 1 for row in chain),
               "AC-PSFM4 every chain row sits at depth >= 1 (%d rows)"
               % len(chain)) and ok
    text = "\n".join(FOM.report(rows)) + "\n"
    match = re.search(r"FANOUT_LAYERS=(\d+)", text)
    counted = sum(1 for row in chain if row["calls"] >= 2)
    ok = check(match is not None and int(match.group(1)) == counted,
               "AC-PSFM4 FANOUT_LAYERS equals the rows at CALLS >= 2 (%s vs %d)"
               % (match.group(1) if match else "none", counted)) and ok
    return ok


def ac_psf5():
    first = capture([])
    second = capture([])
    ok = check(first == second,
               "AC-PSFM5 two runs are byte-identical (%d bytes)"
               % len(first.encode("utf-8")))
    work = tempfile.mkdtemp(prefix="psf-cli-")
    try:
        path = os.path.join(work, "map.log")
        out = capture(["--evidence", path])
        with open(path, "rb") as handle:
            raw = handle.read()
        ok = check(raw.decode("utf-8") == first,
                   "AC-PSFM5 --evidence writes exactly the stdout text "
                   "(%d bytes)" % len(raw)) and ok
        tail = [line for line in out.splitlines()
                if line.startswith("EVIDENCE ")]
        want = "bytes=%d lines=%d" % (len(raw),
                                      len(first.strip("\n").splitlines()))
        ok = check(len(tail) == 1 and want in tail[0],
                   "AC-PSFM5 the EVIDENCE line names the same bytes and lines "
                   "(%r)" % (tail or ["none"],)) and ok
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok


def ac_psf6():
    with open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        raw.decode("ascii")
        ascii_only = True
    except UnicodeDecodeError:
        ascii_only = False
    text = raw.decode("utf-8", "replace")
    imports = set(re.findall(r"(?m)^import ([A-Za-z_][\w.]*)", text))
    ok = check(ascii_only, "AC-PSFM6 the map source is pure ASCII")
    ok = check(imports == {"argparse", "os", "re", "sys"},
               "AC-PSFM6 imports are stdlib only (%r)" % sorted(imports)) and ok
    ok = check(not (imports & {"time", "datetime", "random"}),
               "AC-PSFM6 the map reads no clock") and ok
    ok = check(not (imports & {"urllib", "requests", "socket", "http",
                               "ftplib", "xmlrpc", "smtplib", "asyncio"}),
               "AC-PSFM6 zero network imports") and ok
    with open(RUNNER, encoding="utf-8") as handle:
        runner = handle.read()
    ok = check(WIRED_LABEL in runner and WIRED_SUITE in runner,
               "AC-PSFM6 the runner wires this suite") and ok
    return ok


def main():
    print("PROBE SEAM FANOUT MAP suite (R2870, %d criteria)"
          % EXPECTED_CRITERIA)
    ok = ac_psf1()
    ok = ac_psf2() and ok
    ok = ac_psf3() and ok
    ok = ac_psf4() and ok
    ok = ac_psf5() and ok
    ok = ac_psf6() and ok
    total = len(CHECKS) + len(FAILS)
    acs = set()
    for name in CHECKS + FAILS:
        token = name.split(" ", 1)[0]
        for cut in range(len(token), 0, -1):
            if token[cut - 1].isdigit():
                acs.add(token[:cut])
                break
    print("suite: %d assertions over %d criteria" % (total, len(acs)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s"
              % (total - len(FAILS), total, FAILS))
        return 1
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
