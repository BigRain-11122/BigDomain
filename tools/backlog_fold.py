# backlog_fold.py - the src/os/backlog.md carrier fold as one callable, plus a
# --check read. Criteria AC-BLF1..AC-BLF6 were pre-registered in
# src/os/backlog.md (R3369 PIN) BEFORE this file existed.
#
# Why this exists: the board is the one file every window opens, and it grew to
# 5,049,109 B over 761 round blocks. The read cost is paid by every round - the
# R3369 open read was truncated at 26 of 3800 lines - so the carrier, not the
# work, became the limit. The fold was waiting to be done by hand, and every
# hand fold is a chance to cut a round row in half or to rewrite the archive
# instead of appending to it. This module owns the three decisions once:
# does the board need a fold (waterline law), what exactly moves (round-label
# boundary, verbatim), and how the archive grows (append, byte verified).
#
# The surface is small on purpose:
#   measure(path)                 the waterline verdict, read only
#   plan(text, keep)              the fold predicate, no writes
#   fold(root, ...)               plan, verify, append, write
#   check(root)                   the read-only --check report
#
# Layout law: the board is UTF-8 with LF separators (measured: 0 CRLF). A
# carrier that answers CRLF is refused rather than re-landed in a drifted
# dialect (the same defect state_fold E_SF_EOL was written for).
#
# Pure read in --check: nothing is written, no clock is read on that path.
# Source is pure ASCII, stdlib only, zero network imports.

import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime

GATE = 800000
KEEP_ROUNDS = 120
ARCHIVE_REL = os.path.join("logs", "backlog-archive-2026-11.md")
BOARD_REL = os.path.join("src", "os", "backlog.md")
ROW_PREFIX = "- "
HINT_CHARS = 80
ROUND_RE = re.compile(r"R(\d{4})")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERDICTS = ("FOLD-CLEAR", "FOLD-DUE")


class FoldError(Exception):
    """A refusal, raised before any byte is written."""

    def __init__(self, code, detail=""):
        Exception.__init__(self, code)
        self.code = code
        self.detail = detail


def _p(root, rel):
    return os.path.join(root, rel)


def read_text(path):
    with io.open(path, "rb") as f:
        raw = f.read()
    return raw, raw.decode("utf-8")


def row_round(line):
    """The round label a board row carries, or None for a non-row line.

    Tolerant on purpose: rows arrive as '- [R3368 ...', '- [ ] [R3368] ...',
    '- [x] [done 2026-11-23 R3362 ...', so the label is searched inside the
    row head rather than matched by one literal shape.
    """
    if not line.startswith(ROW_PREFIX):
        return None
    m = ROUND_RE.search(line[:HINT_CHARS])
    return int(m.group(1)) if m else None


def round_labels(lines):
    """Distinct labels in order of appearance (newest first on this board)."""
    seen = []
    seen_set = set()
    for line in lines:
        r = row_round(line)
        if r is not None and r not in seen_set:
            seen_set.add(r)
            seen.append(r)
    return seen


def measure(path):
    raw, text = read_text(path)
    lines = text.split("\n")
    labels = round_labels(lines)
    return {
        "path": path,
        "bytes": len(raw),
        "lines": len(lines),
        "rounds": len(labels),
        "newest": labels[0] if labels else None,
        "oldest": labels[-1] if labels else None,
        "gate": GATE,
        "keep_rounds": KEEP_ROUNDS,
        "verdict": "FOLD-DUE" if len(raw) > GATE else "FOLD-CLEAR",
    }


