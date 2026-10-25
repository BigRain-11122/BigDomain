"""Sweep stale apimarket sandbox temp worlds (D-20261025-15).

The apimarket acceptance suites build their throwaway world with
tempfile.mkdtemp(prefix=...) and never remove it: 62 mkdtemp calls, zero
rmtree, which by 2026-10-25 had left 24,057 directories holding 6.52 GB
under %TEMP%. D-20261025-15 requires that any cleanup be ATTRIBUTED
first (never a blind delete), so this tool only touches a directory when
all three anchors hold:

  1. the name matches our suite prefix family (apimarket-* / apimarket_*
     or am<family>-);
  2. it contains at least one of our world signature files (apimarket.db,
     ledger.db, member.db, member-pay.db, member-ledger.db, empty.html,
     config.json) - an unrelated tool that happens to use a similar name
     is therefore never a candidate;
  3. it is older than --min-age-hours (default 24) by mtime.

Safety: the directory is first renamed to a transient sibling name. On
Windows a rename fails when a live process still holds a file inside, so
a busy world is skipped rather than deleted; only a successful rename is
followed by the recursive delete.

Usage:
  python sweep_suite_tmp.py                 # dry run, 24h policy
  python sweep_suite_tmp.py --execute
  python sweep_suite_tmp.py --min-age-hours 1 --execute --json-out out.json

Source is pure ASCII; no network imports; writes nothing outside the
candidate directories and the optional --json-out file.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import time

NAME_RE = re.compile(
    r"^(apimarket[-_]|am(?:watchalerts|marketfeed|feedlisting|buyertodo|"
    r"rpx|ql|qa|sl|bq|sa|amlg|pi|jprev|feeddemo|btprev|lg|pv|r|qbq)[-_])")

SIGNATURES = ("apimarket.db", "ledger.db", "member.db", "member-pay.db",
              "member-ledger.db", "empty.html", "config.json")


def dir_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def has_signature(path):
    try:
        names = os.listdir(path)
    except OSError:
        return False
    return any(name in SIGNATURES for name in names)


def candidates(root, min_age_hours):
    cutoff = time.time() - min_age_hours * 3600.0
    out = []
    try:
        entries = os.scandir(root)
    except OSError:
        return out
    for entry in entries:
        try:
            if not entry.is_dir(follow_symlinks=False):
                continue
            if not NAME_RE.match(entry.name):
                continue
            if entry.stat(follow_symlinks=False).st_mtime >= cutoff:
                continue
            if not has_signature(entry.path):
                continue
        except OSError:
            continue
        out.append(entry.path)
    out.sort()
    return out


def created_at(stat):
    """Creation time proxy: real birth time where the platform has it,
    Windows st_ctime (creation) otherwise st_mtime."""
    birth = getattr(stat, "st_birthtime", None)
    if birth is not None:
        return birth
    if sys.platform == "win32":
        return stat.st_ctime
    return stat.st_mtime


def run_candidates(root, started_at):
    """Worlds created AT OR AFTER started_at with the same two content
    anchors (name family + signature file).

    This is the battery-window leg: the age policy of candidates() is
    replaced by an explicit window so a run only ever reclaims what it
    itself just produced. Anything that existed before started_at is
    never a candidate, even when it matches - that keeps a concurrent
    window's worlds and older evidence worlds out of reach (AC-TMP3).
    """
    out = []
    try:
        entries = os.scandir(root)
    except OSError:
        return out
    for entry in entries:
        try:
            if not entry.is_dir(follow_symlinks=False):
                continue
            stat = entry.stat(follow_symlinks=False)
            if created_at(stat) < started_at:
                continue
            if not NAME_RE.match(entry.name):
                continue
            if not has_signature(entry.path):
                continue
        except OSError:
            continue
        out.append(entry.path)
    out.sort()
    return out


def sweep_run_temps(root, started_at, execute=True):
    """Reclaim only this run's own worlds (AC-TMP1..AC-TMP6).

    Shares the ownership anchors and the rename-probe delete with the
    standalone sweep - one implementation, two callers (AC-TMP6).
    Returns a report dict; never raises for a single bad directory.
    """
    cands = run_candidates(root, started_at)
    removed = 0
    busy = 0
    failed = 0
    reclaimed = 0
    for path in cands:
        ok, size, reason = sweep(path, execute)
        if ok:
            removed += 1
            reclaimed += size
        elif reason == "dry-run":
            continue
        elif reason == "busy-or-locked":
            busy += 1
        else:
            failed += 1
    return {
        "root": root,
        "started_at": started_at,
        "mode": "execute" if execute else "dry-run",
        "candidates": len(cands),
        "removed": removed,
        "busy_skipped": busy,
        "failed": failed,
        "bytes": reclaimed,
        "mib": round(reclaimed / 1048576.0, 2),
    }


def sweep(path, execute):
    """Delete one world. Returns (removed, bytes, skipped_reason)."""
    size = dir_bytes(path)
    if not execute:
        return False, size, "dry-run"
    probe = path + ".sweeping"
    try:
        os.rename(path, probe)
    except OSError:
        return False, size, "busy-or-locked"
    try:
        shutil.rmtree(probe)
    except OSError as exc:
        # Put it back if the removal failed, so nothing is half-deleted
        # under a name the next sweep would not recognise.
        try:
            os.rename(probe, path)
        except OSError:
            pass
        return False, size, "rmtree-failed:%s" % exc.__class__.__name__
    return True, size, "removed"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sweep stale apimarket sandbox temp worlds")
    parser.add_argument("--root", default=None,
                        help="temp root (default: system TEMP)")
    parser.add_argument("--min-age-hours", type=float, default=24.0,
                        help="only worlds older than this (default 24)")
    parser.add_argument("--execute", action="store_true",
                        help="delete; without it this is a dry run")
    parser.add_argument("--json-out", default=None,
                        help="optional report path")
    args = parser.parse_args(argv)

    root = args.root or tempfile.gettempdir()
    if not os.path.isdir(root):
        print("FAIL: temp root not found: %s" % root)
        return 2
    if args.min_age_hours < 0:
        print("FAIL: --min-age-hours must be >= 0")
        return 2

    cands = candidates(root, args.min_age_hours)
    removed = 0
    reclaimed = 0
    busy = 0
    failed = 0
    planned = 0
    for path in cands:
        ok, size, reason = sweep(path, args.execute)
        planned += size
        if ok:
            removed += 1
            reclaimed += size
        elif reason == "dry-run":
            continue
        elif reason == "busy-or-locked":
            busy += 1
        else:
            failed += 1

    report = {
        "root": root,
        "min_age_hours": args.min_age_hours,
        "mode": "execute" if args.execute else "dry-run",
        "candidates": len(cands),
        "removed": removed,
        "busy_skipped": busy,
        "failed": failed,
        "bytes": reclaimed if args.execute else planned,
        "mib": round((reclaimed if args.execute else planned) / 1048576.0, 2),
    }
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
    print("SWEEP %s: candidates=%d removed=%d busy=%d failed=%d reclaimed=%.2f MiB"
          % (report["mode"], len(cands), removed, busy, failed, report["mib"]))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())