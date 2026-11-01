# stamp_exempt_append.py - a NEW closed row can finally be declared
# Criteria AC-SAP1..AC-SAP6 were pre-registered in state/queue/tech.md as the
# R2294 seed row BEFORE this file existed. Anchor check at HEAD 2026-11-01:
# stamp_exempt_append / AC-SAP / E_SEAP / os-stamp-exempt-append /
# test_stamp_exempt_append were git grep -F zero-occupancy in code (every hit
# was prose or state: the seed row, the board, state.json, state/debt.md,
# status-export.json and three closeout helpers).
#
# Why this exists: queue_done_stamp_exempt reads one pinned declaration of
# accepted stamped rows, but nothing writes it. The 380 entries in
# state/queue/stamp_exempt.json were generated one-off by
# src/os/stamp_exempt_seed_R2280.py, so a row accepted after R2280 can only be
# typed into that file by hand: no duplicate check, no identity check against
# a live debt row, no atomic write. That is exactly the shape debt_append
# already fixed for the debt register, and this is the same fix for the
# acceptance declaration.
#
# The law is imported, never re-derived:
#   * the declaration shape and its per-entry rules come from
#     queue_done_stamp_exempt.read_declaration (the post text is validated by
#     actually running that reader in a throwaway world - the module carries
#     no second copy of the shape);
#   * the live debt rows and the (queue, identity) pair law come from
#     stamp_exempt_review.live_pairs, the same join the reviewer reads.
# The suite proves both imports by patching each one.
#
# Three refusals happen BEFORE any byte of the real file changes:
#   E_SEAP_NO_ROW     the identity matches no live debt row (an acceptance
#                     with nothing to accept).
#   E_SEAP_DUP        the (queue, identity) pair is already declared.
#   E_SEAP_AMBIGUOUS  one entry would cover more than one live row, because
#                     two rows share a text digest; one acceptance must not
#                     silently discharge two rows.
#
# Dry run by default: the report carries before/predicted byte counts and
# nothing is written. With --execute the append is ONE guarded replace from a
# same-directory temp, proved by a read-back of the exact predicted bytes,
# with no temp residue left behind.
#
# Pure apart from the declared write: no clock is read, no network import,
# stdlib only, ASCII source.

import io
import json
import os
import shutil
import sys
import tempfile

import queue_done_stamp_exempt as SEX
import stamp_exempt_guard as SEG
import stamp_exempt_review as SER

DECL_REL = SEX.DECL_REL

TEMP_SUFFIX = ".seap-tmp"

REPORT_KEYS = (
    "path",
    "queue",
    "identity",
    "declared",
    "reason",
    "until",
    "entry_index",
    "entry_count_before",
    "entry_count_after",
    "before_bytes",
    "source_digest",
    "source_bytes",
    "predicted_bytes",
    "wrote",
    "read_back_ok",
)

