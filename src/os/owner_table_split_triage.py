"""owner_table_split_triage (R2436; criteria AC-OTST1..AC-OTST6 pinned inside
the R2412 tech seed row of state/queue/tech.md:500 BEFORE this code).

Why this exists: owner_table_reader_parity publishes the split between the two
shipped readers, and every round it re-reports the SAME known law false
positives. There is no way to say "reviewed and accepted", so the debt count
can never reach zero and the reason a row is still printed lives only in a
docstring. Measured at this window over the real src/os (1067 tools):

    rows=41 superseded=35 split=6

with the six live rows being battery_followup_help_wire, evidence_R2372,
matrix_stamp_compare, r2140_fold, retry_naming and run_identity - each one a
module-level vocabulary the law reads as an argument table while the module
never uses it as argv (measured by opening each file, not assumed).

This module adds the missing triage declaration:

  - a declaration is a dated one-entry-per-tool list of rows shaped exactly
    {tool, reason, since_round};
  - an entry that matches a LIVE disagreement row (same tool AND same reason)
    moves that row out of the split count into TRIAGED, while the row is still
    printed with both verdicts and the law's own flags;
  - an entry that matches nothing is STALE and is printed with the reason it
    is stale ("no-live-disagreement" or "reason-differs"), never silently
    kept and never counted as clean by accident;
  - a tool that has become PARITY-AGREES on both sides is therefore STALE,
    because there is no live row to match at all.

Staleness is measured from the live reading every run, not assumed from the
declaration.

CLI:

    python owner_table_split_triage.py [ROOT] [--declaration PATH] [--json]
    python owner_table_split_triage.py --help

Exit codes: 0 TRIAGE-CLEAN, 2 TRIAGE-SPLIT, 3 root unreadable or the
declaration is missing (when named) or malformed, 5 bad tool flags.

Stdlib only, ASCII source, zero network, no clock, read-only: this module
opens the declaration for reading and creates nothing.

Honest limit stated rather than hidden: a triage entry suppresses ONE tool at
the reason it names. If that tool's own reason changes (for example the law
stops reading a vocabulary and starts reading a real table), the entry reads
reason-differs and the row returns to the split in the same run.
"""

import io
import json
import os
import sys

LABEL = "OWNER TABLE SPLIT TRIAGE"

VERDICT_CLEAN = "TRIAGE-CLEAN"
VERDICT_SPLIT = "TRIAGE-SPLIT"

STATUS_TRIAGED = "TRIAGED"
STATUS_SPLIT = "SPLIT"
STATUS_SUPERSEDED = "SUPERSEDED"

STALE_NO_LIVE = "no-live-disagreement"
STALE_REASON_DIFFERS = "reason-differs"

E_OTST_BAD_DECL = "E_OTST_BAD_DECL"
E_OTST_NO_DECL = "E_OTST_NO_DECL"
E_OTST_UNREADABLE = "E_OTST_UNREADABLE"
E_OTST_BAD_FLAG = "E_OTST_BAD_FLAG"

EXIT_CLEAN = 0
EXIT_SPLIT = 2
EXIT_UNREADABLE = 3
EXIT_BAD_FLAG = 5

ENTRY_KEYS = ("tool", "reason", "since_round")
ROW_KEYS = ("tool", "law", "wire", "reason", "flags", "status")
STALE_KEYS = ("tool", "reason", "since_round", "why")
JSON_KEYS = ("root", "scanned", "rows", "superseded", "split", "triaged",
             "stale", "declaration", "verdict")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DEFAULT_ROOT = HERE
DEFAULT_DECLARATION = os.path.join(REPO, "state", "owner_table_triage.json")


def _parity():
    """The shipped split face, imported at CALL time (AC-OTST2/AC-OTST3)."""
    import owner_table_reader_parity
    return owner_table_reader_parity


