# gate_decl_identity.py - a declared gate identity resolved against the rows
# Criteria AC-GDI1..AC-GDI6 were pre-registered in state/queue/tech.md as the
# R2313 seed row BEFORE this file existed.
#
# Why this exists: gate_decl_append validates an identity only as a
# NON-EMPTY UNIQUE STRING, so the writer cannot tell a live row identity
# from a typo. R2313 measured it live: "--identity -" was planned as a
# brand-new declaration (427B -> 547B) because "-" is not the declared
# "-#02878cdc", while the true duplicate was refused E_GDA_DUP. A
# misaddressed blocker lands silently and then reads INERT against every
# row forever.
#
# This reader takes the declaration plus the live queue text and resolves
# every declared identity against the rows: MATCHED (one row carries it),
# UNMATCHED (no row carries it) or AMBIGUOUS (a bare prefix several rows
# share). It is a reader, not a gate: it refuses nothing about the
# identity, it names why.
#
# Both laws are IMPORTED, never re-implemented:
#   - the queue path, the queue text and the gate marker come from
#     queue_head (patching those imports moves the reading),
#   - the identity shape and the declaration come from machine_gate,
#   - the row law and the criteria prefix come from queue_floor and
#     queue_row.
#
# Pure read: nothing is written, no clock is read, no network import.
# Source is pure ASCII, stdlib only.
#
# CLI: gate_decl_identity.py --check [QUEUE] [--declaration PATH]
#      [--root PATH] [--json]
#   exit 0 = every declared identity is MATCHED
#   exit 2 = at least one UNMATCHED or AMBIGUOUS identity
#   exit 3 = the declaration or the queue is missing / unreadable / malformed
#   exit 5 = bad flags

import io
import json
import os
import sys

import machine_gate as MG
import queue_floor as QF
import queue_head as QH
import queue_row as QR

STATES = ("MATCHED", "UNMATCHED", "AMBIGUOUS")
LEVELS = ("open", "gated", "done")
CLAIMABLE_LEVEL = "open"

REPORT_KEYS = (
    "queue",
    "path",
    "declaration",
    "declarations",
    "rows",
    "matched",
    "unmatched",
    "ambiguous",
    "readings",
    "verdict",
)

READING_KEYS = ("identity", "state", "line", "prefix", "level", "claimable",
                "detail", "carriers")

CARRIER_KEYS = ("line", "prefix", "identity", "level")


class GateIdentityError(Exception):
    """Raised when the reader cannot produce an honest reading."""

    def __init__(self, code, detail):
        Exception.__init__(self, "%s: %s" % (code, detail))
        self.code = code
        self.detail = detail


def rows(root, name="tech"):
    """Every row of one queue, with its identity, in FILE order.

    A done row is read as level "done" and a gated row as level "gated", so
    a MATCHED identity on a row that is not offered is still MATCHED
    (AC-GDI4): this reader never criticises claimability.
    """
    rel = QH.queue_path(name)
    if rel is None:
        raise GateIdentityError("E_GDI_BAD_QUEUE", "unknown queue %s" % name)
    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        raise GateIdentityError("E_GDI_NO_QUEUE", rel.replace(os.sep, "/"))
    try:
        text = QH.read_text(full)
    except QH.QueueHeadError as exc:
        raise GateIdentityError("E_GDI_NO_QUEUE", exc.detail)
    found = []
    for index, line in enumerate(text.split("\n"), 1):
        done = QF.is_done_row(line)
        if not done and not QF.is_open_row(line):
            continue
        prefix = QR.scan_row(line)["prefix"]
        if done:
            level = "done"
        elif QH.gate_marker(line):
            level = "gated"
        else:
            level = "open"
        found.append({"line": index,
                      "prefix": prefix,
                      "identity": MG.identity_of(prefix, line),
                      "level": level,
                      "claimable": level == CLAIMABLE_LEVEL})
    return found


def split_identity(identity):
    """The prefix part and the digest part of a declared identity."""
    body = identity if isinstance(identity, str) else ""
    if "#" in body:
        prefix, digest = body.rsplit("#", 1)
        return prefix, digest
    return body, ""


def carrier_rows(rows_found, prefix):
    """The rows whose own criteria prefix equals the declared one.

    A row carrying no criteria prefix renders as "-" in identity_of, so the
    comparison uses that same rendering instead of a second rule.
    """
    return [row for row in rows_found if (row["prefix"] or "-") == prefix]


def resolve(identity, rows_found):
    """Resolve one declared identity against the rows (AC-GDI2)."""
    exact = [row for row in rows_found if row["identity"] == identity]
    if len(exact) == 1:
        row = exact[0]
        return {"state": "MATCHED",
                "line": row["line"],
                "prefix": row["prefix"],
                "level": row["level"],
                "claimable": row["claimable"],
                "detail": "one row carries this identity",
                "carriers": []}
    if len(exact) > 1:
        return {"state": "AMBIGUOUS",
                "line": None,
                "prefix": exact[0]["prefix"],
                "level": None,
                "claimable": None,
                "detail": "%d rows carry this exact text" % len(exact),
                "carriers": list(exact)}
    prefix, digest = split_identity(identity)
    carriers = carrier_rows(rows_found, prefix)
    if digest:
        # A digest that pins nothing is an identity no row carries; the
        # prefix's carriers are named as the reason, not offered as a match.
        detail = "no row carries this identity"
        if carriers:
            detail = ("%s; %d row(s) carry the prefix %s"
                      % (detail, len(carriers), prefix or '""'))
        return {"state": "UNMATCHED",
                "line": None,
                "prefix": prefix,
                "level": None,
                "claimable": None,
                "detail": detail,
                "carriers": []}
    if len(carriers) == 1:
        row = carriers[0]
        return {"state": "MATCHED",
                "line": row["line"],
                "prefix": row["prefix"],
                "level": row["level"],
                "claimable": row["claimable"],
                "detail": "the bare prefix names exactly one row",
                "carriers": []}
    if len(carriers) > 1:
        return {"state": "AMBIGUOUS",
                "line": None,
                "prefix": prefix,
                "level": None,
                "claimable": None,
                "detail": ("the bare prefix %s is shared by %d rows and no "
                           "digest pins one" % (prefix or '""',
                                                len(carriers))),
                "carriers": list(carriers)}
    return {"state": "UNMATCHED",
            "line": None,
            "prefix": prefix,
            "level": None,
            "claimable": None,
            "detail": "no row carries this identity",
            "carriers": []}