def plan(text, keep=KEEP_ROUNDS):
    """Split the board at the round-label boundary. No writes, no clock."""
    if "\r\n" in text:
        raise FoldError("E_BLF_EOL", "carrier answers CRLF; refusing to re-land it in a drifted dialect")
    lines = text.split("\n")
    labels = round_labels(lines)
    if not labels:
        raise FoldError("E_BLF_NO_ROUNDS", "no row carries a round label")
    newest = labels[0]
    threshold = newest - keep
    if threshold < labels[-1]:
        raise FoldError(
            "E_BLF_NOT_ENOUGH_ROUNDS",
            "board carries %d labels (R%d..R%d), keep=%d needs a remainder to move"
            % (len(labels), newest, labels[-1], keep),
        )
    cut = None
    for i, line in enumerate(lines):
        r = row_round(line)
        if r is not None and r <= threshold:
            cut = i
            break
    if cut is None:
        raise FoldError("E_BLF_BOUNDARY", "no row at or below R%d" % threshold)
    if cut == 0:
        raise FoldError("E_BLF_NO_HEAD", "the boundary is the first line; nothing to keep live")
    head = lines[:cut]
    moved = lines[cut:]
    if not any(x.strip() for x in moved):
        raise FoldError("E_BLF_NO_BLOCK", "the window at R%d is empty" % threshold)
    mixed = 0
    for line in moved:
        r = row_round(line)
        if r is not None and r > threshold:
            mixed += 1
    if "\n".join(head) + "\n" + "\n".join(moved) != text:
        raise FoldError("E_BLF_SPLIT", "split/join is not the inverse of the carrier")
    return {
        "lines": lines,
        "head": head,
        "moved": moved,
        "cut": cut,
        "threshold": threshold,
        "newest": newest,
        "oldest": labels[-1],
        "moved_rows": sum(1 for x in moved if row_round(x) is not None),
        "mixed_newer_rows": mixed,
        "moved_text": "\n".join(moved),
        "head_text": "\n".join(head),
    }


def pointer_row(round_label, threshold, oldest, rows, nbytes, archive_rel):
    return ("- [archive %s] rounds R%d..R%d (%d rows, %d B) folded verbatim on %s -> %s"
            % (round_label, oldest, threshold, rows, nbytes,
               datetime.now().strftime("%Y-%m-%d"), archive_rel.replace("\\", "/")))


def _sha(text_or_bytes):
    if isinstance(text_or_bytes, str):
        text_or_bytes = text_or_bytes.encode("utf-8")
    return hashlib.sha256(text_or_bytes).hexdigest()


def check(root, keep=KEEP_ROUNDS):
    """Read-only report: nothing written, no clock read."""
    board = _p(root, BOARD_REL)
    rep = measure(board)
    archive = _p(root, ARCHIVE_REL)
    rep["archive_path"] = ARCHIVE_REL.replace("\\", "/")
    rep["archive_bytes"] = os.path.getsize(archive) if os.path.exists(archive) else 0
    _, text = read_text(board)
    rep["pointer_rows"] = sum(1 for l in text.split("\n") if l.startswith("- [archive R"))
    try:
        pl = plan(text, keep)
        rep["would_move_bytes"] = len(pl["moved_text"].encode("utf-8"))
        rep["would_move_rows"] = pl["moved_rows"]
        rep["would_keep_bytes"] = len(pl["head_text"].encode("utf-8"))
        rep["boundary_round"] = pl["threshold"]
    except FoldError as e:
        rep["would_move_bytes"] = None
        rep["plan_refusal"] = e.code
    return rep


