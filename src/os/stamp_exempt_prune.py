# stamp_exempt_prune.py - the accepted-stamp declaration can now shrink
# Criteria AC-SEPR1..AC-SEPR6 were pre-registered in state/queue/tech.md as the
# R2307 seed row BEFORE this file existed. Anchor check at HEAD 2026-11-01:
# stamp_exempt_prune / AC-SEPR / E_SPR / os-stamp-exempt-prune /
# test_stamp_exempt_prune were all git grep -F zero-occupancy rc=1 (every hit
# was prose: the queue row, the board, the closeout and the state log).
#
# Why this exists: stamp_exempt_append lets the declaration GROW and
# stamp_exempt_review names the two ways it rots, but nothing can retire an
# entry. So an entry whose row was amended after the fact (its text digest
# moves, the reviewer reads it MISSING) or whose `until` round has passed (the
# reader reads the row EXPIRED) stays in the file forever and the list only
# grows. The reviewer diagnoses; the patient never gets treated.
#
# This module is the treatment, and it does NOT rejoin the two sides:
#   * the MISSING half comes from stamp_exempt_review.audit (its own report,
#     its own entry indices), and
#   * the expired half comes from queue_done_stamp_exempt.audit row statuses
#     (the same reader the reviewer reconciles against), joined to the
#     declaration by (queue, identity) only to name which ENTRY the reader
#     already called expired.
# No digest is recomputed here, no row text is parsed here.
#
# AC-SEPR2 dry run by default: a plan names every entry it would drop with its
# declaration index, queue and identity, and prints before/after bytes. Only
# --execute touches the file. The index is the 1-based declaration position,
# the same locator stamp_exempt_review prints for a MISSING entry, so both
# halves of a plan are addressable one way.
#
# AC-SEPR3 the splice is span surgery on the shipped text: entry spans are
# located by json raw_decode inside the exemptions array, so a one-line entry
# and a pretty-printed one behave the same. A surviving entry keeps its exact
# bytes and its order - only the separator comma that happened to belong to a
# dropped neighbour moves with it. The suite pins that by comparing every
# surviving span text byte-for-byte against the original.
#
# AC-SEPR4 the post text is validated by the shipped reader (through
# stamp_exempt_append.declaration_entries -> read_declaration) and must carry
# exactly entries - retired. Never a second copy of the entry rules.
#
# AC-SEPR5 an executed prune is one guarded replace through stamp_exempt_guard,
# read-back, with no temp residue left behind on either path. A refused plan
# (nothing to retire, unpinned, count mismatch, bad splice) writes nothing.
#
# AC-SEPR6 purity: no clock, no network import, stdlib only, ASCII source, and
# the module prints its own reconcile label (one_line) so a window can be read
# without the caller paraphrasing it.

import io
import json
import os
import sys

import queue_done_stamp_exempt as SEX
import stamp_exempt_append as SEPA
import stamp_exempt_guard as SEG
import stamp_exempt_review as SER

DECL_REL = SEX.DECL_REL
TEMP_SUFFIX = ".sepr-tmp"

RETIRE_KEYS = ("entry", "queue", "identity", "declared", "until", "why")

PLAN_KEYS = (
    "round",
    "declaration",
    "path",
    "entries",
    "missing",
    "expired",
    "retire_count",
    "retire",
    "keep_count",
    "before_bytes",
    "source_digest",
    "source_bytes",
    "after_bytes",
    "predicted_bytes",
    "wrote",
    "read_back_ok",
    "verdict",
)

VERDICTS = ("NOTHING-TO-RETIRE", "PLAN")

WHY_MISSING = "MISSING"
WHY_EXPIRED = "EXPIRED"

USAGE = ("usage: stamp_exempt_prune.py [--root DIR] --round R<n> [--execute] "
         "[--json]")


