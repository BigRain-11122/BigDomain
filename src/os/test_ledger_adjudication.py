"""Battery suite: the break-qualification line on tools/qa_log.py (R3616).

AC-LADJ1..AC-LADJ3 were pinned in src/os/backlog.md BEFORE this file existed.
The defect they hold: the count station (`qa_log.py --ledger-check`) printed a
bare `broken=N`, while the qualification station (tools/qa_chain_diagnose.py,
AC-QCH1..6) already judged every one of those breaks explained. A round could
therefore quote "broken=5" as five lost records while the shipped owner of
that judgement read unexplained=0.

What is measured here: the extra line exists exactly when there is a break,
its three numbers are the adjudicator's own (no second chain law in qa_log),
a private world with an unlinked non-shard row reads RED, a linked world
prints nothing extra, an excused (prev_kind=progress) row reads declared=1,
the live ledger's bytes and mtime do not move, and a missing adjudicator is
published as UNADJUDICATED rather than defaulted to OK.

Isolation: every ledger written here lives in the system temp dir; the real
ledger is stat-ed before and after. Stdlib only, ASCII source, no network.
"""

import inspect
import io
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(BASE))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import qa_log  # noqa: E402

CRITERIA = ("AC-LADJ1", "AC-LADJ2", "AC-LADJ3")
FAILS = []
CHECKS = [0]


def check(ac, ok, evidence):
    CHECKS[0] += 1
    print("%s %s: %s" % ("PASS" if ok else "FAIL", ac, evidence), flush=True)
    if not ok:
        FAILS.append(ac)


def run_check(path=None):
    """Call the shipped printer and capture exactly what a round would read."""
    keep = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        rc = qa_log.do_ledger_check(path)
    finally:
        sys.stdout = keep
    return rc, buf.getvalue().splitlines()


def adjudication(lines):
    return [l for l in lines if l.startswith("QA-LEDGER adjudication ")]


def write_ledger(path, rows):
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def row(name, old_sha, new_sha, old_bytes=1, new_bytes=2, kind=None):
    record = {"event": "REPLACED", "name": name, "old_sha16": old_sha,
              "new_sha16": new_sha, "old_bytes": old_bytes,
              "new_bytes": new_bytes, "ts": "2026-11-28T00:00:00+08:00"}
    if kind is not None:
        record["prev_kind"] = kind
    return record


def live_arm():
    live = qa_log.LEDGER
    before = (os.path.getsize(live), os.stat(live).st_mtime_ns)
    rc, lines = run_check()
    after = (os.path.getsize(live), os.stat(live).st_mtime_ns)
    found = adjudication(lines)
    expected = qa_log.chain_reading(None)
    broken = len(qa_log.ledger_report(None)["broken"])
    want = []
    if broken and expected is not None:
        want.append("QA-LEDGER adjudication chain=%s partial=%d declared=%d "
                    "unexplained=%d source=qa_chain_diagnose"
                    % (expected["verdict"], expected["partial"],
                       expected["declared"], expected["unexplained"]))
    check("AC-LADJ1",
          found == want and rc == 0 and before == after,
          "live ledger broken=%d prints %d adjudication line(s) equal to "
          "chain_reading()=%r; rc=%d; (size,mtime_ns) unchanged=%s"
          % (broken, len(found), expected, rc, before == after))


