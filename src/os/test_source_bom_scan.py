"""source_bom_scan suite (R3170; criteria AC-SBS1..AC-SBS6 were pinned in
src/os/backlog.md as the R3170 PIN row BEFORE the code existed).

What this proves: a UTF-8 BOM on a tracked source file is named exactly (and a
UTF-16 BOM or a BOM past byte 0 is not this face's business), the universe is
the git index rather than whatever happens to sit on disk, the scan writes
nothing, the CLI keeps four truthful exit codes, the JSON face is pinned and
repeatable, and the live tree reads clean after this round's strip.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import hashlib
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

import source_bom_scan as SBS  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "source_bom_scan.py")
RUNNER = os.path.join(SRC, "sandbox", "reconcile_all.py")
LABEL = "os-source-bom"
WIRED_EXPECT = '"test_source_bom_scan.py"), 6),'
BOM = b"\xef\xbb\xbf"

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


def write_bytes(path, raw):
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "wb") as handle:
        handle.write(raw)


def digest_tree(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            with io.open(path, "rb") as handle:
                out[rel] = hashlib.sha256(handle.read()).hexdigest()
    return out


def make_world():
    return tempfile.mkdtemp(prefix="bigdomain-sbs-w-")


def ac_sbs1():
    """Detection is exact: EF BB BF at byte 0 only."""
    world = make_world()
    try:
        write_bytes(os.path.join(world, "bom.py"), BOM + b"x = 1\n")
        write_bytes(os.path.join(world, "plain.py"), b"x = 1\n")
        write_bytes(os.path.join(world, "utf16.py"), b"\xff\xfe" + b"x=1\n")
        write_bytes(os.path.join(world, "midbom.py"),
                    b"x = 1\n# " + BOM + b"\n")
        report = SBS.scan(world, tracked=[
            "bom.py", "plain.py", "utf16.py", "midbom.py"])
        empty = make_world()
        try:
            clean = SBS.scan(empty, tracked=[])
        finally:
            shutil.rmtree(empty, ignore_errors=True)
        ok = (report["offenders"] == ["bom.py"]
              and report["unreadable"] == []
              and report["tracked_python"] == 4
              and report["verdict"] == SBS.VERDICT_FOUND
              and clean["offenders"] == []
              and clean["verdict"] == SBS.VERDICT_CLEAN)
        if not ok:
            print("  measured: report=%r clean=%r" % (report, clean), flush=True)
        check(ok, "AC-SBS1 detection is exact: a UTF-8 BOM at byte 0 is an "
                  "offender, a UTF-16 BOM and a BOM past byte 0 are not")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sbs2():
    """The universe is the git index, not the disk."""
    world = make_world()
    try:
        env = dict(os.environ)
        env["GIT_AUTHOR_NAME"] = "sbs"
        env["GIT_AUTHOR_EMAIL"] = "sbs@example.invalid"
        env["GIT_COMMITTER_NAME"] = "sbs"
        env["GIT_COMMITTER_EMAIL"] = "sbs@example.invalid"
        subprocess.run(["git", "init", "-q", world], check=True,
                       capture_output=True, env=env)
        write_bytes(os.path.join(world, "bom.py"), BOM + b"x = 1\n")
        write_bytes(os.path.join(world, "plain.py"), b"x = 1\n")
        write_bytes(os.path.join(world, "notes.txt"), BOM + b"hello\n")
        write_bytes(os.path.join(world, "untracked_bom.py"), BOM + b"y = 2\n")
        subprocess.run(["git", "-C", world, "add", "bom.py", "plain.py",
                        "notes.txt"], check=True, capture_output=True, env=env)
        tracked, error = SBS.tracked_python(world)
        report = SBS.scan(world)
        missing = make_world()
        try:
            _bad, bad_error = SBS.tracked_python(missing)
        finally:
            shutil.rmtree(missing, ignore_errors=True)
        ok = (error is None
              and tracked == ["bom.py", "plain.py"]
              and report["tracked_python"] == 2
              and report["offenders"] == ["bom.py"]
              and bad_error is not None)
        if not ok:
            print("  measured: tracked=%r error=%r report=%r bad=%r"
                  % (tracked, error, report, bad_error), flush=True)
        check(ok, "AC-SBS2 the universe is the git index: an untracked BOM file "
                  "and a tracked non-Python BOM file never enter the reading, "
                  "and an unreadable tree reports an error instead of clean")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sbs3():
    """The scan writes nothing."""
    world = make_world()
    try:
        write_bytes(os.path.join(world, "bom.py"), BOM + b"x = 1\n")
        write_bytes(os.path.join(world, "plain.py"), b"x = 1\n")
        before = digest_tree(world)
        SBS.scan(world, tracked=["bom.py", "plain.py"])
        SBS.main(["--check", "--root", world], out=io.StringIO(),
                 err=io.StringIO())
        after = digest_tree(world)
        ok = before == after
        if not ok:
            print("  measured: before=%r after=%r" % (before, after), flush=True)
        check(ok, "AC-SBS3 the scan and its --check write nothing: every file "
                  "digest is unchanged and no file appears")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sbs4():
    """Four pinned exit codes, each reachable."""
    clean = make_world()
    dirty = make_world()
    nogit = make_world()
    try:
        write_bytes(os.path.join(clean, "plain.py"), b"x = 1\n")
        subprocess.run(["git", "init", "-q", clean], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", clean, "add", "plain.py"], check=True,
                       capture_output=True)
        write_bytes(os.path.join(dirty, "bom.py"), BOM + b"x = 1\n")
        subprocess.run(["git", "init", "-q", dirty], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", dirty, "add", "bom.py"], check=True,
                       capture_output=True)
        write_bytes(os.path.join(nogit, "plain.py"), b"x = 1\n")
        rc_clean = SBS.main(["--check", "--root", clean], out=io.StringIO(),
                            err=io.StringIO())
        rc_found = SBS.main(["--check", "--root", dirty], out=io.StringIO(),
                            err=io.StringIO())
        err = io.StringIO()
        rc_bad = SBS.main(["--nope"], out=io.StringIO(), err=err)
        rc_env = SBS.main(["--check", "--root", nogit], out=io.StringIO(),
                          err=io.StringIO())
        ok = (rc_clean == SBS.EXIT_CLEAN and rc_found == SBS.EXIT_FOUND
              and rc_bad == SBS.EXIT_FOUND and "usage:" in err.getvalue()
              and rc_env == SBS.EXIT_ENV)
        if not ok:
            print("  measured: clean=%r found=%r bad=%r env=%r"
                  % (rc_clean, rc_found, rc_bad, rc_env), flush=True)
        check(ok, "AC-SBS4 the CLI keeps four truthful codes: 0 clean, 2 "
                  "offenders, 2 bad flags with usage, 3 an unreadable tree")
    finally:
        for path in (clean, dirty, nogit):
            shutil.rmtree(path, ignore_errors=True)


def ac_sbs5():
    """The JSON face is pinned and repeatable."""
    world = make_world()
    try:
        write_bytes(os.path.join(world, "bom.py"), BOM + b"x = 1\n")
        write_bytes(os.path.join(world, "plain.py"), b"x = 1\n")
        subprocess.run(["git", "init", "-q", world], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", world, "add", "bom.py", "plain.py"],
                       check=True, capture_output=True)
        one = io.StringIO()
        two = io.StringIO()
        SBS.main(["--json", "--root", world], out=one, err=io.StringIO())
        SBS.main(["--json", "--root", world], out=two, err=io.StringIO())
        body = json.loads(one.getvalue())
        order = list(body.keys())
        ok = (one.getvalue() == two.getvalue()
              and order == list(SBS.REPORT_KEYS)
              and body["verdict"] == SBS.VERDICT_FOUND
              and body["offenders"] == ["bom.py"]
              and body["tracked_python"] == 2
              and "_error" not in order)
        if not ok:
            print("  measured: order=%r body=%r same=%r"
                  % (order, body, one.getvalue() == two.getvalue()), flush=True)
        check(ok, "AC-SBS5 the JSON face carries exactly the pinned keys in "
                  "order, twice byte-identical, with no internal key leaked")
    finally:
        shutil.rmtree(world, ignore_errors=True)


def ac_sbs6():
    """The live tree reads clean, and the source stays honest."""
    live = SBS.scan(REPO)
    with io.open(MODULE, "rb") as handle:
        raw = handle.read()
    try:
        source = raw.decode("ascii")
        ascii_ok = True
    except UnicodeDecodeError:
        source = raw.decode("utf-8", "replace")
        ascii_ok = False
    imports = [ln for ln in source.splitlines()
               if ln.startswith("import ") or ln.startswith("from ")]
    net_ok = not any(("socket" in ln or "urllib" in ln or "http" in ln)
                     for ln in imports)
    with io.open(RUNNER, "r", encoding="utf-8-sig", errors="replace") as fh:
        runner = fh.read()
    wired = WIRED_EXPECT in runner
    ok = (live["verdict"] == SBS.VERDICT_CLEAN
          and live["tracked_python"] >= 1
          and live["offenders"] == []
          and live["unreadable"] == []
          and not raw.startswith(BOM)
          and ascii_ok
          and net_ok
          and wired
          and EXPECTED_CRITERIA == 6)
    if not ok:
        print("  measured: live=%r ascii=%r net=%r wired=%r"
              % (live, ascii_ok, net_ok, wired), flush=True)
    check(ok, "AC-SBS6 the live tree is BOM-clean after the R3170 strip, the "
              "module source is ASCII with no network import, and the registry "
              "row carries this suite with its six criteria")


def main():
    ac_sbs1()
    ac_sbs2()
    ac_sbs3()
    ac_sbs4()
    ac_sbs5()
    ac_sbs6()
    print("SUITE %s %d/%d"
          % ("PASS" if FAILS == 0 else "FAIL", PASSES, PASSES + FAILS),
          flush=True)
    if PASSES + FAILS != EXPECTED_CRITERIA or FAILS:
        print("EXPECTED %d criteria" % EXPECTED_CRITERIA, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
