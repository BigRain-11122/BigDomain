# stamp_exempt_review.py - the accepted-stamp declaration gets a drift reading
# Criteria AC-SER1..AC-SER6 were pre-registered in state/queue/tech.md as the
# R2280 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# stamp_exempt_review / AC-SER / E_SER / os-stamp-exempt-review /
# test_stamp_exempt_review / unmatched_review were git grep -F
# zero-occupancy rc=1 (every hit was prose: the queue row, the board, the
# state log and two closeout helpers).
#
# Why this exists: queue_done_stamp_exempt reads one pinned declaration of 380
# accepted rows and joins it with the live stamp gate. That join only asks one
# question - does this entry still match a debt row - and it answers it from
# inside a single reading. Nothing reports the two ways the pair can silently
# drift apart:
#
#   * a row that was exempted gets annotated after the fact, its text digest
#     moves, and the entry stops matching anything (the reader calls that
#     "unmatched" and moves on), or
#   * a closed row created after the declaration carries no entry at all and
#     is therefore never reviewed as an acceptance.
#
# The acceptance stays green while the pair rots. Today the only way to notice
# is to read a 380-entry file by hand against a 380-row gate reading.
#
# This module reads BOTH sides and lists drift in BOTH directions:
#   MISSING     a declared entry whose (queue, identity) matches no live debt
#              row - the declaration side is stale (or the row was fixed).
#   UNDECLARED  a live debt row carrying no declaration entry - the gate side
#              has grown past the acceptance.
# It never guesses which side is stale: both are listed with their own
# locators (the declaration entry index, the live file and line) and the
# reading refuses to claim one caused the other.
#
# The two readings are NOT re-implemented here:
#   * the gate comes from queue_done_stamp.audit_root, and
#   * the declaration and the row identity law come from
#     queue_done_stamp_exempt (read_declaration, identity_of, queue_of_path).
# The suite proves both imports by patching each one.
#
# AC-SER2 reconciliation: the matched/undeclared split must agree with the
# reader's own numbers before a verdict is issued - matched declared entries
# equal exempt_today + exempt_expired from queue_done_stamp_exempt.audit, and
# the MISSING count equals that report's unmatched_count. A disagreement means
# the two readings disagree about the world, which fails closed (E_SER_COUNT)
# instead of printing a drift list nobody can trust.
#
# AC-SER5 fail-closed: a declaration that is absent reads E_SER_UNPINNED, not
# "everything is drift" - with no acceptance record there is nothing to
# review. A malformed declaration, an unreadable gate, an ambiguous pair (one
# entry matching two rows) and a count disagreement each carry their own code.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import json
import os
import sys

import queue_done_stamp as QDS
import queue_done_stamp_exempt as SEX

MISSING_KEYS = ("entry", "queue", "identity", "declared", "until")

UNDECLARED_KEYS = ("file", "line", "queue", "identity", "seed_round")

REPORT_KEYS = (
    "round",
    "declaration",
    "path",
    "violation_count",
    "entries",
    "matched",
    "exempt",
    "expired",
    "missing_count",
    "missing",
    "undeclared_count",
    "undeclared",
    "verdict",
)

VERDICTS = ("NO-DRIFT", "DRIFT")


