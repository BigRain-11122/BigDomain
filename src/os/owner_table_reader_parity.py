"""owner_table_reader_parity (R2412; criteria AC-OTRP1..AC-OTRP6 pinned inside
the R2399 tech seed row of state/queue/tech.md:480 BEFORE this code).

Why this exists: two readers now answer two different questions and nothing
publishes the difference.

    owner_table_parity      (R2390) "does the declared table match the parser"
    owner_table_usage_wire  (R2399) "which constants ARE the declared table"

Both are right about their own question and they disagree on the same tree.
Measured at HEAD 2026-11-03 over every non-test src/os/*.py: 1016 files, 40
disagreements, 2 files where both readers agree on a table, and 970 files
where neither sees a table. On those 40 rows the law reports a one-sided
table while the wire correctly reads NO-TABLE - the wire's whole job - so an
operator holding either log alone cannot tell a tool with NO table from a tool
whose usage path is named neither way, and cannot tell a corrected false
positive from a real drift.

This module is that missing face. It asks BOTH shipped readers of the same
file and publishes every disagreement with the reason it is one:

  - law-only-table   the law sees a table the usage path never names (the
                     shape the wire was built to remove), carrying the flags
                     the law actually reported, never a canned number;
  - wire-only-table  a usage-named table the law does not derive;
  - table-differs    both see a table and the flags do not match.

The historical one-per-round copies are classified SUPERSEDED rather than
counted as debt, and that classification is derived from the filename family
(NAME_R<digits>.py beside a live NAME.py), never from a whitelist file.

Measured limits, stated rather than hidden:

  (a) the seed row predicted 37 one-per-round copies; measured this window 35
      rows in that family (42 files match the family pattern, 7 of them
      already read NO-TABLE on both sides and so are not disagreement rows);
  (b) SUPERSEDED removes a row from the debt count but never from the report:
      every superseded row is still printed with both verdicts, because the
      point of this face is that the set difference stays visible;
  (c) the verdict on the real tree is PARITY-SPLIT, not CLEAN - five rows are
      genuine law false positives (battery_followup_help_wire, evidence_R2372,
      r2140_fold, retry_naming, run_identity). Reporting CLEAN here would be
      the very lie this module exists to prevent.

CLI:

    python owner_table_reader_parity.py [ROOT] [--json]
    python owner_table_reader_parity.py --help

Exit codes: 0 PARITY-CLEAN, 2 PARITY-SPLIT, 3 root missing or unreadable,
5 bad this-tool flags.

Stdlib only, ASCII source, zero network, no clock, read-only: this module
opens tools for reading and creates nothing.

CRITERIA LABEL NOTE (measurement, not preference): the R2399 seed row pinned
AC-OTRP1..AC-OTRP6 / E_OTRP_*; a fresh anchor check at HEAD 2026-11-03 found
that prefix zero-occupancy in code (it appears only in prose and state files),
so the pinned labels are used as-is.
"""

import json
import os
import re
import sys

LABEL = "OWNER TABLE READER PARITY"

VERDICT_CLEAN = "PARITY-CLEAN"
VERDICT_SPLIT = "PARITY-SPLIT"

REASON_LAW_ONLY = "law-only-table"
REASON_WIRE_ONLY = "wire-only-table"
REASON_TABLE_DIFFERS = "table-differs"

E_OTRP_UNREADABLE = "E_OTRP_UNREADABLE"
E_OTRP_BAD_FLAG = "E_OTRP_BAD_FLAG"

EXIT_CLEAN = 0
EXIT_SPLIT = 2
EXIT_UNREADABLE = 3
EXIT_BAD_FLAG = 5

JSON_KEYS = ("root", "scanned", "rows", "superseded", "split", "verdict")
ROW_KEYS = ("tool", "law", "wire", "reason", "flags", "superseded")

ROUND_SUFFIX = re.compile(r"^(?P<base>.+)_R(?P<round>[0-9]+)$")

DEFAULT_ROOT = os.path.dirname(os.path.abspath(__file__))


def _law():
    """The shipped table law, imported at CALL time (AC-OTRP1)."""
    import owner_table_parity
    return owner_table_parity


def _wire():
    """The shipped usage wire, imported at CALL time (AC-OTRP1)."""
    import owner_table_usage_wire
    return owner_table_usage_wire


def _face(payload):
    """The comparable face of one reading: verdict plus both one-sided lists."""
    return (payload["verdict"], tuple(payload["missing_in_table"]),
            tuple(payload["missing_in_parser"]))