USAGE = ("usage: stamp_exempt_append.py --queue NAME --identity ID "
         "--declared R<nnnn> --reason TEXT [--until R<nnnn>]\n"
         "                              [--execute] [--root PATH] [--json]\n"
         "  dry run by default (writes nothing, prints the prediction)\n"
         "  exit 0 = planned (dry run) or appended and read back\n"
         "  exit 2 = refused (no live row, duplicate pair, ambiguous pair)\n"
         "  exit 3 = declaration missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


class StampExemptAppendError(Exception):
    """A refused append: the code names why, the detail names the pair."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def render_entry(queue, identity, declared, reason, until=None):
    """The entry in the declaration's own shape (order pinned by ENTRY_KEYS).

    Only shape is decided here. Whether the declaration accepts the result is
    answered by read_declaration below, never by a second copy of its rules.
    """
    for name, value in (("queue", queue), ("identity", identity),
                        ("declared", declared), ("reason", reason)):
        if not isinstance(value, str) or not value.strip():
            raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                         "%s must be a non-empty string" % name)
    entry = {"queue": queue, "identity": identity, "declared": declared,
             "reason": reason}
    if until is not None:
        if not isinstance(until, str) or not until.strip():
            raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                         "until must be a non-empty string")
        entry["until"] = until
    ordered = {}
    for key in SEX.ENTRY_KEYS:
        if key in entry:
            ordered[key] = entry[key]
    return ordered


def _read_text_through_reader(text):
    """Validate a declaration TEXT by running the shipped reader on it.

    The reader only reads a file under a root, so the text is placed in a
    throwaway world for the length of one call and that world is removed.
    """
    world = tempfile.mkdtemp(prefix="bigdomain-seap-")
    try:
        folder = os.path.join(world, os.path.dirname(DECL_REL))
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with io.open(os.path.join(world, DECL_REL), "w", encoding="utf-8",
                     newline="\n") as handle:
            handle.write(text)
        return SEX.read_declaration(world)
    finally:
        shutil.rmtree(world, ignore_errors=True)


def declaration_entries(text):
    """The validated entries of a declaration text (reader is the authority)."""
    try:
        declaration = _read_text_through_reader(text)
    except SEX.QueueDoneStampExemptError as exc:
        raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                     "%s (%s)" % (exc.code, exc.detail))
    if not isinstance(declaration, dict):
        raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                     "reader returned %r"
                                     % (type(declaration).__name__,))
    if declaration.get("status") != "PINNED":
        raise StampExemptAppendError(
            "E_SEAP_UNPINNED",
            "no acceptance declaration at %s - there is nothing to append to"
            % (declaration.get("path") or DECL_REL.replace(os.sep, "/")))
    entries = declaration.get("entries")
    if not isinstance(entries, list):
        raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                     "declaration carries no entries list")
    return entries


def _same_entry(reading, entry):
    """Compare a reader entry with the rendered one field by field.

    The reader normalises (it always carries until, None when absent), so the
    comparison is on fields rather than on raw dict equality.
    """
    if not isinstance(reading, dict):
        return False
    for key in ("queue", "identity", "declared", "reason"):
        if reading.get(key) != entry.get(key):
            return False
    return reading.get("until") == entry.get("until")


def splice(text, entry):
    """Insert one entry before the closing bracket, keeping every prior byte."""
    line = json.dumps(entry, ensure_ascii=True, sort_keys=False)
    marker = "\n  ]"
    pos = text.rfind(marker)
    if pos < 0:
        raise StampExemptAppendError("E_SEAP_BAD_ENTRY",
                                     "declaration carries no closing bracket")
    head = text[:pos]
    separator = "\n    " if head.rstrip().endswith("[") else ",\n    "
    return head + separator + line + text[pos:]


def plan(text, entry, pairs):
    """Validate the pair and the post text; return the report and the post."""
    queue = entry["queue"]
    identity = entry["identity"]
    pair = (queue, identity)
    entries = declaration_entries(text)
    for existing in entries:
        if (existing.get("queue"), existing.get("identity")) == pair:
            raise StampExemptAppendError(
                "E_SEAP_DUP", "%s:%s is already declared" % pair)
    hits = pairs.get(pair) or []
    if not hits:
        raise StampExemptAppendError(
            "E_SEAP_NO_ROW",
            "%s:%s matches no live debt row" % pair)
    if len(hits) > 1:
        names = ",".join("%s:%d" % (row.get("file"), row.get("line"))
                         for row in hits)
        raise StampExemptAppendError(
            "E_SEAP_AMBIGUOUS",
            "%s:%s matches %d live rows (%s)" % (queue, identity, len(hits),
                                                names))
    post = splice(text, entry)
    after = declaration_entries(post)
    if len(after) != len(entries) + 1:
        raise StampExemptAppendError(
            "E_SEAP_BAD_ENTRY",
            "post text carries %d entries, expected %d"
            % (len(after), len(entries) + 1))
    if not _same_entry(after[-1], entry):
        raise StampExemptAppendError(
            "E_SEAP_BAD_ENTRY", "post text did not keep the rendered entry")
    report = {}
    for key in REPORT_KEYS:
        report[key] = entry.get(key)
    report["path"] = DECL_REL.replace(os.sep, "/")
    report["entry_index"] = len(after)
    report["entry_count_before"] = len(entries)
    report["entry_count_after"] = len(after)
    report["before_bytes"] = len(text.encode("utf-8"))
    pinned = SEG.pin(text)
    report["source_digest"] = pinned["digest"]
    report["source_bytes"] = pinned["bytes"]
    report["predicted_bytes"] = len(post.encode("utf-8"))
    report["wrote"] = False
    report["read_back_ok"] = None
    return report, post


def live_pairs(root):
    """The (queue, identity) join from the reviewer (never a second wheel)."""
    try:
        _rows, pairs = SER.live_pairs(root)
    except SER.StampExemptReviewError as exc:
        raise StampExemptAppendError("E_SEAP_BAD_GATE",
                                     "%s (%s)" % (exc.code, exc.detail))
    except Exception as exc:  # noqa: BLE001 - an unreadable gate is not clean
        raise StampExemptAppendError("E_SEAP_BAD_GATE",
                                     "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(pairs, dict):
        raise StampExemptAppendError("E_SEAP_BAD_GATE",
                                     "join returned %r"
                                     % (type(pairs).__name__,))
    return pairs


def append(root, queue, identity, declared, reason, until=None, execute=False):
    """Plan (and optionally perform) one entry append under root."""
    path = os.path.join(root, DECL_REL)
    if not os.path.isfile(path):
        raise StampExemptAppendError(
            "E_SEAP_UNPINNED",
            "no acceptance declaration at %s" % DECL_REL.replace(os.sep, "/"))
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise StampExemptAppendError("E_SEAP_BAD_DECL", "%s (%s)" % (path, exc))
    entry = render_entry(queue, identity, declared, reason, until)
    pairs = live_pairs(root)
    report, post = plan(text, entry, pairs)
    if not execute:
        return report
    data = post.encode("utf-8")
    if len(data) != report["predicted_bytes"]:
        raise StampExemptAppendError(
            "E_SEAP_PREDICT",
            "payload is %d bytes, predicted %d"
            % (len(data), report["predicted_bytes"]))
    temp = path + TEMP_SUFFIX
    try:
        guard = SEG.commit(
            path,
            {"digest": report["source_digest"], "bytes": report["source_bytes"]},
            data, TEMP_SUFFIX,
            {"write": "E_SEAP_WRITE", "readback": "E_SEAP_READBACK",
             "residue": "E_SEAP_RESIDUE",
             "unreadable": "E_SEAP_BAD_DECL"})
    except SEG.StampGuardError as exc:
        raise StampExemptAppendError(exc.code, exc.detail)
    report["wrote"] = guard["wrote"]
    report["read_back_ok"] = guard["read_back_ok"]
    if os.path.exists(temp):
        raise StampExemptAppendError("E_SEAP_RESIDUE",
                                     "temp file survived: %s" % temp)
    return report


def one_line(report):
    return ("STAMP EXEMPT APPEND queue=%s identity=%s declared=%s "
            "entries=%d->%d before=%dB after=%dB wrote=%s readback=%s"
            % (report["queue"], report["identity"], report["declared"],
               report["entry_count_before"], report["entry_count_after"],
               report["before_bytes"], report["predicted_bytes"],
               "yes" if report["wrote"] else "no",
               "n/a" if report["read_back_ok"] is None
               else ("ok" if report["read_back_ok"] else "BAD")))


def to_json(report):
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report.get(key)
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    queue = None
    identity = None
    declared = None
    reason = None
    until = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--queue" and index + 1 < len(argv):
            queue = argv[index + 1]
            index += 2
        elif arg == "--identity" and index + 1 < len(argv):
            identity = argv[index + 1]
            index += 2
        elif arg == "--declared" and index + 1 < len(argv):
            declared = argv[index + 1]
            index += 2
        elif arg == "--reason" and index + 1 < len(argv):
            reason = argv[index + 1]
            index += 2
        elif arg == "--until" and index + 1 < len(argv):
            until = argv[index + 1]
            index += 2
        elif arg == "--execute":
            execute = True
            index += 1
        elif arg == "--json":
            as_json = True
            index += 1
        elif arg == "--root" and index + 1 < len(argv):
            root = argv[index + 1]
            index += 2
        else:
            sys.stderr.write("E_SEAP_BAD_ARGS: unknown flag %r\n%s"
                             % (arg, USAGE))
            return 5
    if not queue or not identity or not declared or not reason:
        sys.stderr.write("E_SEAP_BAD_ARGS: --queue, --identity, --declared "
                         "and --reason are all required\n%s" % USAGE)
        return 5
    try:
        report = append(root, queue, identity, declared, reason, until,
                        execute)
    except StampExemptAppendError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2 if exc.code.startswith(("E_SEAP_NO_ROW", "E_SEAP_DUP",
                                         "E_SEAP_AMBIGUOUS")) else 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(one_line(report) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))