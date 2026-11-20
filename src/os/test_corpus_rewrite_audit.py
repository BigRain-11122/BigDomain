"""Battery suite for tools/corpus_rewrite_audit.py - criterion AC-CRA1 (six arms).

WHY THIS SUITE EXISTS (measured at R3102, not assumed):
R3101 measured a windowed drift scan at 180.8ms against 1216.8ms and refused it
on a LAW argument rather than a number. R3102 turned that refusal into a
measurable claim and this suite pins the instrument: git history says 71 of
4,122 tracked evidence files were modified after being added (109 events, 73
commits), the recursive basename face is clean (4,125 files, 0 duplicates), a
stat-only pass measures 9.6-39.2ms against ~712-780ms to read the corpus, and a
same-length rewrite whose mtime_ns is restored reads as UNCHANGED - the blind
spot that keeps the fingerprint an instrument and not a replacement law.

WHAT IS PROVED HERE (one criterion, six arms):
  a  verify_manifest names a size change, an mtime change and an added file,
     never an unchanged one, and the CLI round trip (--manifest-out then
     --verify on an untouched world) answers rc=0 with changed=missing=added=0
     while a later edit makes it rc=1.
  b  the BLIND SPOT is pinned as a law: a same-size rewrite with its mtime_ns
     restored is reported unchanged, so a future round cannot quietly adopt
     the fingerprint as equivalent to the full read.
  c  basename_census counts a private world (3 files, 1 duplicated basename)
     exactly, and on the live corpus its duplicate count equals an independent
     walker's count - a typed number would not survive either arm.
  d  git_modify_census reads a private git world (add -> commit -> modify ->
     commit) as commits=1 files=1 events=1 tracked=1, reads a clean world as
     0 events, and answers a non-git world with a NAMED error instead of a
     silent zero.
  e  the live CLI answers rc=0, prints the four reading lines plus one DERIVED
     verdict line, and writes nothing: the corpus fingerprint (count, bytes) is
     identical before and after.
  f  source discipline: the tool is pure ASCII, imports no socket or network
     module, and names no external host.

Isolation: private worlds are temp dirs; the git worlds are temp repos with -c
user config; the only live read is qa/ opened for reading. Stdlib only.
Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL = os.path.join(ROOT, "tools", "corpus_rewrite_audit.py")
QA = os.path.join(ROOT, "qa")
BATTERY = os.path.abspath(__file__)

sys.path.insert(0, os.path.join(ROOT, "tools"))
import corpus_rewrite_audit as CRA  # noqa: E402

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def write(path, blob):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "wb") as handle:
        handle.write(blob)


def run_cli(args):
    proc = subprocess.run([sys.executable, TOOL] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def corpus_stamp(path):
    files = 0
    size = 0
    for base, dirs, names in os.walk(path):
        for name in names:
            if name.lower().endswith(".log"):
                st = os.stat(os.path.join(base, name))
                files += 1
                size += st.st_size
    return (files, size)


def main():
    # ---- a: the manifest names what moved and nothing else.
    world = tempfile.mkdtemp(prefix="cra-a-")
    cli_world = tempfile.mkdtemp(prefix="cra-a-cli-")
    try:
        write(os.path.join(world, "a.log"), b"aaaa\n")
        write(os.path.join(world, "b.log"), b"bbbb\n")
        write(os.path.join(world, "keep.log"), b"keep\n")
        table = CRA.manifest(world)
        with open(os.path.join(world, "a.log"), "ab") as handle:
            handle.write(b"more\n")            # size change
        st = os.stat(os.path.join(world, "b.log"))
        os.utime(os.path.join(world, "b.log"),
                 ns=(st.st_atime_ns, st.st_mtime_ns + 2000000000))
        write(os.path.join(world, "added.log"), b"new\n")
        report = CRA.verify_manifest(world, table)
        named = (report["changed"] == ["a.log", "b.log"]
                 and report["added"] == ["added.log"]
                 and report["missing"] == []
                 and "keep.log" not in report["changed"])
        write(os.path.join(cli_world, "x.log"), b"x\n")
        table_path = os.path.join(cli_world, "table.json")
        rc_out, out_out = run_cli(["--qa", cli_world,
                                   "--manifest-out", table_path])
        rc_same, out_same = run_cli(["--qa", cli_world, "--verify", table_path])
        with open(os.path.join(cli_world, "x.log"), "ab") as handle:
            handle.write(b"change\n")
        rc_moved, out_moved = run_cli(["--qa", cli_world,
                                       "--verify", table_path])
        ok("AC-CRA1 arm a - the manifest names what moved and nothing else",
           named and rc_out == 0 and rc_same == 0
           and "changed=0 missing=0 added=0" in out_same
           and rc_moved == 1 and "changed=1" in out_moved,
           "named=%s write_rc=%d same_rc=%d moved_rc=%d" %
           (named, rc_out, rc_same, rc_moved))
    finally:
        shutil.rmtree(world, ignore_errors=True)
        shutil.rmtree(cli_world, ignore_errors=True)

    # ---- b: the blind spot is the law this suite exists to keep honest.
    spot = CRA.blind_spot()
    world = tempfile.mkdtemp(prefix="cra-b-")
    try:
        path = os.path.join(world, "a.log")
        write(path, b"1111\n")
        st = os.stat(path)
        table = CRA.manifest(world)
        write(path, b"2222\n")
        os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
        hidden = CRA.verify_manifest(world, table)["changed"] == []
        ok("AC-CRA1 arm b - same size and same mtime_ns reads as unchanged",
           hidden and spot["undetected"]
           and spot["detected_by_size"] and spot["detected_by_mtime"],
           "hidden=%s undetected=%s by_size=%s by_mtime=%s" %
           (hidden, spot["undetected"], spot["detected_by_size"],
            spot["detected_by_mtime"]))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # ---- c: basenames, private and live, both derived.
    world = tempfile.mkdtemp(prefix="cra-c-")
    try:
        write(os.path.join(world, "a.log"), b"1\n")
        write(os.path.join(world, "sub", "a.log"), b"2\n")
        write(os.path.join(world, "sub", "b.log"), b"3\n")
        private = CRA.basename_census(world)
        live = CRA.basename_census(QA)
        independent = 0
        seen = {}
        for base, dirs, names in os.walk(QA):
            for name in names:
                if name.lower().endswith(".log"):
                    seen[name] = seen.get(name, 0) + 1
        for name, count in seen.items():
            if count > 1:
                independent += count
        ok("AC-CRA1 arm c - basename census is counted, not typed",
           private["log_files"] == 3 and private["basenames"] == 2
           and private["duplicate_names"] == 1
           and private["duplicate_files"] == 2
           and live["duplicate_files"] == independent,
           "private=%d/%d/%d live_dup=%d independent=%d" %
           (private["log_files"], private["duplicate_names"],
            private["duplicate_files"], live["duplicate_files"], independent))
    finally:
        shutil.rmtree(world, ignore_errors=True)

    # ---- d: a git history is read, and a missing one is named.
    repo = tempfile.mkdtemp(prefix="cra-d-repo-")
    clean = tempfile.mkdtemp(prefix="cra-d-clean-")
    nongit = tempfile.mkdtemp(prefix="cra-d-none-")
    try:
        def git(args, cwd):
            return subprocess.run(
                ["git", "-C", cwd, "-c", "user.email=a@b", "-c",
                 "user.name=t"] + args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        git(["init", "-q"], repo)
        write(os.path.join(repo, "qa", "x.log"), b"one\n")
        git(["add", "-A"], repo)
        git(["commit", "-q", "-m", "one"], repo)
        write(os.path.join(repo, "qa", "x.log"), b"one changed\n")
        git(["add", "-A"], repo)
        git(["commit", "-q", "-m", "two"], repo)
        moved = CRA.git_modify_census(repo)
        git(["init", "-q"], clean)
        write(os.path.join(clean, "qa", "y.log"), b"only\n")
        git(["add", "-A"], clean)
        git(["commit", "-q", "-m", "only"], clean)
        quiet = CRA.git_modify_census(clean)
        write(os.path.join(nongit, "z.log"), b"z\n")
        absent = CRA.git_modify_census(nongit)
        ok("AC-CRA1 arm d - a modify history is read; no history is named",
           moved.get("commits") == 1 and moved.get("files") == 1
           and moved.get("events") == 1 and moved.get("tracked") == 1
           and quiet.get("events") == 0 and quiet.get("commits") == 0
           and absent.get("error") == "E_CRA_NO_GIT",
           "moved=%s/%s/%s quiet=%s absent=%s" %
           (moved.get("commits"), moved.get("files"), moved.get("events"),
            quiet.get("events"), absent.get("error")))
    finally:
        for path in (repo, clean, nongit):
            shutil.rmtree(path, ignore_errors=True)

    # ---- e: the live face answers and writes nothing.
    before = corpus_stamp(QA)
    rc, out = run_cli([])
    after = corpus_stamp(QA)
    needed = ("CORPUS-REWRITES ", "CORPUS-DUPLICATES ", "CORPUS-COST ",
              "CORPUS-BLIND-SPOT ", "CORPUS-VERDICT sampling-law=")
    ok("AC-CRA1 arm e - the live face answers rc=0 and writes nothing",
       rc == 0 and all(key in out for key in needed) and before == after,
       "rc=%d lines=%d stamp_same=%s" %
       (rc, sum(1 for key in needed if key in out), before == after))

    # ---- f: source discipline, recomputed rather than promised.
    own = open(BATTERY, encoding="utf-8").read()
    tool = open(TOOL, encoding="utf-8").read()
    socket_needle = "import " + "socket"
    host_needle = "https" + "://"
    ascii_ok = True
    for blob in (tool, own):
        try:
            blob.encode("ascii")
        except UnicodeEncodeError:
            ascii_ok = False
    ok("AC-CRA1 arm f - ASCII, no network import, no external host",
       ascii_ok and socket_needle not in tool and host_needle not in tool
       and '"AC-CRA1' in own,
       "ascii=%s socket=%s host=%s labelled=%s" %
       (ascii_ok, socket_needle in tool, host_needle in tool,
        '"AC-CRA1' in own))

    criteria = set()
    for name in CHECKS:
        token = name.split(" ", 1)[0]
        criteria.add(token)
    total = len(CHECKS)
    print("suite: %d assertions over %d criteria" % (total, len(criteria)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 2
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
