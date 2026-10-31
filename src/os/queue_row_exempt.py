# queue_row_exempt.py - record an ACCEPTED pre-registration exemption
# Criteria AC-QRX1..AC-QRX6 were pre-registered in state/queue/tech.md as the
# R2253 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# E_QRX / os-queue-row-exempt / test_queue_row_exempt were git grep -F
# zero-occupancy rc=1, while queue_row_exempt / AC-QRX / prefix_exempt hit
# ONLY prose (the seed row itself, src/os/backlog.md, src/os/state.json and
# docs/status-export.json) - disclosed, with zero code occupancy.
#
# Why this exists: queue_row gates every claimable open row on naming its
# criteria prefix. Nine live rows fail that gate and every one of them
# predates the law, so the reading can never go green - the only ways out are
# rewriting history (which the law must not do) or silently widening the gate
# (which erases the debt). This module adds the third way: an ACCEPTED
# exemption, declared in one file, keyed by a stable row identity instead of a
# line number, carrying a dated reason, and reported back as exempt_today
# against still_debt so acceptance is a named fact rather than a blind spot.
#
# The gate itself is NOT re-implemented: violations come from
# queue_row.audit_root, so the marker law, the two accepted criteria forms and
# the row law all stay in the one place that owns them (AC-QRX5). The
# declaration is the only new input.
#
# Declaration file (pinned): state/queue/prefix_exempt.json
#   {"exemptions": [{"queue": "tech",
#                    "identity": "docker-compose",
#                    "declared": "R2276",
#                    "reason": "why this row is accepted as it stands",
#                    "until": "R2300"}]}
# Required entry keys: queue, identity, declared, reason. Optional: until
# (absent or null means "no expiry"). Any other key is refused, because a
# declaration that silently carries ignored data is not reviewable.
#
# Row identity law (stable under line shifts, readable to a reviewer):
#   1. the first backticked token in the row when there is one, because the
#      module or file a row names is its semantic key, else
#   2. the row's leading ASCII token plus "#" and a sha8 of the normalised row
#      text - readable at a glance, unique by construction, and independent of
#      the line number. Two TEXTUALLY IDENTICAL rows therefore share an
#      identity and an entry matching both is refused (E_QRX_AMBIGUOUS),
#      because one entry must never exempt two rows.
# An identity that matches NO live violating row is reported as unmatched -
# inert, never green-washing, because the row it meant to exempt stays debt.
#
# Expiry (AC-QRX4): an entry whose until round is earlier than the round being
# checked is EXPIRED and the row reads as debt again, with the until round
# named. The round is MANDATORY on the command line - a default round would
# silently decide on its own whether debt is still waived.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.

import hashlib
import io
import json
import os
import re
import sys

import queue_floor as QF
import queue_row as QR

DECL_REL = os.path.join("state", "queue", "prefix_exempt.json")

TOP_KEYS = ("exemptions", "note")

ENTRY_KEYS = ("queue", "identity", "declared", "reason", "until")
REQUIRED_KEYS = ("queue", "identity", "declared", "reason")

ROW_KEYS = ("file", "line", "identity", "status", "until")
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

CODE_RE = re.compile(r"`([^`]+)`")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]{2,}")
ROUND_RE = re.compile(r"^R([0-9]+)$")


