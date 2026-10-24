"""Source-anchored watermark v2 (AC-DWM1..AC-DWM8).

Face under proof: src/os/dec_watermark.py, the write point that turns
the five-silence decisions baseline from a bare content hash into the
four-tuple {repo, commit_sha, blob_bytes, sha256} with a reproducible
fetch command beside it (group decision D-20261025-08, deadline
2026-10-26 06:00 for every company).

Criteria were pre-registered in the tech-queue row BEFORE this file
existed.

  AC-DWM1 tuple: resolve() yields exactly the four tuple keys with the
    real commit sha, the real byte size and the sha256 of the blob.
  AC-DWM2 reproducible fetch: executing the recorded fetch command
    reproduces the identical blob (same bytes, same sha256).
  AC-DWM3 atomic record: the file is v2, ASCII, LF-terminated, no
    .tmp survivor, and two records of the same state are byte-equal.
  AC-DWM4 unchanged: a re-check of an untouched source reports
    unchanged and never rewrites the file.
  AC-DWM5 moved: a new commit changing the file reports moved and the
    record advances to the new source tuple.
  AC-DWM6 stale source: a differing repo label is stale and the
    watermark is never advanced.
  AC-DWM7 stale rewrite: the same commit and byte count carrying a
    different sha256 is stale (history rewritten), never advanced.
  AC-DWM8 delivery: stdlib-only ASCII module, unknown flag exits 2,
    the shipped state/dec_watermark.json carries the four-tuple and
    its fetch command reproduces the recorded sha256.
"""

import hashlib
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import dec_watermark as W                       # noqa: E402

RESULTS = []

SHIPPED = os.path.join(ROOT, "state", "dec_watermark.json")
MODULE = os.path.join(BASE, "dec_watermark.py")
RECONCILE = os.path.join(ROOT, "src", "sandbox", "reconcile_all.py")

STAMP = "2026-10-25T00:00:00Z"
FIRST = "# decisions\nD-20261025-01 first row\n"
SECOND = "# decisions\nD-20261025-01 first row\nD-20261025-09 late row\n"


def record(ac, ok, evidence):
    RESULTS.append((ac, bool(ok)))
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence),
          flush=True)


def sha_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha_file(path):
    with open(path, "rb") as handle:
        return sha_bytes(handle.read())


def git(repo, *args):
    proc = subprocess.run(["git", "-C", repo] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise AssertionError(proc.stderr.decode("utf-8", "replace"))
    return proc.stdout.decode("utf-8", "replace").strip()


def make_repo(folder, text):
    os.makedirs(os.path.join(folder, "docs"))
    git(folder, "init", "-q")
    git(folder, "config", "user.email", "qa@example.invalid")
    git(folder, "config", "user.name", "qa")
    path = os.path.join(folder, "docs", "decisions.md")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    git(folder, "add", "docs/decisions.md")
    git(folder, "commit", "-q", "-m", "seed")
    return path


def write_entry(path, entry):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, indent=1, sort_keys=True) + "\n")


