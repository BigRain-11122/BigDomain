"""Fold-summary line kind suite (R2580; criteria AC-FCLS1..AC-FCLS6 were
pre-registered in state/queue/tech.md BEFORE this code existed - honesty
law).

What this proves: the kind table in ledger_lines.py says a fold line is
"other", and a fold summary really does start with the round it folded
("R2568 fold of log lines 1..20 ..."). The narrative pattern matched that
summary as a round narrative, so once a fold archived a round's ledger
line while leaving the summary live, the audit reported the round as
having no ledger at all - which is how the R2579 battery went red after
the R2578 fold archived the R2568 block. This suite pins the guard, pins
that the shipped families still classify unchanged, pins that the guard
is word-bounded, and pins the live face over the real state.json log.

Stdlib only, ASCII source, zero network. Exit 0 = all green.
"""

import io
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, BASE)

import ledger_lines as LL  # noqa: E402

EXPECTED_CRITERIA = 6
MODULE = os.path.join(BASE, "ledger_lines.py")
STATE = os.path.join(BASE, "state.json")

PASSES = 0
FAILS = 0


def check(ok, label):
    global PASSES, FAILS
    if ok:
        PASSES += 1
        print("PASS %s" % label, flush=True)
    else:
        FAILS += 1
        print("FAIL %s" % label, flush=True)


FOLD_SUMMARY = ("R2568 fold of log lines 1..20 into the archive; all 138 "
                "tokens preserved verbatim in this line: AC-DSRC1 AC-DSRC6")


def main():
    # AC-FCLS1: a real-shaped fold summary is other, not a round narrative.
    check(LL.classify(FOLD_SUMMARY) == "other"
          and LL.classify("R2579 fold of log items 4..6 (the complete block)")
          == "other",
          "AC-FCLS1 a fold summary line classifies as other")

    # AC-FCLS2: the shipped families are untouched.
    check(LL.classify("R2151 battery outcome: RUNNER PASS 352/353 suites")
          == "round"
          and LL.classify("2026-11-08 R2579 PRODUCT window on the tech head")
          == "round"
          and LL.classify("R2151 tokens: local=120k api=0 api_reason=x y z")
          == "ledger"
          and LL.classify("carry-forward rolling line R586: folded") == "other",
          "AC-FCLS2 date narrative, battery outcome and ledger kinds unchanged")

    # AC-FCLS3: word-bounded, so a round whose text merely starts with
    # "folder" is still a narrative and still needs its ledger.
    folder = "R2568 folder of log lines was rebuilt"
    rep = LL.audit([folder])
    check(LL.classify(folder) == "round"
          and rep["rounds_without_ledger"] == [2568]
          and rep["clean"] is False,
          "AC-FCLS3 guard is word-bounded: 'folder' stays a round narrative")

    # AC-FCLS4: the window shape that broke the real tree is clean now.
    shaped = [
        FOLD_SUMMARY,
        "2026-11-08 R2569 PRODUCT window on the tech head",
        "R2569 tokens: local=~22k api=0 api_reason=product window ledger line",
    ]
    shaped_rep = LL.audit(shaped)
    check(shaped_rep["rounds_without_ledger"] == []
          and shaped_rep["ledger_without_round"] == []
          and shaped_rep["other_lines"] == 1
          and shaped_rep["round_lines"] == 1
          and shaped_rep["ledger_lines"] == 1
          and shaped_rep["errors"] == []
          and shaped_rep["clean"] is True,
          "AC-FCLS4 fold summary plus narrative, no ledger for that round "
          "reads clean")

    # AC-FCLS5: no weakening - a bare narrative still gates, and the typo
    # prefix is still caught by the coverage law.
    weakened = LL.audit([
        "2026-11-08 R301 (product change narrative) something happened",
        "R302 token: local=1k api=0 api_reason=typo prefix round keeps gaps",
    ])
    check(weakened["rounds_without_ledger"] == [301, 302]
          and weakened["clean"] is False,
          "AC-FCLS5 bare narrative and typo prefix still gate")

    # AC-FCLS6: the real tree reads clean on the live face.
    with io.open(MODULE, "r", encoding="ascii", errors="strict") as handle:
        source = handle.read()
    net = LL.network_imports(source)
    live = LL.audit(LL.load_state_log(STATE))
    check(live["rounds_without_ledger"] == []
          and live["ledger_without_round"] == []
          and live["errors"] == []
          and live["clean"] is True
          and not net
          and EXPECTED_CRITERIA == 6,
          "AC-FCLS6 real state.json log reads clean, source is ASCII and "
          "network-free")

    print("suite: fold-summary line kind (R2580 AC-FCLS1..AC-FCLS6)")
    if FAILS:
        print("SUITE FAIL %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
        return 1
    print("SUITE PASS %d/%d criteria" % (PASSES, EXPECTED_CRITERIA))
    return 0


if __name__ == "__main__":
    sys.exit(main())