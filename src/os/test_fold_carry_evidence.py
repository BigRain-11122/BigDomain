"""Battery suite for the FOLD-CARRY evidence face - AC-FCE1..AC-FCE6 (R3495).

Six arms were pinned in src/os/backlog.md at R3495 BEFORE this file or the
tools/fold_carry_census.py --evidence face existed. The two questions the
arms answer are the ones the board carried: (A) can a named exemption be
re-proved from disk without git, and (B) can narrowing the FOLD-CARRY range
heal the three frozen holes.

Nothing here changes a law: ledger_lines.py is imported, never edited, and
the six red archive arms stay red on purpose.

Read-only against the repo: the tool, the landed page and the archives are
stat-signed before and after the run. Synthetic worlds live under the system
temp directory and are removed before the run ends.

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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
TOOL = os.path.join(TOOLS, "fold_carry_census.py")
PAGE = os.path.join(ROOT, "preview", "fold-carry-evidence.json")
STATE = os.path.join(ROOT, "src", "os", "state.json")
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(ROOT, "src", "os"))

import fold_carry_census as FCC  # noqa: E402
import ledger_lines as LL  # noqa: E402

FAILS = []
CHECKS = []


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
    return (info.st_size, hashlib.sha256(read_text(path).encode("utf-8", "replace")).hexdigest()[:16])


def main():
    sig_tool = stat_sig(TOOL)
    sig_page = stat_sig(PAGE)
    sig_state = stat_sig(STATE)
    paths = LL.archive_files(LL.default_logs_dir(STATE))
    sig_archives = [stat_sig(path) for path in paths]

    report = FCC.evidence()
    rows = dict((row["round"], row) for row in report["rows"])

    # AC-FCE1: every frozen round carries ONE class, a receipt names parts in
    # words and omits the budget part, and the budget-carrying shape is refused.
    receipts = FCC.receipt_index(paths)
    refused = [round_no for round_no, items in receipts.items()
               for item in items if not item["omits_budget"]]
    with_budget = [item for items in receipts.values() for item in items
                   if not item["omits_budget"]]
    shape_ok = bool(with_budget) and all(
        "tokens" in [part.lower() for part in item["parts"]]
        for item in with_budget)
    classes_ok = all(row["class"] in ("block-receipt", "no-receipt")
                     for row in report["rows"])
    parts_ok = True
    for row in report["rows"]:
        if row["class"] != "block-receipt":
            continue
        receipt = row["receipt"]
        lowered = [part.lower() for part in receipt["parts"]]
        parts_ok = (parts_ok and len(receipt["parts"]) >= 2
                    and "tokens" not in lowered
                    and receipt["omits_budget"] is True)
    ok("AC-FCE1",
       classes_ok and parts_ok and shape_ok and bool(refused)
       and len(report["rows"]) == len(report["frozen_rounds"]),
       "rows=%d receipts=%d refused=%s"
       % (len(report["rows"]), report["block_receipt"],
          ",".join("R%d" % item for item in sorted(set(refused))) or "-"))

    # AC-FCE2: the claim "no git needed" is enforced by the source, not promised.
    source = read_text(TOOL)
    banned = re.search(r"^\s*(?:import|from)\s+"
                       r"(?:subprocess|socket|urllib|http|requests|ftplib)\b",
                       source, re.M)
    calls = re.search(r"\bos\.(?:system|popen)\b|subprocess\.", source)
    ok("AC-FCE2", banned is None and calls is None,
       "child_process_free=%s" % (banned is None and calls is None))

    # AC-FCE3: both measured boundaries are older than every hole, so the
    # narrowing path releases nothing.
    holes = report["frozen_rounds"]
    oldest = min(holes) if holes else None
    earliest = report["boundaries"]["earliest_budget"]["round"]
    lost_at = report["boundaries"]["e_round_lost"]["round"]
    ok("AC-FCE3",
       bool(holes) and earliest is not None and lost_at is not None
       and earliest < oldest and lost_at < oldest
       and report["narrowing_releases"] == 0,
       "holes=%d earliest=%s lost_at=%s releases=%d"
       % (len(holes), earliest, lost_at, report["narrowing_releases"]))

    # AC-FCE4: the repairable shape still reddens - a narrative archived while
    # its ledger line sits only in the live ring is left_behind, never clean.
    probe = 90001
    live_only = FCC.classify_round(probe, set(), set([probe]), ["R90001 x"])
    archived = FCC.classify_round(probe, set([probe]), set([probe]), ["R90001 x"])
    nowhere = FCC.classify_round(probe, set(), set(), ["R90001 x"])
    temp = tempfile.mkdtemp(prefix="fce-")
    try:
        archive = os.path.join(temp, "state-log-archive-probe.md")
        window = ("# --- R90002 fold append (probe)\n"
                  "R90001 probe narrative line one\n")
        handle = io.open(archive, "w", encoding="utf-8", newline="\n")
        handle.write(window)
        handle.close()
        red = LL.audit_fold_carry([archive], min_round=2914)
        handle = io.open(archive, "a", encoding="utf-8", newline="\n")
        handle.write("R90001 tokens: local=1 api=0 api_reason=probe\n")
        handle.close()
        green = LL.audit_fold_carry([archive], min_round=2914)
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    ok("AC-FCE4",
       live_only == "left_behind" and archived is None
       and nowhere == "nowhere" and len(red["gaps"]) == 1
       and len(green["gaps"]) == 0,
       "live_only=%s archived=%s nowhere=%s audit_red=%d audit_green=%d"
       % (live_only, archived, nowhere, len(red["gaps"]),
          len(green["gaps"])))

    # AC-FCE5: the landed page is a function of the current tree, read blind to
    # the checkout filter (the R3494 precedent).
    fresh = json.dumps(FCC.evidence(), indent=2, sort_keys=True) + "\n"
    was = FCC.landed(PAGE)
    ok("AC-FCE5", was is not None and was == fresh,
       "page=%s fresh=%dB"
       % ("missing" if was is None else "on-disk", len(fresh.encode("utf-8"))))

    # AC-FCE6: exit code semantics - rc 2 is reserved for a repairable hole.
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        rc = FCC.main(["--evidence", "--check"])
    text = sink.getvalue()
    ok("AC-FCE6",
       rc == (2 if report["left_behind"] else 0)
       and "FCE-CHECK VERDICT PASS" in text,
       "rc=%d left_behind=%d check=%s"
       % (rc, report["left_behind"],
          "PASS" if "FCE-CHECK VERDICT PASS" in text else "RED"))

    # Read-only proof: nothing the suite touched changed on disk.
    same = (stat_sig(TOOL) == sig_tool and stat_sig(PAGE) == sig_page
            and stat_sig(STATE) == sig_state
            and [stat_sig(path) for path in paths] == sig_archives)
    ok("AC-FCE7", same, "repo_untouched=%s" % same)

    total = len(CHECKS)
    passed = total - len(FAILS)
    if FAILS:
        print("SUITE FAIL %d/%d" % (passed, total))
        return 1
    print("SUITE PASS %d/%d" % (passed, total))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