class DeclarationError(Exception):
    """A declaration that cannot be read as the pinned row shape."""

    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def _entry(raw, where):
    """One declaration row, validated to the pinned shape exactly."""
    if not isinstance(raw, dict):
        raise DeclarationError(E_OTST_BAD_DECL, "%s is not an object" % where)
    keys = set(raw.keys())
    if keys != set(ENTRY_KEYS):
        raise DeclarationError(
            E_OTST_BAD_DECL,
            "%s keys %s are not exactly %s"
            % (where, sorted(keys), list(ENTRY_KEYS)))
    tool = raw["tool"]
    reason = raw["reason"]
    since = raw["since_round"]
    if not isinstance(tool, str) or not tool:
        raise DeclarationError(E_OTST_BAD_DECL, "%s tool is empty" % where)
    if not isinstance(reason, str) or not reason.strip():
        raise DeclarationError(E_OTST_BAD_DECL, "%s reason is empty" % where)
    if isinstance(since, bool) or not isinstance(since, int) or since <= 0:
        raise DeclarationError(E_OTST_BAD_DECL,
                               "%s since_round is not a round number" % where)
    return {"tool": tool, "reason": reason, "since_round": since}


def load_declaration(path):
    """Read and validate the declaration; returns (entries, label).

    A path that is None or empty means "no declaration was named": the caller
    then reads DEFAULT_DECLARATION if it exists, and otherwise triages
    nothing. A named path that does not exist is fail-closed.
    """
    if not path:
        path = DEFAULT_DECLARATION
    if not os.path.isfile(path):
        raise DeclarationError(E_OTST_NO_DECL, path)
    try:
        with io.open(path, "r", encoding="utf-8-sig", newline="") as handle:
            text = handle.read()
        data = json.loads(text)
    except (IOError, OSError, ValueError) as error:
        raise DeclarationError(E_OTST_BAD_DECL, "%s: %s" % (path, error))
    if isinstance(data, dict):
        if "entries" not in data:
            raise DeclarationError(E_OTST_BAD_DECL,
                                   "%s has no entries list" % path)
        raw_entries = data["entries"]
    elif isinstance(data, list):
        raw_entries = data
    else:
        raise DeclarationError(E_OTST_BAD_DECL,
                               "%s is not a list or object" % path)
    if not isinstance(raw_entries, list):
        raise DeclarationError(E_OTST_BAD_DECL,
                               "%s entries is not a list" % path)
    entries = [_entry(raw, "%s entries[%d]" % (path, index))
               for index, raw in enumerate(raw_entries)]
    return entries, path


def _entry_index(entries):
    """tool -> list of entries, so one tool may be triaged more than once."""
    index = {}
    for entry in entries:
        index.setdefault(entry["tool"], []).append(entry)
    return index


def triage_rows(rows, entries):
    """Split every LIVE row into TRIAGED or SPLIT and age every declaration row.

    rows are the disagreement rows of owner_table_reader_parity. Only rows that
    are not superseded are triageable: a superseded row is already out of the
    debt count and its declaration would only ever read stale.
    """
    index = _entry_index(entries)
    matched = set()
    out_rows = []
    stale = []
    triaged = 0
    split = 0
    for row in rows:
        status = STATUS_SPLIT
        reason = row["reason"]
        if row["superseded"]:
            status = STATUS_SUPERSEDED
        else:
            for entry in index.get(row["tool"], []):
                if entry["reason"] == reason:
                    matched.add(id(entry))
                    status = STATUS_TRIAGED
                    break
        if status == STATUS_TRIAGED:
            triaged += 1
        elif status == STATUS_SPLIT:
            split += 1
        out_rows.append({
            "tool": row["tool"],
            "law": row["law"],
            "wire": row["wire"],
            "reason": reason,
            "flags": list(row["flags"]),
            "status": status,
        })
    live_tools = set(row["tool"] for row in rows if not row["superseded"])
    for tool in sorted(index.keys()):
        for entry in index[tool]:
            if id(entry) in matched:
                continue
            if tool not in live_tools:
                why = STALE_NO_LIVE
            else:
                why = STALE_REASON_DIFFERS
            stale.append({
                "tool": tool,
                "reason": entry["reason"],
                "since_round": entry["since_round"],
                "why": why,
            })
    stale.sort(key=lambda item: (item["tool"], item["since_round"]))
    return out_rows, triaged, split, stale


