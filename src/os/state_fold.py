# state_fold.py - the state.json log fold as one callable, plus a --check read
# Criteria AC-SF1..AC-SF6 were pre-registered in state/queue/tech.md (R2240 b)
# BEFORE this file existed.
#
# Why this exists: the fold has been executed by hand in many windows - the
# waterline was measured by eyeballing a file size, the window was chosen by
# counting lines, and the archive append was a bespoke script each time. Each
# hand execution was a chance to cut a round line in half or to rewrite the
# archive instead of appending to it. This module owns the three decisions
# once: does the file need a fold (waterline law), what exactly moves to the
# archive (verbatim preservation plus token coverage), and how the archive
# grows (append, never rewrite).
#
# The surface is small on purpose:
#   measure(size)                      the waterline verdict
#   plan_fold(raw, state, w1, w2, s)   the fold predicate, no writes
#   append_archive(path, header, ln)    the verbatim append, byte verified
#   fold(root, ...)                     one callable: plan, back up, append, write
#   check(root)                         the read-only --check report
#
# Layout law: the live state.json is the PS 5.1 layout - one log item per
# line, indented by exactly 16 spaces, CRLF separators. A file whose layout
# does not match the parsed log length is refused rather than guessed at.
#
# Pure read in --check: nothing is written, no clock is read on that path.
# Source is pure ASCII, stdlib only, zero network imports, and the fold
# predicate is single-owned here (logs_toolkit is not imported).

import hashlib
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime

GATE = 78500

# Token family from the group ledger grammar (AC/BD/C/D/O/T/XL/OH/R).
PAT = re.compile(r'(?:AC|BD|C|D|O|T|XL|OH|R)-[0-9A-Za-z][0-9A-Za-z]*'
                 r'(?:-[0-9A-Za-z]+)*')

VERDICTS = ("FOLD-CLEAR", "FOLD-DUE")

ITEM_INDENT = 16
ITEM_PREFIX = " " * ITEM_INDENT

CHECK_KEYS = ("state_path", "archive_path", "bytes", "log_lines", "gate",
              "margin", "fold_needed", "verdict", "archive_present")

PLAN_KEYS = ("window_start", "window_end", "window_lines",
             "window_content_bytes", "summary_head", "tokens_total",
             "tokens_missing", "token_ok", "gate", "reserve_bytes",
             "predicted_bytes", "margin", "gate_ok", "preop_sha16",
             "newline", "folded_log_len")

ARCHIVE_KEYS = ("path", "created", "prefix_intact", "before_bytes",
                "after_bytes", "appendix_bytes", "sha16")


