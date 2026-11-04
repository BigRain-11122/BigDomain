"""owner_table_triage_expiry (R2438; criteria AC-OTTE1..AC-OTTE6 pinned inside
the R2412 tech seed row of state/queue/tech.md:502 BEFORE this code).

Why this exists: owner_table_split_triage records since_round on every
acceptance, but nothing MEASURED ages it. An acceptance written at R2436 and
one accepted a year earlier read identically, so a never-expiring acceptance is
a silent waiver carrying a date nobody reads.

This module measures the age of every TRIAGED row against the current round:

  - age = current_round - since_round, printed in rounds;
  - age <= window reads FRESH, age > window reads AGED;
  - the row itself keeps status TRIAGED and still prints both verdicts, so an
    aged acceptance is a REVIEW DUE notice, not a silent un-triage;
  - an entry with no live row (the split face's STALE list) is carried as
    unageable and is never counted as aged or as clean;
  - a since_round later than the current round fails closed E_OTTE_FUTURE
    instead of printing a negative age.

Staleness is measured from the live reading every run, not stored, and the
round is supplied by the caller: this module reads no clock.

CLI:

    python owner_table_triage_expiry.py [ROOT] [--declaration PATH]
                                        [--round N] [--window N] [--json]
    python owner_table_triage_expiry.py --help

Exit codes: 0 EXPIRY-CLEAN, 2 EXPIRY-AGED, 3 root unreadable / declaration
missing or malformed / round or window missing or bad, 5 bad tool flags.

Stdlib only, ASCII source, zero network, no clock, read-only.
"""

import io
import json
import os
import sys

LABEL = "OWNER TABLE TRIAGE EXPIRY"

VERDICT_CLEAN = "EXPIRY-CLEAN"
VERDICT_AGED = "EXPIRY-AGED"

STATUS_TRIAGED = "TRIAGED"
STATUS_FRESH = "FRESH"
STATUS_AGED = "AGED"

UNAGEABLE_NO_LIVE = "no-live-disagreement"
UNAGEABLE_REASON_DIFFERS = "reason-differs"

E_OTTE_BAD_DECL = "E_OTTE_BAD_DECL"
E_OTTE_NO_DECL = "E_OTTE_NO_DECL"
E_OTTE_UNREADABLE = "E_OTTE_UNREADABLE"
E_OTTE_BAD_FLAG = "E_OTTE_BAD_FLAG"
E_OTTE_NO_ROUND = "E_OTTE_NO_ROUND"
E_OTTE_BAD_ROUND = "E_OTTE_BAD_ROUND"
E_OTTE_BAD_WINDOW = "E_OTTE_BAD_WINDOW"
E_OTTE_FUTURE = "E_OTTE_FUTURE"

EXIT_CLEAN = 0
EXIT_AGED = 2
EXIT_UNREADABLE = 3
EXIT_BAD_FLAG = 5

DEFAULT_WINDOW = 30

AGED_KEYS = ("tool", "law", "wire", "reason", "flags", "since_round",
             "age_rounds", "status", "age_status")
UNAGEABLE_KEYS = ("tool", "reason", "since_round", "why")
JSON_KEYS = ("root", "scanned", "round", "window", "rows", "triaged", "aged",
             "fresh", "unageable", "declaration", "verdict")

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DEFAULT_ROOT = HERE
DEFAULT_DECLARATION = os.path.join(REPO, "state", "owner_table_triage.json")


def _triage():
    """The shipped split/triage face, imported at CALL time (AC-OTTE1)."""
    import owner_table_split_triage
    return owner_table_split_triage


class ExpiryError(Exception):
    """An input that cannot be aged without inventing a fact."""

    def __init__(self, code, detail):
        Exception.__init__(self, detail)
        self.code = code
        self.detail = detail


