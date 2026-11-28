"""Battery suite for the FOLD-CARRY evidence face's law axis - AC-FCEX1..4.

Pinned in src/os/backlog.md at R3633 BEFORE this file or the tool edit. The
defect measured that window: the evidence face spoke two receipt kinds
(block-receipt / no-receipt) while ledger_lines.FOLD_CARRY_EXEMPT already
carried four evidence kinds, so R3458 (inline payload) and R3610 (tree
absence) were published as "no receipt" beside a law that excuses both by
name. A reader of that page could not tell an unexplained frozen hole from
one the law excuses.

The fix is two axes, never one overloaded class: `class` keeps telling the
RECEIPT fact (R3436 and R3459 are both a block receipt AND law-excused, so a
single class would have to lie about one of them), and law_ok / law_kind /
law_why come from the law's own vocabulary (ledger_lines.exemption_kind).

Read-only against the repo: the tool, the landed page, the state file and
every archive are stat-signed before and after the run. Synthetic worlds live
under the system temp directory and are removed before the run ends.

Source discipline: pure ASCII, stdlib only, no clock, no network, no shell.
"""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "fold_carry_census.py")
LAW = os.path.join(ROOT, "src", "os", "ledger_lines.py")
PAGE = os.path.join(ROOT, "preview", "fold-carry-evidence.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import fold_carry_census as FCC  # noqa: E402
import ledger_lines as LL  # noqa: E402

FAILS = []
CHECKS = []

# The kinds the table carries, written here as the PIN's expectation.
# R3644: R3625 joins as the second tree_absence round once the law named it.
EXPECTED_KINDS = {3436: "receipt", 3458: "inline_payload",
                  3459: "receipt", 3610: "tree_absence",
                  3625: "tree_absence"}


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
            hashlib.sha256(read_text(path).encode("utf-8", "replace"))
            .hexdigest()[:16])


def world(kind_lines):
    """A private state.json plus one archive window under one temp root."""
    root = tempfile.mkdtemp(prefix="fcex-")
    logs = os.path.join(root, "logs")
    state_dir = os.path.join(root, "src", "os")
    os.makedirs(logs)
    os.makedirs(state_dir)
    archive = os.path.join(logs, "state-log-archive-probe.md")
    handle = io.open(archive, "w", encoding="utf-8", newline="\n")
    handle.write("# --- R90002 fold append (probe)\n")
    for line in kind_lines:
        handle.write(line + "\n")
    handle.close()
    state = os.path.join(state_dir, "state.json")
    handle = io.open(state, "w", encoding="utf-8", newline="\n")
    handle.write(json.dumps({"tick": 90002, "log": []}) + "\n")
    handle.close()
    return root, state