def list_tools(root):
    """Every non-test .py directly under root, in name order.

    Tests are excluded because a suite's own fixture literals are not a tool's
    argument surface - the same rule the two shipped readers document.
    """
    try:
        names = sorted(os.listdir(root))
    except (IOError, OSError):
        return None
    return [name for name in names
            if name.endswith(".py") and not name.startswith("test_")]


def family_base(name, root):
    """The single callable that supersedes this per-round copy, or None.

    Derived from the filename family and the directory, never a whitelist:
    ``battery_followup_R2001.py`` is superseded only while
    ``battery_followup.py`` is present beside it. Delete the base and the row
    becomes debt again in the same breath.
    """
    stem, extension = os.path.splitext(name)
    if extension != ".py":
        return None
    match = ROUND_SUFFIX.match(stem)
    if match is None:
        return None
    base = match.group("base") + ".py"
    if base == name:
        return None
    if not os.path.isfile(os.path.join(root, base)):
        return None
    return base


def reason_of(law_verdict, wire_verdict, no_table):
    """Which shape of disagreement this row is, from the two verdicts alone."""
    if wire_verdict == no_table and law_verdict != no_table:
        return REASON_LAW_ONLY
    if law_verdict == no_table and wire_verdict != no_table:
        return REASON_WIRE_ONLY
    return REASON_TABLE_DIFFERS


def reported_flags(law_payload):
    """The flags the law itself reported, both one-sided lists, deduped."""
    flags = []
    for key in ("missing_in_table", "missing_in_parser"):
        for flag in law_payload[key]:
            if flag not in flags:
                flags.append(flag)
    return sorted(flags)


def row_for(name, law_payload, wire_payload, root, no_table):
    """One disagreement row: both verdicts, the reason, the law's own flags."""
    base = family_base(name, root)
    return {
        "tool": name,
        "law": law_payload["verdict"],
        "wire": wire_payload["verdict"],
        "reason": reason_of(law_payload["verdict"],
                            wire_payload["verdict"], no_table),
        "flags": reported_flags(law_payload),
        "superseded": base is not None,
    }


def audit(root=DEFAULT_ROOT):
    """Ask both shipped readers of every tool under root and publish the split.

    Returns None when the root itself cannot be read or holds no tool at all -
    a root that cannot be read is not a clean tree.
    """
    law = _law()
    wire = _wire()
    tools = list_tools(root)
    if tools is None or not tools:
        return None
    rows = []
    for name in tools:
        path = os.path.join(root, name)
        law_payload = law.audit(path)
        wire_payload = wire.audit(path)
        if law_payload is None or wire_payload is None:
            continue
        if _face(law_payload) == _face(wire_payload):
            continue
        rows.append(row_for(name, law_payload, wire_payload, root,
                            law.VERDICT_NO_TABLE))
    rows.sort(key=lambda row: row["tool"])
    superseded = len([row for row in rows if row["superseded"]])
    split = len(rows) - superseded
    return {
        "root": root,
        "scanned": len(tools),
        "rows": rows,
        "superseded": superseded,
        "split": split,
        "verdict": VERDICT_CLEAN if split == 0 else VERDICT_SPLIT,
    }


def render(payload, as_json):
    """One stable line, or byte-stable JSON over the pinned keys."""
    if as_json:
        body = dict((key, payload[key]) for key in JSON_KEYS)
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    names = [row["tool"] for row in payload["rows"] if not row["superseded"]]
    line = ("%s root=%s scanned=%d rows=%d superseded=%d split=%d "
             "verdict=%s" % (LABEL, payload["root"], payload["scanned"],
                             len(payload["rows"]), payload["superseded"],
                             payload["split"], payload["verdict"]))
    if names:
        line += " files=[%s]" % ",".join(names)
    return line


USAGE = ("usage: owner_table_reader_parity.py [ROOT] [--json]\n"
         "       owner_table_reader_parity.py --help\n")


def main(argv):
    args = list(argv[1:])
    as_json = False
    root = ""
    for token in args:
        if token == "--help":
            print(USAGE, end="", flush=True)
            return EXIT_CLEAN
        if token == "--json":
            as_json = True
            continue
        if token.startswith("-"):
            print("%s %s %s" % (LABEL, E_OTRP_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        if root:
            print("%s %s %s" % (LABEL, E_OTRP_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        root = token
    if not root:
        root = DEFAULT_ROOT
    if not os.path.isdir(root):
        print("%s %s %s" % (LABEL, E_OTRP_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    payload = audit(root)
    if payload is None:
        print("%s %s %s" % (LABEL, E_OTRP_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    print(render(payload, as_json), flush=True)
    if payload["verdict"] == VERDICT_CLEAN:
        return EXIT_CLEAN
    return EXIT_SPLIT


if __name__ == "__main__":
    sys.exit(main(sys.argv))