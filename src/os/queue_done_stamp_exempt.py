# queue_done_stamp_exempt.py - record an ACCEPTED window-stamp exemption
# Criteria AC-SEX1..AC-SEX6 were pre-registered in state/queue/tech.md as the
# R2278 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# queue_done_stamp_exempt / AC-SEX / E_SEX / os-queue-done-stamp-exempt /
# test_queue_done_stamp_exempt / stamp_exempt were git grep -F
# zero-occupancy rc=1 (disclosed: that check was run by the seeding window).
#
# Why this exists: queue_done_stamp gates every CLOSED queue row on carrying a
# resolvable window stamp. 380 live closed rows fail that gate (289 with no
# bracket at all, 91 with a date but no window) and every one of them was
# written before the law landed, so the reading can never go green. The only
# ways out are rewriting the history the law must not rewrite, or silently
# widening the gate into a blind spot. This module adds the third way: an
# ACCEPTED exemption, declared in one pinned file, keyed by a stable row
# identity instead of a line number, carrying a dated reason, and reported
# back as exempt_today against still_debt so acceptance is a named fact.
#
# The gate is NOT re-implemented: violations come from
# queue_done_stamp.audit_root, so the stamp forms, the seed-round law and the
# row law all stay in the one place that owns them (AC-SEX5). The declaration
# is the only new input.
#
# Declaration file (pinned): state/queue/stamp_exempt.json
#   {"exemptions": [{"queue": "tech",
#                    "identity": "done#1a2b3c4d",
#                    "declared": "R2280",
#                    "reason": "why this row is accepted as it stands",
#                    "until": "R2300"}]}
# Required entry keys: queue, identity, declared, reason. Optional: until
# (absent or null means "no expiry"). Any other key is refused, because a
# declaration that silently carries ignored data is not reviewable.
#
# Row identity law (stable under line shifts, unique by construction):
#   <lead>#<sha8 of the normalised row text>, where <lead> is the first ASCII
#   token of at least three characters (letters, digits, dot, underscore,
#   dash) or "row" when the row carries none. The digest makes the identity
#   independent of the line number and unique per DISTINCT row text, so a row
#   that moves inside the file, or a file that grows above it, keeps its
#   identity. An identity that matches NO live debt row is reported as
#   unmatched - inert, never green-washing, because the row it meant to
#   exempt stays debt. Two textually identical rows therefore share an
#   identity and an entry matching both is refused (E_SEX_AMBIGUOUS), because
#   one entry must never exempt two rows.
#
# Expiry (AC-SEX4): an entry whose until round is earlier than the round
# being checked is EXPIRED and the row reads as debt again, with the until
# round named. The round is MANDATORY on the command line - a default round
# would silently decide on its own whether debt is still waived.
#
# A missing declaration reads UNPINNED with the full debt (AC-SEX1), never a
# fabricated pass. A malformed declaration, an unknown key, an empty reason,
# a non-round date or a duplicate pair is refused with its own code.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import hashlib
import io
import json
import os
import re
import sys

import queue_done_stamp as QDS

DECL_REL = os.path.join("state", "queue", "stamp_exempt.json")

TOP_KEYS = ("exemptions", "note")

ENTRY_KEYS = ("queue", "identity", "declared", "reason", "until")
REQUIRED_KEYS = ("queue", "identity", "declared", "reason")

ROW_KEYS = ("file", "line", "queue", "identity", "status", "until",
            "seed_round")

UNMATCHED_KEYS = ("queue", "identity", "declared")

REPORT_KEYS = (
    "round",
    "declaration",
    "path",
    "entries",
    "violation_count",
    "exempt_today",
    "exempt_expired",
    "still_debt",
    "unmatched_count",
    "unmatched",
    "rows",
    "verdict",
)

VERDICTS = ("EXEMPT-CLEAN", "EXEMPT-DEBT")

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]{2,}")
ROUND_RE = re.compile(r"^R([0-9]+)$")