def _as_round(value, code, where):
    """A round number, accepted as an int or as the R<digits> spelling."""
    if isinstance(value, bool):
        raise ExpiryError(code, "%s is not a round number" % where)
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if text[:1] in ("R", "r"):
            text = text[1:]
        if not text.isdigit():
            raise ExpiryError(code, "%s is not a round number" % where)
        number = int(text)
    else:
        raise ExpiryError(code, "%s is not a round number" % where)
    if number <= 0:
        raise ExpiryError(code, "%s is not a positive round" % where)
    return number


def _window(value):
    number = _as_round(value, E_OTTE_BAD_WINDOW, "window")
    return number


def age_rows(rows, entries, current_round, window):
    """Age every TRIAGED row against the current round.

    rows are the split face's rows (each carries tool, reason, status and both
    verdicts). entries are the validated declaration entries, keyed by the same
    tool AND reason the split face matched on. Returns (aged_rows, fresh,
    unageable) where aged_rows keeps every TRIAGED row with its measured age
    and status, fresh counts those still inside the window, and unageable
    carries the split face's STALE entries with their why.
    """
    index = {}
    for entry in entries:
        index.setdefault((entry["tool"], entry["reason"]), entry)
    out = []
    fresh = 0
    aged = 0
    matched = set()
    triage_status = _triage().STATUS_TRIAGED
    for row in rows:
        if row["status"] != triage_status:
            continue
        key = (row["tool"], row["reason"])
        entry = index.get(key)
        if entry is None:
            continue
        matched.add(key)
        since = entry["since_round"]
        age = current_round - since
        if age < 0:
            raise ExpiryError(
                E_OTTE_FUTURE,
                "%s since_round=%d is later than round=%d"
                % (row["tool"], since, current_round))
        age_status = STATUS_AGED if age > window else STATUS_FRESH
        if age_status == STATUS_AGED:
            aged += 1
        else:
            fresh += 1
        out.append({
            "tool": row["tool"],
            "law": row["law"],
            "wire": row["wire"],
            "reason": row["reason"],
            "flags": list(row["flags"]),
            "since_round": since,
            "age_rounds": age,
            "status": STATUS_TRIAGED,
            "age_status": age_status,
        })
    triage = _triage()
    live_tools = set()
    for row in rows:
        if row["status"] != triage.STATUS_SUPERSEDED:
            live_tools.add(row["tool"])
    unageable = []
    for entry in entries:
        key = (entry["tool"], entry["reason"])
        if key in matched:
            continue
        if entry["tool"] in live_tools:
            named = UNAGEABLE_REASON_DIFFERS
        else:
            named = UNAGEABLE_NO_LIVE
        unageable.append({
            "tool": entry["tool"],
            "reason": entry["reason"],
            "since_round": entry["since_round"],
            "why": named,
        })
    unageable.sort(key=lambda item: (item["tool"], item["since_round"]))
    return out, fresh, aged, unageable


def audit(root=DEFAULT_ROOT, declaration=None, current_round=None,
          window=DEFAULT_WINDOW):
    """Ask the shipped split/triage face, then age its TRIAGED rows.

    Returns None when the root cannot be read or holds no tool. A declaration
    that cannot be read raises the split face's DeclarationError; a missing
    round raises E_OTTE_NO_ROUND - this face never guesses a clock.
    """
    if current_round is None:
        raise ExpiryError(E_OTTE_NO_ROUND, "no current round was supplied")
    current = _as_round(current_round, E_OTTE_BAD_ROUND, "round")
    span = _window(window)
    triage = _triage()
    payload = triage.audit(root, declaration)
    if payload is None:
        return None
    if declaration:
        entries, label = triage.load_declaration(declaration)
    elif os.path.isfile(triage.DEFAULT_DECLARATION):
        entries, label = triage.load_declaration(triage.DEFAULT_DECLARATION)
    else:
        entries, label = [], "absent"
    rows, fresh, aged, unageable = age_rows(
        payload["rows"], entries, current, span)
    return {
        "root": payload["root"],
        "scanned": payload["scanned"],
        "round": current,
        "window": span,
        "rows": rows,
        "triaged": len(rows),
        "aged": aged,
        "fresh": fresh,
        "unageable": unageable,
        "declaration": label,
        "verdict": VERDICT_AGED if aged else VERDICT_CLEAN,
    }


