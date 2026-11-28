"""Battery suite for the single archive READ shared by the two FOLD-CARRY
faces - AC-FCW1..AC-FCW6.

Pinned in src/os/backlog.md at R3634 (AC-FCW1..AC-FCW4) and at R3635
(AC-FCW1 re-pointed, AC-FCW2 strengthened, AC-FCW5/AC-FCW6 added) BEFORE
this file or the tool changed.

R3635: the walk of R3634 shared only the window view. The receipt scan, the
budget-bound scan and census's own exemption reading still opened the same
archives again, so one `--evidence` run opened each of the three archives
four times (measured: 12 opens). The reader now returns numbered raw lines
and windows from ONE open of each file, and every consumer takes that view.

The defect measured that window: one `--evidence` run walked every archive
twice (tmp/probe_R3634_walk.py on the live tree read `archives_on_disk=3
calls_total=6`, two opens per file) because evidence() first called census(),
which walked the archives, and then walked them again for its own
archive_ledger set and narratives. The fix is one materialised walk
(`_archive_walk`) that census() and evidence() both accept, so a face that is
handed a walk never opens an archive itself.

Read-only against the repo: the tool, the two landed pages, the state file and
every archive are stat-signed before and after the run. Synthetic worlds live
under the system temp directory and are removed before the run ends.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "fold_carry_census.py")
STATE = os.path.join(ROOT, "src", "os", "state.json")
CENSUS_PAGE = os.path.join(ROOT, "preview", "fold-carry-census.json")
EVIDENCE_PAGE = os.path.join(ROOT, "preview", "fold-carry-evidence.json")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import fold_carry_census as FCC  # noqa: E402
import ledger_lines as LL  # noqa: E402

FAILS = []
CHECKS = []
WINDOW_CALL = "LL.load_archive_windows("
VIEW_CALL = "LL.read_archive_view("


def ok(name, cond, detail=""):
    CHECKS.append(name)
    if not cond:
        FAILS.append(name)
        print("FAIL %s %s" % (name, detail))
    else:
        print("PASS %s %s" % (name, detail))


def read_text(path):
    handle = io.open(path, "r", encoding="utf-8")
    try:
        return handle.read()
    finally:
        handle.close()


def stat_sig(path):
    try:
        info = os.stat(path)
    except OSError:
        return None
    return (info.st_size,
            hashlib.sha256(io.open(path, "rb").read()).hexdigest()[:16])


def report_bytes(report):
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def world():
    """Two archives whose halves of round 90003 sit in different files."""
    root = tempfile.mkdtemp(prefix="fcw-")
    logs = os.path.join(root, "logs")
    state_dir = os.path.join(root, "src", "os")
    os.makedirs(logs)
    os.makedirs(state_dir)
    first = os.path.join(logs, "state-log-archive-probe-a.md")
    handle = io.open(first, "w", encoding="utf-8", newline="\n")
    handle.write("# --- R90010 fold append (probe)\n")
    handle.write("R90003 probe narrative line one\n")
    handle.close()
    second = os.path.join(logs, "state-log-archive-probe-b.md")
    handle = io.open(second, "w", encoding="utf-8", newline="\n")
    handle.write("# --- R90011 fold append (probe)\n")
    handle.write("R90003 tokens: local=1 api=0 api_reason=probe\n")
    handle.close()
    state = os.path.join(state_dir, "state.json")
    handle = io.open(state, "w", encoding="utf-8", newline="\n")
    handle.write(json.dumps({"tick": 90011, "log": []}) + "\n")
    handle.close()
    return root, state, [first, second]


def main():
    sig_tool = stat_sig(TOOL)
    sig_state = stat_sig(STATE)
    sig_pages = [stat_sig(CENSUS_PAGE), stat_sig(EVIDENCE_PAGE)]
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    sig_archives = [stat_sig(path) for path in paths]
    source = read_text(TOOL)

    # AC-FCW1 (R3635, re-pointed and stricter): the tool opens no archive of
    # its own. Exactly one read site - read_archive_view inside _archive_walk
    # - precedes both faces, no face asks for windows by path, and every
    # block_receipts call in the tool carries the handed-in views.
    view_calls = source.count(VIEW_CALL)
    window_calls = source.count(WINDOW_CALL)
    open_calls = source.count("io.open(")
    walk_at = source.find("def _archive_walk(")
    call_at = source.find(VIEW_CALL)
    evidence_at = source.find("def evidence(")
    census_at = source.find("def census(")
    inside = 0 <= walk_at < call_at < evidence_at < census_at
    receipts = [at for at in range(len(source))
                if source.startswith("LL.block_receipts(", at)]
    receipts_bound = all("views=" in source[at:at + 60] for at in receipts)
    # The three remaining io.open calls are the landed-page reader, the page
    # writer and the no-view fallback in _raw_lines; the two faces always
    # hand a view in, so none of them is reached by a face.
    ok("AC-FCW1",
       view_calls == 1 and window_calls == 0 and open_calls == 3 and inside
       and len(receipts) == 2 and receipts_bound,
       "view=%d window=%d io_open=%d(landed/write/fallback) inside=%s"
       " receipts=%d bound=%s walk_at=%d call_at=%d"
       % (view_calls, window_calls, open_calls, inside, len(receipts),
          receipts_bound, walk_at, call_at))

    # AC-FCW2 (R3635, strengthened): the wrapper counts REAL opens of the one
    # read site, so a narrower walk cannot hide the other consumers - twelve
    # opens read green under the old arm, which counted only the view layer.
    # Both faces are asked: one evidence run and one standalone census run
    # must open each archive exactly once.
    def opens_during(fn):
        seen = []
        real_view = LL.read_archive_view

        def counting(path):
            seen.append(path)
            return real_view(path)

        LL.read_archive_view = counting
        try:
            report = fn()
        finally:
            LL.read_archive_view = real_view
        return report, seen

    counted, seen_evidence = opens_during(FCC.evidence)
    plain, seen_census = opens_during(FCC.census)

    def once_each(seen):
        per_path = {}
        for path in seen:
            per_path[path] = per_path.get(path, 0) + 1
        return (sorted(seen) == sorted(paths)
                and set(per_path.values()) == set([1])), per_path

    evidence_once, per_evidence = once_each(seen_evidence)
    census_once, per_census = once_each(seen_census)
    ok("AC-FCW2",
       evidence_once and census_once
       and len(counted["frozen_rounds"]) == 5
       and len(plain["nowhere_rounds"]) == 5,
       "archives=%d evidence=%d census=%d per_path=%s frozen=%d holes=%d"
       % (len(paths), len(seen_evidence), len(seen_census),
          ",".join("%s:%d/%d" % (os.path.basename(key),
                                 per_evidence.get(key, 0),
                                 per_census.get(key, 0))
                   for key in sorted(set(per_evidence) | set(per_census))),
          len(counted["frozen_rounds"]), len(plain["nowhere_rounds"])))

    # AC-FCW3: injecting the walk is transparent on the live tree - both
    # faces read the same bytes whether they build the walk or are handed it
    # - and both landed pages equal their fresh derivation.
    walk = FCC._archive_walk(paths)
    plain_census = report_bytes(FCC.census())
    given_census = report_bytes(FCC.census(_walk=walk))
    plain_evidence = report_bytes(FCC.evidence())
    given_evidence = report_bytes(FCC.evidence(_walk=walk))
    fresh_census = report_bytes(FCC.census())
    fresh_evidence = report_bytes(FCC.evidence())
    landed_census = FCC.landed(CENSUS_PAGE)
    landed_evidence = FCC.landed(EVIDENCE_PAGE)
    pages = (landed_census == fresh_census.decode("utf-8")
             and landed_evidence == fresh_evidence.decode("utf-8"))
    ok("AC-FCW3",
       plain_census == given_census and plain_evidence == given_evidence
       and pages,
       "census_same=%s evidence_same=%s census_page=%s evidence_page=%s"
       % (plain_census == given_census, plain_evidence == given_evidence,
          landed_census == fresh_census.decode("utf-8"),
          landed_evidence == fresh_evidence.decode("utf-8")))

    # AC-FCW4: the walk is really consumed - a walk that omits the file
    # holding round 90003's ledger line turns a clean census into a hole -
    # and both page checks still pass with the repo untouched.
    root, state, world_paths = world()
    saved = FCC.STATE
    try:
        FCC.STATE = state
        world_walk = FCC._archive_walk(LL.archive_files(
            LL.default_logs_dir(state)))
        full = FCC.census(90000)
        truncated = FCC.census(90000, _walk=world_walk[:1])
    finally:
        FCC.STATE = saved
        shutil.rmtree(root, ignore_errors=True)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc_census = FCC.main(["--check"])
        rc_evidence = FCC.main(["--evidence", "--check"])
    text = out.getvalue()
    untouched = (stat_sig(TOOL) == sig_tool and stat_sig(STATE) == sig_state
                 and [stat_sig(page) for page in (CENSUS_PAGE, EVIDENCE_PAGE)]
                 == sig_pages
                 and [stat_sig(path) for path in paths] == sig_archives)
    ok("AC-FCW4",
       len(world_paths) == 2
       and full["nowhere_rounds"] == [] and full["rounds"] == 1
       and full["archive_ledger_rounds"] == 1
       and truncated["nowhere_rounds"] == [90003]
       and truncated["archive_ledger_rounds"] == 0
       and rc_census == 0 and rc_evidence == 0
       and "FCC-CHECK VERDICT PASS" in text
       and "FCE-CHECK VERDICT PASS" in text
       and untouched,
       "world=%s full=%s/%d trunc=%s/%d rc=%d/%d pages=%s untouched=%s"
       % (len(world_paths), full["nowhere_rounds"], full["rounds"],
          truncated["nowhere_rounds"], truncated["archive_ledger_rounds"],
          rc_census, rc_evidence,
          "PASS" if ("FCC-CHECK VERDICT PASS" in text
                     and "FCE-CHECK VERDICT PASS" in text) else "RED",
          untouched))

    # AC-FCW5 (R3635): the view is an equal standing for the two line scans.
    # On the live tree a receipts read and a budget-bound read are identical
    # whether they open the files or take the view, down to each receipt's
    # physical line number and span. A private world then proves the line
    # number comes from the numbered raw lines: the receipt and the presence
    # line sit on COMMENT lines, which the window view never holds.
    line_world = tempfile.mkdtemp(prefix="fcu-")
    try:
        logs = os.path.join(line_world, "logs")
        os.makedirs(logs)
        probe = os.path.join(logs, "state-log-archive-probe-c.md")
        handle = io.open(probe, "w", encoding="utf-8", newline="\n")
        handle.write("# header line one\n")
        handle.write("# header line two\n")
        handle.write("# --- R90020 fold append (probe)\n")
        handle.write("R90001 probe narrative line one\n")
        handle.write("# fold 24 moved the whole R90001 round block "
                     "(narrative, tokens, evidence)\n")
        handle.write("R90002 tokens: local=1 api=0 api_reason=probe\n")
        handle.write("R90003 fold refuses by name (E_ROUND_LOST)\n")
        handle.close()
        line_views = [LL.read_archive_view(probe)]
        live_receipts = FCC.receipt_index(paths)
        view_receipts = FCC.receipt_index(paths, views=FCC._archive_walk(paths))
        live_bounds = FCC.budget_line_bounds(paths, LL.load_state_log(STATE))
        view_bounds = FCC.budget_line_bounds(
            paths, LL.load_state_log(STATE), views=FCC._archive_walk(paths))
        world_receipts = FCC.receipt_index([probe], views=line_views)
        world_receipts_by_path = FCC.receipt_index([probe])
        world_bounds = FCC.budget_line_bounds([probe], [], views=line_views)
        one = world_receipts.get(90001, [])
        ok("AC-FCW5",
           live_receipts == view_receipts and live_bounds == view_bounds
           and bool(live_receipts)
           and world_receipts == world_receipts_by_path
           and len(one) == 1 and one[0]["line"] == 5
           and one[0]["file"] == os.path.basename(probe)
           and one[0]["omits_budget"] is False
           and world_bounds == (90002, 90003),
           "live_receipts=%d same=%s live_bounds=%s same=%s line=%s bounds=%s"
           % (len(live_receipts), live_receipts == view_receipts,
              live_bounds, live_bounds == view_bounds,
              one[0]["line"] if one else None, world_bounds))
    finally:
        shutil.rmtree(line_world, ignore_errors=True)

    # AC-FCW6 (R3635, negative control): a view that omits a file really is
    # the world the consumer sees - the receipt set and the budget boundary
    # both move - so the shared read is consumed rather than decorative.
    cut_world = tempfile.mkdtemp(prefix="fcu-cut-")
    try:
        logs = os.path.join(cut_world, "logs")
        os.makedirs(logs)
        kept = os.path.join(logs, "state-log-archive-probe-d.md")
        handle = io.open(kept, "w", encoding="utf-8", newline="\n")
        handle.write("# --- R90030 fold append (probe)\n")
        handle.write("R90005 probe narrative line one\n")
        handle.close()
        dropped = os.path.join(logs, "state-log-archive-probe-e.md")
        handle = io.open(dropped, "w", encoding="utf-8", newline="\n")
        handle.write("# --- R90031 fold append (probe)\n")
        handle.write("R90006 tokens: local=2 api=0 api_reason=probe\n")
        handle.write("# fold 25 moved the whole R90006 round block "
                     "(narrative, tokens)\n")
        handle.close()
        both = [LL.read_archive_view(kept), LL.read_archive_view(dropped)]
        full_receipts = FCC.receipt_index([kept, dropped], views=both)
        cut_receipts = FCC.receipt_index([kept, dropped], views=both[:1])
        full_bounds = FCC.budget_line_bounds([kept, dropped], [], views=both)
        cut_bounds = FCC.budget_line_bounds([kept, dropped], [], views=both[:1])
        ok("AC-FCW6",
           90006 in full_receipts and 90006 not in cut_receipts
           and full_bounds == (90006, None) and cut_bounds == (None, None),
           "full=%s cut=%s full_bounds=%s cut_bounds=%s"
           % (sorted(full_receipts), sorted(cut_receipts),
              full_bounds, cut_bounds))
    finally:
        shutil.rmtree(cut_world, ignore_errors=True)

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