def fold(root, keep=KEEP_ROUNDS, round_label="R0000", dry_run=False):
    board = _p(root, BOARD_REL)
    archive = _p(root, ARCHIVE_REL)
    raw, text = read_text(board)
    pl = plan(text, keep)
    moved_bytes = pl["moved_text"].encode("utf-8")
    ptr = pointer_row(round_label, pl["threshold"], pl["oldest"],
                      pl["moved_rows"], len(moved_bytes), ARCHIVE_REL)
    head_text = pl["head_text"]
    new_text = head_text + "\n" + ptr + "\n"
    header = ("# --- %s backlog fold: rounds R%d..R%d (%d rows, %d B) moved verbatim from %s\n"
              % (round_label, pl["oldest"], pl["threshold"], pl["moved_rows"],
                 len(moved_bytes), BOARD_REL.replace("\\", "/")))
    rep = {
        "round": round_label,
        "mode": "dry-run" if dry_run else "fold",
        "threshold": pl["threshold"],
        "newest": pl["newest"],
        "oldest": pl["oldest"],
        "oldest_kept": pl["oldest"] if False else None,
        "moved_rows": pl["moved_rows"],
        "mixed_newer_rows": pl["mixed_newer_rows"],
        "bytes_before": len(raw),
        "bytes_after": len(new_text.encode("utf-8")),
        "lines_before": len(pl["lines"]),
        "lines_after": len(new_text.split("\n")),
        "rounds_before": len(round_labels(pl["lines"])),
        "rounds_after_live": len(round_labels(new_text.split("\n"))),
        "moved_sha": _sha(moved_bytes),
        "new_text_sha": _sha(new_text),
        "archive_path": ARCHIVE_REL.replace("\\", "/"),
        "archive_appendix_bytes": len(header.encode("utf-8")) + len(moved_bytes),
        "gate": GATE,
        "verdict_before": "FOLD-DUE" if len(raw) > GATE else "FOLD-CLEAR",
        "verdict_after": "FOLD-DUE" if len(new_text.encode("utf-8")) > GATE else "FOLD-CLEAR",
    }
    labels_kept = round_labels(new_text.split("\n"))
    rep["rounds_after_live"] = len(labels_kept)
    rep["oldest_kept"] = min(labels_kept) if labels_kept else None
    if dry_run:
        rep["dry_run_digest_same"] = True
        rep["archive_sha_matches"] = None
        rep["head_same"] = None
        rep["labels_findable"] = None
        return rep

    before = pl["lines"]
    if new_text.split("\n")[0] != before[0]:
        raise FoldError("E_BLF_HEAD", "the first line would change")
    if os.path.exists(archive):
        _, prev = read_text(archive)
        prev_raw = prev.encode("utf-8")
    else:
        prev_raw = b""
        os.makedirs(os.path.dirname(archive), exist_ok=True)
    with io.open(archive, "ab") as f:
        f.write(header.encode("utf-8"))
        f.write(moved_bytes)
        if not moved_bytes.endswith(b"\n"):
            f.write(b"\n")
    _, after_archive = read_text(archive)
    appendix = after_archive.encode("utf-8")[len(prev_raw):]
    rep["archive_sha_matches"] = _sha(appendix) == _sha(header.encode("utf-8") + moved_bytes) \
        or _sha(appendix) == _sha(header.encode("utf-8") + moved_bytes + b"\n")
    rep["archive_appendix_bytes"] = len(appendix)
    if not rep["archive_sha_matches"]:
        raise FoldError("E_BLF_ARCHIVE", "the appended window is not the moved block")

    tmp = board + ".tmp"
    with io.open(tmp, "wb") as f:
        f.write(new_text.encode("utf-8"))
    os.replace(tmp, board)

    _, landed = read_text(board)
    landed_lines = landed.split("\n")
    rep["head_same"] = landed_lines[0] == before[0]
    # no line lost, none invented: the landed board minus its pointer row is
    # exactly the head, and the archive ends with exactly the moved block.
    rep["no_line_lost"] = landed_lines[:-2] == pl["head"]
    rep["pointer_present"] = landed_lines[-2] == ptr
    labels_after = set(round_labels(landed_lines)) | set(round_labels(after_archive.split("\n")))
    rep["labels_findable"] = set(round_labels(before)) <= labels_after
    if not (rep["head_same"] and rep["no_line_lost"] and rep["pointer_present"]
            and rep["labels_findable"]):
        raise FoldError("E_BLF_VERIFY", "post-write verification failed")
    return rep


def main(argv):
    args = argv[1:]
    if not args or args[0] not in ("--check", "--fold"):
        print("USAGE: backlog_fold.py --check [--json] | --fold [--keep N] [--dry-run] [--round R####]")
        return 2
    keep = KEEP_ROUNDS
    round_label = "R0000"
    dry = False
    as_json = False
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--keep":
            keep = int(args[i + 1])
            i += 2
        elif a == "--round":
            round_label = args[i + 1]
            i += 2
        elif a == "--dry-run":
            dry = True
            i += 1
        elif a == "--json":
            as_json = True
            i += 1
        else:
            print("FAIL flags: E_BLF_BAD_FLAGS %s" % a)
            return 2
    try:
        if args[0] == "--check":
            rep = check(BASE, keep)
            if as_json:
                print(json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1))
            else:
                print("BACKLOG-FOLD bytes=%d gate=%d verdict=%s lines=%d rounds=%d "
                      "newest=R%s oldest=R%s archive_bytes=%d pointer_rows=%d "
                      "would_move=%s would_keep=%s boundary=%s plan_refusal=%s"
                      % (rep["bytes"], rep["gate"], rep["verdict"], rep["lines"],
                         rep["rounds"], rep["newest"], rep["oldest"],
                         rep["archive_bytes"], rep["pointer_rows"],
                         rep.get("would_move_bytes"), rep.get("would_keep_bytes"),
                         rep.get("boundary_round"), rep.get("plan_refusal")))
            return 0
        rep = fold(BASE, keep, round_label, dry)
        print(json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1))
        return 0
    except FoldError as e:
        print("FAIL %s %s" % (e.code, e.detail))
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
