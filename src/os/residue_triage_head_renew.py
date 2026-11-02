"""residue_triage_head_renew - renew the triage head only over what it read (R2351).

`state/residue_triage.json` carries a HEAD claim: one `declared_by` and one
`reason` sentence that speak for the WHOLE entry set. Entries are appended
later, through the shipped writer, carrying their OWN `declared_by` and
`until`, and the head has no writer at all - it can only be renewed by hand,
which is exactly how it aged. Measured live at R2350: the head still reads
`declared_by R2331 ... until R2350` while eleven appended entries carry their
own rounds (three of them until R2360), so a hand renewal today would be a
prose edit claiming a re-read nobody performed.

This is that missing writer, and it may only renew what it MEASURED:

  * the entry set, the status vocabulary and the live residue are all asked of
    `residue_triage` at call time (its loader, its stamp reader, its live
    residue), and the head claim is asked of `residue_triage_decl_reason`, so
    patching any of them moves the renewal - nothing is re-derived here;
  * the dry run is the DEFAULT: the plan names the old head, the new head, the
    entry count, the status histogram and the predicted byte count, and it
    writes nothing at all (no temp file, no byte) without --execute;
  * a renewal is REFUSED before any byte when a declared entry disagrees with
    the live reading, when a live residue round is still undeclared, or when
    the new head would predate an entry's own `declared_by`; every refusal
    names the offending rounds rather than a bare count;
  * an executed renewal is ONE atomic text splice that rewrites only the head
    `declared_by` and `reason` values, leaves every entry byte-identical,
    proves the predicted post size against the write, and leaves no temp
    residue behind.

A renewal moves the head ROUND and nothing else. The head's window is not a
stored field - it is the window most entries carry (the mode that
residue_triage_decl_reason already measures) - so a renewal leaves every
entry's own claim intact and cannot shorten one. When the entry set carries
more than one window, the differing entries survive as UNTIL breaks; the plan
names how many will survive and which one is first, rather than implying a
renewal makes a heterogeneous set read clean.

Pure ASCII source, stdlib only, zero network, no clock read of its own: the
round is an argument, never `time`. No delete path (the atomic replace renames
the temp file, it never unlinks one).
Criteria AC-RTRH1..AC-RTRH6 were pinned inside the R2350 seed row of
state/queue/tech.md BEFORE this code existed.
"""

import json
import os
import re
import sys

import residue_triage as RT
import residue_triage_decl_reason as DR

DECLARATION_PATH = RT.DECLARATION_PATH

TMP_SUFFIX = ".renew-part"

ENTRIES_MARKER = re.compile(r'"entries"\s*:')

HEAD_DECLARED_BY = re.compile(r'("declared_by"\s*:\s*")([^"]*)(")')

HEAD_REASON = re.compile(r'("reason"\s*:\s*")((?:[^"\\]|\\.)*)(")', re.S)

REPORT_KEYS = (
    "declaration",
    "old_declared_by",
    "old_until",
    "new_declared_by",
    "new_until",
    "entries",
    "statuses",
    "unmatched",
    "old_bytes",
    "predicted_bytes",
    "remaining_breaks",
    "remaining_first",
    "executed",
    "verdict",
)

STATUS_KEYS = ("status", "count")

VERDICTS = ("PLANNED", "RENEWED", "NOOP")

EXIT_OK = 0
EXIT_INTEGRITY = 1
EXIT_REFUSED = 2
EXIT_UNREADABLE = 3
EXIT_BAD_ARGS = 5


class RenewError(Exception):
    """A refusal carrying its own code and its own exit code."""

    def __init__(self, code, detail="", exit_code=EXIT_REFUSED):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail
        self.exit_code = exit_code


def parse_round(value):
    """The caller's round, through residue_triage own parser (AC-RTRH1)."""
    try:
        return RT.parse_round(value, "caller")
    except RT.ResidueTriageError as exc:
        raise RenewError("E_RTRH_BAD_ARGS", exc.detail, EXIT_BAD_ARGS)