class QueueRowExemptError(Exception):
    """Raised when an honest reading cannot be produced."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def identity_of(text):
    """The stable identity of one row, derived from the row text alone."""
    norm = " ".join(text.split())
    hit = CODE_RE.search(norm)
    if hit:
        code = hit.group(1).strip()
        if code:
            return code
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
    return tuple(name for name, _rel in QF.QUEUE_PATHS)


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
        raise QueueRowExemptError("E_QRX_BAD_DECL", "%s (%s)" % (shown, exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise QueueRowExemptError("E_QRX_BAD_DECL",
                                 "%s is not JSON (%s)" % (shown, exc))
    if not isinstance(data, dict):
        raise QueueRowExemptError("E_QRX_BAD_DECL", "%s is not an object"
                                  % shown)
    for key in data:
        if key not in TOP_KEYS:
            raise QueueRowExemptError("E_QRX_BAD_DECL",
                                      "%s carries unknown key %r"
                                      % (shown, key))
    if "exemptions" not in data:
        raise QueueRowExemptError("E_QRX_BAD_DECL",
                                  "%s carries no exemptions list" % shown)
    if not isinstance(data["exemptions"], list):
        raise QueueRowExemptError("E_QRX_BAD_DECL",
                                  "%s exemptions is not a list" % shown)
    note = data.get("note")
    if note is not None and not isinstance(note, str):
        raise QueueRowExemptError("E_QRX_BAD_DECL",
                                  "%s note is not a string" % shown)
    entries = []
    seen = set()
    for index, raw in enumerate(data["exemptions"]):
        where = "%s entry %d" % (shown, index + 1)
        if not isinstance(raw, dict):
            raise QueueRowExemptError("E_QRX_BAD_DECL",
                                      "%s is not an object" % where)
        for key in raw:
            if key not in ENTRY_KEYS:
                raise QueueRowExemptError("E_QRX_BAD_DECL",
                                          "%s carries unknown key %r"
                                          % (where, key))
        for key in REQUIRED_KEYS:
            if key not in raw:
                raise QueueRowExemptError("E_QRX_BAD_DECL",
                                          "%s is missing %r" % (where, key))
        queue = raw["queue"]
        identity = raw["identity"]
        declared = raw["declared"]
        reason = raw["reason"]
        until = raw.get("until")
        if not isinstance(queue, str) or queue not in allowed_queues():
            raise QueueRowExemptError("E_QRX_BAD_DECL",
                                      "%s names unknown queue %r"
                                      % (where, queue))
        if not isinstance(identity, str) or not identity.strip():
            raise QueueRowExemptError("E_QRX_BAD_IDENTITY",
                                      "%s identity is empty" % where)
        if identity != identity.strip():
            raise QueueRowExemptError("E_QRX_BAD_IDENTITY",
                                      "%s identity carries padding" % where)
        if round_number(declared) is None:
            raise QueueRowExemptError("E_QRX_BAD_DATE",
                                      "%s declared is not a round: %r"
                                      % (where, declared))
        if until is not None:
            if round_number(until) is None:
                raise QueueRowExemptError("E_QRX_BAD_DATE",
                                          "%s until is not a round: %r"
                                          % (where, until))
            if round_number(until) < round_number(declared):
                raise QueueRowExemptError("E_QRX_BAD_DATE",
                                          "%s until predates declared"
                                          % where)
        if not isinstance(reason, str) or not reason.strip():
            raise QueueRowExemptError("E_QRX_BAD_REASON",
                                      "%s carries no reason" % where)
        pair = (queue, identity)
        if pair in seen:
            raise QueueRowExemptError("E_QRX_DUP",
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
            "identity": identity_of(bad.get("excerpt", "")),
            "queue": queue_of_path(bad["file"]),
            "status": "DEBT",
            "until": None,
        })
    return rows


def audit(root, round_no):
    """Join the declaration with the gate reading; never writes."""
    if ROUND_RE.match("R%d" % round_no) is None:
        raise QueueRowExemptError("E_QRX_BAD_ARGS", "bad round")
    declaration = read_declaration(root)
    gate = QR.audit_root(root)
    missing = gate.get("missing") or []
    if missing:
        raise QueueRowExemptError("E_QRX_BAD_QUEUE", ",".join(missing))
    rows = live_rows(gate)
    unmatched = []
    exempt_today = 0
    exempt_expired = 0
    if declaration["status"] == "PINNED":
        by_pair = {}
        for index, row in enumerate(rows):
            by_pair.setdefault((row["queue"], row["identity"]), []).append(index)
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
                raise QueueRowExemptError(
                    "E_QRX_AMBIGUOUS",
                    "%s:%s matches %d rows (%s)"
                    % (entry["queue"], entry["identity"], len(hits), names))
            index = hits[0]
            if index in entry_hits:
                raise QueueRowExemptError(
                    "E_QRX_DUP",
                    "two entries match %s:%d" % (rows[index]["file"],
                                                 rows[index]["line"]))
            entry_hits[index] = entry
        for index, entry in entry_hits.items():
            rows[index]["until"] = entry["until"]
            until = round_number(entry["until"])
            if until is not None and round_no > until:
                rows[index]["status"] = "EXPIRED"
                exempt_expired += 1
            else:
                rows[index]["status"] = "EXEMPT"
                exempt_today += 1
        for row in rows:
            if row["status"] not in ("EXEMPT", "EXPIRED"):
                row["status"] = "DEBT"
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
    return ("QUEUE ROW EXEMPT round=R%d declaration=%s entries=%d "
            "violations=%d exempt=%d expired=%d still_debt=%d unmatched=%d "
            "verdict=%s"
            % (report["round"], report["declaration"], report["entries"],
               report["violation_count"], report["exempt_today"],
               report["exempt_expired"], report["still_debt"],
               report["unmatched_count"], report["verdict"]))


def render(report):
    """The one line, then every row and every unmatched entry."""
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


USAGE = ("usage: queue_row_exempt.py --check --round R<n> [--root PATH] "
         "[--json]\n"
         "  --round is mandatory: a default round would decide on its own\n"
         "  whether an exemption is still in force.\n"
         "  exit 0 = no row is still debt (EXEMPT-CLEAN)\n"
         "  exit 2 = at least one row is still debt (EXEMPT-DEBT)\n"
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
                sys.stdout.write("E_QRX_BAD_ARGS: --round needs a value\n")
                return 5
            round_text = argv[index]
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_QRX_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        else:
            sys.stdout.write("E_QRX_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        index += 1
    if not check:
        sys.stdout.write("E_QRX_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if round_text is None:
        sys.stdout.write("E_QRX_BAD_ARGS: --round is mandatory\n")
        sys.stdout.write(USAGE)
        return 5
    round_no = round_number(round_text)
    if round_no is None:
        sys.stdout.write("E_QRX_BAD_ARGS: --round is not a round: %s\n"
                         % round_text)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = audit(root, round_no)
    except QueueRowExemptError as exc:
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