def private_arms():
    world = tempfile.mkdtemp(prefix="qa-ledger-adj-")
    # Negative control: an unlinked break whose name no in-place progress
    # writer can explain, so the adjudicator must read RED.
    red_path = os.path.join(world, "red.jsonl")
    write_ledger(red_path, [row("not-a-shard.log", "a" * 16, "b" * 16),
                            row("not-a-shard.log", "c" * 16, "d" * 16,
                                old_bytes=9, new_bytes=10)])
    red_rc, red_lines = run_check(red_path)
    red = adjudication(red_lines)
    red_ok = (red == ["QA-LEDGER adjudication chain=RED partial=0 declared=0 "
                      "unexplained=1 source=qa_chain_diagnose"]
              and len(qa_log.ledger_report(red_path)["broken"]) == 1)

    # A linked chain is not a break, so the line must NOT appear.
    clean_path = os.path.join(world, "clean.jsonl")
    write_ledger(clean_path, [row("linked.log", "a" * 16, "b" * 16),
                              row("linked.log", "e" * 16, "e" * 16,
                                  old_bytes=2, new_bytes=3)])
    clean_rc, clean_lines = run_check(clean_path)
    clean_ok = adjudication(clean_lines) == [] and clean_rc == 0
    # (the second row links only when old_sha16 == prev new_sha16)
    write_ledger(clean_path, [row("linked.log", "a" * 16, "b" * 16),
                              row("linked.log", "b" * 16, "c" * 16,
                                  old_bytes=2, new_bytes=3)])
    clean_rc, clean_lines = run_check(clean_path)
    clean_ok = adjudication(clean_lines) == [] and clean_rc == 0

    # A row that declares it replaced a progress partial is excused and is
    # counted as `declared`; a second, unexplained break keeps the verdict
    # RED, so the two sub-counts are measured apart.
    excused_path = os.path.join(world, "excused.jsonl")
    write_ledger(excused_path,
                 [row("not-a-shard.log", "a" * 16, "b" * 16),
                  row("not-a-shard.log", "c" * 16, "d" * 16, old_bytes=9,
                      new_bytes=10, kind=qa_log.PREV_KIND_PROGRESS),
                  row("other.log", "1" * 16, "2" * 16),
                  row("other.log", "3" * 16, "4" * 16, old_bytes=7,
                      new_bytes=8)])
    ex_rc, ex_lines = run_check(excused_path)
    ex = adjudication(ex_lines)
    ex_ok = (ex == ["QA-LEDGER adjudication chain=RED partial=0 declared=1 "
                    "unexplained=1 source=qa_chain_diagnose"]
             and len(qa_log.ledger_report(excused_path)["excused"]) == 1)

    # An excused-only world has nothing broken, so the line must NOT appear.
    only_path = os.path.join(world, "only-excused.jsonl")
    write_ledger(only_path,
                 [row("x.log", "a" * 16, "b" * 16),
                  row("x.log", "c" * 16, "d" * 16, old_bytes=9, new_bytes=10,
                      kind=qa_log.PREV_KIND_PROGRESS)])
    only_rc, only_lines = run_check(only_path)
    only_ok = adjudication(only_lines) == [] and only_rc == 0

    check("AC-LADJ2", red_ok and clean_ok and ex_ok and only_ok,
          "red world reads %r; linked world prints %d extra line(s); "
          "mixed world reads %r; excused-only world prints %d extra line(s)"
          % (red, len(adjudication(clean_lines)), ex,
             len(adjudication(only_lines))))


def law_arms():
    source = inspect.getsource(qa_log)
    helper = inspect.getsource(qa_log.chain_reading)
    # The qualification is asked, never re-derived: the helper must not
    # carry its own link law or its own kind vocabulary.
    no_second_law = ("new_sha16" not in helper
                     and "progress-partial" not in helper
                     and "qa_chain_diagnose" in helper)
    once = source.count("import qa_chain_diagnose") == 1

    live = qa_log.LEDGER
    before = (os.path.getsize(live), os.stat(live).st_mtime_ns)
    saved = sys.modules.get("qa_chain_diagnose", "absent")
    sys.modules["qa_chain_diagnose"] = None
    try:
        rc, lines = run_check()
    finally:
        if saved == "absent":
            sys.modules.pop("qa_chain_diagnose", None)
        else:
            sys.modules["qa_chain_diagnose"] = saved
    blind = adjudication(lines)
    after = (os.path.getsize(live), os.stat(live).st_mtime_ns)

    check("AC-LADJ3",
          no_second_law and once and before == after
          and blind == ["QA-LEDGER adjudication chain=UNADJUDICATED"],
          "helper carries no second chain law=%s, one import=%s, read-only=%s,"
          " missing adjudicator reads %r"
          % (no_second_law, once, before == after, blind))


def main():
    live_arm()
    private_arms()
    law_arms()
    verdict = "PASS" if not FAILS else "FAIL:" + ",".join(FAILS)
    # The registry census reads a printed SUITE leaf of the shipped shape
    # ("SUITE %s %d/%d"); the criteria count follows on its own line so the
    # declared row and the measured run can be compared.
    print("SUITE %s %d/%d" % (verdict, CHECKS[0] - len(FAILS), CHECKS[0]),
          flush=True)
    print("SUITE criteria=%d failed=%s"
          % (len(CRITERIA), ",".join(FAILS) or "(none)"), flush=True)
    return 0 if not FAILS else 2


if __name__ == "__main__":
    sys.exit(main())
