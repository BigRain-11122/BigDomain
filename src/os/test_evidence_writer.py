#!/usr/bin/env python3
"""test_evidence_writer.py - sandbox suite for src/os/evidence_writer.py.

AC-EVD1..AC-EVD8 (pre-registered in state/queue/tech.md R2072 claim
line BEFORE this code): one check per criterion, on throwaway temp
fixtures. ASCII-only source; stdlib only; zero network. Exit 0 = green.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evidence_writer as EW
import qa_writer_census as CENSUS

TOOL = os.path.join(HERE, "evidence_writer.py")
CHECKS = 0


def ok(cond, label):
    global CHECKS
    assert cond, "FAIL: " + label
    CHECKS += 1
    print("PASS " + label)


def run(*args):
    proc = subprocess.run([sys.executable, TOOL] + list(args),
                          capture_output=True)
    return (proc.returncode,
            proc.stdout.decode("utf-8", "replace"),
            proc.stderr.decode("utf-8", "replace"))


def main():
    root = tempfile.mkdtemp(prefix="bd-evd-")
    try:
        # AC-EVD1: single LF writer byte shape
        plain = os.path.join(root, "plain.log")
        row = EW.write_evidence(plain, "FUNNEL-DAILY day=2026-10-24\n")
        with open(plain, "rb") as handle:
            raw = handle.read()
        ok(row["class"] == "tee" and raw.count(b"\r") == 0
           and not raw.startswith(b"\xef\xbb\xbf")
           and raw.endswith(b"\n") and not raw.endswith(b"\n\n"),
           "AC-EVD1 utf-8 no-BOM LF exactly-one-trailing-newline")

        # AC-EVD2: input normalisation on the EOL axis only
        mixed = os.path.join(root, "mixed.log")
        EW.write_evidence(mixed, "a\r\nb\rc\n\nd")
        with open(mixed, "rb") as handle:
            got = handle.read()
        ok(got == b"a\nb\nc\n\nd\n",
           "AC-EVD2 CRLF/CR/mixed input lands as LF lines")

        # AC-EVD3: encode-before-touch, atomic replace, no temp residue
        before = open(mixed, "rb").read()
        raised = False
        try:
            EW.write_evidence(mixed, b"bytes-not-str")
        except TypeError:
            raised = True
        leftovers = [n for n in os.listdir(root) if n.startswith(".evd-")]
        ok(raised and open(mixed, "rb").read() == before and not leftovers,
           "AC-EVD3 bad input touches nothing, no temp leftovers")

        # AC-EVD4: the post-write self-check is live
        original = CENSUS.classify_file
        try:
            CENSUS.classify_file = lambda path: {"class": "pwsh-capture",
                                                 "bytes": 0, "crlf": 0,
                                                 "bare_lf": 0}
            caught = False
            try:
                EW.write_evidence(os.path.join(root, "guard.log"), "x\n")
            except EW.EvidenceDialectError:
                caught = True
        finally:
            CENSUS.classify_file = original
        ok(caught, "AC-EVD4 non-tee post-write classification raises")

        # AC-EVD5: read-only check face, missing file raises
        st_before = os.stat(plain)
        time.sleep(0.01)
        checked = EW.check_file(plain)
        st_after = os.stat(plain)
        missing_raised = False
        try:
            EW.check_file(os.path.join(root, "nope.log"))
        except EW.EvidenceDialectError:
            missing_raised = True
        ok(checked["class"] == "tee" and st_after.st_mtime == st_before.st_mtime
           and missing_raised,
           "AC-EVD5 check is read-only and refuses missing files")

        # AC-EVD6: real CRLF pollution is flagged, fixed, non-utf8 refused
        dirty = os.path.join(root, "dirty.log")
        with open(dirty, "wb") as handle:
            handle.write(b"line one\r\nline two\r\n")
        flagged = EW.check_file(dirty)["class"] != "tee"
        fixed = EW.fix_file(dirty)
        with open(dirty, "rb") as handle:
            fixed_raw = handle.read()
        binary = os.path.join(root, "binary.log")
        with open(binary, "wb") as handle:
            handle.write(b"\xff\xfe\r\n")
        refused = False
        try:
            EW.fix_file(binary)
        except EW.EvidenceDialectError:
            refused = True
        ok(flagged and fixed["class"] == "tee"
           and fixed_raw == b"line one\nline two\n" and refused,
           "AC-EVD6 CRLF flagged and repaired, non-utf8 refused")

        # AC-EVD7: census over a fixture directory is read-only
        fixture = os.path.join(root, "census")
        os.makedirs(fixture)
        shutil.copy(plain, os.path.join(fixture, "a-tee.log"))
        shutil.copy(dirty, os.path.join(fixture, "b-tee.log"))
        with open(os.path.join(fixture, "c-crlf.log"), "wb") as handle:
            handle.write(b"only\r\ncrlf\r\n")
        snap = {}
        for name in sorted(os.listdir(fixture)):
            path = os.path.join(fixture, name)
            with open(path, "rb") as handle:
                snap[name] = (handle.read(), os.stat(path).st_mtime)
        lines, code, summary = CENSUS.probe_dir(fixture)
        stable = True
        for name in sorted(os.listdir(fixture)):
            path = os.path.join(fixture, name)
            with open(path, "rb") as handle:
                if (handle.read(), os.stat(path).st_mtime) != snap[name]:
                    stable = False
        ok(code == 0 and summary["counts"]["tee"] == 2
           and summary["counts"]["pwsh-capture"] == 1 and stable,
           "AC-EVD7 census counts tee/non-tee and rewrites nothing")

        # AC-EVD8: CLI contract + source hygiene
        cli_dirty = os.path.join(root, "cli-dirty.log")
        with open(cli_dirty, "wb") as handle:
            handle.write(b"cli one\r\ncli two\r\n")
        c_tee, out_tee, _ = run("--check", plain)
        c_dirty, out_dirty, _ = run("--check", cli_dirty)
        c_missing, out_missing, _ = run("--check",
                                        os.path.join(root, "gone.log"))
        c_fix, out_fix, _ = run("--fix", cli_dirty)
        with open(os.path.join(HERE, "evidence_writer.py"), "rb") as handle:
            src = handle.read()
        net = [n for n in ("requests", "urllib", "socket", "http.client")
               if ("import " + n) in src.decode("ascii", "replace")]
        ok(c_tee == 0 and c_dirty == 2 and c_missing == 3 and c_fix == 0
           and "class=" in out_fix and out_missing.startswith("MISSING")
           and not net,
           "AC-EVD8 CLI exit codes 0/2/3, fix prints class, ASCII stdlib")

        print("SUITE PASS %d/8 checks" % CHECKS)
        return 0 if CHECKS == 8 else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())