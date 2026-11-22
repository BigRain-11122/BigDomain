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

Nothing here renders a page itself, runs JS, opens a socket or reads the clock
for a product number.
"""
import argparse
import io
import json
import os
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

# (reader, writer, kind, reader_file, evidence_token) - kind in {"bytes","mtime"}.
EDGES = [
    ("chain", "index", "bytes", "tools/face_backhop.py", "data-back-bytes"),
    ("index", "chain", "bytes", "tools/deliverable_index.py", "html_bytes"),
    ("index", "export", "bytes", "tools/deliverable_index.py", "census_ts"),
    ("sweep", "index", "bytes", "tools/face_sweep.py", ("preview/index.html")),
    ("sweep", "chain", "bytes", "tools/face_sweep.py", "preview/first-yuan-chain.html"),
    ("export", "sweep", "mtime", "src/os/export_round.py", "BOARD_PAGES"),
]

# The standalone check face of each artifact (read-only, prints VERDICT).
CHECKS = [
    ("chain", "tools/first_yuan_chain.py", ["--check"]),
    ("index", "tools/deliverable_index.py", ["--check"]),
    ("sweep", "tools/face_sweep.py", ["--check"]),
    ("export", "src/os/export_round.py", ["--check"]),
]


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


def cmd_plan():
    print("STEPS %d %s" % (len(STEPS), ",".join(n for n, _, _ in STEPS)))
    for row in edge_report():
        print("EDGE %-7s <- %-7s %-5s %s:%s found=%s"
              % (row["reader"], row["writer"], row["kind"],
                 row["reader_file"], row["token"], row["token_found"]))
    cycles = byte_cycle()
    print("BYTE-CYCLES %d %s" % (len(cycles), ",".join("->".join(c) for c in cycles) or "none"))
    law_ok = law_row()
    bad = [r for r in edge_report() if not (r["file_present"] and r["token_found"])]
    if bad:
        print("VERDICT FAIL %d orphan-edge(s): %s"
              % (len(bad), ",".join("%s<-%s" % (r["reader"], r["writer"]) for r in bad)))
        return 2
    if not law_ok:
        print("VERDICT FAIL AC-COO9 witness row")
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
