"""Backlog-fold suite (R3369; criteria AC-BLF1..AC-BLF6 were pre-registered in
src/os/backlog.md as the R3369 PIN BEFORE tools/backlog_fold.py existed).

What this proves: the board carrier is folded by a predicate the code owns
once, not by a hand cut (AC-BLF1 waterline read is pure and answers the disk
size); a fold keeps the newest rounds live, moves the rest verbatim and lands
the archive by append with the moved block byte-verified (AC-BLF2); every
round label that existed before is still findable in live or archive after
(AC-BLF3); every refusal lands before any byte and a dry run writes nothing
(AC-BLF4); a second fold on the folded board is a named no-op refusal and the
head row survives (AC-BLF5); and the module is ASCII, stdlib only, zero
network (AC-BLF6).

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import hashlib
import io
import os
import shutil
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(BASE)
REPO = os.path.dirname(SRC)
sys.path.insert(0, os.path.join(REPO, "tools"))

import backlog_fold as BF  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(REPO, "tools", "backlog_fold.py")
LABEL = "os-backlog-fold"

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


def make_world(rows, tail_lines=0, pad=40):
    """A temp repo root holding a synthetic board."""
    world = tempfile.mkdtemp(prefix="blfold-")
    os.makedirs(os.path.join(world, "src", "os"), exist_ok=True)
    os.makedirs(os.path.join(world, "logs"), exist_ok=True)
    lines = []
    for i, r in enumerate(sorted(rows, reverse=True)):
        lines.append("- [R%04d row %d payload %s]" % (r, i, "x" * pad))
    for j in range(tail_lines):
        lines.append("- [R%04d tail %d %s]" % (min(rows), j, "y" * pad))
    text = "\n".join(lines) + "\n"
    path = os.path.join(world, "src", "os", "backlog.md")
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return world, path, text


def digest_tree(world):
    h = hashlib.sha256()
    for root, dirs, files in os.walk(world):
        dirs.sort()
        for name in sorted(files):
            p = os.path.join(root, name)
            h.update(os.path.relpath(p, world).encode("utf-8"))
            with io.open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def drop(world):
    shutil.rmtree(world, ignore_errors=True)


def run():
    # AC-BLF1: the waterline is the disk size, and the check path writes
    # nothing (tree digest holds across the read).
    world, path, text = make_world(list(range(3300, 3440)), pad=6000)
    try:
        small = os.path.join(world, "small.md")
        with io.open(small, "w", encoding="utf-8", newline="") as fh:
            fh.write("\n".join("- [R3300 tiny]" for _ in range(10)) + "\n")
        before = digest_tree(world)
        m1 = BF.measure(path)
        m2 = BF.measure(small)
        rep = BF.check(world)
        after = digest_tree(world)
        check(m1["verdict"] == "FOLD-DUE" and m2["verdict"] == "FOLD-CLEAR"
              and m1["gate"] == 800000 and m1["bytes"] == len(text.encode("utf-8"))
              and rep["verdict"] == "FOLD-DUE" and before == after,
              "AC-BLF1 the waterline reads the disk size (over gate = FOLD-DUE, "
              "under gate = FOLD-CLEAR) and --check writes nothing")
    finally:
        drop(world)

    # AC-BLF2/BLF3: the fold keeps the newest rounds live, moves the rest
    # verbatim, appends to the archive byte-verified, and every old label is
    # still findable.
    world, path, text = make_world(list(range(3200, 3340)), tail_lines=3, pad=6000)
    try:
        labels_before = set(BF.round_labels(text.split("\n")))
        head_before = text.split("\n")[0]
        pre_dry = digest_tree(world)
        dry = BF.fold(world, BF.KEEP_ROUNDS, "R3369", dry_run=True)
        dry_ok = (digest_tree(world) == pre_dry
                  and dry["mode"] == "dry-run"
                  and dry["bytes_after"] < dry["bytes_before"])
        archive_path = os.path.join(world, "logs", "backlog-archive-2026-11.md")
        rep = BF.fold(world, BF.KEEP_ROUNDS, "R3369")
        with io.open(path, "rb") as fh:
            live = fh.read().decode("utf-8")
        with io.open(archive_path, "rb") as fh:
            arch = fh.read().decode("utf-8")
        live_labels = set(BF.round_labels(live.split("\n")))
        arch_labels = set(BF.round_labels(arch.split("\n")))
        check(dry_ok and dry["new_text_sha"] == rep["new_text_sha"]
              and rep["head_same"] is True and rep["no_line_lost"] is True
              and rep["pointer_present"] is True
              and rep["archive_sha_matches"] is True
              and rep["bytes_after"] < rep["bytes_before"]
              and rep["verdict_after"] == "FOLD-CLEAR"
              and live.split("\n")[0] == head_before
              and live.split("\n")[-2].startswith("- [archive R3369]"),
              "AC-BLF2 the fold keeps the head row, moves the tail verbatim, "
              "appends one byte-verified window and the live board drops under "
              "the gate (dry run wrote nothing and predicted the landed text)")
        check(labels_before <= (live_labels | arch_labels)
              and rep["labels_findable"] is True,
              "AC-BLF3 every round label present before the fold is still "
              "findable in the live board or the archive")
    finally:
        drop(world)

    # AC-BLF4: refusals land before any byte.
    world, path, text = make_world(list(range(3200, 3300)))
    try:
        with io.open(path, "wb") as fh:
            fh.write(text.replace("\n", "\r\n").encode("utf-8"))
        before = digest_tree(world)
        eol = None
        try:
            BF.fold(world, BF.KEEP_ROUNDS, "R3369")
        except BF.FoldError as exc:
            eol = exc.code
        short = None
        try:
            BF.plan(text, keep=200)
        except BF.FoldError as exc:
            short = exc.code
        check(eol == "E_BLF_EOL" and short == "E_BLF_NOT_ENOUGH_ROUNDS"
              and digest_tree(world) == before,
              "AC-BLF4 a CRLF carrier and a board with too few rounds are both "
              "refused before any byte is written")
    finally:
        drop(world)

    # AC-BLF5: a second fold is a named no-op refusal, and the head row is the
    # one the first fold kept.
    world, path, text = make_world(list(range(3200, 3340)))
    try:
        head_before = text.split("\n")[0]
        first = BF.fold(world, BF.KEEP_ROUNDS, "R3369")
        after_first = digest_tree(world)
        second = None
        try:
            BF.fold(world, BF.KEEP_ROUNDS, "R3369")
        except BF.FoldError as exc:
            second = exc.code
        check(second == "E_BLF_NOT_ENOUGH_ROUNDS"
              and digest_tree(world) == after_first
              and first["head_same"] is True
              and first["mixed_newer_rows"] == 0,
              "AC-BLF5 a second fold on the folded board is a named refusal "
              "that writes nothing")
    finally:
        drop(world)

    # AC-BLF6: ASCII source, stdlib only, no network import.
    with io.open(MODULE, "rb") as fh:
        raw = fh.read()
    text_mod = raw.decode("utf-8")
    ascii_ok = all(ord(ch) < 128 for ch in text_mod)
    banned = ("import socket", "import ssl", "import http", "import urllib",
              "import requests", "from http", "from urllib")
    net_ok = not any(b in text_mod for b in banned)
    check(ascii_ok and net_ok and "GATE = 800000" in text_mod,
          "AC-BLF6 the module is ASCII, stdlib only, zero network and owns "
          "its waterline constant")


if __name__ == "__main__":
    run()
    print("SUITE %s %d/%d" % (
        "PASS" if FAILS == 0 else "FAIL", PASSES + FAILS, EXPECTED_CRITERIA),
        flush=True)
    sys.exit(0 if FAILS == 0 else 2)