class StateFoldError(Exception):
    """Raised when the fold cannot produce an honest result."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def state_path(root):
    return os.path.join(root, "src", "os", "state.json")


def default_archive(root, now=None):
    stamp = (now or datetime.now()).strftime("%Y-%m")
    return os.path.join(root, "logs", "state-log-archive-%s.md" % stamp)


def measure(disk_bytes, gate=GATE):
    """Waterline law: fold_needed iff the disk size is strictly over gate."""
    margin = gate - int(disk_bytes)
    fold_needed = margin < 0
    return {
        "bytes": int(disk_bytes),
        "gate": int(gate),
        "margin": margin,
        "fold_needed": fold_needed,
        "verdict": "FOLD-DUE" if fold_needed else "FOLD-CLEAR",
    }


def read_state(path=None):
    """Read and parse the state file; fail closed on anything unexpected."""
    if path is None:
        raise StateFoldError("E_SF_BAD_ARGS", "state path is required")
    try:
        with io.open(path, "rb") as handle:
            raw = handle.read()
    except (IOError, OSError) as exc:
        raise StateFoldError("E_SF_BAD_STATE", "%s (%s)" % (path, exc))
    try:
        state = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise StateFoldError("E_SF_BAD_STATE", "%s (%s)" % (path, exc))
    log = state.get("log")
    if not isinstance(log, list) or not all(isinstance(x, str) for x in log):
        raise StateFoldError("E_SF_BAD_STATE", "%s (log is not a string list)"
                             % path)
    return raw, state


def split_layout(text, log_len):
    """Locate the log item lines in the canonical PS layout.

    Returns a dict with the split lines, the newline, the ordered item line
    indices and the first item index, or None when the file is not in the
    canonical layout for this log length.
    """
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    first = None
    items = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('"log"') and stripped.endswith("["):
            first = index
            continue
        if first is None:
            continue
        if (len(line) > ITEM_INDENT and line[:ITEM_INDENT] == ITEM_PREFIX
                and line[ITEM_INDENT] == '"'):
            items.append(index)
        elif stripped.startswith("]"):
            break
    if first is None or len(items) != log_len:
        return None
    return {
        "lines": lines,
        "newline": newline,
        "item_index": items,
        "first_item": items[0],
    }


def ps_escape(value):
    """Serialize one log string in the on-disk PS 5.1 style."""
    literal = json.dumps(value, ensure_ascii=False)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"),
                         ("&", "\\u0026"), ("'", "\\u0027")):
        literal = literal.replace(char, escape)
    return literal


def plan_fold(raw, state, window_start, window_end, summary, reserve=0,
              gate=GATE):
    """The fold predicate. Returns (plan, folded_text); writes nothing."""
    if not isinstance(summary, str) or not summary.strip():
        raise StateFoldError("E_SF_BAD_SUMMARY", "summary must be a line")
    if "\n" in summary or "\r" in summary:
        raise StateFoldError("E_SF_BAD_SUMMARY", "summary must be one line")
    log = state["log"]
    count = len(log)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StateFoldError("E_SF_BAD_LAYOUT", "state is not utf-8 (%s)"
                             % exc)
    layout = split_layout(text, count)
    if layout is None:
        raise StateFoldError("E_SF_BAD_LAYOUT",
                             "log item lines do not match log length %d"
                             % count)
    start = int(window_start)
    end = int(window_end)
    if start < 1 or end < start or end > count:
        raise StateFoldError("E_SF_WINDOW",
                             "window %d:%d is out of log bounds 1:%d"
                             % (start, end, count))
    window = log[start - 1:end]
    tokens = set()
    for line in window:
        tokens |= set(PAT.findall(line))
    missing = sorted(token for token in tokens if token not in summary)
    literal = ITEM_PREFIX + ps_escape(summary)
    if end < count:
        literal += ","
    drop = end - start + 1
    insert_at = layout["item_index"][start - 1]
    new_lines = (layout["lines"][:insert_at] + [literal]
                 + layout["lines"][insert_at + drop:])
    folded_text = layout["newline"].join(new_lines)
    predicted = len(folded_text.encode("utf-8"))
    new_log_len = count - drop + 1
    plan = {
        "window_start": start,
        "window_end": end,
        "window_lines": drop,
        "window_content_bytes": sum(len(line.encode("utf-8"))
                                    for line in window),
        "summary_head": summary[:60],
        "tokens_total": len(tokens),
        "tokens_missing": missing,
        "token_ok": not missing,
        "gate": int(gate),
        "reserve_bytes": int(reserve),
        "predicted_bytes": predicted,
        "margin": int(gate) - predicted,
        "gate_ok": predicted + int(reserve) <= int(gate),
        "preop_sha16": hashlib.sha256(raw).hexdigest()[:16],
        "newline": "CRLF" if layout["newline"] == "\r\n" else "LF",
        "folded_log_len": new_log_len,
    }
    return plan, folded_text


def archive_appendix(header, window_lines):
    """The exact bytes a fold contributes to the archive."""
    if not isinstance(header, str) or not header.startswith("# --- "):
        raise StateFoldError("E_SF_BAD_HEADER",
                             "header must start with '# --- '")
    if "\n" in header or "\r" in header:
        raise StateFoldError("E_SF_BAD_HEADER", "header must be one line")
    blob = header + "\n" + "\n".join(window_lines) + "\n"
    return blob.encode("utf-8")


def append_archive(path, header, window_lines, allow_create=False, now=None):
    """Append the fold block verbatim; never rewrite what is already there."""
    appendix = archive_appendix(header, window_lines)
    if os.path.isfile(path):
        with io.open(path, "rb") as handle:
            before = handle.read()
        separator = b""
        if before and not before.endswith(b"\n"):
            separator = b"\n"
        expected = before + separator + appendix
        with io.open(path, "ab") as handle:
            handle.write(separator + appendix)
        with io.open(path, "rb") as handle:
            after = handle.read()
        if after != expected:
            raise StateFoldError("E_SF_ARCHIVE",
                                 "append read-back differs from expectation")
        return {
            "path": path,
            "created": False,
            "prefix_intact": after.startswith(before),
            "before_bytes": len(before),
            "after_bytes": len(after),
            "appendix_bytes": len(separator) + len(appendix),
            "sha16": hashlib.sha256(after).hexdigest()[:16],
        }
    if not allow_create:
        raise StateFoldError("E_SF_ARCHIVE_MISSING",
                             "%s (pass allow_create to create it)" % path)
    stamp = (now or datetime.now()).strftime("%Y-%m-%d")
    preamble = ("# logs/%s (created by state_fold.py %s)\n"
                % (os.path.basename(path), stamp)).encode("utf-8")
    blob = preamble + appendix
    with io.open(path, "wb") as handle:
        handle.write(blob)
    with io.open(path, "rb") as handle:
        if handle.read() != blob:
            raise StateFoldError("E_SF_ARCHIVE",
                                 "create read-back differs from expectation")
    return {
        "path": path,
        "created": True,
        "prefix_intact": False,
        "before_bytes": 0,
        "after_bytes": len(blob),
        "appendix_bytes": len(blob),
        "sha16": hashlib.sha256(blob).hexdigest()[:16],
    }


def fold(root, round_label, fold_no, window_start, window_end, summary,
         reserve=0, gate=GATE, execute=True, archive_path=None, now=None):
    """One callable: plan the fold, back up, append the archive, write state.

    A dry run (execute=False) returns the plan and writes nothing. An
    execute run refuses before any write when the plan is not clean.
    """
    path = state_path(root)
    raw, state = read_state(path)
    plan, folded_text = plan_fold(raw, state, window_start, window_end,
                                  summary, reserve=reserve, gate=gate)
    fail = []
    if plan["tokens_missing"]:
        fail.append("token-missing")
    if not plan["gate_ok"]:
        fail.append("gate-exceed")
    result = dict(plan)
    result["mode"] = "execute" if execute else "dry-run"
    result["round"] = round_label
    result["fold_no"] = fold_no
    result["would_fail"] = fail
    if not execute or fail:
        return result
    stamp = now or datetime.now()
    window = state["log"][plan["window_start"] - 1:plan["window_end"]]
    backup_path = os.path.join(root, "logs",
                               "state-preop-%s.bak" % round_label)
    with io.open(backup_path, "wb") as handle:
        handle.write(raw)
    with io.open(backup_path, "rb") as handle:
        if handle.read() != raw:
            raise StateFoldError("E_SF_BACKUP", "backup read-back differs")
    archive = archive_path or default_archive(root, stamp)
    header = ("# --- %s fold append (%s, %d lines verbatim: %s, "
              "fold %s window, pre-op sha16 %s)"
              % (round_label, stamp.strftime("%Y-%m-%d"),
                 plan["window_lines"], "log window", fold_no,
                 plan["preop_sha16"]))
    appended = append_archive(archive, header, window,
                             allow_create=True, now=stamp)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path),
                               prefix=".state-fold-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(folded_text.encode("utf-8"))
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    with io.open(path, "rb") as handle:
        post_raw = handle.read()
    post_state = json.loads(post_raw.decode("utf-8"))
    expected_log = (state["log"][:plan["window_start"] - 1] + [summary]
                    + state["log"][plan["window_end"]:])
    result.update({
        "backup_path": backup_path,
        "archive": appended,
        "post_bytes": len(post_raw),
        "predicted_eq_actual": (len(post_raw) == plan["predicted_bytes"]
                                and post_raw == folded_text.encode("utf-8")
                                and post_state["log"] == expected_log),
    })
    return result


def check(root, gate=GATE):
    """The read-only waterline report behind --check."""
    path = state_path(root)
    raw, state = read_state(path)
    size = os.path.getsize(path)
    water = measure(size, gate)
    archive = default_archive(root)
    return {
        "state_path": path,
        "archive_path": archive,
        "bytes": water["bytes"],
        "log_lines": len(state["log"]),
        "gate": water["gate"],
        "margin": water["margin"],
        "fold_needed": water["fold_needed"],
        "verdict": water["verdict"],
        "archive_present": os.path.isfile(archive),
    }


def to_json(report, keys):
    ordered = {}
    for key in keys:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def render(report):
    return ("STATE FOLD bytes=%d gate=%d margin=%d log_lines=%d verdict=%s "
            "archive=%s" % (report["bytes"], report["gate"],
                            report["margin"], report["log_lines"],
                            report["verdict"],
                            "present" if report["archive_present"]
                            else "absent"))


USAGE = ("usage: state_fold.py --check [--root PATH] [--json]\n"
         "  exit 0 = FOLD-CLEAR (disk size at or under the waterline)\n"
         "  exit 2 = FOLD-DUE (disk size over the waterline) or bad flags\n"
         "  exit 3 = the state file is missing or not readable\n")


def main(argv):
    check_mode = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check_mode = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SF_BAD_ARGS: --root needs a path\n")
                return 2
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SF_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 2
        index += 1
    if not check_mode:
        sys.stdout.write("E_SF_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 2
    try:
        report = check(root)
    except StateFoldError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report, CHECK_KEYS))
    else:
        sys.stdout.write(render(report) + "\n")
    return 2 if report["fold_needed"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))