"""Archive provenance reader suite (R3091).

Criteria AC-APR1..AC-APR6 were pinned in src/os/backlog.md BEFORE this
file existed. The queue head asked whether an archive's tracked state can
be read without a child process, because the FOLD-CARRY locator is only as
stable as that provenance and only the November archive is git-backed.

AC-APR1  a version-2 index is parsed into exactly the tracked path set,
         including a path whose entry needs 8-byte padding.
AC-APR2  every refusal is named and lands nothing on stdout: no index,
         bad magic, a non-2 version, a truncated entry.
AC-APR3  the prefix filter takes only matching files and measures each
         file's own size; a non-matching sibling is not reported.
AC-APR4  the live tree reads PASS: rc=0, ASCII only, the three archives
         carry the flags the index holds, and the summary counts agree.
AC-APR5  the module imports nothing that can spawn work or open a socket.
AC-APR6  --json is stable under repetition (two runs byte-identical) and a
         missing directory refuses with rc=2 and zero bytes on stdout.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import contextlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)

import archive_provenance as APR  # noqa: E402

EXPECTED_CRITERIA = 6
PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
    else:
        FAILS += 1
        print("FAIL %s" % label)


def index_bytes(names, version=2):
    """Build a synthetic DIRC index for the named paths."""
    body = b"DIRC" + struct.pack(">II", version, len(names))
    for name in names:
        raw = name.encode("utf-8")
        entry = b"\x00" * 40 + b"\x10" * 20 + struct.pack(">H", len(raw))
        entry += raw + b"\x00"
        pad = (8 - len(entry) % 8) % 8
        body += entry + b"\x00" * pad
    return body


def write(path, blob):
    handle = open(path, "wb")
    try:
        handle.write(blob)
    finally:
        handle.close()


def world(root):
    os.makedirs(os.path.join(root, ".git"))
    os.makedirs(os.path.join(root, "logs"))
    write(os.path.join(root, ".git", "index"),
          index_bytes(["logs/state-log-archive-2026-11.md", "src/kept.py"]))
    write(os.path.join(root, "logs", "state-log-archive-2026-11.md"),
          b"# --- R1 archive\n")
    write(os.path.join(root, "logs", "state-log-archive-2026-09.md"),
          b"# --- R2 archive\n")
    write(os.path.join(root, "logs", "other.txt"), b"not an archive\n")


def capture(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = APR.main(argv)
    return code, out.getvalue(), err.getvalue()


def run():
    root = tempfile.mkdtemp(prefix="apr-")
    try:
        world(root)
        # AC-APR1: exact set, padding included.
        tracked, stats = APR.read_index(os.path.join(root, ".git", "index"))
        check(tracked == {"logs/state-log-archive-2026-11.md", "src/kept.py"}
              and stats["entries"] == 2 and stats["index_bytes"] > 12,
              "AC-APR1 v2 index parses to the exact tracked set")

        # AC-APR2: four named refusals, zero stdout. Each case gets its own
        # private repository so one refusal cannot be masked by another.
        cases = [("noindex", None),
                 ("magic", b"NOPE" + b"\x00" * 8),
                 ("version", index_bytes([], 3)),
                 ("truncated", b"DIRC" + struct.pack(">II", 2, 2))]
        codes = []
        for label, blob in cases:
            box = os.path.join(root, "case-" + label)
            os.makedirs(os.path.join(box, ".git"))
            os.makedirs(os.path.join(box, "logs"))
            if blob is not None:
                write(os.path.join(box, ".git", "index"), blob)
            code, out, err = capture(["apr", "--repo", box, "--dir", "logs"])
            codes.append((code, out, err.strip().split(":")[0]))
        check([row[0] for row in codes] == [2, 2, 2, 2]
              and [row[1] for row in codes] == ["", "", "", ""]
              and codes[0][2] == APR.NO_INDEX
              and codes[1][2] == APR.BAD_INDEX
              and codes[2][2] == APR.BAD_VERSION
              and codes[3][2] == APR.BAD_INDEX,
              "AC-APR2 refusals are named, rc=2, zero stdout")

        # AC-APR3: prefix filter, per-file bytes, index truth.
        rows, _stats = APR.archive_rows(root, "logs", "state-log-archive-")
        names = [row["file"] for row in rows]
        flags = dict((row["file"], row["tracked"]) for row in rows)
        sizes = dict((row["file"],
                      os.path.getsize(os.path.join(root, "logs", row["file"])))
                     for row in rows)
        check(names == ["state-log-archive-2026-09.md",
                        "state-log-archive-2026-11.md"]
              and flags["state-log-archive-2026-11.md"] is True
              and flags["state-log-archive-2026-09.md"] is False
              and all(row["bytes"] == sizes[row["file"]] for row in rows),
              "AC-APR3 prefix filter and per-file size")

        # AC-APR4: live tree agrees with the index it read.
        code, out, err = capture(["apr", "--repo", REPO])
        live = dict((line.split()[1], line) for line in out.splitlines()
                    if line.startswith("ARCHIVE "))
        tracked_rows = [row for row in live.values() if "tracked=yes" in row]
        summary = [line for line in out.splitlines()
                   if line.startswith("PROVENANCE ")]
        check(code == 0 and err == ""
              and out == out.encode("ascii").decode("ascii")
              and "state-log-archive-2026-11.md" in [
                  row.split()[1] for row in tracked_rows]
              and "state-log-archive-2026-09.md" in live
              and "tracked=no" in live["state-log-archive-2026-09.md"]
              and len(summary) == 1
              and ("files=%d" % len(live)) in summary[0],
              "AC-APR4 live tree: rc=0, ASCII, flags and counts agree")

        # AC-APR5: nothing here can spawn work or open a socket.
        src = open(os.path.join(TOOLS, "archive_provenance.py"),
                   encoding="utf-8").read()
        banned = ["import subprocess", "import socket", "os.system",
                  "os.popen", "urllib", "http.client"]
        check(not any(token in src for token in banned),
              "AC-APR5 the reader imports no child-process or socket door")

        # AC-APR6: --json stable, missing dir refuses with zero bytes.
        first = capture(["apr", "--repo", REPO, "--json"])
        second = capture(["apr", "--repo", REPO, "--json"])
        payload = json.loads(first[1])
        missing = capture(["apr", "--repo", root, "--dir", "nope"])
        check(first[0] == 0 and second[0] == 0
              and first[1] == second[1] and first[2] == ""
              and payload["source"] == ".git/index"
              and isinstance(payload["archives"], list)
              and payload["archives"] == sorted(
                  payload["archives"], key=lambda row: row["file"])
              and missing[0] == 2 and missing[1] == ""
              and missing[2].startswith(APR.NO_DIR),
              "AC-APR6 --json is stable; a missing dir refuses silently")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    print("suite: archive provenance reader (R3091 AC-APR1..6)")
    run()
    total = PASSES + FAILS
    print("SUITE %s %d/%d criteria"
          % ("PASS" if FAILS == 0 and total == EXPECTED_CRITERIA
             else "FAIL", PASSES, EXPECTED_CRITERIA))
    return 0 if FAILS == 0 and total == EXPECTED_CRITERIA else 2


if __name__ == "__main__":
    sys.exit(main())
