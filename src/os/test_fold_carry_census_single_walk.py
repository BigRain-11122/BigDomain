"""Battery suite for the single archive walk shared by the two FOLD-CARRY
faces - AC-FCW1..AC-FCW4.

Pinned in src/os/backlog.md at R3634 BEFORE this file or the tool changed.

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
WALK_CALL = "LL.load_archive_windows("


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

    # AC-FCW1: exactly one archive walk in the tool, inside _archive_walk,
    # and it precedes both faces - so neither face can open a file itself.
    calls = source.count(WALK_CALL)
    walk_at = source.find("def _archive_walk(")
    call_at = source.find(WALK_CALL)
    evidence_at = source.find("def evidence(")
    census_at = source.find("def census(")
    inside = 0 <= walk_at < call_at < evidence_at < census_at
    ok("AC-FCW1",
       calls == 1 and inside,
       "call_sites=%d walk_at=%d call_at=%d evidence_at=%d census_at=%d"
       % (calls, walk_at, call_at, evidence_at, census_at))

    # AC-FCW2: one evidence run opens each archive exactly once. The wrapper
    # counts real calls, so a second walk cannot hide behind the first.
    seen = []
    real_walk = LL.load_archive_windows

    def counting(path):
        seen.append(path)
        return real_walk(path)

    LL.load_archive_windows = counting
    try:
        counted = FCC.evidence()
    finally:
        LL.load_archive_windows = real_walk
    per_path = {}
    for path in seen:
        per_path[path] = per_path.get(path, 0) + 1
    once_each = (sorted(seen) == sorted(paths)
                 and set(per_path.values()) == set([1]))
    ok("AC-FCW2",
       once_each and len(counted["frozen_rounds"]) == 4,
       "archives=%d calls=%d per_path=%s frozen=%d"
       % (len(paths), len(seen),
          ",".join("%s:%d" % (os.path.basename(key), per_path[key])
                   for key in sorted(per_path)),
          len(counted["frozen_rounds"])))

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

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
