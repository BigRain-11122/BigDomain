# machine_gate.py - which claimable row this host can actually deliver
# Criteria AC-MGT1..AC-MGT6 were pre-registered in state/queue/tech.md as the
# R2270 seed row BEFORE this file existed. Anchor check at HEAD 2026-10-31:
# "E_MGT", "test_machine_gate" and "src/os/machine_gate.py" were git grep -F
# zero-occupancy rc=1; "machine_gate", "AC-MGT" and "os-machine-gate" hit only
# prose and closeout/export helpers (the seed row that names them, this
# board, state.json, status-export.json, state/debt.md), disclosed here.
#
# Why this exists: queue_head answers WHICH row comes first, but it cannot
# know that a row is undeliverable for a MACHINE reason. The docker-absent
# row and the toolkit row are skipped today because a human remembers the
# prose, and the reader honestly offers them as the head. This reader joins
# one declared file (state/machine_gates.json) with the head reading and
# names the first claimable row this host is NOT blocked from, so a machine
# gate becomes data with a date instead of the operator's memory.
#
# The head law is IMPORTED from queue_head, never re-implemented: every
# candidate comes out of queue_head.head_text, and advancing past a blocked
# row only MASKS that row's leading marker in a copy of the text (same line
# count, so line numbers stay honest) and asks the same law again. A patched
# head law therefore flows straight through, which the suite proves.
#
# Row identity is a capability-blocker key that survives a line shift:
# "<prefix>#<sha8 of the row text>". A row that moves inside the file keeps
# its identity; a row whose text changes does not, and its declaration then
# reads INERT rather than silently gating something else.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: machine_gate.py --gate [QUEUE] [--root PATH] [--decl PATH] [--json]
#   exit 0 = a row was offered
#   exit 2 = NO-OFFER (nothing claimable is unblocked) - an honest reading
#   exit 3 = the declaration or the queue is missing / unreadable / malformed
#   exit 5 = bad flags

import hashlib
import io
import json
import os
import sys

import queue_floor as QF
import queue_head as QH

VERDICTS = ("OFFERED", "NO-OFFER", "MISSING")

# The capability vocabulary is declared here on purpose: a blocker may only
# name a capability this module knows, so a typo fails closed instead of
# quietly blocking nothing.
CAPABILITIES = ("battery", "docker", "gpu", "toolkit")

DECLARATION_KEYS = ("version", "declared_by", "reason", "gates")
ENTRY_KEYS = ("identity", "capability", "reason", "declared_by")

REPORT_KEYS = ("queue", "path", "declaration", "declarations", "candidates",
               "offered", "blocked", "inert", "blocked_rows", "verdict")
OFFER_KEYS = ("line", "prefix", "identity", "text")
BLOCK_KEYS = ("line", "prefix", "identity", "capability", "reason",
              "declared_by")
INERT_KEYS = ("identity", "capability", "reason", "declared_by", "line")

DEFAULT_DECLARATION = os.path.join("state", "machine_gates.json")

# A queue cannot hold this many claimable rows; the guard stops a loop law
# from spinning instead of hanging the window.
CANDIDATE_GUARD = 500

MASK_CHAR = "~"


class MachineGateError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def digest8(text):
    """The stable text digest an identity carries."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def identity_of(prefix, text):
    """The declaration key: the criteria prefix plus the row-text digest."""
    return "%s#%s" % (prefix if prefix else "-", digest8(text))


def mask_row(line):
    """Neutralise a row's leading marker, keeping the line count and length."""
    if not line:
        return line
    return MASK_CHAR + line[1:]