class QueueDoneStampExemptError(Exception):
    """Raised when an honest reading cannot be produced."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity_of(text):
    """The stable identity of one row, derived from the row text alone."""
    norm = " ".join(text.split())
    digest = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:8]
    hit = TOKEN_RE.search(norm)
    base = hit.group(0) if hit else "row"
    return "%s#%s" % (base, digest)


def round_number(text):
    """R<n> -> n, or None when the token is not a round."""
    if not isinstance(text, str):
        return None
    hit = ROUND_RE.match(text.strip())
    if not hit:
        return None
    return int(hit.group(1))


def allowed_queues():
    """The queue names the row law knows, taken from queue_floor."""
    return tuple(name for name, _rel in QDS.QF.QUEUE_PATHS)


def queue_of_path(rel):
    """state/queue/tech.md -> tech (the queue name the gate reports)."""
    leaf = rel.replace("\\", "/").split("/")[-1]
    if leaf.endswith(".md"):
        leaf = leaf[:-3]
    return leaf


def read_declaration(root):
    """Read and validate the declaration; a missing file reads UNPINNED."""
    shown = DECL_REL.replace(os.sep, "/")
    path = os.path.join(root, DECL_REL)
    if not os.path.isfile(path):
        return {"status": "UNPINNED", "path": shown, "entries": [],
                "note": None}
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s (%s)" % (shown, exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s is not JSON (%s)" % (shown, exc))
    if not isinstance(data, dict):
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s is not an object" % shown)
    for key in data:
        if key not in TOP_KEYS:
            raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                            "%s carries unknown key %r"
                                            % (shown, key))
    if "exemptions" not in data:
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s carries no exemptions list"
                                        % shown)
    if not isinstance(data["exemptions"], list):
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s exemptions is not a list" % shown)
    note = data.get("note")
    if note is not None and not isinstance(note, str):
        raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                        "%s note is not a string" % shown)
    entries = []
    seen = set()
    for index, raw in enumerate(data["exemptions"]):
        where = "%s entry %d" % (shown, index + 1)
        if not isinstance(raw, dict):
            raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                            "%s is not an object" % where)
        for key in raw:
            if key not in ENTRY_KEYS:
                raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                                "%s carries unknown key %r"
                                                % (where, key))
        for key in REQUIRED_KEYS:
            if key not in raw:
                raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                                "%s is missing %r"
                                                % (where, key))
        queue = raw["queue"]
        identity = raw["identity"]
        declared = raw["declared"]
        reason = raw["reason"]
        until = raw.get("until")
        if not isinstance(queue, str) or queue not in allowed_queues():
            raise QueueDoneStampExemptError("E_SEX_BAD_DECL",
                                            "%s names unknown queue %r"
                                            % (where, queue))
        if not isinstance(identity, str) or not identity.strip():
            raise QueueDoneStampExemptError("E_SEX_BAD_IDENTITY",
                                            "%s identity is empty" % where)
        if identity != identity.strip():
            raise QueueDoneStampExemptError("E_SEX_BAD_IDENTITY",
                                            "%s identity carries padding"
                                            % where)
        if round_number(declared) is None:
            raise QueueDoneStampExemptError("E_SEX_BAD_DATE",
                                            "%s declared is not a round: %r"
                                            % (where, declared))
        if until is not None:
            if round_number(until) is None:
                raise QueueDoneStampExemptError("E_SEX_BAD_DATE",
                                                "%s until is not a round: %r"
                                                % (where, until))
            if round_number(until) < round_number(declared):
                raise QueueDoneStampExemptError("E_SEX_BAD_DATE",
                                                "%s until predates declared"
                                                % where)
        if not isinstance(reason, str) or not reason.strip():
            raise QueueDoneStampExemptError("E_SEX_BAD_REASON",
                                            "%s carries no reason" % where)
        pair = (queue, identity)
        if pair in seen:
            raise QueueDoneStampExemptError("E_SEX_DUP",
                                            "%s repeats %s:%s"
                                            % (where, queue, identity))
        seen.add(pair)
        entries.append({"queue": queue, "identity": identity,
                        "declared": declared, "until": until,
                        "reason": reason})
    return {"status": "PINNED", "path": shown, "entries": entries,
            "note": note}


def live_rows(gate):
    """The gate violations as rows, each with its derived identity."""
    rows = []
    for bad in gate["violations"]:
        rows.append({
            "file": bad["file"],
            "line": bad["line"],
            "queue": queue_of_path(bad["file"]),
            "identity": identity_of(bad.get("excerpt", "")),
            "status": "DEBT",
            "until": None,
            "seed_round": bad.get("seed_round"),
        })
    return rows


def audit(root, round_no):
    """Join the declaration with the gate reading; never writes."""
    if round_number("R%d" % round_no) is None:
        raise QueueDoneStampExemptError("E_SEX_BAD_ARGS", "bad round")
    declaration = read_declaration(root)
    gate = QDS.audit_root(root)
    missing = gate.get("missing") or []
    if missing:
        raise QueueDoneStampExemptError("E_SEX_BAD_QUEUE", ",".join(missing))
    rows = live_rows(gate)
    unmatched = []
    exempt_today = 0
    exempt_expired = 0
    if declaration["status"] == "PINNED":
        by_pair = {}
        for index, row in enumerate(rows):
            by_pair.setdefault((row["queue"], row["identity"]),
                               []).append(index)
        entry_hits = {}
        for entry in declaration["entries"]:
            pair = (entry["queue"], entry["identity"])
            hits = by_pair.get(pair, [])
            if not hits:
                unmatched.append({"queue": entry["queue"],
                                  "identity": entry["identity"],
                                  "declared": entry["declared"]})
                continue
            if len(hits) > 1:
                names = ",".join("%s:%d" % (rows[i]["file"], rows[i]["line"])
                                 for i in hits)
                raise QueueDoneStampExemptError(
                    "E_SEX_AMBIGUOUS",
                    "%s:%s matches %d rows (%s)"
                    % (entry["queue"], entry["identity"], len(hits), names))
            index = hits[0]
            if index in entry_hits:
                raise QueueDoneStampExemptError(
                    "E_SEX_DUP",
                    "two entries match %s:%d" % (rows[index]["file"],
                                                 rows[index]["line"]))
            entry_hits[index] = entry
        for index in sorted(entry_hits):
            entry = entry_hits[index]
            rows[index]["until"] = entry["until"]
            until = round_number(entry["until"])
            if until is not None and round_no > until:
                rows[index]["status"] = "EXPIRED"
                exempt_expired += 1
            else:
                rows[index]["status"] = "EXEMPT"
                exempt_today += 1
    else:
        for row in rows:
            row["status"] = "DEBT"
    # An expired exemption stays debt: the row must be seen again, not hidden.
    still_debt = len(rows) - exempt_today
    verdict = "EXEMPT-CLEAN" if still_debt == 0 else "EXEMPT-DEBT"
    return {
        "round": round_no,
        "declaration": declaration["status"],
        "path": declaration["path"],
        "entries": len(declaration["entries"]),
        "violation_count": len(rows),
        "exempt_today": exempt_today,
        "exempt_expired": exempt_expired,
        "still_debt": still_debt,
        "unmatched_count": len(unmatched),
        "unmatched": unmatched,
        "rows": rows,
        "verdict": verdict,
    }


def one_line(report):
    """The single line an operator reads."""
    return ("QUEUE DONE STAMP EXEMPT round=R%d declaration=%s entries=%d "
            "violations=%d exempt=%d expired=%d still_debt=%d unmatched=%d "
            "verdict=%s"
            % (report["round"], report["declaration"], report["entries"],
               report["violation_count"], report["exempt_today"],
               report["exempt_expired"], report["still_debt"],
               report["unmatched_count"], report["verdict"]))


def render(report):
    """The one line, then every row, then every unmatched entry."""
    out = [one_line(report)]
    for row in report["rows"]:
        extra = ""
        if row["until"]:
            extra = " until=%s" % row["until"]
        out.append("  %-8s %s:%d %s%s"
                   % (row["status"], row["file"], row["line"],
                      row["identity"], extra))
    for item in report["unmatched"]:
        out.append("  UNMATCHED %s:%s declared=%s"
                   % (item["queue"], item["identity"], item["declared"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    pinned_rows = []
    for row in report["rows"]:
        item = {}
        for key in ROW_KEYS:
            item[key] = row[key]
        pinned_rows.append(item)
    ordered["rows"] = pinned_rows
    pinned_unmatched = []
    for item in report["unmatched"]:
        out = {}
        for key in UNMATCHED_KEYS:
            out[key] = item[key]
        pinned_unmatched.append(out)
    ordered["unmatched"] = pinned_unmatched
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: queue_done_stamp_exempt.py --check --round R<n> "
         "[--root PATH] [--json]\n"
         "  --round is mandatory: a default round would decide on its own\n"
         "  whether an exemption is still in force.\n"
         "  exit 0 = no closed row is still debt (EXEMPT-CLEAN)\n"
         "  exit 2 = at least one closed row is still debt (EXEMPT-DEBT)\n"
         "  exit 3 = a queue file or the declaration is unreadable\n"
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
                sys.stdout.write("E_SEX_BAD_ARGS: --round needs a value\n")
                return 5
            round_text = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_SEX_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_SEX_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_SEX_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_SEX_BAD_ARGS: --round is mandatory\n")
        sys.stdout.write(USAGE)
        return 5
    round_no = round_number(round_text)
    if round_no is None:
        sys.stdout.write("E_SEX_BAD_ARGS: --round is not a round: %s\n"
                         % round_text)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit(root, round_no)
    except QueueDoneStampExemptError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "EXEMPT-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))