def main():
    sig_tool = stat_sig(TOOL)
    sig_law = stat_sig(LAW)
    sig_page = stat_sig(PAGE)
    sig_state = stat_sig(STATE)
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    sig_archives = [stat_sig(path) for path in paths]

    tool_source = read_text(TOOL)
    law_source = read_text(LAW)
    report = FCC.evidence()
    rows = dict((row["round"], row) for row in report["rows"])

    # AC-FCEX1: one vocabulary owner, no local kind literals in the tool, and
    # no local fallback - the negative control replaces the law call.
    literals = [name for name in ("tree_absence", "inline_payload",
                                  "narrative_span") if name in tool_source]
    # Two named sites, both through the law: the publication call and the
    # pre-existing not-a-hole class, which used to carry its own string copy.
    calls = len(re.findall(r"LL\.exemption_kind\(", tool_source))
    named = len(re.findall(r"LL\.FOLD_CARRY_NOT_A_HOLE_KIND", tool_source))
    owner = (len(re.findall(r"^FOLD_CARRY_EXEMPT_KINDS = \(", law_source,
                            re.M)) == 1
             and len(re.findall(r"^def exemption_kind\(", law_source,
                                re.M)) == 1)
    real_kind = LL.exemption_kind
    try:
        LL.exemption_kind = lambda round_no: None
        blind = FCC.evidence()
    finally:
        LL.exemption_kind = real_kind
    blind_kinds = [row["law_kind"] for row in blind["rows"]]
    ok("AC-FCEX1",
       not literals and calls == 2 and named == 1 and owner
       and all(item is None for item in blind_kinds)
       and all(row["law_ok"] for row in blind["rows"]),
       "literals=%s calls=%d named=%d owner=%s blind_none=%d"
       % (",".join(literals) or "-", calls, named, owner,
          len([item for item in blind_kinds if item is None])))

    # AC-FCEX2: the live tree publishes one kind per hole, and a round the
    # table does not name still reads unexplained - the excuse cannot swallow
    # a real new hole.
    live_kinds = dict((round_no, row["law_kind"]) for round_no, row in rows.items())
    live_ok = all(row["law_ok"] for row in rows.values())
    counts = (report["law_excused"] == len(rows)
              and report["unexplained"] == 0)
    root, state = world(["R90003 probe narrative line one"])
    saved = FCC.STATE
    try:
        FCC.STATE = state
        foreign = FCC.evidence()
    finally:
        FCC.STATE = saved
        shutil.rmtree(root, ignore_errors=True)
    foreign_rows = foreign["rows"]
    ok("AC-FCEX2",
       live_kinds == EXPECTED_KINDS and live_ok and counts
       and len(foreign_rows) == 1
       and foreign_rows[0]["class"] == "no-receipt"
       and foreign_rows[0]["law_ok"] is False
       and foreign_rows[0]["law_kind"] is None
       and foreign_rows[0]["law_why"] == "not-named"
       and foreign["law_excused"] == 0 and foreign["unexplained"] == 1,
       "kinds=%s counts=%d/%d foreign=%s/%s/%s"
       % (",".join("%d:%s" % (key, live_kinds[key]) for key in sorted(live_kinds)),
          report["law_excused"], report["unexplained"],
          foreign_rows[0]["class"], foreign_rows[0]["law_ok"],
          foreign_rows[0]["law_why"]))

    # AC-FCEX3: the page is a function of the tree, the summary line ends on
    # the law counts, and every hole prints exactly one law token.
    fresh = json.dumps(FCC.evidence(), indent=2, sort_keys=True) + "\n"
    was = FCC.landed(PAGE)
    line = FCC.evidence_line(report)
    tail = "law_excused=%d unexplained=%d" % (report["law_excused"],
                                              report["unexplained"])
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        rc = FCC.main(["--evidence", "--check"])
    text = sink.getvalue()
    tokens = [item for item in text.split() if item.startswith("law=")]
    ok("AC-FCEX3",
       was is not None and was == fresh
       and "\n" not in line and line.endswith(" " + tail)
       and rc == 0 and "FCE-CHECK VERDICT PASS" in text
       and len(tokens) == len(rows)
       and sorted(tokens) == sorted(
           "law=%s" % item for item in live_kinds.values()),
       "page=%s line_tail=%s tokens=%d rc=%d"
       % ("on-disk" if was == fresh else "STALE", line[-1 * len(tail):],
          len(tokens), rc))

    # AC-FCEX4: the law was not widened - the table keys and the live
    # exemption set are exactly the R3632 readings, a foreign round gets no
    # kind, and the tool stays child-process free.
    table = sorted(LL.FOLD_CARRY_EXEMPT.keys())
    single_kind = all(
        len([1 for kind in LL.FOLD_CARRY_EXEMPT_KINDS
             if kind in LL.FOLD_CARRY_EXEMPT[round_no]]) == 1
        for round_no in table)
    audit = LL.audit_fold_carry(paths, live_lines=LL.load_state_log(STATE))
    excused = sorted(set(item["round"] for item in audit["exemptions"]))
    banned = re.search(r"^\s*(?:import|from)\s+"
                       r"(?:subprocess|socket|urllib|http|requests|ftplib)\b",
                       tool_source, re.M)
    same = (stat_sig(TOOL) == sig_tool and stat_sig(LAW) == sig_law
            and stat_sig(PAGE) == sig_page and stat_sig(STATE) == sig_state
            and [stat_sig(path) for path in paths] == sig_archives)
    ok("AC-FCEX4",
       table == [3112, 3436, 3458, 3459, 3610, 3625] and single_kind
       and excused == [3112, 3436, 3458, 3459, 3610, 3625]
       and audit["gaps"] == [] and LL.exemption_kind(90001) is None
       and banned is None and same,
       "table=%s single_kind=%s excused=%s gaps=%d repo_untouched=%s"
       % (",".join(str(item) for item in table), single_kind,
          ",".join("R%d" % item for item in excused),
          len(audit["gaps"]), same))

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
