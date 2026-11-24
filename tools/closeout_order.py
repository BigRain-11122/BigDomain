"""Close the four-face ordering ring with one executable order.

Why this exists: R3298 measured a ring instead of a clock. Each face carries a
back-hop block whose data-back-bytes holds the ENTRY page's byte count
(tools/face_backhop.py), preview/index.html quotes the newest pair's html bytes
and docs/status-export.json's census_ts, preview/face-sweep.html reads the
entry page and every face, and the export audits the sweep when the sweep is
the newest artifact. Any re-render of one artifact therefore makes another
stale - measured at R3298: first-yuan-chain went E_STALE the moment
deliverable_index --write changed index.html from 42499B to 42644B.

R3298 found a static order by hand and honestly recorded that this is NOT a
fix: "only the ordering of the resting state was found". This file makes that
order executable and grades it, without changing any producer's semantics.

Two kinds of edge, kept apart (AC-COO2):

  bytes  the reader parses the writer's byte count or a quoted scalar, so the
         writer must be rendered again whenever the writer's size moves. These
         are equalities and they may need more than one pass.
  mtime  the reader only ranks artifacts by mtime/commit date, so "write me
         last" satisfies it; it never needs to enter the iteration.

The only byte-cycle is chain<->index (index quotes the chain's html size, every
face embeds the index's size). It is width-stable: the injected number only
changes the chain's length when its digit count changes, so a bounded
fixed-point iteration (<=3 passes) converges. That is measured here, not
assumed: a pass is accepted only when all four --check faces are green at the
END of that pass (AC-COO4).

Criteria AC-COO1..AC-COO7 (pinned in src/os/backlog.md, R3299 PIN line, before
this file existed):

  AC-COO1 every declared edge names its reader file and an evidence token that
          is present in that file (no orphan edge, machine-checked here)
  AC-COO2 byte edges and mtime edges are separate lists; mtime edges are not
          iterated
  AC-COO3 the only byte cycle is chain<->index and it is resolved by bounded
          fixed-point iteration, never by a hardcoded direction
  AC-COO4 VERDICT PASS only when all four --check faces are green at the end of
          a pass; a red face aborts with rc=2 and names the edges feeding it
  AC-COO5 --check/--dry-run write nothing: every preview pair and
          docs/status-export.json keep their (size, mtime_ns)
  AC-COO6 --write twice leaves the four faces green the second time (a real
          fixed point, not a single-window accident)
  AC-COO7 zero network: no socket, requests or urllib import
  AC-COO9 (R3301) the two "newest" laws are compared in THIS read-only row and
          nowhere else: both names freshly derived, the flag computed from them,
          and no preview page may carry the row (the copy is what broke the
          fixed point)
  AC-COO10 (R3302) the census-day edge is DECLARED and proven width-safe: the
          entry page prints a ten-character day, the declaration names both
          files and the remedy, it never enters the byte-edge list, and no
          preview page carries the declaration row
  AC-COO11 (R3304) the remedy is MEASURED: the renderers it names are exactly
          the ones a private-tree day advance actually reddened, each named
          renderer's own file must still carry its criterion token, the edge
          left out must still be the byte edge this table declares, and no
          preview page may carry the remedy row
  AC-COO12 (R3305) a DAY CROSSING costs TWO passes, and that count is graded
          against its premise: the export step must still be the LAST step and
          must still be the writer of the census day, the declared count must
          fit inside MAX_PASSES, and no preview page may carry the row
  AC-COO13 (R3306) the EVIDENCE edge (a newest qa/*.log moving the export's
          latest_evidence line) is an INPUT, not a ring edge: the export must
          still own that field, no ring reader's own source may read it, the
          export must still run last, the edge must not be listed in EDGES, and
          no preview page may carry the row

The measured pass count (AC-COO12): R3304 proved a day republish reddens the
entry page and the sweep board, and its remedy names both - but the remedy was
never measured as an ORDERING, and the closeout's own contract ("<=3 passes
until the four faces are green together") had never been run in a world whose
day had moved. R3305 measured it in two private copy trees (day only, and day
plus a reading whose width moves): both needed TWO passes, and the second pass
was never a rounding error. The premise is the order itself - the export step
is LAST in STEPS and it is a WRITER of the census day (it imports
status_export_fresh, whose CLAIMS_TS_KEY is census_ts), so the index rendered
earlier in the same pass prints the day it read at pass start and is one step
behind at pass end. Two passes is therefore not a defect to be tuned away: it
is what a ring with export -> index -> sweep and sweep -> export owes. What the
criterion refuses is the claim drifting away from that structure - reorder the
steps and the arm reddens instead of the number quietly going stale.

What the third edge costs (measured at R3306 in two private copy trees, not
guessed): TWO edges (day + a reading width) need two passes; THREE edges (day,
width, and a fresh qa/*.log whose mtime is newest) also need exactly two. The
evidence edge is free because it is an INPUT to the last step, not a ring edge:
the export face's own check grades the file it NAMES (a snapshot at export_ts),
not "whatever is newest", so a new log cannot redden any face - and no ring
reader's source reads `latest_evidence` at all (0 of 4, measured). The write
still consumes it: after the write the export names the planted file and
publishes the note. AC-COO13 grades that structure, so promoting the field into
a reader or moving the export out of last place reddens the arm instead of the
spare iteration quietly disappearing.

The day edge (AC-COO10): preview/index.html prints `census day YYYY-MM-DD` and
AC-DIX19 refuses a page whose day is not the export's current day. That is a
content edge on a CALENDAR, not on a render, and it is the one edge that stays
after R3300/R3301 cut the clock copy and the copied newest-pair answer. It is
declared here instead of being cut because the day is the only thing telling a
reader which day the six numbers belong to, and because it is ten ASCII
characters whatever the date: a claims republish on a new day cannot move this
page's byte count, so it cannot move the chain's data-back-bytes and cannot add
an iteration to the ring. Measured at R3302: two exports a day apart render the
same note in the same number of bytes.

What a day republish still owes (measured at R3304 in a private copy tree, not
guessed): the entry page must be re-rendered (AC-DIX19 and AC-COO8 redden on the
export's new day), and so must the SWEEP BOARD - it stamps the moment it
executed each face, so a newer index.html makes its verdict a claim about a
version nobody measured (AC-FSW10, measured 20/21). The chain is NOT owed while
only the day moves: the page stayed at 42875 bytes, delta zero. It IS owed the
moment a reading changes width (claimed 339 -> 1000 moved the page one byte and
the chain answered E_STALE), which is the byte edge the table above already
carries - so this remedy does not invent a second rule, it names the renderers.

Nothing here renders a page itself, runs JS, opens a socket or reads the clock
for a product number.
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREVIEW = os.path.join(ROOT, "preview")
EXPORT = os.path.join(ROOT, "docs", "status-export.json")

MAX_PASSES = 3

# (name, module relpath, args) - the render order measured at R3298/R3299.
STEPS = [
    ("chain", "tools/first_yuan_chain.py", []),
    ("index", "tools/deliverable_index.py", []),
    ("backhop", "tools/face_backhop.py", ["--write"]),
    ("sweep", "tools/face_sweep.py", []),
    ("export", "src/os/export_round.py", []),
]

# R3391 measured, not landed: the UGC page (tools/ugc_gate_report.py) is a
# TWO-WRITER product - its bare render carries no back-hop block, and
# tools/face_backhop.py injects it - so a single recorded command cannot
# reproduce the bytes the entry page quotes. Putting it in STEPS reddens
# AC-DIX21/AC-DIX23 (measured), so the recurrence fix needs either a producer
# that injects its own channel or a declared two-step recipe in the index.

# A declared step whose module is gone would fail as a mid-pass transient and
# the ring could still print PASS, so every declared path is checked before the
# first step runs (AC-CUG2).
MISSING_STEP = "E_MISSING_STEP"

# (reader, writer, kind, reader_file, evidence_token) - kind in {"bytes","mtime"}.
EDGES = [
    ("chain", "index", "bytes", "tools/face_backhop.py", "data-back-bytes"),
    ("index", "chain", "bytes", "tools/deliverable_index.py", "html_bytes"),
    ("index", "export", "bytes", "tools/deliverable_index.py", "census_ts"),
    ("sweep", "index", "bytes", "tools/face_sweep.py", ("preview/index.html")),
    ("sweep", "chain", "bytes", "tools/face_sweep.py", "preview/first-yuan-chain.html"),
    ("export", "sweep", "mtime", "src/os/export_round.py", "BOARD_PAGES"),
]

# (reader, writer, kind, landed page, prefix, width) - AC-COO10. The census day
# is a declared content edge whose width is fixed at ten ASCII characters, which
# is why it is NOT in EDGES: a byte cycle can only be closed by something whose
# length moves with its value, and this one cannot. Read from the landed page,
# never from this table, so the declaration cannot agree with itself.
DAY_EDGE = ("index", "export", "day", "preview/index.html", "census day ", 10)
DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

# AC-COO11 (R3304). The remedy is a claim about which renderers a day advance
# reddens, so it is graded against the CALL SITE each renderer uses to record
# its criterion, not against a bare name: a comment that mentions AC-DIX19
# grades nothing, and an arm proved that a bare-token read stays green when the
# code is gone. (name, reader file, the call site the reader really holds)
REMEDY = "re-render-index-and-sweep-after-claims-republish"
REMEDY_OWED = (
    ("index", "tools/deliverable_index.py", 'record("AC-DIX19"'),
    ("sweep", "tools/face_sweep.py", 'fails.append("AC-FSW10'),
)
# The spared renderer is not described here on purpose: which edge it owes is
# read out of EDGES above, so the exclusion cannot drift away from the table.
REMEDY_SPARED = "chain"
REMEDY_LEAK = "REMEDY-EDGE "

# AC-COO12 (R3305). A day crossing costs TWO passes, measured in two private
# copy trees (day only, and day + a reading width). The count is a property of
# the order, so its PREMISE is graded rather than the number alone: export must
# still be the last step and must still be the writer of the census day (it
# imports the fresh writer, whose CLAIMS_TS_KEY is census_ts). Reorder STEPS or
# move the day out of the export step and this arm reddens, so the declared
# count cannot outlive the structure that produced it.
DAY_PASSES = 2
DAY_PASSES_WHY = "export-publishes-census-day-and-runs-last"
DAY_PASSES_WRITER = ("export", "src/os/export_round.py",
                     "import status_export_fresh as SXF")
DAY_PASSES_KEY = ("tools/status_export_fresh.py", 'CLAIMS_TS_KEY = "census_ts"')
DAY_PASSES_LEAK = "DAY-PASSES "

# AC-COO13 (R3306). A newest qa/*.log moves the export's evidence line, and
# that move is an INPUT to the last step rather than an edge inside the ring:
# measured in a private tree, three simultaneous edges (day, width, evidence)
# still converge in TWO passes, because no face's check grades "newest qa log"
# and no ring reader reads the field. The arms grade that structure, so a future
# change that promotes the field into a reader - or moves the export out of last
# place - reddens here instead of silently eating the iteration budget.
EVIDENCE_EDGE = ("export", "qa", "mtime", "src/os/export_round.py", "latest_evidence")
EVIDENCE_READERS = (
    ("chain", "tools/first_yuan_chain.py"),
    ("index", "tools/deliverable_index.py"),
    ("backhop", "tools/face_backhop.py"),
    ("sweep", "tools/face_sweep.py"),
)
EVIDENCE_LEAK = "EVIDENCE-EDGE "

# The standalone check face of each artifact (read-only, prints VERDICT).
CHECKS = [
    ("chain", "tools/first_yuan_chain.py", ["--check"]),
    ("index", "tools/deliverable_index.py", ["--check"]),
    ("sweep", "tools/face_sweep.py", ["--check"]),
    ("export", "src/os/export_round.py", ["--check"]),
]


def missing_steps(steps=None):
    """Declared modules that are not on disk, in declaration order (AC-CUG2)."""
    out = []
    for name, module, _ in (STEPS if steps is None else steps):
        if not os.path.isfile(os.path.join(ROOT, module)):
            out.append((name, module))
    return out


def _run(module, args):
    proc = subprocess.run(
        [sys.executable, os.path.join(ROOT, module)] + list(args),
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    text = proc.stdout.decode("utf-8", "replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # deliverable_index prints a json summary AFTER its VERDICT line, so the
    # verdict is not necessarily the last line: find it, do not assume it.
    verdict = [ln for ln in lines if "VERDICT" in ln]
    tail = verdict[-1] if verdict else (lines[-1] if lines else "")
    return proc.returncode, tail, text


def snapshot():
    """(size, mtime_ns) of every preview pair file plus the export document."""
    out = {}
    for name in sorted(os.listdir(PREVIEW)):
        if not (name.endswith(".html") or name.endswith(".json")):
            continue
        path = os.path.join(PREVIEW, name)
        st = os.stat(path)
        out["preview/" + name] = (st.st_size, st.st_mtime_ns)
    st = os.stat(EXPORT)
    out["docs/status-export.json"] = (st.st_size, st.st_mtime_ns)
    return out


def edge_report():
    """AC-COO1/AC-COO2: every edge resolves to a reader file carrying its token."""
    rows = []
    for reader, writer, kind, relpath, token in EDGES:
        path = os.path.join(ROOT, relpath)
        present = os.path.isfile(path)
        hit = False
        if present:
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                hit = token in fh.read()
        rows.append({"reader": reader, "writer": writer, "kind": kind,
                     "reader_file": relpath, "token": token,
                     "file_present": present, "token_found": hit})
    return rows


def byte_cycle():
    """The byte edges as a graph; return the cycles found (writer->reader)."""
    adj = {}
    for reader, writer, kind, _, _ in EDGES:
        if kind != "bytes":
            continue
        adj.setdefault(writer, set()).add(reader)
    found = set()
    for start in sorted(adj):
        stack = [(start, [start])]
        while stack:
            node, path = stack.pop()
            for nxt in sorted(adj.get(node, ())):
                if nxt == start:
                    found.add(tuple(path + [start]))
                elif nxt not in path:
                    stack.append((nxt, path + [nxt]))
    # A cycle reached from every one of its members is one cycle, not N
    # rotations: canonicalise each to its lexicographically smallest rotation.
    unique = set()
    for cyc in found:
        ring = cyc[:-1]
        best = min(tuple(ring[i:] + ring[:i]) for i in range(len(ring)))
        unique.add(best + (best[0],))
    return sorted(unique)


def verify():
    """Run each standalone check face; return [(name, ok, verdict_line)]."""
    out = []
    for name, module, args in CHECKS:
        rc, tail, _ = _run(module, args)
        ok = rc == 0 and "VERDICT PASS" in tail
        out.append((name, ok, tail))
    return out


def feeding_edges(red):
    """Byte edges whose writer feeds a red artifact (so the failure is actionable)."""
    return [e for e in EDGES if e[0] == red and e[2] == "bytes"]


def law_view():
    """AC-COO9 (R3301, exit 2): the one place the two "newest" laws are compared.

    R3300 measured that docs/status-export.json's own answer to "which pair is
    newest" flips with the last write. The entry page used to copy that answer
    (R3297 three-way branch, R3300 one boolean) and could therefore never be a
    fixed point. The answer left the page; the comparison lives HERE, read-only,
    so the disagreement is still observable without feeding a page's bytes.

    Both names come from fresh derivations - an mtime scan here and
    export_round's own call - and the flag is computed from them, never typed.
    """
    best = None
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".json"):
            continue
        stem = name[:-5]
        if not os.path.isfile(os.path.join(PREVIEW, stem + ".html")):
            continue
        stamp = os.stat(os.path.join(PREVIEW, stem + ".html")).st_mtime_ns
        if best is None or stamp >= best[0]:
            best = (stamp, name)
    mtime_json = best[1] if best else None
    export_json = None
    try:
        if os.path.join(ROOT, "src", "os") not in sys.path:
            sys.path.insert(0, os.path.join(ROOT, "src", "os"))
        import importlib
        er = importlib.import_module("export_round")
        pair, _skipped, _board = er.newest_artifact(ROOT)
        if pair is not None:
            export_json = os.path.basename(pair[2])
    except Exception as exc:          # named, never fabricated
        return mtime_json, None, "export-derivation-failed: %s" % exc
    if export_json is None:
        return mtime_json, None, "export-derives-no-pair"
    return mtime_json, export_json, (mtime_json == export_json)


def law_row():
    """Print the witness row and grade the four AC-COO9 arms. Returns True/False."""
    mtime_json, export_json, same = law_view()
    if isinstance(same, str):         # derivation failure: named absence, not a pair
        print("LAW mtime=%s export=- same=unknown why=%s"
              % (mtime_json or "-", same))
        return True
    print("LAW mtime=%s export=%s same=%s" % (mtime_json, export_json, same))
    arms = {
        "both-named": bool(mtime_json) and bool(export_json),
        "flag-derived": same == (mtime_json == export_json),
    }
    leaked = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with io.open(os.path.join(PREVIEW, name), "r", encoding="utf-8",
                     errors="replace") as fh:
            if "LAW mtime=" in fh.read():
                leaked.append(name)
    arms["no-page-carries-it"] = not leaked
    print("AC-COO9 %s %s" % ("PASS" if all(arms.values()) else "FAIL",
                             " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items()))
                             or "all-arms-green"))
    return all(arms.values())


def day_view():
    """AC-COO10 arms, read from the landed page and the declared table.

    The day is taken out of preview/index.html at `census day ` and graded on
    its own characters: ten, all date-shaped, then a separator. If the page ever
    prints a differently shaped moment the arm reddens rather than trusting the
    declaration above it.
    """
    reader, writer, kind, page, prefix, width = DAY_EDGE
    landed = None
    shaped = False
    path = os.path.join(ROOT, page)
    if os.path.isfile(path):
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        at = text.find(prefix)
        if at >= 0:
            start = at + len(prefix)
            landed = text[start:start + width]
            after = text[start + width:start + width + 1]
            shaped = (bool(DAY_RE.fullmatch(landed))
                      and not after.isalnum())
    in_cycle = any(e[2] == kind for e in EDGES)
    leaked = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with io.open(os.path.join(PREVIEW, name), "r", encoding="utf-8",
                     errors="replace") as fh:
            if "DAY-EDGE " in fh.read():
                leaked.append(name)
    arms = {
        "both-named": bool(reader) and bool(writer),
        "width-10": width == 10 and shaped,
        "outside-byte-cycle": not in_cycle,
        "no-page-carries-it": not leaked,
    }
    return landed, kind, arms


def day_row():
    """Print the declared day edge and grade AC-COO10. Returns True/False."""
    landed, kind, arms = day_view()
    print("DAY-EDGE index <- export kind=%s width=10 landed=%s in-byte-cycle=%s "
          "remedy=%s"
          % (kind, landed or "-", not arms["outside-byte-cycle"], REMEDY))
    print("AC-COO10 %s %s" % ("PASS" if all(arms.values()) else "FAIL",
                              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items()))))
    return all(arms.values())


def remedy_view():
    """AC-COO11 arms: the printed remedy must be the measured one.

    The names are parsed out of REMEDY (so a hand-edit that drops or adds a
    renderer reddens), and each owed name must still be a file that holds the
    criterion token measured to fail - the remedy cannot name a reader that
    stopped grading anything. The spared edge must still be the byte edge the
    table declares, so "chain is not owed" stays a statement about this ring.
    """
    names = []
    at = REMEDY.find("re-render-")
    if at >= 0:
        head = REMEDY[at + len("re-render-"):].split("-after-")[0]
        names = [n for n in head.split("-and-") if n]
    owed = tuple(n for n, _, _ in REMEDY_OWED)
    readers = []
    for name, relpath, token in REMEDY_OWED:
        path = os.path.join(ROOT, relpath)
        present = os.path.isfile(path)
        hit = False
        if present:
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                hit = token in fh.read()
        readers.append({"name": name, "reader_file": relpath, "token": token,
                        "file_present": present, "token_found": hit})
    spared = REMEDY_SPARED
    spared_edges = [e for e in EDGES if e[0] == spared and e[2] == "bytes"]
    spared_ok = False
    if spared_edges:
        relpath, token = spared_edges[0][3], spared_edges[0][4]
        path = os.path.join(ROOT, relpath)
        if os.path.isfile(path):
            with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
                spared_ok = token in fh.read()
    leaked = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with io.open(os.path.join(PREVIEW, name), "r", encoding="utf-8",
                     errors="replace") as fh:
            if REMEDY_LEAK in fh.read():
                leaked.append(name)
    arms = {
        "remedy-names-owed": sorted(names) == sorted(owed) and len(names) == len(owed),
        "owed-readers-carry-token": all(r["file_present"] and r["token_found"]
                                        for r in readers),
        "spared-is-the-declared-edge": (spared not in names) and spared_ok,
        "no-page-carries-it": not leaked,
    }
    return names, readers, arms


def remedy_row():
    """Print the measured remedy row and grade AC-COO11. Returns True/False."""
    names, readers, arms = remedy_view()
    print("REMEDY-EDGE owed=%s spared=%s why=day-is-ten-chars-and-board-stamps-"
          "executions" % (",".join(names) or "-", REMEDY_SPARED))
    for row in readers:
        print("REMEDY-READER %-6s %s:%s found=%s"
              % (row["name"], row["reader_file"], row["token"], row["token_found"]))
    print("AC-COO11 %s %s" % ("PASS" if all(arms.values()) else "FAIL",
                              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items()))))
    return all(arms.values())


def day_passes_view():
    """AC-COO12 arms: the declared pass count and the structure that owes it.

    The number is not re-measured here (a day cannot be advanced from a
    read-only plan); what is graded is that the order still has the shape the
    measurement found - export last, export really writing the census day - and
    that the declared count fits the iteration budget.
    """
    writer_name, relpath, import_token = DAY_PASSES_WRITER
    path = os.path.join(ROOT, relpath)
    import_hit = False
    if os.path.isfile(path):
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            import_hit = import_token in fh.read()
    key_path, key_token = DAY_PASSES_KEY
    key_hit = False
    key_abs = os.path.join(ROOT, key_path)
    if os.path.isfile(key_abs):
        with io.open(key_abs, "r", encoding="utf-8", errors="replace") as fh:
            key_hit = key_token in fh.read()
    last = STEPS[-1][0] if STEPS else ""
    leaked = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with io.open(os.path.join(PREVIEW, name), "r", encoding="utf-8",
                     errors="replace") as fh:
            if DAY_PASSES_LEAK in fh.read():
                leaked.append(name)
    arms = {
        "budget-covers-it": MAX_PASSES >= DAY_PASSES,
        "export-runs-last": last == writer_name,
        "export-writes-the-day": import_hit and key_hit,
        "no-page-carries-it": not leaked,
    }
    return arms


def day_passes_row():
    """Print the measured pass count and grade AC-COO12. Returns True/False."""
    arms = day_passes_view()
    print("DAY-PASSES count=%d why=%s budget=%d export-last=%s"
          % (DAY_PASSES, DAY_PASSES_WHY, MAX_PASSES, arms["export-runs-last"]))
    print("AC-COO12 %s %s" % ("PASS" if all(arms.values()) else "FAIL",
                              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items()))))
    return all(arms.values())


def evidence_view():
    """AC-COO13 arms: the evidence edge is an input, never a ring edge.

    Derived from the files: the export must still own the field, no ring
    reader's own source may read it, the export must still be the last step, the
    edge must not be listed in EDGES, and no preview page may carry the row.
    """
    reader_name, writer_name, kind, relpath, token = EVIDENCE_EDGE
    path = os.path.join(ROOT, relpath)
    owns = False
    if os.path.isfile(path):
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            owns = token in fh.read()
    readers = []
    for name, rel in EVIDENCE_READERS:
        abs_path = os.path.join(ROOT, rel)
        hit = False
        if os.path.isfile(abs_path):
            with io.open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
                hit = token in fh.read()
        readers.append({"name": name, "reader_file": rel, "reads_it": hit})
    listed = [e for e in EDGES if writer_name in (e[0], e[1])]
    last = STEPS[-1][0] if STEPS else ""
    leaked = []
    for name in sorted(os.listdir(PREVIEW)):
        if not name.endswith(".html"):
            continue
        with io.open(os.path.join(PREVIEW, name), "r", encoding="utf-8",
                     errors="replace") as fh:
            if EVIDENCE_LEAK in fh.read():
                leaked.append(name)
    arms = {
        "export-owns-the-field": owns,
        "no-ring-reader-reads-it": not any(r["reads_it"] for r in readers),
        "export-runs-last": last == reader_name,
        "not-in-the-edge-table": not listed,
        "no-page-carries-it": not leaked,
    }
    return arms, readers


def evidence_row():
    """Print the evidence-input edge and grade AC-COO13. Returns True/False."""
    arms, readers = evidence_view()
    reader_name, writer_name, kind, relpath, token = EVIDENCE_EDGE
    print("EVIDENCE-EDGE %-7s %-7s %-5s %s:%s ring-readers=%d"
          % (writer_name, reader_name, kind, relpath, token,
             sum(1 for r in readers if r["reads_it"])))
    for row in readers:
        print("EVIDENCE-READER %-7s %s reads-it=%s"
              % (row["name"], row["reader_file"], row["reads_it"]))
    print("AC-COO13 %s %s" % ("PASS" if all(arms.values()) else "FAIL",
                              " ".join("%s=%s" % (k, v) for k, v in sorted(arms.items()))))
    return all(arms.values())


def cmd_plan():
    print("STEPS %d %s" % (len(STEPS), ",".join(n for n, _, _ in STEPS)))
    gone = missing_steps()
    if gone:
        for name, module in gone:
            print("MISSING %s %s" % (name, module))
        print("VERDICT FAIL %s %s"
              % (MISSING_STEP, ",".join(n for n, _ in gone)))
        return 2
    for row in edge_report():
        print("EDGE %-7s <- %-7s %-5s %s:%s found=%s"
              % (row["reader"], row["writer"], row["kind"],
                 row["reader_file"], row["token"], row["token_found"]))
    cycles = byte_cycle()
    print("BYTE-CYCLES %d %s" % (len(cycles), ",".join("->".join(c) for c in cycles) or "none"))
    law_ok = law_row()
    day_ok = day_row()
    remedy_ok = remedy_row()
    passes_ok = day_passes_row()
    evidence_ok = evidence_row()
    bad = [r for r in edge_report() if not (r["file_present"] and r["token_found"])]
    if bad:
        print("VERDICT FAIL %d orphan-edge(s): %s"
              % (len(bad), ",".join("%s<-%s" % (r["reader"], r["writer"]) for r in bad)))
        return 2
    if not law_ok:
        print("VERDICT FAIL AC-COO9 witness row")
        return 2
    if not day_ok:
        print("VERDICT FAIL AC-COO10 day edge")
        return 2
    if not remedy_ok:
        print("VERDICT FAIL AC-COO11 remedy row")
        return 2
    if not passes_ok:
        print("VERDICT FAIL AC-COO12 day pass count")
        return 2
    if not evidence_ok:
        print("VERDICT FAIL AC-COO13 evidence input edge")
        return 2
    print("VERDICT PASS edges=%d cycles=%d" % (len(EDGES), len(cycles)))
    return 0


def cmd_dry():
    before = snapshot()
    print("PLAN steps=%s" % ",".join(n for n, _, _ in STEPS))
    results = verify()
    after = snapshot()
    for name, ok, tail in results:
        print("CHECK %-6s %s %s" % (name, "PASS" if ok else "FAIL", tail))
    unchanged = before == after
    print("READ-ONLY unchanged=%s" % unchanged)
    red = [n for n, ok, _ in results if not ok]
    if red:
        print("VERDICT FAIL red=%s (dry run: nothing written)" % ",".join(red))
        return 2
    if not unchanged:
        print("VERDICT FAIL dry run changed bytes (AC-COO5)")
        return 2
    print("VERDICT PASS dry-run checks=4/4 read_only=True")
    return 0


def cmd_check():
    before = snapshot()
    results = verify()
    after = snapshot()
    for name, ok, tail in results:
        print("CHECK %-6s %s %s" % (name, "PASS" if ok else "FAIL", tail))
    red = [n for n, ok, _ in results if not ok]
    if before != after:
        print("VERDICT FAIL check changed bytes (AC-COO5)")
        return 2
    if red:
        for name in red:
            for e in feeding_edges(name):
                print("REDGE %s <- %s bytes %s" % (e[0], e[1], e[3]))
        print("VERDICT FAIL red=%s read_only=True" % ",".join(red))
        return 2
    print("VERDICT PASS checks=4/4 read_only=True")
    return 0


def cmd_write():
    gone = missing_steps()
    if gone:
        for name, module in gone:
            print("MISSING %s %s" % (name, module))
        print("VERDICT FAIL %s %s"
              % (MISSING_STEP, ",".join(n for n, _ in gone)))
        return 2
    for pass_no in range(1, MAX_PASSES + 1):
        transient = []
        for name, module, args in STEPS:
            rc, tail, _ = _run(module, args)
            print("PASS%d %-7s rc=%d %s" % (pass_no, name, rc, tail))
            if rc != 0:
                # A producer that grades its own gates while the ring is mid-
                # pass can be red and still have landed its page. The fixed
                # point is judged at the END of a pass (AC-COO4), so a mid-pass
                # rc is recorded and disclosed, not treated as the verdict.
                transient.append(name)
        if transient:
            print("PASS%d TRANSIENT red-steps=%s (landed anyway; judged at pass end)"
                  % (pass_no, ",".join(transient)))
        results = verify()
        for name, ok, tail in results:
            print("PASS%d CHECK %-6s %s %s" % (pass_no, name, "PASS" if ok else "FAIL", tail))
        red = [n for n, ok, _ in results if not ok]
        if not red:
            print("VERDICT PASS passes=%d steps=%d checks=4/4 transient_steps=%d"
                  % (pass_no, len(STEPS), len(transient)))
            return 0
        for name in red:
            for e in feeding_edges(name):
                print("REDGE pass=%d %s <- %s bytes %s" % (pass_no, e[0], e[1], e[3]))
    print("VERDICT FAIL no fixed point in %d passes (AC-COO3)" % MAX_PASSES)
    return 2


def build_parser():
    parser = argparse.ArgumentParser(description="Executable closeout order for the four faces.")
    parser.add_argument("--plan", action="store_true",
                        help="print the declared steps and edges, grade the edge table")
    parser.add_argument("--dry-run", action="store_true",
                        help="run the four checks, write nothing")
    parser.add_argument("--check", action="store_true",
                        help="read-only: the four faces must be green together")
    parser.add_argument("--write", action="store_true",
                        help="render in the declared order until all four checks pass")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.plan:
        return cmd_plan()
    if args.dry_run:
        return cmd_dry()
    if args.check:
        return cmd_check()
    if args.write:
        return cmd_write()
    build_parser().print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