def render(payload, as_json):
    """One stable line, or byte-stable JSON over the pinned keys."""
    if as_json:
        body = dict((key, payload[key]) for key in JSON_KEYS)
        return json.dumps(body, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=True)
    aged = ["%s(%d)" % (row["tool"], row["age_rounds"])
            for row in payload["rows"] if row["age_status"] == STATUS_AGED]
    fresh = ["%s(%d)" % (row["tool"], row["age_rounds"])
             for row in payload["rows"] if row["age_status"] == STATUS_FRESH]
    unageable = [item["tool"] for item in payload["unageable"]]
    line = ("%s root=%s scanned=%d round=%d window=%d triaged=%d aged=%d "
            "fresh=%d unageable=%d verdict=%s"
            % (LABEL, payload["root"], payload["scanned"], payload["round"],
               payload["window"], payload["triaged"], payload["aged"],
               payload["fresh"], len(payload["unageable"]),
               payload["verdict"]))
    if aged:
        line += " aged=[%s]" % ",".join(aged)
    if fresh:
        line += " fresh=[%s]" % ",".join(fresh)
    if unageable:
        line += " unageable=[%s]" % ",".join(unageable)
    return line


USAGE = ("usage: owner_table_triage_expiry.py [ROOT] [--declaration PATH] "
         "[--round N] [--window N] [--json]\n"
         "       owner_table_triage_expiry.py --help\n")


def main(argv):
    args = list(argv[1:])
    as_json = False
    root = ""
    declaration = ""
    current_round = None
    window = DEFAULT_WINDOW
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
        if token in ("--declaration", "--round", "--window"):
            if index + 1 >= len(args):
                print("%s %s %s" % (LABEL, E_OTTE_BAD_FLAG, token), flush=True)
                return EXIT_BAD_FLAG
            value = args[index + 1]
            if token == "--declaration":
                declaration = value
            elif token == "--round":
                try:
                    current_round = _as_round(value, E_OTTE_BAD_ROUND, token)
                except ExpiryError as error:
                    print("%s %s %s" % (LABEL, error.code, error.detail),
                          flush=True)
                    return EXIT_UNREADABLE
            else:
                try:
                    window = _window(value)
                except ExpiryError as error:
                    print("%s %s %s" % (LABEL, error.code, error.detail),
                          flush=True)
                    return EXIT_UNREADABLE
            index += 2
            continue
        if token.startswith("-"):
            print("%s %s %s" % (LABEL, E_OTTE_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        if root:
            print("%s %s %s" % (LABEL, E_OTTE_BAD_FLAG, token), flush=True)
            return EXIT_BAD_FLAG
        root = token
        index += 1
    if not root:
        root = DEFAULT_ROOT
    if not os.path.isdir(root):
        print("%s %s %s" % (LABEL, E_OTTE_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    triage = _triage()
    try:
        payload = audit(root, declaration, current_round, window)
    except ExpiryError as error:
        print("%s %s %s" % (LABEL, error.code, error.detail), flush=True)
        return EXIT_UNREADABLE
    except triage.DeclarationError as error:
        print("%s %s %s" % (LABEL, error.code, error.detail), flush=True)
        return EXIT_UNREADABLE
    if payload is None:
        print("%s %s %s" % (LABEL, E_OTTE_UNREADABLE, root), flush=True)
        return EXIT_UNREADABLE
    print(render(payload, as_json), flush=True)
    if payload["verdict"] == VERDICT_CLEAN:
        return EXIT_CLEAN
    return EXIT_AGED


if __name__ == "__main__":
    sys.exit(main(sys.argv))