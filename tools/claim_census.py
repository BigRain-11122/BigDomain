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

R3226: a count is not a name. `census(root, detail=[])` appends one named row
per contradicted claim - face, 1-based line, the number the sentence claims,
the file or ledger it points at, the number that source actually carries, and a
`why=` form. Nine of the ten live-tree contradictions measured this window were
dated snapshots (an old round's sentence saying `rows=0` while today's ledger
holds four), so the form is what lets a reader tell a historical record from a
sentence about now; the classification itself is untouched.

R3227: the same nine needed a number, not only a name, because a reader who
lowered `contradicted` from ten to one would delete them from the record. So
`historic` is published beside it - a SUB-count, never a reclassification:
every contradicted claim stays counted, and `historic` says how many of them
were true when written (the line carries a round tag older than the newest tag
any face carries, and the claim speaks about the live ledger). A citation that
disagrees with its own file was wrong when written, so it is never historic.
`contradicted - historic` is what is wrong about now.
"""

import io
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

FACES = (("board", os.path.join("src", "os", "backlog.md")),
         ("state", os.path.join("src", "os", "state.json")),
         ("export", os.path.join("docs", "status-export.json")))

# R3359 measured the loose form on the live tree: `rows=(\d+)` also matched the
# TAIL of a longer identifier, so `newest_rows=2`, `window_rows=5`,
# `last_stamp_rows=...` and `_newest_rows` were counted as claims about the
# ledger - 311 board tokens fell to 183 with a left boundary, and state 8 to 5.
# Those are different readings (a trend row's width, a series cut), so grading
# them here named a hole the reader never had. The token must start a word.
ROWS_RE = re.compile(r"(?<![A-Za-z0-9_])rows=(\d+)")
QA_REF_RE = re.compile(r"qa/([A-Za-z0-9._-]+\.(?:log|txt|json|md))")
LEDGER_ROW_RE = re.compile(r"LEDGER\s+\S+\s+rows=(\d+)")
ROUND_RE = re.compile(r"R(\d{3,4})")
LIVE_NAMES = ("state/qa_replacements.jsonl", "qa_replacements.jsonl")
DETAIL_LIMIT = 8


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
    """The token that would stand for this claim in another file.

    R3359: the same left boundary the claim reader uses, so a compound
    identifier in a cited file (`newest_rows=3`) cannot capture a genuine
    `rows=3` sentence - the two sides must agree about what a token is.
    """
    if "LEDGER" in line:
        return re.compile(r"LEDGER\s+\S+\s+rows=%d\b" % number)
    return re.compile(r"(?<![A-Za-z0-9_])rows=%d\b" % number)


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


def _newest_tag(texts):
    """The newest round tag any face carries - a reading, never a constant."""
    best = 0
    for text in texts:
        for raw in ROUND_RE.findall(text):
            best = max(best, int(raw))
    return best


def _is_historic(line, reading, newest):
    """A contradicted claim that was true when it was written (R3227).

    Only a claim about the live ledger can be a snapshot: its own line carries
    a round tag, and that tag is older than the newest tag the three faces
    carry. A citation that disagrees with the file it names was wrong when it
    was written, so it stays among what is wrong about now.
    """
    if reading["status"] != "contradicted" or reading["source"] != "live":
        return False
    tags = [int(raw) for raw in ROUND_RE.findall(line)]
    return bool(tags) and max(tags) < newest


def _named(root, face, lineno, line, reading, live_rows, newest):
    """One contradicted claim, addressed and sourced (R3226)."""
    source = reading["source"]
    if source == "live":
        src_rows = [live_rows]
        label = "live"
        why = ("live-snapshot" if _is_historic(line, reading, newest)
               else "live-now")
    else:
        body = _read(os.path.join(root, "qa", source))
        src_rows = [int(raw) for raw in LEDGER_ROW_RE.findall(body)]
        label = "qa/" + source
        why = "evidence-differs" if src_rows else "evidence-no-ledger-row"
    return {"face": face, "line": lineno, "rows": reading["rows"],
            "source": label, "source_rows": src_rows, "why": why}


def census(root=None, detail=None, export_text=None):
    """Classify every written claim of the three faces. Read-only.

    `detail`, when a list is passed, receives one named row per contradicted
    claim. The result dict is unchanged, so a caller that only wants the counts
    (the closeout gate) keeps exactly the shape it had.

    `export_text` (AC-SXFB39, R3383) answers the census over a CANDIDATE
    document instead of the one on disk. The export face carries `rows=` tokens
    inside its own prose rows (`latest_artifact`, `next_milestone`), so the
    writer that edits those rows changes the very number it publishes; the
    reader must be able to ask about the text that will land, not the text
    that is there now. Absent, the disk read and every existing caller are
    untouched.
    """
    root = ROOT if root is None else root
    import sys
    sys.path.insert(0, BASE)
    import qa_log as QL

    report = QL.ledger_report(os.path.join(root, "state", QL.LEDGER_NAME),
                              evidence_dir=os.path.join(root, "qa"))
    live_rows = report["rows"]
    result = {"claimed": 0, "captured": 0, "contradicted": 0, "uncaptured": 0,
              "historic": 0, "rows": live_rows,
              "present": bool(report["present"]), "faces": {}}
    faces = []
    for face, rel in FACES:
        if face == "export" and export_text is not None:
            faces.append((face, export_text))
            continue
        path = os.path.join(root, rel)
        text = _read(path) if os.path.isfile(path) else None
        faces.append((face, text))
    newest = _newest_tag([text for _face, text in faces if text is not None])
    for face, text in faces:
        if text is None:
            result["faces"][face] = {"present": False, "claimed": 0}
            continue
        claimed = 0
        for lineno, line in enumerate(text.split("\n"), 1):
            for reading in classify(root, line, live_rows):
                claimed += 1
                result[reading["status"]] += 1
                if reading["status"] != "contradicted":
                    continue
                if _is_historic(line, reading, newest):
                    result["historic"] += 1
                if detail is not None:
                    detail.append(_named(root, face, lineno, line, reading,
                                         live_rows, newest))
        result["faces"][face] = {"present": True, "claimed": claimed}
        result["claimed"] += claimed
    return result


def detail_row(item):
    """One line a reader can act on: where the sentence is and what disagrees."""
    return ("CLAIM %s:%d rows=%d source=%s source_rows=%s why=%s"
            % (item["face"], item["line"], item["rows"], item["source"],
               ",".join(str(n) for n in item["source_rows"]) or "none",
               item["why"]))


def detail_lines(items, limit=DETAIL_LIMIT):
    """Named rows, capped, with the remainder counted rather than dropped."""
    limit = max(0, limit)
    out = [detail_row(item) for item in items[:limit]]
    if len(items) > limit:
        out.append("+%d more" % (len(items) - limit))
    return out


def census_row(result):
    """One line: the three readings, the historic sub-count, the live count."""
    return ("CLAIMS captured=%d uncaptured=%d contradicted=%d historic=%d "
            "rows=%d present=%s"
            % (result["captured"], result["uncaptured"],
               result["contradicted"], result["historic"], result["rows"],
               "true" if result["present"] else "false"))


def _main(argv):
    args = argv[1:]
    unknown = [arg for arg in args if arg != "--all"]
    if unknown:
        import sys
        sys.stdout.write("usage: claim_census.py [--all]\n")
        return 2
    named = []
    result = census(detail=named)
    print(census_row(result))
    limit = len(named) if "--all" in args else DETAIL_LIMIT
    for line in detail_lines(named, limit):
        print(line)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_main(sys.argv))
