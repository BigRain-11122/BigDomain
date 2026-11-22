"""Battery suite for src/os/heartbeat.py - criterion AC-HB1 (seven arms).

WHY THIS SUITE EXISTS (measured at R3110, not assumed):
`heartbeat.txt` is read by one shipped face (`scan_five_still.ps1`, which takes
the last non-blank of the last five lines and matches `tick (\\d+)`) and written
by 41 shipped scripts with no shared guard. Of the last 60 shipped versions, 20
were a clean tick line, 19 a bare number, 21 something else, and the reader's
rule would FLAG 40 of the 60. This suite pins the single birth site that
replaces that arrangement.

WHAT IS PROVED HERE (one criterion, seven arms):
  a  write then read round-trips, and the bytes on disk are exactly
     b"tick <n>\\n" - one line, no CR, no BOM.
  b  four illegal values (a str, a bool, a negative int, a float) are refused
     with E_HB_TICK and the file on disk is byte-identical afterwards.
  c  parser parity: an independent transcription of the shipped PS rule and
     read_tick agree on six private worlds, including one where the only tick
     line sits just past the five-line window - so the bound is transcribed,
     not guessed - and the shipped PS1 still carries the two tokens the
     transcription rests on.
  d  verify derives its verdict from the two readings: lag=0 PASS, lag>0 FLAG
     with the measured lag, a missing file FLAGs with its own reason.
  e  live parity: read_tick(ROOT) equals the tick in src/os/state.json.
  f  atomicity: after a module write and after a CLI write the folder holds
     only heartbeat.txt (no temp leftovers) and the content really moved.
  g  source discipline: ASCII, no socket import, no external host, and the
     refusal code is the one the arms assert on.

Isolation: private worlds are temp dirs; the only live reads are state.json,
heartbeat.txt and the shipped PS1. Stdlib only.
Exit 0 = all green, 2 = at least one red.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = os.path.join(ROOT, "src", "os", "heartbeat.py")
SCAN = os.path.join(ROOT, "tools", "skills", "bigdomain-loop-scan", "scripts",
                    "scan_five_still.ps1")
BATTERY = os.path.abspath(__file__)

sys.path.insert(0, os.path.join(ROOT, "src", "os"))
import heartbeat as HB  # noqa: E402

CHECKS = []
FAILS = []


def ok(name, cond, detail):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))


def world():
    return tempfile.mkdtemp(prefix="hb-")


def blob_of(root):
    with open(os.path.join(root, "heartbeat.txt"), "rb") as handle:
        return handle.read()


def ps_rule(blob):
    """Independent transcription of the shipped PS rule (last 5, last non-blank)."""
    text = blob.decode("utf-8", "replace").replace("\r\n", "\n")
    tail = [line for line in text.split("\n")[-5:] if line.strip()]
    if not tail:
        return -1
    hit = re.search(r"tick (\d+)", tail[-1])
    return int(hit.group(1)) if hit else -1


def run_cli(args):
    proc = subprocess.run([sys.executable, MODULE] + args,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def main():
    worlds = []
    try:
        # ---- a: round trip, and the bytes are the law.
        root = world()
        worlds.append(root)
        size = HB.write_tick(root, 42)
        raw = blob_of(root)
        ok("AC-HB1 arm a - one tick line, no CR, no BOM, round trip",
           HB.read_tick(root) == 42 and raw == b"tick 42\n" and size == len(raw)
           and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf"),
           "read=%s bytes=%r" % (HB.read_tick(root), raw))

        # ---- b: refusals happen before any write.
        before = raw
        refused = []
        for bad in ("3110", True, -1, 3.7):
            try:
                HB.write_tick(root, bad)
                refused.append("ACCEPTED:%r" % (bad,))
            except ValueError as exc:
                if "E_HB_TICK" in str(exc):
                    refused.append("refused")
                else:
                    refused.append("wrong-code:%s" % exc)
        ok("AC-HB1 arm b - four illegal values refused, file untouched",
           refused == ["refused"] * 4 and blob_of(root) == before,
           "codes=%s untouched=%s" % (refused, blob_of(root) == before))

        # ---- c: parity with the shipped reader, including its five-line bound.
        shapes = [
            ("clean", b"tick 7\n"),
            ("bare-number", b"7\n"),
            ("prose-with-tick", b"R1000 closeout tick 7 landed\n"),
            ("trailing-blanks", b"tick 7\n\n\n\n\n\n"),
            ("tick-just-outside-window", b"tick 7\n" + b"\n" * 6 + b"done\n"),
            ("empty", b""),
        ]
        parity = []
        for label, blob in shapes:
            probe = world()
            worlds.append(probe)
            with open(os.path.join(probe, "heartbeat.txt"), "wb") as handle:
                handle.write(blob)
            mine = HB.read_tick(probe)
            theirs = ps_rule(blob)
            parity.append((label, mine, theirs,
                           (theirs == -1 and mine is None)
                           or (theirs >= 0 and mine == theirs)))
        missing = world()
        worlds.append(missing)
        absent = HB.read_tick(missing)
        scan_src = open(SCAN, encoding="utf-8", errors="replace").read()
        anchored = ("tick (\\d+)" in scan_src and "-Tail 5" in scan_src)
        ok("AC-HB1 arm c - read_tick matches the shipped reader on six shapes;"
           " a missing file reads None; the transcription is anchored",
           all(row[3] for row in parity) and absent is None and anchored,
           "parity=%s absent=%s anchored=%s"
           % ([(p[0], p[1], p[2]) for p in parity], absent, anchored))

        # ---- d: the verdict is derived from two readings.
        fresh = HB.verify(root, 42)
        behind = HB.verify(root, 45)
        ahead = HB.verify(root, 40)
        gone = HB.verify(missing, 45)
        ok("AC-HB1 arm d - verify derives PASS/FLAG and the lag",
           fresh["status"] == "PASS" and fresh["lag"] == 0
           and behind["status"] == "FLAG" and behind["lag"] == 3
           and ahead["status"] == "PASS" and ahead["lag"] == -2
           and ahead["reason"] == "heartbeat_ahead"
           and gone["status"] == "FLAG"
           and gone["reason"] == "heartbeat_missing_or_unparsed",
           "fresh=%s/%s behind=%s/%s ahead=%s/%s/%s gone=%s/%s"
           % (fresh["status"], fresh["lag"], behind["status"], behind["lag"],
              ahead["status"], ahead["lag"], ahead["reason"],
              gone["status"], gone["reason"]))

        # ---- d2: the write hand names an ahead stamp; a fresh write stays
        # byte-identical to the pinned HEARTBEAT-WRITE line (R3322).
        root_ahead = world()
        worlds.append(root_ahead)
        os.makedirs(os.path.join(root_ahead, "src", "os"))
        with open(os.path.join(root_ahead, "src", "os", "state.json"), "w",
                  encoding="utf-8") as handle:
            json.dump({"tick": 40}, handle)
        rc_a, out_a = run_cli(["--write", "42", "--root", root_ahead])
        rc_b, out_b = run_cli(["--write", "40", "--root", root_ahead])
        ok("AC-HB1 arm d2 - an ahead write is named, a fresh write is not",
           rc_a == 0 and "HEARTBEAT-NOTICE ahead=2 state=40" in out_a
           and "reason=heartbeat_ahead" in out_a
           and rc_b == 0 and "HEARTBEAT-NOTICE" not in out_b,
           "ahead=%r fresh=%r" % (out_a.strip(), out_b.strip()))

        # ---- e: the live file and the live state agree right now.
        with open(os.path.join(ROOT, "src", "os", "state.json"),
                  encoding="utf-8") as handle:
            state_tick = int(json.load(handle)["tick"])
        live = HB.read_tick(ROOT)
        ok("AC-HB1 arm e - live heartbeat equals the live state tick",
           live == state_tick,
           "heartbeat=%s state=%s" % (live, state_tick))

        # ---- f: atomicity, through the module and through the CLI.
        root_f = world()
        worlds.append(root_f)
        HB.write_tick(root_f, 10)
        first = sorted(os.listdir(root_f))
        HB.write_tick(root_f, 11)
        second = sorted(os.listdir(root_f))
        moved = HB.read_tick(root_f) == 11 and blob_of(root_f) == b"tick 11\n"
        rc_cli, out_cli = run_cli(["--write", "12", "--root", root_f])
        after_cli = sorted(os.listdir(root_f))
        ok("AC-HB1 arm f - no temp leftovers, and a rewrite really moves",
           first == ["heartbeat.txt"] and second == ["heartbeat.txt"]
           and after_cli == ["heartbeat.txt"] and moved and rc_cli == 0
           and "HEARTBEAT-WRITE tick=12" in out_cli
           and blob_of(root_f) == b"tick 12\n",
           "listings=%s/%s/%s moved=%s cli=%d"
           % (first, second, after_cli, moved, rc_cli))

        # ---- g: source discipline, recomputed rather than promised.
        src = open(MODULE, encoding="utf-8").read()
        own = open(BATTERY, encoding="utf-8").read()
        socket_needle = "import " + "socket"
        host_needle = "https" + "://"
        ascii_ok = True
        for blob in (src, own):
            try:
                blob.encode("ascii")
            except UnicodeEncodeError:
                ascii_ok = False
        ok("AC-HB1 arm g - ASCII, no network import, no external host, coded refusal",
           ascii_ok and socket_needle not in src and host_needle not in src
           and HB.E_HB_TICK == "E_HB_TICK" and '"AC-HB1' in own,
           "ascii=%s socket=%s host=%s code=%s"
           % (ascii_ok, socket_needle in src, host_needle in src, HB.E_HB_TICK))
    finally:
        for path in worlds:
            shutil.rmtree(path, ignore_errors=True)

    criteria = set()
    for name in CHECKS:
        criteria.add(name.split(" ", 1)[0])
    total = len(CHECKS)
    print("suite: %d assertions over %d criteria" % (total, len(criteria)))
    if FAILS:
        print("SUITE FAIL %d/%d failed=%s" % (total - len(FAILS), total, FAILS))
        return 2
    print("SUITE PASS %d/%d" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