def audit(root=DEFAULT_ROOT, declaration=None):
    """Ask the shipped split face, then age the declaration against it.

    Returns None when the root cannot be read or holds no tool. A declaration
    that cannot be read raises DeclarationError so the CLI can fail closed
    instead of silently reporting a tree as clean.
    """
    parity = _parity()
    payload = parity.audit(root)
    if payload is None:
        return None
    if declaration:
        path = declaration
    elif os.path.isfile(DEFAULT_DECLARATION):
        path = DEFAULT_DECLARATION
    else:
        path = ""
    if path:
        entries, label = load_declaration(path)
    else:
        entries, label = [], "absent"
    rows, triaged, split, stale = triage_rows(payload["rows"], entries)
    return {
        "root": payload["root"],
        "scanned": payload["scanned"],
        "rows": rows,
        "superseded": payload["superseded"],
        "split": split,
        "triaged": triaged,
        "stale": stale,
        "declaration": label,
        "verdict": VERDICT_CLEAN if split == 0 else VERDICT_SPLIT,
    }


def render(payload, as_json):
    """One stable line, or byte-stable JSON over the pinned keys."""
    if as_json:
        body = dict((key, payload[key]) for key in JSON_KEYS)
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    names = [row["tool"] for row in payload["rows"]
             if row["status"] == STATUS_SPLIT]
    stale = [item["tool"] for item in payload["stale"]]
    line = ("%s root=%s scanned=%d rows=%d superseded=%d split=%d "
            "triaged=%d stale=%d verdict=%s"
            % (LABEL, payload["root"], payload["scanned"],
               len(payload["rows"]), payload["superseded"], payload["split"],
               payload["triaged"], len(payload["stale"]),
               payload["verdict"]))
    if names:
        line += " files=[%s]" % ",".join(names)
    if stale:
        line += " stale=[%s]" % ",".join(stale)
    return line


USAGE = ("usage: owner_table_split_triage.py [ROOT] [--declaration PATH] "
         "[--json]\n"
         "       owner_table_split_triage.py --help\n")


def main(argv):
    args = list(argv[1:])
    as_json = False
    root = ""
    declaration = ""
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--help":
            print(USAGE, end="", flush=True)
            return EXIT_CLEAN
        if token == "--json":
            as_json = True
            index += 1
            continue
        if token == "--declaration":
            if index + 1 >= len(args):
                print("%s %s %s" % (LABEL, E_OTST_BAD_FLAG, token), flush=True)
                return EXIT_BAD_FLAG
            declaration = args[index + 1]
            index += 2
            continue
        if token.startswith("-"):
            print("%s %s %s" % (LABEL, E_OTST_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        if root:
            print("%s %s %s" % (LABEL, E_OTST_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        root = token
        index += 1
    if not root:
        root = DEFAULT_ROOT
    if not os.path.isdir(root):
        print("%s %s %s" % (LABEL, E_OTST_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    try:
        payload = audit(root, declaration)
    except DeclarationError as error:
        print("%s %s %s" % (LABEL, error.code, error.detail), flush=True)
        return EXIT_UNREADABLE
    if payload is None:
        print("%s %s %s" % (LABEL, E_OTST_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    print(render(payload, as_json), flush=True)
    if payload["verdict"] == VERDICT_CLEAN:
        return EXIT_CLEAN
    return EXIT_SPLIT


if __name__ == "__main__":
    sys.exit(main(sys.argv))