def declaration_of(root):
    """The declaration through the shipped reader (AC-RTRH1)."""
    try:
        declaration = DR.load(root)
    except DR.DeclReasonError as exc:
        raise RenewError(exc.code, exc.detail, EXIT_UNREADABLE)
    if declaration is None:
        raise RenewError(
            "E_RTRH_UNPINNED",
            "no declaration at %s, so there is nothing to renew"
            % DECLARATION_PATH.replace(os.sep, "/"),
            EXIT_UNREADABLE)
    return declaration


def head_of(root):
    """The head claim, through residue_triage_decl_reason (AC-RTRH1)."""
    try:
        return DR.read(root)
    except DR.DeclReasonError as exc:
        raise RenewError(exc.code, exc.detail, EXIT_UNREADABLE)


def live_statuses(root):
    """Round -> live status, through residue_triage own live residue."""
    try:
        rows = RT.live_residue(root)
    except RT.ResidueTriageError as exc:
        raise RenewError(exc.code, exc.detail, EXIT_UNREADABLE)
    out = {}
    for row in rows:
        out[row["round"]] = row["status"]
    return out


def histogram(entries):
    """Declared status -> count, in the live vocabulary order (AC-RTRH2)."""
    counts = {}
    for entry in entries:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    order = list(RT.SR.STATUSES)
    for status in sorted(counts):
        if status not in order:
            order.append(status)
    rows = []
    for status in order:
        if status in counts:
            rows.append({"status": status, "count": counts[status]})
    return rows


def remaining_breaks(entries, current, window):
    """What the renewal will NOT fix, measured by the shipped comparison.

    `residue_triage_decl_reason` judges an entry whose window differs from the
    head's mode window as a break, and a renewal may not rewrite an entry, so
    a heterogeneous entry set stays HEAD-STALE on the UNTIL axis. That is
    stated instead of hidden: the plan names every break that will survive.
    """
    declaration = {"declared_by": current, "entries": entries}
    return DR.compare(declaration, window)


def reason_text(current, entries, window):
    """One honest sentence: every entry was compared to the live reading."""
    return ("renewed at R%d by residue_triage_head_renew: all %d entries were "
            "re-read against the live stamp_residue table at R%d, every "
            "declared status matched its live status, and the window now runs "
            "to R%d" % (current, len(entries), current, window))


def splice(raw, new_head, new_reason):
    """Rewrite ONLY the head values; the entries region is returned untouched."""
    match = ENTRIES_MARKER.search(raw)
    if match is None:
        raise RenewError(
            "E_RTRH_BAD_SHAPE",
            "the declaration carries no top-level entries key", EXIT_UNREADABLE)
    head_text = raw[:match.start()]
    tail = raw[match.start():]
    escaped = json.dumps(new_reason, ensure_ascii=True)[1:-1]
    head_text, first = HEAD_DECLARED_BY.subn(
        lambda hit: hit.group(1) + "R%d" % new_head + hit.group(3),
        head_text, count=1)
    head_text, second = HEAD_REASON.subn(
        lambda hit: hit.group(1) + escaped + hit.group(3),
        head_text, count=1)
    if first != 1 or second != 1:
        raise RenewError(
            "E_RTRH_BAD_SHAPE",
            "the head carries no declared_by/reason pair to renew",
            EXIT_UNREADABLE)
    return head_text + tail, tail


def write_atomic(path, data, predicted, tail, old_tail):
    """One write, proved against the prediction before it is trusted."""
    if len(data) != predicted:
        raise RenewError(
            "E_RTRH_INTEGRITY",
            "predicted %d bytes but rendered %d" % (predicted, len(data)),
            EXIT_INTEGRITY)
    if tail != old_tail:
        raise RenewError(
            "E_RTRH_INTEGRITY", "the entries region moved during the splice",
            EXIT_INTEGRITY)
    tmp = path + TMP_SUFFIX
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    with open(path, "rb") as handle:
        back = handle.read()
    if back != data:
        raise RenewError(
            "E_RTRH_INTEGRITY",
            "the written file does not match the rendered bytes",
            EXIT_INTEGRITY)
    if os.path.exists(tmp):
        raise RenewError(
            "E_RTRH_INTEGRITY", "the temp file survived the replace",
            EXIT_INTEGRITY)