class StampExemptPruneError(Exception):
    """Raised when an honest prune cannot be planned or performed."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def round_number(text):
    """R<n> -> n, or None when the token is not a round (imported law)."""
    return SEX.round_number(text)


def _array_region(text):
    """(open_index, close_index) of the exemptions array, or raise."""
    marker = '"exemptions"'
    pos = text.find(marker)
    if pos < 0:
        raise StampExemptPruneError("E_SPR_BAD_DECL",
                                    "declaration carries no exemptions key")
    open_at = text.find("[", pos)
    if open_at < 0:
        raise StampExemptPruneError("E_SPR_BAD_DECL",
                                    "exemptions carries no array")
    depth = 0
    in_string = False
    escape = False
    for at in range(open_at, len(text)):
        char = text[at]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return open_at, at
    raise StampExemptPruneError("E_SPR_BAD_DECL",
                               "exemptions array is never closed")


def entry_spans(text):
    """Every entry span (start, end) of the exemptions array, in file order."""
    open_at, close_at = _array_region(text)
    decoder = json.JSONDecoder()
    spans = []
    at = open_at + 1
    while at < close_at:
        while at < close_at and text[at] in " \t\r\n,":
            at += 1
        if at >= close_at:
            break
        try:
            _value, end = decoder.raw_decode(text, at)
        except ValueError as exc:
            raise StampExemptPruneError(
                "E_SPR_BAD_DECL", "entry at byte %d is not JSON (%s)"
                % (at, exc))
        spans.append((at, end))
        at = end
    return spans


def splice(text, spans, drop):
    """Remove the named spans, deleting only their own separators.

    Dropped indices are grouped into contiguous runs so one cut never lands
    inside another cut's region (a descending per-index walk would map an
    earlier index onto bytes a later cut already deleted - that was a real
    defect, caught by AC-SEPR3 before any evidence). Each run takes the
    separator that sits AFTER it; a run that reaches the end of the array takes
    the separator BEFORE it instead. Cuts are disjoint and applied from the
    last one backwards, so every surviving entry keeps its exact bytes.
    """
    drop = set(drop)
    total = len(spans)
    runs = []
    index = 0
    while index < total:
        if index in drop:
            first = index
            while index + 1 < total and (index + 1) in drop:
                index += 1
            runs.append((first, index))
        index += 1
    cuts = []
    for first, last in runs:
        if last + 1 < total:
            cuts.append((spans[first][0], spans[last + 1][0]))
        else:
            previous = first - 1
            while previous >= 0 and previous in drop:
                previous -= 1
            if previous >= 0:
                cuts.append((spans[previous][1], spans[last][1]))
            else:
                cuts.append((spans[first][0], spans[last][1]))
    removed = text
    for start, end in sorted(cuts, reverse=True):
        removed = removed[:start] + removed[end:]
    return removed


def surviving_texts(text, spans, drop):
    """The exact text of every surviving entry, in order."""
    return [text[start:end] for index, (start, end) in enumerate(spans)
            if index not in drop]


def _expired_entries(root, round_no, entries):
    """Entry indices the reader already calls EXPIRED (joined, not re-derived).

    Returns 1-based declaration positions, the same locator stamp_exempt_review
    prints for a MISSING entry, so the two halves of a plan are addressable the
    same way.
    """
    try:
        reader = SEX.audit(root, round_no)
    except SEX.QueueDoneStampExemptError as exc:
        raise StampExemptPruneError("E_SPR_BAD_DECL", str(exc))
    expired_pairs = set()
    for row in reader.get("rows") or []:
        if row.get("status") == "EXPIRED":
            expired_pairs.add((row.get("queue"), row.get("identity")))
    hits = []
    for index, entry in enumerate(entries):
        pair = (entry.get("queue"), entry.get("identity"))
        if pair in expired_pairs:
            hits.append(index + 1)
    return hits, reader


def retire_set(root, round_no):
    """The entries worth retiring, from the two shipped readings only."""
    try:
        review = SER.audit(root, round_no)
    except SER.StampExemptReviewError as exc:
        raise StampExemptPruneError("E_SPR_BAD_REVIEW", str(exc))
    entries = SEX.read_declaration(root)["entries"]
    expired, reader = _expired_entries(root, round_no, entries)
    retire = {}
    for item in review["missing"]:
        index = item["entry"]
        retire[index] = {
            "entry": index,
            "queue": item["queue"],
            "identity": item["identity"],
            "declared": item["declared"],
            "until": item.get("until"),
            "why": WHY_MISSING,
        }
    for index in expired:
        if index in retire:
            continue
        entry = entries[index - 1]
        retire[index] = {
            "entry": index,
            "queue": entry.get("queue"),
            "identity": entry.get("identity"),
            "declared": entry.get("declared"),
            "until": entry.get("until"),
            "why": WHY_EXPIRED,
        }
    return review, reader, entries, [retire[key] for key in sorted(retire)]


def plan(root, round_no, execute=False):
    """Plan (and optionally perform) one prune under root."""
    path = os.path.join(root, DECL_REL)
    shown = DECL_REL.replace(os.sep, "/")
    if not os.path.isfile(path):
        raise StampExemptPruneError(
            "E_SPR_UNPINNED",
            "no acceptance declaration at %s - there is nothing to retire"
            % shown)
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise StampExemptPruneError("E_SPR_BAD_DECL", "%s (%s)" % (path, exc))

    review, _reader, entries, retire = retire_set(root, round_no)
    spans = entry_spans(text)
    if len(spans) != len(entries):
        raise StampExemptPruneError(
            "E_SPR_COUNT",
            "declaration reads %d entries but the shipped reader validated %d"
            % (len(spans), len(entries)))

    drop = [item["entry"] - 1 for item in retire]
    pinned = SEG.pin(text)
    report = {
        "round": round_no,
        "declaration": review["declaration"],
        "path": shown,
        "entries": len(entries),
        "missing": review["missing_count"],
        "expired": review["expired"],
        "retire_count": len(drop),
        "retire": retire,
        "keep_count": len(entries) - len(drop),
        "before_bytes": len(text.encode("utf-8")),
        "source_digest": pinned["digest"],
        "source_bytes": pinned["bytes"],
        "after_bytes": None,
        "predicted_bytes": None,
        "wrote": False,
        "read_back_ok": None,
        "verdict": VERDICTS[1] if drop else VERDICTS[0],
    }
    if not drop:
        report["after_bytes"] = report["before_bytes"]
        return report

    try:
        post = splice(text, spans, set(drop))
    except StampExemptPruneError:
        raise
    except IndexError:
        raise StampExemptPruneError("E_SPR_BAD_DECL",
                                    "splice ran past the entry spans")

    before_texts = surviving_texts(text, spans, set(drop))
    after_spans = entry_spans(post)
    after_texts = [post[start:end] for start, end in after_spans]
    if before_texts != after_texts:
        raise StampExemptPruneError(
            "E_SPR_SPLICE",
            "%d surviving entries changed bytes or order"
            % len(before_texts))

    try:
        validated = SEPA.declaration_entries(post)
    except SEPA.StampExemptAppendError as exc:
        raise StampExemptPruneError("E_SPR_COUNT",
                                    "%s (%s)" % (exc.code, exc.detail))
    if len(validated) != report["keep_count"]:
        raise StampExemptPruneError(
            "E_SPR_COUNT",
            "post text carries %d entries, expected %d"
            % (len(validated), report["keep_count"]))

    payload = post.encode("utf-8")
    report["after_bytes"] = len(payload)
    report["predicted_bytes"] = len(payload)
    if not execute:
        return report

    temp = path + TEMP_SUFFIX
    try:
        guard = SEG.commit(
            path,
            {"digest": report["source_digest"], "bytes": report["source_bytes"]},
            payload, TEMP_SUFFIX,
            {"write": "E_SPR_WRITE", "readback": "E_SPR_READBACK",
             "residue": "E_SPR_RESIDUE",
             "unreadable": "E_SPR_BAD_DECL"})
    except SEG.StampGuardError as exc:
        raise StampExemptPruneError(exc.code, exc.detail)
    report["wrote"] = guard["wrote"]
    report["read_back_ok"] = guard["read_back_ok"]
    if os.path.exists(temp):
        raise StampExemptPruneError("E_SPR_RESIDUE",
                                    "temp file survived: %s" % temp)
    return report


def one_line(report):
    """The single line a window prints for itself (its own reconcile label)."""
    return ("STAMP EXEMPT PRUNE round=R%d declaration=%s entries=%d "
            "missing=%d expired=%d retire=%d keep=%d before=%dB after=%dB "
            "wrote=%s read_back=%s verdict=%s"
            % (report["round"], report["declaration"], report["entries"],
               report["missing"], report["expired"], report["retire_count"],
               report["keep_count"], report["before_bytes"],
               report["after_bytes"], "yes" if report["wrote"] else "no",
               ("yes" if report["read_back_ok"] else
                ("no" if report["read_back_ok"] is False else "n/a")),
               report["verdict"]))


def render(report):
    """The one line, then every entry the plan would drop."""
    out = [one_line(report)]
    for item in report["retire"]:
        until = ""
        if item["until"]:
            until = " until=%s" % item["until"]
        out.append("  RETIRE entry=%d %s:%s declared=%s%s why=%s"
                   % (item["entry"], item["queue"], item["identity"],
                      item["declared"], until, item["why"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one line per entry)."""
    ordered = {}
    for key in PLAN_KEYS:
        ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False)


def main(argv):
    root = "."
    round_no = None
    execute = False
    as_json = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--root" and index + 1 < len(argv):
            root = argv[index + 1]
            index += 2
        elif arg == "--round" and index + 1 < len(argv):
            round_no = round_number(argv[index + 1])
            index += 2
        elif arg == "--execute":
            execute = True
            index += 1
        elif arg == "--json":
            as_json = True
            index += 1
        else:
            sys.stderr.write(USAGE + "\n")
            return 2
    if round_no is None:
        sys.stderr.write(USAGE + "\n")
        return 2
    try:
        report = plan(root, round_no, execute=execute)
    except StampExemptPruneError as exc:
        sys.stderr.write("%s\n" % exc)
        return 2
    sys.stdout.write((to_json(report) if as_json else render(report)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))