def read_declaration(path):
    """Read and validate the declared blockers; fail closed on every defect."""
    if not os.path.isfile(path):
        raise MachineGateError("E_MGT_NO_DECL", path)
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError) as exc:
        raise MachineGateError("E_MGT_NO_DECL", "%s (%s)" % (path, exc))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise MachineGateError("E_MGT_BAD_DECL", "%s (%s)" % (path, exc))
    if not isinstance(data, dict):
        raise MachineGateError("E_MGT_BAD_DECL", "top level is not an object")
    for key in DECLARATION_KEYS:
        if key not in data:
            raise MachineGateError("E_MGT_BAD_DECL", "missing %s" % key)
    for key in data:
        if key not in DECLARATION_KEYS:
            raise MachineGateError("E_MGT_BAD_DECL", "unknown key %s" % key)
    if not isinstance(data["version"], int) or isinstance(data["version"], bool):
        raise MachineGateError("E_MGT_BAD_DECL", "version is not an int")
    for key in ("declared_by", "reason"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise MachineGateError("E_MGT_BAD_DECL", "%s is not a string" % key)
    gates = data["gates"]
    if not isinstance(gates, list):
        raise MachineGateError("E_MGT_BAD_DECL", "gates is not a list")
    seen = set()
    entries = []
    for index, entry in enumerate(gates):
        where = "gate %d" % index
        if not isinstance(entry, dict):
            raise MachineGateError("E_MGT_BAD_ENTRY", "%s is not an object"
                                   % where)
        for key in ENTRY_KEYS:
            if key not in entry:
                raise MachineGateError("E_MGT_BAD_ENTRY", "%s missing %s"
                                       % (where, key))
        for key in entry:
            if key not in ENTRY_KEYS:
                raise MachineGateError("E_MGT_BAD_ENTRY", "%s unknown key %s"
                                       % (where, key))
        for key in ENTRY_KEYS:
            if not isinstance(entry[key], str) or not entry[key].strip():
                raise MachineGateError("E_MGT_BAD_ENTRY", "%s %s is empty"
                                       % (where, key))
        if entry["capability"] not in CAPABILITIES:
            raise MachineGateError("E_MGT_BAD_CAPABILITY",
                                   "%s names %s" % (where, entry["capability"]))
        if entry["identity"] in seen:
            raise MachineGateError("E_MGT_BAD_ENTRY", "%s repeats identity %s"
                                   % (where, entry["identity"]))
        seen.add(entry["identity"])
        entries.append({"identity": entry["identity"],
                        "capability": entry["capability"],
                        "reason": entry["reason"],
                        "declared_by": entry["declared_by"]})
    return {"version": data["version"],
            "declared_by": data["declared_by"],
            "reason": data["reason"],
            "gates": entries}


def candidates(root, name="tech"):
    """Every offerable row in FILE order, read through queue_head's own law."""
    rel = QH.queue_path(name)
    if rel is None:
        raise MachineGateError("E_MGT_BAD_QUEUE", "unknown queue %s" % name)
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        raise MachineGateError("E_MGT_NO_QUEUE", rel)
    try:
        text = QH.read_text(full)
    except QH.QueueHeadError as exc:
        raise MachineGateError("E_MGT_NO_QUEUE", exc.detail)
    rows = []
    masked = text
    for _step in range(CANDIDATE_GUARD):
        report = QH.head_text(name, rel, masked)
        head = report["head"]
        if head is None:
            return rows
        line = head["line"]
        lines = masked.split("\n")
        if line < 1 or line > len(lines):
            raise MachineGateError("E_MGT_ADVANCE",
                                   "line %d outside the text" % line)
        body = lines[line - 1]
        rows.append({"line": line,
                     "prefix": head["prefix"],
                     "identity": identity_of(head["prefix"], body),
                     "text": head["text"]})
        lines[line - 1] = mask_row(body)
        masked = "\n".join(lines)
    raise MachineGateError("E_MGT_ADVANCE", "candidate guard exceeded")


def inert_line(root, name, identity):
    """The line of a queue row carrying this identity, or None when absent."""
    rel = QH.queue_path(name)
    if rel is None or "#" not in identity:
        return None
    want = identity.rsplit("#", 1)[1]
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        return None
    try:
        with io.open(full, "r", encoding="utf-8") as handle:
            text = handle.read()
    except (IOError, OSError, UnicodeDecodeError):
        return None
    for index, line in enumerate(text.split("\n"), 1):
        # The row law is queue_floor's, called here rather than copied.
        if (QF.is_open_row(line) or QF.is_done_row(line)) \
                and digest8(line) == want:
            return index
    return None


def gate(root, name="tech", declaration=None):
    """Join the declaration with the head reading; the closed report shape."""
    decl_rel = declaration or DEFAULT_DECLARATION
    decl = read_declaration(os.path.join(root, decl_rel))
    shown_decl = decl_rel.replace(os.sep, "/")
    rel = QH.queue_path(name)
    if rel is None:
        raise MachineGateError("E_MGT_BAD_QUEUE", "unknown queue %s" % name)
    shown = rel.replace(os.sep, "/")
    rows = candidates(root, name)
    by_identity = {}
    for entry in decl["gates"]:
        by_identity[entry["identity"]] = entry
    offered = None
    blocked = []
    matched = set()
    for row in rows:
        entry = by_identity.get(row["identity"])
        if entry is None:
            if offered is None:
                offered = row
            continue
        matched.add(row["identity"])
        blocked.append({"line": row["line"],
                        "prefix": row["prefix"],
                        "identity": row["identity"],
                        "capability": entry["capability"],
                        "reason": entry["reason"],
                        "declared_by": entry["declared_by"]})
    inert = []
    for entry in decl["gates"]:
        if entry["identity"] in matched:
            continue
        inert.append({"identity": entry["identity"],
                      "capability": entry["capability"],
                      "reason": entry["reason"],
                      "declared_by": entry["declared_by"],
                      "line": inert_line(root, name, entry["identity"])})
    return {"queue": name,
            "path": shown,
            "declaration": shown_decl,
            "declarations": len(decl["gates"]),
            "candidates": len(rows),
            "offered": offered,
            "blocked": blocked,
            "inert": inert,
            "blocked_rows": len(blocked),
            "verdict": "OFFERED" if offered is not None else "NO-OFFER"}


def missing_report(name, declaration=None, rel=None):
    """A queue that does not exist reads MISSING with no invented offer."""
    decl_rel = declaration or DEFAULT_DECLARATION
    return {"queue": name,
            "path": (rel or "state/queue/%s.md" % name).replace(os.sep, "/"),
            "declaration": decl_rel.replace(os.sep, "/"),
            "declarations": 0,
            "candidates": 0,
            "offered": None,
            "blocked": [],
            "inert": [],
            "blocked_rows": 0,
            "verdict": "MISSING"}


def one_line(report):
    """The single line an operator reads."""
    if report["verdict"] == "MISSING":
        return ("MACHINE GATE %s MISSING declarations=%d"
                % (report["queue"], report["declarations"]))
    if report["offered"] is None:
        return ("MACHINE GATE %s NO-OFFER declarations=%d blocked=%d "
                "candidates=%d"
                % (report["queue"], report["declarations"],
                   report["blocked_rows"], report["candidates"]))
    return ("MACHINE GATE %s line=%d prefix=%s declarations=%d blocked=%d "
            "inert=%d candidates=%d verdict=%s"
            % (report["queue"], report["offered"]["line"],
               report["offered"]["prefix"], report["declarations"],
               report["blocked_rows"], len(report["inert"]),
               report["candidates"], report["verdict"]))


def render(report):
    """Full text rendering: the one line, the offer, then every declaration."""
    out = [one_line(report)]
    if report["offered"] is not None:
        out.append("  OFFER %s:%d %s"
                   % (report["path"], report["offered"]["line"],
                      report["offered"]["text"]))
    for item in report["blocked"]:
        out.append("  BLOCK %s:%d %s %s (%s, declared %s)"
                   % (report["path"], item["line"], item["identity"],
                      item["capability"], item["reason"],
                      item["declared_by"]))
    for item in report["inert"]:
        out.append("  INERT %s %s (line=%s)"
                   % (item["identity"], item["capability"],
                      "none" if item["line"] is None else item["line"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    if report["offered"] is not None:
        offer_out = {}
        for key in OFFER_KEYS:
            offer_out[key] = report["offered"][key]
        ordered["offered"] = offer_out
    blocked_out = []
    for item in report["blocked"]:
        pinned = {}
        for key in BLOCK_KEYS:
            pinned[key] = item[key]
        blocked_out.append(pinned)
    ordered["blocked"] = blocked_out
    inert_out = []
    for item in report["inert"]:
        pinned = {}
        for key in INERT_KEYS:
            pinned[key] = item[key]
        inert_out.append(pinned)
    ordered["inert"] = inert_out
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: machine_gate.py --gate [QUEUE] [--root PATH] "
         "[--decl PATH] [--json]\n"
         "  QUEUE defaults to tech (state/queue/<QUEUE>.md)\n"
         "  --decl defaults to %s\n"
         "  exit 0 = a row was offered\n"
         "  exit 2 = NO-OFFER (nothing claimable is unblocked)\n"
         "  exit 3 = declaration or queue missing / unreadable / malformed\n"
         "  exit 5 = bad flags\n" % DEFAULT_DECLARATION.replace(os.sep, "/"))


def main(argv):
    operation = False
    as_json = False
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    name = "tech"
    declaration = None
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--gate":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg in ("--root", "--decl"):
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_MGT_BAD_ARGS: %s needs a path\n" % arg)
                return 5
            if arg == "--root":
                root = argv[index]
            else:
                declaration = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_MGT_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            name = arg
        index += 1
    if not operation:
        sys.stdout.write("E_MGT_BAD_ARGS: --gate is required\n")
        sys.stdout.write(USAGE)
        return 5
    if QH.queue_path(name) is None:
        sys.stdout.write("E_MGT_BAD_ARGS: unknown queue %s\n" % name)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = gate(root, name, declaration)
    except MachineGateError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "NO-OFFER":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))