def plan(root, round_text, execute=False):
    """The whole renewal: refusals first, then a plan, then maybe the write."""
    current = parse_round(round_text)
    declaration = declaration_of(root)
    head = head_of(root)
    path = os.path.join(root, DECLARATION_PATH)
    try:
        with open(path, "rb") as handle:
            raw_bytes = handle.read()
    except (IOError, OSError) as exc:
        raise RenewError("E_RTRH_UNREADABLE", str(exc), EXIT_UNREADABLE)
    raw = raw_bytes.decode("utf-8", "replace")

    entries = declaration["entries"]
    head_until = None if head["head_until"] == "-" else \
        int(head["head_until"].lstrip("R"))
    old_bytes = len(raw_bytes)

    if head["verdict"] == "HEAD-CURRENT":
        return {
            "declaration": "PINNED",
            "old_declared_by": head["declared_by"],
            "old_until": head["head_until"],
            "new_declared_by": head["declared_by"],
            "new_until": head["head_until"],
            "entries": len(entries),
            "statuses": histogram(entries),
            "unmatched": 0,
            "old_bytes": old_bytes,
            "predicted_bytes": old_bytes,
            "remaining_breaks": 0,
            "remaining_first": "-",
            "executed": False,
            "verdict": "NOOP",
        }

    live = live_statuses(root)
    declared_rounds = set(entry["round"] for entry in entries)

    disagreements = []
    for entry in entries:
        live_status = live.get(entry["round"])
        if live_status is not None and entry["status"] != live_status:
            disagreements.append("R%d declared %s but live reads %s"
                                 % (entry["round"], entry["status"],
                                    live_status))
    if disagreements:
        raise RenewError(
            "E_RTRH_DISAGREES",
            "the live reading moved under the declaration: %s"
            % "; ".join(disagreements), EXIT_REFUSED)

    undeclared = sorted(number for number in live
                        if number not in declared_rounds)
    if undeclared:
        raise RenewError(
            "E_RTRH_UNDECLARED",
            "live residue rounds carry no declaration: %s"
            % ", ".join("R%d" % number for number in undeclared),
            EXIT_REFUSED)

    late = [entry for entry in entries if entry["declared_by"] > current]
    if late:
        raise RenewError(
            "E_RTRH_HEAD_PREDATES",
            "the renewal round R%d would predate %s"
            % (current,
               ", ".join("R%d (declared_by R%d)"
                         % (entry["round"], entry["declared_by"])
                         for entry in late)), EXIT_REFUSED)

    window = current if head_until is None else head_until
    survivors = remaining_breaks(entries, current, window)
    first_survivor = survivors[0]["round"] if survivors else "-"
    reason = reason_text(current, entries, window)
    renewed, tail = splice(raw, current, reason)
    data = renewed.encode("utf-8")
    predicted = len(data)
    unmatched = len([entry for entry in entries
                     if entry["round"] not in live])

    if execute:
        try:
            with open(path, "rb") as handle:
                fresh = handle.read()
        except (IOError, OSError) as exc:
            raise RenewError("E_RTRH_UNREADABLE", str(exc), EXIT_UNREADABLE)
        if fresh != raw_bytes:
            raise RenewError(
                "E_RTRH_STALE",
                "the declaration moved between the plan and the write",
                EXIT_REFUSED)
        # The shared NOOP comparison is asked BEFORE the write (AC-DWNP1): a
        # renewal whose rendered bytes equal the file leaves it untouched
        # instead of rewriting the same document under a RENEWED word.
        import declaration_writer_noop_parity as DWNP
        if DWNP.is_noop(path, data):
            return {
                "declaration": "PINNED",
                "old_declared_by": head["declared_by"],
                "old_until": head["head_until"],
                "new_declared_by": head["declared_by"],
                "new_until": head["head_until"],
                "entries": len(entries),
                "statuses": histogram(entries),
                "unmatched": unmatched,
                "old_bytes": old_bytes,
                "predicted_bytes": old_bytes,
                "remaining_breaks": len(survivors),
                "remaining_first": first_survivor,
                "executed": False,
                "verdict": "NOOP",
            }
        write_atomic(path, data, predicted, tail, tail)

    return {
        "declaration": "PINNED",
        "old_declared_by": head["declared_by"],
        "old_until": head["head_until"],
        "new_declared_by": "R%d" % current,
        "new_until": "R%d" % window,
        "entries": len(entries),
        "statuses": histogram(entries),
        "unmatched": unmatched,
        "old_bytes": old_bytes,
        "predicted_bytes": predicted,
        "remaining_breaks": len(survivors),
        "remaining_first": first_survivor,
        "executed": bool(execute),
        "verdict": "RENEWED" if execute else "PLANNED",
    }