class StampExemptReviewError(Exception):
    """Raised when an honest drift reading cannot be produced."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def round_number(text):
    """R<n> -> n, or None when the token is not a round (imported law)."""
    return SEX.round_number(text)


def live_pairs(root):
    """The gate reading as {(queue, identity): [row, ...]}, plus the rows."""
    gate = QDS.audit_root(root)
    missing = gate.get("missing") or []
    if missing:
        raise StampExemptReviewError("E_SER_BAD_GATE",
                                     "missing queue file(s): %s"
                                     % ",".join(missing))
    rows = []
    for bad in gate.get("violations") or []:
        excerpt = bad.get("excerpt", "")
        rows.append({
            "file": bad.get("file"),
            "line": bad.get("line"),
            "queue": SEX.queue_of_path(bad.get("file")),
            "identity": SEX.identity_of(excerpt),
            "seed_round": bad.get("seed_round"),
        })
    by_pair = {}
    for row in rows:
        by_pair.setdefault((row["queue"], row["identity"]), []).append(row)
    return rows, by_pair


def declaration_of(root):
    """The accepted-stamp declaration; absent is a refusal, not drift."""
    try:
        declaration = SEX.read_declaration(root)
    except SEX.QueueDoneStampExemptError as exc:
        raise StampExemptReviewError("E_SER_BAD_DECL", str(exc))
    except Exception as exc:  # noqa: BLE001 - a broken reader is not clean
        raise StampExemptReviewError("E_SER_UNREADABLE",
                                     "%s (%s)" % (type(exc).__name__, exc))
    if not isinstance(declaration, dict):
        raise StampExemptReviewError("E_SER_BAD_DECL",
                                     "reader returned %r"
                                     % (type(declaration).__name__,))
    if declaration.get("status") != "PINNED":
        raise StampExemptReviewError(
            "E_SER_UNPINNED",
            "no acceptance declaration at %s - there is nothing to review"
            % (declaration.get("path") or SEX.DECL_REL))
    entries = declaration.get("entries")
    if not isinstance(entries, list):
        raise StampExemptReviewError("E_SER_BAD_DECL",
                                     "declaration carries no entries list")
    return declaration


def join(rows, by_pair, entries):
    """Split the pair both ways; never guesses which side is stale."""
    matched = []
    missing = []
    for index, entry in enumerate(entries):
        pair = (entry.get("queue"), entry.get("identity"))
        hits = by_pair.get(pair, [])
        if not hits:
            missing.append({
                "entry": index + 1,
                "queue": entry.get("queue"),
                "identity": entry.get("identity"),
                "declared": entry.get("declared"),
                "until": entry.get("until"),
            })
            continue
        if len(hits) > 1:
            names = ",".join("%s:%d" % (row["file"], row["line"])
                             for row in hits)
            raise StampExemptReviewError(
                "E_SER_AMBIGUOUS",
                "%s:%s matches %d live rows (%s)"
                % (entry.get("queue"), entry.get("identity"), len(hits),
                   names))
        matched.append(index)
    matched_pairs = set()
    for index in matched:
        matched_pairs.add((entries[index].get("queue"),
                           entries[index].get("identity")))
    undeclared = []
    for row in rows:
        if (row["queue"], row["identity"]) not in matched_pairs:
            undeclared.append({
                "file": row["file"],
                "line": row["line"],
                "queue": row["queue"],
                "identity": row["identity"],
                "seed_round": row["seed_round"],
            })
    return len(matched), missing, undeclared


def reconcile(matched, missing, undeclared, reader, violation_count):
    """AC-SER2: the split must agree with the reader own numbers, or refuse."""
    expected_matched = reader["exempt_today"] + reader["exempt_expired"]
    if matched != expected_matched:
        raise StampExemptReviewError(
            "E_SER_COUNT",
            "matched %d disagrees with exempt+expired %d"
            % (matched, expected_matched))
    if len(missing) != reader["unmatched_count"]:
        raise StampExemptReviewError(
            "E_SER_COUNT",
            "missing %d disagrees with the reader unmatched_count %d"
            % (len(missing), reader["unmatched_count"]))
    if violation_count != matched + len(undeclared):
        raise StampExemptReviewError(
            "E_SER_COUNT",
            "violations %d != matched %d + undeclared %d"
            % (violation_count, matched, len(undeclared)))
    return True


def audit(root, round_no):
    """Read both sides and report drift in both directions. Writes nothing."""
    if round_number("R%d" % round_no) is None:
        raise StampExemptReviewError("E_SER_BAD_ARGS", "bad round")
    declaration = declaration_of(root)
    rows, by_pair = live_pairs(root)
    entries = declaration["entries"]
    matched, missing, undeclared = join(rows, by_pair, entries)
    try:
        reader = SEX.audit(root, round_no)
    except SEX.QueueDoneStampExemptError as exc:
        raise StampExemptReviewError("E_SER_BAD_DECL", str(exc))
    violation_count = len(rows)
    reconcile(matched, missing, undeclared, reader, violation_count)
    drift = bool(missing or undeclared)
    return {
        "round": round_no,
        "declaration": declaration["status"],
        "path": declaration["path"],
        "violation_count": violation_count,
        "entries": len(entries),
        "matched": matched,
        "exempt": reader["exempt_today"],
        "expired": reader["exempt_expired"],
        "missing_count": len(missing),
        "missing": missing,
        "undeclared_count": len(undeclared),
        "undeclared": undeclared,
        "verdict": VERDICTS[1] if drift else VERDICTS[0],
    }


def one_line(report):
    """The single line a window prints for itself."""
    return ("STAMP EXEMPT REVIEW round=R%d declaration=%s entries=%d "
            "violations=%d matched=%d exempt=%d expired=%d missing=%d "
            "undeclared=%d verdict=%s"
            % (report["round"], report["declaration"], report["entries"],
               report["violation_count"], report["matched"],
               report["exempt"], report["expired"], report["missing_count"],
               report["undeclared_count"], report["verdict"]))


def render(report):
    """The one line, then the declaration side, then the gate side."""
    out = [one_line(report)]
    for item in report["missing"]:
        until = ""
        if item["until"]:
            until = " until=%s" % item["until"]
        out.append("  MISSING entry=%d %s:%s declared=%s%s"
                   % (item["entry"], item["queue"], item["identity"],
                      item["declared"], until))
    for row in report["undeclared"]:
        out.append("  UNDECLARED %s:%d %s:%s seed=%s"
                   % (row["file"], row["line"], row["queue"],
                      row["identity"], row["seed_round"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned_missing = []
    for item in report["missing"]:
        out = {}
        for key in MISSING_KEYS:
            out[key] = item[key]
        pinned_missing.append(out)
    pinned_undeclared = []
    for row in report["undeclared"]:
        out = {}
        for key in UNDECLARED_KEYS:
            out[key] = row[key]
        pinned_undeclared.append(out)
    ordered["missing"] = pinned_missing
    ordered["undeclared"] = pinned_undeclared
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: stamp_exempt_review.py --check --round R<n> "
         "[--root PATH] [--json]\n"
         "  Both sides are read and drift is listed in both directions:\n"
         "  a declared entry matching no live debt row reads MISSING, and a\n"
         "  live debt row with no declaration entry reads UNDECLARED.\n"
         "  exit 0 = NO-DRIFT (every live row declared, every entry matched)\n"
         "  exit 2 = DRIFT (either side is listed)\n"
         "  exit 3 = missing/malformed declaration or unreadable gate\n"
         "  exit 5 = bad flags\n")


def main(argv):
    check = False
    as_json = False
    round_text = None
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--check":
            check = True
        elif arg == "--json":
            as_json = True
        elif arg == "--round":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SER_BAD_ARGS: --round needs a value\n")
                return 5
            round_text = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SER_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SER_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_SER_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_SER_BAD_ARGS: --round is mandatory\n")
        sys.stdout.write(USAGE)
        return 5
    round_no = round_number(round_text)
    if round_no is None:
        sys.stdout.write("E_SER_BAD_ARGS: --round is not a round: %s\n"
                         % round_text)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit(root, round_no)
    except StampExemptReviewError as exc:
        sys.stdout.write("REFUSE %s: %s\n" % (exc.code, exc.detail))
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "DRIFT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))