def main():
    tmp = tempfile.mkdtemp(prefix="decwm-")
    try:
        repo = os.path.join(tmp, "src_repo")
        doc = make_repo(repo, FIRST)
        wm = os.path.join(tmp, "watermark.json")

        verdict, note, entry = W.record(repo, "docs/decisions.md", "HEAD",
                                        wm, STAMP)

        # -- AC-DWM1 tuple --------------------------------------------
        with open(doc, "rb") as handle:
            body = handle.read()
        head = git(repo, "rev-parse", "HEAD")
        ok1 = (all(k in entry for k in W.TUPLE_KEYS)
               and entry["commit_sha"] == head
               and entry["blob_bytes"] == len(body)
               and entry["sha256"] == sha_bytes(body)
               and entry["format"] == W.WATERMARK_FORMAT
               and verdict == W.NEW)
        record("AC-DWM1", ok1,
               "verdict=%s keys=%d bytes=%d match=%s"
               % (verdict, len(W.TUPLE_KEYS), entry["blob_bytes"],
                  (entry["commit_sha"] == head
                   and entry["sha256"] == sha_bytes(body))))

        # -- AC-DWM2 reproducible fetch -------------------------------
        argv = shlex.split(entry["fetch"])
        proc = subprocess.run(argv, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        ok2 = (proc.returncode == 0
               and proc.stdout == body
               and sha_bytes(proc.stdout) == entry["sha256"])
        record("AC-DWM2", ok2,
               "rc=%d bytes=%d same=%s"
               % (proc.returncode, len(proc.stdout),
                  proc.stdout == body))

        # -- AC-DWM3 atomic record ------------------------------------
        first = open(wm, "rb").read()
        W.record(repo, "docs/decisions.md", "HEAD", wm, STAMP)
        second = open(wm, "rb").read()
        ok3 = (first == second
               and b"\r" not in first
               and all(byte < 128 for byte in first)
               and first.endswith(b"\n")
               and not os.path.exists(wm + ".tmp"))
        record("AC-DWM3", ok3,
               "same=%s ascii=%s lf=%s tmp=%s"
               % (first == second, all(b < 128 for b in first),
                  first.endswith(b"\n"), os.path.exists(wm + ".tmp")))

        # -- AC-DWM4 unchanged ----------------------------------------
        before = open(wm, "rb").read()
        verdict4, _note, _stored = W.check(wm)
        ok4 = (verdict4 == W.UNCHANGED
               and open(wm, "rb").read() == before)
        record("AC-DWM4", ok4, "verdict=%s untouched=%s"
               % (verdict4, open(wm, "rb").read() == before))

        # -- AC-DWM5 moved --------------------------------------------
        with io.open(doc, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(SECOND)
        git(repo, "add", "docs/decisions.md")
        git(repo, "commit", "-q", "-m", "row nine")
        verdict5, _note, _stored = W.check(wm)
        moved_ok = verdict5 == W.MOVED
        W.record(repo, "docs/decisions.md", "HEAD", wm, STAMP)
        fresh = json.load(open(wm, "r", encoding="utf-8"))
        head5 = git(repo, "rev-parse", "HEAD")
        ok5 = (moved_ok
               and fresh["commit_sha"] == head5
               and fresh["sha256"] == sha_bytes(SECOND.encode("utf-8")))
        record("AC-DWM5", ok5,
               "check=%s advanced=%s"
               % (verdict5, fresh["commit_sha"] == head5))

        # -- AC-DWM6 stale source -------------------------------------
        stored6 = json.loads(open(wm, "r", encoding="utf-8").read())
        stored6["repo"] = "git@example.invalid:other/FluxGroup.git"
        write_entry(wm, stored6)
        before6 = open(wm, "rb").read()
        verdict6, _note, _stored = W.check(wm)
        rec6, _note6, _entry6 = W.record(repo, "docs/decisions.md", "HEAD",
                                         wm, STAMP)
        ok6 = (verdict6 == W.STALE and rec6 == W.STALE
               and open(wm, "rb").read() == before6)
        record("AC-DWM6", ok6,
               "check=%s record=%s untouched=%s"
               % (verdict6, rec6, open(wm, "rb").read() == before6))

        # -- AC-DWM7 stale rewrite ------------------------------------
        stored7 = json.loads(open(wm, "r", encoding="utf-8").read())
        stored7["repo"] = W.repo_identity(repo)
        stored7["sha256"] = "0" * 64
        write_entry(wm, stored7)
        before7 = open(wm, "rb").read()
        verdict7, note7, _stored = W.check(wm)
        rec7, _note7, _entry7 = W.record(repo, "docs/decisions.md", "HEAD",
                                         wm, STAMP)
        ok7 = (verdict7 == W.STALE and rec7 == W.STALE
               and "history" in note7
               and open(wm, "rb").read() == before7)
        record("AC-DWM7", ok7,
               "check=%s record=%s note=%s untouched=%s"
               % (verdict7, rec7, bool("history" in note7),
                  open(wm, "rb").read() == before7))

        # -- AC-DWM8 delivery -----------------------------------------
        src = open(MODULE, "rb").read()
        forbidden = ("import requests", "import urllib", "import socket",
                     "import http")
        shipped = {}
        fetch_ok = False
        shipped_ok = False
        if os.path.isfile(SHIPPED):
            shipped = json.loads(open(SHIPPED, "r", encoding="utf-8").read())
            shipped_ok = (shipped.get("format") == W.WATERMARK_FORMAT
                          and all(k in shipped for k in W.TUPLE_KEYS))
            if shipped_ok and os.path.isdir(shipped.get("repo_path", "")):
                argv = shlex.split(shipped["fetch"])
                proc = subprocess.run(argv, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                fetch_ok = (proc.returncode == 0
                            and sha_bytes(proc.stdout) == shipped["sha256"]
                            and len(proc.stdout) == int(
                                shipped["blob_bytes"]))
        runner_src = open(RECONCILE, "r", encoding="utf-8").read()
        proc_usage = subprocess.run(
            [sys.executable, MODULE, "--not-a-flag"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ok8 = (all(byte < 128 for byte in src)
               and b"\r" not in src
               and not any(tok in src.decode("ascii") for tok in forbidden)
               and proc_usage.returncode == 2
               and "os-decwatermark" in runner_src
               and shipped_ok and fetch_ok)
        record("AC-DWM8", ok8,
               "ascii=%s usage=%d runner=%s shipped=%s fetch=%s"
               % (all(b < 128 for b in src), proc_usage.returncode,
                  "os-decwatermark" in runner_src, shipped_ok, fetch_ok))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(RESULTS)
    passed = sum(1 for _ac, ok in RESULTS if ok)
    print("SUITE %d/%d %s" % (passed, total,
                             "PASS" if passed == total else "FAIL"),
          flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())