def one_line(report):
    """The single line an operator reads."""
    counts = " ".join("%s=%d" % (row["status"], row["count"])
                      for row in report["statuses"])
    return ("RESIDUE TRIAGE HEAD RENEW old=%s/%s new=%s/%s entries=%d [%s] "
            "unmatched=%d bytes=%d->%d remaining=%d/%s executed=%s verdict=%s"
            % (report["old_declared_by"], report["old_until"],
               report["new_declared_by"], report["new_until"],
               report["entries"], counts, report["unmatched"],
               report["old_bytes"], report["predicted_bytes"],
               report["remaining_breaks"], report["remaining_first"],
               "yes" if report["executed"] else "no", report["verdict"]))


def render(report):
    """Full text: the one line, then the histogram entry by entry."""
    out = [one_line(report)]
    for row in report["statuses"]:
        out.append("  STATUS %s count=%d" % (row["status"], row["count"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in the pinned key order only (no extra keys leak)."""
    pinned = []
    for row in report["statuses"]:
        narrow = {}
        for key in STATUS_KEYS:
            narrow[key] = row[key]
        pinned.append(narrow)
    ordered = {}
    for key in REPORT_KEYS:
        if key == "statuses":
            ordered["statuses"] = pinned
        else:
            ordered[key] = report[key]
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: residue_triage_head_renew.py --round R<n> [--execute] "
         "[--root PATH] [--json]\n"
         "  the dry run is the default: nothing is written without --execute\n"
         "  exit 0 = PLANNED, RENEWED, or NOOP (the head already speaks for "
         "every entry)\n"
         "  exit 1 = the post-write integrity check failed\n"
         "  exit 2 = refused over live state (entries disagree, live residue "
         "undeclared, or the round would predate an entry)\n"
         "  exit 3 = the declaration, or the live residue, is missing or "
         "unreadable\n"
         "  exit 5 = bad flags\n")


def main(argv):
    as_json = False
    execute = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            as_json = True
        elif arg == "--execute":
            execute = True
        elif arg in ("--round", "--root"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_RTRH_BAD_ARGS: %s needs a value\n" % arg)
                sys.stdout.write(USAGE)
                return EXIT_BAD_ARGS
            if arg == "--round":
                round_text = argv[index]
            else:
                root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return EXIT_OK
        else:
            sys.stdout.write("E_RTRH_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return EXIT_BAD_ARGS
        index += 1
    if round_text is None:
        sys.stdout.write("E_RTRH_BAD_ARGS: --round is required\n")
        sys.stdout.write(USAGE)
        return EXIT_BAD_ARGS
    try:
        report = plan(root, round_text, execute)
    except RenewError as exc:
        if as_json:
            sys.stdout.write(json.dumps(
                {"error": exc.code, "detail": exc.detail},
                ensure_ascii=True) + "\n")
        else:
            sys.stdout.write("%s: %s\n" % (exc.code, exc.detail))
        return exc.exit_code
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))