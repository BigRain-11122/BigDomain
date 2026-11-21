"""Read the `rows=<n>` numbers this company writes about its own ledger (R3225).

WHY (measured this window, qa/probe-R3225.log): the board, the state log and the
export together carry 307 `rows=<n>` tokens and 21 `LEDGER ... rows=N` claims,
and nothing ever read one of them back. Five of the seven claims that carry a
round tag disagree with the ledger as that round's own commit recorded it - a
handwritten number wearing the clothes of a measurement. `qa_log.ledger_report`
answers "what does the ledger hold now"; this face answers the other question:
"what did WE SAY it holds, and what can speak for that number".

Three readings per claim, never a verdict:

  captured      a landed file this very line names carries the same token
                (or the line speaks about the live ledger and agrees with it);
  contradicted  a landed file this line names carries the same SHAPE with a
                different number, or the line speaks about the live ledger and
                the number is not the ledger's;
  uncaptured    nothing the line names carries that shape, so the number is
                prose - named, never deleted and never counted as a measurement.

The live ledger is asked through `qa_log.ledger_report` and nothing else: a
second parser here would let the reader and the writer disagree about what a
row is.
"""

import io
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

FACES = (("board", os.path.join("src", "os", "backlog.md")),
         ("state", os.path.join("src", "os", "state.json")),
         ("export", os.path.join("docs", "status-export.json")))

ROWS_RE = re.compile(r"rows=(\d+)")
QA_REF_RE = re.compile(r"qa/([A-Za-z0-9._-]+\.(?:log|txt|json|md))")
LEDGER_ROW_RE = re.compile(r"LEDGER\s+\S+\s+rows=(\d+)")
LIVE_NAMES = ("state/qa_replacements.jsonl", "qa_replacements.jsonl")


def _read(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def _evidence(root, line):
    """The landed files this line names, with their text. Unlanded names are
    dropped rather than trusted: a citation to nothing cannot speak for a
    number."""
    out = []
    seen = set()
    for name in QA_REF_RE.findall(line):
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(root, "qa", name)
        if os.path.isfile(path):
            out.append((name, _read(path)))
    return out


def _same_shape(line, number):
    """The token that would stand for this claim in another file."""
    if "LEDGER" in line:
        return re.compile(r"LEDGER\s+\S+\s+rows=%d\b" % number)
    return re.compile(r"rows=%d\b" % number)


def classify(root, line, live_rows):
    """One reading per `rows=<n>` token on this line, in order."""
    numbers = ROWS_RE.findall(line)
    if not numbers:
        return []
    evidence = _evidence(root, line)
    names_live = any(name in line for name in LIVE_NAMES)
    out = []
    for raw in numbers:
        number = int(raw)
        same = _same_shape(line, number)
        if evidence:
            if any(same.search(body) for _name, body in evidence):
                status, source = "captured", evidence[0][0]
            elif any(LEDGER_ROW_RE.search(body) for _name, body in evidence):
                status, source = "contradicted", evidence[0][0]
            else:
                status, source = "uncaptured", ""
        elif names_live:
            status = "captured" if number == live_rows else "contradicted"
            source = "live"
        else:
            status, source = "uncaptured", ""
        out.append({"rows": number, "status": status, "source": source})
    return out


def census(root=None):
    """Classify every written claim of the three faces. Read-only."""
    root = ROOT if root is None else root
    import sys
    sys.path.insert(0, BASE)
    import qa_log as QL

    report = QL.ledger_report(os.path.join(root, "state", QL.LEDGER_NAME),
                              evidence_dir=os.path.join(root, "qa"))
    live_rows = report["rows"]
    result = {"claimed": 0, "captured": 0, "contradicted": 0, "uncaptured": 0,
              "rows": live_rows, "present": bool(report["present"]),
              "faces": {}}
    for face, rel in FACES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            result["faces"][face] = {"present": False, "claimed": 0}
            continue
        claimed = 0
        for line in _read(path).split("\n"):
            for reading in classify(root, line, live_rows):
                claimed += 1
                result[reading["status"]] += 1
        result["faces"][face] = {"present": True, "claimed": claimed}
        result["claimed"] += claimed
    return result


def census_row(result):
    """One line: the three readings, the live count, and whether it exists."""
    return ("CLAIMS captured=%d uncaptured=%d contradicted=%d rows=%d present=%s"
            % (result["captured"], result["uncaptured"],
               result["contradicted"], result["rows"],
               "true" if result["present"] else "false"))


def _main(argv):
    if len(argv) > 1:
        import sys
        sys.stdout.write("usage: claim_census.py\n")
        return 2
    print(census_row(census()))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv))