def review(root, name="tech", declaration=None):
    """Resolve every declared identity under root; the closed report shape."""
    decl_rel = declaration or MG.DEFAULT_DECLARATION
    try:
        decl = MG.read_declaration(os.path.join(root, decl_rel))
    except MG.MachineGateError as exc:
        raise GateIdentityError("E_GDI_BAD_DECLARATION", exc.detail)
    found = rows(root, name)
    readings = []
    counts = {"MATCHED": 0, "UNMATCHED": 0, "AMBIGUOUS": 0}
    for entry in decl["gates"]:
        reading = resolve(entry["identity"], found)
        counts[reading["state"]] += 1
        out = {"identity": entry["identity"]}
        for key in READING_KEYS[1:]:
            out[key] = reading[key]
        readings.append(out)
    verdict = "ALL-MATCHED" if (counts["UNMATCHED"] == 0 and
                               counts["AMBIGUOUS"] == 0) else "IDENTITY-DEBT"
    return {"queue": name,
            "path": (QH.queue_path(name) or "").replace(os.sep, "/"),
            "declaration": decl_rel.replace(os.sep, "/"),
            "declarations": len(decl["gates"]),
            "rows": len(found),
            "matched": counts["MATCHED"],
            "unmatched": counts["UNMATCHED"],
            "ambiguous": counts["AMBIGUOUS"],
            "readings": readings,
            "verdict": verdict}


def one_line(report):
    """The single line an operator reads."""
    return ("GATE DECL IDENTITY declarations=%d rows=%d matched=%d "
            "unmatched=%d ambiguous=%d verdict=%s"
            % (report["declarations"], report["rows"], report["matched"],
               report["unmatched"], report["ambiguous"], report["verdict"]))


def render(report):
    """The one line, then every identity reading with its carriers."""
    out = [one_line(report)]
    for item in report["readings"]:
        where = "line=%s level=%s" % (item["line"], item["level"])
        out.append("  %s %s %s (%s)"
                   % (item["state"], item["identity"], where, item["detail"]))
        for carrier in item["carriers"]:
            out.append("    CARRIER %s:%d %s level=%s"
                       % (report["path"], carrier["line"],
                          carrier["identity"], carrier["level"]))
    return "\n".join(out)


def to_json(report):
    """Serialise in a stable key order (ASCII, one trailing LF)."""
    ordered = {}
    for key in REPORT_KEYS:
        ordered[key] = report[key]
    readings = []
    for item in report["readings"]:
        pinned = {}
        for key in READING_KEYS:
            pinned[key] = item[key]
        carriers = []
        for carrier in item["carriers"]:
            row = {}
            for key in CARRIER_KEYS:
                row[key] = carrier[key]
            carriers.append(row)
        pinned["carriers"] = carriers
        readings.append(pinned)
    ordered["readings"] = readings
    return json.dumps(ordered, ensure_ascii=True, sort_keys=False) + "\n"


USAGE = ("usage: gate_decl_identity.py --check [QUEUE] [--declaration PATH]\n"
         "      [--root PATH] [--json]\n"
         "  QUEUE defaults to tech (state/queue/<QUEUE>.md)\n"
         "  exit 0 = every declared identity is MATCHED\n"
         "  exit 2 = at least one UNMATCHED or AMBIGUOUS identity\n"
         "  exit 3 = declaration or queue missing, unreadable or malformed\n"
         "  exit 5 = bad flags\n")


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
        if arg == "--check":
            operation = True
        elif arg == "--json":
            as_json = True
        elif arg == "--root":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_GDI_BAD_ARGS: --root needs a path\n")
                return 5
            root = argv[index]
        elif arg == "--declaration":
            index += 1
            if index >= len(argv):
                sys.stdout.write("E_GDI_BAD_ARGS: --declaration needs a path\n")
                return 5
            declaration = argv[index]
        elif arg in ("--help", "-h"):
            sys.stdout.write(USAGE)
            return 0
        elif arg.startswith("-"):
            sys.stdout.write("E_GDI_BAD_ARGS: unknown flag %s\n" % arg)
            sys.stdout.write(USAGE)
            return 5
        else:
            name = arg
        index += 1
    if not operation:
        sys.stdout.write("E_GDI_BAD_ARGS: --check is required\n")
        sys.stdout.write(USAGE)
        return 5
    if QH.queue_path(name) is None:
        sys.stdout.write("E_GDI_BAD_ARGS: unknown queue %s\n" % name)
        sys.stdout.write(USAGE)
        return 5
    try:
        report = review(root, name, declaration)
    except GateIdentityError as exc:
        sys.stdout.write("%s\n" % exc.code)
        return 3
    if as_json:
        sys.stdout.write(to_json(report))
    else:
        sys.stdout.write(render(report) + "\n")
    if report["verdict"] == "IDENTITY-DEBT":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))